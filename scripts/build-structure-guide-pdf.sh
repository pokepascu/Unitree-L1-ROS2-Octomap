#!/usr/bin/env bash
set -euo pipefail

export LC_ALL=C.UTF-8
umask 022

project_root="$(cd "$(dirname "$0")/.." && pwd)"
source_file="$project_root/docs/report/guide_structure_projet_unitree_l1.roff"
output_directory="$project_root/docs/report/pdf/01_environment"
output_file="$output_directory/GUIDE_STRUCTURE_PROJET_UNITREE_L1.pdf"
temporary_directory="$(mktemp -d)"
trap 'rm -rf "$temporary_directory"' EXIT

for command_name in awk grep groff gs pdfinfo pdftotext ps2pdf sha256sum; do
  command -v "$command_name" >/dev/null || {
    printf 'Required command is missing: %s\n' "$command_name" >&2
    exit 1
  }
done

[[ -r "$source_file" ]] || {
  printf 'Roff source is missing or unreadable: %s\n' "$source_file" >&2
  exit 1
}
[[ -d "$output_directory" ]] || {
  printf 'PDF directory does not exist yet: %s\n' "$output_directory" >&2
  printf '%s\n' 'Create and organize docs/report/pdf before running this generator.' >&2
  exit 2
}
[[ -w "$output_directory" ]] || {
  printf 'PDF directory is not writable: %s\n' "$output_directory" >&2
  exit 2
}

postscript_file="$temporary_directory/guide_structure.ps"
candidate_pdf="$temporary_directory/GUIDE_STRUCTURE_PROJET_UNITREE_L1.pdf"
text_file="$temporary_directory/guide_structure.txt"
bounds_file="$temporary_directory/guide_structure.bounds"

groff -Kutf8 -Tps "$source_file" >"$postscript_file"
ps2pdf \
  -dCompatibilityLevel=1.4 \
  -dPDFSETTINGS=/prepress \
  -sPAPERSIZE=a4 \
  "$postscript_file" \
  "$candidate_pdf"

page_count="$(pdfinfo "$candidate_pdf" | awk '/^Pages:/ {print $2; exit}')"
[[ "$page_count" =~ ^[0-9]+$ ]] || {
  printf 'Unable to read PDF page count.\n' >&2
  exit 1
}
if ((page_count < 9 || page_count > 14)); then
  printf 'Unexpected page count: %s (expected 9 to 14).\n' "$page_count" >&2
  exit 1
fi

read -r page_width page_height < <(
  pdfinfo "$candidate_pdf" |
    awk '/^Page size:/ {print $3, $5; exit}'
)
awk -v width="$page_width" -v height="$page_height" '
  BEGIN {
    if (width < 594.0 || width > 596.0 || height < 841.0 || height > 843.0) {
      exit 1
    }
  }
' || {
  printf 'PDF is not A4 portrait: width=%s height=%s points.\n' \
    "$page_width" "$page_height" >&2
  exit 1
}

read -r media_llx media_lly media_urx media_ury < <(
  pdfinfo -box "$candidate_pdf" |
    awk '/^MediaBox:/ {print $2, $3, $4, $5; exit}'
)
awk \
  -v llx="$media_llx" -v lly="$media_lly" \
  -v urx="$media_urx" -v ury="$media_ury" '
  BEGIN {
    if (llx < -0.1 || llx > 0.1 || lly < -0.1 || lly > 0.1 ||
        urx < 594.0 || urx > 596.0 || ury < 841.0 || ury > 843.0) {
      exit 1
    }
  }
' || {
  printf 'Unexpected PDF MediaBox: %s %s %s %s.\n' \
    "$media_llx" "$media_lly" "$media_urx" "$media_ury" >&2
  exit 1
}

gs -q -dNOPAUSE -dBATCH -sDEVICE=bbox \
  "$candidate_pdf" >/dev/null 2>"$bounds_file"
bounds_count="$(
  awk '/^%%HiResBoundingBox:/ {count++} END {print count + 0}' \
    "$bounds_file"
)"
[[ "$bounds_count" -eq "$page_count" ]] || {
  printf 'Bounding-box count differs from page count: %s versus %s.\n' \
    "$bounds_count" "$page_count" >&2
  exit 1
}
awk '
  /^%%HiResBoundingBox:/ {
    page++
    if ($2 < -0.1 || $3 < -0.1 || $4 > 595.5 || $5 > 842.5) {
      printf "Content outside A4 bounds on page %d: %s\n", page, $0 > "/dev/stderr"
      invalid = 1
    }
  }
  END {
    exit invalid
  }
' "$bounds_file"

pdftotext "$candidate_pdf" "$text_file"
while IFS= read -r marker; do
  grep -Fq -- "$marker" "$text_file" || {
    printf 'Required PDF marker is missing: %s\n' "$marker" >&2
    exit 1
  }
done <<'MARKERS'
Deux côtés, un seul projet
ros2_ws/colcon_defaults.yaml
l1_octomap_bringup
find_package
catkinConfig.cmake
OCTOMAPConfig.cmake
OctoMap ne calcule pas la pose
git remote add origin
Zones protégées et glossaire
MARKERS

mv -f "$candidate_pdf" "$output_file"
printf 'STRUCTURE_GUIDE_PDF_PASS file=%s pages=%s sha256=%s\n' \
  "$output_file" \
  "$page_count" \
  "$(sha256sum "$output_file" | awk '{print $1}')"
