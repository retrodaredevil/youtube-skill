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
        self.is_playing = False
        self.is_auto_paused = False

    def initialize(self):
        self.add_event("recognizer_loop:record_begin", self.record_begin)
        self.add_event("recognizer_loop:audio_output_end", self.record_end)
        self.add_event("mycroft.audio.service.play", self.play)
        self.add_event("mycroft.audio.service.resume", self.play)
        self.add_event("mycroft.audio.service.pause", lambda: self.pause())  # in lambda so unwanted args aren't passed
        self.add_event("mycroft.audio.service.next", lambda: self.skip_10_seconds(2))
        self.add_event("mycroft.audio.service.prev", lambda: self.skip_10_seconds(2, forward=False))

    def record_begin(self):
        print("record begin.")
        if self.is_playing:
            print("should auto pause in next method call because music is playing")
            self.pause(auto_paused=True)

    def record_end(self):
        print("record end")
        if self.is_auto_paused:
            print("it was auto paused so now we'll play")
            self.play()

    def play(self):
        if not self.is_playing:
            self.toggle_pause()
        self.is_auto_paused = False
        print("auto paused is now False after calling play()")

    def pause(self, auto_paused=False):
        if self.is_playing:
            self.toggle_pause()

        self.is_auto_paused = auto_paused
        print("auto paused is now " + str(auto_paused) + " after calling pause()")

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
        if self._get_process():
            self.is_playing = True
        return r

    def toggle_pause(self):
        process = self._get_process()
        if process:
            toggle_pause(process)
            self.is_playing = not self.is_playing
            return True
        return False

    def skip_10_seconds(self, number_of_skips, forward=True):
        process = self._get_process()
        if process:
            skip_10_seconds(process, number_of_skips, forward=forward)
            self.is_playing = True
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
