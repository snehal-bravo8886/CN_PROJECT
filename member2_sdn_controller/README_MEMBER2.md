# Member 2 — SDN Controller (OpenFlow 1.3)

## Update summary

This package migrates the supplied Ryu-based controller to **OS-Ken**, a maintained
Ryu-derived framework. The controller source imports have been changed from `ryu.*`
to `os_ken.*`; the OpenFlow application logic and UDP severity-to-queue contract
are retained. OS-Ken documents itself as a Ryu fork and provides the `osken-manager`
command. See the upstream OS-Ken documentation and PyPI metadata linked below.

**Runtime target:** Python 3.11 in a project-local virtual environment.
**Dependency pin:** `os-ken==4.2.2`.
This version is selected from current package metadata; it has not been executed
inside your VM by this file-generation process. Successful installation and live
OpenFlow/OVS integration must still be verified on your machine.

## Verified topology values supplied by the project screenshots

| Setting | Value |
|---|---:|
| Switch | `s1` |
| DPID | `1` |
| Log-server-facing egress | `s1-eth4` |
| OpenFlow port | `4` |
| Bottleneck capacity | `2,000,000` bps (2 Mbps) |
| OpenFlow version | 1.3 |
| Controller TCP port | 6653 |

These are the values reported from your Mininet/OVS inspection. Recheck them if
the topology changes. The controller reads DPID, port and capacity from `.env`.

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
cp .env.example .env
cat .env
```

Review `.env`; it should contain DPID `1`, port `4`, and capacity `2000000`.
Do not commit a real `.env` if your team treats local configuration as untracked.

## Start order

1. Start the Mininet topology with the switch configured for OpenFlow 1.3 and
   connected to the controller at the controller VM's reachable IP, TCP 6653.
2. Start the controller from this directory:

   ```bash
   ./run_controller.sh
   ```

3. Confirm startup logs include `OPENFLOW_READY dpid=1 version=1.3`.
4. Only after confirming the actual port and capacity, configure QoS. The setup
   script defaults to dry-run and requires both `--apply` and typing `APPLY`:

   ```bash
   sudo ./setup_queues.sh s1-eth4 2
   sudo ./setup_queues.sh s1-eth4 2 --apply
   ```

   This replaces the QoS attachment on `s1-eth4`; inspect the existing state first.
   Do not run the apply command if the interface is not the actual bottleneck egress.

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

This is a single-switch learning-switch starter implementation. Queue scheduling
depends on Linux HTB support in the OVS host and must be demonstrated with traffic.
The controller's utilization estimate is derived from TX-byte counter deltas and is
a lab heuristic, not a universal congestion detector. Queue objects existing in OVSDB
do not by themselves prove packets were scheduled as intended.

Record actual Python, OS-Ken, OVS and Mininet versions. Do not write that the
controller ran successfully until the startup and traffic tests pass.

## Upstream references

- OS-Ken project: https://github.com/openstack/os-ken
- OS-Ken documentation: https://docs.openstack.org/os-ken/latest/
- OS-Ken package: https://pypi.org/project/os-ken/4.2.2/
