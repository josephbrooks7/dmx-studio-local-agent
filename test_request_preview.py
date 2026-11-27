import hashlib
import json
import os
import struct
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4
import character_preview as preview

class RequestPreviewTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        p = patch.object(preview, "EXPORT_DIR", root)
        p.start()
        self.addCleanup(p.stop)
        self.identifier = str(uuid4())
        now = datetime.now(timezone.utc)
        self.created = (now - timedelta(seconds=5)).isoformat()
        self.data = bytes.fromhex("89504e470d0a1a0a0000000d49484452") + struct.pack(">II", 768, 1024) + bytes(9)
        self.image = root / (self.identifier + ".png")
        self.manifest = root / (self.identifier + ".json")
        self.image.write_bytes(self.data)
        self.image.chmod(0o600)
        self.metadata = {"id": self.identifier, "character": "male", "build": "414",
                         "captured_at": now.isoformat(),
                         "sha256": hashlib.sha256(self.data).hexdigest()}
        self.write_manifest()

    def write_manifest(self):
        self.manifest.write_text(json.dumps(self.metadata))
        self.manifest.chmod(0o600)

    def read(self):
        return preview.read_request_preview("male", self.identifier, self.created, "414")

    def test_valid(self):
        self.assertEqual(self.read(), self.data)

    def test_mismatches(self):
        for key, value in [("id", str(uuid4())), ("character", "female"),
                           ("build", "413"), ("sha256", "0"*64),
                           ("captured_at", "2000-01-01T00:00:00+00:00")]:
            with self.subTest(key=key):
                original = self.metadata[key]
                self.metadata[key] = value
                self.write_manifest()
                with self.assertRaises(ValueError):
                    self.read()
                self.metadata[key] = original

    def test_stale_file(self):
        os.utime(self.image, (1, 1))
        with self.assertRaises(ValueError):
            self.read()

    def test_missing_manifest(self):
        self.manifest.unlink()
        with self.assertRaises(FileNotFoundError):
            self.read()

    def test_public_permissions(self):
        self.manifest.chmod(0o644)
        with self.assertRaises(ValueError):
            self.read()

    def test_corrupted_image(self):
        self.image.write_bytes(self.data[:-1] + b"x")
        with self.assertRaises(ValueError):
            self.read()
