# PETase Knowledge & RL System

This workspace ingests PETase-related PDFs, extracts text + structured facts, builds a knowledge graph/vector store, and powers retrieval-augmented RL + LLM agents for planning new experiments and designs. It also supports topic-agnostic workspaces (data/*) and Biofoundry instrument-aware protocols.

## Repository Layout

```
KnowledgeGraph/        # PETase KG (text/metadata/kg_edges/graph.sqlite/vector_store/methodology/protocols)
Papers/                # raw PETase PDFs
data/                  # topic folders (3hp_pand, c4c2_decarb, ired, petase, retron, transaminase)
workspaces/            # per-topic + merged generic workspaces (text + vector stores)
08_Instrument_Docs/    # instrument manuals (for Biofoundry modes)
InstrumentGraph/       # instrument text/metadata/kg_edges/vector_store/inventory
scripts/               # ingestion, KG builders, topic workspace builder
services/              # retrieval backends, LLM config, instrument/methodology helpers
agents/                # RL policy, protocol agents (papers + Biofoundry), PPO training
app/                   # CLI, Gradio, unified chatbot
```

## End-to-End Pipeline

### PETase KG (structured)
1) PDFs → text/metadata: `scripts/extract_corpus.py --pdf-dir Papers --out-dir KnowledgeGraph [--export-images]`
2) Heuristic KG edges: `scripts/build_kg_edges.py` → `KnowledgeGraph/kg_edges.jsonl`
3) Graph DB: `scripts/build_graph_store.py` → `KnowledgeGraph/graph.sqlite`
4) Vector store (edges): `scripts/build_vector_store.py` → `KnowledgeGraph/vector_store/`
5) Methodology/protocols (optional): `scripts/extract_methodology_full.py` → `build_methodology_kg.py` → `build_methodology_edge_store.py` / `build_methodology_vector_store.py` → `build_protocols.py`

### Topic-agnostic workspaces (text + vector only)
- Build all topics in `data/` + merged sets:
  ```bash
  python scripts/build_topic_workspaces.py --data-root data --workspace-root workspaces --model sentence-transformers/all-MiniLM-L6-v2
  ```
  Outputs per-topic workspaces (`workspaces/3hp_pand`, `.../retron`, etc.), `workspaces/petase_full` (Papers + data/petase), and `workspaces/all_topics` (everything combined).

### Biofoundry instruments
1) Ingest manuals: `scripts/extract_instrument_corpus.py --docs-dir 08_Instrument_Docs --out-dir InstrumentGraph`
2) Instrument KG + vector: `scripts/build_instrument_kg.py`, `scripts/build_instrument_vector_store.py`
3) Inventory: `scripts/build_instrument_inventory.py`

### Quick rebuild when new PDFs arrive
- PETase KG: rerun the PETase steps above.
- Topic workspaces: rerun `scripts/build_topic_workspaces.py` (idempotent).

## Usage Guide

### Unified chatbot (QA + protocols across workspaces)
```bash
python app/unified_chat.py --mode qa --use-llm
python app/unified_chat.py --mode protocol --protocol-mode relaxed         # papers/methodology-driven
python app/unified_chat.py --mode protocol --protocol-mode biofoundry      # instrument-constrained
```
- Selects a workspace interactively (or `--workspace`). Sets `WORKSPACE_ROOT` and clears retrieval caches. Use `--alias-expansion` only for PETase topics.

### PETase CLI chat (legacy)
```bash
python app/cli_chat.py --mode llm
python app/cli_chat.py --mode llm --policy models/ppo_policy.zip
```

### Protocol agents (direct)
- Methodology-driven: `python app/protocol_agent_cli.py "..."` (PETase KnowledgeGraph)
- Instrument-constrained: `python app/instrument_protocol_cli_v2.py "..."` (InstrumentGraph)

### Batch benchmarking
```bash
python scripts/report_answer_metrics.py --mode llm --questions-file benchmark_questions.txt [--policy models/ppo_policy.zip]
```

### FastAPI retrieval (optional)
```bash
uvicorn services.retrieval_service:app --host 0.0.0.0 --port 8000 --reload
```
- Honors `WORKSPACE_ROOT` for swapping vector/graph; `USE_ALIAS_EXPANSION=0` to disable PETase-specific query boosts.

## Metrics Explained

| Metric           | Meaning                                                                              | Typical Range |
|------------------|--------------------------------------------------------------------------------------|---------------|
| FAISS avg        | Mean cosine similarity between question embedding and retrieved evidence sentences. | 0.6–0.8       |
| KG conf avg      | Average heuristic confidence of the KG edges used (captures clarity of statements). | 0.4–0.9 (populates as edges refresh) |
| RL reward sum    | Policy reward for the episode (vector hit + graph hop + summary).                   | ~0.6 with heuristic policy |
| Citations        | Inline `[n]` markers referencing the originating PDF.                               | integer IDs   |

## Inputs & Outputs

- **Input**: PDFs under `Papers/`. Add new files and run `scripts/update_pipeline.py`.
- **Output**:
  - Text files (`KnowledgeGraph/text/*.txt`)
  - Metadata JSON (`KnowledgeGraph/metadata/*.json`)
- Knowledge graph edges (`KnowledgeGraph/kg_edges.jsonl`)
- Vector store (`KnowledgeGraph/vector_store/*`)
- Graph DB (`KnowledgeGraph/graph.sqlite`)
- Methodology extracts (`KnowledgeGraph/methodology/*.json`)
- Protocol snippets (`KnowledgeGraph/protocols/*.json`)
- Logs (`logs/*.jsonl`)

## How the RL/LLM agent works

There are two policy options:

1. **Heuristic policy** – deterministic sequence (vector search → graph expand → summarize). No training required.
2. **PPO policy** – train with `python agents/train_ppo.py --questions-file benchmark_questions.txt --timesteps 20000 --output models/ppo_policy`. Load via `--policy models/ppo_policy.zip` in the CLI or benchmarking script.

Regardless of policy, the loop is identical:

1. **Vector search**: question embedding ↔ FAISS index to pull top sentences.
2. **Graph expansion**: uses SQLite KG to pull related edges (mutations, substrates) with alias-aware seeding.
3. **Expected entity boost**: ensures question-specific enzymes appear.
4. **Summarization**: GPT-OSS (when `--mode llm`) produces natural prose with inline citations.
5. **Metrics logging**: FAISS/KG scores and RL reward are stored in `logs/rl_agent_runs.jsonl`.

## FAQ / Tips

- **New PDFs**: run `python scripts/update_pipeline.py`. This rebuilds the entire knowledge stack so the agent immediately “sees” the new paper.
- **Confidence**: treat FAISS avg + RL reward as quick sanity checks. If FAISS < 0.5, the answer likely needs better evidence. (KG confidence will populate once legacy edges are backfilled.)
- **Benchmarking**: update `benchmark_questions.txt` to track coverage over your priority question set.
- **LLM config**: `config/llm_config.json` controls whether we use local Ollama/GPT-OSS or a cloud API.
- **Protocol planning**: run `python scripts/build_protocols.py` followed by `python app/protocol_agent_cli.py "..."` for LangChain/LangGraph-generated experimental roadmaps.

## Roadmap

- Populate KG confidence for historical edges (so `kg_conf_avg` stops showing `n/a`).
- Optional Streamlit/Gradio UI (CLI already supports citations + metrics).
- Hybrid metrics dashboard (plots over time using `scripts/report_answer_metrics.py`).
- Larger question sets + reward shaping for PPO policies.

For any new automation, drop additional scripts into `scripts/` and wire them into `update_pipeline.py`.
