"""Exercise malformed datagrams, mismatched severity, duplicates and late packets over UDP."""

from pathlib import Path
import socket
import sqlite3
import subprocess
import sys
import tempfile
import time
import unittest
import uuid

from app.protocol import encode_record
from tests.test_integration import ROOT, find_available_five_ports


class ResilienceTests(unittest.TestCase):
    def test_reject_bad_datagrams_and_restore_gap(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = find_available_five_ports()
            db = Path(tmp) / "resilience.db"
            server = subprocess.Popen(
                [sys.executable, "-u", "-m", "app.server", "--bind", "127.0.0.1",
                 "--base-port", str(base), "--db", str(db), "--print-every", "0",
                 "--max-datagrams", "6"], cwd=ROOT,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            try:
                time.sleep(0.3)
                self.assertIsNone(server.poll())
                # Containerized test environments may isolate the test runner's
                # sockets from its subprocesses, so send through a client subprocess.
                sender_code = r"""
import socket, sys, time, uuid
from app.protocol import encode_record
base = int(sys.argv[1])
record = {"version": 1, "host_id": "h1", "session_id": str(uuid.uuid4()),
          "severity": "ERROR", "sequence": 1,
          "sent_ns": time.time_ns(), "message": "test"}
with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
    sock.sendto(b"broken json", ("127.0.0.1", base + 3))
    sock.sendto(encode_record(record), ("127.0.0.1", base + 0))
    for seq in (1, 3, 2, 2):
        record["sequence"] = seq
        record["sent_ns"] = time.time_ns()
        sock.sendto(encode_record(record), ("127.0.0.1", base + 3))
        time.sleep(0.015)
"""
                sent = subprocess.run([sys.executable, "-c", sender_code, str(base)],
                                      cwd=ROOT, capture_output=True, text=True, timeout=5)
                self.assertEqual(sent.returncode, 0, sent.stderr)
                output, _ = server.communicate(timeout=10)
                self.assertEqual(server.returncode, 0, output)
                for expected in ("datagrams=6", "stored=3", "invalid=2", "duplicates=1",
                                 "out_of_order=1", "apparent_gaps=0"):
                    self.assertIn(expected, output, output)
                with sqlite3.connect(str(db)) as conn:
                    found = [row[0] for row in conn.execute("SELECT sequence FROM logs ORDER BY sequence")]
                self.assertEqual(found, [1, 2, 3])
            finally:
                if server.poll() is None:
                    server.kill()
                    server.communicate(timeout=5)


if __name__ == "__main__":
    unittest.main()
