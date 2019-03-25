import subprocess


def create_player(path_str, show_video=True):
    args = ["mplayer"]
    if not show_video:
        args.extend(["-vo", "null"])
    args.append(path_str)
    return subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, stdin=subprocess.PIPE)


def send(text, process):
    process.stdin.write(text.encode())
    process.stdin.flush()


def toggle_pause(process):
    send(" ", process)


def skip_10_seconds(process, number_of_skips, forward=True):
    number_of_skips = int(number_of_skips)
    if number_of_skips < 1:
        raise ValueError("Cannot skip " + str(number_of_skips) + " times!")

    send(("\033[" + ("C" if forward else "D")) * number_of_skips, process)

