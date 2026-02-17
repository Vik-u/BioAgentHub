#!/usr/bin/env python3
"""
Biofoundry template agent (topic-agnostic) that performs Tasks A–D using only local templates:
- Task A: parse ModuleTemplate/Modules_library.md into structured JSON (no invented content).
- Task B: reverse-map each of the 4 protocol templates to ordered module IDs with cited sections.
- Task C: select three case studies via provided heuristics (organism/readout) and justify choices.
- Task D: emit human-readable protocols + machine-readable plans with TODOs for missing details.
- KG enrichment (default): pull evidence from instrument + methodology KGs to fill rationale/evidence
  (still no invented content; TODOs stay when evidence is missing).

Safety rails:
- Do NOT invent steps, reagents, instruments, timings, or module names beyond the source files.
- If a detail is missing, surface it as a TODO with the module/template section that lacks it.
"""

from __future__ import annotations

import argparse
import sys
import json
import os
import shutil
import re
import re as _re
import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))
from utils.output_paths import biofoundry_dir, logs_dir  # noqa: E402

OUTPUT_ROOT = biofoundry_dir()
MODULE_LIB = PROJECT_ROOT / "ModuleTemplate" / "Modules_library.md"
TEMPLATE_DIR = PROJECT_ROOT / "ModuleTemplate"
TEMPLATES = {
    "E.coli_EchoMS_protocol.md": TEMPLATE_DIR / "E.coli_EchoMS_protocol.md",
    "E.coli_plate_reader_protocol.md": TEMPLATE_DIR / "E.coli_plate_reader_protocol.md",
    "Yeast_EchoMS_protocol.md": TEMPLATE_DIR / "Yeast_EchoMS_protocol.md",
    "Yeast_plate_reader_protocol.md": TEMPLATE_DIR / "Yeast_plate_reader_protocol.md",
}


def _instrument_usage_enabled() -> bool:
    value = os.environ.get("BIOAGENT_USE_INSTRUMENTS", "")
    return value.strip().lower() in {"1", "true", "yes", "on"}
# Keep logs for traceability; outputs live under biofoundry_output
OUT_DIR = logs_dir() / "biofoundry" / "auto"

from utils.workspace_utils import list_topics  # noqa: E402

STOP_SUBSTRINGS = [
    "license",
    "cc-by",
    "biorxiv",
    "preprint",
    "copyright",
    "licenseavailable",
    "revised",
    "accepted",
    "received",
    "instrumentgraph",
    "research article",
    "very important paper",
    "cinematic",
]
BAD_SOURCES = {"1", "articles", "article", "research article", "cinematic", "very important paper", "unknown"}

# Topic-specific assay and metadata prompts to reduce generic TODO spam
TOPIC_ASSAY_CONFIGS = {
    "petase": {
        "PlateReader": [
            "Define PET/BHET/TPA plate assay chemistry (substrate concentration, temperature, incubation time).",
            "Specify absorbance/fluorescence wavelengths per substrate; include plate type and pathlength correction.",
        ],
        "EchoMS": [
            "Provide Echo-MS MRM panel for TPA/MHET/BHET with internal standard (e.g., d4-TPA) and calibration range.",
            "Upload worklists for Echo transfers (sample volume 60 µL split, carrier solvent, plate barcodes).",
        ],
    },
    "3hp_pand": {
        "EchoMS": [
            "Define MRM transitions for 3-hydroxypropionate and pathway intermediates; specify isotope-labeled standards.",
            "Calibration series (0–500 µM) and QC levels; sample prep (quench, dilution) and plate layout for Echo-MS.",
        ],
        "PlateReader": [
            "If optical assay is used, declare chromogenic/fluorogenic readout for 3-HP or coupled enzyme; include wavelengths.",
        ],
    },
    "retron": {
        "PlateReader": [
            "Retron screens are build/genotyping driven—define colony PCR + Sanger/NGS workflow for edited loci.",
            "If using growth/fluorescence readouts, specify reporter construct, excitation/emission, and control strains.",
        ],
        "EchoMS": [
            "If MS readout is desired, define target analyte and extraction; otherwise prefer genotyping assays.",
        ],
    },
}

MODULE_METADATA_FIELDS = {
    "module_1": [
        "Plasmid template ID/backbone",
        "Target gene and variant list",
        "Forward/reverse primer IDs and sequences",
        "PCR product concentration (ng/µL) after DpnI",
    ],
    "module_2": [
        "Assembly fragments/backbone IDs and antibiotic marker",
        "Insert/backbone molar ratios and total assembly volume",
        "Transformation strain and heat-shock parameters per plate layout",
    ],
    "module_3": [
        "Plate/colony map (source omnitray to destination deepwell)",
        "Pick criteria (colony size/fluorescence) and expected culture OD range",
    ],
    "module_4": [
        "Miniprep yield target (ng/µL) and QC (A260/280)",
        "Expression strain antibiotic selection and plate format",
    ],
    "module_5": [
        "Number of colonies per construct to pick; mapping to preculture wells",
        "Preculture media/antibiotic volumes and incubation duration",
    ],
    "module_6": [
        "Induction mode (IPTG vs autoinduction), concentration, temperature, duration",
        "Culture volume per well and shaking RPM/oxygenation constraints",
    ],
    "module_7": [
        "Assay substrate/reagent kit, excitation/emission or absorbance wavelengths",
        "Standard curve concentrations and controls; lysis buffer composition",
    ],
    "module_8": [
        "Target analytes for Echo-MS, internal standards, calibration levels",
        "Sample prep volumes, carrier solvent, plate/barcode mapping",
    ],
}

MODULE_OUTPUT_EXPECTATIONS = {
    "module_1": "DpnI-treated mutagenesis PCR amplicons with QC (ng/µL, melt curve).",
    "module_2": "Assembled plasmids and DH5α transformant plates with colony counts.",
    "module_3": "Overnight DH5α cultures in deepwell plates, OD600 ranges recorded.",
    "module_4": "Purified plasmid DNA with concentration/A260/280; plated BL21 transformants.",
    "module_5": "BL21 precultures ready for induction; plate IDs and colony source recorded.",
    "module_6": "Induced expression cultures with induction timestamps and temperatures logged.",
    "module_7": "Plate-reader assay results (raw spectra/OD, normalized activity, controls).",
    "module_8": "Echo-MS MRM results with calibration curves and QC sample performance.",
}

# Keyword hints for evidence search to avoid empty sections
KEYWORD_HINTS = {
    "petase": {
        "EchoMS": ["BHET MRM", "TPA MRM", "MHET calibration", "PETase EchoMS", "PET degradation LCMS"],
        "PlateReader": ["BHET assay absorbance", "TPA colorimetric", "PETase plate assay", "BHET substrate plate", "TPA fluorescence"],
    },
    "3hp_pand": {
        "EchoMS": ["PAND enzyme variant MRM", "BHET/TPA MRM", "Echo-MS metabolite quant", "enzyme engineering LCMS workflow", "His-tag protein expression MRM"],
        "PlateReader": ["enzyme variant plate assay", "optical assay PET/BHET", "fluorescence enzyme screening", "plate reader kinetic assay", "protein engineering plate assay"],
    },
    "retron": {
        "EchoMS": ["retron MS assay", "RT-Toprim LCMS", "msDNA LCMS"],
        "PlateReader": ["colony PCR retron", "retron Eco2 plaque assay", "genotyping retron", "OD600 retron defense", "reporter fluorescence retron"],
    },
}

def llm_expand_keywords(topic: str, readout: str) -> List[str]:
    """Use local LLM to propose extra search hints."""
    llm = get_local_llm()
    prompt = (
        f"Provide 25 short search phrases (max 4 words each) for finding experimental/assay evidence about topic '{topic}' "
        f"with readout '{readout}'. Focus on actionable lab terms (substrates, MRMs, wavelengths, colony PCR, plaque assays, "
        f"expression/induction details). Return as a comma-separated list, no prose."
    )
    try:
        resp = llm.generate(prompt)
    except Exception:
        return []
    hints = []
    for part in resp.split(","):
        hint = part.strip()
        if 0 < len(hint) <= 40:
            hints.append(hint)
    return hints


def score_ev(ev: Dict[str, object]) -> float:
    """Lightweight ranking: prefer assay/measurement relations, then shorter values."""
    rel = str(ev.get("relation", "")).lower()
    val = str(ev.get("value", ""))
    score = 0.0
    if any(k in rel for k in ("mrm", "assay", "wavelength", "substrate", "pcr", "plaque", "induction")):
        score += 1.0
    score += max(0.0, 1.0 - len(val) / 200.0)
    return score

# Topic aliases to map pand ↔ 3hp_pand, etc.
TOPIC_ALIASES = {
    "pand": ["pand", "3hp_pand"],
    "3hp_pand": ["3hp_pand", "pand"],
}

# Lazy imports for KG backends (avoids heavy load if disabled)
def get_method_backend():
    from services.methodology_retrieval import get_backend as _get_backend

    return _get_backend()


def get_local_llm():
    from services import local_llm

    return local_llm


