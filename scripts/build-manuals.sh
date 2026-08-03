#!/usr/bin/env bash
set -euo pipefail

export LC_ALL=C.UTF-8
umask 022

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source_directory="${project_root}/docs/manuals"
output_directory="${project_root}/exports/manuals"
temporary_directory="$(mktemp -d)"
trap 'rm -rf "${temporary_directory}"' EXIT

for command_name in \
  awk find grep groff gs pdfinfo pdffonts pdftotext ps2pdf python3 sha256sum; do
  command -v "${command_name}" >/dev/null || {
    printf 'Required PDF tool is missing: %s\n' "${command_name}" >&2
    exit 1
  }
done

mkdir -p "${output_directory}"

build_document() {
  local source_name="$1"
  local output_name="$2"
  local title="$3"
  local minimum_pages="$4"
  shift 4

  local source_file="${source_directory}/${source_name}"
  local roff_file="${temporary_directory}/${source_name%.md}.roff"
  local postscript_file="${temporary_directory}/${source_name%.md}.ps"
  local groff_errors="${temporary_directory}/${source_name%.md}.groff-errors"
  local candidate_pdf="${temporary_directory}/${output_name}"
  local text_file="${temporary_directory}/${source_name%.md}.txt"
  local bounds_file="${temporary_directory}/${source_name%.md}.bounds"
  local output_file="${output_directory}/${output_name}"
  local pdf_title="${title// /_}"

  test -r "${source_file}"
  "${project_root}/scripts/render-manual.py" "${source_file}" "${roff_file}"
  groff -Kutf8 -t -Tps "${roff_file}" \
    >"${postscript_file}" 2>"${groff_errors}"
  if [[ -s "${groff_errors}" ]]; then
    printf 'groff reported layout warnings for %s:\n' "${source_name}" >&2
    cat "${groff_errors}" >&2
    exit 1
  fi
  ps2pdf \
    -dCompatibilityLevel=1.7 \
    -dPDFSETTINGS=/prepress \
    -dEmbedAllFonts=true \
    -dSubsetFonts=true \
    -sPAPERSIZE=a4 \
    -sTitle="${pdf_title}" \
    -sAuthor=Unitree_L1_ROS_2_project \
    "${postscript_file}" "${candidate_pdf}"

  local page_count
  page_count="$(pdfinfo "${candidate_pdf}" | awk '/^Pages:/ {print $2; exit}')"
  [[ "${page_count}" =~ ^[0-9]+$ ]] || {
    printf 'Unable to determine page count for %s.\n' "${output_name}" >&2
    exit 1
  }
  ((page_count >= minimum_pages && page_count <= 80)) || {
    printf 'Unexpected page count for %s: %s (expected %s..80).\n' \
      "${output_name}" "${page_count}" "${minimum_pages}" >&2
    exit 1
  }

  read -r page_width page_height < <(
    pdfinfo "${candidate_pdf}" |
      awk '/^Page size:/ {print $3, $5; exit}'
  )
  awk -v width="${page_width}" -v height="${page_height}" '
    BEGIN {
      if (width < 594.0 || width > 596.0 ||
          height < 841.0 || height > 843.0) {
        exit 1
      }
    }
  ' || {
    printf 'PDF is not A4 portrait: %s (%s x %s points).\n' \
      "${output_name}" "${page_width}" "${page_height}" >&2
    exit 1
  }

  gs -q -dNOPAUSE -dBATCH -sDEVICE=bbox \
    "${candidate_pdf}" >/dev/null 2>"${bounds_file}"
  test "$(
    awk '/^%%HiResBoundingBox:/ {count++} END {print count + 0}' \
      "${bounds_file}"
  )" -eq "${page_count}"
  awk '
    /^%%HiResBoundingBox:/ {
      page++
      if ($2 < -0.1 || $3 < -0.1 || $4 > 595.5 || $5 > 842.5) {
        printf "Content outside A4 on page %d: %s\n", page, $0 > "/dev/stderr"
        invalid = 1
      }
    }
    END { exit invalid }
  ' "${bounds_file}"

  pdftotext "${candidate_pdf}" "${text_file}"
  for required_marker in "$@"; do
    grep -Fq -- "${required_marker}" "${text_file}" || {
      printf 'Required marker missing from %s: %s\n' \
        "${output_name}" "${required_marker}" >&2
      exit 1
    }
  done

  local font_rows
  font_rows="$(pdffonts "${candidate_pdf}" | awk 'NR > 2 {count++} END {print count + 0}')"
  ((font_rows >= 2)) || {
    printf 'Expected at least two fonts in %s.\n' "${output_name}" >&2
    exit 1
  }

  mv -f "${candidate_pdf}" "${output_file}"
  printf 'MANUAL_PDF_PASS file=%s pages=%s bytes=%s sha256=%s\n' \
    "${output_file}" \
    "${page_count}" \
    "$(stat -c '%s' "${output_file}")" \
    "$(sha256sum "${output_file}" | awk '{print $1}')"
}

build_document \
  engineering-manual.md \
  UNITREE_L1_ENGINEERING_MANUAL.pdf \
  'Unitree L1 Engineering Manual' \
  8 \
  'Engineering Manual' \
  'ros2 launch l1_bringup' \
  'ros2 launch l1_octomap_bringup' \
  '/occupied_cells_vis_array' \
  'Hardware acceptance limitation' \
  'Maintenance and change control'

build_document \
  user-manual.md \
  UNITREE_L1_USER_MANUAL.pdf \
  'Unitree L1 User Manual' \
  6 \
  'User Manual' \
  'Terminal A' \
  'ros2 launch l1_octomap_bringup' \
  'ros2 bag record' \
  'Stop cleanly and inspect the bag'

build_document \
  structure-and-organisation.md \
  UNITREE_L1_STRUCTURE_AND_ORGANISATION.pdf \
  'Unitree L1 Structure and Organisation' \
  5 \
  'Structure and Organisation' \
  'Complete File Inventory' \
  'l1_octomap_bringup' \
  'sleep infinity' \
  'What Runs and When'

printf 'MANUAL_SET_PASS output=%s count=3\n' "${output_directory}"
