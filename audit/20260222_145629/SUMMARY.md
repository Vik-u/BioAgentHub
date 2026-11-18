**Overview**
- Repo audited: `/taiga/illinois/eng/chbe/zhao5/vikas/iBF/BioAgentHub_iBF`.
- Audit outputs: `audit/20260222_145629/` (see `audit/20260222_145629/METRICS.json` for full structured results).

**Task 1 — KG Noise Audit (Duplicates + Unit/Parse Noise)**
- KG edge files found: 19 JSONL edge artifacts across `workspaces/*`, `InstrumentGraph/`, `archive/legacy_20260204/**`, and `tests/fixtures/workspace_tiny/`.
- KG schemas found: 6× `kg_schema.json` and 3× `methodology_kg_schema.json` (paths listed in `METRICS.json`).
- High duplicate pressure by `(subject, relation, value)` and `(relation, value)` is present in current workspaces (examples):
- `workspaces/petase/kg_edges.jsonl`: `edge_count=85966`, `dup_sro=69884`, `dup_rel_val=84513`.
- `workspaces/3hp_pand/kg_edges.jsonl`: `edge_count=12016`, `dup_sro=7498`, `dup_rel_val=11745`.
- `InstrumentGraph/kg_edges.jsonl`: `edge_count=6854`, `dup_exact=707`, `dup_sro=6318`, `dup_rel_val=6552`.
- Unit/parse noise is widespread in methodology KGs (line-break + unit artifacts). Example value fragments observed: `3.7 m`, `0.25 m` (concentration), `584 nm` (captured as concentration), and lowercase liter values like `10 l`.
- Top noisy relations (global across KGs) and why:
- `volume`: lowercase `l` values (e.g., `10 l`, `2 l`, `7 l`) and PDF line-break artifacts.
- `temperature`: broken `°C` tokens and line-break split units.
- `speed`: split `rpm`/`xg` tokens across line breaks.
- `concentration`: `m` without `M` (e.g., `3.7 m`, `0.25 m`) and wavelength values like `584 nm` treated as concentration.
- `duration`: time units split across line breaks.
- `pH`: values embedded in broken sentences (line breaks/hyphenation).
- `has_mutation`: noise dominated by broken sentence fragments, not unit parsing.
- `active_temperature`: same unit-break patterns as temperature.
- `temperature_range`: dash/line-break artifacts inside ranges.
- `active_pH`: same issues as pH.

**Task 2 — KG Exploitation Audit (Where KGs Are Consumed + Numeric Parameter Flow)**
- Primary KG consumers (paths + entrypoints):
- `fabric/agents/protocol_agent_v2.py::run_protocol_agent_v2` uses `MethodologyRetrievalBackend.section_search` (section_type filtered) and `edge_search` (no section filter).
- `fabric/services/methodology_retrieval.py::MethodologyRetrievalBackend` provides vector search over methodology sections and edges; `filter_edges_by_section` exists but is not used in protocol generation.
- `fabric/agents/rag_agent.py::collect_kg_edge_evidence / collect_candidate_evidence` uses `graph.sqlite` (built from `kg_edges.jsonl`) with SQL `LIKE` filters; no methods/experimental prioritization.
- `fabric/services/retrieval_service.py::RetrievalBackend` uses `vector_store` + `graph.sqlite` (BM25/FAISS); no method-type prioritization.
- `fabric/agents/instrument_protocol_agent_v2.py` + `fabric/services/instrument_retrieval.py` consume `InstrumentGraph/kg_edges.jsonl` (vector search + sqlite graph).
- `fabric/agents/timeline_gap_agent.py` reads `kg_edges.jsonl` and `timeline_edges.jsonl` for summaries.
- Numeric parameter extraction paths (repo-grounded):
- `forge/scripts/build_kg_edges.py`: regex over sentences (temperature, pH, time, degradation) → `kg_edges.jsonl`.
- `forge/scripts/build_methodology_kg.py`: regex over methodology sections (temp, time, volume, concentration, speed) → `methodology_kg_edges.jsonl`.
- `forge/scripts/build_structured_facts.py`: normalization (`normalized_value`, `normalized_unit`) exists but no runtime consumer found in protocol/QA paths.
- `fabric/agents/protocol_agent_v2.py`: `PARAM_RE` regex + heuristic injection; `_has_parameter` returns True when the draft contains `No numeric parameters reported in sources`, allowing validation to pass without real numbers.
- Pydantic schema enforcement and unit normalization are **not** executed at runtime in KG consumers; only schema induction uses PydanticAI (`forge/agents/kg_schema_agent.py`).

**Prioritized Fixes (Grounded by File/Function)**
- Fix `_has_parameter` in `fabric/agents/protocol_agent_v2.py` so it does **not** treat `No numeric parameters reported in sources` as a valid parameter.
- Filter parameter edges in `protocol_agent_v2.py` to experimental sections (use `MethodologyRetrievalBackend.filter_edges_by_section`).
- Add unit validation/normalization to `forge/scripts/build_methodology_kg.py` (reject `m`/`l` without proper units; use normalization logic from `forge/scripts/build_structured_facts.py`).
- De-duplicate methodology edges by `(paper, relation, value)` at build time to reduce repeated edges.
- Prefer `normalized_value/normalized_unit` when available and expose them to protocol generation instead of raw strings.
- Add explicit unit sanity checks to parameter selection in `protocol_agent_v2.py` (avoid `nm` for concentration unless explicitly `nM`).

**Task 3 — Minimal Tracking**
- Added `utils/ops_tracking.py` with `start_run`, `log_artifact`, `finalize_run` and `audit/_private/` storage; `audit/_private/` is gitignored.
- Wired tracking into new audit scripts under `tools/`.

**Task 4 — Modularization + CI**
- Modules and recommended CLI entrypoints:
- KG build: `python forge/scripts/build_kg_edges.py --workspace workspaces/<topic>`.
- Methodology KG: `python forge/scripts/build_methodology_kg.py --workspace workspaces/<topic>` + `python forge/scripts/build_methodology_edge_store.py --edges ... --out-dir ...`.
- KG query: `python -m uvicorn services.retrieval_service:app`.
- Protocol generation: `python app/instrument_protocol_cli_v2.py "<question>"` and `python -c "from fabric.agents.protocol_agent_v2 import run_protocol_agent_v2; print(run_protocol_agent_v2('...'))"`.
- Audits: `python tools/kg_noise_audit.py --root .` and `python tools/kg_exploitation_audit.py`.
- GitHub Actions added: `.github/workflows/smoke.yml` (schema normalization + pytest) and `.github/workflows/audit-smoke.yml` (KG noise audit on fixture).
