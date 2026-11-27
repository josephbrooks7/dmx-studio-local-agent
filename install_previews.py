"""Install a separate opt-in character preview service on macOS."""
import argparse
import os
import plistlib
import stat
import subprocess
import sys
from pathlib import Path

LABEL = "com.dmxstudio.previews"

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--key-file", required=True, type=Path)
    parser.add_argument("--enable-character-previews", action="store_true", required=True)
    args = parser.parse_args()
    if sys.platform != "darwin":
        raise SystemExit("macOS required")
    key = args.key_file.expanduser().absolute()
    info = key.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
        raise SystemExit("Expected private device key")
    root = Path(__file__).resolve().parent
    subprocess.run(["/usr/bin/python3", "-m", "unittest", "discover", "-v"], cwd=root, check=True)
    directory = Path.home() / "Library" / "LaunchAgents"
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / (LABEL + ".plist")
    config = {"Label": LABEL, "ProgramArguments": ["/usr/bin/python3",
        str(root / "run_previews.py"), "--key-file", str(key),
        "--enable-character-previews"], "RunAtLoad": True, "StartInterval": 120}
    fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "wb") as stream:
        plistlib.dump(config, stream)
    try:
        subprocess.run(["/bin/launchctl", "bootstrap", "gui/" + str(os.getuid()), str(target)], check=True)
    except subprocess.CalledProcessError:
        target.unlink()
        raise
    print("Preview service registered. Existing diagnostics unchanged.")

if __name__ == "__main__":
    main()
