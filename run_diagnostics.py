"""Run one diagnostic cycle without changing the existing status reporter."""
import argparse
import os
import stat
from pathlib import Path
from poll_diagnostics import poll_once

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--key-file", required=True, type=Path)
    args = parser.parse_args()
    path = args.key_file
    fd = os.open(str(path), os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(fd, "r", encoding="ascii") as stream:
        info = os.fstat(stream.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
            raise SystemExit("Device key must be a private, owner-only regular file")
        key = stream.read(128).strip()
    publishable_key = "sb_publishable_30tdnZZRBpicllo00yPkhQ_6FUx1hCe"
    try:
        poll_once(key, publishable_key)
    except Exception as exc:
        # Do not log request bodies, credentials or server response contents.
        raise SystemExit("Diagnostic cycle failed: " + type(exc).__name__) from None

if __name__ == "__main__":
    main()
