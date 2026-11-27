"""Protocol handler for approved DMX diagnostics; transport is separate."""
import json
import uuid
from diagnostics import collect

MAX_REQUEST_BYTES = 2048

def handle(raw):
    if not isinstance(raw, bytes) or len(raw) > MAX_REQUEST_BYTES:
        raise ValueError("Invalid request size")
    request = json.loads(raw)
    if not isinstance(request, dict) or set(request) != {"id", "operation"}:
        raise ValueError("Invalid request fields")
    request_id = str(uuid.UUID(request["id"]))
    if request["operation"] != "inspect_bundle":
        raise ValueError("Unsupported operation")
    return {"id": request_id, "operation": "inspect_bundle",
            "result": collect()}
