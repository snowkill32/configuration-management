import shlex
import sys
from pathlib import Path

MAX_PATH_ARGUMENTS = 1


class Shell:
    def __init__(self, name="default", output=None):
        self.name = name
        # Обычно вывод идет в консоль, а в тестах сохраняется в памяти.
        self.output = output if output is not None else sys.stdout
        self.running = True

    @property
    def prompt(self):
        return f"{self.name}:/$ "

    def execute(self, line):
        # shlex сохраняет текст в кавычках как один аргумент.
        parts = shlex.split(line)
        if not parts:
            return
        command, *args = parts
        if command == "exit":
            if args:
                raise ValueError("exit: аргументы не нужны")
            self.running = False
        elif command in ("ls", "cd"):
            if len(args) > MAX_PATH_ARGUMENTS:
                raise ValueError(f"{command}: допустим один путь")
            print(f"{command}: аргументы = {args}", file=self.output)
        else:
            raise ValueError(f"неизвестная команда: {command}")

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
