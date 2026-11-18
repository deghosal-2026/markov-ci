r"""Diff path parser (docs/spec/0005-guardrails.md §1, ADR-0009).

The engine never trusts a patch's declared file list: it derives the paths a diff
touches from the diff itself. This parser handles the four places git records a
path — ``diff --git``, ``---`` / ``+++``, ``rename from/to`` and ``copy from/to`` —
and collects **both** the old and the new path, so a rename or delete cannot smuggle
a change past the allowlist.

Rules (spec 0005 §1):

- text after a tab is dropped (git appends timestamps there);
- ``/dev/null`` is skipped;
- the first path component is stripped (``-p1`` — git's ``a/`` / ``b/`` prefix);
- git C-style quoted paths (``\\``, ``\"``, ``\t``, ``\n``, octal ``\NNN``) are
  unescaped before matching.
"""

from __future__ import annotations

_C_ESCAPES = {
    "\\": "\\",
    '"': '"',
    "t": "\t",
    "n": "\n",
    "r": "\r",
    "a": "\a",
    "b": "\b",
    "f": "\f",
    "v": "\v",
}

# Keywords that carry a single path in a diff header.
_FROM_TO_PREFIXES = ("rename from ", "rename to ", "copy from ", "copy to ")


def _unescape_c(text: str) -> str:
    r"""Unescape git's C-style quoting (``\\``, ``\"``, ``\t``, ``\n``, octal ``\NNN``)."""
    out: list[str] = []
    index = 0
    length = len(text)
    while index < length:
        char = text[index]
        if char != "\\":
            out.append(char)
            index += 1
            continue
        index += 1
        if index >= length:  # a trailing lone backslash
            out.append("\\")
            break
        escaped = text[index]
        if escaped in "01234567":
            end = index
            while end < length and end < index + 3 and text[end] in "01234567":
                end += 1
            out.append(chr(int(text[index:end], 8)))
            index = end
        else:
            out.append(_C_ESCAPES.get(escaped, escaped))
            index += 1
    return "".join(out)


def _split_quoted(text: str) -> list[str]:
    """Split ``text`` on spaces, keeping git-quoted ``"..."`` tokens intact."""
    tokens: list[str] = []
    index = 0
    length = len(text)
    while index < length:
        while index < length and text[index] == " ":
            index += 1
        if index >= length:
            break
        if text[index] == '"':
            index += 1
            buffer: list[str] = []
            while index < length and text[index] != '"':
                if text[index] == "\\" and index + 1 < length:
                    buffer.append(text[index : index + 2])
                    index += 2
                else:
                    buffer.append(text[index])
                    index += 1
            index += 1  # consume the closing quote
            tokens.append('"' + "".join(buffer) + '"')
        else:
            start = index
            while index < length and text[index] != " ":
                index += 1
            tokens.append(text[start:index])
    return tokens


def normalize_path(token: str) -> str | None:
    """Return the repo-relative path for one raw token, or ``None`` for ``/dev/null``."""
    token = token.strip()
    if len(token) >= 2 and token[0] == '"' and token[-1] == '"':
        token = _unescape_c(token[1:-1])
    if token == "/dev/null" or not token:
        return None
    # `-p1`: strip git's leading `a/` or `b/` path component.
    if token[:2] in {"a/", "b/"}:
        token = token[2:]
    return token or None


def parse_diff_paths(diff: str) -> tuple[str, ...]:
    """Return the repo-relative paths a unified diff touches (both sides, deduped)."""
    found: list[str] = []
    for line in diff.splitlines():
        tokens: list[str] = []
        if line.startswith("diff --git "):
            tokens = _split_quoted(line[len("diff --git ") :])
        elif line.startswith(("--- ", "+++ ")):
            tokens = [line[4:].split("\t", 1)[0]]
        else:
            for prefix in _FROM_TO_PREFIXES:
                if line.startswith(prefix):
                    tokens = [line[len(prefix) :]]
                    break
        for token in tokens:
            path = normalize_path(token)
            if path is not None:
                found.append(path)
    return tuple(dict.fromkeys(found))


def symlink_paths(diff: str) -> tuple[str, ...]:
    """Return the paths a diff turns into a symlink (``mode 120000``), spec 0005 §1.

    A symlink can point outside the allowlist (``src/link -> /etc/passwd``), so a
    symlink creation is denied and recorded rather than matched by path alone.
    """
    found: list[str] = []
    current: str | None = None
    is_symlink = False
    for line in diff.splitlines():
        if line.startswith("diff --git "):
            if is_symlink and current is not None:
                found.append(current)
            current = None
            is_symlink = False
            tokens = _split_quoted(line[len("diff --git ") :])
            if tokens:
                current = normalize_path(tokens[-1])
        elif line.startswith(("new file mode 120000", "new mode 120000")):
            is_symlink = True
    if is_symlink and current is not None:
        found.append(current)
    return tuple(dict.fromkeys(found))


__all__ = ["normalize_path", "parse_diff_paths", "symlink_paths"]
