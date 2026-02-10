# Used Surface (Canonical vs Legacy)

## Canonical entrypoints (defined scope)
- `forge/run_forge.py`
- `fabric/agents/rl_rag_agent.py`
- `app/gradio_chatbot.py`
- `app/qa_chat_langgraph.py`
- `app/hub_api.py`
- `app/hub_cli.py`
- `app/protocol_agent_cli_v2.py`
- `app/instrument_protocol_cli_v2.py`
- `fabric/agents/biofoundry_protocol_orchestrator.py`
- `agents/biofoundry_protocol_agent.py`
- `fabric/agents/multi_agent_orchestrator.py`

## Canonical policy (current)
- Evidence sources are canonical under `workspaces/<topic>/` (Forge outputs).
- `KnowledgeGraph/` is legacy-only (not used by default).
- Instrument evidence is **opt-in** via `BIOAGENT_USE_INSTRUMENTS=1` (default off).

## USED SURFACE (kept)
Evidence: static imports from canonical entrypoints and runtime path usage.

- **Forge (IE/KG construction)**
  - `forge/` (all; includes `forge/run_forge.py`, `forge/scripts/*`, `forge/utils/*`)
- **Fabric (agents/services)**
  - `fabric/` (all)
- **Workspace resolution + schema helpers**
  - `utils/workspace_utils.py`
  - `utils/kg_schema_utils.py`
  - `utils/enzyme_aliases.py` (used by `fabric/services/retrieval_service.py`)
  - `utils/output_paths.py` (shared output root)
- **Service wrappers used by Fabric**
  - `services/__init__.py`
  - `services/local_llm.py`
  - `services/retrieval_service.py`
  - `services/methodology_retrieval.py`
  - `services/instrument_retrieval.py`
  - `services/generic_retrieval.py`
- **Agent wrappers used by canonical CLIs/orchestrator**
  - `agents/__init__.py`
  - `agents/rl_rag_agent.py`
  - `agents/protocol_agent_v2.py`
  - `agents/timeline_gap_agent.py`
  - `agents/hypothesis_planner.py`
  - `agents/multi_agent_orchestrator.py`
  - Additional wrappers kept for sanity-check imports: `agents/run_agent_plain.py`, `agents/run_agent_llm.py`, `agents/protocol_agent.py`, `agents/instrument_protocol_agent.py`, `agents/instrument_protocol_agent_v2.py`, `agents/biofoundry_protocol_orchestrator.py`, `agents/biofoundry_protocol_agent.py`, `agents/timeline_summarizer.py`.
- **CLIs/UI (canonical)**
- `app/gradio_chatbot.py`
- `app/qa_chat_langgraph.py`
  - `app/hub_api.py`
  - `app/hub_cli.py`
  - `app/protocol_agent_cli_v2.py`
  - `app/instrument_protocol_cli_v2.py`
- **Inputs/Artifacts/Config**
  - `workspaces/` (canonical artifacts)
  - `data/` (Forge input PDFs)
  - `config/` (LLM config)
  - `ModuleTemplate/` (Biofoundry templates)
  - `logs/`, `reports/`, `biofoundry_output/` (runtime outputs)

## LEGACY CANDIDATES (not referenced by canonical surface)
Evidence: no static import or entrypoint reference from canonical surface.

- **App/UI**: none (only canonical entrypoints are present in `app/`).

## AMBIGUOUS / OPTIONAL (kept)
- `InstrumentGraph/` (optional evidence branch; only used when `BIOAGENT_USE_INSTRUMENTS=1`).
- `KnowledgeGraph/` (legacy data kept; not used by canonical flows).
- `docs/` (documentation, including canonical policies and audit notes).
