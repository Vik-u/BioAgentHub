#!/usr/bin/env python3
"""Preference-guided policy stub to mirror an RLHF-style controller."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

import numpy as np

from agents.rl_rag_agent import ACTIONS


@dataclass
class PreferenceGuidedPolicy:
    """Deterministic policy approximating RLHF-like preferences."""

    vector_threshold: float = 0.3
    graph_threshold: float = 0.35
    stop_threshold: float = 0.8

    def predict(
        self,
        observation,
        state=None,
        episode_start=None,
        deterministic: bool = True,
    ) -> Tuple[np.ndarray, None]:
        context = float(observation[0])
        graph = float(observation[1])
        steps = float(observation[2])

        if context < self.vector_threshold:
            action = "vector_search"
        elif graph < self.graph_threshold:
            action = "graph_expand"
        elif steps < 0.5:
            action = "graph_expand"
        elif graph >= self.graph_threshold and context >= self.vector_threshold:
            action = "summarize"
        else:
            action = "stop"

        if steps >= self.stop_threshold and context > 0:
            action = "stop"

        idx = ACTIONS.index(action)
        return np.array([idx]), None
