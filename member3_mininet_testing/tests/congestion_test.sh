#!/usr/bin/env bash
# Run this bounded background-load client inside the isolated Mininet H3 namespace.
# Start iperf3 -s -p 5201 on H4 before launching this script.
set -euo pipefail

RATE="${1:-3M}"
DURATION="${2:-30}"

if (( $# > 2 )) || [[ ! "$RATE" =~ ^(0\.5M|1\.5M|3M)$ ]] || [[ ! "$DURATION" =~ ^[1-9][0-9]{0,2}$ ]] || (( DURATION > 300 )); then
  echo "Usage: $0 [0.5M|1.5M|3M] [duration seconds: 1-300]" >&2
  exit 2
fi

if ! command -v ip >/dev/null || ! command -v iperf3 >/dev/null; then
  echo "ERROR: iproute2 and iperf3 are required." >&2
  exit 1
fi

if ! ip -4 -o addr show dev h3-eth0 2>/dev/null | grep -q 'inet 10\.0\.0\.3/24 '; then
  echo "ERROR: run this script inside Mininet H3 (h3-eth0, 10.0.0.3/24)." >&2
  exit 1
fi

echo "Starting H3 → H4 UDP background load: $RATE for ${DURATION}s" >&2
exec iperf3 -c 10.0.0.4 -B 10.0.0.3 -u -b "$RATE" -t "$DURATION" -p 5201
