#!/usr/bin/env bash
# Read-only OVS/OpenFlow inspection. Pass switch name (default s1).
set -euo pipefail
SWITCH="${1:-s1}"
echo "=== OVS configuration ==="
sudo ovs-vsctl show
sudo ovs-vsctl list-ports "$SWITCH"
echo "=== OpenFlow 1.3 ports, DPID and port numbers ==="
sudo ovs-ofctl -O OpenFlow13 show "$SWITCH"
echo "=== Installed flows ==="
sudo ovs-ofctl -O OpenFlow13 dump-flows "$SWITCH"
echo "=== QoS objects ==="
sudo ovs-vsctl list QoS
sudo ovs-vsctl list Queue
