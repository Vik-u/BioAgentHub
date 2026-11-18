# Biofoundry Protocol Template Selection Audit (Code-Grounded)

**A) Template Inventory (table)**
Templates are defined as Markdown files under `ModuleTemplate/` and mapped in code via `TEMPLATES` dictionaries in both agents. Evidence: `fabric/agents/biofoundry_protocol_orchestrator.py` (module scope identifier `TEMPLATES = {"E.coli_EchoMS_protocol.md": ..., "Yeast_plate_reader_protocol.md": ...}`) and `fabric/agents/biofoundry_protocol_agent.py` (module scope identifier `TEMPLATES = {"ecoli_plate": ..., "yeast_echoms": ...}`).

Template inventory:

| Template file | Code IDs / selection keys | Organism/readout mapping | Ordered module IDs (parsed from `## Module <n>` headings) | Notes |
|---|---|---|---|---|
| `ModuleTemplate/E.coli_EchoMS_protocol.md` | Orchestrator uses filename key in `fabric/agents/biofoundry_protocol_orchestrator.py` (module scope `TEMPLATES`), simple agent uses `ecoli_echoms` key in `fabric/agents/biofoundry_protocol_agent.py` (module scope `TEMPLATES`). | Orchestrator mapping uses filename substring checks: `"E.coli"` → organism, `"EchoMS"` → readout in `fabric/agents/biofoundry_protocol_orchestrator.py::build_template_map` (identifiers `"E.coli"`, `"EchoMS"`). | `module_1, module_2, module_3, module_4, module_5, module_6, module_8` derived from headings matched by `fabric/agents/biofoundry_protocol_orchestrator.py::parse_template_modules` (regex `^##\s+Module\s+(\d+)\s+[—-]\s+`) in `ModuleTemplate/E.coli_EchoMS_protocol.md` (identifier string `"## Module"`). | The template content is copied verbatim in the simple agent: `fabric/agents/biofoundry_protocol_agent.py::main` (identifier string `"Content is copied verbatim from the chosen template"`). |
| `ModuleTemplate/E.coli_plate_reader_protocol.md` | Orchestrator filename key in `fabric/agents/biofoundry_protocol_orchestrator.py` (module scope `TEMPLATES`), simple agent key `ecoli_plate` in `fabric/agents/biofoundry_protocol_agent.py` (`TEMPLATES`). | Organism/readout mapping via filename checks in `fabric/agents/biofoundry_protocol_orchestrator.py::build_template_map` (identifiers `"E.coli"`, `"PlateReader"`). | `module_1, module_2, module_3, module_4, module_5, module_6, module_7` parsed by `fabric/agents/biofoundry_protocol_orchestrator.py::parse_template_modules` (regex `^##\s+Module\s+(\d+)\s+[—-]\s+`) from `ModuleTemplate/E.coli_plate_reader_protocol.md`. | Verbatim copy behavior also enforced in UI path: `app/gradio_chatbot.py::run_biofoundry` (identifier string `"Content is copied verbatim from the chosen template"`). |
| `ModuleTemplate/Yeast_EchoMS_protocol.md` | Orchestrator filename key in `fabric/agents/biofoundry_protocol_orchestrator.py` (`TEMPLATES`), simple agent key `yeast_echoms` in `fabric/agents/biofoundry_protocol_agent.py` (`TEMPLATES`). | Organism/readout mapping via `fabric/agents/biofoundry_protocol_orchestrator.py::build_template_map` (identifiers `"Yeast"`, `"EchoMS"`). | `module_1, module_2, module_3, module_4, module_9, module_10, module_12` parsed by `fabric/agents/biofoundry_protocol_orchestrator.py::parse_template_modules` (regex `^##\s+Module\s+(\d+)\s+[—-]\s+`) from `ModuleTemplate/Yeast_EchoMS_protocol.md`. | Template selection for this file is possible via KG routing in `fabric/agents/biofoundry_protocol_orchestrator.py::select_template_for_topic` (identifier `template_key`). |
| `ModuleTemplate/Yeast_plate_reader_protocol.md` | Orchestrator filename key in `fabric/agents/biofoundry_protocol_orchestrator.py` (`TEMPLATES`), simple agent key `yeast_plate` in `fabric/agents/biofoundry_protocol_agent.py` (`TEMPLATES`). | Organism/readout mapping via `fabric/agents/biofoundry_protocol_orchestrator.py::build_template_map` (identifiers `"Yeast"`, `"PlateReader"`). | `module_1, module_2, module_3, module_4, module_9, module_10, module_11` parsed by `fabric/agents/biofoundry_protocol_orchestrator.py::parse_template_modules` (regex `^##\s+Module\s+(\d+)\s+[—-]\s+`) from `ModuleTemplate/Yeast_plate_reader_protocol.md`. | Simple agent routes to this template only if `CASE_MAP` uses `yeast_plate` (not present in current `fabric/agents/biofoundry_protocol_agent.py::CASE_MAP`). |

