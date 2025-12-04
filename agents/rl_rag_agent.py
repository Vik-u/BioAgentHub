#!/usr/bin/env python3
"""Lightweight RL-driven RAG agent over the PETase retrieval stack."""

from __future__ import annotations

import json
import os
import random
import sys
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Tuple, Optional

import numpy as np

import typer

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services import local_llm
from services.retrieval_service import RetrievalBackend, get_backend, log_event
from utils.enzyme_aliases import expected_entities_from_question, preferred_sources

LOG_PATH = Path(__file__).resolve().parents[1] / "logs" / "rl_agent_runs.jsonl"
ACTIONS = ("vector_search", "graph_expand", "summarize", "stop")
DEFAULT_USE_LLM = os.environ.get("USE_LOCAL_LLM", "1") == "1"
WORKSPACE_ROOT = Path(os.environ.get("WORKSPACE_ROOT", PROJECT_ROOT / "KnowledgeGraph")).resolve()
TEXT_DIR = WORKSPACE_ROOT / "text"
META_DIR = WORKSPACE_ROOT / "metadata"


@lru_cache(maxsize=1)
def load_pdf_titles() -> Dict[str, str]:
    titles: Dict[str, str] = {}
    if META_DIR.exists():
        for meta_file in META_DIR.glob("*.json"):
            try:
                data = json.loads(meta_file.read_text())
            except Exception:
                continue
            pdf = data.get("pdf_file")
            title = data.get("title_candidate") or meta_file.stem
            if pdf:
                titles[pdf] = title
    return titles


def resolve_title(pdf_file: str | None) -> str:
    if not pdf_file:
        return "Unknown source"
    return load_pdf_titles().get(pdf_file, pdf_file)


@dataclass
class AgentState:
    question: str
    context: List[Dict[str, Any]] = field(default_factory=list)
    graph_nodes: List[Dict[str, Any]] = field(default_factory=list)
    steps: int = 0


def state_to_observation(state: AgentState | None) -> np.ndarray:
    if state is None:
        return np.zeros(3, dtype=np.float32)
    context = min(len(state.context), 10) / 10.0
    graph = min(len(state.graph_nodes), 10) / 10.0
    steps = min(state.steps, 6) / 6.0
    return np.array([context, graph, steps], dtype=np.float32)


class RetrievalEnvironment:
    def __init__(self, backend: RetrievalBackend, max_steps: int = 6) -> None:
        self.backend = backend
        self.max_steps = max_steps
        self.state: AgentState | None = None

    def reset(self, question: str) -> AgentState:
        self.state = AgentState(question=question)
        return self.state

    def step(self, action: str) -> Tuple[AgentState, float, bool, str]:
        assert self.state is not None
        self.state.steps += 1
        done = False
        info = ""
        reward = -0.01  # small per-step penalty

        if action == "vector_search":
            results = self.backend.vector_search(self.state.question, top_k=5)
            self.state.context.extend(results)
            reward += 0.2 if results else -0.1
            info = "vector_search"
        elif action == "graph_expand":
            if not self.state.context:
                reward -= 0.1
                info = "graph_expand_failed"
            else:
                context_sources = [
                    ctx.get("metadata", {}).get("source")
                    for ctx in self.state.context
                    if ctx.get("metadata", {}).get("source")
                ]
                seeds = preferred_sources(context_sources)
                neighbors = self.backend.graph_neighbors_diverse(seeds, top_k=10)
                self.state.graph_nodes.extend(neighbors)
                reward += 0.15 if neighbors else -0.05
                info = f"graph_expand:{'/'.join(seeds[:3])}"
        elif action == "summarize":
            if not self.state.context:
                reward -= 0.05
                info = "summarize_empty"
            else:
                info = "summarize"
                reward += 0.25
        elif action == "stop":
            done = True
            reward += 0.3 if self.state.context else -0.2
            info = "stop"
        else:
            raise ValueError(f"Unknown action {action}")

        if self.state.steps >= self.max_steps:
            done = True
        return self.state, reward, done, info


