#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
markdown_file="${project_root}/docs/report/engineering_manual_unitree_l1_docker_rviz_octomap.md"
roff_file="${project_root}/docs/report/engineering_manual_unitree_l1_docker_rviz_octomap.roff"
output_file="${project_root}/docs/report/pdf/03_octomap_mapping/ENGINEERING_MANUAL_UNITREE_L1_DOCKER_RVIZ_OCTOMAP.pdf"
temporary_directory="$(mktemp -d)"
trap 'rm -rf "${temporary_directory}"' EXIT

for command_name in \
  python3 groff ps2pdf pdfinfo pdftotext grep awk sha256sum; do
  command -v "${command_name}" >/dev/null || {
    printf 'Required command is missing: %s\n' "${command_name}" >&2
    exit 1
  }
done

mkdir -p "$(dirname "${output_file}")"

python3 "${project_root}/scripts/generate-engineering-manual-roff.py" \
  "${markdown_file}" "${roff_file}"

postscript_file="${temporary_directory}/engineering-manual.ps"
text_file="${temporary_directory}/engineering-manual.txt"

groff -Kutf8 -Tps "${roff_file}" >"${postscript_file}"
ps2pdf -dPDFSETTINGS=/prepress -sPAPERSIZE=a4 \
  "${postscript_file}" "${output_file}"

page_count="$(pdfinfo "${output_file}" | awk '/^Pages:/ {print $2}')"
if ((page_count < 30 || page_count > 55)); then
  printf 'Unexpected engineering-manual page count: %s (expected 30..55).\n' \
    "${page_count}" >&2
  exit 1
fi

test "$(pdfinfo "${output_file}" | awk '/^Page size:/ {print $3, $5}')" = \
  "595 842"

pdftotext "${output_file}" "${text_file}"

for marker in \
  'Part 1 — Unitree L1 configuration' \
  'Part 2 — RViz2 configuration' \
  'Part 3 — OctoMap setup' \
  'ros@<container>:/workspace/ros2_ws' \
  'docker compose version' \
  'unitre_lidar_sdk_node' \
  'unitree_lidar_ros2_node' \
  '/dev/unitree_lidar' \
  '/unilidar/cloud' \
  'l1_octomap_bringup' \
  'GroupAction(scoped=True)' \
  'octomap_saver_node' \
  'static_sensor:=false' \
  'One physical LiDAR. One driver. One Docker runtime.'; do
  grep -Fq -- "${marker}" "${text_file}" || {
    printf 'Required engineering-manual marker is missing: %s\n' \
      "${marker}" >&2
    exit 1
  }
done

if grep -Fq 'ros2_ws/src/install/setup.bash       correct overlay' \
  "${text_file}"; then
  printf '%s\n' 'Incorrect setup path was labelled as correct.' >&2
  exit 1
fi

printf 'ENGINEERING_MANUAL_PDF_PASS file=%s pages=%s bytes=%s sha256=%s\n' \
  "${output_file}" "${page_count}" "$(stat -c '%s' "${output_file}")" \
  "$(sha256sum "${output_file}" | awk '{print $1}')"
