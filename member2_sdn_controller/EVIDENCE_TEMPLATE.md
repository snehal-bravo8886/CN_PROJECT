# Member 2 evidence log

Replace each field with evidence from an actual run. Do not report expected events as observed.

- Date/time:
- Host OS / VM architecture:
- Python version:
- OS-Ken version:
- Open vSwitch version:
- Mininet version:
- Switch DPID:
- Bottleneck egress interface and OpenFlow port:
- Configured bottleneck rate:

## Startup evidence
Paste actual `osken-manager` startup and switch connection output.
Confirm `OPENFLOW_READY dpid=1 version=1.3`.

## QoS evidence
Paste actual `ovs-vsctl list Port s1-eth4`, `list QoS`, and `list Queue` output.

## Congestion transition evidence
Paste actual `BOTTLENECK_STATS`, `CONGESTION_ENTERED`, and `POLICY_CHANGED` lines.

## Severity queue evidence
Capture actual `LOG_PACKET` lines for DEBUG, INFO, WARNING, ERROR and CRITICAL
while congestion is active, including the queue IDs.

## Recovery evidence
Paste actual `CONGESTION_CLEARED` and baseline restoration lines.

## Notes / deviations
Record anything that differed from the planned configuration.
