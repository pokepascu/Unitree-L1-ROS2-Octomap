# Validation matrix

`PASS` records a reproducible successful check. `PASS_HW` records a successful
check that requires the physical L1.

| ID | Area | Reproducible check | Expected result | Status |
|---|---|---|---|---|
| VAL-001 | Compose | `docker compose` config for base, GUI, and LiDAR overlays | all configurations valid | PASS, 2026-07-29 |
| VAL-002 | Dependency lock | `./scripts/fetch-dependencies.sh` | both checkouts at configured commits and clean | PASS, 2026-07-29 |
| VAL-003 | Package discovery | `colcon list` in the project container | exactly six permitted ROS 2 packages | PASS, 2026-07-29 |
| VAL-004 | Output isolation | invoke colcon from `/workspace/ros2_ws/src` | output remains under `/workspace/ros2_ws`; nothing appears under `src` | PASS, 2026-07-29 |
| VAL-005 | Workspace build | `./scripts/workspace-build.sh` | all six packages build | PASS, 2026-07-29 |
| VAL-006 | Project tests | `colcon test --packages-select l1_bringup l1_monitor l1_octomap_bringup` | no failed tests | PASS, 17/17 on 2026-07-29 |
| VAL-007 | Runtime smoke | `./scripts/smoke-test.sh` | ROS, driver, launch, and linkage checks pass | PASS, 2026-07-29 |
| VAL-008 | Monitor | `./scripts/monitor-synthetic-test.sh` | healthy cloud and IMU diagnostics | PASS, isolated DDS on 2026-07-29 |
| VAL-009 | Docker boundary | host guard plus `./scripts/verify-docker-only.sh` | host ROS refused; runtime processes are containerised | PASS, 2026-07-29 |
| VAL-010 | GUI and DRI | `./scripts/gui-smoke-test.sh` | X11 works and OpenGL uses DRI | PASS, 2026-07-29 |
| VAL-011 | Device detection | `./scripts/check-lidar.sh` | one stable serial adapter is identified without permission changes | PASS_HW, 2026-07-16 |
| VAL-012 | Live messages | `./scripts/lidar-validate.sh` | cloud, IMU, frequencies, and diagnostics are non-empty | PASS_HW, 2026-07-16; cloud ~8–10 Hz and IMU ~210–250 Hz |
| VAL-013 | Recording/replay | record a 30 s bag, inspect it, then replay it | cloud and IMU counts are positive; replay exits cleanly | PASS_HW, 2026-07-16 |
| VAL-014 | Stationary OctoMap | live launch plus `./scripts/evaluate-octomap.sh` | binary map and occupied markers are non-empty | PASS_HW, 2026-07-16 |
| VAL-015 | Map lifecycle | save, inspect, and reopen a `.bt` map | valid header, non-zero nodes, and visible occupied map | PASS_HW, 2026-07-16 |
| VAL-016 | Mobile mapping | dynamic TF plus external odometry/SLAM evaluation | bounded trajectory and map metrics | PENDING |

## Static repository checks

The source tree is clean only when all of these conditions hold:

```bash
git diff --check

find ros2_ws/src -type d \
  \( -name build -o -name install -o -name log \) -print

git ls-files | grep -E \
  '(^|/)(build|install|log|__pycache__|\.pytest_cache)(/|$)|\.pyc$'
```

The two discovery commands must print nothing. Generated outputs from a valid
build may exist at `ros2_ws/build`, `ros2_ws/install`, and `ros2_ws/log`; those
paths are ignored and must not change `git status`.
