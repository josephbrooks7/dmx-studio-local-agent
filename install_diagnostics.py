"""Install a separate user-level LaunchAgent from a reviewed local checkout."""
import argparse
import os
import plistlib
import stat
import subprocess
import sys
from pathlib import Path

LABEL = "com.dmxstudio.diagnostics"

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--key-file", required=True, type=Path)
    args = parser.parse_args()
    key = args.key_file.expanduser().absolute()
    info = key.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
        raise SystemExit("Expected owner-only device key file")
    root = Path(__file__).resolve().parent
    if sys.platform != "darwin":
        raise SystemExit("macOS required")
    subprocess.run(["/usr/bin/python3", "-m", "unittest", "test_diagnostics"], cwd=str(root), check=True)
    directory = Path.home() / "Library" / "LaunchAgents"
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / (LABEL + ".plist")
    config = {"Label": LABEL, "ProgramArguments": ["/usr/bin/python3",
        str(root / "run_diagnostics.py"), "--key-file", str(key)],
        "RunAtLoad": True, "StartInterval": 60}
    # Exclusive creation prevents overwriting an existing installation.
    fd = os.open(str(target), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "wb") as stream:
        plistlib.dump(config, stream)
    domain = "gui/" + str(os.getuid())
    try:
        subprocess.run(["/bin/launchctl", "bootstrap", domain, str(target)], check=True)
    except subprocess.CalledProcessError:
        target.unlink()
        raise
    print("Diagnostic service registered. Existing version reporter unchanged.")

if __name__ == "__main__":
    main()
