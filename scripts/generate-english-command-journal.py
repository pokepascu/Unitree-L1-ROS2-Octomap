#!/usr/bin/env python3
"""Generate the English, command-complete Unitree L1 hardware journal.

The French journal is the historical source of truth for the exact terminal
transcript.  This generator keeps every fenced command/output block verbatim
and adds an English explanation for each chronological entry.
"""

from __future__ import annotations

import re
import textwrap
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE = PROJECT_ROOT / "docs/report/journal_materiel_commandes_20260716.md"
MARKDOWN_OUTPUT = PROJECT_ROOT / "docs/report/journal_materiel_commandes_20260716_en.md"
ROFF_OUTPUT = PROJECT_ROOT / "docs/report/journal_materiel_commandes_20260716_en.roff"


# The keys intentionally cover every entry in the historical journal.  Keeping
# the map explicit makes a missing translation fail loudly instead of silently
# producing an unexplained command block.
ENTRY_TEXT = {
    "CMD-001": ("Inventory the control files", "Lists the scripts and documentation used to operate the project before touching the sensor."),
    "CMD-002": ("Read the durable rules and runbooks", "Reads the project rules, hardware runbook, launch/validation scripts and LiDAR Compose override so the hardware run follows the approved safety boundary."),
    "CMD-003": ("Detect the physical L1 adapter", "Runs the stable USB-serial detector and confirms the CP2104 identity, serial number, resolved tty and current owner."),
    "CMD-004": ("First hardware launch without RViz2", "Starts the named Docker runtime with the L1 driver and monitor but no GUI, isolating data reception from display troubleshooting."),
    "CMD-005": ("Validate real sensor messages", "Checks actual PointCloud2 and IMU messages, rates, point fields and timestamp monotonicity rather than accepting topic names alone."),
    "CMD-006": ("Record a 30-second rosbag2 capture", "Creates a bounded bag containing cloud, IMU and diagnostics so the real stream can be inspected and replayed."),
    "CMD-007": ("Inspect the recorded bag", "Runs the project bag-info wrapper to verify duration, size, topics and positive message counters."),
    "CMD-008": ("Check RViz2 prerequisites and runtime stability", "Verifies the display, X11 cookie readability, DRI devices, container state and recent runtime output without exposing the cookie itself."),
    "ACTION-009": ("Stop the first live runtime", "Sends one Ctrl-C byte to the launch terminal and records the shutdown exception that exposed the monitor defect."),
    "CMD-010": ("Inspect the shutdown defect", "Reads the monitor shutdown code and checks whether a stale runtime container remains."),
    "PATCH-011": ("Fix the ROS 2 double-shutdown", "Adds an rclpy.ok() guard so the monitor does not call rclpy.shutdown() twice after ROS 2 has already handled SIGINT."),
    "CMD-012": ("Rebuild after the shutdown fix", "Recompiles the project overlay and confirms the monitor, driver and bringup packages still build."),
    "CMD-013": ("Find the existing test command", "Searches the project documentation and scripts for the canonical colcon test and test-result commands."),
    "CMD-014": ("Re-read Compose and earlier evidence", "Reopens the container definition and prior configuration log to reproduce the same environment for regression testing."),
    "CMD-015": ("Run targeted package tests", "Runs the monitor, bringup and vendor ROS 2 package tests inside the same Humble container and records the console output."),
    "CMD-016": ("Aggregate the test results", "Uses colcon test-result to report errors, failures and skipped tests across the complete test run."),
    "CMD-017": ("Launch the real L1 with RViz2", "Starts the driver, monitor and RViz2 together so the live cloud can be viewed under graphical load."),
    "CMD-018": ("Validate data while RViz2 subscribes", "Repeats the real-message validator while RViz2 consumes the cloud, checking that visualization does not break the stream."),
    "ACTION-019": ("Stop the corrected RViz2 runtime", "Sends one Ctrl-C and records clean termination of the driver, monitor and RViz2 after PATCH-011."),
    "CMD-020": ("Inspect the replay script", "Reads the replay wrapper and checks that no live runtime or serial device is required for bag playback."),
    "CMD-021": ("Replay the real bag once", "Runs the first bag replay and records the false header-age warning caused by comparing recorded time with wall time."),
    "PATCH-022": ("Make replay use ROS time", "Adds use_sim_time to monitor/RViz2 and --clock to ros2 bag play so recorded timestamps are compared with /clock."),
    "CMD-023": ("Replay after the clock correction", "Repeats playback and confirms healthy diagnostics and valid cloud/IMU rates with simulated ROS time."),
    "CMD-024": ("Inspect the project before documentation", "Reviews the validation matrix, final-report outline, code diff, generated evidence, bag size and container state."),
    "CMD-025": ("Check syntax, hashes and vendor integrity", "Runs Bash syntax checks, optional shellcheck, SHA-256 measurements and clean/expected vendor checkout checks."),
    "ACTION-026": ("Write the first documentation set", "Records which Markdown, roff, validation and configuration-log files were changed through atomic file patches."),
    "CMD-027": ("Generate the first hardware journal PDF", "Makes the PDF builder executable and converts the exact Markdown journal into an A4 PDF."),
    "CMD-028": ("Check the first journal PDF", "Verifies PDF metadata, text markers, known hashes and the generated journal checksum."),
    "CMD-029": ("Render journal pages for visual inspection", "Rasterizes every journal page so margins, pagination, characters and clipping can be inspected visually."),
    "CMD-030": ("Run the final hardware-journal check and stage it", "Rechecks the builder, then stages only the project changes and selected evidence while excluding bags and the pre-existing ZIP."),
    "CMD-031": ("Record the first milestone state", "Captures Git status, the new commit and Docker state after the initial hardware milestone."),
    "CMD-032": ("Inventory material for readable guides", "Collects the existing reports, runbook, launch script, RViz profile and report index before writing beginner-facing PDFs."),
    "CMD-033": ("Reuse the validated A4 layout", "Reads the existing roff macros, synthesis generator and complete hardware source so the new guides retain the tested page geometry."),
    "ACTION-034": ("Draft and independently audit readable guides", "Creates the readable data report, RViz tutorial and their roff/build sources after separate structure and beginner-command reviews."),
    "CMD-035": ("Generate the first readable guides", "Runs syntax checks and builds the first readable report and RViz tutorial."),
    "CMD-036": ("Render all readable-guide pages", "Rasterizes every page of both guides and makes contact sheets when montage is available."),
    "ACTION-037": ("Inspect the first readable-guide render", "Visual review finds tight cover spacing, inherited indentation and inconsistent footer text."),
    "CMD-038": ("Rebuild after layout corrections", "Runs the PDF generator after the cover, indentation and footer fixes."),
    "CMD-039": ("Inspect corrected pages", "Renders selected covers, middle pages and final pages to verify the layout corrections."),
    "ACTION-040": ("Finish the visual layout", "Confirms readable covers and left-aligned body text, then keeps only a centered page number in the footer."),
    "CMD-041": ("Generate PDFs with metadata checks", "Rebuilds both guides and reads their PDF metadata to confirm A4, page counts and a simple PDF profile."),
    "CMD-042": ("Render another targeted set", "Renders selected pages from both guides using a temporary directory for a release check."),
    "CMD-043": ("Check the page-label finishing change", "Rebuilds and renders pages after removing the unreliable roff footer label, keeping the centered number."),
    "CMD-044": ("Validate final guide text markers", "Checks the source syntax, required explanatory sections, validation markers, hashes and stop instructions in extracted text."),
    "CMD-045": ("Inspect the last pages", "Renders the final page of each guide and verifies that no text is cut off and page numbers are complete."),
    "CMD-046": ("Audit the tutorial functionally", "Checks that the scripts named by the RViz tutorial are executable and valid, that the replay bag exists and that the runtime is idle."),
    "ACTION-047": ("Update the index and general log", "Adds the readable documents, their checks, layout corrections and hashes to the report index and configuration log."),
    "CMD-048": ("Regenerate the extended command register", "Rebuilds the hardware journal after the readable-guide work so the chronology includes the new documentation work."),
    "CMD-049": ("Rebuild after removing a fixed command count", "Regenerates the readable guides and records their final hashes after changing the cover to avoid a stale command-count claim."),
    "CMD-050": ("Find superseded documented hashes", "Searches the repository for earlier guide hashes and distinguishes historical evidence from current final hashes."),
    "CMD-051": ("Check the extended journal", "Reads the journal page metadata and extracts markers from the newly extended register before hashing it."),
    "CMD-052": ("Run final checks without regenerating guides", "Checks source syntax, exact page counts and hashes without changing already-final readable PDFs."),
    "CMD-053": ("Stage the first complete documentation milestone", "Adds the selected source, PDFs, logs and code changes to Git while leaving generated bags and the user ZIP outside the index."),
    "CMD-054": ("Record the post-documentation state", "Captures status, the current commit, active containers and the vendor checkout state."),
    "CMD-055": ("Audit the project before OctoMap integration", "Lists current tracked PDFs, source packages, project files and the state of the working tree."),
    "CMD-056": ("Audit Docker, scripts, dependencies and OctoMap", "Reads all relevant Compose/Docker/workspace scripts and inspects the pinned OctoMap checkout and server build files."),
    "CMD-057": ("Reproduce the photo's incorrect package discovery", "Inspects the existing container and runs colcon list to prove that ROS 1 catkin and the raw SDK were being discovered alongside the correct ROS 2 driver."),
    "CMD-058": ("Read both real CMake errors", "Reads the ROS 1 driver and OctoMap build stderr logs and confirms the missing catkin and OCTOMAP configuration layers."),
    "SOURCE-059": ("Verify official colcon discovery configuration", "Checks the official colcon configuration and discovery references used to justify workspace-local base paths."),
    "PATCH-060": ("Fix discovery without editing vendors", "Adds pinned OctoMap dependencies, safe discovery roots, GUI/LiDAR shell options and image packages while leaving both vendor checkouts intact."),
    "CMD-061": ("Inspect and syntax-check the integration patch", "Reads the changed files, checks the working tree and runs Bash syntax checks before building."),
    "CMD-062": ("Test the first colcon-defaults harness", "Runs colcon list and a YAML assertion; the assertion is corrected after a false substring match between unitree_lidar_ros and unitree_lidar_ros2."),
    "ACTION-063": ("Move the first PDF set into the PDF folder", "Creates the canonical PDF directory and moves the historical PDFs with git mv, preserving the user ZIP and removing an exact duplicate."),
    "PATCH-064": ("Add the project-owned l1_octomap_bringup package", "Adds OctoMap parameters, RViz profile, two launch files and tests; remaps cloud_in to the L1 cloud and makes the bench/mobile TF contract explicit."),
    "CMD-065": ("Rebuild the Docker image with OctoMap", "Rebuilds the Humble image with OctoMap dependencies and records the complete build log without stopping the pre-existing interactive container."),
    "CMD-066": ("Reproduce the corrected version of the photo command", "Runs colcon build from the workspace with the corrected discovery defaults and records a six-package successful build."),
    "CMD-067": ("Test the three project packages", "Runs colcon test and colcon test-result for l1_monitor, l1_bringup and l1_octomap_bringup."),
    "CMD-068": ("Test the simple GUI/LiDAR Docker shell", "Feeds exit to docker-shell.sh to verify default GUI, serial detection and the mapped /dev/unitree_lidar without leaving a shell open."),
    "CMD-069": ("Validate X11, OpenGL and serial access together", "Runs xdpyinfo, glxinfo and character-device checks in the combined Compose overrides and records the GUI/LiDAR pass."),
    "CMD-070": ("Launch the real L1 into OctoMap", "Starts the combined driver, monitor, bench TF, OctoMap server and no RViz2 against the physical spinning L1."),
    "ERR-CMD-071": ("Record the first active-container diagnostic error", "Shows that enabling set -u before sourcing ROS makes AMENT_TRACE_SETUP_FILES undefined; the active graph is not changed."),
    "CMD-072": ("Run the corrected graph and rate audit", "Sources ROS first, lists nodes/topics, measures raw cloud and OctoMap marker rates and prints detailed marker QoS."),
    "CMD-073": ("Probe non-empty OctoMap content", "Uses a reliable transient-local ROS 2 MarkerArray subscriber to prove occupied markers and points exist, not merely that a topic name exists."),
    "CMD-074": ("Stop the validation launch and release the port", "Sends SIGINT, inspects the temporary container, checks tty ownership and confirms only the user's pre-existing container remains."),
    "CMD-075": ("Record final OctoMap package and image versions", "Reads Debian package versions, image metadata and the exact OctoMap tag/commit; a shell-dollar quoting error is corrected."),
    "CMD-076": ("Build and check the project-structure guide", "Generates the structure PDF, checks A4/text markers and records the visual inspection pages and checksum."),
    "ACTION-077": ("Document the local Git repository and future remote", "Confirms main has no remote and documents the safe remote-add/push procedure without sending anything externally."),
    "CMD-078": ("Rebuild all readable PDFs in the canonical location", "Runs all readable-PDF builders and records page counts and hashes after the PDF-folder reorganization."),
    "CMD-079": ("Regenerate the extended exact command journal", "Rebuilds the hardware journal after OctoMap integration and PDF reorganization."),
    "ERR-CMD-080": ("Find an orphaned command heading during review", "Visual/text review finds CMD-066 separated from its command block at a page break; no content is lost, but the journal is harder to follow."),
    "CMD-081": ("Fix journal pagination and run regression checks", "Adds roff reservation before Markdown headings, rebuilds, extracts CMD-066/CMD-067 and checks A4 metadata."),
    "CMD-082": ("Verify pinned dependencies and workspace build", "Confirms both external commits, installed rosdeps and a successful six-package workspace build."),
    "ERR-CMD-083": ("Record an invalid Python compileall option", "Shows that this Python version does not accept --dir; the failed check does not modify the project."),
    "CMD-084": ("Run corrected static checks", "Runs compileall, XML parsing and YAML parsing for the project package and dependency/default/configuration files."),
    "CMD-085": ("Prepare the local Git commit", "Stages project code, configuration, PDFs and selected evidence, then checks the staged diff while excluding the user ZIP and vendor checkouts."),
    "CMD-086": ("Create and verify the principal local commit", "Commits the OctoMap integration and trace preservation, then checks HEAD, status, remotes, ZIP hash and vendor commits."),
}


