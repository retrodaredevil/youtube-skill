import json

from ytutil import download, get_track, get_artist
from mplayerutil import create_player


def success(path, info):
    print("success! path: " + path)
    print(json.dumps(info))
    print("track: " + get_track(info))
    print("artist: " + get_artist(info))
    process = create_player(path)
    process.wait()


def main():
    download("super mario 64 dire dire docks", success, lambda: print("Failed!"))


if __name__ == '__main__':
    main()

