#!/usr/bin/env bash
# Create five Linux-HTB queues on a confirmed bottleneck egress port.
# Usage: sudo ./setup_queues.sh <OVS_PORT_NAME> <RATE_MBIT>
set -euo pipefail
PORT="${1:-}"
RATE_MBIT="${2:-}"
if [[ -z "$PORT" || -z "$RATE_MBIT" ]]; then
  echo "Usage: sudo $0 <confirmed-bottleneck-egress-port> <rate-mbps>"
  exit 2
fi
if ! [[ "$RATE_MBIT" =~ ^[1-9][0-9]*([.][0-9]+)?$ ]]; then
  echo "ERROR: rate must be a positive number of Mbps."
  exit 2
fi
if ! ovs-vsctl list Port "$PORT" >/dev/null 2>&1; then
  echo "ERROR: OVS port '$PORT' not found."
  exit 1
fi
RATE_BPS="$(python3 - "$RATE_MBIT" <<'PYRATE'
import sys
print(int(float(sys.argv[1]) * 1000000))
PYRATE
)"
echo "Port: $PORT | parent rate: ${RATE_MBIT} Mbps"
echo "WARNING: this replaces the QoS attachment currently on this port."
read -r -p "Continue? Type YES: " CONFIRM
if [[ "$CONFIRM" != "YES" ]]; then
  echo "Cancelled; no QoS changes made."
  exit 0
fi
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
echo "QoS queues created on $PORT."
ovs-vsctl list Port "$PORT"
ovs-vsctl list QoS
ovs-vsctl list Queue
