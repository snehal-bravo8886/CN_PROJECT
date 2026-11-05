# Member 2 evidence log

Replace every field with output from an actual run. Do not report expected events
or example values as observed results.

- Date/time:
- Host OS / VM and architecture:
- Python version used by Ryu:
- Ryu version:
- Open vSwitch version:
- Mininet version:
- Switch name:
- Switch DPID (from live OVS output):
- Bottleneck egress interface name:
- Bottleneck OpenFlow port number:
- Confirmed bottleneck rate:
- Member 1 UDP destination-port mapping verified: yes/no

## Controller startup
Paste actual Ryu startup and switch-connection output.

## OVS / OpenFlow
Paste actual `ovs-ofctl -O OpenFlow13 show` and `dump-flows` output.

## QoS
Paste actual `ovs-vsctl list Port`, `list QoS`, and `list Queue` output.

## Congestion transition
Paste actual `BOTTLENECK_STATS`, `CONGESTION_ENTERED`, and `POLICY_CHANGED` lines.

## Queue assignment
Capture actual `LOG_PACKET` lines for DEBUG, INFO, WARNING, ERROR, and CRITICAL
while congestion is active. Verify queue IDs, not just severity labels.

## Recovery
Paste actual `CONGESTION_CLEARED` and baseline-policy restoration lines.

## Notes / deviations
Record failures, deviations, and behavior that could not be verified.
