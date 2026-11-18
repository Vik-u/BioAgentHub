#!/usr/bin/env python3
"""Enhanced protocol agent using full methodology sections + instrument KG."""

from __future__ import annotations

import json
import os
import re
from collections import defaultdict
from pathlib import Path
from typing import Dict, List

# Guard against thread-pool init failures during import-time BLAS usage.
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
os.environ.setdefault("RAYON_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

from services import local_llm
from utils.output_paths import logs_dir
from utils.workspace_utils import resolve_workspace_root
from services.methodology_retrieval import get_backend as get_method_backend
from services.instrument_retrieval import get_backend as get_instrument_backend
from services.generic_retrieval import GenericRetrievalBackend
from utils.numeric_normalization import (
    discover_units_from_edges,
    normalize_edge_numeric,
    cluster_numeric_values,
    section_priority,
)

LOG_DIR = logs_dir() / "protocol_v2_runs"
LOG_DIR.mkdir(parents=True, exist_ok=True)


DOI_RE = re.compile(r"(10\\.[0-9]{4,9}/[A-Z0-9._;()/:\\-]+)", re.IGNORECASE)
SECTION_RE = re.compile(r"^##\s+(Computational Workflow|Experimental Workflow)\s*$", re.MULTILINE)
STEP_RE = re.compile(r"^\s*\d+\.\s+", re.MULTILINE)
PARAM_RE = re.compile(
    r"\b(?:"
    r"\d+(?:\.\d+)?\s*(?:°C|C|K|°F|min|mins|minutes|h|hr|hrs|hours|s|sec|secs|seconds|"
    r"µL|uL|mL|L|mg|g|µg|ng|mM|µM|nM|pH|rpm|x\s?g|×g|%)"
    r"|10\^\d+"
    r"|\d+(?:\.\d+)?\s*(?:variants|colonies|replicates|wells|plates|samples)"
    r")\b",
    re.IGNORECASE,
)
SENTENCE_RE = re.compile(r"[.!?](?:\s|$)")

MIN_COMP_SENTENCES = 2
MIN_ACTION_SENTENCES = 2
MAX_ACTION_SENTENCES = 5
MAX_RETRIES = 5

SAFETY_KEYWORDS = (
    "biohazard",
    "biosafety",
    "bsl",
    "ppe",
    "gloves",
    "lab coat",
    "eye protection",
    "goggles",
    "fume hood",
    "hazardous",
    "toxic",
    "flammable",
    "corrosive",
    "irritant",
    "dispose",
    "disposal",
    "decontam",
    "bleach",
    "autoclave",
    "sterile",
    "sterilize",
    "pathogen",
    "infectious",
)
SAFETY_KEYWORD_RE = re.compile(r"\\b(" + "|".join(map(re.escape, SAFETY_KEYWORDS)) + r")\\b", re.IGNORECASE)
SAFETY_EXCLUDE_RE = re.compile(r"J\\s+Hazard\\s+Mater", re.IGNORECASE)
SAFETY_MAX_CHARS = 240
SAFETY_MAX_NOTES = 6


def _extract_doi(text: str | None) -> str | None:
    if not text:
        return None
    match = DOI_RE.search(text)
    if match:
        return match.group(1).rstrip(").,;")
    return None


def _text_path_for_pdf(pdf_file: str | None) -> Path | None:
    if not pdf_file:
        return None
    workspace = resolve_workspace_root()
    candidate = workspace / "text" / f"{Path(pdf_file).stem}.txt"
    return candidate if candidate.exists() else None


def _doi_from_pdf(pdf_file: str | None) -> str | None:
    txt_path = _text_path_for_pdf(pdf_file)
    if not txt_path:
        return None
    try:
        snippet = txt_path.read_text(encoding="utf-8", errors="ignore")[:20000]
    except Exception:
        return None
    return _extract_doi(snippet)


def load_sections_for_prompt(results: List[Dict[str, str]], source_map: Dict[tuple, int]) -> str:
    lines = []
    for doc in results:
        heading = doc.get("heading") or doc.get("section_type").title()
        paper = doc.get("paper") or Path(doc.get("pdf_file") or "").stem
        pdf_file = doc.get("pdf_file")
        doi = _extract_doi(doc.get("text")) or _doi_from_pdf(pdf_file)
        source_id = source_map.get((paper, pdf_file, doi))
        label = f"S{source_id}" if source_id else "S?"
        lines.append(f"### {heading} ({label} — {paper})\n{doc.get('text')[:1500]}")
    return "\n\n".join(lines)


def gather_methodology_edges(question: str, limit: int = 40) -> List[Dict[str, str]]:
    backend = get_method_backend()
    return backend.edge_search(question, top_k=limit)


def gather_full_kg_evidence(question: str, limit: int = 20) -> List[Dict[str, str]]:
    try:
        backend = GenericRetrievalBackend(resolve_workspace_root())
    except Exception:
        return []
    try:
        return backend.search(question, top_k=limit)
    except Exception:
        return []


def gather_instrument_evidence(question: str, sections: List[Dict[str, str]]) -> List[Dict[str, str]]:
    try:
        backend = get_instrument_backend()
    except Exception:
        return []
    queries = [question] + [sec.get("text", "")[:300] for sec in sections]
    evidence = []
    seen = set()
    for query in queries:
        for row in backend.vector_search(query, top_k=8):
            meta = row["metadata"]
            key = (meta["instrument"], meta["relation"], meta["value"])
            if key in seen:
                continue
            seen.add(key)
            evidence.append(
                {
                    "instrument": meta["instrument"],
                    "relation": meta["relation"],
                    "value": meta["value"],
                    "sentence": meta["sentence"],
                    "pdf_file": meta["pdf_file"],
                }
            )
            if len(evidence) >= 30:
                return evidence
    return evidence


def extract_safety_notes(
    sections: List[Dict[str, str]],
    source_map: Dict[tuple, int],
) -> List[str]:
    notes: List[str] = []
    seen = set()
    for doc in sections:
        text = doc.get("text") or ""
        if not text:
            continue
        flattened = re.sub(r"\\s+", " ", text).strip()
        paper = doc.get("paper") or Path(doc.get("pdf_file") or "").stem
        pdf_file = doc.get("pdf_file")
        doi = _extract_doi(flattened) or _doi_from_pdf(pdf_file)
        source_id = source_map.get((paper, pdf_file, doi))
        label = f"S{source_id}" if source_id else "S?"
        for sentence in re.split(r"(?<=[.!?])\\s+", flattened):
            normalized = sentence.strip()
            if not normalized:
                continue
            if SAFETY_EXCLUDE_RE.search(normalized):
                continue
            if not SAFETY_KEYWORD_RE.search(normalized):
                continue
            key = (normalized, label)
            if key in seen:
                continue
            seen.add(key)
            snippet = normalized if len(normalized) <= SAFETY_MAX_CHARS else normalized[:SAFETY_MAX_CHARS].rstrip() + "…"
            notes.append(f"- {snippet} (source: {label})")
            if len(notes) >= SAFETY_MAX_NOTES:
                return notes
    return notes


def _split_sections(text: str) -> Dict[str, str]:
    matches = list(SECTION_RE.finditer(text))
    if len(matches) < 2:
        return {}
    sections: Dict[str, str] = {}
    for idx, match in enumerate(matches):
        start = match.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
        sections[match.group(1)] = text[start:end].strip()
    return sections


def _split_steps(section_text: str) -> List[str]:
    steps = []
    matches = list(STEP_RE.finditer(section_text))
    for idx, match in enumerate(matches):
        start = match.start()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(section_text)
        steps.append(section_text[start:end].strip())
    return steps


def _sentence_count(text: str) -> int:
    if not text:
        return 0
    return len(SENTENCE_RE.findall(text))


def _has_parameter(text: str) -> bool:
    if not text:
        return False
    return bool(PARAM_RE.search(text))


def _tokenize(text: str) -> List[str]:
    return re.findall(r"[a-z0-9]+", (text or "").lower())


def _annotate_consensus(param_bank: List[Dict[str, str]]) -> None:
    groups: Dict[tuple, List[tuple]] = defaultdict(list)
    for idx, item in enumerate(param_bank):
        if item.get("numeric_status") != "VALID_NORMALIZED":
            continue
        value = item.get("normalized_value")
        if value is None:
            continue
        key = (item.get("relation_category") or "other", item.get("normalized_unit") or "")
        groups[key].append((float(value), idx, item.get("paper_id") or ""))
    for item in param_bank:
        item.setdefault("cluster_size", 1)
        item.setdefault("cluster_paper_diversity", 1)
    for key, values in groups.items():
        clusters = cluster_numeric_values([(v, idx) for v, idx, _ in values])
        for cluster in clusters:
            members = [v for v in values if v[1] in cluster]
            if not members:
                continue
            papers = {m[2] for m in members if m[2]}
            for _, idx, _ in members:
                param_bank[idx]["cluster_size"] = len(members)
                param_bank[idx]["cluster_paper_diversity"] = len(papers)


def _select_parameter_line(step_text: str, param_bank: List[Dict[str, str]]) -> Dict[str, str] | None:
    if not param_bank:
        return None
    candidates = [item for item in param_bank if item.get("numeric_status") == "VALID_NORMALIZED"]
    if not candidates:
        candidates = [item for item in param_bank if item.get("numeric_status") == "RAW_NUMERIC_UNNORMALIZED"]
    if not candidates:
        return None
    step_lower = (step_text or "").lower()
    step_tokens = set(_tokenize(step_text))
    score_best = None
    best = None
    for item in candidates:
        sentence = item.get("sentence", "")
        relation = item.get("relation", "")
        value = item.get("value", "")
        blob = f"{relation} {value} {sentence}".lower()
        relevance = 0
        if any(k in step_lower for k in ("temperature", "thermo", "dsf", "tm", "incubat")):
            if re.search(r"°c|temperature|tm", blob):
                relevance += 3
        if any(k in step_lower for k in ("assay", "activity", "reaction", "substrate", "uplc", "hplc")):
            if re.search(r"min|hour|hr|nM|mM|µM|uM|µL|uL|mL|%|rpm", blob):
                relevance += 2
        if any(k in step_lower for k in ("pcr", "library", "variant", "clone", "transform", "electrop")):
            if re.search(r"10\\^\\d+|variants|colonies|wells|plates", blob):
                relevance += 2
        token_overlap = step_tokens.intersection(set(_tokenize(blob)))
        relevance += min(2, len(token_overlap) // 3)
        cluster_size = item.get("cluster_size", 1)
        paper_div = item.get("cluster_paper_diversity", 1)
        sec_priority = section_priority(item.get("section_type"))
        vec_score = item.get("vector_score", 0.0)
        score_tuple = (relevance, cluster_size, paper_div, sec_priority, vec_score)
        if score_best is None or score_tuple > score_best:
            score_best = score_tuple
            best = item
    return best if best and (score_best[0] if score_best else 0) > 0 else None


def inject_parameter_lines(answer: str, param_bank: List[Dict[str, str]]) -> str:
    sections = _split_sections(answer)
    exp = sections.get("Experimental Workflow")
    if not exp:
        return answer
    steps = _split_steps(exp)
    new_steps = []
    for step in steps:
        step_norm = step.replace("**", "")
        if "Parameters:" in step_norm and "No numeric parameters reported in sources" in step_norm:
            selected = _select_parameter_line(step_norm, param_bank)
            if selected:
                source_id = selected.get("source_id") or "?"
                sentence = selected.get("sentence") or ""
                value = selected.get("value") or ""
                relation = selected.get("relation") or "parameter"
                if sentence:
                    param_text = sentence.strip()
                elif value:
                    param_text = f"{relation}: {value}"
                else:
                    param_text = "No numeric parameters reported in sources."
                param_text = param_text.replace("\n", " ").strip()
                param_text = param_text[:200].rstrip()
                replacement = f"Parameters: {param_text} [S{source_id}]"
                step = re.sub(
                    r"(?:\\*\\*\\s*)?Parameters(?:\\s*\\*\\*)?:\\s*No numeric parameters reported in sources\\.",
                    replacement,
                    step,
                    flags=re.IGNORECASE,
                )
        new_steps.append(step)
    new_exp = "\n\n".join(new_steps)
    return answer.replace(exp, new_exp)

def validate_protocol(
    text: str,
    require_safety: bool,
    require_params_comp: bool,
    require_params_exp: bool,
) -> List[str]:
    issues: List[str] = []
    sections = _split_sections(text)
    if "Computational Workflow" not in sections or "Experimental Workflow" not in sections:
        issues.append("Missing required sections or incorrect section headers.")
        return issues

    comp_steps = _split_steps(sections["Computational Workflow"])
    exp_steps = _split_steps(sections["Experimental Workflow"])
    if len(comp_steps) < 3:
        issues.append("Computational Workflow must have at least 3 numbered steps.")
    if not (8 <= len(exp_steps) <= 12):
        issues.append("Experimental Workflow must have 8–12 numbered steps.")

    for idx, step in enumerate(comp_steps, start=1):
        step_body = re.sub(r"Citations:.*", "", step, flags=re.IGNORECASE | re.DOTALL).strip()
        if _sentence_count(step_body) < MIN_COMP_SENTENCES:
            issues.append(f"Computational step {idx} must have at least {MIN_COMP_SENTENCES} sentences.")
        if "Citations:" not in step:
            issues.append(f"Computational step {idx} missing citations line.")
        if require_params_comp and not _has_parameter(step_body):
            issues.append(f"Computational step {idx} must include a concrete parameter (temp/time/quantity).")
        if require_safety and "Safety:" in step and "Not specified in sources" in step:
            issues.append(f"Computational step {idx} needs a safety detail from sources (not 'Not specified').")

    required_labels = [
        "Goal:",
        "Reagents/Volumes:",
        "Instruments:",
        "Parameters:",
        "Actions:",
        "QC/Observations:",
        "Next Step Trigger:",
        "Safety:",
    ]
    for idx, step in enumerate(exp_steps, start=1):
        step_norm = step.replace("**", "")
        for label in required_labels:
            if label not in step_norm:
                issues.append(f"Experimental step {idx} missing label: {label}")
        if "Citations:" not in step_norm:
            issues.append(f"Experimental step {idx} missing citations line.")
        actions_match = re.search(
            r"Actions:\s*(.*?)(?:\n\s*-?\s*QC/Observations:|\Z)",
            step_norm,
            flags=re.DOTALL,
        )
        actions_text = actions_match.group(1).strip() if actions_match else ""
        sentence_count = _sentence_count(actions_text)
        if sentence_count < MIN_ACTION_SENTENCES or sentence_count > MAX_ACTION_SENTENCES:
            issues.append(
                f"Experimental step {idx} Actions must have {MIN_ACTION_SENTENCES}–{MAX_ACTION_SENTENCES} sentences."
            )
        if require_params_exp and not _has_parameter(step):
            issues.append(f"Experimental step {idx} must include a concrete parameter (temp/time/volume/etc.).")
        if "Safety:" in step_norm:
            if require_safety and "Not specified in sources" in step_norm:
                issues.append(f"Experimental step {idx} needs a safety detail from sources (not 'Not specified').")
            if (not require_safety) and ("Not specified in sources" not in step_norm):
                issues.append(f"Experimental step {idx} must state 'Safety: Not specified in sources.'")

    return issues


PROMPT_TEMPLATE = """You are drafting a protocol using the provided methodology sections and instrument specifications.

Question: {question}

Sources (cite as [S#] after relevant steps):
{source_index}

Experimental methodology excerpts:
{experimental_sections}

Computational methodology excerpts:
{computational_sections}

Results/outcome snippets:
{results_sections}

Full-paper KG evidence:
{full_kg_edges}

Quantitative parameters:
{parameter_edges}

Instrument capabilities:
{instrument_evidence}

Safety notes from sources (cite these verbatim where relevant):
{safety_notes}

Write Markdown with these strict rules:
1) Include **exactly two sections** in this order: `## Computational Workflow` then `## Experimental Workflow`.
2) Computational Workflow:
   - Provide **at least 3 numbered steps** focused only on design/simulation/data processing.
   - Each step must contain **at least two full sentences**, each ending in a period.
   - Include **concrete parameters** (temperature, time, quantity, threshold) only when they appear in sources; do **not** invent.
   - If a step has no numeric parameters in sources, write: `No numeric parameters reported in sources.` and cite [S?].
   - Include a **Design-to-Experiment Handoff** step that outputs: variant list, construct plan, assay design, plate layout, and acceptance criteria.
   - Include an **Experiment-to-Design Feedback** step explaining how assay results update next designs.
   - End each step with `Citations: [S#]` or `Citations: [S?]` if no direct source exists.
3) Experimental Workflow:
   - Provide **8–12 numbered steps** covering full wet-lab execution from setup to analytics and QC.
   - Each step must include labeled sub-bullets (use this order, every time): Goal, Reagents/Volumes, Instruments, Parameters, Actions, QC/Observations, Next Step Trigger, Safety (if applicable).
   - Actions must be **execution-ready**: 2–5 imperative sentences with concrete setup, mixing, incubation, and measurement details. End each sentence with a period.
   - Include controls, replicates, and acceptance criteria where relevant.
   - End each step with `Citations: [S#]` or `Citations: [S?]` if no direct source exists.
   - Use concrete numbers (volumes, temperatures, times, pH, speeds, plate formats) pulled from the excerpts/edges; avoid vague terms.
   - If no numeric parameters are available for a step, explicitly state `No numeric parameters reported in sources.` and cite [S?].
   - Cite instruments (bold names) and why they fit the step.
   - Safety: use **only** safety details explicitly mentioned in the Safety notes or excerpts, and cite them.
   - If no safety notes are provided, write `Safety: Not specified in sources.` and cite [S?].
4) Cite sources inline as [S#] wherever possible. Do NOT use tables.
"""


def run_protocol_agent_v2(question: str) -> str:
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
    os.environ.setdefault("RAYON_NUM_THREADS", "1")
    os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
    os.environ.setdefault("OMP_NUM_THREADS", "1")
    os.environ.setdefault("MKL_NUM_THREADS", "1")
    method_backend = get_method_backend()
    experimental = method_backend.section_search(question + " experimental workflow", top_k=6, section_type="experimental")
    computational = method_backend.section_search(question + " computational workflow", top_k=4, section_type="computational")
    results = method_backend.section_search(question + " activity results", top_k=3, section_type="results")
    safety_sections = method_backend.section_search(
        question + " safety hazard biosafety PPE waste disposal", top_k=3, section_type="experimental"
    )
    edges = gather_methodology_edges(question, limit=40)
    full_kg_evidence = gather_full_kg_evidence(question, limit=20)
    instrument_evidence = gather_instrument_evidence(question, experimental)
    citations: List[Dict[str, str | None]] = []
    seen: Dict[tuple, int] = {}

    def register_source(paper: str | None, pdf_file: str | None, text: str | None) -> int | None:
        if not (paper or pdf_file or text):
            return None
        label = paper or (Path(pdf_file).stem if pdf_file else None)
        doi = _extract_doi(text or "") or _doi_from_pdf(pdf_file)
        key = (label, pdf_file, doi)
        if key in seen:
            return seen[key]
        seen[key] = len(citations) + 1
        citations.append({"label": label, "doi": doi, "pdf_file": pdf_file})
        return seen[key]

    source_map: Dict[tuple, int] = {}
    for doc in experimental + computational + results + safety_sections:
        paper = doc.get("paper") or Path(doc.get("pdf_file") or "").stem
        pdf_file = doc.get("pdf_file")
        doi = _extract_doi(doc.get("text")) or _doi_from_pdf(pdf_file)
        source_id = register_source(paper, pdf_file, doc.get("text"))
        if source_id:
            source_map[(paper, pdf_file, doi)] = source_id
    for edge in edges:
        meta = edge.get("metadata", {})
        paper = meta.get("paper") or Path(meta.get("pdf_file") or "").stem
        pdf_file = meta.get("pdf_file")
        text = edge.get("text") or meta.get("sentence")
        doi = _extract_doi(text) or _doi_from_pdf(pdf_file)
        source_id = register_source(paper, pdf_file, text)
        if source_id:
            source_map[(paper, pdf_file, doi)] = source_id
    for ev in instrument_evidence:
        paper = Path(ev.get("pdf_file") or "").stem
        pdf_file = ev.get("pdf_file")
        text = ev.get("sentence")
        doi = _extract_doi(text) or _doi_from_pdf(pdf_file)
        source_id = register_source(paper, pdf_file, text)
        if source_id:
            source_map[(paper, pdf_file, doi)] = source_id
    for row in full_kg_evidence:
        meta = row.get("metadata", {}) if isinstance(row, dict) else {}
        paper = meta.get("paper") or meta.get("pdf_file")
        pdf_file = meta.get("pdf_file") or paper
        text = row.get("text") if isinstance(row, dict) else None
        doi = _extract_doi(text) or _doi_from_pdf(pdf_file)
        source_id = register_source(paper, pdf_file, text)
        if source_id:
            source_map[(paper, pdf_file, doi)] = source_id

    safety_notes = extract_safety_notes(experimental + computational + results + safety_sections, source_map)
    safety_text = "\n".join(safety_notes) if safety_notes else "- (No explicit safety notes found in sources.)"

    def source_index_text() -> str:
        lines = []
        for idx, entry in enumerate(citations, start=1):
            label = entry.get("label") or "Unknown source"
            doi = entry.get("doi")
            suffix = f" DOI:{doi}" if doi else ""
            lines.append(f"S{idx}: {label}{suffix}")
        return "\n".join(lines) if lines else "S1: No sources found."
    def format_source_id(source_id: int | None) -> str:
        return f"S{source_id}" if source_id else "S?"

    parameter_lines = []
    param_bank = []
    edge_records = []
    for edge in edges:
        meta = edge.get("metadata", {})
        meta = dict(meta)
        meta["vector_score"] = edge.get("score", 0.0)
        edge_records.append(meta)
    _, _, alias_map = discover_units_from_edges(edge_records)
    enriched_edges = [normalize_edge_numeric(meta, alias_map) for meta in edge_records]
    for edge in enriched_edges:
        source_id = register_source(edge.get("paper"), edge.get("pdf_file"), edge.get("sentence"))
        relation = edge.get("relation") or ""
        value = edge.get("value") or ""
        sentence = edge.get("sentence") or ""
        status = edge.get("numeric_status")
        normalized_unit = edge.get("normalized_unit")
        parameter_lines.append(
            f"- {relation}: {value} (status: {status}, unit: {normalized_unit}) (source: {format_source_id(source_id)})"
        )
        if edge.get("numeric_status") in {"VALID_NORMALIZED", "RAW_NUMERIC_UNNORMALIZED"}:
            param_bank.append(
                {
                    "relation": relation,
                    "value": value,
                    "sentence": sentence,
                    "source_id": source_id or "?",
                    "numeric_status": edge.get("numeric_status"),
                    "normalized_value": edge.get("normalized_value"),
                    "normalized_unit": edge.get("normalized_unit"),
                    "relation_category": edge.get("relation_category"),
                    "paper_id": edge.get("paper_id"),
                    "section_type": edge.get("section_type"),
                    "vector_score": edge.get("vector_score", 0.0),
                }
            )
    _annotate_consensus(param_bank)

    instrument_lines = []
    for ev in instrument_evidence:
        source_id = register_source(Path(ev.get("pdf_file") or "").stem, ev.get("pdf_file"), ev.get("sentence"))
        instrument_lines.append(
            f"- **{ev['instrument']}** ({ev['relation']}: {ev['value']}) – {format_source_id(source_id)} {ev['sentence']}"
        )

    full_kg_lines = []
    for row in full_kg_evidence:
        meta = row.get("metadata", {}) if isinstance(row, dict) else {}
        source_id = register_source(meta.get("paper"), meta.get("pdf_file"), row.get("text") if isinstance(row, dict) else None)
        source = meta.get("source") or meta.get("instrument") or "entity"
        relation = meta.get("relation") or "rel"
        target = meta.get("target") or meta.get("value") or ""
        full_kg_lines.append(f"- {source} {relation} {target} (source: {format_source_id(source_id)})")

    base_prompt = PROMPT_TEMPLATE.format(
        question=question,
        source_index=source_index_text(),
        experimental_sections=load_sections_for_prompt(experimental, source_map),
        computational_sections=load_sections_for_prompt(computational, source_map),
        results_sections=load_sections_for_prompt(results, source_map),
        full_kg_edges="\n".join(full_kg_lines),
        parameter_edges="\n".join(parameter_lines),
        instrument_evidence="\n".join(instrument_lines),
        safety_notes=safety_text,
    )
    answer = ""
    validation_issues: List[str] = []
    # Computational sections often lack explicit numeric parameters; avoid forcing hallucinated values.
    comp_numeric_evidence = False
    exp_numeric_evidence = _has_parameter(
        "\n".join([doc.get("text") or "" for doc in experimental]) + "\n" + "\n".join(parameter_lines)
    )
    for attempt in range(MAX_RETRIES + 1):
        prompt = base_prompt
        if validation_issues:
            prompt += "\n\nThe previous draft failed validation. Fix ALL issues below and regenerate the full protocol:\n"
            prompt += "\n".join(f"- {issue}" for issue in validation_issues)
            prompt += (
                "\n\nHard requirements:\n"
                "- Every Experimental step must include Actions with 2–5 full sentences (each ending with a period).\n"
                "- If a step lacks numeric parameters, include the sentence: `No numeric parameters reported in sources.`\n"
                "- If safety notes are absent, use `Safety: Not specified in sources.`\n"
                "- Do not omit any required labels.\n"
            )
        answer = local_llm.generate(prompt)
        answer = inject_parameter_lines(answer, param_bank)
        validation_issues = validate_protocol(
            answer,
            require_safety=bool(safety_notes),
            require_params_comp=comp_numeric_evidence,
            require_params_exp=exp_numeric_evidence,
        )
        if not validation_issues:
            break
    if citations:
        answer = answer.strip() + "\n\nSources:\n" + "\n".join(
            f"[S{i}] {entry.get('label')}{(' DOI:' + entry['doi']) if entry.get('doi') else ''}"
            for i, entry in enumerate(citations, start=1)
        )
    record_run(
        question,
        experimental,
        computational,
        results,
        edges,
        instrument_evidence,
        safety_notes,
        answer,
        validation_issues,
    )
    return answer


def record_run(
    question: str,
    experimental,
    computational,
    results,
    edges,
    instrument_evidence,
    safety_notes,
    answer: str,
    validation_issues: List[str],
) -> None:
    payload = {
        "question": question,
        "experimental_sections": experimental,
        "computational_sections": computational,
        "results_sections": results,
        "parameter_edges": edges,
        "instrument_evidence": instrument_evidence,
        "safety_notes": safety_notes,
        "answer": answer,
        "validation_issues": validation_issues,
    }
    existing = []
    for path in LOG_DIR.glob("run_*.json"):
        try:
            existing.append(int(path.stem.split("_")[-1]))
        except ValueError:
            continue
    next_idx = max(existing) + 1 if existing else 0
    out_path = LOG_DIR / f"run_{next_idx:05d}.json"
    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False))
