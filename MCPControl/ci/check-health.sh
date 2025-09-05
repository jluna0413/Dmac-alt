#!/usr/bin/env bash
# Simple cross-platform health check helper for CI (uses curl and jq)
set -euo pipefail
HOST=${1:-127.0.0.1}
PORT=${2:-8052}
READY_URL="http://${HOST}:${PORT}/ready"
HEALTH_URL="http://${HOST}:${PORT}/health"

echo "Checking readiness at ${READY_URL}"
curl -sSf "${READY_URL}" | jq .

echo "Checking health at ${HEALTH_URL}"
curl -sSf "${HEALTH_URL}" | jq .
