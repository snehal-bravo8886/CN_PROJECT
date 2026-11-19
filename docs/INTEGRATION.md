# Team 10 — Integration guide and protocol contract

**SNEHAL AGRAWAL (Member 1)** — UDP application; **TEJAS DIWAKAR (Member 2)** — SDN controller; **SIDDHANT CHAWLA (Member 3)** — Mininet and evaluation.

The integrated demonstration is recorded in the [final integration report](integration/FINAL_INTEGRATION_REPORT.md). These instructions describe the current source tree; commands for new runs are not a claim of additional test execution.

## Network configuration

| Item | Value |
|---|---|
| H1, H2, H3, H4 | 10.0.0.1, 10.0.0.2, 10.0.0.3, 10.0.0.4 (/24) |
| H1–H3 access links | 10 Mbps each |
| S1 to H4 | 2 Mbps, 10 ms configured delay, max_queue_size=50 |
| Switch and egress | s1, DPID 1, port 4 / s1-eth4 |
| Controller | OS-Ken 3.1.1, Python 3.11, OpenFlow 1.3, TCP 6653 |

## Severity-to-port contract

| Severity | UDP destination port | Queue | Minimum rate at 2 Mbps |
|---|---:|---:|---:|
| DEBUG | 10000 | 0 | 100 kbps |
| INFO | 10001 | 1 | 200 kbps |
| WARNING | 10002 | 2 | 300 kbps |
| ERROR | 10003 | 3 | 500 kbps |
| CRITICAL | 10004 | 4 | 900 kbps |

The queue script creates Linux HTB minimum-rate shares; these are not strict-priority scheduling or measured throughput guarantees. The controller uses queue actions on the bottleneck egress only when congestion is active. It polls every 2 seconds, enters at >=80%, clears at <=60%, and keeps the previous state between thresholds.

## UDP wire message

One UTF-8 JSON object per datagram, maximum 1200 encoded bytes:

```json
{"version":1,"host_id":"h1","session_id":"11111111-2222-4333-8444-555555555555","severity":"CRITICAL","sequence":1,"sent_ns":1793600000000000000,"message":"Application event"}
```

Fields must match the protocol exactly. Host ID is 1–64 permitted ASCII characters; session ID is a canonical lowercase UUID; sequence starts at 1 per host/session/severity; sent_ns is a positive Unix nanosecond timestamp; message is 1–700 characters; severity must match the destination port. UDP has no delivery acknowledgment or retransmission.

## Run the integrated system

Prerequisites: Linux/Ubuntu lab VM, Mininet, Open vSwitch, iperf3, Python 3.11, and administrator access for Mininet/OVS. Install Matplotlib in an appropriate Python environment if regenerating graphs. Run traffic only inside the isolated lab.

**Terminal A — controller**, from repository root:

```bash
cd member2_sdn_controller
bash setup_controller_env.sh
# Create .env only if it does not already exist:
test -f .env || cp .env.example .env
cat .env
bash run_controller.sh
```

**Terminal B — topology**, from repository root, on the same VM:

```bash
cd member1_udp_application
mkdir -p results
sudo mn --custom ../member3_mininet_testing/topology/topology.py --topo logtopo --controller remote,ip=127.0.0.1,port=6653 --switch ovsk,protocols=OpenFlow13 --link tc
```

If the controller runs on a separate VM, replace 127.0.0.1 with its reachable IP. At the Mininet prompt, run `pingall` to establish connectivity and MAC learning. Confirm the controller reports switch connection.

**Terminal C — queues**, from repository root, while Mininet is running:

```bash
sudo ovs-ofctl -O OpenFlow13 show s1
sudo bash member2_sdn_controller/setup_queues.sh s1-eth4 2
sudo bash member2_sdn_controller/setup_queues.sh s1-eth4 2 --apply
bash member2_sdn_controller/ovs_verification_commands.sh
```

The first setup command is a dry run. Apply only after verifying the egress interface; type APPLY at the confirmation. This replaces the existing QoS attachment on that port.

**Terminal B — Mininet CLI**, with a fresh trial identifier:

```text
h4 python3 -m app.server --bind 0.0.0.0 --db results/trial01.db --print-every 0 > results/trial01_server.log 2>&1 &
h4 iperf3 -s -p 5201 > results/trial01_iperf_server.log 2>&1 &
h3 bash ../member3_mininet_testing/tests/congestion_test.sh 3M 30 > results/trial01_iperf.txt 2>&1 &
h1 python3 -m app.client --server 10.0.0.4 --host-id H1 --count 300 --interval-ms 100 --quiet --summary-file results/trial01_h1.json &
h2 python3 -m app.client --server 10.0.0.4 --host-id H2 --count 300 --interval-ms 100 --quiet --summary-file results/trial01_h2.json &
```

Enter the first two commands, confirm the UDP collector and iperf3 listener are ready, then enter the last three commands. The congestion script runs only inside H3 and exits when the client completes. Run both clients concurrently. Observe controller utilization and queue rules while the background load is active; after traffic stops, wait for the controller to clear congestion. Use separate trial IDs, databases and JSON summaries for each run. For light/medium/heavy tests use 0.5M, 1.5M and 3M background offered rates respectively. These commands describe a reproducible workload, not exact historical launch timing. The adaptive controller cannot supply a true FIFO control under heavy congestion merely by omitting queue setup: a separate baseline forwarding configuration with no severity queue selection or HTB differentiation must be established and verified. Do not label an adaptive run FIFO.

**After clients finish**, allow the collector to commit its data. From another normal terminal in member1_udp_application:

```bash
python3 -m app.query_logs --db results/trial01.db --stats
python3 -m app.query_logs --db results/trial01.db --streams
python3 -m app.compare_results --db results/trial01.db --summaries results/trial01_h1.json results/trial01_h2.json --csv-out results/trial01_metrics.csv
```

Stop the lab processes gracefully (SIGINT to the collector so it flushes SQLite), exit Mininet, and stop the controller. Use sudo mn -c only for cleanup of the isolated lab when necessary.

## Metric definitions and evidence

- Sent = successful sendto calls from sender-summary JSON; received = unique matching SQLite rows; lost = sent minus received, including tail losses.
- Loss percentage = 100 × lost / sent when sent is nonzero.
- One-way delay = (receive_ns - sent_ns) / 1e6 ms; synchronized clocks are required. Mininet hosts share a system clock.
- Sequence gaps are provisional, can shrink when packets arrive late, and cannot identify tail losses alone.
- Switch flow counters are not application delivery counts.
- iperf3 receiver throughput and jitter measure the background UDP flow, not individual log classes.

## Submission documents

- [SRS](SRS.md)
- [STP](STP.md)

## Verification status

- [x] Application implementation, 10 recorded automated tests, and 25/25 local delivery.
- [x] Integrated controller, topology, queue mapping and 50 stored logs documented in the final integration report.
- [x] Baseline light/medium/heavy measurements and graphs archived.
- [ ] Archive matched baseline-versus-QoS per-class performance runs and raw recovery logs for independent quantitative verification.

See [evaluation section of the final integration report](integration/FINAL_INTEGRATION_REPORT.md#8-evaluation-and-evidence) for the distinction between archived baseline measurements and final integration evidence.
