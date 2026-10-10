import base64
import binascii
import csv
from pathlib import Path, PurePosixPath

CSV_FIELDS = ("path", "type", "encoding", "data")


class VFS:
    def __init__(self, name, entries):
        self.name = name
        # None означает папку, bytes — содержимое файла, включая пустой.
        self.entries = entries

    def describe(self):
        lines = []
        for path, data in sorted(self.entries.items()):
            kind = "каталог" if data is None else f"файл, {len(data)} байт"
            lines.append(f"  {path}: {kind}")
        return "\n".join(lines)

    def motd(self):
        data = self.entries.get("/motd")
        if data is None:
            return ""
        try:
            return data.decode("utf-8-sig")
        except UnicodeError as error:
            raise ValueError("motd должен содержать текст UTF-8") from error


def validate_path(path):
    if not path.startswith("/") or path == "/":
        raise ValueError(f"ожидается абсолютный путь к файлу или папке: {path}")
    parts = path[1:].split("/")
    if any(part in ("", ".", "..") for part in parts):
        raise ValueError(f"недопустимый путь: {path}")
    if "\\" in path or "\0" in path:
        raise ValueError(f"недопустимый символ в пути: {path}")


def decode_data(encoding, data):
    if encoding == "utf-8":
        return data.encode("utf-8")
    if encoding != "base64":
        raise ValueError(f"неизвестная кодировка: {encoding}")
    try:
        return base64.b64decode("".join(data.split()), validate=True)
    except (binascii.Error, ValueError) as error:
        raise ValueError("неверные данные base64") from error


def add_record(row, entries):
    if len(row) != len(CSV_FIELDS):
        raise ValueError("ожидаются поля path,type,encoding,data")
    path, kind, encoding, data = row
    validate_path(path)
    if path in entries:
        raise ValueError(f"повторяющийся путь: {path}")
    if kind == "dir":
        if encoding or data:
            raise ValueError(f"папка не должна содержать данные: {path}")
        entries[path] = None
    elif kind == "file":
        entries[path] = decode_data(encoding, data)
    else:
        raise ValueError(f"неизвестный тип: {kind}")


def validate_parents(entries):
    for path in entries:
        if path == "/":
            continue
        parent = str(PurePosixPath(path).parent)
        if parent not in entries or entries[parent] is not None:
            raise ValueError(f"родительская папка отсутствует: {path}")


def load_vfs(path=None):
    entries = {"/": None}
    if path is None:
        return VFS("vfs", entries)
    path = Path(path)
    try:
        with path.open(encoding="utf-8-sig", newline="") as source:
            reader = csv.reader(source, strict=True)
            if next(reader, None) != list(CSV_FIELDS):
                raise ValueError("неверный заголовок CSV")
            for row in reader:
                if not row:
                    continue
                try:
                    add_record(row, entries)
                except ValueError as error:
                    raise ValueError(
                        f"строка CSV {reader.line_num}: {error}"
                    ) from error
    except csv.Error as error:
        raise ValueError(f"неверный CSV: {error}") from error
    # Проверяем родителей после чтения: порядок строк CSV не важен.
    validate_parents(entries)
    return VFS(path.stem, entries)
