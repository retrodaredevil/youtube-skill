import datetime
import re
from os.path import join

from adapt.intent import IntentBuilder
from mycroft.skills.core import MycroftSkill, intent_handler
from mycroft.skills.common_play_skill import CommonPlaySkill, CPSMatchLevel
from mycroft.util.log import LOG
from mycroft.util.parse import extract_number
from .mplayerutil import *
from .ytutil import download, get_artist, get_track


# TODO Use this to make better: https://github.com/penrods/AVmusic/blob/18.08/__init__.py?ts=4

def split_word(to_split):
    """Simple util method that is used throughout this file to easily split a string if needed."""
    return re.split("\W+", to_split)


class VideoInfo:
    def __init__(self, path, info, show_video, start_fullscreen):
        self.path = path
        self.info = info
        self.show_video = show_video
        self.start_fullscreen = start_fullscreen


class YoutubeSkill(CommonPlaySkill):

    def __init__(self):
        super(YoutubeSkill, self).__init__(name="YoutubeAudioAndVideo")
        self.process = None
        self.current_video_info = None

        self.past_videos = []
        self.next_videos = []

        self.is_playing = False
        """True if the current process is playing. If you want to know if something is playing, you should also make
        sure self.process is active. It's recommended to use self._get_process()"""
        self.is_auto_paused = False
        self.is_stopped = False
        """A bool that when True, stops automatic playing of the next song"""

    def initialize(self):
        # useful: https://mycroft.ai/documentation/message-bus/
        self.add_event("recognizer_loop:record_begin", self.auto_pause_begin)
        self.add_event("recognizer_loop:record_end", self.auto_play_end)
        self.add_event("recognizer_loop:audio_output_start", self.auto_pause_begin)
        self.add_event("recognizer_loop:audio_output_end", self.auto_play_end)

        self.add_event("mycroft.audio.service.play", self.play)
        self.add_event("mycroft.audio.service.resume", self.play)
        self.add_event("mycroft.audio.service.pause", lambda: self.pause())  # in lambda so unwanted args aren't passed
        self.add_event("mycroft.audio.service.next", lambda: self.next(say_no_videos=True))
        self.add_event("mycroft.audio.service.prev", lambda: self.previous())

        self.schedule_repeating_event(self.periodic_execute, datetime.datetime.now(), 1)

    def _voc_match(self, utt, voc_filename, lang=None):
        lang = lang or self.lang
        cache_key = lang + voc_filename
        self.voc_match(utt, voc_filename, lang)
        if utt:
            # Check for matches against complete words
            # for i in self.voc_match_cache[cache_key]:
            #     if re.match(r'.*\b' + i + r'\b.*', utt):
            #         return i
            return next((i for i in self.voc_match_cache[cache_key]
                         if re.match(r'.*\b' + i + r'\b.*', utt)), None)
        else:
            return None

    def auto_pause_begin(self):
        if self.is_playing:
            # print("should auto pause in next method call because music is playing")
            self.pause(auto_paused=True)

    def auto_play_end(self):
        if self.is_auto_paused:
            # print("it was auto paused so now we'll play")
            self.play()

    def play(self):
        if not self.is_playing:
            self.toggle_pause()
        self.is_auto_paused = False

    def pause(self, auto_paused=False):
        if self.is_playing:
            self.toggle_pause()

        self.is_auto_paused = auto_paused

    def _get_process(self):
        process = self.process
        if process and process.poll() is None:
            return process
        return None

    def _replace_process(self, process, video_info=None):
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
        self.current_video_info = video_info
        if process:
            self.is_playing = True
            self.is_stopped = False

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

    def play_video(self, video_info):
        self._replace_process(create_player(video_info.path, show_video=video_info.show_video,
                                            start_fullscreen=video_info.start_fullscreen),
                              video_info=video_info)
        self.speak_dialog("playing")

    def next(self, say_no_videos=True):
        if self.next_videos:
            video_info = self.current_video_info
            if video_info:
                self.past_videos.append(video_info)
            next_video = self.next_videos.pop(0)
            self.play_video(next_video)
        elif say_no_videos:
            self.speak_dialog("no.next.videos")

    def previous(self):
        if self.past_videos:
            video_info = self.current_video_info
            if video_info:
                self.next_videos.insert(0, video_info)

            new_video = self.past_videos.pop(-1)
            self.play_video(new_video)
        else:
            self.speak_dialog("no.past.videos")

    def periodic_execute(self):
        if not self.is_stopped and not self._get_process():
            self.next(say_no_videos=False)

    def do_video_search_and_play(self, search, schedule_next, show_video, start_fullscreen):
        def success(path, info):
            video_info = VideoInfo(path, info, show_video, start_fullscreen)
            self.is_stopped = False
            if schedule_next:
                self.next_videos.append(video_info)
                self.speak_dialog("downloaded")
            else:
                current_video = self.current_video_info
                if current_video:
                    self.past_videos.append(current_video)
                self.play_video(video_info)

        def fail():
            self.speak_dialog("failed")
            self.enclosure.mouth_text("Failed to Download")
            self._replace_process(None)
        LOG.info("using: " + search)
        self.speak_dialog("downloading")
        self.enclosure.mouth_text("Downloading...")
        path_str = join(self.file_system.path, ".download-cache")
        download(search, success, fail, path_str=path_str)

    def CPS_match_query_phrase(self, phrase):
        phrase = phrase.lower()

        next_word = self._voc_match(phrase, "Next")
        is_next = bool(next_word)

        without_video = self._voc_match(phrase, "WithoutVideo")
        is_without_video = bool(without_video)

        start_fullscreen = self._voc_match(phrase, "StartFullscreen")
        is_fullscreen = bool(start_fullscreen)

        # print("here: {}, {}, {}".format(next_word, without_video, start_fullscreen))
        if is_next:
            phrase = phrase.replace(next_word, "")
        if is_without_video:
            phrase = phrase.replace(without_video, "")
            is_fullscreen = False
        if is_fullscreen:
            phrase = phrase.replace(start_fullscreen, "")

        # search, schedule next, show video, start full screen
        data = (phrase, is_next, not is_without_video, is_fullscreen)
        if self.voc_match(phrase, "Youtube"):
            return (phrase, CPSMatchLevel.MULTI_KEY, data)
        else:
            return (phrase, CPSMatchLevel.GENERIC, data)

    def CPS_start(self, phrase, data):
        self.do_video_search_and_play(data[0], *(data[1:]))

    @intent_handler(IntentBuilder("YoutubeIntent").require("Youtube").optionally("WithoutVideo")
                    .optionally("StartFullscreen").optionally("Next"))
    def handle_youtube(self, message):

        next_word = message.data.get("Next")
        is_next = bool(next_word)

        without_video = message.data.get("WithoutVideo")
        is_without_video = bool(without_video)

        start_fullscreen = message.data.get("StartFullscreen")
        is_fullscreen = bool(start_fullscreen)

        word = message.data.get("Youtube")
        search = message.data["utterance"].replace(word, "")
        if is_next:
            search = search.replace(next_word, "")
        if is_without_video:
            search = search.replace(without_video, "")
            is_fullscreen = False
        if is_fullscreen:
            search = search.replace(start_fullscreen, "")

        self.do_video_search_and_play(search, is_next, not without_video, is_fullscreen)

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
        current_video = self.current_video_info
        if not current_video:
            if self.is_playing and self._get_process():  # no info available
                self.speak_dialog("no.info.available")
            else:  # nothing playing
                self.speak_dialog("no.song.playing")
            return
        info = current_video.info
        self.speak_dialog("currently.playing", {"title": get_track(info), "artist": get_artist(info)})

    @intent_handler(IntentBuilder("YoutubeFullscreen").require("Youtube").require("ToggleFullscreen"))
    def handle_toggle_fullscreen(self, message):
        process = self._get_process()
        if process:
            toggle_fullscreen(process)
        else:
            self.speak_dialog("no.song.playing")

    def stop(self):
        print("youtube skill received stop.")
        self.is_stopped = True
        return self._replace_process(None)


def create_skill():
    return YoutubeSkill()
