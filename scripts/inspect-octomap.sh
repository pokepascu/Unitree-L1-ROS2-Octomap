#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
map_name="${1:-}"

if [[ "${map_name}" == -h || "${map_name}" == --help ]]; then
  printf 'Usage: %s MAP_NAME.bt|MAP_NAME.ot\n' "$0"
  exit 0
fi
if [[ -z "${map_name}" ]]; then
  printf 'Usage: %s MAP_NAME.bt|MAP_NAME.ot\n' "$0" >&2
  exit 2
fi
[[ "${map_name}" =~ ^[A-Za-z0-9][A-Za-z0-9_.-]*\.(bt|ot)$ ]] || {
  printf 'Map name must be a safe basename ending in .bt or .ot: %s\n' \
    "${map_name}" >&2
  exit 2
}

map_path="${project_root}/maps/${map_name}"
[[ -f "${map_path}" && -r "${map_path}" ]] || {
  printf 'Saved map is not readable: %s\n' "${map_path}" >&2
  exit 3
}

header="$(head -n 7 -- "${map_path}")"
first_line="$(printf '%s\n' "${header}" | sed -n '1p')"
tree_id="$(printf '%s\n' "${header}" | awk '$1 == "id" {print $2}')"
stored_nodes="$(printf '%s\n' "${header}" | awk '$1 == "size" {print $2}')"
resolution="$(printf '%s\n' "${header}" | awk '$1 == "res" {print $2}')"
last_header_line="$(printf '%s\n' "${header}" | tail -n 1)"

[[ "${first_line}" == '# Octomap '* ]] || {
  printf 'Not an OctoMap file: %s\n' "${map_path}" >&2
  exit 4
}
[[ "${tree_id}" =~ ^[A-Za-z0-9_]+$ ]] || {
  printf 'Missing or invalid OctoMap tree id.\n' >&2
  exit 4
}
[[ "${stored_nodes}" =~ ^[0-9]+$ && "${stored_nodes}" -gt 0 ]] || {
  printf 'Missing or invalid stored node count.\n' >&2
  exit 4
}
[[ "${resolution}" =~ ^[0-9]+([.][0-9]+)?$ ]] || {
  printf 'Missing or invalid OctoMap resolution.\n' >&2
  exit 4
}
[[ "${last_header_line}" == data ]] || {
  printf 'OctoMap header does not end with the data marker.\n' >&2
  exit 4
}

printf 'file=%s\n' "${map_path}"
printf 'format=%s tree_id=%s stored_nodes=%s resolution_m=%s\n' \
  "${map_name##*.}" "${tree_id}" "${stored_nodes}" "${resolution}"
printf 'bytes=%s modified=%s\n' \
  "$(stat -c '%s' "${map_path}")" "$(stat -c '%y' "${map_path}")"
printf 'sha256=%s\n' "$(sha256sum "${map_path}" | awk '{print $1}')"
printf 'OCTOMAP_INSPECT_PASS map=%s\n' "${map_name}"