# Keywords for assay-centric filtering
ASSAY_KEYS = ["assay", "substrate", "absorbance", "fluor", "fluorescence", "wavelength", "excitation", "emission", "m/z", "mrm", "volume", "µl", "ul", "temperature", "centrifuge", "g", "rpm", "incubation", "plate", "96", "384"]
KEYWORD_TAGS = ["assay", "analyte", "mrm", "wavelength", "pcr", "plaque", "control", "negative", "instrument", "echo", "plate reader", "ms", "lc-ms", "gc-ms"]
ASSAY_MODULES = {"module_7", "module_8", "module_11", "module_12"}
ALL_MODULE_IDS = [f"module_{idx}" for idx in range(1, 13)]
CORE_REQUIRED_MODULES = {"module_1", "module_2", "module_3", "module_4", "module_5", "module_6"}
MODULE_READOUT_REQUIREMENTS = {
    "module_7": "PlateReader",
    "module_8": "EchoMS",
    "module_11": "PlateReader",
    "module_12": "EchoMS",
}
MODULE_ORGANISM_REQUIREMENTS = {
    "module_9": "Yeast",
    "module_10": "Yeast",
}
MODULE_HINTS = {
    "module_1": ["mutagenesis", "pcr", "dpni", "primer"],
    "module_2": ["assembly", "hifi", "gibson", "transformation", "dh5a"],
    "module_3": ["colony", "picking", "deepwell", "culture"],
    "module_4": ["miniprep", "plasmid", "bl21"],
    "module_5": ["preculture", "inoculation", "expression"],
    "module_6": ["induction", "iptg", "autoinduction", "shaking"],
    "module_7": ["plate reader", "absorbance", "fluorescence", "assay"],
    "module_8": ["echo", "ms", "mrm", "lc-ms", "mass spec"],
    "module_9": ["yeast", "transformation"],
    "module_10": ["fermentation", "bioreactor", "do", "aeration"],
}
STOP_TERMS = {
    "the", "and", "for", "with", "from", "into", "using", "use", "via",
    "module", "subprocess", "protocol", "workflow", "step", "steps",
    "plate", "plates", "well", "wells", "sample", "samples",
}


def _tokenize_terms(text: str) -> List[str]:
    terms: List[str] = []
    for token in re.split(r"[^a-zA-Z0-9\-\+]+", text.lower()):
        token = token.strip()
        if not token or token in STOP_TERMS or len(token) < 3:
            continue
        terms.append(token)
    return terms


def module_focus_terms(mod: "ModuleDef") -> List[str]:
    terms: List[str] = []
    terms.extend(_tokenize_terms(mod.module_name))
    for sp in mod.subprocess:
        for bucket in (sp.objective, sp.actions, sp.materials, sp.instruments, sp.parameters):
            for item in bucket:
                terms.extend(_tokenize_terms(item))
    terms.extend([t.lower() for t in MODULE_HINTS.get(mod.module_id, [])])
    # Keep top unique terms, biasing toward specific hints.
    seen = set()
    ordered: List[str] = []
    for term in terms:
        if term in seen:
            continue
        seen.add(term)
        ordered.append(term)
        if len(ordered) >= 18:
            break
    return ordered


def module_query_phrases(mod: "ModuleDef", topic: str | None, readout: str | None) -> List[str]:
    phrases: List[str] = []
    base = mod.module_name
    if topic:
        phrases.append(f"{topic} {base}")
        phrases.append(f"{topic} {base} protocol")
    else:
        phrases.append(base)
    for hint in MODULE_HINTS.get(mod.module_id, []):
        if topic:
            phrases.append(f"{topic} {hint}")
        phrases.append(hint)
    if mod.module_id in ASSAY_MODULES and topic:
        readout_key = "EchoMS" if (readout or "").lower().find("echo") >= 0 else "PlateReader"
        if topic.lower() in KEYWORD_HINTS:
            phrases.extend(KEYWORD_HINTS[topic.lower()].get(readout_key, []))
    # Deduplicate while preserving order.
    seen = set()
    ordered: List[str] = []
    for phrase in phrases:
        phrase = phrase.strip()
        if not phrase or phrase in seen:
            continue
        seen.add(phrase)
        ordered.append(phrase)
        if len(ordered) >= 18:
            break
    return ordered


def _matches_terms(text: str, terms: List[str]) -> bool:
    if not terms:
        return True
    lower = text.lower()
    return any(term in lower for term in terms)


def normalize_token(value: str) -> str:
    return _re.sub(r"[^a-z0-9]+", "", value.lower())


def load_instrument_inventory() -> List[str]:
    if not _instrument_usage_enabled():
        return []
    inv_path = PROJECT_ROOT / "InstrumentGraph" / "inventory.json"
    if not inv_path.exists():
        return []
    try:
        payload = json.loads(inv_path.read_text())
    except Exception:
        return []
    if isinstance(payload, dict):
        items = payload.get("instruments", payload.get("inventory", payload.get("items", [])))
    else:
        items = payload
    if not isinstance(items, list):
        return []
    return [str(item) for item in items if str(item).strip()]


def instrument_available(required: str, inventory: List[str]) -> bool:
    if not required or not inventory:
        return True
    # LIMITATION: instrument availability uses substring matching; aliases may be missed.
    req_norm = normalize_token(required)
    for entry in inventory:
        entry_norm = normalize_token(entry)
        if req_norm in entry_norm or entry_norm in req_norm:
            return True
    return False


def required_instruments_for_module(mod: "ModuleDef") -> List[str]:
    instruments: List[str] = []
    for sp in mod.subprocess:
        for inst in sp.instruments:
            inst = inst.strip()
            if inst and inst not in instruments:
                instruments.append(inst)
    return instruments


def canonical_source_id(source: str) -> str:
    src = str(source or "").strip()
    lower = src.lower()
    doi_match = _re.search(r"10\.\d{4,9}/\S+", lower)
    if doi_match:
        return f"doi:{doi_match.group(0).rstrip(').,;')}"
    pmid_match = _re.search(r"\bpmid\s*[:=]?\s*(\d+)\b", lower)
    if pmid_match:
        return f"pmid:{pmid_match.group(1)}"
    if "europepmc" in lower:
        return f"europepmc:{lower.split('/')[-1]}"
    if src.endswith(".pdf"):
        stem = Path(src).stem
        return f"file:{stem}"
    return f"text:{normalize_token(src)[:48]}"


def hash_text(text: str) -> str:
    return hashlib.md5(text.encode("utf-8", errors="ignore")).hexdigest()[:12]


@dataclass
class Citation:
    id: int
    source_id: str
    source: str
    title: str
    section: str


class CitationRegistry:
    def __init__(self) -> None:
        self._citations: Dict[str, Citation] = {}
        self._order: List[str] = []

    def add(self, source: str, title: str = "", section: str = "") -> Citation:
        source = str(source or "").strip()
        if not source:
            source = "unknown"
        source_id = canonical_source_id(source)
        key = f"{source_id}|{title}|{section}"
        if key in self._citations:
            return self._citations[key]
        citation = Citation(
            id=len(self._order) + 1,
            source_id=source_id,
            source=source,
            title=title or "",
            section=section or "",
        )
        self._citations[key] = citation
        self._order.append(key)
        return citation

    def list(self) -> List[Dict[str, object]]:
        return [
            {
                "id": self._citations[key].id,
                "source_id": self._citations[key].source_id,
                "source": self._citations[key].source,
                "title": self._citations[key].title,
                "section": self._citations[key].section,
            }
            for key in self._order
        ]


def citation_tag(citation_ids: Sequence[int]) -> str:
    tags = [f"[{cid}]" for cid in citation_ids if cid > 0]
    return "".join(tags)


def clean_evidence_list(evidence: List[Dict[str, object]], max_len: int = 240) -> List[Dict[str, object]]:
    """Filter noisy evidence, trim long values, and deduplicate."""
    cleaned: List[Dict[str, object]] = []
    seen = set()
    for ev in evidence:
        rel = str(ev.get("relation", ""))
        raw_val = str(ev.get("value", ""))
        val = raw_val.replace("\n", " ").strip()
        src = str(ev.get("source", ""))
        if not val:
            continue
        lower_val = val.lower()
        lower_src = src.lower()
        if any(stop in lower_val for stop in STOP_SUBSTRINGS):
            continue
        if any(stop in lower_src for stop in STOP_SUBSTRINGS):
            continue
        if lower_src in BAD_SOURCES or lower_src.strip().isdigit():
            continue
        if "..." in val:
            continue
        if len(raw_val) > max_len:
            continue
        if _re.search(r"\b\d{3,}\s*l\b", lower_val):
            continue
        if rel.lower() in {"concentration", "volume"} and _re.fullmatch(r"\d+\s*(m|mm|mM|M|l|L|%)", val, flags=_re.IGNORECASE):
            continue
        if "instrument" in lower_val and "use_case" in lower_val:
            continue
        key = (rel, val, src)
        if key in seen:
            continue
        seen.add(key)
        ev_clean = dict(ev)
        ev_clean["value"] = val
        ev_clean["relation"] = rel
        ev_clean["source"] = src
        cleaned.append(ev_clean)
    return cleaned


@dataclass
class Subprocess:
    name: str
    objective: List[str] = field(default_factory=list)
    description: List[str] = field(default_factory=list)
    actions: List[str] = field(default_factory=list)
    labware: List[str] = field(default_factory=list)
    instruments: List[str] = field(default_factory=list)
    materials: List[str] = field(default_factory=list)
    parameters: List[str] = field(default_factory=list)


@dataclass
class ModuleDef:
    module_id: str
    module_name: str
    subprocess: List[Subprocess]
    purpose: str
    inputs: List[str]
    outputs: List[str]
    constraints: List[str]
    dependencies: List[str]
    source_file: str


