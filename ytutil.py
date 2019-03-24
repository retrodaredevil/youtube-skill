import subprocess
import threading
from difflib import SequenceMatcher
from pathlib import Path
import youtube_dl


def _download_video(search_str, path_str="."):
    path = Path(path_str)
    print(path.absolute())
    if not path.exists():
        path.mkdir()
    if not path.is_dir():
        raise ValueError("path_str must not be a directory!")
    return subprocess.Popen(["python3", "-m", "youtube_dl", "--default-search", "ytsearch", search_str],
                            cwd=str(path.absolute()), stdout=subprocess.DEVNULL,
                            stdin=subprocess.DEVNULL)


def _get_downloaded_path(search_str, path_str="."):
    """
    :param search_str: The search string
    :param path_str: The path that the file is in
    :return: A str representing the absolute file path to the desired file
    """
    path = Path(path_str)
    if not path.is_dir():
        raise ValueError("path is not a directory!")
    best_ratio = 0
    best_file = None
    for file in path.iterdir():
        ratio = SequenceMatcher(None, file.name.lower(), search_str.lower()).ratio()
        if ratio > best_ratio:
            best_ratio = ratio
            best_file = str(file.absolute())

    return best_file


def download(search_str, on_success, on_fail, path_str="/home/josh/.download-cache"):
    """
    :param search_str: The text to search
    :param on_success: A callable object that takes one argument: The path to the file
    :param on_fail: A callable object that takes no arguments.
    :param path_str: The directory that the file will be downloaded to
    """
    def thread():
        print("starting thread")
        code = _download_video(search_str, path_str).wait(20)  # a maximum time of 20 seconds to download
        print("downloaded")
        if code == 0:
            print("success")
            on_success(_get_downloaded_path(search_str, path_str))
        else:
            print("fail")
            on_fail()

    # threading.Thread(target=thread).start()
    thread()
