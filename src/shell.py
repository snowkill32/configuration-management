import shlex
import sys
from pathlib import Path

from vfs import load_vfs

MAX_PATH_ARGUMENTS = 1


class Shell:
    def __init__(self, name="default", output=None, vfs=None):
        self.vfs = vfs if vfs is not None else load_vfs()
        self.name = vfs.name if vfs is not None else name
        # Обычно вывод идет в консоль, а в тестах сохраняется в памяти.
        self.output = output if output is not None else sys.stdout
        self.running = True
        self.cwd = "/"

    @property
    def prompt(self):
        return f"{self.name}:{self.cwd}$ "

    def execute(self, line):
        # shlex сохраняет текст в кавычках как один аргумент.
        parts = shlex.split(line)
        if not parts:
            return
        command, *args = parts
        handlers = {
            "exit": self.exit_command,
            "ls": self.ls_command,
            "cd": self.cd_command,
        }
        if command not in handlers:
            raise ValueError(f"неизвестная команда: {command}")
        handlers[command](args)

    def exit_command(self, args):
        if args:
            raise ValueError("exit: аргументы не нужны")
        self.running = False

    def get_path(self, args, command, default):
        if len(args) > MAX_PATH_ARGUMENTS:
            raise ValueError(f"{command}: допустим один путь")
        return args[0] if args else default

    def ls_command(self, args):
        path = self.get_path(args, "ls", ".")
        names = self.vfs.list_directory(path, self.cwd)
        if names:
            print("\n".join(names), file=self.output)

    def cd_command(self, args):
        value = self.get_path(args, "cd", "/")
        path = self.vfs.resolve(value, self.cwd)
        self.vfs.require_directory(path)
        self.cwd = path

    def repl(self):
        while self.running:
            try:
                line = input(self.prompt)
                self.execute(line)
            except ValueError as error:
                print(f"Ошибка: {error}", file=self.output)
            except (EOFError, KeyboardInterrupt):
                print(file=self.output)
                break

    def run_script(self, path):
        try:
            # utf-8-sig также убирает служебную отметку BOM в начале файла.
            lines = Path(path).read_text(encoding="utf-8-sig").splitlines()
        except (OSError, UnicodeError) as error:
            print(f"Ошибка чтения скрипта: {error}", file=self.output)
            return False
        for number, line in enumerate(lines, 1):
            print(self.prompt + line, file=self.output)
            try:
                self.execute(line)
            except ValueError as error:
                print(f"Ошибка в строке {number}: {error}", file=self.output)
                continue
            if not self.running:
                break
        return True
