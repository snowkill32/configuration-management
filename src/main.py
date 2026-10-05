"""Точка входа консольного эмулятора."""

import argparse
from pathlib import Path
import sys

from shell import Shell
from vfs import load_vfs

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def parse_args():
    """Получает пути VFS и стартового скрипта из командной строки."""
    parser = argparse.ArgumentParser(description="Эмулятор: вариант 24")
    parser.add_argument(
        "--vfs", type=Path, default=PROJECT_ROOT / "examples/minimal.xml",
        help="путь к XML-файлу VFS",
    )
    parser.add_argument(
        "--script", type=Path, help="путь к стартовому скрипту",
    )
    return parser.parse_args()


def main():
    """Показывает параметры, выполняет скрипт и запускает диалог."""
    args = parse_args()
    print(f"VFS: {args.vfs}")
    print(f"Стартовый скрипт: {args.script or 'не задан'}")
    try:
        vfs = load_vfs(args.vfs)
    except (OSError, ValueError) as error:
        print(f"Ошибка загрузки VFS: {error}")
        return 1
    print(f"Загружена VFS: {vfs.name}")
    print(vfs.describe())
    shell = Shell(vfs=vfs)
    if args.script and not shell.run_script(args.script):
        return 1
    shell.repl()
    return 0


if __name__ == "__main__":
    sys.exit(main())
