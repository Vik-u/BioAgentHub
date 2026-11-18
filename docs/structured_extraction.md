# Structured Extraction: Captions, Tables, Facts

This pipeline adds figure/table caption and table extraction on top of the existing PDF-to-text workflow, then converts that evidence into normalized facts with typed relations.

## Extraction strategy

- Text-native PDFs:
  - Captions are detected with regex anchors (`Figure`, `Fig.`, `Table`) on each page.
  - Table candidates are detected with pdfplumber when available.
  - If a table extractor fails, we fall back to table-like text blocks (multiple numeric columns).
- Scanned/image pages:
  - OCR is only used when page text is empty and Tesseract is available.
  - OCR output is treated like text for caption and table-like block detection.

## Outputs (per workspace)

- `artifacts/captions.jsonl`: figure/table captions with `pdf`, `page`, and `bbox` when available.
- `artifacts/tables.jsonl`: table rows (structured) or text blocks, plus provenance.
- `facts/facts.jsonl`: normalized facts with:
  - `head` and `tail` (raw + normalized)
  - `relation_type` (fixed set)
  - `normalized_value` + `normalized_unit` when numeric
  - `evidence_text` and provenance (pdf + page + bbox + table/caption ids)

## Fallback behavior

- If pdfplumber is not installed, tables fall back to text-block detection.
- If OCR is unavailable, unreadable pages will be skipped for captions/tables.
- Facts are still produced from plain text even if no captions/tables are extracted.
