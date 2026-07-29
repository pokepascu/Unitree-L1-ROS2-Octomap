#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
[[ $# -eq 1 ]] || {
  printf 'Usage: %s bags/<bag-directory>\n' "$0" >&2
  exit 2
}
bag_host="$(realpath -e -- "${1}")"
case "${bag_host}" in
  "${project_root}/bags/"*) ;;
  *) printf 'Bag must be inside %s/bags.\n' "${project_root}" >&2; exit 2 ;;
esac
test -f "${bag_host}/metadata.yaml"
bag_container="/workspace/bags/${bag_host#"${project_root}/bags/"}"
export HOST_UID="$(id -u)" HOST_GID="$(id -g)"
docker compose -f "${project_root}/docker/compose.yaml" run --rm \
  -e BAG_PATH="${bag_container}" dev \
  bash -lc '
    set -euo pipefail
    /workspace/scripts/assert-ros-container.sh
    ros2 bag info "$BAG_PATH"
  '