Module inventory (from `ModuleTemplate/Modules_library.md` headings):

| Module ID | Module name (exact heading text) | Evidence |
|---|---|---|
| `module_1` | Mutagenesis PCR & DpnI Treatment | `ModuleTemplate/Modules_library.md` line `## Module 1 — Mutagenesis PCR & DpnI Treatment` (identifier string `"## Module 1 — Mutagenesis PCR & DpnI Treatment"`). |
| `module_2` | HiFi Assembly & DH5α Transformation | `ModuleTemplate/Modules_library.md` line `## Module 2 — HiFi Assembly & DH5α Transformation` (identifier string `"## Module 2 — HiFi Assembly & DH5α Transformation"`). |
| `module_3` | DH5α Colony Picking & Culture | `ModuleTemplate/Modules_library.md` line `## Module 3 — DH5α Colony Picking & Culture` (identifier string `"## Module 3 — DH5α Colony Picking & Culture"`). |
| `module_4` | Miniprep & BL21 Transformation | `ModuleTemplate/Modules_library.md` line `## Module 4 — Miniprep & BL21 Transformation` (identifier string `"## Module 4 — Miniprep & BL21 Transformation"`). |
| `module_5` | BL21 Colony Picking & Preculture | `ModuleTemplate/Modules_library.md` line `## Module 5 — BL21 Colony Picking & Preculture` (identifier string `"## Module 5 — BL21 Colony Picking & Preculture"`). |
| `module_6` | Protein Expression Induction | `ModuleTemplate/Modules_library.md` line `## Module 6 — Protein Expression Induction` (identifier string `"## Module 6 — Protein Expression Induction"`). |
| `module_7` | E.coli screening - Plate reader | `ModuleTemplate/Modules_library.md` line `## Module 7 — E.coli screening - Plate reader` (identifier string `"## Module 7 — E.coli screening - Plate reader"`). |
| `module_8` | E.coli screening - EchoMS | `ModuleTemplate/Modules_library.md` line `## Module 8 — E.coli screening - EchoMS` (identifier string `"## Module 8 — E.coli screening - EchoMS"`). |
| `module_9` | Yeast transformation and plating | `ModuleTemplate/Modules_library.md` line `## Module 9 - Yeast transformation and plating` (identifier string `"## Module 9 - Yeast transformation and plating"`). |
| `module_10` | Yeast colony picking and fermentation | `ModuleTemplate/Modules_library.md` line `## Module 10 - Yeast colony picking and fermentation` (identifier string `"## Module 10 - Yeast colony picking and fermentation"`). |
| `module_11` | Yeast Screening - plate reader | `ModuleTemplate/Modules_library.md` line `## Module 11 - Yeast Screening - plate reader` (identifier string `"## Module 11 - Yeast Screening - plate reader"`). |
| `module_12` | Yeast Screening - EchoMS | `ModuleTemplate/Modules_library.md` line `## Module 12 - Yeast Screening - EchoMS` (identifier string `"## Module 12 - Yeast Screening - EchoMS"`). |

Required fields + schema class + defaults used to represent modules:
- The parsed schema class is `Subprocess` and `ModuleDef` in `fabric/agents/biofoundry_protocol_orchestrator.py` (dataclasses `class Subprocess` and `class ModuleDef`). Required fields are the fields parsed from headings like `- **Objective**`, `- **Description**`, `- **Actions**`, `- **Labware**`, `- **Instruments**`, `- **Materials**`, `- **Parameters**` in `ModuleTemplate/Modules_library.md` and captured by `fabric/agents/biofoundry_protocol_orchestrator.py::parse_modules_library` (identifier string `line.startswith("- **")`). Default values are empty lists in `Subprocess` (`objective: List[str] = field(default_factory=list)` etc.) and empty strings/lists are injected in `parse_modules_library` for `purpose`, `inputs`, `outputs`, `constraints`, `dependencies` (initializer keys in `current_module = {"purpose": "", "inputs": [], "outputs": [], "constraints": [], "dependencies": []}`).
- Additional required metadata fields and expected outputs are declared in code and appended to protocols: `fabric/agents/biofoundry_protocol_orchestrator.py` (identifiers `MODULE_METADATA_FIELDS` and `MODULE_OUTPUT_EXPECTATIONS`, used in `render_protocol`).
- Template-level schema classes or JSON schema definitions for templates themselves are NOT PRESENT IN CODE (no schema class is defined for template Markdown files; templates are read verbatim via `biofoundry_protocol_agent.py::load_template`).

