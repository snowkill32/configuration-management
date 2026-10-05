"""Проверки XML, двоичных данных и работы только в памяти."""

from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from vfs import load_vfs

ROOT = Path(__file__).resolve().parents[1]


class VFSTests(unittest.TestCase):
    """Проверяет загрузку и валидацию виртуальной файловой системы."""

    def test_minimal(self):
        """Минимальный XML содержит только корневой каталог."""
        vfs = load_vfs(ROOT / "examples/minimal.xml")
        self.assertEqual(vfs.name, "minimal")
        self.assertEqual(vfs.entries, {"/": None})

    def test_text_and_binary(self):
        """Текст сохраняется как UTF-8, base64 дает исходные байты."""
        vfs = load_vfs(ROOT / "examples/files.xml")
        self.assertEqual(vfs.entries["/binary.bin"], bytes([0, 1, 2, 255]))
        self.assertEqual(vfs.entries["/empty.txt"], b"")
        self.assertEqual(vfs.entries["/numbers.txt"], b"one two three")
        self.assertIn("Пример", vfs.entries["/readme.txt"].decode("utf-8"))

    def test_deep_structure(self):
        """Вложенные каталоги и файлы загружаются без распаковки."""
        vfs = load_vfs(ROOT / "examples/deep.xml")
        path = "/docs/projects/demo/src/main.txt"
        self.assertEqual(
            vfs.entries[path], b"Hello from the deepest directory."
        )
        self.assertIsNone(vfs.entries["/docs/projects/demo/src"])
        self.assertIn(path, vfs.describe())

    def test_source_unchanged(self):
        """Изменение данных в памяти не меняет XML и не создает файлов."""
        with TemporaryDirectory() as folder:
            path = Path(folder) / "vfs.xml"
            xml = b'<vfs name="test"><file name="a.txt">data</file></vfs>'
            path.write_bytes(xml)
            vfs = load_vfs(path)
            vfs.entries["/a.txt"] = b"changed in memory"
            self.assertEqual(path.read_bytes(), xml)
            self.assertEqual(list(Path(folder).iterdir()), [path])

    def test_missing_file(self):
        """Отсутствующий XML приводит к ошибке чтения."""
        with TemporaryDirectory() as folder:
            with self.assertRaises(FileNotFoundError):
                load_vfs(Path(folder) / "missing.xml")

    def test_invalid_formats(self):
        """Поврежденные XML, пути и двоичные данные отклоняются."""
        cases = [
            "<vfs>",
            '<root name="bad" />',
            '<vfs name="" />',
            '<vfs name="bad"><unknown name="a" /></vfs>',
            '<vfs name="bad"><file name="../a" /></vfs>',
            '<vfs name="bad"><dir name=".." /></vfs>',
            '<vfs name="bad"><file name="a" /><dir name="a" /></vfs>',
            '<vfs name="bad"><file name="a" encoding="hex" /></vfs>',
            '<vfs name="bad"><file name="a" encoding="base64">'
            '???</file></vfs>',
            '<vfs name="bad"><file name="a"><dir name="b" />'
            '</file></vfs>',
            '<vfs name="bad"><dir name="a">text</dir></vfs>',
            '<vfs name="bad"><file name="a" mode="x" /></vfs>',
        ]
        with TemporaryDirectory() as folder:
            path = Path(folder) / "invalid.xml"
            for xml in cases:
                with self.subTest(xml=xml):
                    path.write_text(xml, encoding="utf-8")
                    with self.assertRaises(ValueError):
                        load_vfs(path)


if __name__ == "__main__":
    unittest.main()
