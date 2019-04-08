import json
import subprocess
from os.path import join
from pathlib import Path


def _download_video(search_str, path_str="."):
    path = Path(path_str)
    print(path.absolute())
    if not path.exists():
        path.mkdir()
    if not path.is_dir():
        raise ValueError("path_str must not be a directory!")
    return subprocess.Popen(["python3", "-m", "youtube_dl", "--print-json", "--default-search", "ytsearch", search_str],
                            cwd=str(path.absolute()), stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                            stdin=subprocess.DEVNULL)


def download(search_str, on_success, on_fail, path_str="./.download-cache"):
    """
    :param search_str: The text to search
    :param on_success: A callable object that takes one argument: The path to the file
    :param on_fail: A callable object that takes no arguments.
    :param path_str: The directory that the file will be downloaded to
    """
    process = _download_video(search_str, path_str)
    try:
        code = process.wait(20)  # a maximum time of 20 seconds to download
    except subprocess.TimeoutExpired:
        on_fail()
        return
    json_str = process.stdout.read()
    try:
        info = json.loads(json_str)
    except json.decoder.JSONDecodeError:
        on_fail()
        return
    if code == 0:
        on_success(join(path_str, info["_filename"]), info)
    else:
        on_fail()


def get_artist(info_dict):
    return info_dict.get("artist") or info_dict.get("creator") or info_dict.get("uploader")


def get_track(info_dict):
    return info_dict.get("track") or info_dict.get("alt_title") or info_dict.get("title")
