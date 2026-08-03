# Manual sources

This directory contains the editable sources for exactly three manuals:

- `engineering-manual.md` — sensor and OctoMap interfaces, architecture,
  parameters, safety, validation limits, and troubleshooting;
- `user-manual.md` — the direct build, raw or OctoMap launch, RViz2,
  recording, inspection, playback, and shutdown procedure;
- `structure-and-organisation.md` — every project file, generated-data
  boundary, and process that can run.

The published A4 PDFs are:

```text
exports/manuals/UNITREE_L1_ENGINEERING_MANUAL.pdf
exports/manuals/UNITREE_L1_USER_MANUAL.pdf
exports/manuals/UNITREE_L1_STRUCTURE_AND_ORGANISATION.pdf
```

Rebuild all three from the repository root:

```bash
./scripts/build-manuals.sh
```

`build-manuals.sh` and `render-manual.py` are documentation-only tools. They
are never copied into the Docker image and never run during LiDAR, RViz2, or
rosbag operation.

The renderer supports the constrained Markdown used by these files, including
headings, paragraphs, lists, tables, fenced code, block quotes, and explicit
PDF page-break comments. The build verifies A4 dimensions, page bounds,
embedded fonts, extractable text, and required content markers before
replacing a published PDF.
