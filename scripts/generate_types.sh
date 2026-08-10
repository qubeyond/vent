#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
source scripts/lib.sh

env="${1:?Usage: scripts/generate_types.sh <dev|prod>}"
compose "$env" exec -T backend python -m app.scripts.export_openapi > backend/openapi.json
(cd frontend && npm run generate-api-types)
echo "Regenerated frontend/src/shared/api/schema.ts from backend/openapi.json"
