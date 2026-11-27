import unittest
from unittest.mock import patch
from datetime import datetime, timedelta, timezone
from uuid import uuid4
from poll_previews import poll_once

class PreviewCycleTests(unittest.TestCase):
    def setUp(self):
        now = datetime.now(timezone.utc)
        self.request = {"id": str(uuid4()), "character": "female",
                        "created_at": (now-timedelta(seconds=5)).isoformat(),
                        "expires_at": (now+timedelta(minutes=5)).isoformat()}

    @patch("transport.rpc")
    def test_disabled_no_network(self, rpc):
        self.assertEqual(poll_once("key", "public", "1", enabled=False), 0)
        rpc.assert_not_called()

    @patch("character_preview.read_request_preview", side_effect=FileNotFoundError)
    @patch("capture_request.publish_request", return_value=True)
    @patch("transport.rpc")
    def test_wait_for_render(self, rpc, publish, read):
        rpc.return_value = [self.request]
        self.assertEqual(poll_once("key", "public", "1", enabled=True), 0)
        rpc.assert_called_once_with("dmx_poll_previews", "key", "public", None)
        publish.assert_called_once_with(self.request, "1", enabled=True)

    @patch("character_preview.read_request_preview")
    @patch("capture_request.publish_request", return_value=True)
    @patch("transport.rpc")
    def test_upload_cycle(self, rpc, publish, read):
        read.return_value = b"sample"
        rpc.side_effect = [[self.request], True, True, True]
        self.assertEqual(poll_once("key", "public", "1", enabled=True), 1)
        self.assertEqual([c.args[0] for c in rpc.call_args_list],
                         ["dmx_poll_previews", "dmx_initialize_preview",
                          "dmx_upload_preview_chunk", "dmx_finish_preview"])
        read.assert_called_once_with("female", self.request["id"], self.request["created_at"], "1")

    @patch("transport.rpc")
    def test_queue_limit(self, rpc):
        rpc.return_value = [self.request]*3
        with self.assertRaises(ValueError):
            poll_once("key", "public", "1", enabled=True)
