# Script Audit

This audit lists script-style entrypoints (files with `__main__` or intended CLI usage), their purpose, and whether they are core/optional. "Optional" typically means it’s only needed for a specific workflow (UI, demos, legacy compatibility) or requires external data/credentials.

## App / CLI / UI
- `app/hub_cli.py`
  Purpose: Unified CLI for QA, protocol, biofoundry orchestration, and multi-agent runs.
  Usefulness: Core. Primary CLI used in README and integration.
  Requirements: Workspace data (`workspaces/*`), optional LLM credentials depending on mode.

- `app/gradio_chatbot.py`
  Purpose: Gradio UI for QA/protocol/biofoundry.
  Usefulness: Optional. Only needed if running the UI.
  Requirements: Same as CLI; additionally needs Gradio runtime.

- `app/qa_chat_langgraph.py`
  Purpose: Interactive QA chat using LangGraph.
  Usefulness: Optional. Only if you want LangGraph chat loop.
  Requirements: Workspaces + LangGraph deps.

- `app/protocol_agent_cli_v2.py`
  Purpose: CLI for protocol generation (methodology-driven).
  Usefulness: Optional but important for protocol workflows.
  Requirements: Workspaces + module templates.

- `app/instrument_protocol_cli_v2.py`
  Purpose: CLI for instrument-aware protocol generation.
  Usefulness: Optional (biofoundry workflows only).
  Requirements: InstrumentGraph data + templates.

- `app/hub_api.py`
  Purpose: FastAPI server exposing QA endpoint.
  Usefulness: Optional. Only needed for API service use.
  Requirements: Same as CLI; requires FastAPI/uvicorn.

## Forge Pipeline (Data -> Workspace/KG)
- `forge/run_forge.py`
  Purpose: End-to-end IE + KG build across topics.
  Usefulness: Core for building workspaces from PDFs.
  Requirements: `data/<topic>/` PDFs; optional LLM keys for schema induction.

- `forge/scripts/build_topic_full.py`
  Purpose: Build a single topic workspace (text, vectors, KG, graph).
  Usefulness: Core for per-topic rebuilds.
  Requirements: PDFs + write access to `workspaces/`.

- `forge/scripts/build_topic_workspaces.py`
  Purpose: Build multiple topic workspaces in batch.
  Usefulness: Core for full dataset refresh.
  Requirements: PDFs + `workspaces/`.

- `forge/scripts/extract_corpus.py`
  Purpose: Extract text/metadata from PETase PDFs.
  Usefulness: Core if you use the PETase topic.
  Requirements: PETase PDFs.

- `forge/scripts/generic_extract_corpus.py`
  Purpose: Extract text/metadata from arbitrary PDF folder.
  Usefulness: Core for non-PETase topics.
  Requirements: PDFs.

- `forge/scripts/extract_pdf_artifacts.py`
  Purpose: Extract figure/table captions and tables.
  Usefulness: Core for richer KG grounding.
  Requirements: PDFs + pypdfium2.

- `forge/scripts/build_structured_facts.py`
  Purpose: Build structured facts from text/tables/captions.
  Usefulness: Core for structured evidence.
  Requirements: Extracted corpus + optional LLM for schema induction.

- `forge/scripts/run_structured_audit.py`
  Purpose: Generate structured audit reports.
  Usefulness: Optional but recommended for QA on extraction quality.
  Requirements: Structured facts outputs.

- `forge/scripts/build_kg_edges.py`
  Purpose: Heuristic KG edge extraction.
  Usefulness: Core for KG-based QA.
  Requirements: Extracted corpus.

- `forge/scripts/build_graph_store.py`
  Purpose: Build SQLite graph store from KG edges.
  Usefulness: Core for fast KG retrieval.
  Requirements: `kg_edges.jsonl`.

- `forge/scripts/build_vector_store.py`
  Purpose: Create vector store for KG edges.
  Usefulness: Core for retrieval.
  Requirements: SentenceTransformer models + embeddings.

- `forge/scripts/generic_build_vector_store.py`
  Purpose: Vector store for generic workspace.
  Usefulness: Core for non-topic-specific corpus.
  Requirements: Embeddings + extracted corpus.

- `forge/scripts/rebuild_vector_store_embeddings.py`
  Purpose: Re-embed an existing vector store.
  Usefulness: Optional maintenance task.
  Requirements: Existing vector store metadata.

