#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
gui=true
lidar_mode=auto

usage() {
  cat <<'EOF'
Usage: docker-shell.sh [--gui|--no-gui] [--lidar|--no-lidar]

By default, the shell receives X11/GPU access and automatically attaches the
only stable serial device when exactly one is detected under /dev/serial/by-id.

  --gui       require X11/GPU access (default)
  --no-gui    open a headless shell
  --lidar     require and attach one LiDAR serial device
  --no-lidar  do not attach a serial device
  -h, --help  show this help

LIDAR_DEVICE=/dev/... can select the serial device explicitly.
EOF
}

while (($#)); do
  case "$1" in
    --gui) gui=true ;;
    --no-gui) gui=false ;;
    --lidar) lidar_mode=required ;;
    --no-lidar) lidar_mode=disabled ;;
    -h | --help)
      usage
      exit 0
      ;;
    *)
      printf 'Unknown option: %s\n' "$1" >&2
      usage >&2
      exit 2
      ;;
  esac
  shift
done

export HOST_UID="$(id -u)"
export HOST_GID="$(id -g)"

compose_files=(-f "${project_root}/docker/compose.yaml")

if [[ "${gui}" == true ]]; then
  : "${DISPLAY:?DISPLAY is required; use --no-gui for a headless shell}"
  : "${XAUTHORITY:?XAUTHORITY is required; use --no-gui for a headless shell}"
  [[ -r "${XAUTHORITY}" ]] || {
    printf 'X11 cookie is not readable: %s\n' "${XAUTHORITY}" >&2
    exit 2
  }
  [[ -c /dev/dri/card0 && -c /dev/dri/renderD128 ]] || {
    printf 'Expected GPU devices /dev/dri/card0 and renderD128 are absent.\n' >&2
    exit 2
  }
  export VIDEO_GID="$(stat -Lc '%g' /dev/dri/card0)"
  export RENDER_GID="$(stat -Lc '%g' /dev/dri/renderD128)"
  compose_files+=(-f "${project_root}/docker/compose.gui.yaml")
fi

device="${LIDAR_DEVICE:-}"
if [[ "${lidar_mode}" != disabled ]]; then
  if [[ -z "${device}" ]]; then
    declare -a detected=()
    if [[ -d /dev/serial/by-id ]]; then
      while IFS= read -r -d '' path; do
        resolved="$(readlink -e -- "${path}" 2>/dev/null || true)"
        [[ -n "${resolved}" && -c "${resolved}" ]] && detected+=("${resolved}")
      done < <(find /dev/serial/by-id -maxdepth 1 -type l -print0 | sort -z)
    fi
    mapfile -t detected < <(printf '%s\n' "${detected[@]}" | sed '/^$/d' | sort -u)
    if ((${#detected[@]} == 1)); then
      device="${detected[0]}"
    elif [[ "${lidar_mode}" == required ]]; then
      printf 'Expected exactly one stable serial device, found %d.\n' \
        "${#detected[@]}" >&2
      exit 2
    elif ((${#detected[@]} > 1)); then
      printf 'Several serial devices found; set LIDAR_DEVICE or use --no-lidar.\n' >&2
      exit 2
    fi
  fi

  if [[ -n "${device}" ]]; then
    device="$(readlink -e -- "${device}" 2>/dev/null || true)"
    [[ -n "${device}" && -c "${device}" ]] || {
      printf 'Serial device is absent or invalid: %s\n' "${LIDAR_DEVICE:-<auto>}" >&2
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
      printf '%s\n' 'No process was stopped.' >&2
      exit 3
    fi
    export LIDAR_DEVICE="${device}"
    export LIDAR_GID="$(stat -Lc '%g' "${device}")"
    compose_files+=(-f "${project_root}/docker/compose.lidar.yaml")
  fi
fi

docker compose "${compose_files[@]}" config --quiet

printf 'Opening ROS 2 shell: gui=%s lidar=%s\n' \
  "${gui}" "${device:-not-attached}"
docker compose "${compose_files[@]}" run --rm \
  -e REQUIRE_GUI="${gui}" dev bash -lc '
  /workspace/scripts/assert-ros-container.sh
  printf "\nROS 2 Humble project shell ready.\n"
  printf "Workspace: /workspace/ros2_ws\n"
  printf "Build:     colcon build\n"
  printf "Activate:  source install/setup.bash\n"
  if [[ -n "${LIDAR_PORT:-}" ]]; then
    printf "LiDAR:     %s\n" "${LIDAR_PORT}"
  fi
  printf "\n"
  exec bash
'
