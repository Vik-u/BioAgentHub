#!/usr/bin/env python3
"""Compatibility wrapper for fabric/agents/rag_agent.py."""

from fabric.agents.rag_agent import *  # noqa: F401,F403


if __name__ == "__main__":
    from fabric.agents.rag_agent import app

    app()
