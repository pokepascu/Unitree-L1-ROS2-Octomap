#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export HOST_UID="$(id -u)"
export HOST_GID="$(id -g)"

docker compose -f "${project_root}/docker/compose.yaml" build --pull
