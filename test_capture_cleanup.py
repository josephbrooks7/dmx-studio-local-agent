import os
import tempfile
import time
import unittest
from pathlib import Path
from uuid import uuid4
from capture_request import cleanup_old_exports

class CleanupTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def make(self, name, old=True, mode=0o600):
        p = self.root / name
        p.write_bytes(b"test")
        p.chmod(mode)
        if old:
            t = time.time() - 90000
            os.utime(p, (t, t))
        return p

    def test_expired_triplet(self):
        uid = str(uuid4())
        paths = [self.make(uid+s) for s in (".png", ".json", ".request.json")]
        self.assertEqual(cleanup_old_exports(self.root), 3)
        self.assertTrue(all(not p.exists() for p in paths))

    def test_preserves_recent_and_unrelated(self):
        paths = [self.make(str(uuid4())+".png", old=False),
                 self.make("male.png"), self.make("show.json"),
                 self.make(str(uuid4())+".json", mode=0o644)]
        self.assertEqual(cleanup_old_exports(self.root), 0)
        self.assertTrue(all(p.exists() for p in paths))

    def test_preserves_symlink(self):
        target = self.make("unrelated.png")
        link = self.root / (str(uuid4())+".png")
        link.symlink_to(target)
        self.assertEqual(cleanup_old_exports(self.root), 0)
        self.assertTrue(link.is_symlink())
        self.assertTrue(target.exists())

    def test_batch_limit(self):
        for _ in range(70):
            self.make(str(uuid4())+".png")
        self.assertEqual(cleanup_old_exports(self.root), 64)
        self.assertEqual(len(list(self.root.iterdir())), 6)
