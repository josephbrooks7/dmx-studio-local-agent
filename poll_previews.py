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

def poll_once(device_key, publishable_key, build, *, enabled=False):
    """One bounded cycle; missing renders are deferred until a later poll."""
    if enabled is not True:
        return 0
    from transport import rpc
    from capture_request import publish_request
    from character_preview import read_request_preview
    def call(operation, fields=None):
        return rpc(operation, device_key, publishable_key, fields)
    requests = call("dmx_poll_previews")
    if not isinstance(requests, list) or len(requests) > 2:
        raise ValueError("Unexpected preview queue")
    completed = 0
    for request in requests:
        if not publish_request(request, build, enabled=True):
            continue
        try:
            if upload_request(request, build, call, enabled=True, reader=read_request_preview):
                completed += 1
        except FileNotFoundError:
            # The app has not published both files yet.
            continue
    return completed
