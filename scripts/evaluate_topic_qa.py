#!/usr/bin/env python3
"""
Lightweight QA evaluation harness for any topic workspace.

Usage:
  python scripts/evaluate_topic_qa.py --workspace workspaces/petase --questions data/questions.txt --out logs/qa_eval_petase.jsonl

Each question line is run through rl_rag_agent (LLM optional). Outputs JSONL with answer, citations, and metrics.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Dict, Any

from agents import rl_rag_agent


def run_eval(workspace: Path, questions: Path, out_path: Path, use_llm: bool) -> None:
    os.environ["WORKSPACE_ROOT"] = str(workspace.resolve())
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with questions.open() as handle, out_path.open("w", encoding="utf-8") as out:
        for line in handle:
            q = line.strip()
            if not q:
                continue
            result: Dict[str, Any] = rl_rag_agent.run_agent(q, use_llm=use_llm)
            out.write(json.dumps({"question": q, **result}, ensure_ascii=False) + "\n")
            out.flush()
    print(f"Saved QA eval to {out_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, required=True, help="Workspace root with KG and vector store.")
    parser.add_argument("--questions", type=Path, required=True, help="Text file with one question per line.")
    parser.add_argument("--out", type=Path, required=True, help="Output JSONL path.")
    parser.add_argument("--llm", action="store_true", help="Use LLM summarizer (costly). Default: off.")
    args = parser.parse_args()
    run_eval(args.workspace, args.questions, args.out, use_llm=args.llm)


if __name__ == "__main__":
    main()
