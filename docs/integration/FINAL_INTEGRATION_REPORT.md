# Final Integration Report — Computer Networks Project

## 1. Project Overview

This project combines three components into a distributed log collection and congestion-aware networking system.

- Member 1: UDP-based centralized log collection and querying.
- Member 2: SDN controller with congestion detection and severity-based queue selection.
- Member 3: Mininet topology, traffic generation, and performance analysis.

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

The controller monitored bottleneck port 4 and detected congestion when utilization exceeded 80%. It returned to baseline policy when utilization fell below 60%.

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
