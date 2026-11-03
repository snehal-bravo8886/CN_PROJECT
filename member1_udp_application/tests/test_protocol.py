import unittest
import uuid

from app.protocol import (DEFAULT_SEVERITY_PORTS, MAX_DATAGRAM_BYTES,
                          ProtocolError, SEVERITIES, decode_record,
                          encode_record, severity_port)
from app.server import StreamState


class ProtocolTests(unittest.TestCase):
    def setUp(self):
        self.record = {"version": 1, "host_id": "h1", "session_id": str(uuid.uuid4()),
                       "severity": "CRITICAL", "sequence": 1,
                       "sent_ns": 1_000_000_000, "message": "Database unavailable"}

    def test_roundtrip(self):
        encoded = encode_record(self.record)
        self.assertLess(len(encoded), MAX_DATAGRAM_BYTES)
        self.assertEqual(decode_record(encoded, expected_severity="CRITICAL"), self.record)

    def test_five_ports(self):
        self.assertEqual(SEVERITIES, ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"))
        self.assertEqual(DEFAULT_SEVERITY_PORTS, {"DEBUG": 10000, "INFO": 10001,
                         "WARNING": 10002, "ERROR": 10003, "CRITICAL": 10004})
        self.assertEqual(severity_port("ERROR", 20000), 20003)

    def test_reject_malformed(self):
        for payload in (b"{broken", b"", b"x" * (MAX_DATAGRAM_BYTES + 1), b"\xff"):
            with self.subTest(payload=payload[:10]), self.assertRaises(ProtocolError):
                decode_record(payload)

    def test_reject_mismatched_port(self):
        with self.assertRaisesRegex(ProtocolError, "destination UDP port"):
            decode_record(encode_record(self.record), expected_severity="DEBUG")

    def test_reject_invalid_host(self):
        self.record["host_id"] = "../other host"
        with self.assertRaises(ProtocolError):
            encode_record(self.record)

    def test_reject_boolean_sequence(self):
        self.record["sequence"] = True
        with self.assertRaises(ProtocolError):
            encode_record(self.record)

    def test_reject_overlong_message(self):
        self.record["message"] = "a" * 701
        with self.assertRaises(ProtocolError):
            encode_record(self.record)

    def test_detect_gaps_and_late_packets(self):
        tracker = StreamState()
        self.assertEqual(tracker.observe(1), (False, False))
        self.assertEqual(tracker.observe(3), (False, False))
        self.assertEqual(tracker.apparent_missing, 1)
        self.assertEqual(tracker.observe(2), (False, True))
        self.assertEqual(tracker.apparent_missing, 0)
        self.assertEqual(tracker.observe(2), (True, False))
        self.assertEqual(tracker.out_of_order, 1)
        self.assertEqual(len(tracker.seen), 3)


if __name__ == "__main__":
    unittest.main()
