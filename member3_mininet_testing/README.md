# Member 3 — SIDDHANT CHAWLA — Mininet, integration and evaluation

**Status:** Implemented and integrated. Baseline experiment measurements and graphs are committed in results/. The [final integration report](../docs/integration/FINAL_INTEGRATION_REPORT.md) records the separate integrated QoS demonstration.

## Topology

H1 (10.0.0.1) and H2 (10.0.0.2) generate application logs; H3 (10.0.0.3) generates background UDP traffic; H4 (10.0.0.4) hosts the collector. All are connected to s1. Access links are 10 Mbps; s1 to h4 is a 2 Mbps bottleneck with 10 ms configured delay and queue size 50. The bottleneck egress is s1-eth4, port 4.

## Files

- topology/topology.py — Mininet LogTopology, registered as logtopo.
- tests/congestion_test.sh — bounded iperf3 UDP client helper for the H3 namespace; start the receiver on H4 first.
- analysis/analyze.py — reads SQLite and sender summaries, generates CSVs and plots using Matplotlib.
- results/ — archived sender summaries, iperf3 transcripts, CSVs and graphs.

## Run and analyze

Follow the [current integration guide](../docs/INTEGRATION.md) for controller startup, topology, queues, client/server and background traffic commands. For new experiments, use separate trial identifiers and save corresponding sender summaries and databases.

From the Mininet CLI (working directory = repository root):

```text
h4 iperf3 -s -p 5201 &
h3 bash member3_mininet_testing/tests/congestion_test.sh 3M 30
```

Wait until the receiver is listening before starting the client. Use 0.5M, 1.5M or 3M for light, medium or heavy load. The client validates its H3 interface/address, sends to H4, and exits after the configured duration. Stop the H4 listener when finished.

The analysis script requires `results/final-baseline.db` and the original sender-summary JSON files. The database is not tracked. Restore the matching database locally to repeat the analysis, or inspect the existing CSVs and PNGs directly. Install Matplotlib with `python3 -m pip install matplotlib`. The script writes to `results/`, so use a separate working copy for new experiments.

## Recorded baseline

| Load | H1 received/sent | H2 received/sent | Background receiver throughput |
|---|---:|---:|---:|
| Light | 300/300 | 300/300 | 0.50 Mbps |
| Medium | 300/300 | 300/300 | 1.50 Mbps |
| Heavy | 133/300 | 210/300 | 1.94 Mbps |

See [evaluation section of the final integration report](../docs/integration/FINAL_INTEGRATION_REPORT.md#8-evaluation-and-evidence) for loss, jitter, derived fairness and evidence limitations. These baseline results are not a matched QoS-versus-FIFO comparison.
