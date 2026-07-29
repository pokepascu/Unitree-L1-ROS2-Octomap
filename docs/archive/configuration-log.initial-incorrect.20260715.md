# Unitree L1 Configuration Log

Date: 2026-07-15
Project root: `/home/isr/unitree_l1_project`
Scope of this turn: read-only host inspection only, with project-local documentation.

## Technical choice

- Planned baseline: prefer `Ubuntu 22.04 + ROS 2 Humble` inside Docker if the host is `Ubuntu 24.04`, because that matches the stated compatibility target for the Unitree L1 workflow and selected Point-LIO stack.
- Logging method: record each significant command in this file to preserve a reproducible setup trail and support the final PDF report.

## Command log

### 1. Confirm working directory

- Command: `pwd`
- Purpose: verify that inspection starts from the expected project root before creating project documentation.
- Relevant result: current directory is `/home/isr/unitree_l1_project`.
- Errors encountered: none.
- Diagnosis: workspace path is correct.
- Solution applied: none needed.
- Reason for technical choice: `pwd` is the minimal read-only check for execution context.

### 2. Check for existing docs or top-level guidance files

- Command: `rg --files -g 'AGENTS.md' -g 'docs/**' -g 'README*'`
- Purpose: detect existing documentation structure before creating `docs/configuration-log.md`.
- Relevant result: no matching files were found.
- Errors encountered: command exited with status `1`, which is expected when `rg` finds no matches.
- Diagnosis: there was no pre-existing `docs/` tree or matching README file in the workspace.
- Solution applied: create a new project-local log file under `docs/`.
- Reason for technical choice: `rg --files` is fast, reproducible, and avoids broader filesystem traversal.

### 3. Identify host operating system

- Command: `cat /etc/os-release`
- Purpose: determine the exact Linux distribution and release.
- Relevant result: host reports `PRETTY_NAME="Ubuntu Core 24"`.
- Errors encountered: none.
- Diagnosis: the machine is not reporting a standard Ubuntu 24.04 classic environment; it is reporting `Ubuntu Core 24`, which is a materially different operating model.
- Solution applied: continue inspection with extra attention to Docker, ROS availability, and host tooling constraints.
- Reason for technical choice: `/etc/os-release` is the canonical low-risk source for distro identification.

### 4. Check CPU architecture

- Command: `uname -m`
- Purpose: verify machine architecture for ROS images, vendor binaries, and build compatibility.
- Relevant result: architecture is `x86_64`.
- Errors encountered: none.
- Diagnosis: the machine matches the common `amd64/x86_64` target used by most ROS 2 Humble Docker images and upstream toolchains.
- Solution applied: none needed.
- Reason for technical choice: `uname -m` is the minimal reproducible architecture check.

### 5. Check RAM capacity

- Command: `free -h`
- Purpose: estimate whether the system has enough memory for containerized ROS, visualization, bagging, and LIO workloads.
- Relevant result: `15 GiB` total RAM, `12 GiB` available, `4.0 GiB` swap.
- Errors encountered: none.
- Diagnosis: memory capacity appears adequate for the planned Docker-based workflow.
- Solution applied: none needed.
- Reason for technical choice: `free -h` is a standard read-only summary of RAM and swap availability.

### 6. Check free disk space

- Command: `df -h / /home/isr/unitree_l1_project`
- Purpose: confirm storage headroom for Docker images, ROS workspaces, bags, and PCD map outputs.
- Relevant result: `/` shows `7.8G` free; `/home` shows `850G` free.
- Errors encountered: `df` warned that it could not read the mount table due to permission restrictions in the current execution environment.
- Diagnosis: despite the warning, the output still indicates large free space on `/home`, which is the more relevant location for project artifacts and likely for Docker storage if configured there.
- Solution applied: continue using the reported figures while noting that mount table visibility is partially restricted in this environment.
- Reason for technical choice: `df -h` gives the most direct read-only capacity check for likely storage paths.

### 7. Check graphical session environment

- Command: `printenv XDG_SESSION_TYPE XDG_CURRENT_DESKTOP DISPLAY WAYLAND_DISPLAY`
- Purpose: determine whether a graphical session exists and whether it uses X11 or Wayland.
- Relevant result: `XDG_SESSION_TYPE=x11`, `XDG_CURRENT_DESKTOP=ubuntu:GNOME`, `DISPLAY=:1`; `WAYLAND_DISPLAY` was unset.
- Errors encountered: command exited with status `1` because one requested variable was not set.
- Diagnosis: the machine appears to be running a GNOME `X11` session, which is favorable for future RViz and GUI forwarding from Docker.
- Solution applied: none needed.
- Reason for technical choice: querying environment variables is a low-risk way to infer session type without changing session state.

### 8. Check Docker CLI presence

- Command: `docker --version`
- Purpose: verify whether Docker tooling is installed and available on the command line.
- Relevant result: command not found.
- Errors encountered: `/bin/bash: line 1: docker: command not found`
- Diagnosis: Docker is not currently available on the shell `PATH`.
- Solution applied: none in this turn; installation or host-specific enablement would require approval in a later step.
- Reason for technical choice: Docker CLI presence is the quickest readiness indicator for the planned container workflow.

