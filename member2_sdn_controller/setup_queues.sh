#!/usr/bin/env bash
# Create 5 Linux-HTB queues on the bottleneck egress port.
# Usage: sudo ./setup_queues.sh <switch-egress-interface> [rate-mbps]
# Example: sudo ./setup_queues.sh s1-eth3 10
set -euo pipefail

PORT="${1:-}"
RATE_MBIT="${2:-10}"
if [[ -z "$PORT" ]]; then
  echo "Usage: sudo $0 <bottleneck-egress-interface> [link-rate-mbps]"
  exit 1
fi
if ! ovs-vsctl list Port "$PORT" >/dev/null 2>&1; then
  echo "ERROR: OVS port '$PORT' not found."
  exit 1
fi

RATE_BPS=$((RATE_MBIT * 1000000))
# Guaranteed minimum shares add up to the parent link rate.
# Queue 0 DEBUG lowest; queue 4 CRITICAL highest.
Q0=$((RATE_BPS * 5 / 100))
Q1=$((RATE_BPS * 10 / 100))
Q2=$((RATE_BPS * 15 / 100))
Q3=$((RATE_BPS * 25 / 100))
Q4=$((RATE_BPS * 45 / 100))

ovs-vsctl --if-exists clear Port "$PORT" qos
ovs-vsctl \
  -- set Port "$PORT" qos=@qos \
  -- --id=@q0 create Queue other-config:min-rate="$Q0" \
  -- --id=@q1 create Queue other-config:min-rate="$Q1" \
  -- --id=@q2 create Queue other-config:min-rate="$Q2" \
  -- --id=@q3 create Queue other-config:min-rate="$Q3" \
  -- --id=@q4 create Queue other-config:min-rate="$Q4" \
  -- --id=@qos create QoS type=linux-htb other-config:max-rate="$RATE_BPS" \
       queues:0=@q0 queues:1=@q1 queues:2=@q2 queues:3=@q3 queues:4=@q4

echo "QoS queues created on $PORT at parent rate ${RATE_MBIT} Mbps."
ovs-vsctl list Port "$PORT"
ovs-vsctl list Queue
