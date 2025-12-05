#!/usr/bin/env python3
"""Config-driven wrapper around local (Ollama) or remote LLM APIs."""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any, Dict, Optional

import requests
from requests import RequestException

CONFIG_PATH = Path(__file__).resolve().parents[1] / "config" / "llm_config.json"


def _load_config() -> Dict[str, Any]:
    if CONFIG_PATH.exists():
        return json.loads(CONFIG_PATH.read_text())
    return {
        "backend": "ollama",
        "model": os.environ.get("OLLAMA_MODEL", "gpt-oss:20b"),
        "host": os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434"),
        "temperature": 0.2,
    }


CONFIG = _load_config()
BACKEND = CONFIG.get("backend", "ollama").lower()
DEFAULT_MODEL = CONFIG.get("model", "gpt-oss:20b")
TEMPERATURE = float(CONFIG.get("temperature", 0.2) or 0.2)


class LocalLLMError(RuntimeError):
    """Raised when the configured LLM endpoint fails."""


def _ping_ollama(host: str, timeout: float = 5.0) -> None:
    try:
        response = requests.get(f"{host}/api/tags", timeout=timeout)
    except RequestException as exc:  # pragma: no cover - network
        raise LocalLLMError(f"Ollama backend {host} unreachable: {exc}") from exc
    if response.status_code != 200:
        raise LocalLLMError(f"Ollama ping failed ({response.status_code}): {response.text}")


def _call_ollama(prompt: str, model: str) -> str:
    host = CONFIG.get("host", "http://127.0.0.1:11434")
    _ping_ollama(host)
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": TEMPERATURE},
    }
    url = f"{host}/api/generate"
    last_exc: Optional[Exception] = None
    for attempt in range(3):
        try:
            response = requests.post(url, json=payload, timeout=300)
        except RequestException as exc:  # pragma: no cover - network
            last_exc = exc
        else:
            if response.status_code == 200:
                data: Dict[str, str] = response.json()
                return data.get("response", "").strip()
            last_exc = LocalLLMError(f"Ollama error {response.status_code}: {response.text}")
        time.sleep(2 * (attempt + 1))
    raise LocalLLMError(f"Ollama request failed after retries: {last_exc}") from last_exc


def _call_openai(prompt: str, model: str) -> str:
    api_base = CONFIG.get("api_base", "https://api.openai.com/v1")
    api_key_env = CONFIG.get("api_key_env", "OPENAI_API_KEY")
    api_key = os.environ.get(api_key_env)
    if not api_key:
        raise LocalLLMError(f"Missing API key in environment variable {api_key_env}")
    url = f"{api_base.rstrip('/')}/chat/completions"
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a helpful PETase research assistant."},
            {"role": "user", "content": prompt},
        ],
        "temperature": TEMPERATURE,
    }
    headers = {"Authorization": f"Bearer {api_key}"}
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=120)
    except RequestException as exc:  # pragma: no cover - network
        raise LocalLLMError(f"OpenAI request failed: {exc}") from exc
    if response.status_code != 200:
        raise LocalLLMError(f"OpenAI error {response.status_code}: {response.text}")
    data = response.json()
    return data["choices"][0]["message"]["content"].strip()


def generate(prompt: str, model: Optional[str] = None, temperature: Optional[float] = None) -> str:
    """Dispatch a prompt to the configured backend."""
    active_model = model or DEFAULT_MODEL
    if temperature is not None:
        global TEMPERATURE
        TEMPERATURE = temperature

    if BACKEND == "ollama":
        return _call_ollama(prompt, active_model)
    if BACKEND in {"openai", "azure-openai"}:
        return _call_openai(prompt, active_model)
    raise LocalLLMError(f"Unsupported backend: {BACKEND}")
