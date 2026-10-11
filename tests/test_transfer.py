import io
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from shell import Shell
from vfs import load_vfs

ROOT = Path(__file__).resolve().parents[1]


class TransferTests(unittest.TestCase):
    def setUp(self):
        self.vfs = load_vfs(ROOT / "examples/deep.csv")
        self.shell = Shell(vfs=self.vfs, output=io.StringIO())

    def test_copy_file_to_new_name_and_directory(self):
        original = self.vfs.read_file("/docs/notes.txt")
        self.shell.execute("cp /docs/notes.txt /copy.txt")
        self.shell.execute('cp /copy.txt "/my docs"')
        self.assertEqual(self.vfs.read_file("/copy.txt"), original)
        self.assertEqual(self.vfs.read_file("/my docs/copy.txt"), original)
        self.assertEqual(self.vfs.read_file("/docs/notes.txt"), original)

    def test_copy_relative_and_quoted_paths(self):
        self.shell.execute('cd "/my docs"')
        self.shell.execute('cp readme.txt "../a b.txt"')
        self.assertEqual(
            self.vfs.read_file("/a b.txt"),
            self.vfs.read_file("/my docs/readme.txt"),
        )
        self.assertEqual(self.shell.cwd, "/my docs")

    def test_copy_overwrites_file(self):
        self.vfs.entries["/copy.txt"] = b"old"
        self.shell.execute("cp /docs/notes.txt /copy.txt")
        self.assertEqual(
            self.vfs.read_file("/copy.txt"),
            self.vfs.read_file("/docs/notes.txt"),
        )

    def test_copy_empty_and_binary_files(self):
        self.vfs.entries["/empty.txt"] = b""
        self.shell.execute("cp /empty.txt /empty-copy.txt")
        self.shell.execute("cp /docs/projects/demo/data.bin /binary.bin")
        self.assertEqual(self.vfs.read_file("/empty-copy.txt"), b"")
        self.assertEqual(self.vfs.read_file("/binary.bin"), b"\0\1\2\xff")

    def test_recursive_copy_and_directory_destination(self):
        self.shell.execute("cp -r /docs /backup")
        self.shell.execute('cp -r /docs/projects "/my docs"')
        for path, data in tuple(self.vfs.entries.items()):
            if path == "/docs" or path.startswith("/docs/"):
                self.assertEqual(self.vfs.entries["/backup" + path[5:]], data)
        self.assertEqual(
            self.vfs.read_file("/my docs/projects/demo/data.bin"),
            self.vfs.read_file("/docs/projects/demo/data.bin"),
        )

    def test_recursive_copy_merges_directories(self):
        self.vfs.entries["/backup"] = None
        self.vfs.entries["/backup/docs"] = None
        self.vfs.entries["/backup/docs/keep.txt"] = b"keep"
        self.shell.execute("cp -r /docs /backup")
        self.assertEqual(self.vfs.read_file("/backup/docs/keep.txt"), b"keep")
        self.assertEqual(
            self.vfs.read_file("/backup/docs/notes.txt"),
            self.vfs.read_file("/docs/notes.txt"),
        )

    def test_copy_errors_do_not_change_entries(self):
        commands = (
            "cp", "cp /docs", "cp a b c", "cp -r /docs",
            "cp /missing /new", "cp /docs /new",
            "cp /docs/notes.txt /missing/new",
            'cp /docs/notes.txt ""', "cp /docs/notes.txt /missing/",
            "cp /docs/notes.txt /docs/notes.txt",
            "cp -r /docs /docs/projects", "cp -r / /new",
            "cp -r /docs /docs/notes.txt",
        )
        original = dict(self.vfs.entries)
        for command in commands:
            with self.subTest(command=command), self.assertRaises(ValueError):
                self.shell.execute(command)
            self.assertEqual(self.vfs.entries, original)

    def test_copy_type_conflict_is_atomic(self):
        self.vfs.entries["/backup"] = None
        self.vfs.entries["/backup/docs"] = None
        self.vfs.entries["/backup/docs/projects"] = b"file"
        original = dict(self.vfs.entries)
        with self.assertRaises(ValueError):
            self.shell.execute("cp -r /docs /backup")
        self.assertEqual(self.vfs.entries, original)

    def test_copy_does_not_access_disk(self):
        original = (ROOT / "examples/deep.csv").read_bytes()
        with patch("pathlib.Path.open", side_effect=AssertionError):
            self.shell.execute("cp /docs/notes.txt /copy.txt")
        self.assertEqual((ROOT / "examples/deep.csv").read_bytes(), original)
        fresh = load_vfs(ROOT / "examples/deep.csv")
        self.assertNotIn("/copy.txt", fresh.entries)

    def test_move_file_to_new_name_and_directory(self):
        original = self.vfs.read_file("/docs/notes.txt")
        self.shell.execute("mv /docs/notes.txt /renamed.txt")
        self.assertNotIn("/docs/notes.txt", self.vfs.entries)
        self.shell.execute('mv /renamed.txt "/my docs"')
        self.assertNotIn("/renamed.txt", self.vfs.entries)
        self.assertEqual(self.vfs.read_file("/my docs/renamed.txt"), original)

    def test_move_relative_and_overwrite(self):
        self.vfs.entries["/old.txt"] = b"old"
        self.shell.execute("cd /docs")
        self.shell.execute("mv notes.txt ../old.txt")
        self.assertNotIn("/docs/notes.txt", self.vfs.entries)
        self.assertNotEqual(self.vfs.read_file("/old.txt"), b"old")
        self.assertEqual(self.shell.cwd, "/docs")

    def test_move_directory_updates_all_paths(self):
        original = dict(self.vfs.entries)
        self.shell.execute("mv /docs /renamed")
        for path, data in original.items():
            if path == "/docs" or path.startswith("/docs/"):
                self.assertNotIn(path, self.vfs.entries)
                self.assertEqual(self.vfs.entries["/renamed" + path[5:]], data)

    def test_move_current_directory_and_ancestor(self):
        self.shell.execute("cd /docs/projects/demo/src")
        self.shell.execute("mv /docs /renamed")
        self.assertEqual(self.shell.cwd, "/renamed/projects/demo/src")
        self.shell.execute('mv . "/my docs"')
        self.assertEqual(self.shell.cwd, "/my docs/src")
        self.shell.execute("rev main.txt")
        self.assertIn(".yrotcerid tsepeed", self.shell.output.getvalue())
        self.shell.execute("cd ..")
        self.assertEqual(self.shell.cwd, "/my docs")

    def test_move_directory_to_empty_existing_directory(self):
        self.vfs.entries["/backup"] = None
        self.vfs.entries["/backup/docs"] = None
        self.shell.execute("mv /docs /backup")
        self.assertNotIn("/docs", self.vfs.entries)
        self.assertEqual(
            self.vfs.read_file("/backup/docs/projects/demo/data.bin"),
            b"\0\1\2\xff",
        )

    def test_move_errors_do_not_change_entries_or_cwd(self):
        self.vfs.entries["/backup"] = None
        self.vfs.entries["/backup/docs"] = None
        self.vfs.entries["/backup/docs/keep.txt"] = b"keep"
        commands = (
            "mv", "mv /docs", "mv a b c", "mv /missing /new",
            "mv /docs/notes.txt /missing/new", 'mv /docs/notes.txt ""',
            "mv /docs/notes.txt /docs/notes.txt", "mv /docs /docs/projects",
            "mv / /new", "mv /docs /docs/notes.txt", "mv /docs /backup",
        )
        original = dict(self.vfs.entries)
        for command in commands:
            with self.subTest(command=command), self.assertRaises(ValueError):
                self.shell.execute(command)
            self.assertEqual(self.vfs.entries, original)
            self.assertEqual(self.shell.cwd, "/")

    def test_move_does_not_access_disk_and_restart_restores_data(self):
        original = (ROOT / "examples/deep.csv").read_bytes()
        with patch("pathlib.Path.open", side_effect=AssertionError):
            self.shell.execute("mv /docs /renamed")
        self.assertEqual((ROOT / "examples/deep.csv").read_bytes(), original)
        fresh = load_vfs(ROOT / "examples/deep.csv")
        self.assertIn("/docs/notes.txt", fresh.entries)
        self.assertNotIn("/renamed", fresh.entries)

    def test_move_empty_binary_and_quoted_name(self):
        self.vfs.entries["/empty.txt"] = b""
        self.shell.execute('mv /empty.txt "/my docs/empty file.txt"')
        self.shell.execute("mv /docs/projects/demo/data.bin /moved.bin")
        self.assertEqual(self.vfs.read_file("/my docs/empty file.txt"), b"")
        self.assertEqual(self.vfs.read_file("/moved.bin"), b"\0\1\2\xff")
        self.assertNotIn("/empty.txt", self.vfs.entries)
        self.assertNotIn("/docs/projects/demo/data.bin", self.vfs.entries)


if __name__ == "__main__":
    unittest.main()
