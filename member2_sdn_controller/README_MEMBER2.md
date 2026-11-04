# Member 2 — SDN Controller (OpenFlow 1.3)

## Responsibility

This component learns MAC-to-port mappings, installs forwarding rules, classifies IPv4/UDP log packets by UDP destination port, polls bottleneck-port statistics, and enables severity queue selection while measured utilization is high.

**Important distinction:** OpenFlow flow-table priority is rule-match precedence. It is not packet scheduling priority. Packet service differentiation is performed by Open vSwitch QoS queues selected using `OFPActionSetQueue`.

## UDP port contract — coordinate with Member 1

| Severity | UDP destination port | OVS queue ID |
|---|---:|---:|
| DEBUG | 10000 | 0 |
| INFO | 10001 | 1 |
| WARNING | 10002 | 2 |
| ERROR | 10003 | 3 |
| CRITICAL | 10004 | 4 |

The client must send each severity to the corresponding destination port. The controller does not inspect a severity label inside the UDP payload.

## Before running: set the real bottleneck port

Edit the configuration constants near the top of `sdn_controller.py`:

```python
BOTTLENECK_DPID = 1
BOTTLENECK_PORT = 3
LINK_CAPACITY_BPS = 10_000_000
```

These are example values, NOT verified facts about your topology. Ask Member 3 for:
- switch datapath ID (DPID)
- switch interface number that sends packets toward the central log server
- configured bottleneck bandwidth

Find OVS ports and port numbers:

```bash
sudo ovs-vsctl show
sudo ovs-vsctl list-ports s1
sudo ovs-ofctl -O OpenFlow13 show s1
```

The queues must be created on the **bottleneck egress port**, i.e. the switch port used by packets as they leave the switch toward the constrained link/server. Confirm the direction with Member 3.

## Dependencies and versions

- Controller API: Ryu 4.34
- OpenFlow protocol: 1.3
- Switch: Open vSwitch with OpenFlow 1.3 and Linux HTB QoS support
- Emulator: Mininet

Record actual installed versions in your report:

```bash
ryu-manager --version
ovs-vswitchd --version
mn --version
python3 --version
```

Ryu 4.34 is an older release and can be incompatible with some modern Python distributions. Use the Python environment provided by your lab or a compatible virtual environment if installation fails. Do not claim a version was tested unless it was actually run.

Install:

```bash
sudo apt update
sudo apt install -y openvswitch-switch mininet python3-pip
python3 -m pip install -r requirements.txt
```

## Start the controller

From the directory containing `sdn_controller.py`:

```bash
sudo ryu-manager --ofp-tcp-listen-port 6653 sdn_controller.py
```

Configure the Mininet OVS switch for OpenFlow 1.3 and connect it to the controller at TCP port 6653. Example Python topology setup (adapt to your topology):

```python
net = Mininet(topo=topo, controller=None, switch=OVSSwitch)
net.addController('c0', controller=RemoteController,
                  ip='127.0.0.1', port=6653)
# Ensure the OVS switch is created with protocols='OpenFlow13'.
```

If Ryu is on a separate VM, replace `127.0.0.1` with the controller VM's reachable IP.

## Configure OVS QoS queues

Identify the correct bottleneck egress interface first. The example `s1-eth3` is not guaranteed to be correct:

```bash
sudo ovs-vsctl list-ports s1
sudo ovs-ofctl -O OpenFlow13 show s1
```

Then configure queues on that port (example 10 Mbps bottleneck):

```bash
sudo bash setup_queues.sh s1-eth3 10
```

Queue mapping and configured minimum-rate shares:

| Queue | Severity | Share of parent rate |
|---:|---|---:|
| 0 | DEBUG | 5% |
| 1 | INFO | 10% |
| 2 | WARNING | 15% |
| 3 | ERROR | 25% |
| 4 | CRITICAL | 45% |

These are example Linux-HTB minimum-rate shares. Confirm that the OVS QoS type and queues are supported by the lab host. Queue creation is separate from controller flow programming.

## Congestion policy

The controller polls the configured bottleneck port every 2 seconds and estimates transmit utilization from the change in `tx_bytes`.

- Enter congestion at or above 80% of configured link capacity.
- Clear congestion at or below 60%.
- Between 60% and 80%, retain the previous state (hysteresis to reduce rapid toggling).
- When congested, recognized UDP log packets leaving the configured bottleneck egress port receive queue IDs 0–4 based on severity.
- When congestion clears, the controller returns to baseline forwarding without severity queue selection.

Adjust thresholds and polling interval in `sdn_controller.py` if your experiment design requires it. The controller's rate estimate is based on port TX counters and is a simple lab heuristic, not a universal congestion detector.

## Verification commands

Check controller/switch connection and OpenFlow rules:

```bash
sudo ovs-vsctl get Bridge s1 protocols
sudo ovs-ofctl -O OpenFlow13 show s1
sudo ovs-ofctl -O OpenFlow13 dump-flows s1
```

Inspect QoS attached to the bottleneck port:

```bash
sudo ovs-vsctl list Port <BOTTLENECK_PORT_NAME>
sudo ovs-vsctl list QoS
sudo ovs-vsctl list Queue
```

Inspect controller events in the Ryu terminal. Expected event labels emitted by this code include:

```text
OPENFLOW_READY
BOTTLENECK_STATS
CONGESTION_ENTERED
POLICY_CHANGED policy=severity_priority
LOG_PACKET severity=CRITICAL
CONGESTION_CLEARED
POLICY_CHANGED policy=baseline
```

The exact utilization values, timestamps, packet counts and events must come from your actual run. Do not put fabricated screenshots or sample numbers in the report.

## Evidence checklist for the team report

Capture screenshots or save terminal output showing:

1. `ryu-manager` startup and OpenFlow 1.3 switch connection.
2. `ovs-ofctl -O OpenFlow13 show s1` showing the actual bottleneck port.
3. `ovs-vsctl list Port`, `list QoS`, and `list Queue` showing queue mapping.
4. `dump-flows` showing forwarding/classification rules.
5. Ryu log lines showing `BOTTLENECK_STATS` and `CONGESTION_ENTERED`.
6. Ryu log lines showing queue assignment for the five severity classes while congested.
7. `CONGESTION_CLEARED` and baseline policy restoration.
8. Test results with and without congestion, including delivered/missing sequence numbers and delay.

Keep the actual logs/screenshots in a folder such as `evidence/member2/`, with short captions and the date of the run.

## Known integration limits

- Set the correct DPID, egress port number and link capacity before testing.
- The controller chooses queues only for packets egressing the configured bottleneck port.
- The first packet of a new flow is sent to the controller. After congestion state changes, dynamic flows are removed so subsequent packets are handled under the new policy.
- The controller polls port stats; it also requests flow stats for diagnostics. Port utilization drives the congestion state in this implementation.
- This is a single-switch learning-switch starter implementation. If your topology has multiple switches or multiple paths, extend and test forwarding across the full topology.
- Queue scheduling behavior depends on OVS/Linux QoS support and the actual constrained egress link. Verify with traffic tests; do not infer success merely because queue objects exist.
