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

    def require_exists(self, path):
        if path not in self.entries:
            raise ValueError(f"путь не найден: {path}")

    def require_directory(self, path):
        self.require_exists(path)
        if self.entries[path] is not None:
            raise ValueError(f"не каталог: {path}")

    def resolve(self, value, cwd="/"):
        if not value:
            raise ValueError("путь не должен быть пустым")
        path = "/" if value.startswith("/") else cwd
        for part in value.split("/"):
            if not part:
                continue
            self.require_directory(path)
            if part == ".":
                continue
            if part == "..":
                path = str(PurePosixPath(path).parent)
            else:
                path = path.rstrip("/") + "/" + part
            self.require_exists(path)
        if value.endswith("/"):
            self.require_directory(path)
        return path

    def list_directory(self, value=".", cwd="/"):
        path = self.resolve(value, cwd)
        if self.entries[path] is not None:
            return [PurePosixPath(path).name]
        # Показываем только прямых потомков, без содержимого вложенных папок.
        return sorted(
            PurePosixPath(item).name for item in self.entries
            if item != "/" and str(PurePosixPath(item).parent) == path
        )

    def read_file(self, value, cwd="/"):
        path = self.resolve(value, cwd)
        data = self.entries[path]
        if data is None:
            raise ValueError(f"ожидается файл, а не папка: {path}")
        return data

    def destination_path(self, value, source, cwd):
        if not value:
            raise ValueError("путь назначения не должен быть пустым")
        parent, separator, name = value.rpartition("/")
        if name in ("", ".", ".."):
            path = self.resolve(value, cwd)
        else:
            parent = (parent or "/") if separator else "."
            parent = self.resolve(parent, cwd)
            self.require_directory(parent)
            path = parent.rstrip("/") + "/" + name
            validate_path(path)
        if path in self.entries and self.entries[path] is None:
            path = path.rstrip("/") + "/" + PurePosixPath(source).name
        return path

    def prepare_transfer(self, value, destination, cwd):
        source = self.resolve(value, cwd)
        if source == "/":
            raise ValueError("корень нельзя копировать или перемещать")
        target = self.destination_path(destination, source, cwd)
        if source == target:
            raise ValueError("исходный путь и назначение совпадают")
        if target.startswith(source + "/"):
            raise ValueError("папку нельзя поместить внутрь самой себя")
        return source, target

    def transfer_entries(self, source, target):
        # У всех вложенных записей заменяем начало пути на новое.
        return {
            target + path[len(source):]: data
            for path, data in self.entries.items()
            if path == source or path.startswith(source + "/")
        }

    def check_replacements(self, changes):
        for path, data in changes.items():
            if path in self.entries:
                old_is_directory = self.entries[path] is None
                if (data is None) != old_is_directory:
                    raise ValueError(f"тип назначения не совпадает: {path}")

    def copy(self, value, destination, cwd="/", recursive=False):
        source, target = self.prepare_transfer(value, destination, cwd)
        if self.entries[source] is None and not recursive:
            raise ValueError("для копирования папки нужен cp -r")
        changes = self.transfer_entries(source, target)
        # Сначала проверяем все записи, чтобы ошибка не оставила часть копии.
        self.check_replacements(changes)
        self.entries.update(changes)

    def move(self, value, destination, cwd="/"):
        source, target = self.prepare_transfer(value, destination, cwd)
        if target in self.entries and self.entries[target] is None:
            if self.list_directory(target):
                raise ValueError(f"папка назначения не пуста: {target}")
        changes = self.transfer_entries(source, target)
        self.check_replacements(changes)
        for path in list(self.entries):
            if path == source or path.startswith(source + "/"):
                del self.entries[path]
        self.entries.update(changes)
        # Если перенесли текущую папку или её родителя, обновляем cwd.
        if cwd == source or cwd.startswith(source + "/"):
            cwd = target + cwd[len(source):]
        return cwd


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
