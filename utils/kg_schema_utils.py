#!/usr/bin/env python3
"""Compatibility wrapper for forge/utils/kg_schema_utils.py."""

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from forge.utils.kg_schema_utils import *  # noqa: F401,F403,E402
