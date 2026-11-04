# Member 2 evidence log

This is a template. Replace each section with output/screenshots from a real run.
Do not report expected example events as observed results.

- Date/time:
- Host OS / VM:
- Python version:
- Ryu version:
- Open vSwitch version:
- Mininet version:
- Switch DPID:
- Bottleneck egress port name and OpenFlow port number:
- Configured bottleneck rate:

## Startup evidence
Paste actual Ryu startup and switch connection output.

## QoS evidence
Paste actual `ovs-vsctl list Port`, `list QoS`, and `list Queue` output.

## Congestion transition evidence
Paste actual `BOTTLENECK_STATS`, `CONGESTION_ENTERED`, and `POLICY_CHANGED` lines.

## Recovery evidence
Paste actual `CONGESTION_CLEARED` and baseline restoration lines.

## Notes / deviations
Record anything that differed from the planned configuration.
