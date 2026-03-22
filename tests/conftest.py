"""
Ensure repo root is on sys.path so `import app` and `import trialmatch` work in CI and locally.
pytest.ini also sets pythonpath = . (pytest 7+); this is a fallback for edge cases.
"""
from __future__ import annotations

import pathlib
import sys

_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
