import argparse
from pathlib import Path
import sys

from shell import Shell

# parents[0] — папка src, parents[1] — папка проекта.
PROJECT_ROOT = Path(__file__).resolve().parents[1]


def parse_args():
    parser = argparse.ArgumentParser(description="Эмулятор: вариант 25")
    parser.add_argument(
        "--vfs", type=Path, default=PROJECT_ROOT / "vfs.csv",
        help="путь к VFS (на этом этапе файл не загружается)",
    )
    parser.add_argument(
        "--script", type=Path, help="путь к стартовому скрипту",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    print(f"VFS: {args.vfs}")
    print(f"Стартовый скрипт: {args.script or 'не задан'}")
    shell = Shell(name=args.vfs.stem or "default")
    # False означает, что сам файл команд не удалось прочитать.
    if args.script and not shell.run_script(args.script):
        return 1
    shell.repl()
    return 0


if __name__ == "__main__":
    sys.exit(main())
