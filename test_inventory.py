import hashlib
import plistlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import diagnostics

class InventoryTests(unittest.TestCase):
    def test_bundle(self):
        with tempfile.TemporaryDirectory() as directory:
            app = Path(directory) / "DMX Studio.app"
            resources = app / "Contents" / "Resources"
            resources.mkdir(parents=True)
            with (app / "Contents" / "Info.plist").open("wb") as stream:
                plistlib.dump({"CFBundleShortVersionString": "test", "CFBundleVersion": "1"}, stream)
            data = b"model fixture"
            (resources / "character.usdz").write_bytes(data)
            (resources / "alias.usdz").symlink_to(resources / "character.usdz")
            with patch.object(diagnostics, "APP", app):
                result = diagnostics.collect()
            self.assertEqual(result["asset_counts"], {".usdz": 1})
            self.assertEqual(result["model_inventory"], [{"name": "character.usdz", "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}])

if __name__ == "__main__":
    unittest.main()
