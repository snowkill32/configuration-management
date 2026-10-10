import argparse
from pathlib import Path
import sys

from shell import Shell
from vfs import load_vfs


def parse_args():
    parser = argparse.ArgumentParser(description="Эмулятор: вариант 25")
    parser.add_argument(
        "--vfs", type=Path, help="путь к CSV-файлу VFS",
    )
    parser.add_argument(
        "--script", type=Path, help="путь к стартовому скрипту",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    print(f"VFS: {args.vfs or 'по умолчанию (в памяти)'}")
    print(f"Стартовый скрипт: {args.script or 'не задан'}")
    try:
        vfs = load_vfs(args.vfs)
        message = vfs.motd()
    except (OSError, ValueError, UnicodeError) as error:
        print(f"Ошибка загрузки VFS: {error}")
        return 1
    print(f"Загружена VFS: {vfs.name}")
    print(vfs.describe())
    if message:
        print(message)
    shell = Shell(vfs=vfs)
    # False означает, что сам файл команд не удалось прочитать.
    if args.script and not shell.run_script(args.script):
        return 1
    shell.repl()
    return 0


if __name__ == "__main__":
    sys.exit(main())
