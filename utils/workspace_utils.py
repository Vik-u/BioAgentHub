#!/usr/bin/env python3
"""Workspace discovery and canonical path helpers."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Dict, List

PROJECT_ROOT = Path(__file__).resolve().parents[1]
WORKSPACES_ROOT = PROJECT_ROOT / "workspaces"
ATTIC_ROOT = PROJECT_ROOT / "attic"
DEFAULT_WORKSPACE_MAP = PROJECT_ROOT / "agents" / "workspace_map.json"


def _is_backup_name(name: str) -> bool:
    return name.startswith("workspaces_backup_")


def _is_deprecated_name(name: str) -> bool:
    return name.startswith("_") or "deprecated" in name


def _is_excluded_name(name: str) -> bool:
    return name == "all_topics"


def is_ignored_path(path: Path) -> bool:
    for part in path.parts:
        if part == ATTIC_ROOT.name:
            return True
        if _is_backup_name(part):
            return True
        if _is_deprecated_name(part):
            return True
        if _is_excluded_name(part):
            return True
    return False


def is_canonical_workspace(path: Path) -> bool:
    resolved = path.expanduser().resolve()
    if is_ignored_path(resolved):
        return False
    return resolved.parent == WORKSPACES_ROOT


def ensure_canonical_workspace(path: Path) -> Path:
    resolved = path.expanduser().resolve()
    if not is_canonical_workspace(resolved):
        raise ValueError(
            f"Workspace must be under {WORKSPACES_ROOT} and not in attic/backups/deprecated: {resolved}"
        )
    return resolved


def load_workspace_map(path: Path | None = None) -> Dict[str, Path]:
    map_path = path or DEFAULT_WORKSPACE_MAP
    if not map_path.exists():
        return {}
    raw = json.loads(map_path.read_text())
    mapping: Dict[str, Path] = {}
    for topic, value in raw.items():
        candidate = Path(value)
        if not candidate.is_absolute():
            candidate = PROJECT_ROOT / candidate
        candidate = candidate.resolve()
        if not is_canonical_workspace(candidate):
            raise ValueError(f"Non-canonical workspace mapping for {topic}: {candidate}")
        mapping[topic] = candidate
    return mapping


def list_workspaces(
    workspace_map_path: Path | None = None,
    workspace_root: Path | None = None,
) -> List[Path]:
    mapping = load_workspace_map(workspace_map_path)
    if mapping:
        return [mapping[topic] for topic in sorted(mapping)]
    root = (workspace_root or WORKSPACES_ROOT).resolve()
    if not root.exists():
        return []
    candidates = []
    for child in root.iterdir():
        if child.is_dir() and is_canonical_workspace(child):
            candidates.append(child)
    return sorted(candidates)


def list_topics(
    workspace_map_path: Path | None = None,
    workspace_root: Path | None = None,
) -> List[str]:
    mapping = load_workspace_map(workspace_map_path)
    if mapping:
        return sorted(mapping.keys())
    return [ws.name for ws in list_workspaces(workspace_root=workspace_root)]


def resolve_workspace_root(
    topic: str | None = None,
    workspace_root: Path | str | None = None,
    workspace_map_path: Path | None = None,
    allow_noncanonical: bool = False,
) -> Path:
    if workspace_root:
        resolved = Path(workspace_root).expanduser().resolve()
        return resolved if allow_noncanonical else ensure_canonical_workspace(resolved)
    env_root = os.environ.get("WORKSPACE_ROOT")
    if env_root:
        resolved = Path(env_root).expanduser().resolve()
        return resolved if allow_noncanonical else ensure_canonical_workspace(resolved)
    mapping = load_workspace_map(workspace_map_path)
    if topic and topic in mapping:
        return mapping[topic]
    if mapping:
        return mapping[sorted(mapping.keys())[0]]
    if topic:
        return ensure_canonical_workspace(WORKSPACES_ROOT / topic)
    workspaces = list_workspaces(workspace_root=WORKSPACES_ROOT)
    if workspaces:
        return workspaces[0]
    raise FileNotFoundError(f"No canonical workspaces found under {WORKSPACES_ROOT}")
