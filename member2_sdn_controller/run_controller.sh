#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

ENV_FILE="${ENV_FILE:-.env}"
if [[ ! -f "$ENV_FILE" ]]; then
  echo "ERROR: $ENV_FILE not found. Copy .env.example to .env and review it."
  exit 1
fi

set -a
# shellcheck disable=SC1090
source "$ENV_FILE"
set +a

: "${BOTTLENECK_DPID:?Missing BOTTLENECK_DPID in $ENV_FILE}"
: "${BOTTLENECK_PORT:?Missing BOTTLENECK_PORT in $ENV_FILE}"
: "${LINK_CAPACITY_BPS:?Missing LINK_CAPACITY_BPS in $ENV_FILE}"
OPENFLOW_LISTEN_PORT="${OPENFLOW_LISTEN_PORT:-6653}"

if [[ ! -x ".venv-osken/bin/osken-manager" ]]; then
  echo "ERROR: OS-Ken is not installed in .venv-osken."
  echo "Run ./setup_controller_env.sh first."
  exit 1
fi

echo "Starting OS-Ken: DPID=$BOTTLENECK_DPID port=$BOTTLENECK_PORT capacity=${LINK_CAPACITY_BPS}bps OpenFlow-port=$OPENFLOW_LISTEN_PORT"
exec .venv-osken/bin/osken-manager --ofp-tcp-listen-port "$OPENFLOW_LISTEN_PORT" sdn_controller.py
