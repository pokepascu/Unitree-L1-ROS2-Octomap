#!/usr/bin/env bash
set -euo pipefail

runtime_container="${RUNTIME_CONTAINER:-unitree_l1_runtime}"
require_rviz="${REQUIRE_RVIZ:-true}"

[[ $# -eq 0 ]] || {
  printf 'Usage: RUNTIME_CONTAINER=name REQUIRE_RVIZ=true|false %s\n' "$0" >&2
  exit 2
}
[[ "${runtime_container}" =~ ^[A-Za-z0-9][A-Za-z0-9_.-]+$ ]] || {
  printf 'Invalid RUNTIME_CONTAINER name: %s\n' "${runtime_container}" >&2
  exit 2
}
[[ "${require_rviz}" == true || "${require_rviz}" == false ]] || {
  printf 'REQUIRE_RVIZ accepts only true or false.\n' >&2
  exit 2
}
[[ "$(docker inspect -f '{{.State.Running}}' "${runtime_container}" 2>/dev/null || true)" == true ]] || {
  printf 'Runtime container is not active: %s\n' "${runtime_container}" >&2
  exit 3
}

# Reading the host release only explains its role; no ROS command is run here.
# shellcheck disable=SC1091
source /etc/os-release
printf 'host_role=docker_client_x11_server host_os=%s-%s\n' \
  "${ID:-unknown}" "${VERSION_ID:-unknown}"
printf 'container_name=%s image=%s init_pid=%s\n' \
  "${runtime_container}" \
  "$(docker inspect -f '{{.Config.Image}}' "${runtime_container}")" \
  "$(docker inspect -f '{{.State.Pid}}' "${runtime_container}")"

docker exec -e REQUIRE_GUI="${require_rviz}" "${runtime_container}" \
  /workspace/scripts/assert-ros-container.sh

if [[ "${require_rviz}" == true ]]; then
  rviz_processes="$(docker top "${runtime_container}" -eo pid,comm,args | \
    awk 'NR == 1 || $0 ~ /(^|[ /])rviz2([[:space:]]|$)/')"
  if [[ "$(printf '%s\n' "${rviz_processes}" | wc -l)" -lt 2 ]]; then
    printf 'RVIZ_CONTAINER_PROCESS_FAIL: rviz2 is not running in %s.\n' \
      "${runtime_container}" >&2
    exit 4
  fi
  printf '%s\n' "${rviz_processes}"

  while read -r rviz_pid; do
    [[ -z "${rviz_pid}" || -f "/proc/${rviz_pid}/root/.dockerenv" ]] || {
      printf 'HOST_NATIVE_RVIZ_PROCESS_FAIL pid=%s\n' "${rviz_pid}" >&2
      exit 5
    }
  done < <(ps -eo pid=,comm= | awk '$2 == "rviz2" {print $1}')
  printf '%s\n' HOST_NATIVE_RVIZ_ABSENT
fi

printf 'DOCKER_ONLY_PIPELINE_PASS container=%s rviz_required=%s\n' \
  "${runtime_container}" "${require_rviz}"
