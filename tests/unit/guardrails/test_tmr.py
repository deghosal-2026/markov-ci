"""M5.2 (#27) — test-modification-ratio checker (docs/spec/0005-guardrails.md §2)."""

from __future__ import annotations

from markov_ci.guardrails.tmr import TMRResult, check_test_modification

SRC_ONLY = """\
--- a/src/app.py
+++ b/src/app.py
@@ -1,2 +1,4 @@
 line
+new src line a
+new src line b
 line
"""

TEST_AND_SRC = """\
--- a/src/app.py
+++ b/src/app.py
@@ -1,2 +1,4 @@
 line
+new src line a
+new src line b
 line
--- a/tests/test_app.py
+++ b/tests/test_app.py
@@ -1,2 +1,3 @@
 line
+new test line
 line
"""

TEST_HEAVY = """\
--- a/src/app.py
+++ b/src/app.py
@@ -1,2 +1,2 @@
 line
-old
+new
--- a/tests/test_app.py
+++ b/tests/test_app.py
@@ -1,2 +1,6 @@
 line
+t1
+t2
+t3
+t4
 line
"""

ASSERTION_DELETED = """\
--- a/tests/test_app.py
+++ b/tests/test_app.py
@@ -1,3 +1,2 @@
 def test_x():
-    assert value == 1
     return
"""

ASSERTION_MOVED = """\
--- a/tests/test_app.py
+++ b/tests/test_app.py
@@ -1,4 +1,4 @@
 def test_a():
-    assert value == 1
+    assert value == 2
 def test_b():
-    assert other == 3
+    assert other == 3
"""


def test_source_only_change_is_clean() -> None:
    result = check_test_modification(SRC_ONLY)
    assert isinstance(result, TMRResult)
    assert result.stop is False
    assert result.mandatory_review is False
    assert result.src_lines_changed == 2


def test_balanced_change_is_clean() -> None:
    result = check_test_modification(TEST_AND_SRC)
    assert result.ratio == 0.5
    assert result.stop is False


def test_test_heavy_change_is_stopped() -> None:
    result = check_test_modification(TEST_HEAVY)
    assert result.ratio > 1.0
    assert result.stop is True
    assert result.mandatory_review is True


def test_assertion_deletion_is_stopped() -> None:
    result = check_test_modification(ASSERTION_DELETED)
    assert result.assertion_deletions == 1
    assert result.stop is True
    assert result.mandatory_review is True


def test_rewritten_assertion_is_not_a_deletion() -> None:
    result = check_test_modification(ASSERTION_MOVED)
    assert result.assertion_deletions == 0


def test_pure_test_change_with_no_src_is_stopped() -> None:
    result = check_test_modification(ASSERTION_MOVED)
    assert result.src_lines_changed == 0
    assert result.stop is True


def test_pure_test_change_reason_is_readable() -> None:
    result = check_test_modification(ASSERTION_MOVED)
    assert "pure test change with no source change" in result.reason
    assert "inf" not in result.reason


def test_empty_diff_is_clean() -> None:
    result = check_test_modification("")
    assert result.ratio == 0.0
    assert result.stop is False


def test_reason_is_present_when_stopped() -> None:
    assert check_test_modification(ASSERTION_DELETED).reason


def test_counts_test_and_src_lines() -> None:
    result = check_test_modification(TEST_AND_SRC)
    assert result.test_lines_changed == 1
    assert result.src_lines_changed == 2


def test_is_deterministic() -> None:
    assert check_test_modification(TEST_HEAVY) == check_test_modification(TEST_HEAVY)


DELETED_TEST = """\
diff --git a/tests/test_app.py b/tests/test_app.py
deleted file mode 100644
--- a/tests/test_app.py
+++ /dev/null
@@ -1,3 +0,0 @@
-def test_x():
-    assert value == 1
-    return
"""

DELETED_SRC = """\
diff --git a/src/app.py b/src/app.py
deleted file mode 100644
--- a/src/app.py
+++ /dev/null
@@ -1,2 +0,0 @@
-value = 1
-other = 2
"""

RATIO_EXACTLY_ONE = """\
--- a/src/app.py
+++ b/src/app.py
@@ -1 +1,2 @@
 line
+src
--- a/tests/test_app.py
+++ b/tests/test_app.py
@@ -1 +1,2 @@
 line
+test
"""


def test_deleted_test_file_is_classified_by_its_original_path() -> None:
    # M13.11 (#95): a deleted file is classified by its *original* path, so a
    # deleted test file counts as test lines (not as /dev/null source lines).
    result = check_test_modification(DELETED_TEST)
    assert result.test_lines_changed == 3
    assert result.src_lines_changed == 0
    assert result.stop is True


def test_deleted_source_file_is_classified_as_source() -> None:
    result = check_test_modification(DELETED_SRC)
    assert result.src_lines_changed == 2
    assert result.test_lines_changed == 0
    assert result.stop is False


def test_deleted_test_assertion_is_a_deletion() -> None:
    assert check_test_modification(DELETED_TEST).assertion_deletions == 1


def test_ratio_of_exactly_one_is_not_stopped() -> None:
    # spec 0005 §2: the hard stop is tmr > 1.0, so exactly 1.0 is allowed.
    result = check_test_modification(RATIO_EXACTLY_ONE)
    assert result.ratio == 1.0
    assert result.stop is False
