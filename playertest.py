import sys
from time import sleep

from mplayerutil import *


def main():
    file_path_str = sys.argv[1]
    process = create_player(file_path_str)
    sleep(1)
    toggle_pause(process)
    sleep(3)
    toggle_pause(process)
    sleep(3)
    skip_10_seconds(process, 1)
    sleep(5)
    skip_10_seconds(process, 1, forward=False)

    for i in range(0, 10):
        sleep(11)
        if process.poll() is not None:
            break
        skip_10_seconds(process, 1, forward=False)

    process.wait()
    print("Hey, nice. It worked! (Assuming the song isn't still playing)")


if __name__ == '__main__':
    main()