ENTRY_RE = re.compile(r"^### ((?:CMD|ACTION|PATCH|SOURCE|ERR-CMD)-\d+) — ([^\n]+)$", re.MULTILINE)
BLOCK_RE = re.compile(
    r"(?ms)^(?P<fence>```|~~~)(?P<language>[A-Za-z0-9_-]*)\n"
    r"(?P<body>.*?)^(?P=fence)\s*$"
)


def parse_entries(source: str):
    matches = list(ENTRY_RE.finditer(source))
    entries = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(source)
        section = source[match.end() : end]
        blocks = []
        for block in BLOCK_RE.finditer(section):
            language = block.group("language") or "text"
            body = block.group("body").rstrip()
            blocks.append((language, body))
        identifier = match.group(1)
        if identifier not in ENTRY_TEXT:
            raise SystemExit(f"Missing English explanation for {identifier}")
        entries.append((identifier, match.group(2), blocks))
    expected = set(ENTRY_TEXT)
    actual = {identifier for identifier, _, _ in entries}
    if expected != actual:
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        raise SystemExit(f"Entry mapping mismatch; missing={missing}, extra={extra}")
    return entries


def write_markdown(entries) -> None:
    bash_blocks = sum(
        1
        for _, _, blocks in entries
        for language, _ in blocks
        if language in {"bash", "sh", "shell"}
    )
    total_lines = sum(
        len(body.splitlines())
        for _, _, blocks in entries
        for _, body in blocks
    )
    lines = [
        "# Complete English command journal — Unitree L1 and OctoMap",
        "",
        "Date of recorded work: 16 July 2026",
        "Project: `/home/isr/unitree_l1_project`",
        "Scope: physical L1 connection, ROS 2 validation, RViz2, rosbag2,",
        "OctoMap integration, map saving, PDF production and local Git traceability.",
        "",
        "## How to read this edition",
        "",
        "This is the English companion to the historical French command journal.",
        "Every command, terminal input, patch block and recorded output block from",
        "the source journal is retained verbatim and appears below in chronological",
        "order. A block labelled `bash` is a command that was run in a terminal;",
        "`text` blocks are recorded output or terminal input; `diff` and `python`",
        "blocks are source changes or embedded checks. Historical paths are kept",
        "exactly as executed, even when the current PDF folder has since been",
        "reorganized.",
        "The PDF visually wraps very long source lines with an indentation; the",
        "English Markdown companion keeps those lines unbroken for exact copy/paste.",
        "The PDF builder also verifies A4 metadata and removes only a final page",
        "that contains the footer number alone, which groff can emit when its",
        "footer trap fires at end-of-file.",
        "",
        f"Coverage: 86 chronological entries, {bash_blocks} shell blocks, 18 recorded output/patch blocks and {total_lines} exact transcript lines.",
        "The short explanation before each block states what the command did, why",
        "it was safe, and how its result changed the next decision. The raw logs",
        "named in the entries remain the evidence for long-running output.",
        "",
        "## Safety and project boundary",
        "",
        "- ROS 2 Humble ran inside Docker Ubuntu 22.04; ROS 2 was not installed on the host.",
        "- No `privileged` container, `chmod 777`, global `xhost +` or system-service stop was used.",
        "- The L1 serial adapter was passed as one targeted character device.",
        "- The Unitree SDK and OctoMap checkout were kept at their pinned commits and not edited.",
        "- Bags and maps are generated data; the pre-existing user ZIP was left untracked and untouched.",
        "",
        "## Validated outcome",
        "",
        "The real CP2104 L1 published `/unilidar/cloud` at approximately 8–10 Hz",
        "and `/unilidar/imu` at approximately 210–250 Hz. The OctoMap bench run",
        "received the cloud through `l1_octomap_bringup`, produced an occupied",
        "MarkerArray (`OCTOMAP_MARKER_PROBE_PASS markers=17 occupied_markers=2",
        "points=13247`) and saved `maps/l1_real_bench_20260716.bt` with",
        "`OCTOMAP_SAVE_PASS` (18,902 bytes). OctoMap is the mapping layer; a moving",
        "robot still needs an external dynamic `map -> unilidar_lidar` TF for SLAM.",
        "",
        "## Complete chronological command register",
        "",
    ]
    for identifier, _original_title, blocks in entries:
        title, explanation = ENTRY_TEXT[identifier]
        lines.extend([f"### {identifier} — {title}", "", f"**English explanation:** {explanation}", ""])
        if not blocks:
            lines.extend([
                "No fenced terminal block was present in the historical source for this entry.",
                "The entry records a file patch, visual inspection or decision performed at this point.",
                "",
            ])
        for language, body in blocks:
            label = "Exact terminal command or input" if language in {"bash", "sh", "shell"} else "Recorded output, patch or embedded check"
            lines.extend([f"**{label}:**", "", f"~~~{language}", body, "~~~", ""])

    lines.extend([
        "## Appendix A — What was actually proven",
        "",
        "- USB identity and targeted Docker device access were proven before the driver was trusted.",
        "- Real PointCloud2 and IMU messages, rates, fields and timestamps were checked.",
        "- A real rosbag2 was recorded, inspected, replayed and corrected to use ROS time.",
        "- The original catkin discovery error was corrected by restricting colcon roots; the vendor was not patched.",
        "- OctoMap dependencies, launches, TF modes, RViz display and map saving were validated with the spinning L1.",
        "- The local Git commit preserved source, PDFs and selected logs without adding the user's ZIP or generated bags/maps.",
        "",
        "## Appendix B — Current canonical documents",
        "",
        "- `docs/report/pdf/03_octomap_mapping/JOURNAL_MATERIEL_COMMANDES_UNITREE_L1_20260716_EN.pdf` — this English detailed journal.",
        "- `docs/report/pdf/03_octomap_mapping/TUTORIAL_UNITREE_L1_OCTOMAP_MAPPING_EN.pdf` — English run tutorial.",
        "- `docs/report/pdf/03_octomap_mapping/RAPPORT_CONFIGURATION_UNITREE_L1_OCTOMAP_EN.pdf` — English configuration report.",
        "- `docs/configuration-log.md` and `docs/report/pdf/01_environment/CONFIGURATION_LOG_UNITREE_L1.pdf` — chronological project log.",
        "",
        "## Appendix C — Rebuilding this English journal",
        "",
        "~~~bash",
        "cd /home/isr/unitree_l1_project",
        "pwd",
        "git status --short",
        "wc -l docs/report/journal_materiel_commandes_20260716.md docs/configuration-log.md",
        "python3 -m py_compile scripts/generate-english-command-journal.py",
        "python3 scripts/generate-english-command-journal.py",
        "./scripts/build-english-command-journal-pdf.sh",
        "pdfinfo docs/report/pdf/03_octomap_mapping/JOURNAL_MATERIEL_COMMANDES_UNITREE_L1_20260716_EN.pdf",
        "pdftotext docs/report/pdf/03_octomap_mapping/JOURNAL_MATERIEL_COMMANDES_UNITREE_L1_20260716_EN.pdf - | grep -E 'CMD-001|CMD-086|OCTOMAP_SAVE_PASS'",
        "pdftoppm -f 1 -l 1 -png -r 120 docs/report/pdf/03_octomap_mapping/JOURNAL_MATERIEL_COMMANDES_UNITREE_L1_20260716_EN.pdf /tmp/english-journal-check/cover",
        "./scripts/build-english-octomap-guides-pdf.sh",
        "bash -n scripts/build-english-command-journal-pdf.sh scripts/build-english-octomap-guides-pdf.sh",
        "~~~",
        "",
    ])
    MARKDOWN_OUTPUT.write_text("\n".join(lines), encoding="utf-8")


