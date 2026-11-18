#!/usr/bin/env python3
"""Compatibility wrapper for fabric/agents/timeline_summarizer.py."""

from fabric.agents.timeline_summarizer import *  # noqa: F401,F403


if __name__ == "__main__":
    from fabric.agents.timeline_summarizer import main

    main()
