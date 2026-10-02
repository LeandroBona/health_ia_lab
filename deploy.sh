#!/usr/bin/env bash
set -Eeuo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")"

if [[ ! -f .env.production ]]; then
  echo "Crie .env.production a partir de .env.production.example antes do deploy." >&2
  exit 1
fi
if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "deploy.sh requer um checkout Git; use git clone na VPS." >&2
  exit 1
fi
if ! docker compose version >/dev/null 2>&1; then
  echo "Docker Compose v2 não está disponível." >&2
  exit 1
fi
if ! docker info >/dev/null 2>&1; then
  echo "O daemon Docker não está disponível." >&2
  exit 1
fi

git pull --ff-only
docker compose --env-file .env.production build
docker compose --env-file .env.production up -d

echo "Atualização concluída. Teste: curl -f http://127.0.0.1:8080/api/health"
