"""Минимальная командная оболочка для варианта 24."""

import sys
from pathlib import Path

MAX_PATH_ARGUMENTS = 1


class Shell:
    """Обрабатывает команды и поддерживает цикл ввода."""

    def __init__(self, name="default", output=None, vfs=None):
        """Задает имя VFS и поток для вывода сообщений."""
        self.vfs = vfs
        self.name = vfs.name if vfs is not None else name
        self.output = output if output is not None else sys.stdout
        self.running = True

    @property
    def prompt(self):
        """Возвращает приглашение с именем VFS."""
        return f"{self.name}:/$ "

    def execute(self, line):
        """Разделяет ввод по пробелам и выполняет одну команду."""
        parts = line.split()
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
        """Читает команды до exit, конца ввода или Ctrl+C."""
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
        """Показывает диалог из файла и останавливается при первой ошибке."""
        try:
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
                return False
            if not self.running:
                break
        return True