### 9. Check Docker daemon reachability

- Command: `docker info --format 'Server={{.ServerVersion}} Driver={{.Driver}} Cgroup={{.CgroupDriver}} Root={{.DockerRootDir}}'`
- Purpose: verify whether the Docker daemon is installed and reachable by the current user.
- Relevant result: command could not run because `docker` is not installed or not on `PATH`.
- Errors encountered: `/bin/bash: line 1: docker: command not found`
- Diagnosis: daemon status cannot be evaluated until Docker itself is present.
- Solution applied: defer until Docker is installed or confirmed through host package metadata.
- Reason for technical choice: `docker info` is the most direct read-only usability check once the CLI exists.

### 10. Check Docker snap metadata

- Command: `snap list docker`
- Purpose: determine whether Docker may already be installed via snap on this `Ubuntu Core 24` host.
- Relevant result: unable to obtain a result in the sandboxed execution environment.
- Errors encountered: `/bin/bash: line 1: /usr/bin/snap: Permission denied`
- Diagnosis: this looks like a sandbox restriction rather than proof that `snap` is absent on the host.
- Solution applied: prepare to retry this read-only command with explicit elevated approval.
- Reason for technical choice: on Ubuntu Core, snap metadata is a relevant source of truth for installed system software.

### 11. Check USB enumeration tool presence

- Command: `lsusb`
- Purpose: verify whether standard USB enumeration tooling is available.
- Relevant result: command not found.
- Errors encountered: `/bin/bash: line 1: lsusb: command not found`
- Diagnosis: `usbutils` or an equivalent USB user-space listing tool is not currently available in this shell.
- Solution applied: use kernel sysfs inspection as the fallback USB visibility check.
- Reason for technical choice: `lsusb` is the standard first-pass USB inventory command and is harmless when present.

### 12. Check USB devices through sysfs

- Command: `ls -1 /sys/bus/usb/devices`
- Purpose: inspect the kernel USB subsystem directly.
- Relevant result: unable to obtain a result in the sandboxed execution environment.
- Errors encountered: `ls: cannot open directory '/sys/bus/usb/devices': Permission denied`
- Diagnosis: this looks like sandbox-limited visibility, not a confirmed host USB failure.
- Solution applied: prepare to retry this read-only command with explicit elevated approval.
- Reason for technical choice: sysfs is a reliable fallback when user-space USB tools are unavailable.

### 13. Check serial device nodes

- Command: `find /dev -maxdepth 1 \( -name 'ttyUSB*' -o -name 'ttyACM*' -o -name 'ttyAMA*' -o -name 'ttyS*' \) -printf '%f\n' | sort`
- Purpose: list currently visible common serial device nodes.
- Relevant result: multiple `ttyS*` nodes were present; no `ttyUSB*` or `ttyACM*` nodes were observed.
- Errors encountered: `find` reported `Permission denied` on `/dev/mqueue`, but it still returned the requested serial-node listing.
- Diagnosis: the machine currently exposes onboard-style serial devices only; this is consistent with the LiDAR remaining disconnected.
- Solution applied: none needed.
- Reason for technical choice: a filtered `/dev` scan is reproducible and avoids touching device permissions.

### 14. Check persistent serial symlinks

- Command: `ls -l /dev/serial/by-id`
- Purpose: determine whether stable serial-device names already exist.
- Relevant result: the directory does not exist.
- Errors encountered: `ls: cannot access '/dev/serial/by-id': No such file or directory`
- Diagnosis: there are currently no udev-created persistent serial symlinks visible, which is expected with no USB serial device attached.
- Solution applied: none needed.
- Reason for technical choice: `/dev/serial/by-id` is often the safest reference point for repeatable hardware binding.

### 15. Check Git installation

- Command: `git --version`
- Purpose: verify source-control tooling needed for reproducible repository management.
- Relevant result: `git version 2.43.0`
- Errors encountered: none.
- Diagnosis: Git is installed and usable.
- Solution applied: none needed.
- Reason for technical choice: Git is required to pin, inspect, and later clone software dependencies reproducibly.

### 16. Check workspace repository status

- Command: `git status --short --branch`
- Purpose: determine whether the current workspace is already a Git repository.
- Relevant result: command failed because the current directory is not inside a Git repository.
- Errors encountered: `fatal: not a git repository (or any parent up to mount point /)`
- Diagnosis: `/home/isr/unitree_l1_project` is currently just a working directory, not a Git checkout.
- Solution applied: none in this turn.
- Reason for technical choice: repository status helps track future changes cleanly if the workspace is version-controlled.

### 17. Check C compiler

- Command: `gcc --version`
- Purpose: verify the presence of a GNU C compiler.
- Relevant result: command not found.
- Errors encountered: `/bin/bash: line 1: gcc: command not found`
- Diagnosis: a standard C compiler is not currently available on the shell `PATH`.
- Solution applied: none in this turn.
- Reason for technical choice: ROS and Point-LIO builds require a working native toolchain.

### 18. Check C++ compiler

