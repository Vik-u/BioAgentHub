#!/usr/bin/env python3
"""Extract figure/table captions and table contents with provenance."""

from __future__ import annotations

import argparse
import json
import re
import shutil
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

try:
    import pypdfium2 as pdfium  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    pdfium = None
from pypdf import PdfReader

try:
    import pdfplumber  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    pdfplumber = None

try:
    import pytesseract  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    pytesseract = None

CAPTION_START_RE = re.compile(r"^(Figure|Fig\.|FIGURE|FIG\.|Table|TABLE)\s*\d+[A-Za-z0-9-]*[.:]?\s*(.*)")
NUMERIC_LINE_RE = re.compile(r"(\d+(\.\d+)?)")

HAS_TESSERACT = pytesseract is not None and shutil.which("tesseract") is not None and pdfium is not None


def iter_pdfs(root: Path) -> List[Path]:
    return sorted(path for path in root.rglob("*.pdf") if path.is_file())


def load_pdf_list(workspace: Path, pdf_dir: Optional[Path]) -> List[Path]:
    if pdf_dir:
        return iter_pdfs(pdf_dir)
    corpus_index = workspace / "corpus_index.json"
    if not corpus_index.exists():
        return []
    payload = json.loads(corpus_index.read_text())
    pdfs = []
    for entry in payload:
        pdf_path = entry.get("pdf_file")
        if pdf_path:
            candidate = Path(pdf_path)
            if candidate.exists():
                pdfs.append(candidate)
    return pdfs


def ocr_page(pdf_path: Path, page_number: int, scale: float = 1.5) -> str:
    if not HAS_TESSERACT:
        return ""
    doc = pdfium.PdfDocument(str(pdf_path))
    page = doc.get_page(page_number)
    pil_image = page.render(scale=scale).to_pil()
    page.close()
    doc.close()
    return pytesseract.image_to_string(pil_image)


def extract_page_text(reader: PdfReader, pdf_path: Path, page_index: int, allow_ocr: bool) -> str:
    try:
        text = reader.pages[page_index].extract_text() or ""
    except Exception:
        text = ""
    if text.strip():
        return text
    if allow_ocr:
        return ocr_page(pdf_path, page_index).strip()
    return ""


def detect_captions(lines: List[str]) -> List[Tuple[str, str, int]]:
    captions: List[Tuple[str, str, int]] = []
    idx = 0
    while idx < len(lines):
        line = lines[idx].strip()
        match = CAPTION_START_RE.match(line)
        if match:
            label = match.group(1)
            caption_type = "table" if label.lower().startswith("table") else "figure"
            collected = [line]
            idx += 1
            while idx < len(lines):
                next_line = lines[idx].strip()
                if not next_line:
                    break
                if CAPTION_START_RE.match(next_line):
                    break
                collected.append(next_line)
                if len(collected) >= 4:
                    break
                idx += 1
            captions.append((caption_type, " ".join(collected).strip(), idx))
        idx += 1
    return captions


def find_caption_bbox(words: List[dict], caption_text: str) -> Optional[List[float]]:
    if not words:
        return None
    tokens = [re.sub(r"[^\w.-]", "", tok).lower() for tok in caption_text.split()]
    tokens = [tok for tok in tokens if tok]
    if len(tokens) < 2:
        return None
    word_tokens = [re.sub(r"[^\w.-]", "", word["text"]).lower() for word in words]
    for i in range(len(word_tokens)):
        if word_tokens[i] != tokens[0]:
            continue
        matched = []
        for j, tok in enumerate(tokens[:8]):
            if i + j >= len(word_tokens):
                break
            if word_tokens[i + j] == tok:
                matched.append(words[i + j])
        if len(matched) >= 2:
            x0 = min(w["x0"] for w in matched)
            top = min(w["top"] for w in matched)
            x1 = max(w["x1"] for w in matched)
            bottom = max(w["bottom"] for w in matched)
            return [round(x0, 2), round(top, 2), round(x1, 2), round(bottom, 2)]
    return None


def extract_text_tables(text: str) -> List[str]:
    lines = [line for line in text.splitlines() if line.strip()]
    blocks = []
    current = []
    for line in lines:
        tokens = re.split(r"\s{2,}", line.strip())
        numeric_hits = len(NUMERIC_LINE_RE.findall(line))
        if len(tokens) >= 2 and numeric_hits >= 2:
            current.append(line)
        else:
            if len(current) >= 2:
                blocks.append("\n".join(current))
            current = []
    if len(current) >= 2:
        blocks.append("\n".join(current))
    return blocks


