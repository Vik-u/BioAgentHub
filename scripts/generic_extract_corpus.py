#!/usr/bin/env python3
"""Extract text/metadata from an arbitrary PDF folder into a reusable workspace."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Dict, List, Tuple

import pypdfium2 as pdfium
from pdfminer.high_level import extract_text as pdfminer_extract_text
from pypdf import PdfReader

try:
    import pytesseract
except ImportError:  # pragma: no cover - optional
    pytesseract = None

HAS_TESSERACT = pytesseract is not None and shutil.which("tesseract") is not None


def ocr_page(pdf_path: Path, page_number: int, scale: float = 1.5) -> str:
    if not HAS_TESSERACT:
        return ""
    doc = pdfium.PdfDocument(str(pdf_path))
    page = doc.get_page(page_number)
    pil_image = page.render(scale=scale).to_pil()
    page.close()
    doc.close()
    return pytesseract.image_to_string(pil_image)


def extract_page_text(reader: PdfReader, pdf_path: Path, page_index: int) -> Tuple[str, str]:
    method = "pypdf"
    try:
        text = reader.pages[page_index].extract_text() or ""
    except Exception as exc:  # pragma: no cover
        text = f"[PAGE_EXTRACTION_ERROR: {exc}]"
    if text.strip():
        return text, method
    method = "pdfminer"
    try:
        text = pdfminer_extract_text(str(pdf_path), page_numbers=[page_index]).strip()
    except Exception:
        text = ""
    if text.strip():
        return text, method
    if HAS_TESSERACT:
        method = "ocr"
        try:
            text = ocr_page(pdf_path, page_index).strip()
        except Exception:
            text = ""
        if text.strip():
            return text, method
    return "[UNREADABLE_PAGE]", "unreadable"


def first_non_empty_line(text: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped
    return ""


def iter_pdfs(root: Path) -> List[Path]:
    return sorted(path for path in root.rglob("*.pdf") if path.is_file())


def extract_pdf(pdf_path: Path, export_images: bool, image_root: Path) -> Tuple[str, int, List[Dict[str, str]]]:
    reader = PdfReader(str(pdf_path))
    pages = []
    methods = []
    for idx in range(len(reader.pages)):
        text, method = extract_page_text(reader, pdf_path, idx)
        pages.append(text)
        methods.append({"page": idx + 1, "method": method})
        if export_images:
            image_dir = image_root / pdf_path.stem
            image_dir.mkdir(parents=True, exist_ok=True)
            doc = pdfium.PdfDocument(str(pdf_path))
            page = doc.get_page(idx)
            page.render(scale=1.5).to_pil().save(image_dir / f"page-{idx + 1:03d}.png")
            page.close()
            doc.close()
    combined = "\n".join(pages).strip()
    return combined, len(reader.pages), methods


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf-dir", type=Path, required=True, help="Folder containing source PDFs.")
    parser.add_argument("--workspace", type=Path, required=True, help="Workspace root (created if missing).")
    parser.add_argument("--export-images", action="store_true", help="Render page PNGs for visual QA.")
    args = parser.parse_args()

    workspace = args.workspace.resolve()
    text_dir = workspace / "text"
    meta_dir = workspace / "metadata"
    image_dir = workspace / "images"
    text_dir.mkdir(parents=True, exist_ok=True)
    meta_dir.mkdir(parents=True, exist_ok=True)
    if args.export_images:
        image_dir.mkdir(parents=True, exist_ok=True)

    corpus_index = []
    for pdf_path in iter_pdfs(args.pdf_dir):
        text, page_count, methods = extract_pdf(pdf_path, args.export_images, image_dir)
        safe_name = pdf_path.stem.replace("/", "_")
        txt_file = text_dir / f"{safe_name}.txt"
        # Some OCR/backends can emit surrogate characters; drop them to keep UTF-8 clean.
        safe_text = text.encode("utf-8", "ignore").decode("utf-8")
        txt_file.write_text(safe_text, encoding="utf-8")
        metadata = {
            "pdf_file": str(pdf_path.resolve()),
            "txt_file": txt_file.name,
            "page_count": page_count,
            "char_count": len(safe_text),
            "title_candidate": first_non_empty_line(safe_text),
            "extraction_methods": methods,
            "images_exported": args.export_images,
        }
        (meta_dir / f"{safe_name}.json").write_text(json.dumps(metadata, indent=2))
        corpus_index.append(metadata)

    index_path = workspace / "corpus_index.json"
    index_path.write_text(json.dumps(corpus_index, indent=2))
    print(f"Extracted {len(corpus_index)} PDFs → {index_path}")


if __name__ == "__main__":
    main()
