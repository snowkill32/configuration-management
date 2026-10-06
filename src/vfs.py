import base64
import binascii
import xml.etree.ElementTree as ET


class VFS:
    def __init__(self, name, entries):
        self.name = name
        # В словаре None означает папку, а bytes — содержимое файла.
        self.entries = entries

    def describe(self):
        lines = []
        for path, data in sorted(self.entries.items()):
            kind = "каталог" if data is None else f"файл, {len(data)} байт"
            lines.append(f"  {path}: {kind}")
        return "\n".join(lines)


def file_data(element):
    if len(element):
        raise ValueError("файл не может содержать вложенные элементы")
    text = element.text or ""
    encoding = element.get("encoding", "utf-8")
    if encoding == "utf-8":
        return text.encode("utf-8")
    if encoding != "base64":
        raise ValueError(f"неизвестная кодировка файла: {encoding}")
    try:
        # Убираем пробелы и переносы перед чтением данных base64.
        return base64.b64decode("".join(text.split()), validate=True)
    except (binascii.Error, ValueError) as error:
        raise ValueError("неверные данные base64") from error


def validate_node(element):
    name = element.get("name", "")
    if not name or name in (".", "..") or any(c in name for c in "/\\\0"):
        raise ValueError(f"недопустимое имя: {name!r}")
    if element.tag not in ("dir", "file"):
        raise ValueError(f"неизвестный элемент: {element.tag}")
    allowed = {"name", "encoding"} if element.tag == "file" else {"name"}
    if set(element.attrib) - allowed:
        raise ValueError(f"неизвестные атрибуты: {name}")
    return name


def add_node(element, parent, entries):
    name = validate_node(element)
    path = parent.rstrip("/") + "/" + name
    if path in entries:
        raise ValueError(f"повторяющийся путь: {path}")
    if element.tag == "file":
        entries[path] = file_data(element)
    else:
        if (element.text or "").strip():
            raise ValueError(f"каталог содержит текст: {path}")
        entries[path] = None
        for child in element:
            # Вызываем эту же функцию для содержимого вложенной папки.
            add_node(child, path, entries)
    if (element.tail or "").strip():
        raise ValueError(f"текст вне файла: {path}")


def load_vfs(path):
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as error:
        raise ValueError(f"неверный XML: {error}") from error
    name = root.get("name", "").strip()
    if root.tag != "vfs" or not name or set(root.attrib) != {"name"}:
        raise ValueError('ожидается корневой элемент <vfs name="имя">')
    if (root.text or "").strip():
        raise ValueError("корневой каталог содержит текст")
    entries = {"/": None}
    for element in root:
        add_node(element, "/", entries)
    return VFS(name, entries)
