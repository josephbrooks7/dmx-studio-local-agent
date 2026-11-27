"""Preview upload orchestration; not wired into the installed agent."""
from datetime import datetime, timezone
from uuid import UUID
from preview_transfer import encode_preview

def upload_request(request, build, call, *, enabled=False, reader=None):
    if enabled is not True:
        return False
    request_id = str(UUID(request["id"]))
    character = request["character"]
    if character not in ("male", "female"):
        raise ValueError("Invalid character")
    expiry = datetime.fromisoformat(request["expires_at"].replace("Z", "+00:00"))
    if expiry <= datetime.now(timezone.utc):
        return False
    # Reader must supply a request-bound fresh render, not an old cached PNG.
    if reader is None:
        return False
    data = reader(character, request_id, request["created_at"], build)
    manifest, chunks = encode_preview(data)
    if call("dmx_initialize_preview", {"p_id": request_id, "p_bytes": manifest["bytes"],
            "p_sha256": manifest["sha256"], "p_build": build}) is not True:
        return False
    for index, payload in chunks:
        if datetime.now(timezone.utc) >= expiry:
            return False
        if call("dmx_upload_preview_chunk", {"p_id": request_id, "p_index": index,
                "p_payload": payload}) is not True:
            return False
    return call("dmx_finish_preview", {"p_id": request_id}) is True