class SimplePolicy:
    def select(self, state: AgentState) -> str:
        if not state.context:
            return "vector_search"
        if len(state.graph_nodes) < 5:
            return "graph_expand"
        if state.steps >= 3:
            return "summarize"
        return "stop"


def augment_with_expected_entities(state: AgentState, backend: RetrievalBackend, expected_entities: List[str]) -> None:
    present_sources = set()
    for ctx in state.context:
        source = ctx.get("metadata", {}).get("source")
        if source:
            present_sources.add(source)
    for node in state.graph_nodes:
        src = node.get("source")
        if src:
            present_sources.add(src)

    for entity in expected_entities:
        if entity in present_sources:
            continue
        edges = backend.graph_neighbors(entity, top_k=5)
        if edges:
            state.graph_nodes = edges + state.graph_nodes
            for edge in edges:
                present_sources.add(edge.get("source"))


def fetch_pdf_context(paper: str | None, sentence: str, window: int = 600) -> str:
    if not paper:
        return ""
    txt_path = TEXT_DIR / (Path(paper).stem + ".txt")
    if not txt_path.exists():
        return ""
    content = txt_path.read_text(errors="ignore")
    snippet = sentence.strip()
    snippet_lower = snippet.lower()[:120]
    idx = content.lower().find(snippet_lower) if snippet_lower else -1
    if idx == -1:
        return content[:window].strip()
    start = max(0, idx - window // 2)
    end = min(len(content), idx + window // 2)
    return content[start:end].strip()


def summarize_context(state: AgentState, use_llm: bool, question: str) -> Tuple[str, List[Dict[str, str]]]:
    sentences = []
    evidence_blocks = []
    citations: List[Dict[str, str]] = []
    citation_index: Dict[str, int] = {}

    def register_citation(paper: str | None) -> int | None:
        if not paper:
            return None
        if paper not in citation_index:
            citation_index[paper] = len(citations) + 1
            citations.append({
                "id": citation_index[paper],
                "paper": paper,
                "title": resolve_title(paper),
            })
        return citation_index[paper]

    def add_block(entry: str, paper: str | None, context: str) -> None:
        cid = register_citation(paper)
        evidence_blocks.append({
            "entry": entry,
            "context": context,
            "citation": cid,
        })

    def format_entry(meta: Dict[str, Any]) -> str:
        if "source" in meta and "relation" in meta:
            target = meta.get("target", "")
            return f"{meta['source']} {meta['relation']} {target}".strip()
        label = meta.get("title") or meta.get("pdf_file") or meta.get("chunk_id") or "evidence"
        return str(label)

    for ctx in state.context[:5]:
        meta = ctx.get("metadata", {})
        snippet = ctx["text"].split("Evidence:", 1)[-1].strip()
        entry = format_entry(meta)
        sentences.append(entry)
        add_block(entry, meta.get("paper") or meta.get("pdf_file"), fetch_pdf_context(meta.get("paper"), snippet))

    for neighbor in state.graph_nodes[:5]:
        entry = format_entry(neighbor)
        sentences.append(entry)
        add_block(entry, neighbor.get("paper"), fetch_pdf_context(neighbor.get("paper"), neighbor.get("sentence", "")))

    if not sentences:
        return "No evidence gathered.", []

    if use_llm:
        expected_entities = expected_entities_from_question(question)
        evidence_text_lines = []
        for block in evidence_blocks:
            prefix = f"[{block['citation']}] " if block["citation"] else ""
            context_part = f"\n  Context: {block['context']}" if block["context"] else ""
            evidence_text_lines.append(f"- {prefix}{block['entry']}{context_part}")
        evidence_text = "\n".join(evidence_text_lines)
        expected_text = ", ".join(expected_entities) if expected_entities else "the enzymes already cited"
        prompt = (
            "You are a PETase research assistant. Read the evidence snippets (with citations like [1], [2]) and respond in natural paragraphs.\n"
            "Goals:\n"
            "- Summarize what is already known.\n"
            "- Identify limitations or knowledge gaps (note if an expected enzyme is missing: "
            f"{expected_text}).\n"
            "- Recommend concrete computational and experimental next steps.\n"
            "Write fluid prose (no bullet headings) and reference citations inline using [n].\n"
            "Evidence:\n"
            f"{evidence_text}"
        )
        answer_text = local_llm.generate(prompt)
    else:
        answer_text = " ".join(sentences)

    if citations:
        citation_lines = [
            f"[{c['id']}] {c['title']} ({c['paper']})"
            for c in citations
        ]
        answer_text = answer_text.strip() + "\n\nSources:\n" + "\n".join(citation_lines)

    return answer_text, citations


def compute_metrics(state: AgentState, rewards: List[float]) -> Dict[str, float | None]:
    faiss_scores = [ctx.get("score") for ctx in state.context if isinstance(ctx.get("score"), (int, float))]
    kg_conf = [node.get("confidence") for node in state.graph_nodes if isinstance(node.get("confidence"), (int, float))]
    metrics = {
        "faiss_avg": sum(faiss_scores) / len(faiss_scores) if faiss_scores else None,
        "kg_conf_avg": sum(kg_conf) / len(kg_conf) if kg_conf else None,
        "rl_reward_sum": sum(rewards) if rewards else None,
    }
    return metrics


def log_trajectory(question: str, steps: List[Dict[str, Any]], answer: str, rewards: List[float]) -> None:
    payload = {
        "question": question,
        "steps": steps,
        "answer": answer,
        "rewards": rewards,
    }
    with LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def run_agent(
    question: str,
    use_llm: bool = DEFAULT_USE_LLM,
    seed: int = 7,
    policy_model: Optional[Any] = None,
) -> Dict[str, Any]:
    random.seed(seed)
    backend = get_backend()
    env = RetrievalEnvironment(backend)
    heuristic_policy = SimplePolicy()
    state = env.reset(question)
    done = False
    trajectory = []
    rewards = []

    while not done:
        if policy_model is not None:
            obs = state_to_observation(state)
            action_idx, _ = policy_model.predict(obs, deterministic=True)
            action = ACTIONS[int(action_idx)]
        else:
            action = heuristic_policy.select(state)
        state, reward, done, info = env.step(action)
        trajectory.append({"action": action, "info": info, "context_size": len(state.context)})
        rewards.append(reward)
        if action == "summarize":
            done = True
            break

    expected = expected_entities_from_question(question)
    if expected:
        augment_with_expected_entities(state, backend, expected)
    answer, citations = summarize_context(state, use_llm, question)
    metrics = compute_metrics(state, rewards)
    log_trajectory(question, trajectory, answer, rewards)
    log_event(
        {
            "event": "rl_agent_run",
            "question": question,
            "trajectory": trajectory,
            "answer": answer,
            "use_llm": use_llm,
            "metrics": metrics,
        }
    )
    return {
        "answer": answer,
        "citations": citations,
        "metrics": metrics,
        "trajectory": trajectory,
        "rewards": rewards,
        "use_llm": use_llm,
    }


app = typer.Typer(add_completion=False)


@app.command()
def ask(
    question: str = typer.Argument(..., help="Natural-language question for the PETase agent."),
    use_llm: bool = typer.Option(
        DEFAULT_USE_LLM,
        "--use-llm/--no-llm",
        help="Toggle the local LLM summarizer.",
    ),
    seed: int = typer.Option(7, help="Random seed for reproducibility."),
) -> None:
    """Run the RL-based agent against a natural-language question."""
    result = run_agent(question, use_llm=use_llm, seed=seed)
    typer.echo(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    app()
