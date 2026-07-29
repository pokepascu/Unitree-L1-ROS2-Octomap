#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export HOST_UID="$(id -u)"
export HOST_GID="$(id -g)"
export VIDEO_GID="$(stat -Lc '%g' /dev/dri/card0)"
export RENDER_GID="$(stat -Lc '%g' /dev/dri/renderD128)"
: "${DISPLAY:?DISPLAY doit désigner la session graphique}"
: "${XAUTHORITY:?XAUTHORITY doit pointer vers le cookie X11}"
test -r "${XAUTHORITY}"

docker compose \
  -f "${project_root}/docker/compose.yaml" \
  -f "${project_root}/docker/compose.gui.yaml" \
  run --rm -e REQUIRE_GUI=true dev \
  bash -lc 'set -euo pipefail
    /workspace/scripts/assert-ros-container.sh
    xdpyinfo >/dev/null
    glxinfo -B
    rviz2 --help >/dev/null
    printf "%s\n" "GUI_SMOKE_TEST_PASS display=${DISPLAY}"'
