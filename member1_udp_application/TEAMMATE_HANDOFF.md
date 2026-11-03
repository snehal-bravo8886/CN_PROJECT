# Member 1 handoff to Members 2 and 3

**Working code:** \`app/client.py\`, \`app/server.py\`, \`app/protocol.py\`, \`app/query_logs.py\`, \`app/compare_results.py\`; \`scripts/run_local_demo.py\`; \`tests/\`.

**Verification:** Ten automated tests pass. Two localhost clients successfully sent 25 logs to the single server, all 25 uniquely persisted in SQLite. The code has not yet been validated through Mininet or a live SDN prioritization policy.

## The exact network contract

| Destination UDP port | Severity | Desired network service |
|---|---|---|
| 10000 | DEBUG | lowest |
| 10001 | INFO | low |
| 10002 | WARNING | medium |
| 10003 | ERROR | high |
| 10004 | CRITICAL | highest |

Each UDP payload is one JSON object with \`version=1\`, \`host_id\`, \`session_id\` (UUID), \`severity\`, \`sequence\` (per host, session and severity), \`sent_ns\` and \`message\`. The max datagram size is 1200 encoded bytes. The 5-port mapping is defined in \`app/protocol.py\`.

## Member 2 — what you must integrate

- Match IPv4 + UDP + destination port in OpenFlow 1.3; the 5 destination ports reveal severity without parsing JSON on the switch.
- Configure or coordinate OVS priority queues *on the bottleneck-facing egress port*. Flow-rule match priority alone does **not** guarantee that CRITICAL traffic receives more bandwidth.
- Provide forwarding, congestion monitoring, dynamic activation of priority handling, and policy restoration.
- Compare controller traffic counters to application delivery counts, recognizing they measure different things.

## Member 3 — how to use the application

Start in \`member1_udp_application/\` with Python 3.10+.

For a local smoke test without Mininet:

\`\`\`bash
python3 -m unittest discover -s tests -v
python3 -m scripts.run_local_demo
\`\`\`

Inside your Mininet network, start the server in the server-host namespace and clients in their client-host namespaces (adapt IPs and host names to your topology):

\`\`\`bash
mkdir -p results
# Server, in hServer namespace:
python3 -m app.server --bind 0.0.0.0 --db results/trial01.db --print-every 0

# Clients, in h1/h2 network namespaces, running concurrently:
python3 -m app.client --server 10.0.0.10 --host-id h1 --count 100 --interval-ms 20 --quiet --summary-file results/trial01_h1.json
python3 -m app.client --server 10.0.0.10 --host-id h2 --count 100 --interval-ms 20 --quiet --summary-file results/trial01_h2.json
\`\`\`

\`10.0.0.10\` is an **example**, not a confirmed Mininet server IP. Launch server and clients concurrently via your topology script. The commands above run *inside each host namespace*; they are not intended as one sequential shell script.

After each trial, run:

\`\`\`bash
python3 -m app.query_logs --db results/trial01.db --stats
python3 -m app.query_logs --db results/trial01.db --streams
python3 -m app.compare_results --db results/trial01.db --summaries results/trial01_h1.json results/trial01_h2.json --csv-out results/trial01_metrics.csv
\`\`\`

## How to calculate and compare correctly

Sender \`sendto\` success does not imply delivery. Packet loss is \`sent - unique_received\` using sender-summary files and server SQLite records. Observed sequence gaps are provisional and do not reveal tail loss. One-way delay uses timestamp subtraction, meaningful only with synchronized sender/server clocks.

Keep separate DB/summary/CSV for each run. Compare baseline vs SDN priority-enabled trials with the same number of hosts, offered traffic and constrained link. Run light, medium and heavy congestion in **isolated Mininet**, not uncontrolled traffic on a normal network.

## Full-team acceptance criteria

- [ ] Functional controller recognizes all severity destination ports and installs verified queue rules.
- [ ] Mininet server and clients can communicate end-to-end over the target topology.
- [ ] Congestion triggers a *dynamic* policy change and recovery restores baseline policy.
- [ ] Server database + sender summaries reconcile with graphs of loss/delay by severity.
- [ ] Comparable baseline and prioritized experiments, with saved scripts and repeatable measurements.
