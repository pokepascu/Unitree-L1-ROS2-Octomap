# PDF manual sources

This directory contains the maintained source for three project manuals:

- `engineering-manual.md` — complete system architecture, operation,
  troubleshooting, validation, and maintenance;
- `first-run-tutorial.md` — a beginner workflow from UniLiDAR detection through
  RViz2 to a saved stationary OctoMap;
- `file-organization-reference.md` — file-by-file ownership, origin, purpose,
  and generated-data boundaries.

Render all three A4 PDFs from the repository root:

```bash
./scripts/build-manuals.sh
```

The generated PDFs are written to `exports/manuals/`. The three named manuals
are tracked publication artifacts so they can be downloaded directly from
GitHub. Other content beneath `exports/` remains ignored. Rebuild and review
all three PDFs whenever their source or renderer changes.

The renderer intentionally supports only the Markdown constructs used by these
manuals. In addition to headings, paragraphs, lists, fenced code, blockquotes,
and simple tables, the hidden `<!-- PDF_PAGE_BREAK -->` directive may be used
sparingly before a section that must start on a fresh PDF page.
`<!-- PDF_KEEP_NEXT -->` keeps a short lead-in with the command or result that
follows it when a full page break would waste space. The renderer relies on the
host's `groff`, Ghostscript, and Poppler command-line tools and validates page
size, page bounds, text markers, fonts, and checksums before publishing an
output file.
