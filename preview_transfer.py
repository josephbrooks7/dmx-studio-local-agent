"""Transport-independent preview encoding; no network or credentials."""
import base64
import hashlib
from character_preview import MAX_BYTES

CHUNK_BYTES = 3072

def encode_preview(data):
    if not isinstance(data, bytes) or not 0 < len(data) <= MAX_BYTES:
        raise ValueError("Invalid preview size")
    return {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(),
            "chunks": (len(data) + CHUNK_BYTES - 1) // CHUNK_BYTES}, (
        (index // CHUNK_BYTES, base64.b64encode(data[index:index + CHUNK_BYTES]).decode("ascii"))
        for index in range(0, len(data), CHUNK_BYTES))

def decode_preview(manifest, chunks):
    size = manifest["bytes"]
    count = manifest["chunks"]
    if type(size) is not int or not 0 < size <= MAX_BYTES or count != (size + CHUNK_BYTES - 1) // CHUNK_BYTES:
        raise ValueError("Invalid manifest")
    output = bytearray()
    for expected, (index, encoded) in enumerate(chunks):
        if expected >= count or index != expected or len(encoded) > 4096:
            raise ValueError("Invalid chunk")
        part = base64.b64decode(encoded, validate=True)
        if len(part) != min(CHUNK_BYTES, size - len(output)):
            raise ValueError("Invalid chunk size")
        output.extend(part)
    if len(output) != size or hashlib.sha256(output).hexdigest() != manifest["sha256"]:
        raise ValueError("Preview integrity mismatch")
    return bytes(output)
