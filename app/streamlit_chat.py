#!/usr/bin/env python3
"""Streamlit UI for chatting with the PETase RL/RAG agent."""

from __future__ import annotations

import json
from pathlib import Path
import sys

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agents.rl_rag_agent import run_agent  # noqa: E402

st.set_page_config(
    page_title="PETase Research Copilot",
    page_icon="🧪",
    layout="wide",
)

st.title("🧪 PETase Research Copilot (Streamlit)")
st.caption("Ask PETase literature questions using either the RL-only agent or the RL + GPT-OSS hybrid.")

if "history" not in st.session_state:
    st.session_state.history = []

col_mode, col_seed = st.columns([2, 1])
mode = col_mode.radio("Agent Mode", ["RL Only", "RL + GPT-OSS"], horizontal=True)
seed = col_seed.number_input("Random Seed", value=7, step=1)

question = st.text_area(
    "Question",
    placeholder="e.g., Which engineered PETases target semi-crystalline PET?",
    height=120,
)

col_submit, col_clear = st.columns([1, 1])
ask_clicked = col_submit.button("Ask")
clear_clicked = col_clear.button("Clear History")

if clear_clicked:
    st.session_state.history = []

if ask_clicked and question.strip():
    with st.spinner("Thinking..."):
        result = run_agent(question.strip(), use_llm=(mode == "RL + GPT-OSS"), seed=int(seed))
    answer = result["answer"]
    meta = {
        "mode": mode,
        "rewards": result["rewards"],
        "steps": result["trajectory"],
    }
    st.session_state.history.insert(
        0,
        {
            "question": question.strip(),
            "answer": answer,
            "meta": meta,
        },
    )

if not st.session_state.history:
    st.info("Ask a question above to get started.")
else:
    st.subheader("Conversation History")
    for entry in st.session_state.history:
        with st.expander(entry["question"], expanded=False):
            st.markdown(entry["answer"])
            st.code(json.dumps(entry["meta"], indent=2), language="json")

st.markdown("---")
st.caption(
    "Backend: PETase corpus (46 papers) → heuristic KG → RL policy for retrieval → optional GPT-OSS summarizer."
)
