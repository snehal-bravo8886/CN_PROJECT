#!/usr/bin/env bash
set -euo pipefail
BRIDGE="${1:-s1}"
PORT="${2:-s1-eth4}"

echo "=== Open vSwitch version ==="
ovs-vswitchd --version
echo "=== Mininet version ==="
mn --version || true
echo "=== Bridge protocols ==="
sudo ovs-vsctl get Bridge "$BRIDGE" protocols
echo "=== Switch DPID and ports ==="
sudo ovs-ofctl -O OpenFlow13 show "$BRIDGE"
echo "=== Flows ==="
sudo ovs-ofctl -O OpenFlow13 dump-flows "$BRIDGE"
echo "=== Bottleneck port QoS attachment ==="
sudo ovs-vsctl list Port "$PORT"
echo "=== QoS objects ==="
sudo ovs-vsctl list QoS
echo "=== Queue objects ==="
sudo ovs-vsctl list Queue
