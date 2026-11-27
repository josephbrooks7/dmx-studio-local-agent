import json
import unittest
from unittest.mock import patch
import poll_diagnostics
from requests import handle

JOB = "12345678-1234-4234-8234-123456789abc"

class DiagnosticTests(unittest.TestCase):
    def test_reject_unknown_operation(self):
        with self.assertRaises(ValueError):
            handle(json.dumps({"id": JOB, "operation": "shell"}).encode())

    def test_reject_extra_fields(self):
        with self.assertRaises(ValueError):
            handle(json.dumps({"id": JOB, "operation": "inspect_bundle", "path": "/"}).encode())

    @patch("poll_diagnostics.rpc", return_value=None)
    def test_empty_queue(self, rpc):
        self.assertFalse(poll_diagnostics.poll_once("0"*64, "test"))
        rpc.assert_called_once()

    @patch("requests.collect", return_value={"installed": True})
    @patch("poll_diagnostics.rpc", side_effect=[{"id": JOB, "operation": "inspect_bundle"}, True])
    def test_round_trip(self, rpc, collect):
        self.assertTrue(poll_diagnostics.poll_once("0"*64, "test"))
        collect.assert_called_once()
        self.assertEqual(rpc.call_args.args[3], {"p_id": JOB, "p_result": {"installed": True}})

if __name__ == "__main__":
    unittest.main()