def extract_tables_from_page(plumber_page) -> List[dict]:
    tables = []
    try:
        found = plumber_page.find_tables()
    except Exception:
        found = []
    for table in found:
        rows = table.extract() if table else None
        text = ""
        if rows:
            text = "\n".join(["\t".join([cell or "" for cell in row]) for row in rows])
        tables.append(
            {
                "rows": rows,
                "text": text,
                "bbox": [round(coord, 2) for coord in table.bbox] if table else None,
                "extraction_method": "pdfplumber",
            }
        )
    return tables


def write_jsonl(path: Path, rows: Iterable[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def run(
    workspace: Path,
    pdf_dir: Optional[Path],
    out_dir: Path,
    max_pdfs: Optional[int],
    max_pages: Optional[int],
    allow_ocr: bool,
) -> Dict[str, int]:
    pdfs = load_pdf_list(workspace, pdf_dir)
    if max_pdfs:
        pdfs = pdfs[:max_pdfs]
    captions_out = out_dir / "captions.jsonl"
    tables_out = out_dir / "tables.jsonl"

    captions = []
    tables = []
    summary = {
        "pdf_count": len(pdfs),
        "caption_count": 0,
        "table_count": 0,
        "table_structured_count": 0,
        "table_text_count": 0,
    }

    for pdf_path in pdfs:
        reader = PdfReader(str(pdf_path))
        plumber_doc = pdfplumber.open(str(pdf_path)) if pdfplumber else None
        total_pages = len(reader.pages)
        page_limit = min(total_pages, max_pages) if max_pages else total_pages
        for page_index in range(page_limit):
            text = extract_page_text(reader, pdf_path, page_index, allow_ocr=allow_ocr)
            lines = text.splitlines() if text else []
            page_number = page_index + 1
            words = []
            if plumber_doc:
                try:
                    words = plumber_doc.pages[page_index].extract_words()
                except Exception:
                    words = []
            for idx, (caption_type, caption_text, _) in enumerate(detect_captions(lines)):
                caption_id = f"{pdf_path.stem}-p{page_number:03d}-c{idx:02d}"
                bbox = find_caption_bbox(words, caption_text) if words else None
                captions.append(
                    {
                        "caption_id": caption_id,
                        "caption_type": caption_type,
                        "text": caption_text,
                        "pdf_file": str(pdf_path),
                        "page": page_number,
                        "bbox": bbox,
                        "extraction_method": "regex",
                    }
                )
            page_tables = []
            if plumber_doc:
                try:
                    page_tables = extract_tables_from_page(plumber_doc.pages[page_index])
                except Exception:
                    page_tables = []
            if page_tables:
                for table_idx, entry in enumerate(page_tables):
                    table_id = f"{pdf_path.stem}-p{page_number:03d}-t{table_idx:02d}"
                    tables.append(
                        {
                            "table_id": table_id,
                            "pdf_file": str(pdf_path),
                            "page": page_number,
                            "bbox": entry.get("bbox"),
                            "rows": entry.get("rows"),
                            "text": entry.get("text", ""),
                            "extraction_method": entry.get("extraction_method", "pdfplumber"),
                        }
                    )
                    summary["table_count"] += 1
                    if entry.get("rows"):
                        summary["table_structured_count"] += 1
                    else:
                        summary["table_text_count"] += 1
            else:
                for block_idx, block in enumerate(extract_text_tables(text)):
                    table_id = f"{pdf_path.stem}-p{page_number:03d}-tb{block_idx:02d}"
                    tables.append(
                        {
                            "table_id": table_id,
                            "pdf_file": str(pdf_path),
                            "page": page_number,
                            "bbox": None,
                            "rows": None,
                            "text": block,
                            "extraction_method": "heuristic_text_block",
                        }
                    )
                    summary["table_count"] += 1
                    summary["table_text_count"] += 1
        if plumber_doc:
            plumber_doc.close()

    summary["caption_count"] = len(captions)
    write_jsonl(captions_out, captions)
    write_jsonl(tables_out, tables)
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2))
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, required=True, help="Workspace with corpus_index.json.")
    parser.add_argument("--pdf-dir", type=Path, help="Optional PDF directory (defaults to corpus index).")
    parser.add_argument("--out-dir", type=Path, help="Output directory for artifacts.")
    parser.add_argument("--max-pdfs", type=int, help="Process only the first N PDFs.")
    parser.add_argument("--max-pages", type=int, help="Process only the first N pages of each PDF.")
    parser.add_argument("--no-ocr", action="store_true", help="Disable OCR fallback.")
    args = parser.parse_args()

    workspace = args.workspace.resolve()
    out_dir = (args.out_dir or (workspace / "artifacts")).resolve()
    run(
        workspace=workspace,
        pdf_dir=args.pdf_dir.resolve() if args.pdf_dir else None,
        out_dir=out_dir,
        max_pdfs=args.max_pdfs,
        max_pages=args.max_pages,
        allow_ocr=not args.no_ocr,
    )


if __name__ == "__main__":
    main()
