#!/usr/bin/env python3
"""VASP module test runner (Member 6).

Runs the VASP unit test suite that lives in vasp/tests/.
The suite covers: attribution, confidence, evidence, investigation,
report generator, and package imports, using synthetic/demo data only.
"""

import os
import sys
import unittest

REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)


def main():
    suite = unittest.defaultTestLoader.discover(
        start_dir=os.path.join(REPO_ROOT, "vasp", "tests"),
        pattern="test_*.py",
    )
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())