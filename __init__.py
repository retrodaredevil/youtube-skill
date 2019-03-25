from adapt.intent import IntentBuilder
from mycroft.skills.core import MycroftSkill, intent_handler
from mycroft.util.log import LOG
from mycroft.util import get_cache_directory
from mycroft.util.parse import extract_number
from .mplayerutil import *
from .ytutil import download, get_artist, get_track


# from mycroft.util.lang import get_primary_lang_code


class YoutubeSkill(MycroftSkill):

    def __init__(self):
        super(YoutubeSkill, self).__init__(name="YoutubeAudioAndVideo")
        self.process = None
        self.info_dict = None
        self.is_playing = False
        """True if the current process is playing. If you want to know if something is playing, you should also make
        sure self.process is active. It's recommended to use self._get_process()"""
        self.is_auto_paused = False

    def initialize(self):
        self.add_event("recognizer_loop:record_begin", self.auto_pause_begin)
        self.add_event("recognizer_loop:utterance", self.auto_play_end)
        self.add_event("recognizer_loop:audio_output_start", self.auto_pause_begin)
        self.add_event("recognizer_loop:audio_output_end", self.auto_play_end)

        self.add_event("mycroft.audio.service.play", self.play)
        self.add_event("mycroft.audio.service.resume", self.play)
        self.add_event("mycroft.audio.service.pause", lambda: self.pause())  # in lambda so unwanted args aren't passed
        # self.add_event("mycroft.audio.service.next", lambda: self.skip_10_seconds(2))
        # self.add_event("mycroft.audio.service.prev", lambda: self.skip_10_seconds(2, forward=False))

    def auto_pause_begin(self):
        print("record begin.")
        if self.is_playing:
            # print("should auto pause in next method call because music is playing")
            self.pause(auto_paused=True)

    def auto_play_end(self):
        print("record end")
        if self.is_auto_paused:
            # print("it was auto paused so now we'll play")
            self.play()

    def play(self):
        if not self.is_playing:
            self.toggle_pause()
        self.is_auto_paused = False
        # print("auto paused is now False after calling play()")

    def pause(self, auto_paused=False):
        if self.is_playing:
            self.toggle_pause()

        self.is_auto_paused = auto_paused
        # print("auto paused is now " + str(auto_paused) + " after calling pause()")

    def _get_process(self):
        process = self.process
        if process and process.poll() is None:
            return process
        return None

    def _replace_process(self, process, info_dict=None):
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
        self.info_dict = info_dict
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
        def success(path, info):
            self._replace_process(create_player(path), info_dict=info)
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

    def handle_skip(self, message, forward):
        is_minute = bool(message.data.get("Minute"))
        number = extract_number(message.data["utterance"], self.lang)
        if is_minute:
            number *= 60

        if number <= 5:
            self.speak_dialog("must.choose.multiple.of.ten")
        else:
            amount = int(round(number / 10.0))
            if not self.skip_10_seconds(amount, forward=forward):
                self.speak_dialog("no.song.playing")

    @intent_handler(IntentBuilder("YoutubeSkipForwardIntent").require("SkipForward")
                    .optionally("Second").optionally("Minute"))
    def handle_skip_forward(self, message):
        self.handle_skip(message, True)

    @intent_handler(IntentBuilder("YoutubeSkipBackwardIntent").require("SkipBackward")
                    .optionally("Second").optionally("Minute"))
    def handle_skip_backward(self, message):
        self.handle_skip(message, False)

    @intent_handler(IntentBuilder("YoutubeVideoInfo").require("Youtube").require("Info"))
    def handle_video_info(self, message):
        info = self.info_dict
        if not info:
            if self.is_playing and self._get_process():  # no info available
                self.speak_dialog("no.info.available")
            else:  # nothing playing
                self.speak_dialog("no.song.playing")
            return
        self.speak_dialog("currently.playing", {"title": get_track(info), "artist": get_artist(info)})

    def stop(self):
        return self._replace_process(None)


def create_skill():
    return YoutubeSkill()
