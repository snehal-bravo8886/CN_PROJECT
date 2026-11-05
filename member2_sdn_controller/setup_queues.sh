#!/usr/bin/env bash
# Create five Linux-HTB queues on the bottleneck egress interface.
# Usage: sudo ./setup_queues.sh <egress-interface> <rate-mbps> --apply
set -euo pipefail

PORT="${1:-}"
RATE_MBIT="${2:-}"
APPLY="${3:-}"

if [[ -z "$PORT" || -z "$RATE_MBIT" ]]; then
  echo "Usage: sudo $0 <bottleneck-egress-interface> <rate-mbps> [--apply]"
  exit 2
fi
if ! [[ "$RATE_MBIT" =~ ^[1-9][0-9]*$ ]]; then
  echo "ERROR: rate-mbps must be a positive integer."
  exit 2
fi
if ! ovs-vsctl list Port "$PORT" >/dev/null 2>&1; then
  echo "ERROR: OVS port '$PORT' not found."
  exit 1
fi

RATE_BPS=$((RATE_MBIT * 1000000))
Q0=$((RATE_BPS * 5 / 100))
Q1=$((RATE_BPS * 10 / 100))
Q2=$((RATE_BPS * 15 / 100))
Q3=$((RATE_BPS * 25 / 100))
Q4=$((RATE_BPS * 45 / 100))

echo "Planned QoS on $PORT at ${RATE_MBIT} Mbps:"
echo " queue 0 DEBUG     min-rate=$Q0"
echo " queue 1 INFO      min-rate=$Q1"
echo " queue 2 WARNING   min-rate=$Q2"
echo " queue 3 ERROR     min-rate=$Q3"
echo " queue 4 CRITICAL  min-rate=$Q4"
if [[ "$APPLY" != "--apply" ]]; then
  echo "DRY RUN ONLY. Re-run with --apply to replace the QoS attachment on this port."
  exit 0
fi

echo "WARNING: applying this will replace the current QoS attachment on $PORT."
read -r -p "Type APPLY to continue: " CONFIRM
[[ "$CONFIRM" == "APPLY" ]] || { echo "Cancelled."; exit 1; }

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

echo "QoS command completed. Inspect the resulting OVSDB state before testing."
ovs-vsctl list Port "$PORT"
ovs-vsctl list QoS
ovs-vsctl list Queue
