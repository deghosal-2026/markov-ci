"""JUnit XML parsing (docs/spec/0010-triage.md §1).

Triage input is whatever the user's runner emits, and it is often imperfect.
Malformed XML therefore degrades to a best-effort regex recovery with a recorded
warning — it never raises and never crashes the pipeline.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import ClassVar

_KINDS = ("failure", "error", "skipped")

_TESTCASE = re.compile(r"<testcase\b([^>]*?)(?:/>|>(.*?)</testcase>)", re.DOTALL)
_NAME = re.compile(r"""\bname\s*=\s*["']([^"']*)["']""")
_KIND = re.compile(r"<(failure|error|skipped)\b([^>]*?)/?>", re.DOTALL)
_MESSAGE = re.compile(r"""\bmessage\s*=\s*["']([^"']*)["']""")


@dataclass(frozen=True, slots=True)
class TestFailure:
    """A single non-passing test."""

    __test__: ClassVar[bool] = False  # keep pytest from collecting this dataclass

    name: str
    message: str
    kind: str


@dataclass(frozen=True, slots=True)
class JUnitReport:
    """The parsed result of a JUnit document."""

    failures: tuple[TestFailure, ...]
    warnings: tuple[str, ...]


def _localname(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _from_element_tree(text: str) -> JUnitReport:
    root = ET.fromstring(text)  # noqa: S314 - trusted CI artefact, hardened by fallback
    failures: list[TestFailure] = []
    for element in root.iter():
        if _localname(element.tag) != "testcase":
            continue
        name = element.get("name", "")
        for child in element:
            kind = _localname(child.tag)
            if kind not in _KINDS:
                continue
            message = child.get("message") or (child.text or "").strip()
            failures.append(TestFailure(name=name, message=message, kind=kind))
    return JUnitReport(failures=tuple(failures), warnings=())


def _from_regex(text: str, warning: str) -> JUnitReport:
    failures: list[TestFailure] = []
    for match in _TESTCASE.finditer(text):
        body = match.group(2) or match.group(1)
        name_match = _NAME.search(match.group(1))
        name = name_match.group(1) if name_match else ""
        kind_match = _KIND.search(body)
        if kind_match is None:
            continue
        message_match = _MESSAGE.search(kind_match.group(2))
        message = message_match.group(1) if message_match else ""
        failures.append(
            TestFailure(name=name, message=message, kind=kind_match.group(1)),
        )
    return JUnitReport(failures=tuple(failures), warnings=(warning,))


def parse_junit(text: str) -> JUnitReport:
    """Parse a JUnit XML document into failures, never raising on bad input."""
    if not text.strip():
        return JUnitReport(failures=(), warnings=("empty JUnit document",))
    try:
        return _from_element_tree(text)
    except ET.ParseError as exc:
        return _from_regex(text, f"malformed JUnit XML: {exc}")