def parse_modules_library(path: Path) -> List[ModuleDef]:
    """Parse Modules_library.md without inventing content."""
    lines = path.read_text().splitlines()
    modules: List[ModuleDef] = []
    current_module: Dict[str, object] | None = None
    current_subprocess: Subprocess | None = None
    current_field: str | None = None

    def flush_subprocess() -> None:
        nonlocal current_subprocess
        if current_module is None or current_subprocess is None:
            return
        current_module["subprocess"].append(current_subprocess)
        current_subprocess = None

    def flush_module() -> None:
        nonlocal current_module
        if current_module is None:
            return
        flush_subprocess()
        modules.append(
            ModuleDef(
                module_id=current_module["module_id"],
                module_name=current_module["module_name"],
                subprocess=current_module["subprocess"],
                purpose=current_module["purpose"],
                inputs=current_module["inputs"],
                outputs=current_module["outputs"],
                constraints=current_module["constraints"],
                dependencies=current_module["dependencies"],
                source_file=current_module["source_file"],
            )
        )
        current_module = None

    module_pattern = re.compile(r"^##\s+Module\s+(\d+)\s+[—-]\s+(.*)")
    subprocess_pattern = re.compile(r"^###\s+Subprocess\s+[\d\.]+\s*:\s*(.*)")

    for raw_line in lines:
        line = raw_line.rstrip()
        module_match = module_pattern.match(line)
        if module_match:
            flush_module()
            module_num, module_name = module_match.group(1), module_match.group(2).strip()
            current_module = {
                "module_id": f"module_{module_num}",
                "module_name": module_name,
                "subprocess": [],
                "purpose": "",
                "inputs": [],
                "outputs": [],
                "constraints": [],
                "dependencies": [],
                "source_file": f"Modules_library.md#Module {module_num} — {module_name}",
            }
            current_subprocess = None
            current_field = None
            continue

        subprocess_match = subprocess_pattern.match(line)
        if subprocess_match and current_module is not None:
            flush_subprocess()
            current_subprocess = Subprocess(name=subprocess_match.group(1).strip())
            current_field = None
            continue

        if line.startswith("- **") and "**" in line[3:]:
            label = line.split("**")[1].strip(":").lower()
            current_field = label
            if current_subprocess is None and current_module is not None:
                current_subprocess = Subprocess(name=current_module["module_name"])
            continue

        if line.startswith("  - ") and current_subprocess is not None and current_field:
            value = line[4:].strip()
            if hasattr(current_subprocess, current_field):
                getattr(current_subprocess, current_field).append(value)
            continue

    flush_module()

    enriched: List[ModuleDef] = []
    for mod in modules:
        inputs: List[str] = []
        constraints: List[str] = []
        purpose = ""
        for sp in mod.subprocess:
            if sp.objective and not purpose:
                purpose = "; ".join(sp.objective)
            inputs.extend(sp.materials)
            constraints.extend(sp.parameters)
        enriched.append(
            ModuleDef(
                module_id=mod.module_id,
                module_name=mod.module_name,
                subprocess=mod.subprocess,
                purpose=purpose,
                inputs=inputs,
                outputs=mod.outputs,
                constraints=constraints,
                dependencies=mod.dependencies,
                source_file=mod.source_file,
            )
        )
    return enriched


def parse_template_modules(path: Path) -> Tuple[List[str], List[str]]:
    """Return ordered module IDs and notes citing where they were found."""
    lines = path.read_text().splitlines()
    module_pattern = re.compile(r"^##\s+Module\s+(\d+)\s+[—-]\s+")
    ordered: List[str] = []
    notes: List[str] = []
    for idx, raw in enumerate(lines, start=1):
        match = module_pattern.match(raw)
        if match:
            module_id = f"module_{match.group(1)}"
            ordered.append(module_id)
            notes.append(f"Line {idx}: contains Module {match.group(1)} heading")
    return ordered, notes


def save_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False))


def save_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)

def cleanup_old_runs(output_root: Path, keep: int = 2) -> None:
    runs_dir = output_root / "runs"
    if not runs_dir.exists():
        return
    run_dirs = sorted([d for d in runs_dir.iterdir() if d.is_dir()])
    excess = len(run_dirs) - keep
    for d in run_dirs[:max(0, excess)]:
        shutil.rmtree(d, ignore_errors=True)


def emit_task_a(modules: List[ModuleDef]) -> None:
    payload = []
    for mod in modules:
        payload.append(
            {
                "module_id": mod.module_id,
                "module_name": mod.module_name,
                "subprocess": [
                    {
                        "name": sp.name,
                        "objective": sp.objective,
                        "description": sp.description,
                        "actions": sp.actions,
                        "labware": sp.labware,
                        "instruments": sp.instruments,
                        "materials": sp.materials,
                        "parameters": sp.parameters,
                    }
                    for sp in mod.subprocess
                ],
                "purpose": mod.purpose,
                "inputs": mod.inputs,
                "outputs": mod.outputs,
                "constraints": mod.constraints,
                "dependencies": mod.dependencies,
                "source_file": mod.source_file,
            }
        )
    save_json(OUT_DIR / "modules.generated.json", payload)


def emit_task_b(template_map: Dict[str, Dict[str, object]]) -> None:
    lines = ["| template_name | organism | readout | ordered_modules | notes |", "|---|---|---|---|---|"]
    for name, meta in template_map.items():
        ordered = "[" + ", ".join(meta["ordered_modules"]) + "]"
        notes = "; ".join(meta["notes"])
        lines.append(f"| {name} | {meta['organism']} | {meta['readout']} | {ordered} | {notes} |")
    save_text(OUT_DIR / "template_mapping.generated.md", "\n".join(lines) + "\n")


def build_template_map(modules: List[ModuleDef]) -> Dict[str, Dict[str, object]]:
    mapping: Dict[str, Dict[str, object]] = {}
    for name, path in TEMPLATES.items():
        ordered, notes = parse_template_modules(path)
        mapping[name] = {
            "organism": "E.coli" if "E.coli" in name else "Yeast",
            "readout": "EchoMS" if "EchoMS" in name else "PlateReader",
            "ordered_modules": ordered,
            "notes": notes,
        }
    return mapping


def discover_topics() -> List[str]:
    """Discover topics from canonical workspace mapping."""
    return list_topics()


def score_query(backend, query: str, top_k: int = 6) -> Tuple[float, List[str]]:
    """Average score and sources from methodology KG."""
    scores: List[float] = []
    sources: List[str] = []
    try:
        docs = backend.section_search(query, top_k=top_k)
    except Exception:
        docs = []
    for doc in docs:
        if isinstance(doc.get("score", 0.0), (int, float)):
            scores.append(float(doc.get("score", 0.0)))
        src = doc.get("paper") or doc.get("pdf_file") or "unknown"
        sources.append(str(src))
    try:
        edges = backend.edge_search(query, top_k=max(3, top_k))
    except Exception:
        edges = []
    for edge in edges:
        meta = edge.get("metadata", edge)
        if isinstance(edge.get("score", 0.0), (int, float)):
            scores.append(float(edge.get("score", 0.0)))
        src = meta.get("paper") or meta.get("pdf_file") or "unknown"
        sources.append(str(src))
    if not scores:
        return 0.0, []
    avg = sum(scores) / len(scores)
    # Keep the first few sources for concise rationale.
    deduped: List[str] = []
    seen = set()
    for src in sources:
        if src in seen:
            continue
        seen.add(src)
        deduped.append(src)
        if len(deduped) >= 4:
            break
    return avg, deduped


def score_query_details(backend, query: str, top_k: int = 6) -> Dict[str, object]:
    """Return average score, top score, and sources for a query."""
    avg_score, sources = score_query(backend, query, top_k=top_k)
    top_score = 0.0
    try:
        docs = backend.section_search(query, top_k=top_k)
    except Exception:
        docs = []
    for doc in docs:
        if isinstance(doc.get("score", 0.0), (int, float)):
            top_score = max(top_score, float(doc.get("score", 0.0)))
    try:
        edges = backend.edge_search(query, top_k=max(3, top_k))
    except Exception:
        edges = []
    for edge in edges:
        if isinstance(edge.get("score", 0.0), (int, float)):
            top_score = max(top_score, float(edge.get("score", 0.0)))
    return {"avg_score": avg_score, "top_score": top_score, "sources": sources}


def select_template_for_topic(topic: str, template_map: Dict[str, Dict[str, object]], backend, readout_bias: int = 0) -> Dict[str, object]:
    """Choose organism/readout via KG evidence; fall back to highest score."""
    organisms = ["E.coli", "Yeast"]
    readouts = ["PlateReader", "EchoMS"]
    org_scores = {}
    readout_scores = {}

    for org in organisms:
        q = f"{topic} {org} expression screening"
        score, src = score_query(backend, q, top_k=6)
        org_scores[org] = {"score": score, "sources": src}
    for ro in readouts:
        q = f"{topic} {ro} assay protocol"
        score, src = score_query(backend, q, top_k=6)
        # optional bias toward EchoMS when chemistry is implied
        if ro == "EchoMS":
            score += readout_bias
        readout_scores[ro] = {"score": score, "sources": src}

    chosen_org = max(org_scores.items(), key=lambda kv: kv[1]["score"])[0]
    chosen_readout = max(readout_scores.items(), key=lambda kv: kv[1]["score"])[0]

    template_key = None
    for name, meta in template_map.items():
        if meta["organism"] == chosen_org and meta["readout"] == chosen_readout:
            template_key = name
            break
    if not template_key:
        # Fallback: choose first matching organism
        for name, meta in template_map.items():
            if meta["organism"] == chosen_org:
                template_key = name
                break
    if not template_key:
        template_key = next(iter(template_map.keys()))

    template_meta = template_map[template_key]
    title = f"{topic} ({chosen_org} + {chosen_readout})"
    case = {
        "case_study_title": title,
        "topic": topic,
        "organism": chosen_org,
        "readout": chosen_readout,
        "template": template_key,
        "ordered_modules": template_meta["ordered_modules"],
        "selection_evidence": {
            "organism": org_scores,
            "readout": readout_scores,
        },
    }
    return case


def build_case_studies(template_map: Dict[str, Dict[str, object]], topics: List[str]) -> List[Dict[str, object]]:
    backend = get_method_backend()
    cases = []
    for topic in topics:
        cases.append(select_template_for_topic(topic, template_map, backend, readout_bias=0))
    return cases


