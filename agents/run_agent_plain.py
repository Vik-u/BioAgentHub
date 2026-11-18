#!/usr/bin/env python3
"""Compatibility wrapper for fabric/agents/run_agent_plain.py."""

from fabric.agents.run_agent_plain import *  # noqa: F401,F403


if __name__ == "__main__":
    from fabric.agents.run_agent_plain import app

    app()
