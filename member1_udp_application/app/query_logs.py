"""Query SQLite logs by host, severity, and session; no extra dependencies."""

import argparse
import datetime as dt
import sqlite3
from pathlib import Path

from .protocol import SEVERITIES


def main() -> None:
    parser = argparse.ArgumentParser(description="Search the centralized UDP log database")
    parser.add_argument("--db", default="logs.db")
    parser.add_argument("--host", help="filter by exact host ID")
    parser.add_argument("--severity", choices=SEVERITIES)
    parser.add_argument("--session", help="filter by sender session UUID")
    parser.add_argument("--limit", type=int, default=30, help="maximum rows for listing")
    parser.add_argument("--stats", action="store_true", help="totals and mean delivery time by severity")
    parser.add_argument("--streams", action="store_true", help="counts/gaps by host, session and severity")
    args = parser.parse_args()
    if args.limit <= 0:
        parser.error("--limit must be > 0")
    if not Path(args.db).exists():
        parser.error(f"database not found: {args.db}")
    clauses, params = [], []
    for field, value in (("host_id", args.host), ("severity", args.severity), ("session_id", args.session)):
        if value is not None:
            clauses.append(f"{field} = ?")
            params.append(value)
    where = " WHERE " + " AND ".join(clauses) if clauses else ""
    try:
        with sqlite3.connect(f"file:{Path(args.db).resolve()}?mode=ro", uri=True) as conn:
            if args.stats:
                rows = conn.execute(
                    "SELECT severity, COUNT(*), ROUND(AVG(CASE WHEN delay_ms >= 0 "
                    "THEN delay_ms END), 3) FROM logs" + where + " GROUP BY severity", params).fetchall()
                print("SEVERITY   RECEIVED   AVG_ONE_WAY_DELAY_MS")
                for sev, count, delay in rows:
                    print(f"{sev:<10} {count:<10} {delay if delay is not None else 'N/A'}")
            elif args.streams:
                rows = conn.execute(
                    "SELECT host_id, session_id, severity, COUNT(*), MAX(sequence), "
                    "MAX(sequence)-COUNT(*) FROM logs" + where +
                    " GROUP BY host_id, session_id, severity ORDER BY host_id, session_id, severity", params).fetchall()
                print("HOST  SESSION_ID  SEVERITY  RECEIVED  MAX_SEQUENCE  APPARENT_MISSING")
                for host, session, sev, received, max_seq, missing in rows:
                    print(f"{host}  {session}  {sev}  {received}  {max_seq}  {missing}")
            else:
                rows = conn.execute(
                    "SELECT host_id, severity, sequence, sent_ns, received_ns, "
                    "ROUND(delay_ms,3), message FROM logs" + where +
                    " ORDER BY received_ns DESC LIMIT ?", [*params, args.limit]).fetchall()
                if not rows:
                    print("No matching logs.")
                for host, sev, seq, sent_ns, received_ns, delay, message in rows:
                    arrival = dt.datetime.fromtimestamp(received_ns / 1e9, tz=dt.timezone.utc).isoformat(timespec="milliseconds")
                    print(f"{arrival} | host={host} | {sev} | seq={seq} | delay={delay} ms | {message}")
    except sqlite3.Error as exc:
        parser.exit(2, f"database error: {exc}\n")


if __name__ == "__main__":
    main()