**B) Selection/Routing Logic (with call chain)**
Entry points and call chain:
- CLI entrypoint `app/hub_cli.py::cmd_biofoundry` calls `fabric/agents/biofoundry_protocol_orchestrator.py::run_biofoundry` with args `use_kg`, `include_instruments`, `kg_top_k`, `assay_enabled`, `llm_rationale` (identifiers `cmd_biofoundry`, `run_biofoundry`).
- API entrypoint `app/hub_api.py::biofoundry_generate` calls `fabric/agents/biofoundry_protocol_orchestrator.py::run_biofoundry` with `BiofoundryRequest` fields (identifier `@app.post("/biofoundry/generate")`).
- Gradio entrypoint for template-only mode `app/gradio_chatbot.py::run_biofoundry` loads `fabric/agents/biofoundry_protocol_agent.py::CASE_MAP` and `TEMPLATES` (identifiers `CASE_MAP`, `TEMPLATES`), then returns verbatim template content.
- Gradio entrypoint for orchestrator mode `app/gradio_chatbot.py::run_biofoundry_orchestrator` calls `fabric/agents/biofoundry_protocol_orchestrator.py::run_biofoundry` (identifiers `run_biofoundry_orchestrator`, `run_biofoundry`).
- Orchestrator CLI entrypoint `fabric/agents/biofoundry_protocol_orchestrator.py::main` parses flags `--no-kg`, `--include-instruments`, `--kg-top-k`, `--no-assay-evidence`, `--topics`, `--llm-rationale`, `--kg-eval` and then calls `run_biofoundry` or `run_kg_eval` (identifier strings `--kg-top-k`, `--kg-eval`).

Routing logic for template selection:
- Simple biofoundry agent uses a hard-coded mapping: `fabric/agents/biofoundry_protocol_agent.py` (identifier `CASE_MAP = {"petase": {"template": "ecoli_plate"}, "3hp_pand": {"template": "ecoli_echoms"}, ...}`), selecting by the `case` CLI argument (`biofoundry_protocol_agent.py::main` uses `choice = CASE_MAP[args.case]`).
- Orchestrator selects organism and readout by KG similarity: `fabric/agents/biofoundry_protocol_orchestrator.py::select_template_for_topic` builds queries `f"{topic} {org} expression screening"` and `f"{topic} {ro} assay protocol"`, scores with `score_query`, and picks max score (`max(org_scores.items(), key=...)`, `max(readout_scores.items(), key=...)`).
- Organism/readout routing is then mapped to a template by exact match on `meta["organism"]` and `meta["readout"]` in `fabric/agents/biofoundry_protocol_orchestrator.py::select_template_for_topic`, with fallback to first matching organism (identifier `template_key`).

Routing inputs used (explicitly in code):
- The only inputs to template selection are `topic` (string) and KG similarity scores from `score_query` over those query strings in `fabric/agents/biofoundry_protocol_orchestrator.py::select_template_for_topic` (identifiers `"expression screening"`, `"assay protocol"`).
- Instrument availability affects module inclusion, not template selection: `fabric/agents/biofoundry_protocol_orchestrator.py::build_module_decisions` checks `instrument_available` and can set `exclusion_reason = "instrument_unavailable"` (identifier `instrument_unavailable`).
- Assay/readout constraints are enforced during module decisions via `MODULE_READOUT_REQUIREMENTS` in `fabric/agents/biofoundry_protocol_orchestrator.py` (identifier `MODULE_READOUT_REQUIREMENTS = {"module_7": "PlateReader", ...}`).

**C) Evidence Sources Used for Filling (exact stores/functions)**
Methodology KG and section evidence:
- Methodology stores are loaded from the active workspace: `fabric/services/methodology_retrieval.py::resolve_methodology_dirs` returns `workspace / "methodology_vector_store"` and `workspace / "methodology_edge_store"` (identifier strings `"methodology_vector_store"`, `"methodology_edge_store"`), using `utils/workspace_utils.py::resolve_workspace_root` (identifier `WORKSPACE_ROOT`).
- Retrieval uses `MethodologyRetrievalBackend.section_search` and `.edge_search` in `fabric/services/methodology_retrieval.py` (identifiers `section_search`, `edge_search`), and template selection uses `score_query` in `fabric/agents/biofoundry_protocol_orchestrator.py` which calls both (`score_query` calls `backend.section_search(..., top_k=6)` and `backend.edge_search(..., top_k=max(3, top_k))`).
- Evidence for template filling is gathered by `fabric/agents/biofoundry_protocol_orchestrator.py::gather_method_evidence` and then aggregated in `gather_evidence_for_case` (identifiers `gather_method_evidence`, `gather_evidence_for_case`).
- Evidence is inserted into protocol markdown under a dedicated section: `fabric/agents/biofoundry_protocol_orchestrator.py::emit_case_outputs` appends `"## KG Evidence (per module)"` and lists `relation: value` snippets (identifier string `"## KG Evidence (per module)"`).

