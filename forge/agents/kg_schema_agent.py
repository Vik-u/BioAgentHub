#!/usr/bin/env python3
"""LLM-assisted schema generator for topic-agnostic KG extraction."""

from __future__ import annotations

import argparse
import json
import random
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional
import datetime
import os
import subprocess

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services import local_llm  # noqa: E402
from services.local_llm import LocalLLMError  # noqa: E402


DEFAULT_SCHEMA: Dict[str, object] = {
    "topic": "",
    "focus_query": "",
    "key_entities": [],
    "entity_aliases": {},
    "substrates": [],
    "products": [],
    "metrics": [
        "activity",
        "stability",
        "kinetics",
        "yield",
        "conversion",
        "selectivity",
        "expression",
        "thermostability",
        "specificity",
    ],
    "conditions": [],
    "hosts": [
        "E. coli",
        "Escherichia coli",
        "Saccharomyces cerevisiae",
        "Bacillus subtilis",
        "Pseudomonas",
        "Corynebacterium",
        "yeast",
    ],
    "assays": [
        "HPLC",
        "GC",
        "MS",
        "LC-MS",
        "SDS-PAGE",
        "fluorescence",
        "absorbance",
        "colorimetric",
    ],
    "relation_keywords": {
        "has_mutation": ["mutation", "mutant", "variant", "substitution", "engineered"],
        "active_temperature": ["temperature", "degrees", "thermostable", "Tm"],
        "active_pH": ["pH"],
        "achieves_conversion": ["conversion", "degradation", "hydrolysis", "yield"],
        "targets_substrate": ["substrate", "hydrolysis", "degrade", "target"],
        "discusses_metric": ["activity", "stability", "kinetic", "turnover", "selectivity", "yield"],
        "expressed_in": ["expressed in", "host", "strain", "expression in"],
        "assayed_with": ["assay", "HPLC", "GC", "MS", "SDS-PAGE", "fluorescence", "absorbance"],
    },
    "unit_rules": {},
}


SYSTEM_PROMPT = "You are an information extraction architect for scientific literature."


def load_corpus_index(path: Path) -> List[dict]:
    if not path.exists():
        return []
    return json.loads(path.read_text())

def pick_text_files(text_dir: Path, corpus_index: List[dict], max_docs: int, rng: random.Random) -> List[Path]:
    if corpus_index:
        sorted_docs = sorted(corpus_index, key=lambda entry: entry.get("char_count", 0), reverse=True)
        picks = []
        for entry in sorted_docs:
            txt_name = entry.get("txt_file")
            if not txt_name:
                continue
            candidate = text_dir / txt_name
            if candidate.exists():
                picks.append(candidate)
            if len(picks) >= max_docs:
                break
        return picks
    files = list(text_dir.glob("*.txt"))
    files.sort()
    rng.shuffle(files)
    return files[:max_docs]

