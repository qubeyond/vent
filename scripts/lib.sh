# shellcheck shell=bash

compose() {
  local env="$1"
  shift
  if [[ "$env" != "dev" && "$env" != "prod" ]]; then
    echo "First argument must be 'dev' or 'prod', got: '$env'" >&2
    exit 1
  fi
  local env_file=".env.${env}"
  if [[ ! -f "$env_file" ]]; then
    echo "Missing $env_file. Copy ${env_file}.example to $env_file and fill it in first." >&2
    exit 1
  fi
  docker compose -p "braindump-${env}" \
    -f docker-compose.yml -f "docker-compose.${env}.yml" --env-file "$env_file" "$@"
}

confirm() {
  local reply
  read -r -p "$1 [y/N] " reply
  [[ "$reply" =~ ^[Yy]$ ]]
}
