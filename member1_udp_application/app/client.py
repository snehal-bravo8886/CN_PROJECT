"""UDP sender. Run with: python -m app.client --server 127.0.0.1 --count 25"""

import argparse
import json
from pathlib import Path
import socket
import time
import uuid

from .protocol import (DEFAULT_BASE_PORT, MAX_MESSAGE_CHARS, SEVERITIES,
                       VERSION, encode_record, severity_port, validate_base_port)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate timestamped, severity-tagged UDP logs")
    parser.add_argument("--server", default="127.0.0.1", help="server IPv4 address (Mininet example: 10.0.0.10)")
    parser.add_argument("--host-id", default=socket.gethostname(), help="unique client/host name")
    parser.add_argument("--base-port", type=int, default=DEFAULT_BASE_PORT)
    parser.add_argument("--severity", choices=("ALL", *SEVERITIES), default="ALL")
    parser.add_argument("--count", type=int, default=25, help="total datagrams to attempt")
    parser.add_argument("--interval-ms", type=float, default=100.0, help="delay between packets; 0 = burst")
    parser.add_argument("--message", default="Application event")
    parser.add_argument("--message-size", type=int, default=0,
                        help="pad message to N characters (1..700), for traffic tests")
    parser.add_argument("--summary-file", type=Path, help="save sent counts/session ID for packet-loss analysis")
    parser.add_argument("--quiet", action="store_true", help="hide per-packet output")
    return parser


def run(args: argparse.Namespace) -> dict:
    validate_base_port(args.base_port)
    if args.count <= 0:
        raise ValueError("--count must be greater than zero")
    if args.interval_ms < 0:
        raise ValueError("--interval-ms must be >= 0")
    if args.message_size < 0 or args.message_size > MAX_MESSAGE_CHARS:
        raise ValueError(f"--message-size must be 0..{MAX_MESSAGE_CHARS}")
    if not args.message or len(args.message) > MAX_MESSAGE_CHARS:
        raise ValueError(f"--message must contain 1..{MAX_MESSAGE_CHARS} characters")
    session_id = str(uuid.uuid4())
    sequence_by_severity = {sev: 0 for sev in SEVERITIES}
    sent_by_severity = {sev: 0 for sev in SEVERITIES}
    started_at_ns = time.time_ns()
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        for i in range(args.count):
            severity = SEVERITIES[i % len(SEVERITIES)] if args.severity == "ALL" else args.severity
            seq = sequence_by_severity[severity] + 1
            message = args.message
            if args.message_size:
                message = message[:args.message_size].ljust(args.message_size, ".")
            record = {
                "version": VERSION, "host_id": args.host_id, "session_id": session_id,
                "severity": severity, "sequence": seq, "sent_ns": time.time_ns(),
                "message": message,
            }
            data = encode_record(record)
            destination = (args.server, severity_port(severity, args.base_port))
            sock.sendto(data, destination)
            sequence_by_severity[severity] = seq
            sent_by_severity[severity] += 1
            if not args.quiet:
                print(f"[SENT] {args.host_id} {severity:8} seq={seq:<5} udp_port={destination[1]} bytes={len(data)}", flush=True)
            if args.interval_ms > 0 and i < args.count - 1:
                time.sleep(args.interval_ms / 1000)
    summary = {
        "version": VERSION, "host_id": args.host_id, "session_id": session_id,
        "server": args.server, "base_port": args.base_port,
        "sent_by_severity": sent_by_severity, "sent_total": sum(sent_by_severity.values()),
        "started_at_ns": started_at_ns, "finished_at_ns": time.time_ns(),
    }
    if args.summary_file:
        args.summary_file.parent.mkdir(parents=True, exist_ok=True)
        args.summary_file.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(f"[DONE] host={args.host_id} session={session_id} sent={summary['sent_total']} counts={sent_by_severity}", flush=True)
    if args.summary_file:
        print(f"[SAVED] sender summary: {args.summary_file}", flush=True)
    return summary


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    try:
        run(args)
    except (ValueError, OSError) as exc:
        parser.exit(2, f"client error: {exc}\n")


if __name__ == "__main__":
    main()