Instrument KG evidence and inventory alignment:
- Instrument retrieval backends are in `fabric/services/instrument_retrieval.py` (`InstrumentRetrievalBackend`, methods `vector_search` and `graph_query`, identifiers `vector_search`, `graph_query`) and are only enabled when `BIOAGENT_USE_INSTRUMENTS` is set (`instrument_usage_enabled`).
- Instrument inventory is loaded from `InstrumentGraph/inventory.json` in `fabric/agents/biofoundry_protocol_orchestrator.py::load_instrument_inventory` (identifier string `"InstrumentGraph" / "inventory.json"`).
- Module eligibility checks use inventory substring matching in `fabric/agents/biofoundry_protocol_orchestrator.py::instrument_available` (identifier string `"instrument_unavailable"`) and are applied in `build_module_decisions` before evidence scoring.

Assay-specific evidence:
- Assay evidence is pulled via `fabric/agents/biofoundry_protocol_orchestrator.py::gather_assay_evidence` and `gather_assay_evidence_for_decision` (identifiers `gather_assay_evidence`, `gather_assay_evidence_for_decision`) using `backend.edge_search` with `ASSAY_KEYS` filters (identifier `ASSAY_KEYS = ["assay", "substrate", ...]`).
- Assay evidence is inserted into protocol markdown under `"## Assay Evidence (per module)"` by `fabric/agents/biofoundry_protocol_orchestrator.py::emit_case_outputs` (identifier string `"## Assay Evidence (per module)"`).

**D) Validation + Output Artifacts (paths + formats)**
Output roots and logs:
- Output root is `outputs/biofoundry_output` via `utils/output_paths.py::biofoundry_dir` (identifier `"biofoundry_output"`), and logs are under `outputs/logs/biofoundry/auto` via `fabric/agents/biofoundry_protocol_orchestrator.py` (identifier `OUT_DIR = logs_dir() / "biofoundry" / "auto"`).

Artifacts written by orchestrator:
- Modules JSON: `fabric/agents/biofoundry_protocol_orchestrator.py::emit_task_a` writes `modules.generated.json` under `outputs/logs/biofoundry/auto` (identifier `save_json(OUT_DIR / "modules.generated.json", ...)`).
- Template mapping markdown: `fabric/agents/biofoundry_protocol_orchestrator.py::emit_task_b` writes `template_mapping.generated.md` under `outputs/logs/biofoundry/auto` (identifier `save_text(OUT_DIR / "template_mapping.generated.md", ...)`).
- Protocol markdown and plan JSON: `fabric/agents/biofoundry_protocol_orchestrator.py::emit_case_outputs` writes per-case files under `outputs/logs/biofoundry/auto/runs/<timestamp>/case_studies/` (identifiers `protocol_path = base / f"{slug}.md"`, `plan_path = base / f"{slug}_plan.json"`) and a `latest/` copy (identifiers `latest_protocol_path`, `latest_plan_path`).
- KG evaluation report (optional): `fabric/agents/biofoundry_protocol_orchestrator.py::run_kg_eval` writes `kg_eval_report.json` and `kg_eval_report.md` (identifiers `json_path = output_dir / "kg_eval_report.json"`, `md_path = output_dir / "kg_eval_report.md"`).

Artifacts written by simple agent:
- `fabric/agents/biofoundry_protocol_agent.py::main` writes to user-specified `--out` path if provided (identifier `args.out.write_text(assembled)`), otherwise prints to stdout.

Validation / completeness checks implemented:
- Module inclusion scoring uses thresholds in `fabric/agents/biofoundry_protocol_orchestrator.py::decision_threshold` (identifiers `score >= 0.45` → `"include"`, `score >= 0.30` → `"optional"`) and ambiguity checks in `detect_ambiguity` (identifier `values[0] >= 0.40 and values[1] >= 0.40 and (values[0] - values[1]) < 0.05`).
- There is no explicit schema validation or required-key validation for protocol outputs beyond these scoring rules (NOT PRESENT IN CODE; outputs are assembled in `fabric/agents/biofoundry_protocol_orchestrator.py::emit_case_outputs` without validation hooks).

