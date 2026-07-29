#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
temporary_directory="$(mktemp -d)"
trap 'rm -rf "${temporary_directory}"' EXIT

for command_name in groff ps2pdf pdfinfo pdftotext grep awk sha256sum; do
  command -v "${command_name}" >/dev/null || {
    printf 'Required command is missing: %s\n' "${command_name}" >&2
    exit 1
  }
done

build_report() {
  source_file="$1"
  output_file="$2"
  minimum_pages="$3"
  maximum_pages="$4"
  shift 4

  mkdir -p "$(dirname "${output_file}")"
  base_name="$(basename "${output_file}" .pdf)"
  postscript_file="${temporary_directory}/${base_name}.ps"
  text_file="${temporary_directory}/${base_name}.txt"

  test -r "${source_file}"
  groff -Kutf8 -Tps "${source_file}" >"${postscript_file}"
  ps2pdf -dPDFSETTINGS=/prepress -sPAPERSIZE=a4 \
    "${postscript_file}" "${output_file}"

  page_count="$(pdfinfo "${output_file}" | awk '/^Pages:/ {print $2}')"
  if ((page_count < minimum_pages || page_count > maximum_pages)); then
    printf 'Unexpected page count for %s: %s (expected %s..%s).\n' \
      "${output_file}" "${page_count}" "${minimum_pages}" \
      "${maximum_pages}" >&2
    exit 1
  fi
  test "$(pdfinfo "${output_file}" | awk '/^Page size:/ {print $3, $5}')" = \
    "595 842"

  pdftotext "${output_file}" "${text_file}"
  for marker in "$@"; do
    grep -Fq -- "${marker}" "${text_file}" || {
      printf 'Required report marker is missing from %s: %s\n' \
        "${output_file}" "${marker}" >&2
      exit 1
    }
  done

  printf 'COMPLETE_REPORT_PDF_PASS file=%s pages=%s sha256=%s\n' \
    "${output_file}" "${page_count}" \
    "$(sha256sum "${output_file}" | awk '{print $1}')"
}

build_report \
  "${project_root}/docs/report/complete_configuration_report_unitree_l1.roff" \
  "${project_root}/docs/report/pdf/01_environment/COMPLETE_CONFIGURATION_REPORT_UNITREE_L1.pdf" \
  26 28 \
  'Complete configuration report' \
  '1bd7d95d8ab7ce7a22058d2bb07e39fd62612aa6' \
  'LIDAR_DATA_VALIDATION_PASS' \
  '6,400' \
  '58,202' \
  'HOST_NATIVE_RVIZ_ABSENT' \
  'ERR-029' \
  'TST-012 remains PENDING' \
  'Fifteen project tests pass'

build_report \
  "${project_root}/docs/report/docker_rviz2_usage_report_unitree_l1.roff" \
  "${project_root}/docs/report/pdf/02_lidar_and_rviz/DOCKER_RVIZ2_USAGE_REPORT_UNITREE_L1.pdf" \
  16 18 \
  'Docker-only RViz2' \
  'GUI_SMOKE_TEST_PASS' \
  'START_RVIZ=true' \
  '/unilidar/cloud' \
  'HOST_NATIVE_RVIZ_ABSENT' \
  'use_sim_time=true' \
  '/occupied_cells_vis_array' \
  '/workspace/ros2_ws/src/l1_bringup/config/my_l1_view.rviz' \
  'OCTOMAP_MAPPING_HEALTH_PASS' \
  'quick command card'
