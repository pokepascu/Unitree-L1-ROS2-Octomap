#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
output_file="${project_root}/docs/report/pdf/03_octomap_mapping/JOURNAL_MATERIEL_COMMANDES_UNITREE_L1_20260716_EN.pdf"
temporary_directory="$(mktemp -d)"
trap 'rm -rf "${temporary_directory}"' EXIT

for command_name in python3 groff ps2pdf gs pdfinfo pdftotext tr grep awk sha256sum; do
  command -v "${command_name}" >/dev/null || {
    printf 'Required command is missing: %s\n' "${command_name}" >&2
    exit 1
  }
done

python3 "${project_root}/scripts/generate-english-command-journal.py"
mkdir -p "$(dirname "${output_file}")"
postscript_file="${temporary_directory}/english-journal.ps"
text_file="${temporary_directory}/english-journal.txt"

groff -Kutf8 -Tps \
  "${project_root}/docs/report/journal_materiel_commandes_20260716_en.roff" \
  >"${postscript_file}"
raw_pdf_file="${temporary_directory}/english-journal-raw.pdf"
ps2pdf -dPDFSETTINGS=/prepress -sPAPERSIZE=a4 \
  "${postscript_file}" "${raw_pdf_file}"

page_count="$(pdfinfo "${raw_pdf_file}" | awk '/^Pages:/ {print $2}')"
last_page_text="$(pdftotext -f "${page_count}" -l "${page_count}" "${raw_pdf_file}" - | tr -d '[:space:]')"
if [[ "${last_page_text}" =~ ^[0-9]+$ ]]; then
  trimmed_pdf_file="${temporary_directory}/english-journal-trimmed.pdf"
  gs -q -dBATCH -dNOPAUSE -sDEVICE=pdfwrite \
    -dFirstPage=1 -dLastPage="$((page_count - 1))" \
    -sOutputFile="${trimmed_pdf_file}" "${raw_pdf_file}"
  cp "${trimmed_pdf_file}" "${output_file}"
  page_count="$(pdfinfo "${output_file}" | awk '/^Pages:/ {print $2}')"
fi
if ((page_count < 20 || page_count > 80)); then
  printf 'Unexpected English journal page count: %s (expected 20..80).\n' \
    "${page_count}" >&2
  exit 1
fi
test "$(pdfinfo "${output_file}" | awk '/^Page size:/ {print $3, $5}')" = "595 842"
pdftotext "${output_file}" "${text_file}"

for marker in \
  'Complete English command journal' \
  'CMD-001' \
  'CMD-031' \
  'CMD-055' \
  'CMD-070' \
  'CMD-086' \
  'OCTOMAP_MARKER_PROBE_PASS' \
  'OCTOMAP_SAVE_PASS' \
  'JOURNAL_MATERIEL_COMMANDES_UNITREE_L1_20260716_EN.pdf'; do
  grep -Fq -- "${marker}" "${text_file}" || {
    printf 'Required English journal marker is missing: %s\n' "${marker}" >&2
    exit 1
  }
done

printf 'ENGLISH_COMMAND_JOURNAL_PDF_PASS output=%s pages=%s sha256=%s\n' \
  "${output_file}" "${page_count}" \
  "$(sha256sum "${output_file}" | awk '{print $1}')"
