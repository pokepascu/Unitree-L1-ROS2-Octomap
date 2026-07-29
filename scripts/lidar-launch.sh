#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
runtime_container="${RUNTIME_CONTAINER:-unitree_l1_runtime}"
start_rviz="${START_RVIZ:-false}"
start_monitor="${START_MONITOR:-true}"

for value in "${start_rviz}" "${start_monitor}"; do
  [[ "${value}" == true || "${value}" == false ]] || {
    printf 'START_RVIZ and START_MONITOR accept only true or false.\n' >&2
    exit 2
  }
done
[[ "${runtime_container}" =~ ^[A-Za-z0-9][A-Za-z0-9_.-]+$ ]] || {
  printf 'Invalid RUNTIME_CONTAINER name: %s\n' "${runtime_container}" >&2
  exit 2
}

device="${LIDAR_DEVICE:-}"
if [[ -z "${device}" ]]; then
  declare -a detected=()
  if [[ -d /dev/serial/by-id ]]; then
    while IFS= read -r -d '' path; do
      resolved="$(readlink -e -- "${path}" 2>/dev/null || true)"
      [[ -n "${resolved}" && -c "${resolved}" ]] && detected+=("${resolved}")
    done < <(find /dev/serial/by-id -maxdepth 1 -type l -print0 | sort -z)
  fi
  mapfile -t detected < <(printf '%s\n' "${detected[@]}" | sed '/^$/d' | sort -u)
  if ((${#detected[@]} != 1)); then
    printf 'Expected exactly one /dev/serial/by-id candidate, found %d.\n' \
      "${#detected[@]}" >&2
    printf '%s\n' 'Run ./scripts/check-lidar.sh, then set LIDAR_DEVICE explicitly.' >&2
    exit 2
  fi
  device="${detected[0]}"
fi

resolved_device="$(readlink -e -- "${device}" 2>/dev/null || true)"
[[ -n "${resolved_device}" ]] || {
  printf 'Serial path does not resolve: %s\n' "${device}" >&2
  exit 2
}
device="${resolved_device}"
[[ -c "${device}" ]] || {
  printf 'Not a character device: %s\n' "${device}" >&2
  exit 2
}
case "$(basename "${device}")" in
  ttyUSB* | ttyACM*) ;;
  *)
    printf 'Refusing unexpected serial device: %s\n' "${device}" >&2
    exit 2
    ;;
esac

if command -v fuser >/dev/null && fuser "${device}" >/dev/null 2>&1; then
  printf 'Serial device is already open: %s\n' "${device}" >&2
  fuser -v "${device}" || true
  printf '%s\n' 'No process was stopped. Resolve ownership before retrying.' >&2
  exit 3
fi
if docker container inspect "${runtime_container}" >/dev/null 2>&1; then
  printf 'Container name already exists: %s\n' "${runtime_container}" >&2
  printf '%s\n' 'Stop the previous run cleanly before retrying.' >&2
  exit 3
fi

export HOST_UID="$(id -u)"
export HOST_GID="$(id -g)"
export LIDAR_DEVICE="${device}"
export LIDAR_GID="$(stat -Lc '%g' "${device}")"
export START_RVIZ="${start_rviz}"
export START_MONITOR="${start_monitor}"

compose_files=(-f "${project_root}/docker/compose.yaml" -f "${project_root}/docker/compose.lidar.yaml")
if [[ "${start_rviz}" == true ]]; then
  : "${DISPLAY:?DISPLAY is required when START_RVIZ=true}"
  : "${XAUTHORITY:?XAUTHORITY is required when START_RVIZ=true}"
  test -r "${XAUTHORITY}"
  export VIDEO_GID="$(stat -Lc '%g' /dev/dri/card0)"
  export RENDER_GID="$(stat -Lc '%g' /dev/dri/renderD128)"
  compose_files+=(-f "${project_root}/docker/compose.gui.yaml")
fi

printf 'Using serial device %s (supplementary GID %s).\n' \
  "${LIDAR_DEVICE}" "${LIDAR_GID}"
printf 'Runtime container=%s, monitor=%s, rviz=%s.\n' \
  "${runtime_container}" "${start_monitor}" "${start_rviz}"

docker compose "${compose_files[@]}" config --quiet
docker compose "${compose_files[@]}" run --rm \
  -e REQUIRE_GUI="${start_rviz}" dev bash -lc '
  set -e
  /workspace/scripts/assert-ros-container.sh
  stat -Lc "container_device=%n mode=%A uid=%u gid=%g" "$LIDAR_PORT"
  test -c "$LIDAR_PORT" && test -r "$LIDAR_PORT" && test -w "$LIDAR_PORT"
  printf "%s\n" LIDAR_CONTAINER_ACCESS_PASS
'

exec docker compose "${compose_files[@]}" run --rm \
  --name "${runtime_container}" \
  -e START_RVIZ="${start_rviz}" \
  -e START_MONITOR="${start_monitor}" \
  -e REQUIRE_GUI="${start_rviz}" \
  dev bash -lc '
    /workspace/scripts/assert-ros-container.sh
    exec ros2 launch l1_bringup unitree_l1.launch.py \
      port:="$LIDAR_PORT" rviz:="$START_RVIZ" monitor:="$START_MONITOR"
  '
