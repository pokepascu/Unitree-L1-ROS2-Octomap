#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source_file="${project_root}/docs/configuration-log.md"
output_file="${project_root}/docs/report/pdf/01_environment/CONFIGURATION_LOG_UNITREE_L1.pdf"
temporary_directory="$(mktemp -d)"
trap 'rm -rf "${temporary_directory}"' EXIT

for command_name in groff ps2pdf fold sed awk pdftotext pdfinfo; do
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
} >"${temporary_directory}/configuration-log.roff"

groff -Kutf8 -Tps "${temporary_directory}/configuration-log.roff" \
  >"${temporary_directory}/configuration-log.ps"
ps2pdf -sPAPERSIZE=a4 -dPDFSETTINGS=/prepress \
  "${temporary_directory}/configuration-log.ps" "${output_file}"

temporary_text="${temporary_directory}/configuration-log.txt"
pdftotext "${output_file}" "${temporary_text}"
for marker in \
  'LOG-20260716-049' \
  'ERR-20260716-025' \
  'OCTOMAP_SAVE_PASS' \
  '3dbe4c6b278079573d395bf437629e30c326f614' \
  'LOG-20260723-075' \
  'PDF_CODE_LINE_CHECK checked=813 missing=0' \
  '13b6dbee62957330f005d4a091d33e0720d2f6520db20e526027fba5d8f52fbf'; do
  grep -q "${marker}" "${temporary_text}"
done
pdfinfo "${output_file}" | grep -q '^Page size:.*A4'
printf 'CONFIGURATION_LOG_PDF_PASS output=%s pages=' "${output_file}"
pdfinfo "${output_file}" | awk '/^Pages:/ {print $2}'
