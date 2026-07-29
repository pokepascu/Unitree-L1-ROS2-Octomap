# Project structure and ownership

This repository separates authored source, reproducible third-party checkouts,
generated build output, and runtime data. Only authored source and the files
needed to recreate dependencies belong in Git.

## Tracked source

| Path | Responsibility |
|---|---|
| `config/dependencies.repos` | Immutable URLs and commits for external source |
| `docker/` | ROS 2 Humble image and opt-in GUI/LiDAR Compose overlays |
| `ros2_ws/colcon_defaults.yaml` | Package discovery and canonical output paths |
| `ros2_ws/src/l1_bringup/` | Unitree driver launch, parameters, and RViz |
| `ros2_ws/src/l1_monitor/` | Point-cloud and IMU diagnostics |
| `ros2_ws/src/l1_octomap_bringup/` | OctoMap launch, parameters, and RViz |
| `scripts/` | Host-facing build, validation, recording, and mapping commands |
| `docs/` | Current design, hardware, version, source, and validation guidance |

Package manifests, launch files, RViz profiles, tests, and resource markers are
source. They must not be replaced by installed copies from a previous build.

## Recreated dependencies

`scripts/fetch-dependencies.sh` imports these ignored checkouts:

```text
ros2_ws/src/octomap_mapping/
ros2_ws/src/unilidar_sdk/
```

Their exact commits live in `config/dependencies.repos`. The project does not
modify the Unitree vendor tree. Adaptations belong in one of the three `l1_*`
packages.

## Generated paths

| Path | Producer | Git policy |
|---|---|---|
| `ros2_ws/build/` | `colcon build` and `colcon test` | ignored |
| `ros2_ws/install/` | `colcon build` | ignored |
| `ros2_ws/log/` | all colcon verbs | ignored |
| `bags/` | `scripts/record-bag.sh` | ignored, created on demand |
| `maps/` | `scripts/save-octomap.sh` | ignored, created on demand |
| `logs/` | hardware validation commands | ignored, created on demand |
| `exports/manuals/*.pdf` | reviewed project manuals | three named PDFs tracked |
| Other `exports/` content | optional user exports | ignored |

Python bytecode, test caches, editor state, and local credentials are also
ignored.

## Out-of-source build invariant

The only valid colcon output locations are:

```text
ros2_ws/
├── build/
├── install/
├── log/
└── src/
```

Any directory named `build`, `install`, or `log` beneath `ros2_ws/src` is
invalid. Three independent controls protect this invariant:

1. Compose exports `COLCON_DEFAULTS_FILE`.
2. `colcon_defaults.yaml` uses absolute container paths for discovery and every
   generated output.
3. `scripts/workspace-build.sh` checks for forbidden source-tree output before
   building and asserts that none was created afterward.

The absolute paths are intentional: ROS execution is supported only inside the
project container, where the repository is mounted at `/workspace`.

## Clean build workflow

Run from the repository root:

```bash
./scripts/docker-build.sh
./scripts/workspace-build.sh
```

For direct colcon use:

```bash
./scripts/docker-shell.sh --no-gui --no-lidar
cd /workspace/ros2_ws
colcon list
colcon build
colcon test --packages-select l1_bringup l1_monitor l1_octomap_bringup
colcon test-result --all --verbose
```

The expected package inventory is:

```text
l1_bringup
l1_monitor
l1_octomap_bringup
octomap_mapping
octomap_server
unitree_lidar_ros2
```

## Repository hygiene checks

The following checks should produce no output:

```bash
find ros2_ws/src -type d \
  \( -name build -o -name install -o -name log \) -print

git ls-files | grep -E \
  '(^|/)(build|install|log|__pycache__|\.pytest_cache)(/|$)|\.pyc$'
```

After tests, generated output may exist under `ros2_ws/`, but `git status` must
remain clean.
