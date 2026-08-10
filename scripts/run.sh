#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
source scripts/lib.sh

env="${1:?Usage: scripts/run.sh <dev|prod> [--clear]}"
env_file=".env.${env}"

if [[ ! -f "$env_file" ]]; then
  cp "${env_file}.example" "$env_file"
  echo "Created $env_file from the template."
  echo "Edit it now (passwords, SECRET_KEY, ROUTERAI_API_KEY$( [[ "$env" == "prod" ]] && echo ', DOMAIN' )), then re-run: scripts/run.sh $env"
  exit 1
fi

if [[ "${2:-}" == "--clear" ]]; then
  echo "==> Clean slate for '$env' — each step asks first, Enter/N skips it."

  if confirm "Stop and remove containers + default network for $env?"; then
    compose "$env" down --remove-orphans
    echo "Containers removed."
  fi

  if confirm "Remove volumes for $env — DELETES the database, irreversible?"; then
    compose "$env" down --volumes --remove-orphans
    echo "Volumes removed."
  fi

  if confirm "Remove the docker network for $env (if it's still around)?"; then
    if docker network rm "braindump-${env}_default" 2>/dev/null; then
      echo "Network removed."
    else
      echo "Network already gone (or still in use)."
    fi
  fi

  if confirm "Remove locally built images for $env (backend/web — not pulled base images)?"; then
    compose "$env" down --rmi local
    echo "Images removed."
  fi

  if confirm "Remove local dev artifacts (backend/.venv, frontend/node_modules, caches, dist)? Not Docker resources — just files, safe to regenerate with 'uv sync' / 'npm install'."; then
    rm -rf backend/.venv backend/.pytest_cache backend/.ruff_cache backend/openapi.json
    find backend -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null
    rm -rf frontend/node_modules frontend/dist
    echo "Local dev artifacts removed."
  fi

  echo "Done. Next run of scripts/run.sh $env rebuilds/recreates whatever you removed."
  exit 0
fi

echo "==> Checking migrations ($env)…"
set +e
scripts/migrate.sh "$env"
migrate_status=$?
set -e
if [[ $migrate_status -ne 0 && $migrate_status -ne 2 ]]; then
  echo "Migration check failed unexpectedly — see output above." >&2
  exit 1
fi

echo "==> Starting '$env' — logs below, Ctrl+C to stop…"
compose "$env" up --build
