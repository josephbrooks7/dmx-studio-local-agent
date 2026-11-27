"""Transport for diagnostic RPCs. Server endpoints must be deployed separately."""
import json
import re
import urllib.request
from urllib.parse import urlsplit

BASE = "https://ihtmurlzfwlwzxrmwtqt.supabase.co/rest/v1/rpc/"
MAX_RESPONSE = 16384

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

def rpc(operation, key, publishable_key, fields=None):
    if operation not in ("dmx_claim_diagnostic", "dmx_finish_diagnostic",
                         "dmx_poll_previews", "dmx_initialize_preview",
                         "dmx_upload_preview_chunk", "dmx_finish_preview"):
        raise ValueError("Unsupported RPC")
    if not re.fullmatch(r"[0-9a-f]{64}", key):
        raise ValueError("Invalid device key")
    payload = dict(fields or {})
    payload["p_key"] = key
    data = json.dumps(payload, allow_nan=False).encode("utf-8")
    if len(data) > MAX_RESPONSE:
        raise ValueError("Payload too large")
    req = urllib.request.Request(BASE + operation, data=data,
        headers={"apikey": publishable_key, "Content-Type": "application/json"},
        method="POST")
    opener = urllib.request.build_opener(NoRedirect())
    with opener.open(req, timeout=15) as response:
        raw = response.read(MAX_RESPONSE + 1)
    if len(raw) > MAX_RESPONSE:
        raise ValueError("Response too large")
    return json.loads(raw)
