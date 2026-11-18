#!/usr/bin/env python3
"""Compatibility wrapper for fabric/agents/multi_agent_orchestrator.py."""

from fabric.agents.multi_agent_orchestrator import *  # noqa: F401,F403


if __name__ == "__main__":
    from fabric.agents.multi_agent_orchestrator import main

    main()
