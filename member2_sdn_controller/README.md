# Member 2 — SDN Controller

**Status: pending teammate implementation.** This folder contains the agreed interface and task list; it is **not** controller code.

## Your responsibilities

1. Use an OpenFlow 1.3-compatible controller (Ryu / suitable supported equivalent).
2. Install correct forwarding rules between Mininet clients and the central log server.
3. Classify IPv4 UDP packets using their destination ports:
   - 10000 DEBUG (lowest)
   - 10001 INFO (low)
   - 10002 WARNING (medium)
   - 10003 ERROR (high)
   - 10004 CRITICAL (highest)
4. Coordinate with Member 3 to create and map OVS QoS queues **on the bottleneck egress port**. A high OpenFlow flow-table priority is *not* the same as packet service priority.
5. Monitor traffic/flow statistics and identify congestion.
6. Switch to severity-based priority handling when congestion is observed, then restore baseline policy when congestion clears.
7. Document actual commands, queue mapping, screenshots and observed controller events.

## Files to add

Your controller source, launch/setup notes, version/dependencies, OpenFlow/OVS configuration, verification commands, and any real evidence of changing traffic policy.

## Read first

- [Shared integration guide](../docs/INTEGRATION.md)
- [Member 1 application](../member1_udp_application/README.md)
- [Member 1 handoff](../member1_udp_application/TEAMMATE_HANDOFF.md)

Keep implementation confined here, coordinating any shared interface changes via pull request.
