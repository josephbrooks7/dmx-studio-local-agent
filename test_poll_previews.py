import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock
from uuid import uuid4
from poll_previews import upload_request

class UploadTests(unittest.TestCase):
    def setUp(self):
        now = datetime.now(timezone.utc)
        self.request = {"id": str(uuid4()), "character": "male",
                        "created_at": now.isoformat(),
                        "expires_at": (now + timedelta(minutes=10)).isoformat()}
        self.call = Mock(return_value=True)
        self.reader = Mock(return_value=b"x" * 4000)

    def test_disabled(self):
        self.assertFalse(upload_request(self.request, "1", self.call, reader=self.reader))
        self.call.assert_not_called()
        self.reader.assert_not_called()

    def test_expired(self):
        self.request["expires_at"] = "2000-01-01T00:00:00+00:00"
        self.assertFalse(upload_request(self.request, "1", self.call, enabled=True, reader=self.reader))
        self.reader.assert_not_called()
        self.call.assert_not_called()

    def test_success(self):
        self.assertTrue(upload_request(self.request, "1", self.call, enabled=True, reader=self.reader))
        self.assertEqual([c.args[0] for c in self.call.call_args_list],
            ["dmx_initialize_preview", "dmx_upload_preview_chunk", "dmx_upload_preview_chunk", "dmx_finish_preview"])
        self.reader.assert_called_once_with("male", self.request["id"], self.request["created_at"], "1")

    def test_failed_chunk(self):
        self.call.side_effect = [True, False]
        self.assertFalse(upload_request(self.request, "1", self.call, enabled=True, reader=self.reader))
        self.assertEqual(self.call.call_count, 2)

    def test_missing_reader(self):
        self.assertFalse(upload_request(self.request, "1", self.call, enabled=True))
        self.call.assert_not_called()