- Command: `g++ --version`
- Purpose: verify the presence of a GNU C++ compiler.
- Relevant result: command not found.
- Errors encountered: `/bin/bash: line 1: g++: command not found`
- Diagnosis: a standard C++ compiler is not currently available on the shell `PATH`.
- Solution applied: none in this turn.
- Reason for technical choice: the driver and LIO stack are C++-centric and cannot be built without it.

### 19. Check CMake

- Command: `cmake --version`
- Purpose: verify the presence of the CMake build system.
- Relevant result: command not found.
- Errors encountered: `/bin/bash: line 1: cmake: command not found`
- Diagnosis: CMake is not currently available on the shell `PATH`.
- Solution applied: none in this turn.
- Reason for technical choice: most ROS packages and third-party libraries in this workflow use CMake.

### 20. Check make

- Command: `make --version`
- Purpose: verify the presence of a conventional native build tool.
- Relevant result: command not found.
- Errors encountered: `/bin/bash: line 1: make: command not found`
- Diagnosis: `make` is not currently available on the shell `PATH`.
- Solution applied: none in this turn.
- Reason for technical choice: even if `ninja` is later used, basic build tooling helps establish host readiness.

### 21. Check Python 3

- Command: `python3 --version`
- Purpose: verify the Python runtime needed by ROS 2 tooling.
- Relevant result: `Python 3.12.3`
- Errors encountered: none.
- Diagnosis: Python 3 is available.
- Solution applied: none needed.
- Reason for technical choice: Python is central to ROS tooling, launch systems, and auxiliary scripts.

### 22. Check pip

- Command: `pip3 --version`
- Purpose: verify the availability of Python package management tooling.
- Relevant result: command not found.
- Errors encountered: `/bin/bash: line 1: pip3: command not found`
- Diagnosis: `pip3` is not currently available on the shell `PATH`.
- Solution applied: none in this turn.
- Reason for technical choice: `pip3` is often needed for Python-side ROS and analysis tooling.

### 23. Check colcon

- Command: `colcon --version`
- Purpose: verify the presence of the ROS 2 workspace build tool.
- Relevant result: command not found.
- Errors encountered: `/bin/bash: line 1: colcon: command not found`
- Diagnosis: `colcon` is not currently installed or not on `PATH`.
- Solution applied: none in this turn.
- Reason for technical choice: `colcon` is the standard build orchestrator for ROS 2 workspaces.

### 24. Check conventional ROS installation path

- Command: `ls -1 /opt/ros`
- Purpose: detect native ROS distributions installed under the standard system prefix.
- Relevant result: the path does not exist.
- Errors encountered: `ls: cannot access '/opt/ros': No such file or directory`
- Diagnosis: no conventional system-wide ROS installation is visible.
- Solution applied: none in this turn.
- Reason for technical choice: `/opt/ros` is the default location for system ROS installations on Ubuntu-family hosts.

### 25. Check ROS 2 CLI on PATH

- Command: `which ros2`
- Purpose: confirm whether the ROS 2 command-line tool is available in the current shell.
- Relevant result: no path was returned.
- Errors encountered: command exited with status `1`.
- Diagnosis: `ros2` is not on `PATH`.
- Solution applied: none in this turn.
- Reason for technical choice: `which ros2` is the minimal shell-level presence check.

### 26. Check active ROS environment variables

- Command: `env | rg '^ROS_'`
- Purpose: determine whether the current shell already has ROS environment variables exported.
- Relevant result: no ROS variables were returned.
- Errors encountered: command exited with status `1` because there were no matches.
- Diagnosis: the shell is not currently inside any sourced ROS environment.
- Solution applied: none in this turn.
- Reason for technical choice: environment variables reveal whether ROS has already been sourced in the session.

## First-turn assessment

- Readiness verdict: the machine is **not currently ready** for the planned `Ubuntu 22.04 + ROS 2 Humble in Docker` workflow.
- Positive findings:
  - Host architecture is `x86_64`.
  - Available RAM and `/home` free space appear sufficient for ROS, bags, and mapping.
  - A GNOME `X11` session is present, which should help later with RViz GUI forwarding.
  - `git` and `python3` are available.
- Blocking findings:
  - The host reports `Ubuntu Core 24`, not a standard Ubuntu 24.04 classic installation.
  - `docker` is not currently on `PATH`, so the planned container workflow cannot start yet.
  - No standard native build toolchain is visible: `gcc`, `g++`, `cmake`, and `make` are all missing from `PATH`.
  - No ROS installation is visible: `/opt/ros` does not exist, `ros2` is not on `PATH`, and no `ROS_*` environment variables are set.
  - `colcon` and `pip3` are also absent from `PATH`.
- Unresolved due to execution-environment limits:
  - `snap list docker` could not be executed because `snap` access was denied in the current environment.
  - `/sys/bus/usb/devices` could not be listed because sysfs access was denied in the current environment.
- Current interpretation:
  - The machine has enough hardware capacity for the target workflow, but it lacks the required software baseline and may require a host-specific Docker approach because it reports `Ubuntu Core 24`.
