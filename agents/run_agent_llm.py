#!/usr/bin/env python3
"""Compatibility wrapper for fabric/agents/run_agent_llm.py."""

from fabric.agents.run_agent_llm import *  # noqa: F401,F403


if __name__ == "__main__":
    from fabric.agents.run_agent_llm import app

    app()
