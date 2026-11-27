import unittest
from preview_transfer import encode_preview, decode_preview, CHUNK_BYTES
from character_preview import MAX_BYTES

class TransferTests(unittest.TestCase):
    def test_roundtrip(self):
        data = b"x" * (CHUNK_BYTES * 2 + 17)
        manifest, chunks = encode_preview(data)
        self.assertEqual(decode_preview(manifest, chunks), data)

    def test_missing_chunk(self):
        manifest, chunks = encode_preview(b"x" * (CHUNK_BYTES + 1))
        with self.assertRaises(ValueError):
            decode_preview(manifest, list(chunks)[:-1])

    def test_reordered(self):
        manifest, chunks = encode_preview(b"x" * (CHUNK_BYTES + 1))
        with self.assertRaises(ValueError):
            decode_preview(manifest, reversed(list(chunks)))

    def test_corrupted(self):
        manifest, chunks = encode_preview(b"abc")
        with self.assertRaises(ValueError):
            decode_preview(manifest, [(0, "YWJk")])

    def test_oversized(self):
        with self.assertRaises(ValueError):
            encode_preview(b"x" * (MAX_BYTES + 1))

    def test_extra_chunk(self):
        manifest, chunks = encode_preview(b"abc")
        with self.assertRaises(ValueError):
            decode_preview(manifest, list(chunks) + [(1, "YWJj")])

if __name__ == "__main__":
    unittest.main()
