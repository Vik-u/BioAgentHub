# Biofoundry Protocol Generation System — Current-System Formalization

This document formalizes the biofoundry protocol generation system exactly as implemented in the current codebase. It is intended for auditability and traceability. No new algorithms are proposed here; any future work must be explicitly labeled elsewhere.

## Scope
This specification covers:
- Template selection (organism/readout) from methodology KG evidence.
- Module decision layer (12 modules) with hard-gates and evidence scoring.
- Citation registry and canonical ID mapping.
- KG evaluation mode (`--kg-eval`) and its deterministic metrics.
- Output JSON schemas.
- Determinism guarantees.
- Code mapping (doc → implementation).
- Known limitations (auto-maintained).

## Inputs

### Primary Inputs
- **Topic** (string): `case["topic"]` from `select_template_for_topic` or CLI `--topics`.
- **Module templates** (files):
  - `ModuleTemplate/E.coli_EchoMS_protocol.md`
  - `ModuleTemplate/E.coli_plate_reader_protocol.md`
  - `ModuleTemplate/Yeast_EchoMS_protocol.md`
  - `ModuleTemplate/Yeast_plate_reader_protocol.md`
- **Module library**: `ModuleTemplate/Modules_library.md`
- **Instrument inventory**: `InstrumentGraph/inventory.json`
- **Methodology KG backend**: `services/methodology_retrieval.get_backend()` (section + edge search)
- **Instrument KG backend**: only used in optional evidence enrichment (not in module decision gating)

### Derived Inputs
- **Module ordering**: parsed from template files (`parse_template_modules`).
- **Module metadata**: parsed from `Modules_library.md` (`parse_modules_library`).
- **Module focus terms**: derived from module name + subprocess actions/materials/instruments + `MODULE_HINTS`.

## End-to-End Pipeline

### 1) Template Selection (Organism + Readout)

**Queries used** (exact strings):
- Organism:
  - `"{topic} E.coli expression screening"`
  - `"{topic} Yeast expression screening"`
- Readout:
  - `"{topic} PlateReader assay protocol"`
  - `"{topic} EchoMS assay protocol"`

**Scoring**
- `score_query` averages similarity scores from BOTH section search and edge search over the query.
- For each organism and readout, scores are recorded in `selection_evidence` with the top sources.

**Selection**
- Choose organism = max score among organisms.
- Choose readout = max score among readouts.
- Choose template by matching organism+readout to template map; fallback is first matching organism or first template.

**Selection evidence written**
- `selection_evidence.organism.{E.coli|Yeast}.score`
- `selection_evidence.organism.{E.coli|Yeast}.sources`
- `selection_evidence.readout.{PlateReader|EchoMS}.score`
- `selection_evidence.readout.{PlateReader|EchoMS}.sources`

### 2) Module Decision Algorithm (Modules 1–12)

**Ordering**
- `ordered_modules` is parsed from the selected template file and is not modified.

**Hard-gate rules (override similarity)**
- **Readout mismatch**:
  - PlateReader readout excludes EchoMS assay modules.
  - EchoMS readout excludes PlateReader-only assay modules.
- **Instrument unavailable**: if required instrument is not found in `InstrumentGraph/inventory.json`.
- **Organism mismatch**: organism-specific modules that do not match `case["organism"]`.
- **Template not selected**: if module is not in `ordered_modules`.

**Evidence gathering (module-specific)**
- **Methodology sections**: `section_search` using module-specific query phrases.
- **Methodology edges**: `edge_search` using module-specific query phrases.
- **Assay evidence**: only for assay modules (`module_7`, `module_8`, `module_11`, `module_12`), filtered by assay keywords.
- Evidence is filtered by module focus terms (derived from module name + subprocess actions/materials/instruments + `MODULE_HINTS`).
- Deduplication uses a cross-module `seen_keys` set to avoid reusing identical evidence chunks.

**Scoring aggregation**
- `method_score` = average of `score_query_details` across module-specific query phrases.
- `assay_score` = average of top N (N=min(3,len)) assay evidence scores (assay modules only).
- `combined_score` =
  - assay modules: `(method_score + assay_score) / 2`
  - non-assay modules: `method_score`

**Decision thresholds**
- include if `score >= 0.45`
- optional if `0.30 <= score < 0.45`
- exclude if `score < 0.30` with `exclusion_reason=low_evidence`

**Ambiguity rule**
- `module_status=ambiguous` with `exclusion_reason=contradiction_ambiguous` if:
  - top two `avg_score` values are both `>= 0.40` and margin `< 0.05`.

**Top evidence sets**
- `top_evidence_sets` selects the top 2 items from combined evidence (sections + edges + assays).
- Deterministic ranking: `(-score, type, summary)`.
- Each top evidence entry includes `citation_ids` and a short summary.

**Rationale format**
- Deterministic sentence with score and `[n]` tags (from citations) if available.

### 3) Citation Registry

**Canonical ID rules**
- DOI: `doi:<match>`
- PMID: `pmid:<id>`
- EuropePMC: `europepmc:<tail>`
- PDF file: `file:<stem>`
- Fallback: `text:<normalized>`

**Dedup key**
- `source_id|title|section`

**Ordering**
- Insertion order: selection evidence → module evidence in module order → evidence order in `build_module_decisions`.

**Mapping**
- Each citation object has:
  - `id`, `source_id`, `source`, `title`, `section`

### 4) KG Eval Mode (`--kg-eval`)