def roff_escape(text: str) -> str:
    text = text.replace("\\", r"\e")
    if text.startswith((".", "'")):
        text = r"\&" + text
    return text


def write_roff(markdown: str) -> None:
    output = [
        r'." Generated from the complete English command journal.',
        ".po 1.35c",
        ".ll 18.3c",
        ".pl 29.7c",
        ".lt 18.3c",
        ".ps 9.0",
        ".vs 12p",
        ".ft H",
        ".hy 0",
        ".ad l",
        ".de FOOTER",
        ".ev footer",
        ".in 0",
        ".ti 0",
        ".ll 18.3c",
        ".lt 18.3c",
        ".ft H",
        ".ps 7.5",
        r".tl ''\\n%''",
        ".ev",
        "..",
        ".wh -1.2c FOOTER",
    ]
    # Avoid relying on a Markdown renderer on the Ubuntu host.  This minimal
    # converter handles precisely the Markdown emitted above.
    in_code = False
    entry_count = 0
    top_heading_seen = False
    code_language = "text"
    for raw_line in markdown.splitlines():
        line = raw_line.rstrip()
        if line.startswith("~~~"):
            if not in_code:
                in_code = True
                code_language = line[3:] or "text"
                output.extend([".sp 0.15v", ".nf", ".ft C", ".ps 7.6"])
            else:
                in_code = False
                output.extend([".ps 9.0", ".ft H", ".fi", ".sp 0.15v"])
            continue
        if in_code:
            code_lines = textwrap.wrap(
                line,
                width=104,
                break_long_words=False,
                break_on_hyphens=False,
            ) or [""]
            for index, code_line in enumerate(code_lines):
                # The PDF uses an indented continuation marker for long source
                # lines.  The Markdown companion retains the exact unbroken
                # command for copy/paste.
                prefix = "    " if index else ""
                output.append(roff_escape(prefix + code_line))
            continue
        if not line:
            output.append(".sp 0.18v")
            continue
        if line.startswith("# "):
            if top_heading_seen:
                output.append(".bp")
            top_heading_seen = True
            title = line[2:]
            if " — " in title:
                title, subtitle = title.split(" — ", 1)
                output.extend([".ce 2", ".ft HB", ".ps 19", roff_escape(title), ".ps 15", roff_escape(subtitle), ".ps 9.0", ".ft H", ".sp 0.7v"])
            else:
                output.extend([".ce 2", ".ft HB", ".ps 19", roff_escape(title), ".ps 9.0", ".ft H", ".sp 0.7v"])
            continue
        if line.startswith("## "):
            output.extend([".ne 5v", ".sp 0.55v", ".ft HB", ".ps 13", roff_escape(line[3:]), ".ps 9.0", ".ft H", ".sp 0.25v"])
            continue
        if line.startswith("### "):
            entry_count += 1
            if entry_count == 1 or (entry_count - 1) % 4 == 0:
                output.append(".bp")
            output.extend([".ne 4v", ".sp 0.42v", ".ft HB", ".ps 10.5", roff_escape(line[4:]), ".ps 9.0", ".ft H", ".sp 0.15v"])
            continue
        if line.startswith("**English explanation:**"):
            output.extend([".sp 0.1v", ".ft HB", "English explanation:", ".ft H"])
            prose = line[len("**English explanation:**") :].strip()
            for wrapped in textwrap.wrap(prose, width=104, break_long_words=False, break_on_hyphens=False) or [""]:
                output.append(roff_escape(wrapped))
            continue
        if line.startswith("**Exact terminal command or input:**"):
            output.extend([".sp 0.1v", ".ft HB", "Exact terminal command or input:", ".ft H"])
            continue
        if line.startswith("**Recorded output, patch or embedded check:**"):
            output.extend([".sp 0.1v", ".ft HB", "Recorded output, patch or embedded check:", ".ft H"])
            continue
        if line.startswith("- "):
            output.extend([".sp 0.1v", ".in +0.45c", ".ti -0.35c", r"\(bu\h'0.10c'" + roff_escape(line[2:]), ".in -0.45c"])
            continue
        # Keep generated prose readable and avoid long horizontal lines.
        for wrapped in textwrap.wrap(line, width=104, break_long_words=False, break_on_hyphens=False) or [""]:
            output.append(roff_escape(wrapped))
    while output and output[-1].startswith(".sp "):
        output.pop()
    ROFF_OUTPUT.write_text("\n".join(output) + "\n", encoding="utf-8")


def main() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    entries = parse_entries(source)
    write_markdown(entries)
    write_roff(MARKDOWN_OUTPUT.read_text(encoding="utf-8"))
    print(f"ENGLISH_JOURNAL_SOURCE_PASS entries={len(entries)} markdown={MARKDOWN_OUTPUT} roff={ROFF_OUTPUT}")


if __name__ == "__main__":
    main()
