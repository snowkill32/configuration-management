import io
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from shell import Shell
from vfs import VFS


class ShellTests(unittest.TestCase):
    def setUp(self):
        self.output = io.StringIO()
        vfs = VFS("test-vfs", {
            "/": None, "/docs": None, "/docs/notes.txt": b"notes",
            "/my docs": None, "/my docs/readme.txt": b"text", "/later": None,
        })
        self.shell = Shell(output=self.output, vfs=vfs)

    def test_prompt(self):
        self.assertEqual(self.shell.prompt, "test-vfs:/$ ")

    def test_list_and_cd(self):
        self.shell.execute("  ls   /docs  ")
        self.shell.execute("cd /docs")
        self.assertEqual(self.shell.cwd, "/docs")
        self.assertEqual(self.output.getvalue(), "notes.txt\n")
        self.shell.execute("cd")
        self.assertEqual(self.shell.cwd, "/")

    def test_empty_input(self):
        self.shell.execute("   ")
        self.assertEqual(self.output.getvalue(), "")

    def test_quoted_arguments(self):
        for line in ('ls "/my docs"', "ls '/my docs'"):
            with self.subTest(line=line):
                self.output.seek(0)
                self.output.truncate(0)
                self.shell.execute(line)
                self.assertIn(
                    "readme.txt", self.output.getvalue()
                )

    def test_empty_quoted_argument(self):
        with self.assertRaises(ValueError):
            self.shell.execute('cd ""')
        self.assertEqual(self.shell.cwd, "/")

    def test_unclosed_quotes(self):
        with self.assertRaises(ValueError):
            self.shell.execute('ls "/my docs')
        self.assertTrue(self.shell.running)

    def test_errors(self):
        for line in ("unknown", "ls a b", "cd a b", "exit now"):
            with self.subTest(line=line), self.assertRaises(ValueError):
                self.shell.execute(line)
        self.assertTrue(self.shell.running)

    def test_exit(self):
        self.shell.execute("exit")
        self.assertFalse(self.shell.running)

    def test_repl_continues_after_error(self):
        # Подставляем готовые команды вместо ввода с клавиатуры.
        with patch("builtins.input", side_effect=["unknown", "ls", "exit"]):
            self.shell.repl()
        self.assertIn("Ошибка:", self.output.getvalue())
        self.assertIn("docs\n", self.output.getvalue())
        self.assertFalse(self.shell.running)

    def test_script_continues_after_error(self):
        with TemporaryDirectory() as folder:
            path = Path(folder) / "startup.txt"
            path.write_text("ls\nunknown\ncd /later\n", encoding="utf-8")
            self.assertTrue(self.shell.run_script(path))
        text = self.output.getvalue()
        self.assertIn("test-vfs:/$ ls", text)
        self.assertIn("Ошибка в строке 2:", text)
        self.assertEqual(self.shell.cwd, "/later")

    def test_relative_paths_and_parent(self):
        self.shell.execute("cd docs")
        self.assertEqual(self.shell.prompt, "test-vfs:/docs$ ")
        self.shell.execute("ls ./notes.txt")
        self.assertEqual(self.output.getvalue(), "notes.txt\n")
        self.shell.execute("cd ../my\\ docs")
        self.assertEqual(self.shell.cwd, "/my docs")
        self.shell.execute("cd ../../..")
        self.assertEqual(self.shell.cwd, "/")

    def test_failed_cd_keeps_directory(self):
        self.shell.execute("cd /docs")
        for value in ("/missing", "/docs/notes.txt", "/docs/notes.txt/.."):
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.shell.execute(f"cd {value}")
            self.assertEqual(self.shell.cwd, "/docs")

    def test_list_is_not_recursive(self):
        self.shell.execute("ls /")
        self.assertEqual(self.output.getvalue(), "docs\nlater\nmy docs\n")

    def test_script_exit(self):
        with TemporaryDirectory() as folder:
            path = Path(folder) / "startup.txt"
            path.write_text("ls\nexit\nunknown\n", encoding="utf-8")
            self.assertTrue(self.shell.run_script(path))
        self.assertFalse(self.shell.running)
        self.assertNotIn("unknown", self.output.getvalue())

    def test_missing_script(self):
        with TemporaryDirectory() as folder:
            path = Path(folder) / "missing.txt"
            self.assertFalse(self.shell.run_script(path))
        self.assertIn("Ошибка чтения скрипта:", self.output.getvalue())


if __name__ == "__main__":
    unittest.main()
