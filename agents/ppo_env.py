#!/usr/bin/env python3
"""Gymnasium environment wrapper around the PETase retrieval loop for PPO training."""

from __future__ import annotations

import random
from pathlib import Path
from typing import List, Sequence

import gymnasium as gym
import numpy as np

from agents.rl_rag_agent import ACTIONS, RetrievalEnvironment, get_backend

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_QUESTIONS = [
    "What mutations improve PETase thermostability?",
    "Which engineered PETases target semi-crystalline PET?",
    "At what temperatures does ThermoPETase remain active?",
]


def load_questions(path: Path | None) -> List[str]:
    if path and path.exists():
        return [line.strip() for line in path.read_text().splitlines() if line.strip()]
    return DEFAULT_QUESTIONS


class RetrievalGymEnv(gym.Env):
    metadata = {"render_modes": []}

    def __init__(self, questions: Sequence[str], use_llm: bool = False):
        super().__init__()
        self.questions = list(questions)
        if not self.questions:
            raise ValueError("Question list is empty.")
        self.use_llm = use_llm
        self.backend = get_backend()
        self.inner: RetrievalEnvironment | None = None
        self.question: str | None = None
        self.state = None
        self.rewards: List[float] = []

        self.action_space = gym.spaces.Discrete(len(ACTIONS))
        self.observation_space = gym.spaces.Box(low=0.0, high=1.0, shape=(3,), dtype=np.float32)

    def reset(self, *, seed: int | None = None, options: dict | None = None):
        super().reset(seed=seed)
        self.inner = RetrievalEnvironment(self.backend)
        self.question = random.choice(self.questions)
        self.state = self.inner.reset(self.question)
        self.rewards = []
        return self._obs(), {}

    def step(self, action_idx: int):
        assert self.inner is not None and self.state is not None
        action = ACTIONS[action_idx]
        self.state, reward, done, info = self.inner.step(action)
        self.rewards.append(reward)
        obs = self._obs()
        terminated = done
        truncated = False
        return obs, reward, terminated, truncated, {"info": info}

    def _obs(self) -> np.ndarray:
        assert self.inner is not None
        state = self.inner.state
        if state is None:
            return np.zeros(3, dtype=np.float32)
        context = min(len(state.context), 10) / 10.0
        graph = min(len(state.graph_nodes), 10) / 10.0
        steps = min(state.steps, 6) / 6.0
        return np.array([context, graph, steps], dtype=np.float32)
