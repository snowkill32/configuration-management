import csv
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from vfs import load_vfs

ROOT = Path(__file__).resolve().parents[1]


class VFSTests(unittest.TestCase):
    def test_default(self):
        vfs = load_vfs()
        self.assertEqual(vfs.name, "vfs")
        self.assertEqual(vfs.entries, {"/": None})
        self.assertEqual(vfs.motd(), "")

    def test_minimal(self):
        vfs = load_vfs(ROOT / "examples/minimal.csv")
        self.assertEqual(vfs.entries, {"/": None})
        self.assertEqual(vfs.motd(), "")

    def test_files_and_motd(self):
        vfs = load_vfs(ROOT / "examples/files.csv")
        self.assertEqual(vfs.entries["/binary.bin"], bytes([0, 1, 2, 255]))
        self.assertEqual(vfs.entries["/empty.txt"], b"")
        self.assertEqual(vfs.entries["/numbers.txt"], b"one two three")
        self.assertIn("файла, текст", vfs.entries["/readme.txt"].decode())
        self.assertEqual(vfs.motd(), "Добро пожаловать в VFS files!")

    def test_deep_structure(self):
        vfs = load_vfs(ROOT / "examples/deep.csv")
        path = "/docs/projects/demo/src/main.txt"
        self.assertEqual(
            vfs.entries[path], b"Hello from the deepest directory."
        )
        self.assertIsNone(vfs.entries["/docs/projects/demo/src"])
        self.assertIn(path, vfs.describe())

    def test_memory_only(self):
        with TemporaryDirectory() as folder:
            path = Path(folder) / "vfs.csv"
            source = "path,type,encoding,data\n/a,file,utf-8,data\n"
            path.write_text(source, encoding="utf-8")
            original = path.read_bytes()
            vfs = load_vfs(path)
            vfs.entries["/a"] = b"changed"
            vfs.entries["/new"] = None
            self.assertEqual(path.read_bytes(), original)
            self.assertEqual(list(Path(folder).iterdir()), [path])

    def test_row_order_and_csv_quotes(self):
        with TemporaryDirectory() as folder:
            path = Path(folder) / "vfs.csv"
            with path.open("w", encoding="utf-8-sig", newline="") as target:
                writer = csv.writer(target)
                writer.writerow(["path", "type", "encoding", "data"])
                writer.writerow(["/docs/a", "file", "utf-8", 'a,"b"\nc'])
                writer.writerow(["/docs", "dir", "", ""])
            vfs = load_vfs(path)
            self.assertEqual(vfs.entries["/docs/a"], b'a,"b"\nc')

    def test_missing_file(self):
        with TemporaryDirectory() as folder:
            with self.assertRaises(FileNotFoundError):
                load_vfs(Path(folder) / "missing.csv")

    def test_invalid_csv(self):
        cases = [
            "", "wrong,header\n", 'path,type,encoding,data\n"unclosed',
            "path,type,encoding,data\n/a,file,utf-8\n",
            "path,type,encoding,data\nrelative,file,utf-8,data\n",
            "path,type,encoding,data\n/../a,file,utf-8,data\n",
            "path,type,encoding,data\n/a//b,file,utf-8,data\n",
            "path,type,encoding,data\n/a,unknown,,\n",
            "path,type,encoding,data\n/a,dir,utf-8,data\n",
            "path,type,encoding,data\n/a,file,hex,00\n",
            "path,type,encoding,data\n/a,file,base64,???\n",
            "path,type,encoding,data\n/a,file,utf-8,\n/a,dir,,\n",
            "path,type,encoding,data\n/missing/a,file,utf-8,data\n",
            "path,type,encoding,data\n/a,file,utf-8,\n/a/b,dir,,\n",
        ]
        with TemporaryDirectory() as folder:
            path = Path(folder) / "bad.csv"
            for source in cases:
                with self.subTest(source=source):
                    path.write_text(source, encoding="utf-8")
                    with self.assertRaises(ValueError):
                        load_vfs(path)

    def test_motd_must_be_text(self):
        with TemporaryDirectory() as folder:
            path = Path(folder) / "bad.csv"
            path.write_text(
                "path,type,encoding,data\n/motd,file,base64,/w==\n",
                encoding="utf-8",
            )
            with self.assertRaises(ValueError):
                load_vfs(path).motd()


if __name__ == "__main__":
    unittest.main()
