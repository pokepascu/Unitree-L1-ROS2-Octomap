#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source_file="${project_root}/docs/report/tutorial_docker_lidar_rviz_octomap_unitree_l1.roff"
output_file="${project_root}/docs/report/pdf/03_octomap_mapping/TUTORIAL_DOCKER_LIDAR_RVIZ_OCTOMAP_UNITREE_L1.pdf"
temporary_directory="$(mktemp -d)"
trap 'rm -rf "${temporary_directory}"' EXIT

for command_name in groff ps2pdf pdfinfo pdftotext grep awk sha256sum; do
  command -v "${command_name}" >/dev/null || {
    printf 'Required command is missing: %s\n' "${command_name}" >&2
    exit 1
  }
done

mkdir -p "$(dirname "${output_file}")"
postscript_file="${temporary_directory}/docker-lidar-rviz-octomap.ps"
text_file="${temporary_directory}/docker-lidar-rviz-octomap.txt"

groff -Kutf8 -Tps "${source_file}" >"${postscript_file}"
ps2pdf -dPDFSETTINGS=/prepress -sPAPERSIZE=a4 \
  "${postscript_file}" "${output_file}"

page_count="$(pdfinfo "${output_file}" | awk '/^Pages:/ {print $2}')"
if ((page_count < 12 || page_count > 13)); then
  printf 'Unexpected tutorial page count: %s (expected 12..13).\n' \
    "${page_count}" >&2
  exit 1
fi
test "$(pdfinfo "${output_file}" | awk '/^Page size:/ {print $3, $5}')" = \
  "595 842"
pdftotext "${output_file}" "${text_file}"

for marker in \
  'Unitree L1' \
  'inside Docker' \
  'HOST_NATIVE_RVIZ_ABSENT' \
  'LIDAR_DATA_VALIDATION_PASS' \
  '/unilidar/cloud' \
  'OCTOMAP_MAPPING_HEALTH_PASS' \
  'OCTOMAP_SAVE_PASS' \
  'view-octomap.sh' \
  'Quick command card'; do
  grep -Fq -- "${marker}" "${text_file}" || {
    printf 'Required tutorial marker is missing: %s\n' "${marker}" >&2
    exit 1
  }
done

printf 'DOCKER_LIDAR_RVIZ_OCTOMAP_TUTORIAL_PDF_PASS file=%s pages=%s sha256=%s\n' \
  "${output_file}" "${page_count}" \
  "$(sha256sum "${output_file}" | awk '{print $1}')"
