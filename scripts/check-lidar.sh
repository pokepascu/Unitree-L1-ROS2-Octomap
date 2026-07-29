#!/usr/bin/env bash
set -euo pipefail

printf '%s\n' 'USB devices:'
lsusb

udevadm settle --timeout=5
declare -a candidates=()
if [[ -d /dev/serial/by-id ]]; then
  while IFS= read -r -d '' path; do
    candidates+=("${path}")
  done < <(find /dev/serial/by-id -maxdepth 1 -type l -print0 | sort -z)
fi
for pattern in /dev/ttyUSB* /dev/ttyACM*; do
  for path in ${pattern}; do
    [[ -c "${path}" ]] && candidates+=("${path}")
  done
done

printf '\nCandidate serial devices (%d entries, links included):\n' "${#candidates[@]}"
if ((${#candidates[@]} == 0)); then
  printf '%s\n' 'None detected. Run this script before and after connecting the L1.'
fi

declare -A shown=()
for path in "${candidates[@]}"; do
  resolved="$(readlink -e -- "${path}" 2>/dev/null || true)"
  [[ -n "${resolved}" && -c "${resolved}" ]] || continue
  printf '\nlink=%s\nresolved=%s\n' "${path}" "${resolved}"
  stat -Lc 'mode=%A owner_uid=%u group_gid=%g device=%n' "${resolved}"
  if [[ -z "${shown[${resolved}]:-}" ]]; then
    shown["${resolved}"]=1
    udevadm info --query=property --name="${resolved}" | \
      sed -n -E '/^(ID_VENDOR=|ID_VENDOR_ID=|ID_MODEL=|ID_MODEL_ID=|ID_SERIAL=|ID_SERIAL_SHORT=|ID_PATH=|ID_USB_DRIVER=)/p'
    if command -v fuser >/dev/null && fuser "${resolved}" >/dev/null 2>&1; then
      printf '%s\n' 'WARNING: this device is currently opened by:'
      fuser -v "${resolved}" || true
    else
      printf '%s\n' 'open_by_process=none_detected'
    fi
  fi
done

printf '%s\n' 'No permissions, services, udev rules or network settings were changed.'
