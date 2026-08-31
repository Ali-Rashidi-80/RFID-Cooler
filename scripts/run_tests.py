#!/usr/bin/env python3
"""Run host-side unit/smoke tests (honest — stubs MicroPython, real assertions)."""

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SUITE_PATH = ROOT / "test" / "host" / "test_suite.py"


def _load_suite_module():
    host_dir = str(SUITE_PATH.parent)
    if host_dir not in sys.path:
        sys.path.insert(0, host_dir)
    spec = importlib.util.spec_from_file_location("rfid_cooler_host_tests", SUITE_PATH)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {SUITE_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["rfid_cooler_host_tests"] = module
    spec.loader.exec_module(module)
    return module


def main() -> int:
    suite_module = _load_suite_module()
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(suite_module)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    if not result.wasSuccessful():
        print("TESTS FAILED")
        return 1
    print(f"TESTS OK — {result.testsRun} tests")
    return 0


if __name__ == "__main__":
    sys.exit(main())
