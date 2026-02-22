#!/usr/bin/env python3
"""Find PDFs containing keywords and merge matched files per keyword."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List

try:
    from pypdf import PdfReader, PdfWriter  # type: ignore
except Exception:
    PdfReader = None  # type: ignore
    PdfWriter = None  # type: ignore

try:
    import pdfplumber  # type: ignore
except Exception:
    pdfplumber = None

INVALID_FILENAME_CHARS = re.compile(r"[\\/:*?\"<>|]")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Extract text from PDFs, find keyword matches, and merge matched PDFs into "
            "output/pdf/<keyword>.pdf."
        )
    )
    parser.add_argument("--input-dir", required=True, help="Directory containing source PDFs")
    parser.add_argument(
        "--keywords",
        nargs="*",
        default=[],
        help="Keywords to search for. Can be combined with --keywords-file.",
    )
    parser.add_argument(
        "--keywords-file",
        help="Optional text file with one keyword per line",
    )
    parser.add_argument(
        "--output-dir",
        default="output/pdf",
        help="Directory for merged outputs (default: output/pdf)",
    )
    parser.add_argument(
        "--tmp-dir",
        default="tmp/pdfs",
        help="Directory for intermediate report and text files (default: tmp/pdfs)",
    )
    parser.add_argument(
        "--no-recursive",
        action="store_true",
        help="Only scan top-level input directory",
    )
    parser.add_argument(
        "--case-sensitive",
        action="store_true",
        help="Use case-sensitive keyword matching",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Do not write merged PDFs; only print/report matches",
    )
    parser.add_argument(
        "--match-mode",
        choices=["content", "filename"],
        default="content",
        help=(
            "Keyword matching target: 'content' extracts PDF text, "
            "'filename' matches against PDF file names only."
        ),
    )
    return parser.parse_args()


def load_keywords(args: argparse.Namespace) -> List[str]:
    keywords: List[str] = []
    keywords.extend(args.keywords)

    if args.keywords_file:
        path = Path(args.keywords_file)
        if not path.is_file():
            raise FileNotFoundError(f"Keywords file not found: {path}")
        for line in path.read_text(encoding="utf-8").splitlines():
            value = line.strip()
            if value:
                keywords.append(value)

    deduped: List[str] = []
    seen = set()
    for keyword in keywords:
        if keyword not in seen:
            deduped.append(keyword)
            seen.add(keyword)

    if not deduped:
        raise ValueError("No keywords provided. Use --keywords or --keywords-file.")
    return deduped


def safe_output_name(keyword: str) -> str:
    return INVALID_FILENAME_CHARS.sub("_", keyword)


def extract_text_with_pdfplumber(pdf_path: Path) -> str:
    if pdfplumber is None:
        return ""

    chunks: List[str] = []
    with pdfplumber.open(str(pdf_path)) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            if text:
                chunks.append(text)
    return "\n".join(chunks)


def extract_text_with_pypdf(pdf_path: Path) -> str:
    if PdfReader is None:
        return ""
    chunks: List[str] = []
    reader = PdfReader(str(pdf_path))
    for page in reader.pages:
        text = page.extract_text() or ""
        if text:
            chunks.append(text)
    return "\n".join(chunks)


def extract_text_with_gs(pdf_path: Path, tmp_dir: Path) -> str:
    gs_path = shutil.which("gs")
    if not gs_path:
        return ""

    tmp_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w+",
        suffix=".txt",
        prefix="gs_text_",
        dir=str(tmp_dir),
        delete=False,
        encoding="utf-8",
    ) as tf:
        txt_path = Path(tf.name)

    cmd = [
        gs_path,
        "-q",
        "-dNOPAUSE",
        "-dBATCH",
        "-sDEVICE=txtwrite",
        f"-sOutputFile={txt_path}",
        str(pdf_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        try:
            txt_path.unlink(missing_ok=True)
        except Exception:
            pass
        return ""

    try:
        return txt_path.read_text(encoding="utf-8", errors="ignore")
    finally:
        txt_path.unlink(missing_ok=True)


def extract_text(pdf_path: Path, tmp_dir: Path) -> str:
    text = extract_text_with_pdfplumber(pdf_path)
    if text.strip():
        return text

    text = extract_text_with_pypdf(pdf_path)
    if text.strip():
        return text

    return extract_text_with_gs(pdf_path, tmp_dir)


def list_pdfs(input_dir: Path, recursive: bool) -> List[Path]:
    if recursive:
        files = input_dir.rglob("*.pdf")
    else:
        files = input_dir.glob("*.pdf")
    return sorted(path for path in files if path.is_file())


def matches_keyword(text: str, keyword: str, case_sensitive: bool) -> bool:
    if case_sensitive:
        return keyword in text
    return keyword.casefold() in text.casefold()


def matches_filename(pdf_path: Path, keyword: str, case_sensitive: bool) -> bool:
    name = pdf_path.name
    if case_sensitive:
        return keyword in name
    return keyword.casefold() in name.casefold()


def merge_pdfs_with_pypdf(pdf_paths: List[Path], output_path: Path) -> bool:
    if PdfWriter is None or PdfReader is None:
        return False

    writer = PdfWriter()
    for pdf_path in pdf_paths:
        reader = PdfReader(str(pdf_path))
        for page in reader.pages:
            writer.add_page(page)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("wb") as f:
        writer.write(f)
    return True


def merge_pdfs_with_gs(pdf_paths: List[Path], output_path: Path) -> None:
    gs_path = shutil.which("gs")
    if not gs_path:
        raise RuntimeError(
            "No PDF merge backend available. Install pypdf or ensure ghostscript (gs) is installed."
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        gs_path,
        "-q",
        "-dNOPAUSE",
        "-dBATCH",
        "-sDEVICE=pdfwrite",
        f"-sOutputFile={output_path}",
    ] + [str(path) for path in pdf_paths]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Ghostscript merge failed: {result.stderr.strip()}")


def merge_pdfs(pdf_paths: List[Path], output_path: Path) -> None:
    if merge_pdfs_with_pypdf(pdf_paths, output_path):
        return
    merge_pdfs_with_gs(pdf_paths, output_path)


def main() -> int:
    args = parse_args()

    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    tmp_dir = Path(args.tmp_dir)

    if not input_dir.is_dir():
        raise NotADirectoryError(f"Input directory not found: {input_dir}")

    keywords = load_keywords(args)
    pdf_paths = list_pdfs(input_dir, recursive=not args.no_recursive)
    if not pdf_paths:
        raise FileNotFoundError(f"No PDF files found under: {input_dir}")

    extracted_text: Dict[Path, str] = {}
    if args.match_mode == "content":
        for pdf_path in pdf_paths:
            try:
                extracted_text[pdf_path] = extract_text(pdf_path, tmp_dir)
            except Exception as exc:
                print(f"[WARN] Failed to read {pdf_path}: {exc}")
                extracted_text[pdf_path] = ""

    report = {
        "input_dir": str(input_dir),
        "total_pdfs": len(pdf_paths),
        "match_mode": args.match_mode,
        "keywords": {},
    }

    for keyword in keywords:
        if args.match_mode == "filename":
            matched = [
                pdf_path
                for pdf_path in pdf_paths
                if matches_filename(pdf_path, keyword, args.case_sensitive)
            ]
        else:
            matched = [
                pdf_path
                for pdf_path in pdf_paths
                if matches_keyword(extracted_text.get(pdf_path, ""), keyword, args.case_sensitive)
            ]

        report["keywords"][keyword] = {
            "match_count": len(matched),
            "matched_files": [str(path) for path in matched],
        }

        if not matched:
            print(f"[INFO] No matches for keyword: {keyword}")
            continue

        output_name = safe_output_name(keyword) + ".pdf"
        output_path = output_dir / output_name

        if args.dry_run:
            print(f"[DRY-RUN] {keyword}: {len(matched)} files -> {output_path}")
            continue

        merge_pdfs(matched, output_path)
        print(f"[OK] {keyword}: merged {len(matched)} files -> {output_path}")

    tmp_dir.mkdir(parents=True, exist_ok=True)
    report_path = tmp_dir / "keyword_merge_report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[OK] Wrote report: {report_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
