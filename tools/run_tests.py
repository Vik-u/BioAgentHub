#!/usr/bin/env python3
"""Custom test runner with per-test status output.

Usage:
  python tools/run_tests.py

Set TEST_COLOR=1 to enable ANSI colors.
"""

from __future__ import annotations

import os
import sys
import unittest


USE_COLOR = os.environ.get("TEST_COLOR", "0") == "1"


def _color(text: str, code: str) -> str:
    if not USE_COLOR:
        return text
    return f"\033[{code}m{text}\033[0m"


class StatusTextResult(unittest.TextTestResult):
    def addSuccess(self, test):
        super().addSuccess(test)
        self.stream.writeln(_color(f"[PASS] {test.id()}", "32"))

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self.stream.writeln(_color(f"[FAIL] {test.id()}", "31"))

    def addError(self, test, err):
        super().addError(test, err)
        self.stream.writeln(_color(f"[ERROR] {test.id()}", "31"))

    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        self.stream.writeln(_color(f"[SKIP] {test.id()} - {reason}", "33"))


class StatusTextRunner(unittest.TextTestRunner):
    resultclass = StatusTextResult


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.discover("tests")
    runner = StatusTextRunner(verbosity=0)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
