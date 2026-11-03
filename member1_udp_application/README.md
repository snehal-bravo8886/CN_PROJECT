# Member 1 — UDP log application

**Status:** Implemented and tested on localhost (10/10 automated tests passed; two clients sent 25 logs and the server stored all 25). **SDN controller and Mininet tests are not part of Member 1's code.**

## What this module does

- Generates UDP log messages from independent client hosts with five severity levels.
- Each datagram carries \`version\`, \`host_id\`, \`session_id\`, \`severity\`, \`sequence\`, \`sent_ns\`, and \`message\`.
- Sends DEBUG/INFO/WARNING/ERROR/CRITICAL to UDP destination ports 10000/10001/10002/10003/10004 by default.
- Central server listens concurrently on all five ports, validates incoming JSON, rejects invalid/mismatched datagrams, and stores unique messages in SQLite.
- Detects duplicate or out-of-order sequence numbers and provisional gaps. Compares sender-summary JSON to server database to find losses including trailing packets.
- Queries logs by host, severity, and sender session; generates per-severity CSV metrics.
- Contains unit and real-UDP integration tests plus a scripted localhost demo.

Requires Python **3.10+**, built-in standard library only. All commands should be run **from this folder** so \`python3 -m app...\` imports work.

## Run every test (macOS / Linux)

\`\`\`bash
python3 -m unittest discover -s tests -v
\`\`\`

Expected: **Ran 10 tests ... OK**.

## Run the two-client demo (no Mininet necessary)

\`\`\`bash
python3 -m scripts.run_local_demo
\`\`\`

The demo starts a server on five free local ports, runs h1 (15 messages) and h2 (10 messages), then stops the server, compares sent/received logs, and saves a SQLite DB, summary JSONs, CSV, and terminal transcript to \`demo_output/\` (ignored by Git). Sample representative outputs live in \`samples/verified_demo/\`.

\`\`\`bash
python3 -m app.query_logs --db demo_output/logs.db --limit 10
python3 -m app.query_logs --db demo_output/logs.db --severity CRITICAL
python3 -m app.query_logs --db demo_output/logs.db --stats
python3 -m app.query_logs --db demo_output/logs.db --streams
\`\`\`

## Manual two-terminal demo

Terminal 1 starts the UDP server:

\`\`\`bash
python3 -m app.server --bind 127.0.0.1 --db logs.db
\`\`\`

Terminal 2 sends a workload:

\`\`\`bash
python3 -m app.client --server 127.0.0.1 --host-id h1 --count 25 --interval-ms 50 --summary-file h1_summary.json
python3 -m app.client --server 127.0.0.1 --host-id h2 --count 25 --interval-ms 50 --summary-file h2_summary.json
\`\`\`

Then compute loss:

\`\`\`bash
python3 -m app.compare_results --db logs.db --summaries h1_summary.json h2_summary.json --csv-out results/local_metrics.csv
\`\`\`

Stop the long-running server with Ctrl+C. \`logs.db\`, \`results/\`, and other generated data should not be committed.

## Code map

| File | Purpose |
|---|---|
| \`app/protocol.py\` | Wire format, validation, severity-to-port mapping |
| \`app/client.py\` | Creates and transmits UDP logs; saves per-severity sender summaries |
| \`app/server.py\` | 5 raw UDP sockets, multi-client collection, SQLite persistence, sequence tracking |
| \`app/query_logs.py\` | Search/filter stored logs and inspect counts/gaps |
| \`app/compare_results.py\` | Compute sent/received/lost totals, delay and export CSV |
| \`scripts/run_local_demo.py\` | Reproducible two-client localhost demonstration |
| \`tests/\` | 10 protocol, integration and resilience tests |

## Integration reminders

For the real team demo, Member 3 must put client/server processes in Mininet host namespaces and give clients the *actual* server IP. Member 2 must implement matching OpenFlow and OVS egress queue rules. Default UDP ports 10000–10004 are fixed unless all three members agree to a change. Only the local demo substitutes other ports to avoid conflicts.

See [TEAMMATE_HANDOFF.md](TEAMMATE_HANDOFF.md) and [../docs/INTEGRATION.md](../docs/INTEGRATION.md).

**Limits:** Raw UDP is not guaranteed to deliver every packet. The application cannot itself prioritize switch queues. Measured one-way delays require synchronized clocks; Mininet hosts typically share the same kernel clock.
