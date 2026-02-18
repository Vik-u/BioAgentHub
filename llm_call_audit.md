# LLM Call Audit (BioAgentHub_iBF)

This report lists every LLM call site, how the schema induction step works, and how outputs flow into downstream IE/KG.

## LLM Call Sites

**LLM transport layer**
- `services/local_llm.py`
  - Library: `requests` HTTP calls to OpenAI chat completions or Ollama.
  - Backend selection: `config/llm_config.json` (`backend`, `model`, `api_base`, `api_key_env`, `temperature`).
  - Output: raw text; no validation.

**Schema/ontology induction (LLM)**
- `agents/kg_schema_agent.py`
  - Functions: `generate_schema_existing`, `generate_schema_pydantic_ai`, `generate_schema`.
  - Libraries: `services/local_llm` (existing backend) or `pydantic_ai` (new backend).
  - Prompt:
    - “Design a JSON schema for knowledge graph extraction …”
    - Includes topic + focus query + sampled text.
  - Output parsing/validation:
    - Existing backend: regex JSON block extraction → `normalize_schema`.
    - PydanticAI backend: `SchemaInduction` Pydantic model (validated); failures raise.
  - Storage: `workspaces/<topic>/kg_schema.json` with `schema_version` metadata.
  - Downstream use:
    - `scripts/build_kg_edges.py` uses `kg_schema.json` for keyword lists + relation keywords.
    - `scripts/generic_build_vector_store.py` uses schema aliases for chunk source tagging.
    - `utils/kg_schema_utils.py` uses aliases for entity seeding + query expansion.

**Protocol generation (LLM)**
- `agents/protocol_agent.py`
  - Library: LangChain + LangGraph (`langchain_core`, `langgraph.graph`); LLM = `services/local_llm`.
  - Prompt: `PROMPT` template for experimental + computational workflows.
  - Output: raw Markdown; no structured validation.
- `agents/protocol_agent_v2.py`
  - Library: `services/local_llm` (direct).
  - Prompt: `PROMPT_TEMPLATE` using methodology + instrument evidence.
  - Output: raw Markdown; logged to `logs/protocol_v2_runs`.
- `agents/instrument_protocol_agent.py`
  - Library: LangChain prompt templates; LLM = `services/local_llm`.
  - Prompt: instrument-constrained workflow.
- `agents/instrument_protocol_agent_v2.py`
  - Library: `services/local_llm`.
  - Prompt: instrument evidence + protocol snippets.
- `scripts/generate_protocol_from_summaries.py`
  - Library: `services/local_llm`.
  - Prompt: Fluent-guided workflow based on ranked summary chunks.
- `app/generic_protocol_cli.py`
  - Library: `services/local_llm`.
  - Prompt: evidence summary with inline citations.

**QA + planning (LLM)**
- `agents/rag_agent.py`
  - Function: `summarize_context`.
  - Library: `services/local_llm`.
  - Prompt: cite evidence snippets; outputs summary + sources.
- `agents/hypothesis_planner.py`
  - Functions: `generate_hypotheses`, `computational_plan`, `experimental_plan`, `arbiter`.
  - Library: `services/local_llm`.
  - Output: free text; no structured validation.
- `agents/biofoundry_protocol_orchestrator.py`
  - Function: `llm_expand_keywords`.
  - Library: `services/local_llm`.
  - Output parsing: comma-separated list of search phrases.

## Schema Induction (Before/After)

**Before**
- `agents/kg_schema_agent.py::generate_schema` (local_llm + regex JSON extraction).
- If JSON parsing fails or LLM fails: falls back to default schema.
- Output stored in `workspaces/<topic>/kg_schema.json`.

**After**
- Config switch in `config/llm_config.json`:
  - `schema_induction_backend`: `existing_backend` or `pydantic_ai`
  - `schema_induction_model`: model name for PydanticAI (defaults to main model)
  - `schema_induction_seed`: deterministic sampling seed
- PydanticAI uses a strict `SchemaInduction` model:
  - `entities` (name + aliases)
  - `assays`, `metrics`, `substrates`, `products`, `conditions`
  - `relation_keywords`, `unit_rules`
- Validation errors raise loudly (stderr + exception).
- Output is normalized into existing schema fields and stored with `schema_version` metadata.

## Storage + Downstream Consumption
- Schema stored at: `workspaces/<topic>/kg_schema.json`.
- Used by:
  - `scripts/build_kg_edges.py` → relation keyword matching + edge typing.
  - `scripts/generic_build_vector_store.py` → alias-based source tagging for chunks.
  - `utils/kg_schema_utils.py` → query expansion + KG seed selection.

## Notes
- Caption artifacts are not duplicated in `workspaces/petase/artifacts/captions.jsonl`; file is unique by caption_id.
- `_pand_deprecated` workspace is excluded from auto-discovery to avoid confusion; defaults now use `3hp_pand`.
