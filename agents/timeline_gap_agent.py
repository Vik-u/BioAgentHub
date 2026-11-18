#!/usr/bin/env python3
"""Compatibility wrapper for fabric/agents/timeline_gap_agent.py."""

from fabric.agents.timeline_gap_agent import *  # noqa: F401,F403


if __name__ == "__main__":
    from fabric.agents.timeline_gap_agent import main

    main()