def module_todos(mod: ModuleDef, topic: str | None, readout: str | None) -> List[str]:
    todos: List[str] = []
    topic_key = (topic or "").lower()
    readout_key = (readout or "").replace(" ", "").lower()

    # Core build gaps
    if mod.module_id == "module_1":
        todos.append("Provide plasmid/backbone identifiers, target variants, and mutagenic primer sequences.")
        todos.append("Record DpnI digest QC (concentration, melt curve) for each well.")
    if mod.module_id == "module_2":
        todos.append("List assembly fragment IDs, antibiotic markers, and expected colony counts per construct.")
    if mod.module_id == "module_3":
        todos.append("Define colony picking criteria and barcode map from omnitray to deepwell plate.")
    if mod.module_id == "module_4":
        todos.append("Specify antibiotics for BL21 transformation and miniprep yield/QC targets.")
    if mod.module_id == "module_5":
        todos.append("Set colonies-per-construct and preculture volume/timing; map source colonies to wells.")
    if mod.module_id == "module_6":
        todos.append("Choose induction mode (IPTG vs autoinduction) with temperature, concentration, and duration.")

    # Assay/readout-specific gaps
    if mod.module_id in {"module_7", "module_8", "module_11", "module_12"}:
        topic_assays = TOPIC_ASSAY_CONFIGS.get(topic_key, {})
        topic_readout = "EchoMS" if "echo" in readout_key else "PlateReader"
        todos.extend(topic_assays.get(topic_readout, []))
        if mod.module_id in {"module_7"}:
            todos.append("Confirm substrate, wavelength, pathlength correction, and control wells for plate reader run.")
        if mod.module_id in {"module_8"}:
            todos.append("Define MS method (MRM transitions, internal standards, calibration curve, blanks/QCs).")

    # Yeast-specific reminders
    if mod.module_id == "module_9":
        todos.append("Add yeast transformation worklist and heat-shock timing/temperature.")
    if mod.module_id == "module_10":
        todos.append("Provide fermentation media/temperature/DO setpoints beyond 24 h.")

    # Deduplicate while preserving order
    seen = set()
    deduped: List[str] = []
    for item in todos:
        if item in seen:
            continue
        seen.add(item)
        deduped.append(item)
    return deduped


def case_parameters(case_modules: List[ModuleDef]) -> List[str]:
    params: List[str] = []
    for mod in case_modules:
        if mod.module_id == "module_1":
            params.append("Plasmid template/backbone IDs, target variants, mutagenic primer sequences.")
        if mod.module_id == "module_2":
            params.append("Assembly fragment IDs, molar ratios, antibiotic markers for transformation.")
        if mod.module_id == "module_6":
            params.append("Induction mode (IPTG vs autoinduction), concentration, temperature, duration.")
        if mod.module_id in {"module_7", "module_8", "module_11", "module_12"}:
            params.append("Assay substrates/readout settings (substrate, wavelength or MRM, standards, controls).")
        if mod.module_id == "module_9":
            params.append("Yeast strain, transformation worklist, and heat-shock parameters.")
    return sorted(set(params))


def build_module_lookup(modules: List[ModuleDef]) -> Dict[str, ModuleDef]:
    return {m.module_id: m for m in modules}


def render_protocol(case: Dict[str, object], module_lookup: Dict[str, ModuleDef]) -> str:
    lines: List[str] = []
    lines.append(f"# {case['case_study_title']}")
    lines.append(f"Closest template used: ModuleTemplate/{case['template']}")
    lines.append("")
    for idx, module_id in enumerate(case["ordered_modules"], start=1):
        mod = module_lookup[module_id]
        lines.append(f"{idx}. [{mod.module_id}] {mod.module_name}")
        lines.append(f"   - Purpose: {mod.purpose or 'Not specified in source; see Objective section.'}")
        for sp in mod.subprocess:
            lines.append(f"   - Subprocess: {sp.name}")
            if sp.objective:
                lines.append(f"     * Objective: {'; '.join(sp.objective)}")
            if sp.description:
                lines.append(f"     * Description: {'; '.join(sp.description)}")
            if sp.actions:
                lines.append(f"     * Actions: {'; '.join(sp.actions)}")
            if sp.labware:
                lines.append(f"     * Labware: {', '.join(sp.labware)}")
            if sp.instruments:
                lines.append(f"     * Instruments: {', '.join(sp.instruments)}")
            if sp.materials:
                lines.append(f"     * Inputs/Materials: {', '.join(sp.materials)}")
            if sp.parameters:
                lines.append(f"     * Parameters: {', '.join(sp.parameters)}")
        metadata_fields = MODULE_METADATA_FIELDS.get(mod.module_id, [])
        if metadata_fields:
            lines.append(f"   - Metadata to provide: {', '.join(metadata_fields)}")
        expected_output = MODULE_OUTPUT_EXPECTATIONS.get(mod.module_id)
        if expected_output:
            lines.append(f"   - Expected output: {expected_output}")
        module_specific_todos = module_todos(mod, case.get("topic"), case.get("readout"))
        if module_specific_todos:
            for todo in module_specific_todos:
                lines.append(f"   - Open item: {todo}")
    lines.append("")
    lines.append("Note: All content is directly sourced from ModuleTemplate/Modules_library.md. Missing items are flagged as TODOs.")
    return "\n".join(lines)


def render_plan(case: Dict[str, object], module_lookup: Dict[str, ModuleDef]) -> Dict[str, object]:
    modules = [module_lookup[mid] for mid in case["ordered_modules"]]
    todos: List[str] = []
    for mod in modules:
        todos.extend(module_todos(mod, case.get("topic"), case.get("readout")))
    plan = {
        "case_study_title": case["case_study_title"],
        "organism": case["organism"],
        "readout": case["readout"],
        "closest_template_used": f"ModuleTemplate/{case['template']}",
        "ordered_modules": case["ordered_modules"],
        "parameters_needed": case_parameters(modules),
        "TODOs": sorted(set(todos)),
        "assumptions": [
            "Module order follows template; no reordering applied.",
            "Organism/readout chosen via methodology KG evidence (vector search scores).",
        ],
        "selection_evidence": case.get("selection_evidence", {}),
    }
    return plan


def gather_instrument_evidence(mod: ModuleDef, backend) -> List[Dict[str, object]]:
    """Collect instrument evidence using instrument names present in subprocess metadata."""
    if backend is None:
        return []
    seen = set()
    ev: List[Dict[str, object]] = []
    for sp in mod.subprocess:
        for instrument in sp.instruments:
            instrument = instrument.strip()
            if not instrument:
                continue
            # Graph edges for the instrument
            try:
                for row in backend.graph_query(instrument, top_k=5):
                    key = (row["instrument"], row["relation"], row["value"])
                    if key in seen:
                        continue
                    seen.add(key)
                    ev.append(
                        {
                            "module_id": mod.module_id,
                            "type": "instrument_edge",
                            "instrument": row["instrument"],
                            "relation": row["relation"],
                            "value": row["value"],
                            "source": row["pdf_file"],
                        }
                    )
            except Exception:
                pass
            # Vector search for additional snippets
            try:
                for row in backend.vector_search(instrument, top_k=2):
                    meta = row["metadata"]
                    key = (meta["instrument"], meta["relation"], meta["value"])
                    if key in seen:
                        continue
                    seen.add(key)
                    ev.append(
                        {
                            "module_id": mod.module_id,
                            "type": "instrument_vector",
                            "instrument": meta["instrument"],
                            "relation": meta["relation"],
                            "value": meta["value"],
                            "source": meta["pdf_file"],
                        }
                    )
            except Exception:
                pass
    return ev


def gather_method_evidence(
    mod: ModuleDef,
    backend,
    top_k: int = 5,
    topic: str | None = None,
    readout: str | None = None,
) -> List[Dict[str, object]]:
    """Collect methodology edges; try topic-scoped first, then fall back."""
    if backend is None:
        return []
    ev: List[Dict[str, object]] = []
    topic_key = (topic or "").lower()
    aliases = TOPIC_ALIASES.get(topic_key, [topic_key] if topic_key else [])
    queries = module_query_phrases(mod, topic, readout)
    queries.extend(llm_expand_keywords(topic_key or mod.module_name, "methodology"))
    module_terms = module_focus_terms(mod)
    strict_matches: List[Dict[str, object]] = []
    relaxed_matches: List[Dict[str, object]] = []

    def accept(meta_src: str) -> bool:
        if "instrumentgraph" in meta_src:
            return False
        if not aliases:
            return True
        return any(f"data/{al}" in meta_src for al in aliases)

    # Topic-scoped pass
    for q in queries:
        try:
            edges = backend.edge_search(q, top_k=top_k)
        except Exception:
            continue
        for edge in edges:
            meta = edge["metadata"] if "metadata" in edge else edge
            src = str(meta.get("paper", meta.get("pdf_file", ""))).lower()
            if aliases and not accept(src):
                continue
            payload = {
                "module_id": mod.module_id,
                "type": "methodology_edge",
                "relation": meta.get("relation", ""),
                "value": meta.get("value", ""),
                "source": meta.get("paper", meta.get("pdf_file", "")),
            }
            text = f"{payload['relation']} {payload['value']}"
            if _matches_terms(text, module_terms):
                strict_matches.append(payload)
            else:
                relaxed_matches.append(payload)
    # Fallback: if still empty, allow any source (still filtered for junk)
    if not strict_matches:
        for q in queries:
            try:
                edges = backend.edge_search(q, top_k=top_k)
            except Exception:
                continue
            for edge in edges:
                meta = edge["metadata"] if "metadata" in edge else edge
                src = str(meta.get("paper", meta.get("pdf_file", ""))).lower()
                if "instrumentgraph" in src:
                    continue
                payload = {
                    "module_id": mod.module_id,
                    "type": "methodology_edge",
                    "relation": meta.get("relation", ""),
                    "value": meta.get("value", ""),
                    "source": meta.get("paper", meta.get("pdf_file", "")),
                }
                text = f"{payload['relation']} {payload['value']}"
                if _matches_terms(text, module_terms):
                    strict_matches.append(payload)
                else:
                    relaxed_matches.append(payload)

    ev = strict_matches if strict_matches else relaxed_matches
    ev = clean_evidence_list(ev)
    ev = sorted(ev, key=score_ev, reverse=True)[:10]
    return ev


