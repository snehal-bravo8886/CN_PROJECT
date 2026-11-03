"""Central UDP log collector; uses raw sockets, selectors, and SQLite."""

import argparse
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
import selectors
import socket
import sqlite3
import time

from .protocol import (DEFAULT_BASE_PORT, MAX_DATAGRAM_BYTES, ProtocolError,
                       SEVERITIES, decode_record, severity_port, validate_base_port)


@dataclass
class StreamState:
    seen: set[int] = field(default_factory=set)
    maximum: int = 0
    out_of_order: int = 0

    def observe(self, seq: int) -> tuple[bool, bool]:
        """Return (duplicate, out_of_order). Missing counts can shrink after late arrivals."""
        if seq in self.seen:
            return True, False
        late = seq < self.maximum
        if late:
            self.out_of_order += 1
        self.seen.add(seq)
        self.maximum = max(self.maximum, seq)
        return False, late

    @property
    def apparent_missing(self) -> int:
        # Every severity stream begins at sequence 1. Tail loss is not observable here.
        return self.maximum - len(self.seen)


class UDPLogServer:
    def __init__(self, *, bind: str = "0.0.0.0", base_port: int = DEFAULT_BASE_PORT,
                 db_path: str = "logs.db", print_every: int = 1, stats_interval: float = 5.0,
                 max_datagrams: int = 0):
        validate_base_port(base_port)
        if print_every < 0 or stats_interval <= 0 or max_datagrams < 0:
            raise ValueError("--print-every >= 0, --stats-interval > 0, --max-datagrams >= 0 required")
        self.bind = bind
        self.base_port = base_port
        self.db_path = Path(db_path)
        self.print_every = print_every
        self.stats_interval = stats_interval
        self.max_datagrams = max_datagrams
        self.selector = selectors.DefaultSelector()
        self.conn: sqlite3.Connection | None = None
        self.streams: dict[tuple[str, str, str], StreamState] = defaultdict(StreamState)
        self.received_by_severity = {sev: 0 for sev in SEVERITIES}
        self.datagrams = 0
        self.invalid = 0
        self.duplicates = 0
        self.out_of_order = 0
        self.pending_writes = 0
        self.last_commit = time.monotonic()

    def setup(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA synchronous=NORMAL")
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                host_id TEXT NOT NULL,
                session_id TEXT NOT NULL,
                severity TEXT NOT NULL,
                sequence INTEGER NOT NULL,
                sent_ns INTEGER NOT NULL,
                received_ns INTEGER NOT NULL,
                delay_ms REAL NOT NULL,
                source_ip TEXT NOT NULL,
                source_port INTEGER NOT NULL,
                message TEXT NOT NULL,
                UNIQUE(host_id, session_id, severity, sequence)
            );
            CREATE INDEX IF NOT EXISTS idx_logs_host_severity ON logs(host_id, severity, received_ns);
            CREATE INDEX IF NOT EXISTS idx_logs_session_severity ON logs(session_id, severity);
        """)
        # One socket per class: OpenFlow matches UDP destination port to the queue.
        try:
            for severity in SEVERITIES:
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                try:
                    sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 1024 * 1024)
                    sock.bind((self.bind, severity_port(severity, self.base_port)))
                    sock.setblocking(False)
                    self.selector.register(sock, selectors.EVENT_READ, severity)
                except Exception:
                    sock.close()
                    raise
        except Exception:
            self.close()
            raise
        print(f"[READY] UDP server listening on {self.bind}, ports " +
              ", ".join(f"{sev}={severity_port(sev, self.base_port)}" for sev in SEVERITIES), flush=True)
        print(f"[STORAGE] SQLite: {self.db_path}", flush=True)

    def process_datagram(self, payload: bytes, address: tuple[str, int], severity: str, received_ns: int) -> None:
        assert self.conn is not None
        try:
            record = decode_record(payload, expected_severity=severity)
        except ProtocolError as exc:
            self.invalid += 1
            print(f"[DROP] {address[0]}:{address[1]} target={severity}: {exc}", flush=True)
            return
        key = (record["host_id"], record["session_id"], severity)
        state = self.streams[key]
        duplicate, late = state.observe(record["sequence"])
        if duplicate:
            self.duplicates += 1
            return
        delay_ms = (received_ns - record["sent_ns"]) / 1_000_000
        cursor = self.conn.execute("""
            INSERT OR IGNORE INTO logs (
              host_id, session_id, severity, sequence, sent_ns, received_ns,
              delay_ms, source_ip, source_port, message
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (record["host_id"], record["session_id"], severity,
              record["sequence"], record["sent_ns"], received_ns, delay_ms,
              address[0], address[1], record["message"]))
        if cursor.rowcount == 0:  # Duplicate seen before server restarted.
            self.duplicates += 1
            return
        self.received_by_severity[severity] += 1
        self.pending_writes += 1
        if late:
            self.out_of_order += 1
        if self.print_every and sum(self.received_by_severity.values()) % self.print_every == 0:
            print(f"[RECV] {record['host_id']} {severity:8} seq={record['sequence']:<5} "
                  f"delay_ms={delay_ms:.3f} missing_so_far={state.apparent_missing}", flush=True)

    def commit_if_due(self, force: bool = False) -> None:
        if self.conn and self.pending_writes and (force or self.pending_writes >= 100 or
                                                   time.monotonic() - self.last_commit >= 0.5):
            self.conn.commit()
            self.pending_writes = 0
            self.last_commit = time.monotonic()

    def print_stats(self) -> None:
        missing = sum(state.apparent_missing for state in self.streams.values())
        print(f"[STATS] datagrams={self.datagrams} stored={sum(self.received_by_severity.values())} "
              f"invalid={self.invalid} duplicates={self.duplicates} "
              f"out_of_order={self.out_of_order} apparent_gaps={missing} "
              f"counts={self.received_by_severity}", flush=True)

    def serve_forever(self) -> None:
        self.setup()
        last_stats = time.monotonic()
        try:
            while not self.max_datagrams or self.datagrams < self.max_datagrams:
                for key, _ in self.selector.select(timeout=0.15):
                    sock = key.fileobj
                    severity = key.data
                    # Limit per-socket batch to prevent starvation of other severity ports.
                    for _ in range(64):
                        try:
                            payload, address = sock.recvfrom(max(8192, MAX_DATAGRAM_BYTES + 1))
                        except BlockingIOError:
                            break
                        received_ns = time.time_ns()
                        self.datagrams += 1
                        self.process_datagram(payload, address, severity, received_ns)
                        if self.max_datagrams and self.datagrams >= self.max_datagrams:
                            break
                    if self.max_datagrams and self.datagrams >= self.max_datagrams:
                        break
                self.commit_if_due()
                if time.monotonic() - last_stats >= self.stats_interval:
                    self.print_stats()
                    last_stats = time.monotonic()
        except KeyboardInterrupt:
            print("\n[STOP] Interrupted by operator", flush=True)
        finally:
            self.commit_if_due(force=True)
            self.print_stats()
            self.close()

    def close(self) -> None:
        for key in list(self.selector.get_map().values()):
            try:
                self.selector.unregister(key.fileobj)
            except Exception:
                pass
            key.fileobj.close()
        self.selector.close()
        if self.conn is not None:
            self.conn.commit()
            self.conn.close()
            self.conn = None


def main() -> None:
    parser = argparse.ArgumentParser(description="Central UDP log server using raw sockets")
    parser.add_argument("--bind", default="0.0.0.0")
    parser.add_argument("--base-port", type=int, default=DEFAULT_BASE_PORT)
    parser.add_argument("--db", default="logs.db")
    parser.add_argument("--print-every", type=int, default=1, help="0 disables individual receive messages")
    parser.add_argument("--stats-interval", type=float, default=5.0)
    parser.add_argument("--max-datagrams", type=int, default=0, help="0 = run until Ctrl+C; useful for tests")
    args = parser.parse_args()
    try:
        UDPLogServer(bind=args.bind, base_port=args.base_port, db_path=args.db,
                     print_every=args.print_every, stats_interval=args.stats_interval,
                     max_datagrams=args.max_datagrams).serve_forever()
    except (OSError, ValueError, sqlite3.Error) as exc:
        parser.exit(2, f"server error: {exc}\n")


if __name__ == "__main__":
    main()
