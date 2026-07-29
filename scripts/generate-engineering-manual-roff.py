#!/usr/bin/env python3
"""Render the constrained engineering-manual Markdown source as groff."""

from __future__ import annotations

import re
import sys
from pathlib import Path


PREAMBLE = r""".\" Generated from engineering_manual_unitree_l1_docker_rviz_octomap.md.
.po 1.55c
.ll 17.9c
.pl 29.7c
.lt 17.9c
.ps 9.5
.vs 12.5p
.ft H
.hy 0
.ad l
.kern 0
.defcolor Navy rgb #16425B
.defcolor Teal rgb #247A86
.defcolor Slate rgb #52616B
.de FOOTER
.ev footer
.in 0
.ti 0
.ll 17.9c
.lt 17.9c
.ft H
.ps 7
\m[Slate]Unitree L1 engineering manual\m[black]
.tl '''\m[Slate]\\n%\m[black]'
.ev
'bp
..
.wh -1.15c FOOTER
.de PART
.bp
.in 0
.ti 0
.sp 1.0c
.ne 7v
.ft HB
.ps 20
.vs 24p
\m[Navy]\\$*\m[black]
.ps 9.5
.vs 12.5p
.ft H
.sp 0.75v
\m[Teal]\l'17.9c'\m[black]
.sp 0.65v
..
.de H2
.in 0
.ti 0
.sp 0.8v
.ne 5v
.ft HB
.ps 14
.vs 17p
\m[Navy]\\$*\m[black]
.ps 9.5
.vs 12.5p
.ft H
.sp 0.32v
..
.de H3
.in 0
.ti 0
.sp 0.62v
.ne 4v
.ft HB
.ps 11.5
.vs 14p
\m[Teal]\\$*\m[black]
.ps 9.5
.vs 12.5p
.ft H
.sp 0.24v
..
.de H4
.in 0
.ti 0
.sp 0.45v
.ne 3v
.ft HB
.ps 9.8
\m[Navy]\\$*\m[black]
.ps 9.5
.ft H
.sp 0.18v
..
.de META
.sp 0.12v
.ft HB
\m[Slate]\\$*\m[black]
.ft H
..
.de BU
.sp 0.10v
.in +0.55c
.ti -0.40c
\(bu\h'0.12c'\\$*
.in -0.55c
..
.de NUM
.sp 0.10v
.in +0.70c
.ti -0.62c
\m[Teal]\\$1.\m[black]\h'0.13c'\\$2
.in -0.70c
..
.de CODEBEGIN
.sp 0.24v
.ne 3v
.in +0.42c
.nf
.ft C
.ps 8
.vs 10.1p
\m[Slate]
..
.de CODEEND
\m[black]
.br
.ps 9.5
.vs 12.5p
.ft H
.fi
.in -0.42c
.sp 0.24v
..
.de RULE
.sp 0.45v
\m[Teal]\l'17.9c'\m[black]
.sp 0.25v
..
.sp 1.8c
.ce 4
.ft HB
.ps 24
.vs 28p
\m[Navy]Engineering manual\m[black]
Unitree L1
Docker, RViz2 and OctoMap
ROS 2 Humble runtime
.sp 0.85v
.ce 4
.ft H
.ps 12
.vs 16p
Exact environment reconstruction
Manual component-by-component operation
Stationary mapping and mobile-SLAM boundary
Three technical parts
.sp 1.0v
.ce 3
.ps 10
.vs 13p
Project: /home/isr/unitree_l1_project
Target: ros@<container>:/workspace/ros2_ws
Assembled: 23 July 2026
.sp 1.0v
.ce 1
.ft HB
.ps 12
\m[Teal]ENGINEER'S OPERATING PRINCIPLE\m[black]
.ps 10
.ft H
.sp 0.35v
.in +1.0c
One physical LiDAR. One driver. One Docker runtime.
.br
Additional terminals attach to that same runtime with docker exec.
.br
ROS 2, RViz2 and OctoMap execute inside Ubuntu 22.04 Docker.
.in -1.0c
.bp
"""


def roff_escape(text: str, *, code: bool = False) -> str:
    """Escape literal text so it cannot become a roff request."""
    text = text.replace("\\", r"\e")
    text = text.replace("**", "")
    text = text.replace("`", "")
    if code:
        text = text.replace("'", r"\(aq")
    if text.startswith((".", "'")):
        text = r"\&" + text
    return text


def heading_text(text: str) -> str:
    return roff_escape(text.strip())


def convert(lines: list[str]) -> str:
    output = [PREAMBLE]
    in_code = False
    first_title_skipped = False

    for raw_line in lines:
        line = raw_line.rstrip("\n")

        if line.startswith("```"):
            if in_code:
                output.append(".CODEEND\n")
                in_code = False
            else:
                output.append(".CODEBEGIN\n")
                in_code = True
            continue

        if in_code:
            output.append(roff_escape(line, code=True) + "\n")
            continue

        if line.startswith("# "):
            if not first_title_skipped:
                first_title_skipped = True
                continue
            output.append(f".PART {heading_text(line[2:])}\n")
            continue

        if line.startswith("## "):
            output.append(f".H2 {heading_text(line[3:])}\n")
            continue

        if line.startswith("### "):
            output.append(f".H3 {heading_text(line[4:])}\n")
            continue

        if line.startswith("#### "):
            output.append(f".H4 {heading_text(line[5:])}\n")
            continue

        if line.strip() == "---":
            output.append(".RULE\n")
            continue

        numbered = re.match(r"^(\d+)\.\s+(.*)$", line)
        if numbered:
            number = roff_escape(numbered.group(1))
            body = roff_escape(numbered.group(2))
            output.append(f".NUM {number} \"{body}\"\n")
            continue

        if line.startswith("- "):
            output.append(f".BU {roff_escape(line[2:])}\n")
            continue

        if line.startswith("**") and line.endswith("**"):
            output.append(f".META {roff_escape(line)}\n")
            continue

        if not line.strip():
            output.append(".sp 0.16v\n")
            continue

        output.append(roff_escape(line) + "\n")

    if in_code:
        output.append(".CODEEND\n")

    return "".join(output)


def main() -> int:
    if len(sys.argv) != 3:
        print(
            "usage: generate-engineering-manual-roff.py INPUT.md OUTPUT.roff",
            file=sys.stderr,
        )
        return 2

    source = Path(sys.argv[1])
    destination = Path(sys.argv[2])
    lines = source.read_text(encoding="utf-8").splitlines(keepends=True)
    rendered = convert(lines)
    destination.write_text(rendered, encoding="utf-8")
    print(
        "ENGINEERING_MANUAL_ROFF_PASS "
        f"source={source} output={destination} lines={len(rendered.splitlines())}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
