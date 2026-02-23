#!/usr/bin/env python3
"""Find PDFs by keywords and merge all matched files into one PDF."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Sequence, Set

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
            "Find PDFs by keywords and merge all unique matches into one output file. "
            "Default size limit is 2MB."
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
        "--output-name",
        default="merged_keywords.pdf",
        help="Output filename for merged PDF (default: merged_keywords.pdf)",
    )
    parser.add_argument(
        "--tmp-dir",
        default="tmp/pdfs",
        help="Directory for intermediate report/text/temp files (default: tmp/pdfs)",
    )
    parser.add_argument(
        "--size-limit-mb",
        type=float,
        default=2.0,
        help="Maximum output size in MB (default: 2.0)",
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
        help="Do not write merged PDF; only print/report matches",
    )
    parser.add_argument(
        "--match-mode",
        choices=["content", "filename"],
        default="filename",
        help=(
            "Keyword matching target: 'filename' matches against PDF file names only (default), "
            "'content' extracts PDF text."
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


def safe_output_name(name: str) -> str:
    cleaned = INVALID_FILENAME_CHARS.sub("_", name)
    return cleaned if cleaned.lower().endswith(".pdf") else f"{cleaned}.pdf"


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
        txt_path.unlink(missing_ok=True)
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
    files = input_dir.rglob("*.pdf") if recursive else input_dir.glob("*.pdf")
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


def merge_pdfs_with_pypdf(pdf_paths: Sequence[Path], output_path: Path) -> bool:
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


def run_gs_merge(pdf_paths: Sequence[Path], output_path: Path, extra_args: Sequence[str]) -> None:
    gs_path = shutil.which("gs")
    if not gs_path:
        raise RuntimeError("Ghostscript (gs) is required for PDF compression/merge fallback.")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        gs_path,
        "-q",
        "-dNOPAUSE",
        "-dBATCH",
        "-sDEVICE=pdfwrite",
        *extra_args,
        f"-sOutputFile={output_path}",
        *[str(path) for path in pdf_paths],
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Ghostscript failed: {result.stderr.strip()}")


def merge_pdfs(pdf_paths: Sequence[Path], output_path: Path) -> None:
    if merge_pdfs_with_pypdf(pdf_paths, output_path):
        return
    run_gs_merge(pdf_paths, output_path, extra_args=[])


def enforce_size_limit(output_path: Path, limit_bytes: int, tmp_dir: Path) -> tuple[bool, int]:
    original_size = output_path.stat().st_size
    if original_size <= limit_bytes:
        return True, original_size

    gs_path = shutil.which("gs")
    if not gs_path:
        return False, original_size

    tmp_dir.mkdir(parents=True, exist_ok=True)
    attempts = [
        ("screen", 110),
        ("screen", 96),
        ("screen", 72),
        ("ebook", 110),
        ("ebook", 96),
        ("ebook", 72),
    ]

    smallest_path = output_path
    smallest_size = original_size
    chosen_path: Path | None = None
    candidates: List[Path] = []

    for preset, dpi in attempts:
        candidate = tmp_dir / f"compressed_{preset}_{dpi}_{output_path.name}"
        candidates.append(candidate)
        extra_args = [
            "-dCompatibilityLevel=1.4",
            f"-dPDFSETTINGS=/{preset}",
            "-dDetectDuplicateImages=true",
            "-dCompressFonts=true",
            "-dSubsetFonts=true",
            "-dDownsampleColorImages=true",
            "-dDownsampleGrayImages=true",
            "-dDownsampleMonoImages=true",
            f"-dColorImageResolution={dpi}",
            f"-dGrayImageResolution={dpi}",
            f"-dMonoImageResolution={dpi}",
        ]
        run_gs_merge([output_path], candidate, extra_args=extra_args)
        size = candidate.stat().st_size

        if size < smallest_size:
            smallest_size = size
            smallest_path = candidate
        if size <= limit_bytes:
            chosen_path = candidate
            break

    if chosen_path is None:
        if smallest_path != output_path:
            shutil.move(str(smallest_path), str(output_path))
        for candidate in candidates:
            if candidate != smallest_path:
                candidate.unlink(missing_ok=True)
        final_size = output_path.stat().st_size
        return final_size <= limit_bytes, final_size

    shutil.move(str(chosen_path), str(output_path))
    for candidate in candidates:
        if candidate != chosen_path:
            candidate.unlink(missing_ok=True)
    final_size = output_path.stat().st_size
    return final_size <= limit_bytes, final_size


def indexed_output_path(base_output_path: Path, index: int) -> Path:
    return base_output_path.with_name(
        f"{base_output_path.stem}_{index:02d}{base_output_path.suffix}"
    )


def group_fits_size_limit(
    group: Sequence[Path], limit_bytes: int, tmp_dir: Path, label: str
) -> tuple[bool, int]:
    tmp_dir.mkdir(parents=True, exist_ok=True)
    probe = tmp_dir / f"fit_probe_{label}.pdf"
    merge_pdfs(group, probe)
    ok, size = enforce_size_limit(probe, limit_bytes, tmp_dir)
    probe.unlink(missing_ok=True)
    return ok, size


def partition_groups_by_size(
    group: Sequence[Path], limit_bytes: int, tmp_dir: Path, label: str
) -> List[List[Path]]:
    if not group:
        return []

    ok, _ = group_fits_size_limit(group, limit_bytes, tmp_dir, label)
    if ok:
        return [list(group)]
    if len(group) == 1:
        return [list(group)]

    mid = len(group) // 2
    left = partition_groups_by_size(group[:mid], limit_bytes, tmp_dir, f"{label}_L")
    right = partition_groups_by_size(group[mid:], limit_bytes, tmp_dir, f"{label}_R")
    return left + right


def main() -> int:
    args = parse_args()

    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    tmp_dir = Path(args.tmp_dir)
    output_name = safe_output_name(args.output_name)
    output_path = output_dir / output_name
    size_limit_bytes = int(args.size_limit_mb * 1024 * 1024)

    if not input_dir.is_dir():
        raise NotADirectoryError(f"Input directory not found: {input_dir}")
    if size_limit_bytes <= 0:
        raise ValueError("--size-limit-mb must be greater than 0")

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

    matched_by_keyword: Dict[str, List[Path]] = {}
    all_matches: Set[Path] = set()

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
        matched_by_keyword[keyword] = matched
        all_matches.update(matched)
        if not matched:
            print(f"[INFO] No matches for keyword: {keyword}")
        else:
            print(f"[INFO] {keyword}: {len(matched)} matches")

    # Keep deterministic order by following sorted input list.
    unique_merged_targets = [path for path in pdf_paths if path in all_matches]

    report = {
        "input_dir": str(input_dir),
        "total_pdfs": len(pdf_paths),
        "match_mode": args.match_mode,
        "keywords": {
            keyword: {
                "match_count": len(paths),
                "matched_files": [str(path) for path in paths],
            }
            for keyword, paths in matched_by_keyword.items()
        },
        "merged_output": str(output_path),
        "merged_target_count": len(unique_merged_targets),
        "size_limit_bytes": size_limit_bytes,
    }

    report["outputs"] = []

    if not unique_merged_targets:
        print("[INFO] No matched PDFs across all keywords. Skip merge.")
    elif args.dry_run:
        print(
            f"[DRY-RUN] Merge {len(unique_merged_targets)} unique files -> {output_path} "
            f"(limit: {size_limit_bytes} bytes)"
        )
    else:
        merge_pdfs(unique_merged_targets, output_path)
        within_limit, final_size = enforce_size_limit(output_path, size_limit_bytes, tmp_dir)

        if within_limit:
            report["outputs"].append(
                {
                    "path": str(output_path),
                    "size_bytes": final_size,
                    "source_pdf_count": len(unique_merged_targets),
                    "within_limit": True,
                }
            )
            print(
                f"[OK] Merged {len(unique_merged_targets)} unique files -> {output_path} "
                f"({final_size} bytes)"
            )
        else:
            output_path.unlink(missing_ok=True)
            groups = partition_groups_by_size(
                unique_merged_targets, size_limit_bytes, tmp_dir, "root"
            )
            print(
                f"[INFO] Size limit exceeded. Split into {len(groups)} files with index suffix."
            )

            for index, group in enumerate(groups, start=1):
                indexed_path = indexed_output_path(output_path, index)
                merge_pdfs(group, indexed_path)
                group_ok, group_size = enforce_size_limit(indexed_path, size_limit_bytes, tmp_dir)
                report["outputs"].append(
                    {
                        "path": str(indexed_path),
                        "size_bytes": group_size,
                        "source_pdf_count": len(group),
                        "within_limit": group_ok,
                    }
                )
                status = "OK" if group_ok else "WARN"
                print(
                    f"[{status}] Split file {index}: {indexed_path} "
                    f"({group_size} bytes, sources={len(group)})"
                )

    tmp_dir.mkdir(parents=True, exist_ok=True)
    report_path = tmp_dir / "keyword_merge_report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[OK] Wrote report: {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
