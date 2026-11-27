"""Publish narrowly scoped capture requests for the app; never launch commands."""
import json
import os
import stat
import tempfile
from datetime import datetime, timezone
from uuid import UUID
from character_preview import EXPORT_DIR

def publish_request(request, build, *, enabled=False):
    if enabled is not True:
        return False
    identifier = str(UUID(request["id"]))
    character = request["character"]
    if character not in ("male", "female") or not isinstance(build, str) or not 0 < len(build) <= 64:
        raise ValueError("Invalid capture request")
    created = datetime.fromisoformat(request["created_at"].replace("Z", "+00:00"))
    expiry = datetime.fromisoformat(request["expires_at"].replace("Z", "+00:00"))
    now = datetime.now(timezone.utc)
    if not created <= now < expiry:
        return False
    root = EXPORT_DIR
    if root.is_symlink() or root.parent.is_symlink():
        raise ValueError("Invalid directory")
    root.mkdir(mode=0o700, parents=True, exist_ok=True)
    info = root.lstat()
    if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
        raise ValueError("Expected private directory")
    payload = {"id": identifier, "character": character, "build": build,
               "created_at": request["created_at"], "expires_at": request["expires_at"]}
    target = root / (identifier + ".request.json")
    fd, temporary = tempfile.mkstemp(prefix=".capture-", dir=root)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(payload, stream, allow_nan=False)
        os.replace(temporary, target)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return True
