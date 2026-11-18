#!/usr/bin/env python3
"""Minimal run tracking for audits (private prompt logging + public summaries)."""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

PROJECT_ROOT = Path(__file__).resolve().parents[1]
AUDIT_ROOT = PROJECT_ROOT / "audit"
PRIVATE_ROOT = AUDIT_ROOT / "_private"


@dataclass
class RunRecord:
    run_id: str
    task_name: str
    started_at: str
    inputs: Dict[str, Any]
    prompt_text: str
    artifacts: List[Dict[str, str]]
    summary_bullets: List[str]
    git_diff_summary: str | None
    finished_at: str | None


def _now_stamp() -> str:
    return datetime.utcnow().strftime("%Y%m%d_%H%M%S")


def _run_dir(run_id: str) -> Path:
    return PRIVATE_ROOT / run_id


def _run_path(run_id: str) -> Path:
    return _run_dir(run_id) / "run.json"


def start_run(task_name: str, inputs_dict: Dict[str, Any], prompt_text: str) -> Tuple[str, Path]:
    """Start a run and persist raw prompt/inputs under audit/_private.

    Returns (run_id, public_audit_dir_path). Public dir is not created here.
    """
    run_id = _now_stamp()
    PRIVATE_ROOT.mkdir(parents=True, exist_ok=True)
    run_dir = _run_dir(run_id)
    run_dir.mkdir(parents=True, exist_ok=True)
    record = RunRecord(
        run_id=run_id,
        task_name=task_name,
        started_at=datetime.utcnow().isoformat() + "Z",
        inputs=inputs_dict or {},
        prompt_text=prompt_text or "",
        artifacts=[],
        summary_bullets=[],
        git_diff_summary=None,
        finished_at=None,
    )
    _run_path(run_id).write_text(json.dumps(asdict(record), indent=2, ensure_ascii=False))
    return run_id, AUDIT_ROOT / run_id


def log_artifact(run_id: str, filepath: str, short_description: str) -> None:
    path = _run_path(run_id)
    if not path.exists():
        return
    record = json.loads(path.read_text())
    record.setdefault("artifacts", []).append(
        {"path": filepath, "description": short_description}
    )
    path.write_text(json.dumps(record, indent=2, ensure_ascii=False))


def finalize_run(run_id: str, summary_bullets: List[str], git_diff_summary_if_any: str | None) -> None:
    path = _run_path(run_id)
    if not path.exists():
        return
    record = json.loads(path.read_text())
    record["summary_bullets"] = summary_bullets or []
    record["git_diff_summary"] = git_diff_summary_if_any
    record["finished_at"] = datetime.utcnow().isoformat() + "Z"
    path.write_text(json.dumps(record, indent=2, ensure_ascii=False))


def append_private_metrics(run_id: str, payload: Dict[str, Any]) -> None:
    path = _run_dir(run_id) / "metrics.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")