def gather_section_evidence(
    mod: ModuleDef,
    backend,
    queries: Sequence[str],
    top_k: int,
    seen_keys: set,
) -> List[Dict[str, object]]:
    evidence: List[Dict[str, object]] = []
    module_terms = module_focus_terms(mod)
    for query in queries:
        try:
            docs = backend.section_search(query, top_k=top_k)
        except Exception:
            continue
        for doc in docs:
            heading = doc.get("heading", "")
            text = doc.get("text", "")
            source = doc.get("paper") or doc.get("pdf_file") or ""
            key = ("section", str(source), heading, hash_text(text[:200]))
            if key in seen_keys:
                continue
            if not _matches_terms(f"{heading} {text}", module_terms):
                continue
            seen_keys.add(key)
            evidence.append(
                {
                    "type": "methodology_section",
                    "score": doc.get("score", 0.0),
                    "heading": heading,
                    "text": text[:320],
                    "source": source,
                    "title": doc.get("title", ""),
                }
            )
    return evidence


def gather_edge_evidence(
    mod: ModuleDef,
    backend,
    queries: Sequence[str],
    top_k: int,
    seen_keys: set,
) -> List[Dict[str, object]]:
    evidence: List[Dict[str, object]] = []
    module_terms = module_focus_terms(mod)
    for query in queries:
        try:
            edges = backend.edge_search(query, top_k=top_k)
        except Exception:
            continue
        for edge in edges:
            meta = edge.get("metadata", edge)
            rel = str(meta.get("relation", ""))
            val = str(meta.get("value", ""))
            source = meta.get("paper") or meta.get("pdf_file") or ""
            key = ("edge", rel, val, str(source))
            if key in seen_keys:
                continue
            if not _matches_terms(f"{rel} {val}", module_terms):
                continue
            seen_keys.add(key)
            evidence.append(
                {
                    "type": "methodology_edge",
                    "score": edge.get("score", 0.0),
                    "relation": rel,
                    "value": val,
                    "source": source,
                }
            )
    return evidence


def gather_assay_evidence_for_decision(
    mod: ModuleDef,
    backend,
    topic: str,
    readout: str,
    queries: Sequence[str],
    top_k: int,
    seen_keys: set,
) -> List[Dict[str, object]]:
    if mod.module_id not in ASSAY_MODULES:
        return []
    evidence: List[Dict[str, object]] = []
    module_terms = module_focus_terms(mod)
    for query in queries:
        try:
            edges = backend.edge_search(query, top_k=top_k)
        except Exception:
            continue
        for edge in edges:
            meta = edge.get("metadata", edge)
            rel = str(meta.get("relation", ""))
            val = str(meta.get("value", ""))
            source = meta.get("paper") or meta.get("pdf_file") or ""
            if not any(k in rel.lower() or k in val.lower() for k in ASSAY_KEYS):
                continue
            key = ("assay", rel, val, str(source))
            if key in seen_keys:
                continue
            if not _matches_terms(f"{rel} {val}", module_terms):
                continue
            seen_keys.add(key)
            evidence.append(
                {
                    "type": "assay_edge",
                    "score": edge.get("score", 0.0),
                    "relation": rel,
                    "value": val,
                    "source": source,
                }
            )
    return evidence


def expand_keywords_from_kg(topic: str, backend, top_k: int = 50) -> List[Dict[str, str]]:
    """Keyword expansion agent using KG evidence spans."""
    if backend is None:
        return []
    aliases = TOPIC_ALIASES.get(topic.lower(), [topic.lower()])
    hints: List[Dict[str, str]] = []
    queries = aliases + [f"{topic} assay", f"{topic} readout", f"{topic} instrument", f"{topic} control"]
    for q in queries:
        try:
            edges = backend.edge_search(q, top_k=top_k)
        except Exception:
            continue
        for edge in edges:
            meta = edge.get("metadata", edge)
            src = str(meta.get("paper", meta.get("pdf_file", ""))).strip()
            if not src or src.lower() in BAD_SOURCES:
                continue
            val = str(meta.get("value", "")).strip()
            rel = str(meta.get("relation", "")).strip()
            span = f"{rel}: {val}".strip(": ")
            if not span:
                continue
            lower_span = span.lower()
            if any(tag in lower_span for tag in KEYWORD_TAGS):
                hints.append({"keyword": span[:80], "source": src})
    # Deduplicate by keyword text
    seen = set()
    deduped = []
    for h in hints:
        k = h["keyword"]
        if k in seen:
            continue
        seen.add(k)
        deduped.append(h)
    return deduped[:25]


def score_with_keywords(ev_list: List[Dict[str, object]], keywords: List[Dict[str, str]]) -> List[Dict[str, object]]:
    """Re-rank evidence based on keyword overlap."""
    if not ev_list or not keywords:
        return ev_list
    kw_terms = [k["keyword"].lower() for k in keywords]
    scored: List[Tuple[float, Dict[str, object]]] = []
    for ev in ev_list:
        val = str(ev.get("value", "")).lower()
        rel = str(ev.get("relation", "")).lower()
        hits = sum(1 for kw in kw_terms if kw in val or kw in rel)
        base = score_ev(ev)
        scored.append((base + 0.5 * hits, ev))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [ev for _, ev in scored]


def score_with_module_terms(
    ev_list: List[Dict[str, object]],
    module_terms: List[str],
    keywords: List[Dict[str, str]],
) -> List[Dict[str, object]]:
    if not ev_list:
        return ev_list
    kw_terms = [k["keyword"].lower() for k in keywords] if keywords else []
    scored: List[Tuple[float, Dict[str, object]]] = []
    for ev in ev_list:
        text = f"{ev.get('relation','')} {ev.get('value','')}".lower()
        module_hits = sum(1 for term in module_terms if term and term in text)
        keyword_hits = sum(1 for term in kw_terms if term and term in text)
        base = score_ev(ev)
        scored.append((base + 0.4 * module_hits + 0.2 * keyword_hits, ev))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [ev for _, ev in scored]


def gather_evidence_for_case(
    case: Dict[str, object],
    module_lookup: Dict[str, ModuleDef],
    use_kg: bool,
    include_instruments: bool,
    kg_top_k: int,
    keyword_expansion: List[Dict[str, str]],
) -> Dict[str, List[Dict[str, object]]]:
    evidence: Dict[str, List[Dict[str, object]]] = {mid: [] for mid in case["ordered_modules"]}
    if not use_kg:
        return evidence
    meth_backend = get_method_backend()
    for mid in case["ordered_modules"]:
        mod = module_lookup[mid]
        meth_ev = gather_method_evidence(
            mod,
            meth_backend,
            top_k=kg_top_k,
            topic=case.get("topic"),
            readout=str(case.get("readout", "")),
        )
        evidence[mid].extend(meth_ev)
        if include_instruments:
            try:
                from services.instrument_retrieval import get_backend as _get_inst
                inst_backend = _get_inst()
                inst_ev = gather_instrument_evidence(mod, inst_backend)
                evidence[mid].extend(clean_evidence_list(inst_ev))
            except Exception:
                pass
        ev_clean = clean_evidence_list(evidence[mid], max_len=160)
        module_terms = module_focus_terms(mod)
        kw = keyword_expansion if mod.module_id in ASSAY_MODULES else []
        ev_clean = score_with_module_terms(ev_clean, module_terms, kw)
        evidence[mid] = ev_clean[:10]
    return evidence


def gather_assay_evidence(
    topic: str,
    case: Dict[str, object],
    module_lookup: Dict[str, ModuleDef],
    use_kg: bool,
    kg_top_k: int,
) -> Dict[str, List[Dict[str, object]]]:
    assay_hits: Dict[str, List[Dict[str, object]]] = {mid: [] for mid in case["ordered_modules"]}
    if not use_kg:
        return assay_hits
    backend = get_method_backend()
    readout = case.get("readout", "")
    readout_key = "EchoMS" if "echo" in readout.lower() else "PlateReader"
    aliases = TOPIC_ALIASES.get(topic.lower(), [topic.lower()])
    llm_hints = llm_expand_keywords(topic, readout_key)
    readout_hints: List[str] = []
    tk = topic.lower()
    if tk in KEYWORD_HINTS:
        readout_hints.extend(KEYWORD_HINTS[tk].get(readout_key, []))

    for mid in case["ordered_modules"]:
        mod = module_lookup[mid]
        if mid not in ASSAY_MODULES:
            assay_hits[mid] = []
            continue
        base_queries = [f"{topic} {mod.module_name} {readout_key} assay"] + readout_hints + llm_hints
        for query in base_queries:
            try:
                edges = backend.edge_search(query, top_k=kg_top_k * 2)
            except Exception:
                continue
            for edge in edges:
                meta = edge.get("metadata", edge)
                src = str(meta.get("paper", meta.get("pdf_file", ""))).lower()
                if not any(f"data/{al}" in src for al in aliases):
                    continue
                val = str(meta.get("value", "")).lower()
                rel = str(meta.get("relation", "")).lower()
                if any(k in val or k in rel for k in ASSAY_KEYS):
                    assay_hits[mid].append(
                        {
                            "relation": meta.get("relation", ""),
                            "value": meta.get("value", ""),
                            "source": meta.get("paper", meta.get("pdf_file", "")),
                        }
                    )
            if len(assay_hits[mid]) >= kg_top_k:
                break
        if not assay_hits[mid]:
            # fallback: relax source constraint
            for query in base_queries:
                try:
                    edges = backend.edge_search(query, top_k=kg_top_k * 2)
                except Exception:
                    continue
                for edge in edges:
                    meta = edge.get("metadata", edge)
                    val = str(meta.get("value", "")).lower()
                    rel = str(meta.get("relation", "")).lower()
                    if any(k in val or k in rel for k in ASSAY_KEYS):
                        assay_hits[mid].append(
                            {
                                "relation": meta.get("relation", ""),
                                "value": meta.get("value", ""),
                                "source": meta.get("paper", meta.get("pdf_file", "")),
                            }
                        )
                    if len(assay_hits[mid]) >= kg_top_k:
                        break
        assay_hits[mid] = clean_evidence_list(assay_hits[mid], max_len=200)
        assay_hits[mid] = sorted(assay_hits[mid], key=score_ev, reverse=True)[:10]
    return assay_hits


