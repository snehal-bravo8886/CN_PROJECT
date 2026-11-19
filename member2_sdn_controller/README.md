# Member 2 — TEJAS DIWAKAR — SDN controller

**Status:** Implemented and integrated. The [final integration report](../docs/integration/FINAL_INTEGRATION_REPORT.md) records successful OpenFlow 1.3 connection, congestion activation and all five severity queue mappings.

## Current implementation

- sdn_controller.py — OS-Ken learning switch, IPv4 UDP destination-port classification, port/flow polling, dynamic queue selection.
- requirements.txt — OS-Ken 3.1.1; Python 3.11 target.
- setup_controller_env.sh and run_controller.sh — isolated environment and controller startup.
- .env.example — DPID 1, bottleneck port 4, 2 Mbps, TCP 6653.
- setup_queues.sh — Linux HTB queues on s1-eth4; dry-run by default, explicit confirmation before replacing QoS.
- ovs_verification_commands.sh — inspection of the bridge, flow tables and queues.

Poll interval is 2 seconds. Congestion activates at >=80% utilization, clears at <=60%, and retains the current state in between. The controller removes learned flows on a policy transition so subsequent packets receive the new actions. OpenFlow rule priority is not packet scheduling priority.

## Topology and configuration

| Setting | Value |
|---|---:|
| Switch | `s1` |
| DPID | `1` |
| Log-server-facing egress | `s1-eth4` |
| OpenFlow port | `4` |
| Bottleneck capacity | `2,000,000` bps (2 Mbps) |
| OpenFlow version | 1.3 |
| Controller TCP port | 6653 |

These values match the committed Mininet topology. Recheck them if the topology changes. The controller reads DPID, port and capacity from `.env`.

## UDP contract (must match Member 1)

| Severity | UDP destination port | OVS queue |
|---|---:|---:|
| DEBUG | 10000 | 0 |
| INFO | 10001 | 1 |
| WARNING | 10002 | 2 |
| ERROR | 10003 | 3 |
| CRITICAL | 10004 | 4 |

The client must send each severity to its corresponding UDP destination port.
The controller does not inspect a severity label in the payload.

## Install OS-Ken in an isolated environment

From this directory, use Python 3.11. The setup script prefers the Python 3.11
interpreter already managed by `uv`, if available. It does not modify system Python.

```bash
chmod +x setup_controller_env.sh run_controller.sh setup_queues.sh ovs_verification_commands.sh
./setup_controller_env.sh
test -f .env || cp .env.example .env
cat .env
```

Review `.env`; it should contain DPID `1`, port `4`, and capacity `2000000`.
Keep local `.env` files untracked.

## Start order

1. Start the controller from this directory with `bash run_controller.sh`.
2. Start Mininet with OpenFlow 1.3 and the remote controller at its reachable IP, TCP 6653. Follow the [end-to-end integration guide](../docs/INTEGRATION.md).
3. Confirm `OPENFLOW_READY dpid=1 version=1.3` and verify the egress port.
4. Preview queue configuration with `sudo bash setup_queues.sh s1-eth4 2`. Apply only after confirming the port with `sudo bash setup_queues.sh s1-eth4 2 --apply` and typing `APPLY`. This replaces the existing QoS attachment on that port.

## Congestion behavior

- Port statistics are polled every 2 seconds.
- Enter congestion at or above 80% of configured link capacity.
- Clear congestion at or below 60%; between 60% and 80%, retain prior state.
- While congested, recognized UDP log packets leaving DPID 1 through port 4 receive
  queue IDs 0–4 according to severity.
- When congestion clears, dynamic flows are removed and subsequent packets use
  baseline forwarding.

OVS queue selection (`OFPActionSetQueue`) performs packet service differentiation;
OpenFlow flow priority is only match precedence.

## Verification

```bash
sudo ovs-vsctl set bridge s1 protocols=OpenFlow13
sudo ovs-ofctl -O OpenFlow13 show s1
sudo ovs-ofctl -O OpenFlow13 dump-flows s1
sudo ovs-vsctl list Port s1-eth4
sudo ovs-vsctl list QoS
sudo ovs-vsctl list Queue
```

Capture actual controller output for `OPENFLOW_READY`, `BOTTLENECK_STATS`,
`CONGESTION_ENTERED`, `POLICY_CHANGED`, severity `LOG_PACKET` events,
`CONGESTION_CLEARED`, and baseline restoration.

## Important limitations and evidence

This is a single-switch learning-switch implementation. Queue scheduling
depends on Linux HTB support in the OVS host and must be demonstrated with traffic.
The controller's utilization estimate is derived from TX-byte counter deltas and is
a lab heuristic, not a universal congestion detector. Queue objects existing in OVSDB
do not by themselves prove packets were scheduled as intended.

Record actual Python, OS-Ken, OVS and Mininet versions. For a new run, retain startup and traffic evidence.

## Upstream references

- OS-Ken project: https://github.com/openstack/os-ken
- OS-Ken documentation: https://docs.openstack.org/os-ken/latest/
- OS-Ken package: https://pypi.org/project/os-ken/3.1.1/

## Project documentation

- [End-to-end integration commands](../docs/INTEGRATION.md)
- [Final integration report and evaluation](../docs/integration/FINAL_INTEGRATION_REPORT.md)
