"""Actual localhost UDP client/server roundtrip with isolated ports and storage."""

import json
import os
from pathlib import Path
import socket
import sqlite3
import subprocess
import sys
import tempfile
import time
import unittest

from app.compare_results import compare
from app.protocol import SEVERITIES

ROOT = Path(__file__).resolve().parents[1]


def find_available_five_ports() -> int:
    # Bind all ports during discovery; release right before starting subprocess.
    for base in range(18000, 39000, 11):
        opened = []
        try:
            for port in range(base, base + 5):
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                opened.append(sock)
                sock.bind(("127.0.0.1", port))
            return base
        except OSError:
            pass
        finally:
            for sock in opened:
                sock.close()
    raise RuntimeError("could not find five contiguous UDP ports")


class IntegrationTests(unittest.TestCase):
    def test_two_clients_all_severities_and_database(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = find_available_five_ports()
            db_path = Path(tmp) / "collected.db"
            server = subprocess.Popen(
                [sys.executable, "-u", "-m", "app.server", "--bind", "127.0.0.1",
                 "--base-port", str(base), "--db", str(db_path), "--print-every", "0",
                 "--max-datagrams", "25"], cwd=ROOT, stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT, text=True)
            try:
                time.sleep(0.35)
                self.assertIsNone(server.poll(), "server stopped before test clients connected")
                summaries = []
                for host, count in (("host1", 15), ("host2", 10)):
                    summary = Path(tmp) / f"{host}.json"
                    result = subprocess.run(
                        [sys.executable, "-m", "app.client", "--server", "127.0.0.1",
                         "--base-port", str(base), "--host-id", host,
                         "--severity", "ALL", "--count", str(count),
                         "--interval-ms", "12", "--quiet", "--summary-file", str(summary)],
                        cwd=ROOT, text=True, capture_output=True, timeout=10)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertIn("[DONE]", result.stdout)
                    summaries.append(summary)
                output, _ = server.communicate(timeout=10)
                self.assertEqual(server.returncode, 0, output)
                self.assertIn("stored=25", output)
                with sqlite3.connect(str(db_path)) as conn:
                    rows = conn.execute("SELECT host_id, severity, COUNT(*) FROM logs GROUP BY host_id, severity").fetchall()
                self.assertEqual(len(rows), 10)
                expected = {"host1": 3, "host2": 2}
                for host, severity, count in rows:
                    self.assertIn(severity, SEVERITIES)
                    self.assertEqual(count, expected[host])
                report = compare(db_path, summaries)
                self.assertTrue(all(row["lost"] == 0 for row in report), report)
                self.assertEqual(sum(row["received"] for row in report), 25)
            finally:
                if server.poll() is None:
                    server.kill()
                    server.communicate(timeout=5)


if __name__ == "__main__":
    unittest.main()
