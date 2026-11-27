"""Read only explicitly exported Character Studio previews, never desktop screenshots."""
import os
import stat
import struct
from pathlib import Path

EXPORT_DIR = Path.home() / "Library" / "Application Support" / "DMX Studio" / "DiagnosticPreviews"
MAX_BYTES = 4 * 1024 * 1024
NAMES = {"male": "male.png", "female": "female.png"}

def read_preview(character):
    if character not in NAMES:
        raise ValueError("Unsupported character")
    path = EXPORT_DIR / NAMES[character]
    if any(parent.is_symlink() for parent in (EXPORT_DIR, EXPORT_DIR.parent)):
        raise ValueError("Invalid export directory")
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, "rb") as stream:
        info = os.fstat(stream.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_size > MAX_BYTES:
            raise ValueError("Invalid preview file")
        data = stream.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES or len(data) < 33 or data[:16] != b"\x89PNG\r\n\x1a\n\x00\x00\x00\x0dIHDR":
        raise ValueError("Invalid PNG")
    width, height = struct.unpack(">II", data[16:24])
    if not (1 <= width <= 4096 and 1 <= height <= 4096):
        raise ValueError("Invalid preview dimensions")
    return data
