# Local verification snapshot

This folder contains the application tests and localhost demonstration results. It does not contain Mininet congestion results.

- `automated_test_results.txt`: 10/10 tests passed.
- `terminal_output.txt`: two clients h1/h2 send 15+10 UDP logs, server stores 25/25.
- `h1_summary.json` and `h2_summary.json`: sender-side counts.
- `metrics.csv`: received and loss/delay per severity.

To regenerate the local SQLite database, run the following from the repository root:

```bash
cd member1_udp_application
python3 -m scripts.run_local_demo
```

Localhost latency depends on the test environment and is not a measure of congested-network performance.
