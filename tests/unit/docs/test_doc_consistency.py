"""M12.19 (#83) — docs consistency, docs-are-tests.

- every ADR file is listed in the ADR index (and vice versa);
- every relative markdown link resolves (fail, not filter — a missing referenced path
  is a broken doc, not a skipped test);
- the golden absorption numbers quoted in the docs are the ones the model computes;
- the printed Erlang-C worked example matches ``erlang_c()``;
- no doc still maps the retired exit code ``2 -> a2`` (ADR-0017).
"""

from __future__ import annotations

import re
from pathlib import Path

from markov_ci.config import chain_from_config
from markov_ci.data import load_default_config
from markov_ci.model import absorption
from markov_ci.queueing import erlang_c

ROOT = Path(__file__).resolve().parents[3]
DOCS = ROOT / "docs"

_LINK = re.compile(r"\[[^\]]*\]\(([^)]+)\)")


def _markdown_files() -> list[Path]:
    return sorted(DOCS.rglob("*.md")) + [ROOT / "README.md"]


def _relative_targets(path: Path) -> list[str]:
    targets = []
    for raw in _LINK.findall(path.read_text(encoding="utf-8")):
        target = raw.strip().split("#", 1)[0]
        if not target or target.startswith(("http://", "https://", "mailto:", "/", "#")):
            continue
        targets.append(target)
    return targets


def test_adr_index_lists_every_adr() -> None:
    adr_dir = DOCS / "adr"
    files = {p.name for p in adr_dir.glob("[0-9][0-9][0-9][0-9]-*.md")}
    index = (adr_dir / "README.md").read_text(encoding="utf-8")
    missing = sorted(name for name in files if f"({name})" not in index)
    assert missing == [], f"ADRs missing from the index: {missing}"


def test_every_relative_doc_link_resolves() -> None:
    broken: list[str] = []
    for path in _markdown_files():
        for target in _relative_targets(path):
            resolved = (path.parent / target).resolve()
            if not resolved.exists():
                broken.append(f"{path.relative_to(ROOT)} -> {target}")
    assert broken == [], "broken documentation links:\n" + "\n".join(broken)


def _absorption_from(start: str) -> float:
    chain = chain_from_config(load_default_config(), category="default")
    matrix = absorption(chain)
    row = chain.transient.index(start)
    column = chain.absorbing.index("a1_ready_for_human_review")
    return float(matrix[row, column])


def test_golden_absorption_numbers_match_the_model() -> None:
    p_s0 = _absorption_from("s0_deterministic_verify")
    p_s1 = _absorption_from("s1_failure_triage")
    p_s2 = _absorption_from("s2_agent_reasoning#1")
    assert round(p_s0, 2) == 0.92
    assert round(p_s1, 2) == 0.54
    assert round(p_s2, 2) == 0.72


def test_docs_quote_the_golden_numbers() -> None:
    quick_start = (DOCS / "quick-start.md").read_text(encoding="utf-8")
    for value in ("0.92", "0.54", "0.72"):
        assert value in quick_start, f"quick-start.md does not quote {value}"
    model = (DOCS / "explanations" / "markov-model.md").read_text(encoding="utf-8")
    for value in ("0.92", "0.54", "0.72"):
        assert value in model, f"markov-model.md does not quote {value}"
    spec = (DOCS / "spec" / "0002-matrix-assembly.md").read_text(encoding="utf-8")
    for value in ("0.92", "0.72"):
        assert value in spec, f"spec 0002 does not quote {value}"


def test_erlang_worked_example_matches_the_code() -> None:
    metrics = erlang_c(lam=120, mu=30, c=5)
    assert round(metrics.p_wait, 3) == 0.554
    assert round(metrics.mean_wait * 60, 1) == 1.1
    assert round(metrics.p95_wait * 60, 1) == 4.8
    text = (DOCS / "explanations" / "queueing-theory.md").read_text(encoding="utf-8")
    assert "0.554" in text


def test_no_doc_maps_the_retired_exit_code() -> None:
    # ADR-0017: a2 exits 1; 2 is the Click usage-error code.
    suffix = re.compile(r"\b2(=|\s*\)|\s*->|\s*·\s*)+\s*(\"?)a2")
    offenders = [
        str(path.relative_to(ROOT))
        for path in _markdown_files()
        if suffix.search(path.read_text(encoding="utf-8"))
    ]
    assert offenders == [], f"docs still map 2 -> a2: {offenders}"
