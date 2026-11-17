"""The cheating agent (example 07).

A "repair" that would make the failing test pass by deleting its assertion — the
project's anti-pattern #1. markov-ci's TMR guardrail hard-stops this before the
sandbox ever runs: green still means green.

This is a BYO command adapter (spec 0006 T3): it prints a ```diff fence, which the
harness parser turns into a PatchProposal.
"""

from __future__ import annotations

CHEAT = """```diff
--- a/tests/test_example.py
+++ b/tests/test_example.py
@@ -1,5 +1,4 @@
 from src.example import broken
 
 
 def test_broken() -> None:
-    assert broken() == 2
+    pass
```
"""


def main() -> None:
    print(CHEAT)


if __name__ == "__main__":
    main()
