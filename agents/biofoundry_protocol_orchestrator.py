#!/usr/bin/env python3
"""Compatibility wrapper for fabric/agents/biofoundry_protocol_orchestrator.py."""

from fabric.agents.biofoundry_protocol_orchestrator import *  # noqa: F401,F403


if __name__ == "__main__":
    from fabric.agents.biofoundry_protocol_orchestrator import main

    main()
