#!/usr/bin/env python3
"""Extract raw text from all PDFs under Devices/ into structured JSON for retrieval."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import List

from pdfminer.high_level import extract_text


def find_pdfs(root: Path) -> List[Path]:
    return sorted(p for p in root.rglob("*.pdf") if p.is_file())


def extract_pdf(pdf_path: Path) -> dict:
    # Use pdfminer to preserve layout as much as possible.
    text = extract_text(str(pdf_path)) or ""
    # Also capture per-page text to improve precise retrieval later.
    pages = []
    try:
        from pdfminer.pdfdocument import PDFDocument
        from pdfminer.pdfpage import PDFPage
        from pdfminer.pdfparser import PDFParser
        from pdfminer.layout import LAParams
        from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
        from pdfminer.converter import TextConverter
        import io

        with open(pdf_path, "rb") as fh:
            parser = PDFParser(fh)
            doc = PDFDocument(parser)
            laparams = LAParams()
            rsrcmgr = PDFResourceManager()
            for page in PDFPage.create_pages(doc):
                output = io.StringIO()
                device = TextConverter(rsrcmgr, output, laparams=laparams)
                interpreter = PDFPageInterpreter(rsrcmgr, device)
                interpreter.process_page(page)
                pages.append(output.getvalue())
                device.close()
                output.close()
    except Exception:
        pages = []
    return {
        "pdf_file": str(pdf_path),
        "page_count": len(pages) if pages else None,
        "text": text,
        "pages": pages,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--devices-dir",
        type=Path,
        default=Path("Devices"),
        help="Root folder containing Work Units/Workflows PDFs.",
    )
    parser.add_argument(
        "--subdir",
        type=Path,
        default=None,
        help="Optional subfolder under devices-dir (e.g., Workflows or 'Work Units').",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path("Devices") / "text_json",
        help="Where to store extracted JSON files.",
    )
    args = parser.parse_args()

    root = args.devices_dir / args.subdir if args.subdir else args.devices_dir
    args.out_dir.mkdir(parents=True, exist_ok=True)
    pdfs = find_pdfs(root)
    index = []
    for pdf in pdfs:
        record = extract_pdf(pdf)
        out_path = args.out_dir / (pdf.stem.replace("/", "_") + ".json")
        out_path.write_text(json.dumps(record, ensure_ascii=False, indent=2))
        index.append({"pdf_file": record["pdf_file"], "json_file": str(out_path), "page_count": record["page_count"]})
    (args.out_dir / "index.json").write_text(json.dumps(index, indent=2))
    print(f"Extracted {len(pdfs)} PDFs → {args.out_dir}")


if __name__ == "__main__":
    main()
