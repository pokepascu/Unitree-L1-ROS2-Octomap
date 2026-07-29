#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
output_directory="${project_root}/docs/report/pdf/03_octomap_mapping"
temporary_directory="$(mktemp -d)"
trap 'rm -rf "${temporary_directory}"' EXIT

for command_name in groff ps2pdf pdfinfo pdftotext grep awk sha256sum; do
  command -v "${command_name}" >/dev/null || {
    printf 'Required command is missing: %s\n' "${command_name}" >&2
    exit 1
  }
done
mkdir -p "${output_directory}"

build_copy() {
  source_file="$1"
  output_file="$2"
  minimum_pages="$3"
  maximum_pages="$4"
  shift 4
  base_name="$(basename "${output_file}" .pdf)"
  ps_file="${temporary_directory}/${base_name}.ps"
  text_file="${temporary_directory}/${base_name}.txt"

  test -r "${source_file}"
  groff -Kutf8 -Tps "${source_file}" >"${ps_file}"
  ps2pdf -dPDFSETTINGS=/prepress -sPAPERSIZE=a4 "${ps_file}" "${output_file}"
  page_count="$(pdfinfo "${output_file}" | awk '/^Pages:/ {print $2}')"
  test "${page_count}" -ge "${minimum_pages}"
  test "${page_count}" -le "${maximum_pages}"
  test "$(pdfinfo "${output_file}" | awk '/^Page size:/ {print $3, $5}')" = "595 842"
  pdftotext "${output_file}" "${text_file}"
  for marker in "$@"; do
    grep -Fq -- "${marker}" "${text_file}"
  done
  printf 'ENGLISH_OCTOMAP_COPY_PASS file=%s pages=%s sha256=%s\n' \
    "${output_file}" "${page_count}" \
    "$(sha256sum "${output_file}" | awk '{print $1}')"
}

build_copy \
  "${project_root}/docs/report/tutorial_unitree_l1_octomap_mapping.roff" \
  "${output_directory}/TUTORIAL_UNITREE_L1_OCTOMAP_MAPPING_EN.pdf" \
  7 12 \
  'static_sensor:=true' \
  '/occupied_cells_vis_array' \
  'OCTOMAP_SAVE_PASS' \
  'static_sensor:=false'

build_copy \
  "${project_root}/docs/report/rapport_configuration_unitree_l1_octomap.roff" \
  "${output_directory}/RAPPORT_CONFIGURATION_UNITREE_L1_OCTOMAP_EN.pdf" \
  7 12 \
  'catkinConfig.cmake' \
  'l1_octomap_bringup' \
  'OCTOMAP_MARKER_PROBE_PASS' \
  'OCTOMAP_SAVE_PASS'
