from adapt.intent import IntentBuilder
from mycroft.skills.core import MycroftSkill, intent_handler
from mycroft.util.log import LOG
from mycroft.util import get_cache_directory
from .mplayerutil import *
from .ytutil import download


class YoutubeSkill(MycroftSkill):

    def __init__(self):
        super(YoutubeSkill, self).__init__(name="YoutubeSkill")
        self.process = None

    def _get_process(self):
        process = self.process
        if process and process.poll() is None:
            return process
        return None

    def _replace_process(self, process):
        """
        :param process: The new Process to replace the old one or None
        :return: True if there was a previous process, False otherwise
        """
        r = False
        if self.process:
            self.process.terminate()
            self.process.wait()
            r = True
        self.process = process
        return r

    def toggle_pause(self):
        process = self._get_process()
        if process:
            send(" ", process)
            return True
        return False

    def skip_10_seconds(self, number_of_skips, forward=True):
        process = self._get_process()
        if process:
            skip_10_seconds(process, number_of_skips, forward=forward)
            return True
        return False

    @intent_handler(IntentBuilder("YoutubeIntent").require("Youtube"))
    def handle_youtube(self, message):
        def success(path):
            self._replace_process(create_player(path))
            self.speak_dialog("playing")

        def fail():
            self.speak_dialog("failed")
            self._replace_process(None)

        word = message.data.get("Youtube")
        search = message.data["utterance"].replace(word, "")
        LOG.info("using: " + search)
        self.speak_dialog("downloading")
        path_str = get_cache_directory()
        print("using: " + str(path_str))
        download(search, success, fail, path_str=path_str)

    def stop(self):
        return self._replace_process(None)


def create_skill():
    return YoutubeSkill()