def sample_text(
    text_dir: Path,
    corpus_index: List[dict],
    max_docs: int,
    max_chars: int,
    seed: int,
) -> str:
    rng = random.Random(seed)
    picks = pick_text_files(text_dir, corpus_index, max_docs, rng)
    if not picks:
        return ""
    per_doc = max(1000, max_chars // max(len(picks), 1))
    chunks = []
    remaining = max_chars
    for path in picks:
        if remaining <= 0:
            break
        text = path.read_text(errors="ignore")
        snippet = text[: min(len(text), per_doc, remaining)]
        if snippet:
            chunks.append(snippet)
            remaining -= len(snippet)
    return "\n\n".join(chunks)


def extract_json_block(text: str) -> Optional[dict]:
    if not text:
        return None
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return None
    payload = match.group(0)
    try:
        return json.loads(payload)
    except json.JSONDecodeError:
        return None


def log_schema_error(message: str) -> None:
    print(f"[schema-induction] {message}", file=sys.stderr)


def normalize_schema(schema: dict, topic: str, focus_query: str) -> Dict[str, object]:
    normalized: Dict[str, object] = json.loads(json.dumps(DEFAULT_SCHEMA))
    normalized["topic"] = topic
    normalized["focus_query"] = focus_query

    if schema:
        for key, value in schema.items():
            if value is None:
                continue
            normalized[key] = value

    key_entities = [str(item).strip() for item in normalized.get("key_entities", []) if str(item).strip()]
    normalized["key_entities"] = sorted(set(key_entities))

    entity_aliases = normalized.get("entity_aliases") or {}
    if not isinstance(entity_aliases, dict):
        entity_aliases = {}
    cleaned_aliases = {}
    for canonical, aliases in entity_aliases.items():
        if not canonical:
            continue
        alias_list = [str(a).strip() for a in aliases or [] if str(a).strip()]
        cleaned_aliases[str(canonical).strip()] = sorted(set(alias_list))
    for ent in normalized["key_entities"]:
        cleaned_aliases.setdefault(ent, [])
    normalized["entity_aliases"] = cleaned_aliases

    for list_key in ("substrates", "products", "metrics", "conditions", "hosts", "assays"):
        values = normalized.get(list_key, [])
        cleaned = [str(item).strip() for item in values or [] if str(item).strip()]
        normalized[list_key] = sorted(set(cleaned))

    relation_keywords = normalized.get("relation_keywords") or {}
    if not isinstance(relation_keywords, dict):
        relation_keywords = {}
    cleaned_keywords: Dict[str, List[str]] = {}
    for relation, keywords in relation_keywords.items():
        if not relation:
            continue
        cleaned = [str(item).strip() for item in keywords or [] if str(item).strip()]
        cleaned_keywords[str(relation).strip()] = sorted(set(cleaned))
    normalized["relation_keywords"] = cleaned_keywords

    return normalized


def load_schema_induction_config() -> Dict[str, object]:
    config_path = PROJECT_ROOT / "config" / "llm_config.json"
    if config_path.exists():
        try:
            return json.loads(config_path.read_text())
        except json.JSONDecodeError:
            return {}
    return {}


def git_sha() -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
    except Exception:
        return None
    sha = result.stdout.strip()
    return sha or None


def apply_schema_version(schema: Dict[str, object], backend: str, seed: int, model: str | None) -> Dict[str, object]:
    schema = json.loads(json.dumps(schema))
    schema["schema_version"] = {
        "generated_at": datetime.datetime.utcnow().isoformat() + "Z",
        "git_sha": git_sha(),
        "backend": backend,
        "seed": seed,
        "model": model,
    }
    return schema


def generate_schema_existing(
    workspace: Path,
    focus_query: str,
    max_docs: int,
    max_chars: int,
    seed: int,
) -> Dict[str, object]:
    text_dir = workspace / "text"
    corpus_index = load_corpus_index(workspace / "corpus_index.json")
    sample = sample_text(text_dir, corpus_index, max_docs=max_docs, max_chars=max_chars, seed=seed)
    topic = workspace.name
    if not sample:
        return normalize_schema({}, topic, focus_query)

    prompt = (
        "Design a JSON schema for knowledge graph extraction from scientific papers.\n"
        f"Topic: {topic}\n"
        f"Focus query: {focus_query}\n"
        "Use the sample text to infer key entities, substrates, metrics, and relation keywords.\n"
        "Return ONLY valid JSON with these keys:\n"
        "- topic (string)\n"
        "- focus_query (string)\n"
        "- key_entities (list of canonical entity names)\n"
        "- entity_aliases (object: canonical -> list of aliases)\n"
        "- substrates (list of substrate/compound names)\n"
        "- metrics (list of metrics relevant to protein engineering)\n"
        "- hosts (list of common host organisms or strains)\n"
        "- assays (list of assays/instrument terms)\n"
        "- relation_keywords (object: relation -> list of keywords)\n"
        "Use lower_snake_case for relation names. Keep lists under 25 items.\n\n"
        "Sample text:\n"
        f"{sample}"
    )
    try:
        raw = local_llm.generate(prompt, system_prompt=SYSTEM_PROMPT)
    except LocalLLMError:
        log_schema_error("LLM call failed; using default schema.")
        return normalize_schema({}, topic, focus_query)

    parsed = extract_json_block(raw) or {}
    return normalize_schema(parsed, topic, focus_query)


def generate_schema_pydantic_ai(
    workspace: Path,
    focus_query: str,
    max_docs: int,
    max_chars: int,
    seed: int,
    config: Dict[str, object],
) -> Dict[str, object]:
    try:
        from pydantic import BaseModel, Field, ValidationError  # type: ignore
        from pydantic_ai import Agent  # type: ignore
        from pydantic_ai.models.openai import OpenAIModel  # type: ignore
    except Exception as exc:  # pragma: no cover - optional dependency
        raise RuntimeError("PydanticAI backend requested but not available.") from exc

    class Entity(BaseModel):
        name: str = Field(..., min_length=1)
        aliases: List[str] = Field(default_factory=list)

    class SchemaInduction(BaseModel):
        topic: str
        focus_query: str
        entities: List[Entity] = Field(default_factory=list)
        assays: List[str] = Field(default_factory=list)
        metrics: List[str] = Field(default_factory=list)
        substrates: List[str] = Field(default_factory=list)
        products: List[str] = Field(default_factory=list)
        conditions: List[str] = Field(default_factory=list)
        relation_keywords: Dict[str, List[str]] = Field(default_factory=dict)
        unit_rules: Dict[str, object] = Field(default_factory=dict)

    text_dir = workspace / "text"
    corpus_index = load_corpus_index(workspace / "corpus_index.json")
    sample = sample_text(text_dir, corpus_index, max_docs=max_docs, max_chars=max_chars, seed=seed)
    if not sample:
        return normalize_schema({}, workspace.name, focus_query)

    api_base = str(config.get("api_base", "https://api.openai.com/v1"))
    api_key_env = str(config.get("api_key_env", "OPENAI_API_KEY"))
    api_key = os.environ.get(api_key_env)
    if not api_key:
        raise RuntimeError(f"Missing API key in environment variable {api_key_env}")
    model_name = str(config.get("schema_induction_model") or config.get("model") or "gpt-4o-mini")
    model = OpenAIModel(model_name, api_key=api_key, base_url=api_base)

    prompt = (
        "Design a JSON schema for knowledge graph extraction from scientific papers.\n"
        f"Topic: {workspace.name}\n"
        f"Focus query: {focus_query}\n"
        "Return structured data with entities (with aliases), assays, metrics, substrates, products, conditions, "
        "relation_keywords, and unit_rules.\n"
        "Keep lists concise and domain-specific. Use lower_snake_case for relation names.\n\n"
        "Sample text:\n"
        f"{sample}"
    )
    try:
        agent = Agent(model, result_type=SchemaInduction, system_prompt=SYSTEM_PROMPT)
        result = agent.run_sync(prompt)
    except TypeError:
        agent = Agent(model, result_type=SchemaInduction)
        result = agent.run_sync(f"{SYSTEM_PROMPT}\n\n{prompt}")
    except Exception as exc:
        log_schema_error(f"PydanticAI run failed: {exc}")
        raise

    data = getattr(result, "data", result)
    if not isinstance(data, SchemaInduction):
        try:
            data = SchemaInduction.model_validate(data)
        except ValidationError as exc:
            log_schema_error(f"PydanticAI response validation failed: {exc}")
            raise

    key_entities = [entity.name for entity in data.entities]
    entity_aliases = {entity.name: entity.aliases for entity in data.entities}
    schema = {
        "topic": data.topic or workspace.name,
        "focus_query": data.focus_query or focus_query,
        "key_entities": key_entities,
        "entity_aliases": entity_aliases,
        "substrates": data.substrates,
        "products": data.products,
        "metrics": data.metrics,
        "conditions": data.conditions,
        "hosts": DEFAULT_SCHEMA.get("hosts", []),
        "assays": data.assays,
        "relation_keywords": data.relation_keywords,
        "unit_rules": data.unit_rules,
    }
    return normalize_schema(schema, workspace.name, focus_query)


def generate_schema(
    workspace: Path,
    focus_query: str,
    max_docs: int = 6,
    max_chars: int = 12000,
    use_llm: bool = True,
    seed: int = 7,
    backend_override: Optional[str] = None,
) -> Dict[str, object]:
    config = load_schema_induction_config()
    backend = (backend_override or config.get("schema_induction_backend") or "existing_backend").lower()
    if not use_llm:
        schema = normalize_schema({}, workspace.name, focus_query)
        return apply_schema_version(schema, backend, seed, None)
    if backend == "pydantic_ai":
        schema = generate_schema_pydantic_ai(workspace, focus_query, max_docs, max_chars, seed, config)
        return apply_schema_version(schema, backend, seed, str(config.get("schema_induction_model") or config.get("model")))
    schema = generate_schema_existing(workspace, focus_query, max_docs, max_chars, seed)
    return apply_schema_version(schema, backend, seed, str(config.get("model")))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, required=True, help="Workspace containing text/metadata.")
    parser.add_argument(
        "--focus-query",
        default="protein engineering",
        help="User query to bias schema extraction (default: protein engineering).",
    )
    parser.add_argument("--output", type=Path, help="Output schema path (default: <workspace>/kg_schema.json).")
    parser.add_argument("--sample-docs", type=int, default=6, help="Number of documents to sample.")
    parser.add_argument("--sample-chars", type=int, default=12000, help="Max characters sampled across docs.")
    parser.add_argument("--no-llm", action="store_true", help="Skip LLM and emit default schema.")
    parser.add_argument("--seed", type=int, help="Random seed for deterministic sampling.")
    parser.add_argument("--backend", help="Override schema induction backend (existing_backend|pydantic_ai).")
    args = parser.parse_args()

    workspace = args.workspace.resolve()
    output = args.output or (workspace / "kg_schema.json")
    config = load_schema_induction_config()
    seed = args.seed if args.seed is not None else int(config.get("schema_induction_seed", 7) or 7)
    schema = generate_schema(
        workspace,
        focus_query=args.focus_query,
        max_docs=args.sample_docs,
        max_chars=args.sample_chars,
        use_llm=not args.no_llm,
        seed=seed,
        backend_override=args.backend,
    )
    output.write_text(json.dumps(schema, indent=2, ensure_ascii=True))
    print(f"Wrote schema to {output}")


if __name__ == "__main__":
    main()
