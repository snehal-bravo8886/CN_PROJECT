# Shared integration contract and final evaluation checklist

**Member 1:** UDP application (implemented/tested on localhost) · **Member 2:** OpenFlow/OVS controller (pending) · **Member 3:** Mininet/test environment (pending).

## Severity to UDP destination port (DO NOT change without team agreement)

| Severity | Destination UDP port | Intended network priority |
|---|---:|---|
| DEBUG | 10000 | lowest |
| INFO | 10001 | low |
| WARNING | 10002 | medium |
| ERROR | 10003 | high |
| CRITICAL | 10004 | highest |

OpenFlow can match UDP destination port to classify log severity. Open vSwitch must have correctly configured *egress QoS queues* at the bottleneck for actual priority service. This policy is not implemented by the UDP server.

## UDP wire message

One UTF-8 JSON object per UDP datagram; max **1200 bytes**:

\`\`\`json
{"version":1,"host_id":"h1","session_id":"11111111-2222-4333-8444-555555555555","severity":"CRITICAL","sequence":1,"sent_ns":1793600000000000000,"message":"Application event"}
\`\`\`

- \`host_id\`: client label.
- \`session_id\`: canonical UUID generated for each client run.
- \`sequence\`: starts at 1 for each \`(host_id, session_id, severity)\` stream.
- \`sent_ns\`: Unix timestamp nanoseconds, measured just before \`sendto\`.
- \`severity\`: one of five classes, must match the destination port.

## Exact commands for Member 3

Open a terminal at the **member1_udp_application/** directory. The server address \`10.0.0.10\` below is only an example: replace with Member 3's actual topology server IP. Commands beginning with a host name are intended for Mininet CLI, not regular shell.

\`\`\`bash
mkdir -p results
# In Mininet CLI / launch script:
hServer python3 -m app.server --bind 0.0.0.0 --db results/trial01.db --print-every 0
h1 python3 -m app.client --server 10.0.0.10 --host-id h1 --count 100 --interval-ms 20 --quiet --summary-file results/trial01_h1.json
h2 python3 -m app.client --server 10.0.0.10 --host-id h2 --count 100 --interval-ms 20 --quiet --summary-file results/trial01_h2.json
\`\`\`

The example Mininet CLI commands are not all intended to execute sequentially in one blocking console. Run the server and clients as appropriately **concurrent background processes** from a topology/test script.

After each run, with DB and summaries accessible in the same directory:

\`\`\`bash
python3 -m app.query_logs --db results/trial01.db --stats
python3 -m app.query_logs --db results/trial01.db --streams
python3 -m app.compare_results --db results/trial01.db --summaries results/trial01_h1.json results/trial01_h2.json --csv-out results/trial01_metrics.csv
\`\`\`

## Metric definitions

- **Sent:** number of successful sender \`sendto()\` calls, from sender-summary JSON.
- **Received:** unique matching rows in centralized SQLite.
- **Lost:** sent minus received. Unlike a gap-only calculation, catches missing final packets.
- **Loss percentage:** 100 × lost / sent (when sent is nonzero).
- **One-way delay:** (server receive timestamp - client send timestamp) / 1e6 milliseconds. **Meaningful only with synchronized host clocks.** Mininet hosts usually share one system clock.
- **Sequence gaps:** provisional; may shrink if packets arrive late, and do not detect dropped last packets without sender summaries.
- **Flow counts:** counts observed by switch, not necessarily packet delivery at application layer.

Use separate DBs and JSON summary files for each trial; ensure matching offered load, link bandwidth, duration, and client count for a fair comparison. Measure actual results—never substitute hypothetical percentages.

## Verification checklist

- [x] Member 1: client, server, persistent logs, filters, sent/received comparison.
- [x] Member 1: 10 automated protocol/integration/resilience tests passed locally.
- [x] Member 1: two localhost senders, 25 logs, 25 unique stored, loss 0% on uncongested loopback.
- [ ] Member 2: functional controller and verified queue rule changes.
- [ ] Member 3: functional Mininet hosts, topology and bottleneck.
- [ ] Actual SDN-priority traffic across the configured OVS bottleneck.
- [ ] Light/medium/heavy congestion, baseline vs priority, repeated trials.
- [ ] Final performance graphs, documented commands and live demonstration.
