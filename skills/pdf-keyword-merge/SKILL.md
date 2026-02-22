---
name: pdf-keyword-merge
description: Search PDFs for one or more keywords by extracting text, then merge matched PDFs per keyword into a single file named after that keyword. Use when a task requires scanning a PDF folder, selecting files that contain specific codes like AAA-BBB1, and writing merged outputs to output/pdf/KEYWORD.pdf with optional rendering-based visual checks.
---

# PDF Keyword Merge

Use this skill to automate keyword-based PDF collection and merging.

## Prerequisites
- Install PDF capability if missing: `codex skill install pdf`
- Ensure Python packages are available:
  - `uv pip install pypdf pdfplumber`
  - Fallback: `python3 -m pip install pypdf pdfplumber`
- For rendering checks, install Poppler (`pdftoppm`).

## Workflow
1. Collect input PDFs from the target folder.
2. Choose match mode:
   - `content`: Extract text from each PDF and match by content.
   - `filename`: Match by PDF file name only (no PDF content read).
3. Build a per-keyword match list.
4. Merge matched PDFs in stable order (path sort).
5. Save each merged file as `output/pdf/<keyword>.pdf`.
6. Render and visually review merged output pages when layout fidelity matters.

## Command
Preferred command from repository root:

```bash
./pmerge japan AAA-BBB1 AAA-BBB2 FFF-FFF9
```

If `pmerge` is on `PATH`, run:

```bash
pmerge japan AAA-BBB1 AAA-BBB2 FFF-FFF9
```

Underlying Python command:

```bash
python3 skills/pdf-keyword-merge/scripts/keyword_merge.py \
  --input-dir japan \
  --keywords AAA-BBB1 AAA-BBB2 FFF-FFF9 \
  --output-dir output/pdf \
  --tmp-dir tmp/pdfs
```

Useful flags:
- `--keywords-file <path>`: Read newline-separated keywords.
- `--case-sensitive`: Match with case sensitivity.
- `--dry-run`: Print matches without creating merged PDFs.
- `--no-recursive`: Scan only the top level of input directory.
- `--match-mode content|filename`: Choose content match or filename match.
- For `pmerge`, pass extra flags via env var:
  - `PMERGE_EXTRA_ARGS="--dry-run" pmerge japan AAA-BBB1`
  - `PMERGE_EXTRA_ARGS="--match-mode filename" pmerge japan IC-211`

## Quality Checks
- Keep intermediate artifacts under `tmp/pdfs/`.
- Keep final merged outputs under `output/pdf/`.
- For visual inspection, render pages with Poppler:

```bash
pdftoppm -png output/pdf/<keyword>.pdf tmp/pdfs/<keyword>
```

Then inspect rendered images for missing pages, overlap, clipping, or broken glyphs.

## Notes
- If no PDF matches a keyword, the script skips output for that keyword and reports it.
- Output filename uses the keyword value; reserved path characters are replaced with `_` to avoid filesystem errors.
- `--match-mode filename` uses only file names and does not extract or read PDF text.