def compute_method_score(backend, queries: Sequence[str]) -> Tuple[float, List[Dict[str, object]]]:
    details: List[Dict[str, object]] = []
    scores: List[float] = []
    for query in queries:
        detail = score_query_details(backend, query, top_k=6)
        detail["query"] = query
        details.append(detail)
        scores.append(float(detail["avg_score"]))
    avg_score = sum(scores) / len(scores) if scores else 0.0
    return avg_score, details


def compute_assay_score(assays: Sequence[Dict[str, object]], top_n: int = 3) -> float:
    if not assays:
        return 0.0
    ranked = sorted(assays, key=lambda row: float(row.get("score", 0.0)), reverse=True)
    top = ranked[: min(top_n, len(ranked))]
    return sum(float(row.get("score", 0.0)) for row in top) / len(top)


def detect_ambiguity(score_details: Sequence[Dict[str, object]]) -> bool:
    values = [float(d.get("avg_score", 0.0)) for d in score_details if isinstance(d.get("avg_score", 0.0), (int, float))]
    values = sorted(values, reverse=True)
    if len(values) < 2:
        return False
    return values[0] >= 0.40 and values[1] >= 0.40 and (values[0] - values[1]) < 0.05


def decision_threshold(score: float) -> Tuple[str, str]:
    if score >= 0.45:
        return "include", ""
    if score >= 0.30:
        return "optional", ""
    return "excluded", "low_evidence"


def gather_module_decision_evidence(
    mod: ModuleDef,
    backend,
    topic: str,
    readout: str,
    top_k: int,
    seen_keys: set,
) -> Dict[str, List[Dict[str, object]]]:
    queries = module_query_phrases(mod, topic, readout)
    method_sections = gather_section_evidence(mod, backend, queries, top_k=top_k, seen_keys=seen_keys)
    method_edges = gather_edge_evidence(mod, backend, queries, top_k=top_k, seen_keys=seen_keys)
    assay_edges = gather_assay_evidence_for_decision(mod, backend, topic, readout, queries, top_k=top_k, seen_keys=seen_keys)
    return {
        "sections": method_sections,
        "edges": method_edges,
        "assays": assay_edges,
        "queries": queries,
    }


def add_selection_citations(selection: Dict[str, object], registry: CitationRegistry) -> None:
    for block in selection.values():
        if not isinstance(block, dict):
            continue
        for meta in block.values():
            if not isinstance(meta, dict):
                continue
            for src in meta.get("sources", []):
                registry.add(src, title="", section="selection_evidence")


def evidence_citations(evidence: Sequence[Dict[str, object]], registry: CitationRegistry) -> List[Citation]:
    citations: List[Citation] = []
    for ev in evidence:
        source = ev.get("source", "")
        title = ev.get("title", "")
        section = ev.get("heading") or ev.get("relation") or ev.get("type", "")
        citations.append(registry.add(source, title=title, section=str(section)))
    return citations


def summarize_evidence_item(ev: Dict[str, object]) -> str:
    if ev.get("type") == "methodology_section":
        heading = str(ev.get("heading", "")).strip()
        text = str(ev.get("text", "")).strip()
        snippet = text[:120].replace("\n", " ")
        return f"{heading}: {snippet}".strip(": ")
    relation = str(ev.get("relation", "")).strip()
    value = str(ev.get("value", "")).strip()
    return f"{relation}: {value}".strip(": ")


def rank_evidence_items(evidence: Sequence[Dict[str, object]]) -> List[Dict[str, object]]:
    def key(ev: Dict[str, object]) -> Tuple[float, str, str]:
        score = float(ev.get("score", 0.0))
        ev_type = str(ev.get("type", ""))
        summary = summarize_evidence_item(ev).lower()
        return (-score, ev_type, summary)
    return sorted(list(evidence), key=key)


def compose_module_rationale(
    mod: ModuleDef,
    status: str,
    score: float,
    citations: Sequence[Citation],
    exclusion_reason: str,
) -> str:
    cite = citation_tag([c.id for c in citations[:2]])
    if status == "excluded" and exclusion_reason:
        return f"{mod.module_name} excluded due to {exclusion_reason}.{cite}"
    if status == "ambiguous":
        return f"Evidence for {mod.module_name} is conflicting; marked ambiguous at score {score:.2f}.{cite}"
    if status == "required":
        return f"{mod.module_name} required by template with supporting evidence score {score:.2f}.{cite}"
    if status == "include":
        return f"{mod.module_name} supported by evidence score {score:.2f}.{cite}"
    return f"{mod.module_name} optional with evidence score {score:.2f}.{cite}"


def build_module_decisions(
    case: Dict[str, object],
    module_lookup: Dict[str, ModuleDef],
    backend,
    inventory: List[str],
    kg_top_k: int,
) -> Tuple[List[Dict[str, object]], Dict[str, Dict[str, List[Dict[str, object]]]], CitationRegistry]:
    registry = CitationRegistry()
    add_selection_citations(case.get("selection_evidence", {}), registry)
    seen_keys: set = set()
    module_decisions: List[Dict[str, object]] = []
    evidence_bundle: Dict[str, Dict[str, List[Dict[str, object]]]] = {}
    topic = str(case.get("topic", case.get("case_study_title", "")))
    readout = str(case.get("readout", ""))
    organism = str(case.get("organism", ""))

    for module_id in ALL_MODULE_IDS:
        mod = module_lookup.get(module_id)
        if mod is None:
            mod = ModuleDef(
                module_id=module_id,
                module_name=module_id,
                subprocess=[],
                purpose="",
                inputs=[],
                outputs=[],
                constraints=[],
                dependencies=[],
                source_file="",
            )
        required_instruments = required_instruments_for_module(mod)
        in_template = module_id in case.get("ordered_modules", [])

        hard_reason = ""
        if module_id in MODULE_READOUT_REQUIREMENTS:
            required_readout = MODULE_READOUT_REQUIREMENTS[module_id]
            if required_readout.lower() != readout.lower():
                hard_reason = "readout_mismatch"
        if not hard_reason and module_id in MODULE_ORGANISM_REQUIREMENTS:
            required_org = MODULE_ORGANISM_REQUIREMENTS[module_id]
            if required_org.lower() != organism.lower():
                hard_reason = "organism_mismatch"
        if not hard_reason and inventory:
            for inst in required_instruments:
                if not instrument_available(inst, inventory):
                    hard_reason = "instrument_unavailable"
                    break

        if hard_reason:
            decision = {
                "module_id": mod.module_id,
                "module_name": mod.module_name,
                "module_status": "excluded",
                "score": 0.0,
                "exclusion_reason": hard_reason,
                "required_instruments": required_instruments,
                "evidence_sources": [],
                "top_evidence_sets": [],
                "rationale": compose_module_rationale(mod, "excluded", 0.0, [], hard_reason),
            }
            module_decisions.append(decision)
            evidence_bundle[module_id] = {"sections": [], "edges": [], "assays": [], "queries": []}
            continue

        if not in_template:
            decision = {
                "module_id": mod.module_id,
                "module_name": mod.module_name,
                "module_status": "excluded",
                "score": 0.0,
                "exclusion_reason": "template_not_selected",
                "required_instruments": required_instruments,
                "evidence_sources": [],
                "top_evidence_sets": [],
                "rationale": compose_module_rationale(mod, "excluded", 0.0, [], "template_not_selected"),
            }
            module_decisions.append(decision)
            evidence_bundle[module_id] = {"sections": [], "edges": [], "assays": [], "queries": []}
            continue

        ev = gather_module_decision_evidence(mod, backend, topic, readout, kg_top_k, seen_keys)
        evidence_bundle[module_id] = ev
        method_score, score_details = compute_method_score(backend, ev["queries"])
        assay_score = compute_assay_score(ev["assays"], top_n=3) if module_id in ASSAY_MODULES else 0.0
        combined_score = (method_score + assay_score) / 2.0 if module_id in ASSAY_MODULES else method_score

        ambiguous = detect_ambiguity(score_details)
        status, reason = decision_threshold(combined_score)
        if ambiguous:
            status = "ambiguous"
            reason = "contradiction_ambiguous"
        if status == "include" and module_id in CORE_REQUIRED_MODULES:
            status = "required"
        if status == "excluded" and not reason:
            reason = "low_evidence"

        citations = []
        citations.extend(evidence_citations(ev["sections"], registry))
        citations.extend(evidence_citations(ev["edges"], registry))
        citations.extend(evidence_citations(ev["assays"], registry))
        citations = list({c.id: c for c in citations}.values())

        combined_evidence = rank_evidence_items(ev["sections"] + ev["edges"] + ev["assays"])
        top_sets = []
        for item in combined_evidence[:2]:
            item_cites = evidence_citations([item], registry)
            top_sets.append(
                {
                    "type": item.get("type", ""),
                    "score": round(float(item.get("score", 0.0)), 4),
                    "summary": summarize_evidence_item(item),
                    "citation_ids": [c.id for c in item_cites],
                }
            )

        decision = {
            "module_id": mod.module_id,
            "module_name": mod.module_name,
            "module_status": status,
            "score": round(combined_score, 4),
            "exclusion_reason": reason,
            "required_instruments": required_instruments,
            "evidence_sources": [
                {
                    "id": c.id,
                    "source_id": c.source_id,
                    "source": c.source,
                    "title": c.title,
                    "section": c.section,
                }
                for c in citations
            ],
            "top_evidence_sets": top_sets,
            "rationale": compose_module_rationale(mod, status, combined_score, citations, reason),
        }
        module_decisions.append(decision)
    return module_decisions, evidence_bundle, registry
