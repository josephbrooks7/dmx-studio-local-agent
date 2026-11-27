"""Run a single opt-in preview cycle; existing diagnostics remain separate."""
import argparse
import os
import stat
from pathlib import Path
from diagnostics import collect
from poll_previews import poll_once

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--key-file", required=True, type=Path)
    parser.add_argument("--enable-character-previews", action="store_true")
    args = parser.parse_args()
    if not args.enable_character_previews:
        return
    try:
        fd = os.open(args.key_file, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        with os.fdopen(fd, "r", encoding="ascii") as stream:
            info = os.fstat(stream.fileno())
            if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
                raise ValueError("Invalid key file")
            key = stream.read(128).strip()
        status = collect()
        build = status.get("build")
        if not status.get("installed") or not isinstance(build, str) or not build:
            return
        poll_once(key, "sb_publishable_30tdnZZRBpicllo00yPkhQ_6FUx1hCe", build, enabled=True)
    except Exception as exc:
        raise SystemExit("Preview cycle failed: " + type(exc).__name__) from None

if __name__ == "__main__":
    main()
