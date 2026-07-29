#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source_file="${project_root}/docs/report/synthese_pre_materiel.roff"
output_file="${project_root}/docs/report/pdf/00_preparation/SYNTHESE_UNITREE_L1_PRE_MATERIEL.pdf"
temporary_ps="$(mktemp --suffix=.ps)"
temporary_text="$(mktemp --suffix=.txt)"
trap 'rm -f "${temporary_ps}" "${temporary_text}"' EXIT

command -v groff >/dev/null
command -v ps2pdf >/dev/null
command -v pdfinfo >/dev/null
command -v pdftotext >/dev/null
mkdir -p "$(dirname "${output_file}")"

groff -Kutf8 -Tps "${source_file}" > "${temporary_ps}"
ps2pdf -dPDFSETTINGS=/prepress -sPAPERSIZE=a4 \
  "${temporary_ps}" "${output_file}"

test "$(pdfinfo "${output_file}" | awk '/^Pages:/ {print $2}')" -eq 3
test "$(pdfinfo "${output_file}" | awk '/^Page size:/ {print $3, $5}')" = "595 842"
pdftotext "${output_file}" "${temporary_text}"
grep -q "Environnement logiciel validé" "${temporary_text}"
grep -q "8 réussis sur 8" "${temporary_text}"
grep -q "Prochaine étape matérielle" "${temporary_text}"
grep -q "./scripts/check-lidar.sh" "${temporary_text}"

printf 'PDF_SYNTHESIS_PASS file=%s sha256=%s\n' \
  "${output_file}" "$(sha256sum "${output_file}" | awk '{print $1}')"