def generate_llm_rationale(case: Dict[str, object], evidence: Dict[str, List[Dict[str, object]]]) -> str:
    """LLM rationale summarizing why the template/organism/readout was chosen, grounded in selection_evidence + KG snippets."""
    local_llm = get_local_llm()
    sel = case.get("selection_evidence", {})
    org_scores = sel.get("organism", {})
    ro_scores = sel.get("readout", {})
    ev_lines = []
    for mid, evs in evidence.items():
        for ev in evs[:5]:
            ev_lines.append(f"{mid}: {ev.get('relation','')}: {ev.get('value','')} (source: {ev.get('source','')})")
    prompt = (
        "You are justifying a biofoundry template choice. Use only provided evidence; do not invent organisms, readouts, or steps.\n"
        f"Case title: {case.get('case_study_title','')}\n"
        f"Chosen organism: {case.get('organism','')}\n"
        f"Chosen readout: {case.get('readout','')}\n"
        f"Template: {case.get('template','')}\n\n"
        f"Organism scores: {org_scores}\n"
        f"Readout scores: {ro_scores}\n"
        "Module evidence snippets:\n" + "\n".join(ev_lines) + "\n\n"
        "Write a short rationale (3–5 sentences) that:\n"
        "1) States why the organism/readout pair fits, citing the scores/sources provided.\n"
        "2) Notes any uncertainty (e.g., close scores) without adding new information.\n"
        "3) Reminds the reader that module order is locked to the chosen template and no new steps are added.\n"
        "Keep it concise and grounded; do not fabricate details."
    )
    try:
        return local_llm.generate(prompt).strip()
    except Exception:
        return "LLM rationale unavailable (generation failed)."


DECISION_QUERIES = {
    "host_ecoli": "{topic} E.coli expression protocol",
    "host_yeast": "{topic} yeast expression protocol",
    "readout_platereader": "{topic} plate reader fluorescence absorbance assay",
    "readout_echoms": "{topic} EchoMS mass spec assay protocol",
    "plate_96": "{topic} 96 well plate assay",
    "plate_384": "{topic} 384 well plate assay",
    "echo_dispense": "{topic} acoustic dispensing Echo",
    "spark_reader": "{topic} plate reader Tecan Spark",
}


def compute_coverage_metrics(topic: str, backend) -> Dict[str, object]:
    results: Dict[str, object] = {}
    hits = 0
    for key, template in DECISION_QUERIES.items():
        query = template.format(topic=topic)
        detail = score_query_details(backend, query, top_k=6)
        hit = float(detail["top_score"]) >= 0.35
        if hit:
            hits += 1
        results[key] = {
            "query": query,
            "hit": hit,
            "top_score": round(float(detail["top_score"]), 4),
            "avg_score": round(float(detail["avg_score"]), 4),
            "sources": detail["sources"][:3],
        }
    coverage_rate = hits / max(1, len(DECISION_QUERIES))
    results["coverage_rate"] = round(coverage_rate, 4)
    return results


def template_score_table(selection: Dict[str, object], template_map: Dict[str, Dict[str, object]]) -> Dict[str, float]:
    org_scores = selection.get("organism", {})
    ro_scores = selection.get("readout", {})
    table: Dict[str, float] = {}
    for name, meta in template_map.items():
        org = meta["organism"]
        ro = meta["readout"]
        org_score = float(org_scores.get(org, {}).get("score", 0.0))
        ro_score = float(ro_scores.get(ro, {}).get("score", 0.0))
        table[name] = round(org_score + ro_score, 4)
    return table


def compute_template_stability(
    topic: str,
    template_map: Dict[str, Dict[str, object]],
    backend,
    runs: int = 5,
) -> Dict[str, object]:
    chosen: List[str] = []
    run_scores: List[Dict[str, float]] = []
    for _ in range(runs):
        case = select_template_for_topic(topic, template_map, backend, readout_bias=0)
        chosen.append(str(case["template"]))
        run_scores.append(template_score_table(case.get("selection_evidence", {}), template_map))
    mode = max(set(chosen), key=chosen.count) if chosen else ""
    stability = chosen.count(mode) / max(1, len(chosen))
    return {
        "chosen_templates": chosen,
        "stability": round(stability, 4),
        "run_scores": run_scores,
    }


def precision_at_k(value_hits: int, k: int) -> float:
    return round(value_hits / max(1, k), 4)


def compute_precision_at_k(
    modules: List[ModuleDef],
    backend,
    topic: str,
    readout: str,
    k: int = 3,
) -> Dict[str, object]:
    module_precisions: Dict[str, float] = {}
    total = 0.0
    for mod in modules:
        seen_keys: set = set()
        ev = gather_module_decision_evidence(mod, backend, topic, readout, top_k=6, seen_keys=seen_keys)
        combined = ev["sections"] + ev["edges"]
        combined = sorted(combined, key=lambda row: float(row.get("score", 0.0)), reverse=True)
        top_items = combined[:k]
        terms = module_focus_terms(mod)
        relevant = 0
        for item in top_items:
            text = ""
            if item.get("type") == "methodology_section":
                text = f"{item.get('heading','')} {item.get('text','')}"
            else:
                text = f"{item.get('relation','')} {item.get('value','')}"
            if _matches_terms(text, terms):
                relevant += 1
        precision = precision_at_k(relevant, k)
        module_precisions[mod.module_id] = precision
        total += precision
    avg_precision = round(total / max(1, len(modules)), 4)
    return {"per_module": module_precisions, "avg_precision": avg_precision}


def compute_contradictions(coverage: Dict[str, object]) -> Dict[str, bool]:
    host_ecoli = coverage.get("host_ecoli", {}).get("top_score", 0.0)
    host_yeast = coverage.get("host_yeast", {}).get("top_score", 0.0)
    readout_plate = coverage.get("readout_platereader", {}).get("top_score", 0.0)
    readout_echo = coverage.get("readout_echoms", {}).get("top_score", 0.0)
    return {
        "host_contradiction": host_ecoli >= 0.45 and host_yeast >= 0.45,
        "readout_contradiction": readout_plate >= 0.45 and readout_echo >= 0.45,
    }


def compute_traceability_rate(module_decisions: Sequence[Dict[str, object]]) -> Dict[str, object]:
    excluded = [m for m in module_decisions if m.get("module_status") == "excluded"]
    hard_reasons = {"readout_mismatch", "instrument_unavailable", "organism_mismatch", "template_not_selected"}
    missing: List[str] = []
    ok = 0
    for mod in excluded:
        reason = str(mod.get("exclusion_reason", ""))
        evidence = mod.get("evidence_sources", [])
        has_evidence = bool(evidence)
        has_reason = bool(reason)
        is_hard = reason in hard_reasons
        if has_reason and (has_evidence or is_hard):
            ok += 1
        else:
            missing.append(mod.get("module_id", ""))
    rate = ok / max(1, len(excluded))
    return {"traceability_rate": round(rate, 4), "missing_modules": missing}


def build_kg_fix_suggestions(
    coverage_rate: float,
    avg_precision: float,
    stability: float,
) -> List[str]:
    suggestions: List[str] = []
    if coverage_rate < 0.5:
        suggestions.append("Low host/readout coverage; add host annotations and assay edges in methodology KG.")
    if avg_precision < 0.5:
        suggestions.append("Low precision@3 for modules; refine MODULE_HINTS and chunking for module terms.")
    if stability < 0.8:
        suggestions.append("Template selection unstable; add contradiction penalties or strengthen signal separation in KG indexing.")
    if not suggestions:
        suggestions.append("KG coverage and precision look healthy; monitor for new topics or assays.")
    return suggestions


def run_kg_eval(topics: List[str], output_dir: Path) -> Dict[str, object]:
    backend = get_method_backend()
    modules = parse_modules_library(MODULE_LIB)
    module_lookup = build_module_lookup(modules)
    template_map = build_template_map(modules)
    inventory = load_instrument_inventory()
    report: Dict[str, object] = {"topics": {}, "generated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z"}

    for topic in topics:
        coverage = compute_coverage_metrics(topic, backend)
        stability = compute_template_stability(topic, template_map, backend, runs=5)
        case = select_template_for_topic(topic, template_map, backend, readout_bias=0)
        module_decisions, _, _ = build_module_decisions(case, module_lookup, backend, inventory, kg_top_k=5)
        precision = compute_precision_at_k(modules, backend, topic, case.get("readout", ""), k=3)
        contradictions = compute_contradictions(coverage)
        traceability = compute_traceability_rate(module_decisions)

        report["topics"][topic] = {
            "coverage": coverage,
            "stability": stability,
            "precision_at_3": precision,
            "contradictions": contradictions,
            "traceability": traceability,
            "kg_fix_suggestions": build_kg_fix_suggestions(
                coverage_rate=coverage.get("coverage_rate", 0.0),
                avg_precision=precision.get("avg_precision", 0.0),
                stability=stability.get("stability", 0.0),
            ),
        }

    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "kg_eval_report.json"
    md_path = output_dir / "kg_eval_report.md"
    json_path.write_text(json.dumps(report, indent=2))

    md_lines = ["# KG Evaluation Report", ""]
    for topic, data in report["topics"].items():
        md_lines.append(f"## {topic}")
        md_lines.append(
            f"- coverage_rate: {data['coverage']['coverage_rate']}"
        )
        md_lines.append(
            f"- stability: {data['stability']['stability']}"
        )
        md_lines.append(
            f"- avg_precision@3: {data['precision_at_3']['avg_precision']}"
        )
        md_lines.append(
            f"- host_contradiction: {data['contradictions']['host_contradiction']}"
        )
        md_lines.append(
            f"- readout_contradiction: {data['contradictions']['readout_contradiction']}"
        )
        md_lines.append(
            f"- traceability_rate: {data['traceability']['traceability_rate']}"
        )
        md_lines.append("- KG fix suggestions:")
        for suggestion in data["kg_fix_suggestions"]:
            md_lines.append(f"  - {suggestion}")
        md_lines.append("")
    md_path.write_text("\n".join(md_lines) + "\n")
    return report

