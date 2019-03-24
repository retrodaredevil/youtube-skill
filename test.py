from ytutil import download
from mplayerutil import create_player


def success(path):
    print("success! path: " + path)
    process = create_player(path)
    process.wait()


def main():
    download(" viral song", success, lambda: print("Failed!"))


if __name__ == '__main__':
    main()

