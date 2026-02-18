# Runtime Audit (CLI --help)

This audit checks that each script responds to `--help` without executing the full pipeline.

Total scripts: 37
OK: 36
Excluded: 1
Failures: 0

## Results
- `app/hub_cli.py` -> ok
- `app/gradio_chatbot.py` -> ok
- `app/qa_chat_langgraph.py` -> ok
- `app/protocol_agent_cli_v2.py` -> ok
- `app/instrument_protocol_cli_v2.py` -> ok
- `forge/run_forge.py` -> ok
- `forge/scripts/generic_run_pipeline.py` -> ok
- `forge/scripts/build_methodology_edge_store.py` -> ok
- `forge/scripts/build_methodology_kg.py` -> ok
- `forge/scripts/build_methodology_vector_store.py` -> ok
- `forge/scripts/build_vector_store.py` -> ok
- `forge/scripts/build_topic_full.py` -> ok
- `forge/scripts/build_graph_store.py` -> ok
- `forge/scripts/generic_build_vector_store.py` -> ok
- `forge/scripts/build_topic_methodology.py` -> ok
- `forge/scripts/build_timeline_graph.py` -> ok
- `forge/agents/kg_schema_agent.py` -> ok
- `forge/scripts/extract_methodology_full.py` -> ok
- `forge/scripts/extract_corpus.py` -> ok
- `forge/scripts/build_kg_edges.py` -> ok
- `forge/scripts/build_topic_workspaces.py` -> ok
- `forge/scripts/rebuild_vector_store_embeddings.py` -> ok
- `forge/scripts/generic_extract_corpus.py` -> ok
- `forge/scripts/run_structured_audit.py` -> ok
- `forge/scripts/build_structured_facts.py` -> ok
- `forge/scripts/extract_pdf_artifacts.py` -> ok
- `fabric/agents/multi_agent_orchestrator.py` -> ok
- `fabric/agents/run_agent_plain.py` -> ok
- `fabric/agents/timeline_gap_agent.py` -> ok
- `fabric/agents/run_agent_llm.py` -> ok
- `fabric/agents/top_candidates_report.py` -> ok
- `fabric/agents/biofoundry_protocol_orchestrator.py` -> ok
- `fabric/agents/timeline_summarizer.py` -> ok
- `fabric/agents/hypothesis_planner.py` -> ok
- `fabric/agents/biofoundry_protocol_agent.py` -> ok
- `fabric/agents/rag_agent.py` -> ok
- `test_hmmm/run_demos.py` -> excluded
  reason: No CLI parser; running would execute full demos.
