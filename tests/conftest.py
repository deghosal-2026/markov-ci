"""Test configuration.

Put `src/` on the import path so the suite runs from a checkout without an editable
install (mirrors the `pythonpath` setting added to pyproject.toml in M0.2).
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))