**Decision questions (exact)**
- `host_ecoli`: “{topic} E.coli expression protocol”
- `host_yeast`: “{topic} yeast expression protocol”
- `readout_platereader`: “{topic} plate reader fluorescence absorbance assay”
- `readout_echoms`: “{topic} EchoMS mass spec assay protocol”
- `plate_96`: “{topic} 96 well plate assay”
- `plate_384`: “{topic} 384 well plate assay”
- `echo_dispense`: “{topic} acoustic dispensing Echo”
- `spark_reader`: “{topic} plate reader Tecan Spark”

**Coverage**
- Hit if `top_score >= 0.35`.
- `coverage_rate` = hits / number_of_questions.

**Template selection stability**
- Run `select_template_for_topic` 5 times.
- `stability = mode_frequency / 5`.
- Record full score table per run.

**Precision@3 heuristic**
- For each module, take top 3 evidence items.
- Mark relevant if any module focus term occurs in evidence text.
- `precision@3 = relevant_count / 3`.
- Average across all modules.

**Contradiction flags**
- `host_contradiction=True` if `host_ecoli.top_score >= 0.45` AND `host_yeast.top_score >= 0.45`.
- `readout_contradiction=True` if `readout_platereader.top_score >= 0.45` AND `readout_echoms.top_score >= 0.45`.

**Traceability**
- `traceability_rate = excluded_modules_with_reason_and_evidence_or_hard_gate / excluded_modules`.
- Hard-gate reasons: `readout_mismatch`, `instrument_unavailable`, `organism_mismatch`, `template_not_selected`.

**Outputs**
- `logs/biofoundry/auto/kg_eval/kg_eval_report.json`
- `logs/biofoundry/auto/kg_eval/kg_eval_report.md`

## Determinism Guarantees

Deterministic behavior is guaranteed by:
- Fixed module iteration order (`module_1..module_12`).
- Query phrase order from `module_query_phrases` (deduped in insertion order).
- Evidence ranking with explicit sort keys and caps.
- Citation insertion order and dedup key.
- Stable thresholds and scoring rules with no random components.

Non-deterministic elements are not present in module decisions or KG eval. LLM usage is optional and not used by these components.

## Output Schemas

### Plan JSON (`*_plan.json`)
Top-level keys include:
- `case_study_title`
- `organism`
- `readout`
- `closest_template_used`
- `ordered_modules`
- `parameters_needed`
- `TODOs`
- `assumptions`
- `selection_evidence`
- `evidence`
- `assay_evidence`
- `module_decisions` (list length 12)
- `citations` (list)
- `decision_evidence`
- `llm_rationale` (optional)

`module_decisions` fields:
- `module_id`
- `module_name`
- `module_status` (required/include/optional/excluded/ambiguous)
- `score`
- `exclusion_reason` (empty if included/optional/required)
- `required_instruments`
- `evidence_sources` (list of citation objects)
- `top_evidence_sets` (top 2 evidence entries with `citation_ids`)
- `rationale` (sentence with `[n]` tags)

`citations` fields:
- `id`, `source_id`, `source`, `title`, `section`

`decision_evidence` fields:
- `sections` (methodology sections)
- `edges` (methodology edges)
- `assays` (assay edges for assay modules)
- `queries` (module-specific query phrases)

### KG Eval JSON (`kg_eval_report.json`)
- `generated_at`
- `topics[topic].coverage` (per question + coverage_rate)
- `topics[topic].stability` (chosen_templates, stability, run_scores)
- `topics[topic].precision_at_3` (per_module, avg_precision)
- `topics[topic].contradictions` (host_contradiction, readout_contradiction)
- `topics[topic].traceability` (traceability_rate, missing_modules)
- `topics[topic].kg_fix_suggestions`

## Code Mapping

### Template selection
- `select_template_for_topic`
- `score_query`
- `score_query_details`
- `build_template_map`

### Module decision layer
- Hard-gates: `MODULE_READOUT_REQUIREMENTS`, `MODULE_ORGANISM_REQUIREMENTS`, `instrument_available`
- Evidence gathering: `gather_section_evidence`, `gather_edge_evidence`, `gather_assay_evidence_for_decision`
- Module focus terms: `module_focus_terms`, `module_query_phrases`, `MODULE_HINTS`
- Scoring: `compute_method_score`, `compute_assay_score`
- Thresholds: `decision_threshold`
- Ambiguity: `detect_ambiguity`
- Ranking: `rank_evidence_items`, `summarize_evidence_item`
- Decisions: `build_module_decisions`

### Citation registry
- `CitationRegistry`
- `canonical_source_id`

### KG eval
- `DECISION_QUERIES`
- `compute_coverage_metrics`
- `compute_template_stability`
- `compute_precision_at_k`
- `compute_contradictions`
- `compute_traceability_rate`
- `run_kg_eval`

## Known limitations (current)

<!-- LIMITATIONS:START -->
- LIMITATION: instrument availability uses substring matching; aliases may be missed. (/work/hdd/bgcg/viku/PlayGround/CaseStudy/BioAgentHub/agents/biofoundry_protocol_orchestrator.py:335, context: def instrument_available)
### KG-eval flags
- petase: host_contradiction=true, readout_contradiction=true
<!-- LIMITATIONS:END -->

## Limitations Maintainer
A deterministic script updates the limitations section by scanning for tags:
- `LIMITATION:`
- `TODO(LIMITATION):`

If a KG eval report exists, it appends a “KG-eval flags” subsection with contradiction/coverage/stability flags derived from metrics only (no new claims).

