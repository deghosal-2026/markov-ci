"""M13.7 (#91) — diff path parser (docs/spec/0005-guardrails.md §1, ADR-0009)."""

from __future__ import annotations

from markov_ci.guardrails.diffpaths import parse_diff_paths

SIMPLE = (
    "diff --git a/src/example.py b/src/example.py\n"
    "index 1111111..2222222 100644\n"
    "--- a/src/example.py\n"
    "+++ b/src/example.py\n"
    "@@ -1 +1 @@\n"
    "-old\n"
    "+new\n"
)

RENAME = (
    "diff --git a/src/old.py b/src/new.py\n"
    "similarity index 90%\n"
    "rename from src/old.py\n"
    "rename to src/new.py\n"
)

COPY = (
    "diff --git a/src/a.py b/src/b.py\n"
    "similarity index 100%\n"
    "copy from src/a.py\n"
    "copy to src/b.py\n"
)


def test_modification_returns_the_path() -> None:
    assert parse_diff_paths(SIMPLE) == ("src/example.py",)


def test_rename_returns_both_old_and_new_paths() -> None:
    assert parse_diff_paths(RENAME) == ("src/old.py", "src/new.py")


def test_copy_returns_both_old_and_new_paths() -> None:
    assert parse_diff_paths(COPY) == ("src/a.py", "src/b.py")


def test_new_file_skips_dev_null() -> None:
    diff = "diff --git a/src/new.py b/src/new.py\n--- /dev/null\n+++ b/src/new.py\n"
    assert parse_diff_paths(diff) == ("src/new.py",)


def test_deleted_file_skips_dev_null() -> None:
    diff = "diff --git a/src/gone.py b/src/gone.py\n--- a/src/gone.py\n+++ /dev/null\n"
    assert parse_diff_paths(diff) == ("src/gone.py",)


def test_text_after_a_tab_is_dropped() -> None:
    diff = "--- a/src/x.py\t2026-01-01 00:00:00\n+++ b/src/x.py\t2026-01-01 00:00:00\n"
    assert parse_diff_paths(diff) == ("src/x.py",)


def test_quoted_octal_escaped_path_is_unescaped() -> None:
    diff = 'diff --git "a/\\056github/workflows/ci.yml" "b/\\056github/workflows/ci.yml"\n'
    assert parse_diff_paths(diff) == (".github/workflows/ci.yml",)


def test_quoted_tab_escape_is_unescaped() -> None:
    diff = 'diff --git "a/src/tab\\tname.py" "b/src/tab\\tname.py"\n'
    assert parse_diff_paths(diff) == ("src/tab\tname.py",)


def test_quoted_backslash_escape_is_unescaped() -> None:
    diff = 'diff --git "a/src/back\\\\slash.py" "b/src/back\\\\slash.py"\n'
    assert parse_diff_paths(diff) == ("src/back\\slash.py",)


def test_quoted_quote_escape_is_unescaped() -> None:
    diff = 'diff --git "a/src/quo\\"te.py" "b/src/quo\\"te.py"\n'
    assert parse_diff_paths(diff) == ('src/quo"te.py',)


def test_quoted_path_with_a_space_stays_one_path() -> None:
    diff = 'diff --git "a/src/my file.py" "b/src/my file.py"\n'
    assert parse_diff_paths(diff) == ("src/my file.py",)


def test_both_sides_of_a_rename_are_collected() -> None:
    # a rename out of the allowlist into it must still surface the source path
    diff = (
        "diff --git a/docs/secret.md b/src/secret.md\n"
        "rename from docs/secret.md\n"
        "rename to src/secret.md\n"
    )
    assert parse_diff_paths(diff) == ("docs/secret.md", "src/secret.md")


def test_dev_null_only_yields_no_paths() -> None:
    assert parse_diff_paths("--- /dev/null\n+++ /dev/null\n") == ()


def test_paths_are_deduplicated_in_order() -> None:
    diff = SIMPLE + "--- a/src/example.py\n+++ b/src/example.py\n"
    assert parse_diff_paths(diff) == ("src/example.py",)


def test_empty_diff_yields_no_paths() -> None:
    assert parse_diff_paths("") == ()


def test_quoted_and_unquoted_tokens_are_both_parsed() -> None:
    diff = 'diff --git "a/my file.py" b/my-file.py\n'
    assert parse_diff_paths(diff) == ("my file.py", "my-file.py")


def test_two_symlink_blocks_are_both_reported() -> None:
    from markov_ci.guardrails.diffpaths import symlink_paths

    diff = (
        "diff --git a/link1 b/link1\nnew file mode 120000\n"
        "diff --git a/link2 b/link2\nnew file mode 120000\n"
    )
    assert symlink_paths(diff) == ("link1", "link2")
