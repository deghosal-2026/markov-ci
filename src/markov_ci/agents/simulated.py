"""The offline simulated agent (docs/spec/0006-agent-adapters.md §2, ADR-0003).

Deterministic and seeded: it decides whether to produce a patch by sampling from a
success curve, so demos and tests are reproducible with **zero API keys** and zero
tokens. Calibrating the curve to a category's priors lets the demo reproduce the
forecast the `analyze` command prints.
"""

from __future__ import annotations

import random
from collections.abc import Sequence

from markov_ci.agents.base import PatchProposal, RepairContext

_PATCH_DIFF = (
    "--- a/src/example.py\n"
    "+++ b/src/example.py\n"
    "@@ -1,3 +1,3 @@\n"
    " def broken():\n"
    "-    return 1\n"
    "+    return 2\n"
)


class SimulatedAgent:
    """A seeded, fixture-driven agent used as the default adapter."""

    id = "simulated"

    def __init__(self, success_curve: Sequence[float], seed: int = 0) -> None:
        self._success = tuple(float(value) for value in success_curve)
        self._seed = seed
        self._rng = random.Random(seed)

    def _probability(self, attempt: int) -> float:
        index = attempt - 1
        if 0 <= index < len(self._success):
            return self._success[index]
        return 0.0

    def repair(self, ctx: RepairContext) -> PatchProposal:
        """Propose a patch, succeeding with the probability of ``ctx.attempt``."""
        probability = self._probability(ctx.attempt)
        if self._rng.random() < probability:
            return PatchProposal(
                diff=_PATCH_DIFF,
                rationale=(
                    f"simulated {ctx.category.value} fix (attempt {ctx.attempt})"
                ),
                tokens_used=0,
                files_changed=("src/example.py",),
            )
        return PatchProposal(
            diff="",
            rationale="simulated: no valid patch produced",
            tokens_used=0,
        )
