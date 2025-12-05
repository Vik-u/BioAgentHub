#!/usr/bin/env python3
"""Extract raw text + metadata from PETase/Papers PDFs."""

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


def ocr_page(pdf_path: Path, page_number: int, scale: float = 2.0) -> str:
    if not HAS_TESSERACT:
        return ""
    doc = pdfium.PdfDocument(str(pdf_path))
    page = doc.get_page(page_number)
    pil_image = page.render(scale=scale).to_pil()
    page.close()
    doc.close()
    return pytesseract.image_to_string(pil_image)


def save_page_image(pdf_path: Path, page_number: int, out_dir: Path, scale: float = 2.0) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    doc = pdfium.PdfDocument(str(pdf_path))
    page = doc.get_page(page_number)
    pil_image = page.render(scale=scale).to_pil()
    page.close()
    doc.close()
    image_path = out_dir / f"page-{page_number + 1:03d}.png"
    pil_image.save(image_path, format="PNG")
    return image_path


def extract_page_text(reader, pdf_path: Path, page_index: int) -> Tuple[str, str]:
    method = "pypdf"
    try:
        text = reader.pages[page_index].extract_text() or ""
    except Exception as exc:  # noqa: BLE001
        text = f"[PAGE_EXTRACTION_ERROR: {exc}]"
    if text.strip():
        return text, method

    method = "pdfminer"
    try:
        text = pdfminer_extract_text(
            str(pdf_path),
            page_numbers=[page_index],
        ).strip()
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


def extract_pdf(pdf_path: Path, export_images: bool, image_root: Path) -> Tuple[str, int, List[Dict[str, str]]]:
    reader = PdfReader(str(pdf_path))
    pages = []
    methods = []
    for idx in range(len(reader.pages)):
        text, method = extract_page_text(reader, pdf_path, idx)
        pages.append(text)
        methods.append({"page": idx + 1, "method": method})
        if export_images:
            save_page_image(pdf_path, idx, image_root / pdf_path.stem)
    combined = "\n".join(pages).strip()
    return combined, len(reader.pages), methods


def first_non_empty_line(text: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped
    return ""


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--pdf-dir",
        type=Path,
        default=Path("Papers"),
        help="Directory that contains the source PDFs.",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path("KnowledgeGraph"),
        help="Base directory for extracted text + metadata.",
    )
    parser.add_argument(
        "--export-images",
        action="store_true",
        help="Also render each page to PNG under KnowledgeGraph/images/<pdf>/.",
    )
    args = parser.parse_args()

    text_dir = args.out_dir / "text"
    meta_dir = args.out_dir / "metadata"
    image_dir = args.out_dir / "images"
    text_dir.mkdir(parents=True, exist_ok=True)
    meta_dir.mkdir(parents=True, exist_ok=True)

    corpus_index = []
    for pdf_path in sorted(args.pdf_dir.glob("*.pdf")):
        text, page_count, methods = extract_pdf(pdf_path, args.export_images, image_dir)
        txt_file = text_dir / f"{pdf_path.stem}.txt"
        txt_file.write_text(text, encoding="utf-8")
        metadata = {
            "pdf_file": pdf_path.name,
            "txt_file": txt_file.name,
            "page_count": page_count,
            "char_count": len(text),
            "title_candidate": first_non_empty_line(text),
            "extraction_methods": methods,
            "images_exported": args.export_images,
        }
        (meta_dir / f"{pdf_path.stem}.json").write_text(json.dumps(metadata, indent=2))
        corpus_index.append(metadata)

    index_path = args.out_dir / "corpus_index.json"
    index_path.write_text(json.dumps(corpus_index, indent=2))
    print(f"Extracted {len(corpus_index)} PDFs → {index_path}")


if __name__ == "__main__":
    main()
