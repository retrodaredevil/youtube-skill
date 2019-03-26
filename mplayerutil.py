import subprocess
from time import sleep

SKIP_TEN_FORWARD = "\033[C;"
SKIP_TEN_BACKWARD = "\033[D;"
SKIP_MINUTE_FORWARD = "\033[A;"
SKIP_MINUTE_BACKWARD = "\033[B;"


def create_player(path_str, show_video=True, start_fullscreen=False):
    args = ["mplayer"]
    if not show_video:
        args.extend(["-vo", "null"])
    if start_fullscreen:
        args.extend("-fs")
    args.append(path_str)
    return subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, stdin=subprocess.PIPE)


def send(text, process):
    process.stdin.write(text.encode())
    process.stdin.flush()


def toggle_pause(process):
    send(" ", process)


def toggle_fullscreen(process):
    send("f", process)


def volume_up(process):
    send("*", process)


def volume_down(process):
    send("/", process)


def mute(process):
    send("m", process)


def skip_10_seconds(process, number_of_skips, forward=True):
    number_of_skips = int(number_of_skips)
    if number_of_skips < 1:
        raise ValueError("Cannot skip " + str(number_of_skips) + " times!")
    minute, ten_second = divmod(number_of_skips, 6)
    for i in range(minute):
        send(SKIP_MINUTE_FORWARD if forward else SKIP_MINUTE_BACKWARD, process)
        sleep(.01)

    for i in range(ten_second):
        send(SKIP_TEN_FORWARD if forward else SKIP_TEN_BACKWARD, process)
        sleep(.01)

