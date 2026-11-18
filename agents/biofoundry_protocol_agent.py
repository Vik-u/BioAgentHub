#!/usr/bin/env python3
"""Compatibility wrapper for fabric/agents/biofoundry_protocol_agent.py."""

from fabric.agents.biofoundry_protocol_agent import *  # noqa: F401,F403


if __name__ == "__main__":
    from fabric.agents.biofoundry_protocol_agent import main

    main()
