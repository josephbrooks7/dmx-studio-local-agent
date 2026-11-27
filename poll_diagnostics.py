"""One diagnostic polling cycle. No arbitrary command execution."""
import json
from requests import handle
from transport import rpc

def poll_once(device_key, publishable_key):
    request = rpc("dmx_claim_diagnostic", device_key, publishable_key)
    if request is None:
        return False
    if not isinstance(request, dict):
        raise ValueError("Unexpected diagnostic response")
    result = handle(json.dumps(request).encode("utf-8"))
    acknowledged = rpc("dmx_finish_diagnostic", device_key, publishable_key,
                       {"p_id": result["id"], "p_result": result["result"]})
    if acknowledged is not True:
        raise RuntimeError("Diagnostic result not acknowledged")
    return True
