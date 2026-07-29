#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export HOST_UID="$(id -u)"
export HOST_GID="$(id -g)"

docker compose -f "${project_root}/docker/compose.yaml" run --rm dev \
  bash -lc 'set -euo pipefail
    unitree_target=/workspace/ros2_ws/src/unilidar_sdk
    unitree_expected=1bd7d95d8ab7ce7a22058d2bb07e39fd62612aa6
    octomap_target=/workspace/ros2_ws/src/octomap_mapping
    octomap_expected=f79da9a9a1fcdf82e72dab4df288d6cc27c6e163

    import_required=false
    for target in "${unitree_target}" "${octomap_target}"; do
      if [[ -d "${target}/.git" ]]; then
        continue
      elif [[ -e "${target}" ]]; then
        printf "Target exists but is not a Git checkout: %s\n" "${target}" >&2
        exit 1
      else
        import_required=true
      fi
    done

    if [[ "${import_required}" == true ]]; then
      vcs import --skip-existing /workspace/ros2_ws/src \
        < /workspace/config/dependencies.repos
    fi

    verify_checkout() {
      local label="$1"
      local target="$2"
      local expected="$3"
      local actual
      [[ -d "${target}/.git" ]] || {
        printf "%s checkout is missing: %s\n" "${label}" "${target}" >&2
        return 1
      }
      actual="$(git -C "${target}" rev-parse HEAD)"
      if [[ "${actual}" != "${expected}" ]]; then
        printf "Unexpected %s commit: %s (expected %s)\n" \
          "${label}" "${actual}" "${expected}" >&2
        return 1
      fi
      if [[ -n "$(git -C "${target}" status --porcelain)" ]]; then
        printf "%s checkout contains local changes: %s\n" \
          "${label}" "${target}" >&2
        git -C "${target}" status --short >&2
        return 1
      fi
      printf "%s dependency ready at %s\n" "${label}" "${actual}"
    }

    verify_checkout Unitree "${unitree_target}" "${unitree_expected}"
    verify_checkout OctoMap "${octomap_target}" "${octomap_expected}"'
