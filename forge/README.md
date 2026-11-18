# Forge Stage

Forge is the dedicated IE + KG construction stage. It builds topic workspaces from existing PDFs and produces normalized facts, KG edges, graph stores, vector stores, and structured audit reports. It does not crawl or fetch data; it assumes PDFs already exist per topic.

## Inputs
- PDFs under `data/<topic>/` (e.g., `data/petase/`, `data/3hp_pand/`, `data/retron/`).
- Optional config for schema induction in `config/llm_config.json` (PydanticAI default backend).

## Outputs
Per-topic workspace outputs under `workspaces/<topic>/`:
- `text/`, `metadata/`, `corpus_index.json`
- `kg_schema.json` (LLM-inducted schema)
- `kg_edges.jsonl`, `graph_overview.json`
- `graph.sqlite`
- `vector_store/` (text embeddings)
- `kg_vector_store/` (edge embeddings)
- `facts/facts.jsonl`, `facts/facts_summary.json`
- `artifacts/captions.jsonl`, `artifacts/tables.jsonl`, `artifacts/summary.json`

Reports:
- `reports/structured_audit/<topic>_report.json` and `.md` (plus combined report).

Workspace policy:
- Latest KG lives only in `workspaces/<topic>/`.
- Legacy workspaces are archived under `archive/legacy_20260204/` and ignored by discovery.
- `archives/` under each workspace are old versions and are not read by default.

## Deterministic vs LLM components
- **LLM-based:** Schema induction (`forge/agents/kg_schema_agent.py`, PydanticAI default backend). Output is strictly validated by Pydantic models.
- **Deterministic/heuristic:** PDF text extraction, caption/table extraction, fact extraction, normalization, KG edge extraction, graph store creation, vectorization, and audit reporting.

## Libraries used
- PDF/text: `pypdf`, `pdfminer.six`, `pypdfium2`, `pytesseract` (OCR optional)
- Tables/captions: `pdfplumber`
- Embeddings: `sentence-transformers`, `numpy`, `faiss` (optional)
- Schema induction: `pydantic-ai`, `pydantic`
- Storage: `sqlite3`

## Forge flow
```mermaid
flowchart TD
  A[PDFs in data/<topic>] --> B[Text Extraction
pypdf -> pdfminer -> OCR]
  B --> C[Workspace Text + Metadata]
  C --> D[Text Vector Store]
  C --> E[Schema Induction (PydanticAI)]
  E --> F[KG Edge Extraction]
  F --> G[Graph Store (SQLite)]
  F --> H[KG Vector Store]
  A --> I[Caption + Table Extraction]
  I --> J[Structured Facts + Normalization]
  J --> K[Structured Audit Reports]
  F --> K
```

## Run forge end-to-end
Use the canonical entrypoint:

```bash
python forge/run_forge.py --topics petase 3hp_pand retron
```

Optional flags (passed through to existing sub-steps):
- `--limit-pdfs` / `--max-pdfs`, `--max-pages`, `--no-ocr`, `--report-dir`
- `--model`, `--kg-model`, `--focus-query`

Archiving is enabled by default. Existing outputs are moved into `workspaces/<topic>/archives/<timestamp>/` before rebuilds. Use `--delete-old` to skip archiving (dangerous).
