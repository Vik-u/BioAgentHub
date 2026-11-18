#!/usr/bin/env python3
"""Shared output path helpers with a single configurable root."""

from __future__ import annotations

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_ROOT = PROJECT_ROOT / "outputs"


def output_root() -> Path:
    env_root = os.environ.get("BIOAGENT_OUTPUT_ROOT", "")
    root = Path(env_root).expanduser().resolve() if env_root else DEFAULT_OUTPUT_ROOT
    root.mkdir(parents=True, exist_ok=True)
    return root


def logs_dir() -> Path:
    path = output_root() / "logs"
    path.mkdir(parents=True, exist_ok=True)
    return path


def qa_dir() -> Path:
    path = output_root() / "qa_outputs"
    path.mkdir(parents=True, exist_ok=True)
    return path


def biofoundry_dir() -> Path:
    path = output_root() / "biofoundry_output"
    path.mkdir(parents=True, exist_ok=True)
    return path


def reports_dir() -> Path:
    path = output_root() / "reports"
    path.mkdir(parents=True, exist_ok=True)
    return path
