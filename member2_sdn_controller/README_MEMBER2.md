# Member 2 — SDN Controller (OpenFlow 1.3)

## Function and UDP contract

This is a single-switch Ryu learning-switch starter. It learns MAC addresses,
forwards IPv4/UDP packets, polls one configured switch egress port, and selects
an OVS queue for recognized log packets while congestion is active.

OpenFlow flow-table priority controls rule-match precedence; it is not packet
scheduling priority. Service differentiation is attempted through
`OFPActionSetQueue` and OVS QoS queues.

The sender must use this exact UDP destination-port mapping (confirm Member 1's
client actually implements it):

| Severity | UDP destination port | OVS queue ID |
|---|---:|---:|
| DEBUG | 10000 | 0 |
| INFO | 10001 | 1 |
| WARNING | 10002 | 2 |
| ERROR | 10003 | 3 |
| CRITICAL | 10004 | 4 |

The controller does not inspect a severity label in the UDP payload.

## Required live topology configuration

The controller deliberately refuses to start unless these environment variables
are set from actual OVS/Mininet inspection:

- `BOTTLENECK_DPID`: actual switch datapath ID.
- `BOTTLENECK_PORT`: OpenFlow port number for traffic leaving the switch toward
  the constrained link / central log server.
- `LINK_CAPACITY_BPS`: confirmed link capacity in bits per second.

Member 3's topology was previously described as having a 2 Mbps server-facing
link. If the live topology confirms that, set `LINK_CAPACITY_BPS=2000000`.
Do not assume the DPID or port number.

Inspect the live switch:

```bash
sudo ovs-vsctl show
sudo ovs-vsctl list-ports s1
sudo ovs-ofctl -O OpenFlow13 show s1
```

Match the server-facing interface to the topology before choosing the egress
port. The OpenFlow `show` output provides the DPID and numbered ports.

## Set runtime configuration

Example only; replace DPID and PORT with the actual values:

```bash
export BOTTLENECK_DPID=1
export BOTTLENECK_PORT=<confirmed-openflow-port-number>
export LINK_CAPACITY_BPS=2000000
```

Start the controller from the repository root after Ryu has been installed in
the Python environment being used:

```bash
ryu-manager --ofp-tcp-listen-port 6653 member2_sdn_controller/sdn_controller.py
```

Configure Mininet's OVS switch for OpenFlow 1.3 and connect it to the controller
at TCP port 6653.

## Ryu installation compatibility warning

`requirements.txt` retains the team's requested `ryu==4.34`. Ryu 4.34 is an old
release. In the current lab VM, Python 3.11.18 was installed with `uv`, but the
Ryu installation failed during package metadata/build setup with a
`types.SimpleNamespace` / `get_script_args` error. Pinning setuptools to 57.5.0
did not resolve the attempted install. This package therefore does not claim
that Ryu is installed or working.

Do not repeatedly retry installs or change system Python. The team should agree
on a tested Ryu-compatible environment/version or maintained compatible
controller package, then record the exact versions tested. Do not silently
change the dependency without team approval.

## OVS QoS queues

Identify the confirmed bottleneck egress interface first. The setup script asks
for explicit `YES` confirmation because it clears/replaces the QoS attachment
on the selected port:

```bash
sudo bash member2_sdn_controller/setup_queues.sh <confirmed-port-name> 2
```

The `2` is an example for a confirmed 2 Mbps link. Use the actual configured
parent rate. Queue minimum-rate shares are DEBUG 5%, INFO 10%, WARNING 15%,
ERROR 25%, CRITICAL 45%. Queue creation and controller queue selection are
separate operations. Verify Linux-HTB support and measure actual scheduling.

## Congestion policy

- Port statistics are polled every 2 seconds.
- Congestion enters at or above 80% utilization.
- Congestion clears at or below 60%.
- Between 60% and 80%, the previous state is retained.
- Queue selection applies only to recognized UDP log packets leaving the
  configured DPID/egress port while congestion is active.

This is a simple TX-counter utilization heuristic, not a universal congestion
detector. Verify it using actual traffic and controller logs.

## Verification

```bash
sudo ovs-vsctl get Bridge s1 protocols
sudo ovs-ofctl -O OpenFlow13 show s1
sudo ovs-ofctl -O OpenFlow13 dump-flows s1
sudo ovs-vsctl list QoS
sudo ovs-vsctl list Queue
```

Expected log labels include `OPENFLOW_READY`, `BOTTLENECK_STATS`,
`CONGESTION_ENTERED`, `LOG_PACKET`, `CONGESTION_CLEARED`, and
`POLICY_CHANGED`. These labels are not evidence that events occurred; capture
actual run output.

## Known limitations

- Single-switch learning-switch implementation.
- Correct DPID, egress port and link capacity are required.
- Member 1's UDP destination ports must match the table above.
- Queue selection occurs only on the configured bottleneck egress.
- OVS/Linux QoS support and actual scheduling behavior must be tested.
- No successful Ryu runtime test is claimed in this package.
