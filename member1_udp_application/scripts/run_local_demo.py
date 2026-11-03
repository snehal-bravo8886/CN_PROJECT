"""One-command, reproducible localhost demo of the UDP application.

Run from project root: python3 -m scripts.run_local_demo
Writes demo_output/{logs.db,h1_summary.json,h2_summary.json,metrics.csv,terminal_output.txt}.
Uses unused local ports, so does not interfere with the team's real ports.
"""

import argparse
import socket
from pathlib import Path
import subprocess
import sys
import time

def find_available_five_ports() -> int:
    """Find five free contiguous ports for this isolated local demonstration."""
    for base in range(18000, 39000, 11):
        sockets = []
        try:
            for port in range(base, base + 5):
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sockets.append(sock)
                sock.bind(("127.0.0.1", port))
            return base
        except OSError:
            pass
        finally:
            for sock in sockets:
                sock.close()
    raise RuntimeError("Could not find five available contiguous UDP ports")


ROOT = Path(__file__).resolve().parents[1]


def run_command(args: list[str]) -> str:
    result = subprocess.run(args, cwd=ROOT, capture_output=True, text=True, timeout=15)
    if result.returncode:
        raise RuntimeError(f"Command failed ({result.returncode}): {' '.join(args)}\n{result.stderr}")
    return result.stdout


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Member 1's demo with 2 clients on 5 UDP ports")
    parser.add_argument("--out-dir", type=Path, default=Path("demo_output"))
    opts = parser.parse_args()
    out_dir = opts.out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    base = find_available_five_ports()
    db = out_dir / "logs.db"
    for stale in (db, Path(str(db) + "-wal"), Path(str(db) + "-shm")):
        if stale.exists():
            stale.unlink()
    output_parts = ["=== MEMBER 1 UDP APPLICATION DEMO ===", f"Local ports: {base}..{base+4}"]
    server = subprocess.Popen([
        sys.executable, "-u", "-m", "app.server", "--bind", "127.0.0.1",
        "--base-port", str(base), "--db", str(db), "--print-every", "0",
        "--stats-interval", "30", "--max-datagrams", "25",
    ], cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    try:
        time.sleep(0.35)
        if server.poll() is not None:
            raise RuntimeError("Server did not start (possible UDP port conflict)")
        for host, count in (("h1", 15), ("h2", 10)):
            output_parts.append(f"\n--- Client {host} ---")
            output_parts.append(run_command([
                sys.executable, "-m", "app.client", "--server", "127.0.0.1",
                "--base-port", str(base), "--host-id", host, "--count", str(count),
                "--interval-ms", "15", "--quiet", "--summary-file", str(out_dir / f"{host}_summary.json")]))
        server_output, _ = server.communicate(timeout=10)
        if server.returncode:
            raise RuntimeError(f"Server stopped with exit code {server.returncode}:\n{server_output}")
        output_parts.extend(["\n--- Server ---", server_output, "\n--- Query severity counts ---"])
        output_parts.append(run_command([sys.executable, "-m", "app.query_logs", "--db", str(db), "--stats"]))
        output_parts.append("\n--- Packet loss and delay comparison ---")
        output_parts.append(run_command([
            sys.executable, "-m", "app.compare_results", "--db", str(db),
            "--summaries", str(out_dir / "h1_summary.json"), str(out_dir / "h2_summary.json"),
            "--csv-out", str(out_dir / "metrics.csv"),
        ]))
        text = "\n".join(output_parts)
        (out_dir / "terminal_output.txt").write_text(text + "\n", encoding="utf-8")
        print(text)
        print(f"\nDemo saved to {out_dir}")
    finally:
        if server.poll() is None:
            server.kill()
            server.communicate(timeout=5)


if __name__ == "__main__":
    main()
