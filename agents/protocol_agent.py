#!/usr/bin/env python3
"""Agentic reasoning over experimental protocols using LangChain + LangGraph."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, TypedDict

from langchain_core.language_models.llms import LLM
from langchain_core.prompts import PromptTemplate
from langgraph.graph import StateGraph, END

from services import local_llm

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL_DIR = ROOT / "KnowledgeGraph" / "protocols"


class LocalLLM(LLM):
    @property
    def _llm_type(self) -> str:
        return "local_llm"

    def _call(self, prompt: str, stop: List[str] | None = None, run_manager=None) -> str:
        return local_llm.generate(prompt)

    @property
    def _identifying_params(self) -> Dict[str, str]:
        return {"model": "local_llm"}


@dataclass
class ProtocolEntry:
    title: str
    pdf_file: str
    steps: List[str]


def load_protocol_corpus() -> List[ProtocolEntry]:
    entries: List[ProtocolEntry] = []
    for proto_file in sorted(PROTOCOL_DIR.glob("*.json")):
        data = json.loads(proto_file.read_text())
        steps = data.get("steps") or []
        if not steps:
            continue
        entries.append(
            ProtocolEntry(
                title=data.get("title", proto_file.stem),
                pdf_file=data.get("pdf_file", proto_file.stem + ".pdf"),
                steps=steps,
            )
        )
    return entries


CORPUS = load_protocol_corpus()
LLM_MODEL = LocalLLM()
PROMPT = PromptTemplate(
    input_variables=["question", "snippets"],
    template=(
        "You are preparing execution-ready instructions for PETase researchers. Question: {question}\n"
        "Relevant protocol snippets:\n{snippets}\n\n"
        "Write the response as Markdown with two H2 sections in this order:\n"
        "## Experimental Workflow\n"
        "Step 1 – <short title>\n"
        "Action: ...\n"
        "Detailed Instructions: (multi-line, include exact volumes, temperatures, equipment, durations).\n"
        "Rationale: ... [citation]\n"
        "Next Step Trigger: ...\n"
        "(Repeat Step 2, Step 3, etc. until the experimental goal is complete.)\n\n"
        "## Computational Workflow\n"
        "Step 1 – <short title>\n"
        "Action: ...\n"
        "Detailed Instructions: include software, parameters, hardware needs.\n"
        "Rationale: ... [citation]\n"
        "Next Step Trigger: ...\n"
        "(Continue for all computational tasks.)\n"
        "Use full sentences, blank lines between steps, and cite sources with [n]."
    ),
)


class AgentState(TypedDict):
    question: str
    snippets: List[Dict[str, str]]
    answer: str


def retrieve_snippets(question: str, top_k: int = 3) -> List[Dict[str, str]]:
    if not CORPUS:
        return []
    scored = []
    q_lower = question.lower()
    for entry in CORPUS:
        score = sum(1 for token in q_lower.split() if token in entry.title.lower())
        if score == 0:
            for step in entry.steps:
                if any(token in step.lower() for token in q_lower.split()[:5]):
                    score += 1
                    break
        if score > 0:
            scored.append((score, entry))
    scored.sort(reverse=True, key=lambda x: x[0])
    snippets: List[Dict[str, str]] = []
    for idx, (_, entry) in enumerate(scored[:top_k]):
        snippet_text = "\n".join(entry.steps[:8])
        snippets.append({
            "id": idx + 1,
            "title": entry.title,
            "pdf_file": entry.pdf_file,
            "text": snippet_text,
        })
    return snippets or [
        {"id": 1, "title": "No protocols", "pdf_file": "n/a", "text": "No protocol snippets available."}
    ]


def format_snippets(snippets: List[Dict[str, str]]) -> str:
    lines = []
    for snip in snippets:
        lines.append(f"[{snip['id']}] {snip['title']} ({snip['pdf_file']})\n{snip['text']}\n")
    return "\n".join(lines)


def build_graph():
    graph = StateGraph(AgentState)

    def retrieve_node(state: AgentState) -> AgentState:
        snippets = retrieve_snippets(state["question"])
        state["snippets"] = snippets
        return state

    def compose_node(state: AgentState) -> AgentState:
        snippet_blob = format_snippets(state["snippets"])
        response = LLM_MODEL.invoke(PROMPT.format(question=state["question"], snippets=snippet_blob))
        state["answer"] = response
        return state

    graph.add_node("retrieve", retrieve_node)
    graph.add_node("compose", compose_node)
    graph.set_entry_point("retrieve")
    graph.add_edge("retrieve", "compose")
    graph.add_edge("compose", END)
    return graph.compile()


GRAPH = build_graph()


def run_protocol_agent(question: str) -> str:
    state: AgentState = {"question": question, "snippets": [], "answer": ""}
    final_state = GRAPH.invoke(state)
    return final_state["answer"]
