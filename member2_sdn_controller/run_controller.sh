#!/usr/bin/env bash
set -euo pipefail

# Run this script from the repository root, inside the Python environment
# where Ryu has been installed and tested.
export BOTTLENECK_DPID=1
export BOTTLENECK_PORT=4
export LINK_CAPACITY_BPS=2000000

exec ryu-manager --ofp-tcp-listen-port 6653 member2_sdn_controller/sdn_controller.py
