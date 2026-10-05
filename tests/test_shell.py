"""Проверки парсера, команд и обработки ошибок."""

import io
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from shell import Shell


class ShellTests(unittest.TestCase):
    """Проверяет внешнее поведение оболочки."""

    def setUp(self):
        """Создает оболочку с выводом в память."""
        self.output = io.StringIO()
        self.shell = Shell("test-vfs", self.output)

    def test_prompt(self):
        """Имя VFS входит в приглашение."""
        self.assertEqual(self.shell.prompt, "test-vfs:/$ ")

    def test_stubs(self):
        """Заглушки показывают имя и аргументы после разбора пробелов."""
        self.shell.execute("  ls   /docs  ")
        self.shell.execute("cd")
        self.assertIn("ls: аргументы = ['/docs']", self.output.getvalue())
        self.assertIn("cd: аргументы = []", self.output.getvalue())

    def test_empty_input(self):
        """Пустая строка не вызывает ошибки."""
        self.shell.execute("   ")
        self.assertEqual(self.output.getvalue(), "")

    def test_errors(self):
        """Неизвестная команда и лишние аргументы вызывают ошибки."""
        for line in ("unknown", "ls a b", "cd a b", "exit now"):
            with self.subTest(line=line), self.assertRaises(ValueError):
                self.shell.execute(line)
        self.assertTrue(self.shell.running)

    def test_exit(self):
        """exit завершает работу."""
        self.shell.execute("exit")
        self.assertFalse(self.shell.running)

    def test_repl_continues_after_error(self):
        """После ошибки интерактивный режим принимает следующую команду."""
        with patch("builtins.input", side_effect=["unknown", "ls", "exit"]):
            self.shell.repl()
        self.assertIn("Ошибка:", self.output.getvalue())
        self.assertIn("ls: аргументы = []", self.output.getvalue())
        self.assertFalse(self.shell.running)

    def test_script_stops_at_first_error(self):
        """Команды после первой ошибки не исполняются."""
        with TemporaryDirectory() as folder:
            path = Path(folder) / "startup.txt"
            path.write_text("ls\nunknown\ncd /later\n", encoding="utf-8")
            self.assertFalse(self.shell.run_script(path))
        text = self.output.getvalue()
        self.assertIn("test-vfs:/$ ls", text)
        self.assertIn("Ошибка в строке 2:", text)
        self.assertNotIn("/later", text)

    def test_script_exit(self):
        """exit в скрипте завершает работу до следующей строки."""
        with TemporaryDirectory() as folder:
            path = Path(folder) / "startup.txt"
            path.write_text("ls\nexit\nunknown\n", encoding="utf-8")
            self.assertTrue(self.shell.run_script(path))
        self.assertFalse(self.shell.running)
        self.assertNotIn("unknown", self.output.getvalue())

    def test_missing_script(self):
        """Отсутствующий скрипт вызывает понятное сообщение."""
        with TemporaryDirectory() as folder:
            path = Path(folder) / "missing.txt"
            self.assertFalse(self.shell.run_script(path))
        self.assertIn("Ошибка чтения скрипта:", self.output.getvalue())


if __name__ == "__main__":
    unittest.main()
