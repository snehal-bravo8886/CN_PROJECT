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

## Documentation

- [Current controller setup](README_MEMBER2.md)
- [End-to-end integration commands](../docs/INTEGRATION.md)
- [Final integration report](../docs/integration/FINAL_INTEGRATION_REPORT.md)
- [Evaluation and evidence](../docs/EVALUATION.md)

The older Ryu troubleshooting document and ZIP packages are historical; use the current checked-in source and requirements. The evidence template is for recording new runs, not a completed execution log.
