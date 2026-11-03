"""Compare each sender's announced counts to unique arrivals in SQLite.

The sender summary is written by client.py and copied to the test machine.
This detects loss including trailing sequence numbers, unlike gap checks alone.
"""

import argparse
import csv
import json
from pathlib import Path
import sqlite3

from .protocol import SEVERITIES, VERSION


def compare(db_path: Path, summaries: list[Path]) -> list[dict]:
    sent_total = {sev: 0 for sev in SEVERITIES}
    received_total = {sev: 0 for sev in SEVERITIES}
    delay_sum = {sev: 0.0 for sev in SEVERITIES}
    delay_n = {sev: 0 for sev in SEVERITIES}
    if not db_path.is_file():
        raise ValueError(f"database not found: {db_path}")
    with sqlite3.connect(str(db_path)) as conn:
        checked_sessions: set[tuple[str, str]] = set()
        for path in summaries:
            info = json.loads(path.read_text(encoding="utf-8"))
            host, session = info["host_id"], info["session_id"]
            if info["version"] != VERSION or (host, session) in checked_sessions:
                raise ValueError(f"incompatible or repeated sender summary: {path}")
            checked_sessions.add((host, session))
            for severity in SEVERITIES:
                sent = info["sent_by_severity"][severity]
                if type(sent) is not int or sent < 0:
                    raise ValueError(f"invalid sent count in {path}")
                row = conn.execute("""
                    SELECT COUNT(*), COALESCE(SUM(CASE WHEN delay_ms >= 0 THEN delay_ms ELSE 0 END), 0),
                           COUNT(CASE WHEN delay_ms >= 0 THEN 1 END)
                    FROM logs WHERE host_id = ? AND session_id = ? AND severity = ?
                """, (host, session, severity)).fetchone()
                count, this_delay_sum, n_delays = row
                if count > sent:
                    raise ValueError(f"received more unique packets than reported sent for {host}/{severity}")
                sent_total[severity] += sent
                received_total[severity] += count
                delay_sum[severity] += this_delay_sum
                delay_n[severity] += n_delays
    results = []
    for sev in SEVERITIES:
        sent, received = sent_total[sev], received_total[sev]
        missing = sent - received
        results.append({"severity": sev, "sent": sent, "received": received, "lost": missing,
                        "packet_loss_pct": round(100 * missing / sent, 2) if sent else None,
                        "mean_one_way_delay_ms": round(delay_sum[sev] / delay_n[sev], 3) if delay_n[sev] else None})
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Per-severity delivery and loss comparison from client summaries")
    parser.add_argument("--db", type=Path, default=Path("logs.db"))
    parser.add_argument("--summaries", type=Path, nargs="+", required=True)
    parser.add_argument("--csv-out", type=Path, help="save statistics for charts")
    args = parser.parse_args()
    try:
        results = compare(args.db, args.summaries)
    except (ValueError, KeyError, OSError, json.JSONDecodeError, sqlite3.Error) as exc:
        parser.exit(2, f"comparison error: {exc}\n")
    print("SEVERITY   SENT  RECEIVED  LOST  LOSS_%   MEAN_ONE_WAY_DELAY_MS")
    for row in results:
        loss = row["packet_loss_pct"]
        delay = row["mean_one_way_delay_ms"]
        print(f"{row['severity']:<10} {row['sent']:<5} {row['received']:<9} {row['lost']:<5} "
              f"{str(loss) if loss is not None else 'N/A':<8} {delay if delay is not None else 'N/A'}")
    if args.csv_out:
        args.csv_out.parent.mkdir(parents=True, exist_ok=True)
        with args.csv_out.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=results[0].keys())
            writer.writeheader()
            writer.writerows(results)
        print(f"[SAVED] {args.csv_out}")


if __name__ == "__main__":
    main()
