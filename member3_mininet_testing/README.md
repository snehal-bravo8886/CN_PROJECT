# Member 3 — Mininet, Integration and Evaluation

**Status: pending teammate implementation.** This folder is a roadmap; topology and benchmark code have not yet been added.

## Your responsibilities

1. Build a Mininet topology with at least 3 sending hosts, Open vSwitch, and one log-server host.
2. Add a configurable, constrained-bandwidth **bottleneck link**, and document IPs/interfaces.
3. Connect Member 2's OpenFlow controller and configure the bottleneck's OVS QoS queues jointly.
4. Launch Member 1's UDP server inside the server host namespace and the UDP clients inside the respective sender namespaces.
5. Generate repeatable background traffic **only inside the isolated Mininet experiment**.
6. Run baseline (no prioritization) and SDN-priority scenarios under light, medium and heavy congestion using comparable network settings.
7. Export per-severity packet loss and delay CSV; create clear before/after graphs and provide terminal evidence.
8. Prepare final end-to-end instructions and integration screenshots.

## Files to add

\`topology.py\` (or equivalent), setup instructions, test driver/scripts, actual measurements, graphs, and demo/report material. Label experimental outputs with settings so results are reproducible. Do not claim measurements are real until the experiment is actually run.

## Read first

- [Shared integration guide](../docs/INTEGRATION.md)
- [Member 1 handoff](../member1_udp_application/TEAMMATE_HANDOFF.md)
- [Member 1 application](../member1_udp_application/README.md)

Coordinate queue IDs, switch egress interfaces and controller launch options with Member 2.
