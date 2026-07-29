#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd "$(dirname "$0")/.." && pwd)"
temporary_directory="$(mktemp -d)"
trap 'rm -rf "$temporary_directory"' EXIT

for command_name in groff ps2pdf pdfinfo pdftotext grep awk sha256sum; do
  command -v "$command_name" >/dev/null || {
    printf 'Required command is missing: %s\n' "$command_name" >&2
    exit 1
  }
done
mkdir -p "$project_root/docs/report/pdf"

build_pdf() {
  source_file="$1"
  output_file="$2"
  minimum_pages="$3"
  maximum_pages="$4"
  shift 4

  base_name="$(basename "$output_file" .pdf)"
  ps_file="$temporary_directory/$base_name.ps"
  text_file="$temporary_directory/$base_name.txt"

  test -r "$source_file"
  groff -Kutf8 -Tps "$source_file" >"$ps_file"
  ps2pdf -dPDFSETTINGS=/prepress -sPAPERSIZE=a4 "$ps_file" "$output_file"

  page_count="$(pdfinfo "$output_file" | awk '/^Pages:/ {print $2}')"
  test "$page_count" -ge "$minimum_pages"
  test "$page_count" -le "$maximum_pages"
  test "$(pdfinfo "$output_file" | awk '/^Page size:/ {print $3, $5}')" = "595 842"

  pdftotext "$output_file" "$text_file"
  for marker in "$@"; do
    grep -q "$marker" "$text_file"
  done

  printf 'READABLE_PDF_PASS file=%s pages=%s sha256=%s\n' \
    "$output_file" "$page_count" "$(sha256sum "$output_file" | awk '{print $1}')"
}

build_pdf \
  "$project_root/docs/report/rapport_lisible_donnees_unitree_l1.roff" \
  "$project_root/docs/report/pdf/02_lidar_and_rviz/RAPPORT_LISIBLE_LECTURE_DONNEES_UNITREE_L1.pdf" \
  7 12 \
  "Comprendre en quelques minutes" \
  "LIDAR_DATA_VALIDATION_PASS" \
  "29,339711292" \
  "Prochaine étape"

build_pdf \
  "$project_root/docs/report/tutoriel_rviz_unitree_l1.roff" \
  "$project_root/docs/report/pdf/02_lidar_and_rviz/TUTORIEL_RVIZ_UNITREE_L1.pdf" \
  4 7 \
  "Démarrage rapide" \
  "./scripts/check-lidar.sh" \
  "START_RVIZ=true" \
  "LIDAR_DATA_VALIDATION_PASS" \
  "Arrêter proprement"

build_pdf \
  "$project_root/docs/report/tutorial_colcon_rviz2_record_unitree_l1.roff" \
  "$project_root/docs/report/pdf/02_lidar_and_rviz/TUTORIAL_COLCON_RVIZ2_RECORD_UNITREE_L1.pdf" \
  7 12 \
  "colcon build" \
  "LIDAR_DATA_VALIDATION_PASS" \
  "BAG_LABEL=first_scan" \
  "ros2 bag play" \
  "Save Config As"
