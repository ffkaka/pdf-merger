---
name: pdf-keyword-merge
description: Search PDFs for one or more keywords, collect all matched PDFs across keywords, and merge them into one output file with a 2MB size cap. Use when a task requires scanning a PDF folder for codes like AAA-BBB1 and creating a single merged result in output/pdf.
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
3. Build a per-keyword match list, then union all matches into one unique merge target list.
4. Merge matched PDFs in stable order (path sort).
5. Save one merged output file (default: `output/pdf/merged_keywords.pdf`).
6. Enforce output size limit (default: 2MB).
7. If size exceeds 2MB, split into indexed files (`_01`, `_02`, ...) and save them.
8. Render and visually review merged output pages when layout fidelity matters.

## Command
Preferred command from repository root:

```bash
./pmerge japan AAA-BBB1 AAA-BBB2 FFF-FFF9
```

Keyword-file based (recommended for many keywords):

```bash
PMERGE_KEYWORDS_FILE=/home/<USER>/pdf-merger/keywords.txt ./pmerge japan
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
  --output-name merged_keywords.pdf \
  --output-dir output/pdf \
  --tmp-dir tmp/pdfs
```

Useful flags:
- `--keywords-file <path>`: Read newline-separated keywords.
- `--case-sensitive`: Match with case sensitivity.
- `--dry-run`: Print matches without creating merged PDFs.
- `--no-recursive`: Scan only the top level of input directory.
- `--match-mode content|filename`: Choose content match or filename match.
- `--output-name <name>.pdf`: Set output filename for the single merged file.
- `--size-limit-mb <float>`: Maximum output size in MB (default: 2.0).
- For `pmerge`, pass extra flags via env var:
  - `PMERGE_EXTRA_ARGS="--dry-run" pmerge japan AAA-BBB1`
  - `PMERGE_EXTRA_ARGS="--match-mode filename" pmerge japan IC-211`
  - `PMERGE_OUTPUT_NAME="my_merged.pdf" pmerge japan AAA-BBB1 AAA-BBB2`
  - `PMERGE_KEYWORDS_FILE="/home/<USER>/pdf-merger/keywords.txt" pmerge japan`

## Quality Checks
- Keep intermediate artifacts under `tmp/pdfs/`.
- Keep final merged outputs under `output/pdf/`.
- For visual inspection, render pages with Poppler:

```bash
pdftoppm -png output/pdf/merged_keywords.pdf tmp/pdfs/merged_keywords
```

Then inspect rendered images for missing pages, overlap, clipping, or broken glyphs.

## Notes
- If no PDF matches across all keywords, the script skips merge output and writes only the report.
- Output filename is sanitized to avoid filesystem-invalid characters.
- `--match-mode filename` uses only file names and does not extract or read PDF text.
- The script enforces size cap (2MB default).
- If full merge exceeds size cap, it automatically writes indexed split outputs (for example `merged_keywords_01.pdf`, `merged_keywords_02.pdf`).
