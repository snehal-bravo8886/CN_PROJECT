# Member 2 controller integration update

## Verified Mininet configuration

These values were observed in the Member 3 Mininet topology / OVS inspection:

| Setting | Value |
|---|---:|
| Switch | `s1` |
| OpenFlow DPID | `1` (`0000000000000001`) |
| Bottleneck egress interface | `s1-eth4` |
| Bottleneck OpenFlow port | `4` |
| Bottleneck link capacity | `2 Mbps` (`2000000` bits/s) |
| OpenFlow version | OpenFlow 1.3 |

The topology output showed the `s1` to `h4` link as `2.00Mbit` with `10ms` delay. OVS inspection showed `s1-eth4` as port 4.

## Controller configuration

The controller reads these environment variables:

```bash
export BOTTLENECK_DPID=1
export BOTTLENECK_PORT=4
export LINK_CAPACITY_BPS=2000000
```

Run those commands in a normal Ubuntu terminal, **not** at the `mininet>` prompt. Then start the controller from the repository root:

```bash
ryu-manager --ofp-tcp-listen-port 6653 member2_sdn_controller/sdn_controller.py
```

Alternatively, use the supplied `run_controller.sh` from the repository root:

```bash
chmod +x member2_controller_update/run_controller.sh
./member2_controller_update/run_controller.sh
```

If these files are copied into `member2_sdn_controller/`, adjust the script path accordingly.

## Python / Ryu compatibility status

The VM currently reports Python `3.11.18`. The repository's current dependency file specifies `ryu==4.34`.

An installation attempt with this Python version failed while building Ryu, reporting:

```text
AttributeError: 'types.SimpleNamespace' object has no attribute 'get_script_args'
```

Pinning `setuptools==57.5.0` did not resolve the failure. A subsequent no-build-isolation attempt also failed with inconsistent Ryu package metadata.

**No successful Ryu runtime has been verified in this VM.** Therefore this update deliberately does not claim that Python 3.11.18 + Ryu 4.34 works, does not invent a tested Python/Ryu version pair, and does not silently change `requirements.txt`.

Before running the controller, Member 2 should confirm the exact Python and Ryu versions used successfully, or provide a working container/environment definition (for example, a tested Dockerfile or image). Record versions only after a successful installation and controller startup.

## Important safety notes

- Do not run `setup_queues.sh` until confirming the target OVS port. Its current implementation clears any existing QoS attachment on that port before creating queues.
- Queue setup is separate from controller startup. First verify the controller connects and reports the expected DPID / port.
- The controller's queue mapping expects UDP destination ports `10000` through `10004` for DEBUG, INFO, WARNING, ERROR, and CRITICAL respectively. Confirm Member 1's sender uses this UDP-port contract.
- Flow-table priority is not packet scheduling priority. Actual service differentiation depends on OVS QoS queues and must be measured.
- Do not report congestion transitions, queue assignments, or recovery as observed until they appear in actual controller logs and OVS inspection.

## Requested confirmation from Member 2

Please provide:
1. The exact Python version used for a successful Ryu installation.
2. The exact Ryu version used.
3. The OS / base image and installation steps.
4. A Dockerfile or other reproducible environment, if available.
5. Evidence that `ryu-manager` starts the controller and the switch connects over OpenFlow 1.3.