- `forge/scripts/build_methodology_kg.py`
  Purpose: Build KG from methodology sections.
  Usefulness: Optional (methodology-focused workflows).
  Requirements: Methodology corpus.

- `forge/scripts/build_methodology_vector_store.py`
  Purpose: Vector store over methodology sections.
  Usefulness: Optional (methodology retrieval).
  Requirements: Methodology corpus.

- `forge/scripts/build_methodology_edge_store.py`
  Purpose: Vector store for methodology KG edges.
  Usefulness: Optional (methodology KG).
  Requirements: Methodology KG edges.

- `forge/scripts/build_topic_methodology.py`
  Purpose: Top-level methodology build for a workspace.
  Usefulness: Optional (methodology workflows).
  Requirements: Workspace with extracted corpus.

- `forge/scripts/build_timeline_graph.py`
  Purpose: Build timeline graph (paper chronology).
  Usefulness: Optional (timeline analytics).
  Requirements: PDF metadata.

- `forge/scripts/extract_methodology_full.py`
  Purpose: Extract full methods/results sections.
  Usefulness: Optional (methodology coverage).
  Requirements: Extracted corpus.

- `forge/scripts/generic_run_pipeline.py`
  Purpose: Convenience wrapper for generic workspace build.
  Usefulness: Optional (wrapper for multiple scripts).
  Requirements: Same as individual pipeline steps.

## Fabric Agents (Reasoning / Orchestration)
- `fabric/agents/rag_agent.py`
  Purpose: Core QA agent (planner + retrieval + structured blocks).
  Usefulness: Core. Used by CLI, API, and demos.
  Requirements: Workspaces + retrieval artifacts.

- `fabric/agents/qa_graph.py`
  Purpose: LangGraph execution of QA pipeline.
  Usefulness: Core (used by output modes and tests).
  Requirements: Same as `rag_agent`.

- `fabric/agents/multi_agent_orchestrator.py`
  Purpose: Orchestrates QA + protocol + gap detection.
  Usefulness: Optional (multi-agent workflows).
  Requirements: Workspaces + templates + optional LLM.

- `fabric/agents/biofoundry_protocol_orchestrator.py`
  Purpose: Template-based biofoundry protocol synthesis.
  Usefulness: Optional (biofoundry workflows).
  Requirements: `ModuleTemplate/` + instrument/methodology assets.

- `fabric/agents/biofoundry_protocol_agent.py`
  Purpose: Protocol generation from templates only.
  Usefulness: Optional (protocol workflows).
  Requirements: Module templates.

- `fabric/agents/timeline_gap_agent.py`
  Purpose: Timeline/KG gap detection for hypothesis.
  Usefulness: Optional (gap analysis workflows).
  Requirements: Timeline graph + KG.

- `fabric/agents/timeline_summarizer.py`
  Purpose: Timeline summarization for a topic.
  Usefulness: Optional (timeline analytics).
  Requirements: Timeline graph + metadata.

- `fabric/agents/hypothesis_planner.py`
  Purpose: LLM-based hypothesis + planning helper.
  Usefulness: Optional (LLM-heavy workflows).
  Requirements: LLM access.

- `fabric/agents/run_agent_plain.py`
  Purpose: CLI wrapper for QA without LLM summarizer.
  Usefulness: Optional convenience CLI.
  Requirements: Workspaces.

- `fabric/agents/run_agent_llm.py`
  Purpose: CLI wrapper for QA with LLM summarizer.
  Usefulness: Optional convenience CLI.
  Requirements: Workspaces + LLM.

- `fabric/agents/top_candidates_report.py`
  Purpose: Deterministic top-candidates report from vector store.
  Usefulness: Optional (reporting workflows).
  Requirements: Vector store.

## Demos
- `test_hmmm/run_demos.py`
  Purpose: Run QA/protocol/biofoundry demos and save outputs.
  Usefulness: Optional; helpful for regression snapshots.
  Requirements: Workspaces + templates + optional LLM.

## Compatibility Wrappers (Legacy Imports)
- `agents/*.py`
  Purpose: Thin wrappers mapping legacy imports to `fabric/agents/*`.
  Usefulness: Optional; only needed for backward compatibility.
  Requirements: None beyond the target modules.
