# Member 3 — SIDDHANT CHAWLA — Mininet, integration and evaluation

**Status:** Implemented and integrated. Baseline experiment measurements and graphs are committed in results/. The [final integration report](../docs/integration/FINAL_INTEGRATION_REPORT.md) records the separate integrated QoS demonstration.

## Topology

H1 (10.0.0.1) and H2 (10.0.0.2) generate application logs; H3 (10.0.0.3) generates background UDP traffic; H4 (10.0.0.4) hosts the collector. All are connected to s1. Access links are 10 Mbps; s1 to h4 is a 2 Mbps bottleneck with 10 ms configured delay and queue size 50. The bottleneck egress is s1-eth4, port 4.

## Files

- topology/topology.py — Mininet LogTopology, registered as logtopo.
- tests/congestion_test.sh — existing simple iperf3 traffic script; execute traffic in the correct isolated Mininet host namespaces rather than assuming the script creates them.
- analysis/analyze.py — reads SQLite and sender summaries, generates CSVs and plots using Matplotlib.
- results/ — archived sender summaries, iperf3 transcripts, CSVs and graphs.

## Run and analyze

Follow the [current integration guide](../docs/INTEGRATION.md) for controller startup, topology, queues, client/server and background traffic commands. For new experiments, use separate trial identifiers and save corresponding sender summaries and databases.

The existing analysis script expects results/final-baseline.db and the historical JSON filenames. The generated database is not committed; to rerun that exact analysis, restore the matching database locally. The committed CSVs and PNGs can be inspected without it.

## Recorded baseline

| Load | H1 received/sent | H2 received/sent | Background receiver throughput |
|---|---:|---:|---:|
| Light | 300/300 | 300/300 | 0.50 Mbps |
| Medium | 300/300 | 300/300 | 1.50 Mbps |
| Heavy | 133/300 | 210/300 | 1.94 Mbps |

See [evaluation summary](../docs/EVALUATION.md) for loss, jitter, derived fairness and evidence limitations. These baseline results are not a matched QoS-versus-FIFO comparison.
