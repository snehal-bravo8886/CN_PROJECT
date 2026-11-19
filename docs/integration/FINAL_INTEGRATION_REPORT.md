# Final Integration Report — Computer Networks Project

## 1. Project Overview

This project combines three components into a distributed log collection and congestion-aware networking system.

- Member 1 — SNEHAL AGRAWAL: UDP-based centralized log collection and querying.
- Member 2 — TEJAS DIWAKAR: SDN controller with congestion detection and severity-based queue selection.
- Member 3 — SIDDHANT CHAWLA: Mininet topology, traffic generation, and performance analysis.

## 2. Integrated Architecture

The Mininet topology contains hosts H1, H2, H3, and H4 connected through switch S1.

- H1 and H2 generate application log messages.
- H3 generates background traffic to create bottleneck congestion.
- H4 runs the centralized UDP log server.
- S1 connects to the OS-Ken SDN controller over OpenFlow 1.3.

## 3. Member 1 — UDP Log Application

The integrated UDP server successfully received and stored 50 application log messages.

| Severity | Messages received |
|---|---:|
| DEBUG | 10 |
| INFO | 10 |
| WARNING | 10 |
| ERROR | 10 |
| CRITICAL | 10 |
| **Total** | **50** |

The database query reported an average one-way delivery delay of approximately 12 ms for each severity.

## 4. Member 2 — SDN Controller

The OS-Ken controller successfully connected to switch S1 using OpenFlow 1.3.

The controller monitored bottleneck port 4 and detected congestion when utilization reached the 80% entry threshold. The implemented policy returns to baseline when utilization is at or below 60%.

During the integrated test, bottleneck utilization reached approximately 100%, and the controller entered severity-priority mode.

UDP severity-to-queue mapping:

| Severity | UDP port | Queue |
|---|---:|---:|
| DEBUG | 10000 | 0 |
| INFO | 10001 | 1 |
| WARNING | 10002 | 2 |
| ERROR | 10003 | 3 |
| CRITICAL | 10004 | 4 |

OpenFlow flow-table checks confirmed queue selection for all five UDP ports during congestion.

## 5. Member 3 — Mininet Testing

The Mininet topology was launched with the remote controller.

The bottleneck link between S1 and H4 was configured with a 2 Mbps capacity. OVS Linux HTB QoS was configured with five severity queues.

A UDP background traffic test from H3 to H4 achieved approximately 1.96 Mbps, demonstrating the bottleneck.

## 6. Final Integration Result

All three project components were exercised together:

1. Mininet provided the network topology.
2. OS-Ken monitored congestion and selected severity-based queues.
3. The Member 1 UDP application received and stored messages at H4.
4. The database query confirmed 50 stored messages, with 10 messages per severity.
5. OVS flow-table checks confirmed the five severity-to-queue mappings.

## 7. Conclusion

The integrated project successfully demonstrated centralized UDP log collection over a Mininet network, SDN-based bottleneck monitoring, and severity-aware traffic queue selection.

The test results confirm successful integration of the three members' components.

## 8. Evaluation and evidence

The archived baseline measurements below are distinct from the integrated QoS demonstration above.

### Recorded application tests

[Automated test transcript](../../member1_udp_application/samples/verified_demo/automated_test_results.txt): 10/10 passed. [Local demo](../../member1_udp_application/samples/verified_demo/terminal_output.txt): 25 sent, 25 stored, 0 lost, five received per severity.

### Baseline congestion results

Sources: [host summary](../../member3_mininet_testing/results/host_summary.csv), [per-class data](../../member3_mininet_testing/results/log_analysis.csv), [iperf3 summary](../../member3_mininet_testing/results/iperf_analysis.csv). The analysis script reads final-baseline.db, which is not committed; the CSVs and graphs preserve the recorded outputs.

| Load | Offered background Mbps | Received background Mbps | Background jitter (ms) | Background loss | Logs received/sent |
|---|---:|---:|---:|---:|---:|
| Light | 0.5 | 0.50 | 0.717 | 0% | 600/600 |
| Medium | 1.5 | 1.50 | 0.655 | 0% | 600/600 |
| Heavy | 3 | 1.94 | 2.173 | 35% | 343/600 |

Heavy load: H1 received 133/300 and H2 received 210/300. Combined per-class deliveries were DEBUG 69, INFO 69, WARNING 72, ERROR 64, CRITICAL 69, each out of 120 sent. Background jitter and throughput are iperf3 measurements, not per-class application measurements.

### Derived fairness

Jain's index J = (sum x)^2 / (n × sum x²), where x is the delivery fraction for each of the five classes (equal offered counts). This is a derived baseline delivery-fairness metric, not a measured bandwidth fairness result.

- Light: 1.0000 (120 received per class).
- Medium: 1.0000 (120 received per class).
- Heavy: 0.9986 (69, 69, 72, 64, 69 received).

A high index does not imply low loss: heavy baseline delivery is only 343/600. Nor does equal treatment imply that QoS has achieved its intended service differentiation.

### Evidence boundaries

The committed material demonstrates implementation and integrated operation. A matched no-QoS/FIFO versus QoS comparison at identical offered loads, per-class throughput/jitter, and raw recovery logs are not archived in the current evidence set. Do not infer quantitative improvement or a strict scheduling guarantee from the baseline graphs or queue configuration alone. For a future comparison, retain equivalent workloads, run durations, queue settings, sender summaries, databases (locally), controller logs, and per-class metrics. Keep raw generated databases out of Git.