def emit_case_outputs(
    case: Dict[str, object],
    module_lookup: Dict[str, ModuleDef],
    use_kg: bool,
    include_instruments: bool,
    kg_top_k: int,
    assay_enabled: bool,
    llm_rationale: bool,
    keyword_expansion: List[Dict[str, str]],
) -> Dict[str, object]:
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    run_dir = OUTPUT_ROOT / "runs" / timestamp
    base = run_dir / "case_studies"
    base.mkdir(parents=True, exist_ok=True)
    slug = case["case_study_title"].lower().replace(" ", "_").replace("+", "plus").replace("/", "_")
    protocol_path = base / f"{slug}.md"
    plan_path = base / f"{slug}_plan.json"
    latest_dir = OUTPUT_ROOT / "latest"
    latest_dir.mkdir(parents=True, exist_ok=True)
    latest_protocol_path = latest_dir / f"{slug}.md"
    latest_plan_path = latest_dir / f"{slug}_plan.json"
    timestamp = datetime.utcnow().isoformat(timespec="seconds") + "Z"
    protocol_md = f"<!-- generated: {timestamp} UTC -->\n" + render_protocol(case, module_lookup)
    inventory = load_instrument_inventory()
    decision_backend = get_method_backend()
    module_decisions, decision_evidence, registry = build_module_decisions(
        case,
        module_lookup,
        decision_backend,
        inventory,
        kg_top_k,
    )
    evidence = gather_evidence_for_case(case, module_lookup, use_kg, include_instruments, kg_top_k, keyword_expansion)
    assay_hits = gather_assay_evidence(case.get("topic", case.get("case_study_title","")), case, module_lookup, use_kg, kg_top_k) if assay_enabled else {mid: [] for mid in case["ordered_modules"]}
    if use_kg:
        protocol_md += "\n## KG Evidence (per module)\n"
        for mid in case["ordered_modules"]:
            if not evidence[mid]:
                continue
            src_map = {}
            snippets = []
            for idx, ev in enumerate(evidence[mid][:5], start=1):
                src = ev.get("source", "")
                if src not in src_map:
                    src_map[src] = f"K{idx}"
                snippets.append(f"[{src_map[src]}] {ev.get('relation','')}: {ev.get('value','')}")
            protocol_md += f"- {mid}:\n"
            for sn in snippets:
                protocol_md += f"  * {sn}\n"
            if src_map:
                protocol_md += "  Sources: " + "; ".join(f"[{v}] {k}" for k, v in src_map.items()) + "\n"
    if assay_enabled:
        protocol_md += "\n## Assay Evidence (per module)\n"
        for mid in case["ordered_modules"]:
            if not assay_hits[mid]:
                continue
            src_map = {}
            snippets = []
            for idx, hit in enumerate(assay_hits[mid], start=1):
                src = hit.get("source", "")
                if src not in src_map:
                    src_map[src] = f"S{idx}"
                snippets.append(f"[{src_map[src]}] {hit.get('relation','')}: {hit.get('value','')}")
            protocol_md += f"- {mid}:\n"
            for sn in snippets:
                protocol_md += f"  * {sn}\n"
            if src_map:
                protocol_md += "  Sources: " + "; ".join(f"[{v}] {k}" for k, v in src_map.items()) + "\n"
    protocol_md += "\n## Module Decisions\n"
    for decision in module_decisions:
        cite_ids = [src["id"] for src in decision.get("evidence_sources", [])]
        cite = citation_tag(cite_ids)
        protocol_md += (
            f"- {decision['module_id']}: {decision['module_status']} "
            f"(score {decision['score']:.2f}) {decision.get('exclusion_reason','')}. "
            f"{decision['rationale']} {cite}\n"
        )
    citations_list = registry.list()
    if citations_list:
        protocol_md += "\n## Citations\n" + "\n".join(
            f"[{c['id']}] {c['source']}" for c in citations_list
        ) + "\n"
    if llm_rationale:
        rationale = generate_llm_rationale(case, {**evidence, **assay_hits})
        protocol_md += "\n## Template Selection Rationale (KG-grounded)\n" + rationale + "\n"
    save_text(protocol_path, protocol_md)
    save_text(latest_protocol_path, protocol_md)
    plan_json = render_plan(case, module_lookup)
    plan_json["evidence"] = evidence
    plan_json["assay_evidence"] = assay_hits
    plan_json["module_decisions"] = module_decisions
    plan_json["citations"] = citations_list
    plan_json["decision_evidence"] = decision_evidence
    if llm_rationale:
        plan_json["llm_rationale"] = rationale
    save_json(plan_path, plan_json)
    save_json(latest_plan_path, plan_json)
    cleanup_old_runs(OUTPUT_ROOT, keep=2)
    return {
        "case": case,
        "protocol_path": str(protocol_path),
        "plan_path": str(plan_path),
        "protocol": protocol_md,
        "plan": plan_json,
    }


def run_biofoundry(
    topics: Sequence[str] | None = None,
    use_kg: bool = True,
    include_instruments: bool = False,
    kg_top_k: int = 5,
    assay_enabled: bool = True,
    llm_rationale: bool = False,
    kg_eval: bool = False,
    kg_eval_out: Path | None = None,
) -> Dict[str, object]:
    """Programmatic entrypoint for biofoundry template + KG orchestration."""
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    modules = parse_modules_library(MODULE_LIB)
    module_lookup = build_module_lookup(modules)

    emit_task_a(modules)
    template_map = build_template_map(modules)
    emit_task_b(template_map)

    if topics:
        topic_list = [t.strip() for t in topics if t and t.strip()]
    else:
        topic_list = discover_topics()
        if not topic_list:
            topic_list = ["petase", "3hp_pand", "retron"]

    meth_backend = get_method_backend()
    topic_keywords: Dict[str, List[Dict[str, str]]] = {}
    for topic in topic_list:
        topic_keywords[topic] = expand_keywords_from_kg(topic, meth_backend, top_k=50)

    if kg_eval:
        eval_out = kg_eval_out or (OUT_DIR / "kg_eval")
        report = run_kg_eval(topic_list, eval_out)
        return {"kg_eval": report, "kg_eval_out": str(eval_out)}

    cases = build_case_studies(template_map, topic_list)
    outputs: List[Dict[str, object]] = []
    for case in cases:
        kw = topic_keywords.get(case.get("topic", ""), [])
        outputs.append(
            emit_case_outputs(
                case,
                module_lookup,
                use_kg,
                include_instruments,
                kg_top_k,
                assay_enabled,
                llm_rationale,
                kw,
            )
        )

    return {
        "topics": topic_list,
        "cases": cases,
        "outputs": outputs,
        "output_root": str(OUTPUT_ROOT),
        "log_dir": str(OUT_DIR),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Biofoundry template agent with optional KG enrichment.")
    parser.add_argument("--no-kg", action="store_true", help="Disable KG evidence enrichment (defaults to enabled).")
    parser.add_argument(
        "--include-instruments",
        action="store_true",
        help="Include instrument KG evidence (default off; methodology KG still used when KG enabled).",
    )
    parser.add_argument(
        "--kg-top-k",
        type=int,
        default=5,
        help="Number of methodology KG edges to pull per module (default 5). Increase for broader evidence.",
    )
    parser.add_argument(
        "--no-assay-evidence",
        action="store_true",
        help="Disable assay-specific evidence extraction (enabled by default).",
    )
    parser.add_argument(
        "--topics",
        type=str,
        help="Comma-separated topic names. If omitted, auto-discovers from workspaces/ and data/.",
    )
    parser.add_argument(
        "--llm-rationale",
        action="store_true",
        help="Generate an LLM rationale section grounded in selection_evidence and KG/assay snippets.",
    )
    parser.add_argument(
        "--kg-eval",
        action="store_true",
        help="Run deterministic KG health evaluation and write kg_eval_report.json/.md.",
    )
    parser.add_argument(
        "--kg-eval-out",
        type=Path,
        help="Output directory for KG evaluation reports (default: logs/biofoundry/auto/kg_eval).",
    )
    args = parser.parse_args()
    use_kg = not args.no_kg
    include_instruments = bool(args.include_instruments) and _instrument_usage_enabled()
    kg_top_k = max(1, args.kg_top_k)
    assay_enabled = not args.no_assay_evidence
    llm_rationale = bool(args.llm_rationale)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    modules = parse_modules_library(MODULE_LIB)
    module_lookup = build_module_lookup(modules)

    emit_task_a(modules)
    template_map = build_template_map(modules)
    emit_task_b(template_map)

    if args.topics:
        topics = [t.strip() for t in args.topics.split(",") if t.strip()]
    else:
        topics = discover_topics()
        if not topics:
            topics = ["petase", "3hp_pand", "retron"]

    # Keyword expansion agent runs before template selection
    meth_backend = get_method_backend()
    topic_keywords: Dict[str, List[Dict[str, str]]] = {}
    for topic in topics:
        topic_keywords[topic] = expand_keywords_from_kg(topic, meth_backend, top_k=50)

    if args.kg_eval:
        eval_out = args.kg_eval_out or (OUT_DIR / "kg_eval")
        run_kg_eval(topics, eval_out)
        print(f"KG evaluation report written to {eval_out}")
        return

    cases = build_case_studies(template_map, topics)
    for case in cases:
        kw = topic_keywords.get(case.get("topic", ""), [])
        emit_case_outputs(case, module_lookup, use_kg, include_instruments, kg_top_k, assay_enabled, llm_rationale, kw)

    print(f"Generated biofoundry artifacts under {OUT_DIR}")


if __name__ == "__main__":
    main()
