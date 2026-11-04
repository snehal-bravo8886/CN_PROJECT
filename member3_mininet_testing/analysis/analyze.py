
import csv
import json
import re
import sqlite3
from pathlib import Path
from collections import defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "results"
DB_PATH = RESULTS / "final-baseline.db"

EXPERIMENTS = {
    "Light": ["light-h1.json", "light-h2.json"],
    "Medium": ["medium2-h1.json", "medium2-h2.json"],
    "Heavy": ["heavy2-h1.json", "heavy2-h2.json"],
}

IPERF_FILES = {
    "Light": "light-iperf.txt",
    "Medium": "medium2-iperf.txt",
    "Heavy": "heavy2-iperf.txt",
}

SEVERITIES = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


def write_csv(path, rows, fields):
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main():
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Database not found: {DB_PATH}")

    db = sqlite3.connect(DB_PATH)

    log_rows = []
    host_summary = []
    latency_samples = defaultdict(list)

    print("\n========== APPLICATION LOG ANALYSIS ==========")

    for experiment, files in EXPERIMENTS.items():
        for filename in files:
            path = RESULTS / filename

            if not path.exists():
                raise FileNotFoundError(f"Missing JSON file: {path}")

            with open(path) as f:
                data = json.load(f)

            host = data["host_id"]
            session = data["session_id"]
            sent_counts = data["sent_by_severity"]

            received_rows = db.execute("""
                SELECT severity, COUNT(*),
                       AVG(delay_ms), MIN(delay_ms), MAX(delay_ms)
                FROM logs
                WHERE host_id = ? AND session_id = ?
                GROUP BY severity
            """, (host, session)).fetchall()

            received = {r[0]: r for r in received_rows}

            host_sent = 0
            host_received = 0

            for severity in SEVERITIES:
                sent = sent_counts.get(severity, 0)
                record = received.get(severity)

                count = record[1] if record else 0
                avg_latency = record[2] if record else None
                min_latency = record[3] if record else None
                max_latency = record[4] if record else None

                lost = max(0, sent - count)
                loss_pct = (lost / sent * 100) if sent else 0

                host_sent += sent
                host_received += count

                if record and avg_latency is not None:
                    latency_samples[(experiment, severity)].extend(
                        [avg_latency] * count
                    )

                log_rows.append({
                    "experiment": experiment,
                    "host": host,
                    "severity": severity,
                    "sent": sent,
                    "received": count,
                    "lost": lost,
                    "loss_percent": round(loss_pct, 2),
                    "average_latency_ms": (
                        round(avg_latency, 3)
                        if avg_latency is not None else ""
                    ),
                    "minimum_latency_ms": (
                        round(min_latency, 3)
                        if min_latency is not None else ""
                    ),
                    "maximum_latency_ms": (
                        round(max_latency, 3)
                        if max_latency is not None else ""
                    ),
                })

            host_summary.append({
                "experiment": experiment,
                "host": host,
                "sent": host_sent,
                "received": host_received,
                "lost": host_sent - host_received,
                "loss_percent": round(
                    (host_sent - host_received) / host_sent * 100, 2
                ) if host_sent else 0,
            })

            print(
                f"{experiment} | {host} | "
                f"Sent={host_sent} | Received={host_received} | "
                f"Lost={host_sent-host_received}"
            )

    db.close()

    write_csv(
        RESULTS / "log_analysis.csv",
        log_rows,
        [
            "experiment", "host", "severity", "sent",
            "received", "lost", "loss_percent",
            "average_latency_ms", "minimum_latency_ms",
            "maximum_latency_ms"
        ]
    )

    write_csv(
        RESULTS / "host_summary.csv",
        host_summary,
        [
            "experiment", "host", "sent",
            "received", "lost", "loss_percent"
        ]
    )

    print("\n========== UDP/IPERF ANALYSIS ==========")

    iperf_rows = []

    pattern = re.compile(
        r"([\d.]+)\s+([KM]bits/sec)\s+([\d.]+)\s+ms\s+"
        r"(\d+)/(\d+)\s+\(([\d.]+)%\)\s+receiver"
    )

    for experiment, filename in IPERF_FILES.items():
        path = RESULTS / filename

        if not path.exists():
            print(f"WARNING: Missing iperf file: {filename}")
            continue

        content = path.read_text(errors="replace")
        matches = pattern.findall(content)

        if not matches:
            print(f"WARNING: No receiver summary found in {filename}")
            continue

        rate, unit, jitter, lost, total, loss_pct = matches[-1]

        rate = float(rate)
        if unit == "Kbits/sec":
            rate /= 1000

        iperf_rows.append({
            "experiment": experiment,
            "throughput_mbps": rate,
            "jitter_ms": float(jitter),
            "lost_datagrams": int(lost),
            "total_datagrams": int(total),
            "udp_loss_percent": float(loss_pct),
        })

        print(
            f"{experiment} | Throughput={rate} Mbps | "
            f"Jitter={jitter} ms | UDP Loss={loss_pct}%"
        )

    write_csv(
        RESULTS / "iperf_analysis.csv",
        iperf_rows,
        [
            "experiment", "throughput_mbps", "jitter_ms",
            "lost_datagrams", "total_datagrams",
            "udp_loss_percent"
        ]
    )

    print("\n========== GENERATING GRAPHS ==========")

    experiments = ["Light", "Medium", "Heavy"]

    # Graph 1: Application message loss by host
    for host in ["H1", "H2"]:
        values = []

        for exp in experiments:
            row = next(
                r for r in host_summary
                if r["experiment"] == exp and r["host"] == host
            )
            values.append(row["loss_percent"])

        plt.bar(experiments, values)
        plt.title(f"Application Message Loss - {host}")
        plt.xlabel("Congestion Level")
        plt.ylabel("Message Loss (%)")
        plt.tight_layout()
        plt.savefig(RESULTS / f"application_loss_{host}.png")
        plt.close()

    # Graph 2: Average latency by severity
    for severity in SEVERITIES:
        means = []
        labels = []

        for exp in experiments:
            samples = latency_samples.get((exp, severity), [])

            if samples:
                means.append(sum(samples) / len(samples))
                labels.append(exp)

        if means:
            plt.bar(labels, means)
            plt.title(f"Average Log Latency - {severity}")
            plt.xlabel("Congestion Level")
            plt.ylabel("Latency (ms)")
            plt.tight_layout()
            plt.savefig(RESULTS / f"latency_{severity.lower()}.png")
            plt.close()

    # Graph 3, 4 and 5: UDP performance
    if iperf_rows:
        plt.bar(
            [r["experiment"] for r in iperf_rows],
            [r["throughput_mbps"] for r in iperf_rows]
        )
        plt.title("UDP Throughput Comparison")
        plt.xlabel("Congestion Level")
        plt.ylabel("Throughput (Mbps)")
        plt.tight_layout()
        plt.savefig(RESULTS / "udp_throughput.png")
        plt.close()

        plt.bar(
            [r["experiment"] for r in iperf_rows],
            [r["udp_loss_percent"] for r in iperf_rows]
        )
        plt.title("UDP Packet Loss Comparison")
        plt.xlabel("Congestion Level")
        plt.ylabel("Packet Loss (%)")
        plt.tight_layout()
        plt.savefig(RESULTS / "udp_packet_loss.png")
        plt.close()

        plt.bar(
            [r["experiment"] for r in iperf_rows],
            [r["jitter_ms"] for r in iperf_rows]
        )
        plt.title("UDP Jitter Comparison")
        plt.xlabel("Congestion Level")
        plt.ylabel("Jitter (ms)")
        plt.tight_layout()
        plt.savefig(RESULTS / "udp_jitter.png")
        plt.close()

    print("\nAnalysis completed successfully!")
    print("Reports and graphs saved in:", RESULTS)


if __name__ == "__main__":
    main()
