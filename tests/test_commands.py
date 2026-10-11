import io
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from shell import Shell
from vfs import load_vfs

ROOT = Path(__file__).resolve().parents[1]


class CommandTests(unittest.TestCase):
    def setUp(self):
        self.output = io.StringIO()
        self.vfs = load_vfs(ROOT / "examples/deep.csv")
        self.shell = Shell(output=self.output, vfs=self.vfs)

    def test_pwd(self):
        self.shell.execute("pwd")
        self.shell.execute("cd docs/projects")
        self.shell.execute("pwd")
        self.assertEqual(self.output.getvalue(), "/\n/docs/projects\n")

    def test_whoami(self):
        with patch("shell.getpass.getuser", return_value="student"):
            self.shell.execute("whoami")
        self.assertEqual(self.output.getvalue(), "student\n")

    def test_commands_without_arguments(self):
        for command in ("pwd", "whoami", "exit"):
            with self.subTest(command=command), self.assertRaises(ValueError):
                self.shell.execute(f"{command} extra")
        self.assertTrue(self.shell.running)

    def test_rev_utf8_multiple_and_empty_files(self):
        self.vfs.entries["/docs/text.txt"] = "abc\nПривет\n\n".encode()
        self.vfs.entries["/second.txt"] = b"123\r\n"
        self.vfs.entries["/empty.txt"] = b""
        self.shell.execute("cd /docs")
        self.shell.execute("rev text.txt ../second.txt ../empty.txt")
        self.assertEqual(self.output.getvalue(), "cba\nтевирП\n\n321\n")

    def test_rev_quoted_file(self):
        self.vfs.entries["/my docs/a.txt"] = b"hello"
        self.shell.execute('rev "/my docs/a.txt"')
        self.assertEqual(self.output.getvalue(), "olleh\n")

    def test_rev_stdin(self):
        with patch("sys.stdin", io.StringIO("one\ntwo\n")):
            self.shell.execute("rev")
        self.assertEqual(self.output.getvalue(), "eno\nowt\n")

    def test_rev_errors(self):
        for path in ("/missing", "/docs", "/docs/projects/demo/data.bin"):
            with self.subTest(path=path), self.assertRaises(ValueError):
                self.shell.execute(f"rev {path}")

    def test_missing_parent_and_file_with_trailing_slash(self):
        for path in ("/missing/..", "/docs/notes.txt/", "/docs/notes.txt/."):
            with self.subTest(path=path), self.assertRaises(ValueError):
                self.vfs.resolve(path)

    def test_commands_do_not_change_source_or_entries(self):
        source = ROOT / "examples/deep.csv"
        original = source.read_bytes()
        entries = dict(self.vfs.entries)
        for line in ("ls /", "cd /docs", "pwd", "rev notes.txt", "whoami"):
            self.shell.execute(line)
        self.assertEqual(source.read_bytes(), original)
        self.assertEqual(self.vfs.entries, entries)


if __name__ == "__main__":
    unittest.main()