**E) NOT PRESENT IN CODE**
- LLM-based router/classifier for selecting templates (NOT PRESENT IN CODE; selection is hard-coded in `fabric/agents/biofoundry_protocol_agent.py::CASE_MAP` or KG-score based in `fabric/agents/biofoundry_protocol_orchestrator.py::select_template_for_topic`).
- Structured protocol schema validation (JSON Schema or Pydantic validation) for final protocol outputs (NOT PRESENT IN CODE; outputs are markdown + JSON assembled in `fabric/agents/biofoundry_protocol_orchestrator.py::emit_case_outputs`).
- Direct execution integration with laboratory schedulers or workcells (e.g., Momentum/Echo run control) (NOT PRESENT IN CODE; no `run_protocol` or workcell APIs are referenced in `fabric/agents/biofoundry_protocol_orchestrator.py` or `fabric/agents/biofoundry_protocol_agent.py`).
- Template-specific JSON/YAML schema files defining required fields per template (NOT PRESENT IN CODE; templates are raw markdown loaded via `fabric/agents/biofoundry_protocol_agent.py::load_template`).

**F) Slide-ready summary**
Slide title: Biofoundry Template Selection (KG-grounded) derived from `fabric/agents/biofoundry_protocol_orchestrator.py::select_template_for_topic` (identifier `template`).

4 box labels (based on four template files in `ModuleTemplate/` and `TEMPLATES` mapping in `fabric/agents/biofoundry_protocol_orchestrator.py`):
- E.coli + PlateReader (`ModuleTemplate/E.coli_plate_reader_protocol.md`; mapped by `fabric/agents/biofoundry_protocol_orchestrator.py::build_template_map` identifier `"PlateReader"`).
- E.coli + EchoMS (`ModuleTemplate/E.coli_EchoMS_protocol.md`; mapped by `fabric/agents/biofoundry_protocol_orchestrator.py::build_template_map` identifier `"EchoMS"`).
- Yeast + PlateReader (`ModuleTemplate/Yeast_plate_reader_protocol.md`; mapped by `fabric/agents/biofoundry_protocol_orchestrator.py::build_template_map` identifier `"Yeast"`).
- Yeast + EchoMS (`ModuleTemplate/Yeast_EchoMS_protocol.md`; mapped by `fabric/agents/biofoundry_protocol_orchestrator.py::build_template_map` identifier `"EchoMS"`).

3 bullets: what selection uses
- KG similarity over methodology sections + edges via `fabric/agents/biofoundry_protocol_orchestrator.py::score_query` (identifiers `backend.section_search(..., top_k=6)` and `backend.edge_search(..., top_k=...)`).
- Query strings formed from `topic` + organism/readout terms in `fabric/agents/biofoundry_protocol_orchestrator.py::select_template_for_topic` (identifier strings `"expression screening"`, `"assay protocol"`).
- Optional instrument availability gating at module level via `fabric/agents/biofoundry_protocol_orchestrator.py::build_module_decisions` (identifier `exclusion_reason = "instrument_unavailable"`).

3 bullets: what template enforces
- Module order is locked to the chosen template: `fabric/agents/biofoundry_protocol_orchestrator.py::render_plan` includes assumption `"Module order follows template; no reordering applied."`.
- Protocol content is copied verbatim from template in the simple agent: `fabric/agents/biofoundry_protocol_agent.py::main` (identifier string `"Content is copied verbatim from the chosen template"`).
- Required metadata fields per module are explicitly listed in `fabric/agents/biofoundry_protocol_orchestrator.py` (identifier `MODULE_METADATA_FIELDS`) and appended in `render_protocol`.

2 bullets: what we don’t do (yet)
- No schema validation of generated protocols (NOT PRESENT IN CODE; outputs are assembled in `fabric/agents/biofoundry_protocol_orchestrator.py::emit_case_outputs` without validation hooks).
- No automatic workcell execution or scheduling integration (NOT PRESENT IN CODE; no workcell APIs or `run_protocol` calls exist in `fabric/agents/biofoundry_protocol_orchestrator.py`).

Takeaway: Template selection is deterministic and KG-scored (or hard-coded) with verbatim template content, and evidence is appended rather than rewritten (`fabric/agents/biofoundry_protocol_orchestrator.py::select_template_for_topic`, `fabric/agents/biofoundry_protocol_agent.py::load_template`).
