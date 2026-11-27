import struct
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import character_preview as preview

class PreviewTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        p = patch.object(preview, "EXPORT_DIR", self.root)
        p.start()
        self.addCleanup(p.stop)

    def test_header(self):
        data = bytes.fromhex("89504e470d0a1a0a0000000d49484452") + struct.pack(">II", 640, 480) + bytes(9)
        (self.root / "male.png").write_bytes(data)
        self.assertEqual(preview.read_preview("male"), data)

    def test_invalid_name(self):
        with self.assertRaises(ValueError):
            preview.read_preview("../desktop")

    def test_invalid_header(self):
        (self.root / "female.png").write_bytes(b"not a png")
        with self.assertRaises(ValueError):
            preview.read_preview("female")

    def test_oversized(self):
        with (self.root / "male.png").open("wb") as stream:
            stream.truncate(preview.MAX_BYTES + 1)
        with self.assertRaises(ValueError):
            preview.read_preview("male")

    def test_symlink(self):
        (self.root / "male.png").symlink_to("/etc/passwd")
        with self.assertRaises(OSError):
            preview.read_preview("male")

if __name__ == "__main__":
    unittest.main()
