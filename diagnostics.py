"""Local-only diagnostics; no network, shell execution, or device secrets."""
import json
import hashlib
import os
import plistlib
from pathlib import Path

APP = Path("/Applications/DMX Studio.app")

def collect():
    contents = APP / "Contents"
    result = {"schema": 1, "installed": APP.is_dir(), "version": None,
              "build": None, "asset_counts": {}, "resource_bytes": 0, "model_inventory": []}
    if not result["installed"]:
        return result
    with (contents / "Info.plist").open("rb") as stream:
        info = plistlib.load(stream)
    result["version"] = info.get("CFBundleShortVersionString")
    result["build"] = info.get("CFBundleVersion")
    allowed = {".obj", ".dae", ".scn", ".usdz", ".glb", ".gltf",
               ".png", ".jpg", ".jpeg", ".json", ".fbx"}
    for root, dirs, files in os.walk(contents / "Resources", followlinks=False):
        dirs[:] = [d for d in dirs if not (Path(root) / d).is_symlink()]
        for name in files:
            path = Path(root) / name
            if path.is_symlink() or not path.is_file():
                continue
            suffix = path.suffix.lower()
            if suffix in allowed:
                result["asset_counts"][suffix] = result["asset_counts"].get(suffix, 0) + 1
                result["resource_bytes"] += path.stat().st_size
                if suffix in {".usdz", ".scn", ".glb", ".gltf", ".dae", ".obj", ".fbx"} and len(result["model_inventory"]) < 12:
                    digest = hashlib.sha256()
                    with path.open("rb") as stream:
                        for chunk in iter(lambda: stream.read(1048576), b""):
                            digest.update(chunk)
                    result["model_inventory"].append({
                        "name": name[:120], "bytes": path.stat().st_size,
                        "sha256": digest.hexdigest()})
    return result

if __name__ == "__main__":
    print(json.dumps(collect(), sort_keys=True))
