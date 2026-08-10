#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
source scripts/lib.sh

env="${1:?Usage: scripts/create_user.sh <dev|prod> <username>}"
username="${2:?Usage: scripts/create_user.sh <dev|prod> <username>}"
compose "$env" exec backend python -m app.scripts.create_user "$username"
