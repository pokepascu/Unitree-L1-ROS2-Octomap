#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source_file="${project_root}/docs/report/journal_materiel_commandes_20260716.md"
output_file="${project_root}/docs/report/pdf/03_octomap_mapping/JOURNAL_MATERIEL_COMMANDES_UNITREE_L1_20260716.pdf"
temporary_directory="$(mktemp -d)"
trap 'rm -rf "${temporary_directory}"' EXIT

for command_name in groff ps2pdf fold sed pdftotext pdfinfo; do
  command -v "${command_name}" >/dev/null || {
    printf 'Required command is missing: %s\n' "${command_name}" >&2
    exit 1
  }
done
test -r "${source_file}"
mkdir -p "$(dirname "${output_file}")"

fold -s -w 92 "${source_file}" |
  sed -e 's/\\/\\e/g' -e "/^[.']/s/^/\\\\\&/" |
  awk '
    /^## /  { print ".ne 7v" }
    /^### / { print ".ne 5v" }
    { print }
  ' >"${temporary_directory}/body.roff"

{
  printf '%s\n' \
    '.po 1.35c' \
    '.ll 18.3c' \
    '.pl 29.7c' \
    '.ps 8.5' \
    '.vs 10.5' \
    '.ft CR' \
    '.nf' \
    '.hy 0'
  cat "${temporary_directory}/body.roff"
} >"${temporary_directory}/journal.roff"

groff -Kutf8 -Tps "${temporary_directory}/journal.roff" >"${temporary_directory}/journal.ps"
ps2pdf -sPAPERSIZE=a4 -dPDFSETTINGS=/prepress \
  "${temporary_directory}/journal.ps" "${output_file}"

temporary_text="${temporary_directory}/journal.txt"
pdftotext "${output_file}" "${temporary_text}"
for marker in CMD-003 LIDAR_DATA_VALIDATION_PASS PATCH-011 CMD-023 CMD-066 CMD-079 OCTOMAP_MARKER_PROBE_PASS 9c87d26f; do
  grep -q "${marker}" "${temporary_text}"
done
pdfinfo "${output_file}" | grep -q '^Page size:.*A4'
printf 'HARDWARE_JOURNAL_PDF_PASS output=%s pages=' "${output_file}"
pdfinfo "${output_file}" | awk '/^Pages:/ {print $2}'
