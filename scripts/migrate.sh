#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
source scripts/lib.sh

env="${1:?Usage: scripts/migrate.sh <dev|prod> [--apply]}"

compose "$env" build backend 1>&2

if [[ "${2:-}" == "--apply" ]]; then
  compose "$env" run --rm backend alembic upgrade head
  exit 0
fi

current="$(compose "$env" run --rm -T backend alembic current 2>/dev/null | tail -1 | awk '{print $1}')"
head_rev="$(compose "$env" run --rm -T backend alembic heads 2>/dev/null | tail -1 | awk '{print $1}')"

if [[ -z "$current" ]]; then
  echo "Database has no migrations applied yet (latest available: ${head_rev:-unknown})."
  echo "Run: scripts/migrate.sh $env --apply"
  exit 2
fi

if [[ "$current" != "$head_rev" ]]; then
  echo "Database is behind: current=$current latest=$head_rev"
  echo "Run: scripts/migrate.sh $env --apply"
  exit 2
fi

echo "Migrations up to date (current=$current)."
