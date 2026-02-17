# Fabric Stage

Fabric is the agentic reasoning layer that sits on top of Forge. It consumes existing workspace artifacts and produces decisions or responses (QA answers, protocols, biofoundry plans). It does **not** build KGs, schemas, vector stores, or any evidence artifacts.

## Inputs (from Forge outputs)
- `workspaces/<topic>/kg_schema.json`
- `workspaces/<topic>/kg_edges.jsonl`
- `workspaces/<topic>/graph.sqlite`
- `workspaces/<topic>/vector_store/`
- `workspaces/<topic>/kg_vector_store/`
- `workspaces/<topic>/methodology_kg_schema.json`
- `workspaces/<topic>/methodology_kg_edges.jsonl`
- `workspaces/<topic>/methodology_vector_store/`
- `workspaces/<topic>/methodology_edge_store/`
- `InstrumentGraph/` (instrument KG + inventory)

## What Fabric does
- QA and agentic reasoning over text + KG evidence.
- Protocol generation (methodology- and instrument-aware).
- Biofoundry template selection and module decisions.
- Hypothesis, timeline, and gap summaries that inform planning.

## What Fabric does NOT do
- No KG construction or schema induction.
- No text extraction, caption/table extraction, or structured fact building.
- No vector store rebuilding.

## Verification checklist
- [ ] No KG rebuild triggered
- [ ] No schema regeneration
- [ ] No vector store regeneration
- [ ] Imports resolve correctly through compatibility wrappers
