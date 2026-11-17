# Team 10 — Evaluation and evidence

This summary distinguishes the committed baseline experiments from the separate integrated QoS demonstration.

## Recorded application tests

[Automated test transcript](../member1_udp_application/samples/verified_demo/automated_test_results.txt): 10/10 passed. [Local demo](../member1_udp_application/samples/verified_demo/terminal_output.txt): 25 sent, 25 stored, 0 lost, five received per severity.

## Baseline congestion results

Sources: [host summary](../member3_mininet_testing/results/host_summary.csv), [per-class data](../member3_mininet_testing/results/log_analysis.csv), [iperf3 summary](../member3_mininet_testing/results/iperf_analysis.csv). The analysis script reads final-baseline.db, which is not committed; the CSVs and graphs preserve the recorded outputs.

| Load | Offered background Mbps | Received background Mbps | Background jitter (ms) | Background loss | Logs received/sent |
|---|---:|---:|---:|---:|---:|
| Light | 0.5 | 0.50 | 0.717 | 0% | 600/600 |
| Medium | 1.5 | 1.50 | 0.655 | 0% | 600/600 |
| Heavy | 3 | 1.94 | 2.173 | 35% | 343/600 |

Heavy load: H1 received 133/300 and H2 received 210/300. Combined per-class deliveries were DEBUG 69, INFO 69, WARNING 72, ERROR 64, CRITICAL 69, each out of 120 sent. Background jitter and throughput are iperf3 measurements, not per-class application measurements.

## Derived fairness

Jain's index J = (sum x)^2 / (n × sum x²), where x is the delivery fraction for each of the five classes (equal offered counts). This is a derived baseline delivery-fairness metric, not a measured bandwidth fairness result.

- Light: 1.0000 (120 received per class).
- Medium: 1.0000 (120 received per class).
- Heavy: 0.9986 (69, 69, 72, 64, 69 received).

A high index does not imply low loss: heavy baseline delivery is only 343/600. Nor does equal treatment imply that QoS has achieved its intended service differentiation.

## Integrated QoS demonstration

The [final integration report](integration/FINAL_INTEGRATION_REPORT.md) records 50 stored logs (10 per severity), approximately 12 ms mean delay per severity, an OpenFlow 1.3 connection, utilization around 100%, severity queue selection, and approximately 1.96 Mbps background throughput in a separate run.

## Evidence boundaries

The committed material demonstrates implementation and integrated operation. A matched no-QoS/FIFO versus QoS comparison at identical offered loads, per-class throughput/jitter, and raw recovery logs are not archived in the current evidence set. Do not infer quantitative improvement or a strict scheduling guarantee from the baseline graphs or queue configuration alone. For a future comparison, retain equivalent workloads, run durations, queue settings, sender summaries, databases (locally), controller logs, and per-class metrics. Keep raw generated databases out of Git.
