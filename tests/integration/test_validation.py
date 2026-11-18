"""M6.3 (#31) — validator apply-and-test (docs/spec/0011-engine-runtime.md §2).

These are integration tests: they drive a real (tiny) git repository through the
worktree lifecycle.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from collections.abc import Sequence
from pathlib import Path

import pytest

from markov_ci.engine.validation import ValidationResult, WorktreeValidator

GOOD_DIFF = """\
--- a/app.py
+++ b/app.py
@@ -1 +1 @@
-VALUE = 1
+VALUE = 2
"""

BAD_DIFF = """\
--- a/app.py
+++ b/app.py
@@ -1 +1 @@
-VALUE = 1
+VALUE = 3
"""

MALFORMED = "this is not a diff at all\n"


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    path = tmp_path / "repo"
    path.mkdir()
    _git(path, "init", "-q")
    _git(path, "config", "user.email", "test@example.com")
    _git(path, "config", "user.name", "Test")
    (path / "app.py").write_text("VALUE = 1\n", encoding="utf-8")
    (path / "check.py").write_text(
        "import app\nassert app.VALUE == 2, 'not fixed'\n",
        encoding="utf-8",
    )
    _git(path, "add", "-A")
    _git(path, "commit", "-qm", "init")
    return path


def _test_command() -> list[str]:
    return [sys.executable, "check.py"]


def test_good_patch_applies_and_passes(repo: Path, tmp_path: Path) -> None:
    with WorktreeValidator(repo, root=tmp_path / "validator") as validator:
        result = validator.apply_and_test(GOOD_DIFF, _test_command())
    assert isinstance(result, ValidationResult)
    assert result.applied is True
    assert result.passed is True


def test_bad_patch_applies_but_fails(repo: Path, tmp_path: Path) -> None:
    with WorktreeValidator(repo, root=tmp_path / "validator") as validator:
        result = validator.apply_and_test(BAD_DIFF, _test_command())
    assert result.applied is True
    assert result.passed is False


def test_malformed_patch_does_not_apply(repo: Path, tmp_path: Path) -> None:
    with WorktreeValidator(repo, root=tmp_path / "validator") as validator:
        result = validator.apply_and_test(MALFORMED, _test_command())
    assert result.applied is False
    assert result.passed is False


DENIED_DIFF = """\
diff --git a/.github/workflows/evil.yml b/.github/workflows/evil.yml
new file mode 100644
--- /dev/null
+++ b/.github/workflows/evil.yml
@@ -0,0 +1 @@
+name: evil
"""


def test_post_apply_allowlist_denies_a_ci_config_before_running_tests(
    repo: Path, tmp_path: Path,
) -> None:
    # M13.9 (#93): git is the source of truth — the allowlist is re-run on
    # `git diff --name-status -M` before the test command.
    marker = tmp_path / "ran"
    command = [sys.executable, "-c", f"open({str(marker)!r}, 'w').write('x')"]
    with WorktreeValidator(repo, root=tmp_path / "validator") as validator:
        result = validator.apply_and_test(DENIED_DIFF, command)
    assert result.applied is True
    assert result.passed is False
    assert result.guardrail_report
    assert not marker.exists(), "the test command ran despite a denied path"


def test_post_apply_allowlist_permits_a_source_patch(repo: Path, tmp_path: Path) -> None:
    with WorktreeValidator(repo, root=tmp_path / "validator") as validator:
        result = validator.apply_and_test(
            GOOD_DIFF, _test_command(), allow_write=("app.py",),
        )
    assert result.applied is True
    assert result.passed is True
    assert result.guardrail_report == ()


def test_post_apply_allowlist_reports_a_path_outside_the_allowlist(
    repo: Path, tmp_path: Path,
) -> None:
    with WorktreeValidator(repo, root=tmp_path / "validator") as validator:
        result = validator.apply_and_test(
            GOOD_DIFF, _test_command(), allow_write=("src/**", "tests/**"),
        )
    assert result.passed is False
    assert any("app.py" in note for note in result.guardrail_report)


def test_the_repository_is_never_modified(repo: Path, tmp_path: Path) -> None:
    with WorktreeValidator(repo, root=tmp_path / "validator") as validator:
        validator.apply_and_test(GOOD_DIFF, _test_command())
    assert (repo / "app.py").read_text(encoding="utf-8") == "VALUE = 1\n"
    status = subprocess.run(
        ["git", "-C", str(repo), "status", "--porcelain"],
        check=True, capture_output=True, text=True,
    )
    assert status.stdout.strip() == ""


def test_validation_copies_are_cleaned_up(repo: Path, tmp_path: Path) -> None:
    root = tmp_path / "validator"
    with WorktreeValidator(repo, root=root) as validator:
        validator.apply_and_test(GOOD_DIFF, _test_command())
    assert not any(root.glob("clone-*"))
    listing = subprocess.run(
        ["git", "-C", str(repo), "worktree", "list", "--porcelain"],
        check=True, capture_output=True, text=True,
    )
    assert "clone-" not in listing.stdout


def test_validation_runs_in_a_clone_not_a_shared_worktree(
    repo: Path, tmp_path: Path,
) -> None:
    # M13.17 (#101): a worktree checkout has `.git` as a file pointing at the host
    # repo; a clone has a real `.git` directory.
    code = "import pathlib; print('DIR' if pathlib.Path('.git').is_dir() else 'FILE')"
    with WorktreeValidator(repo, root=tmp_path / "validator") as validator:
        result = validator.apply_and_test(
            GOOD_DIFF, [sys.executable, "-c", code], allow_write=("app.py",),
        )
    assert "DIR" in result.output


def test_validation_does_not_share_the_host_git_hooks(
    repo: Path, tmp_path: Path,
) -> None:
    (repo / ".git" / "hooks" / "pre-commit").write_text(
        "#!/bin/sh\nexit 1\n", encoding="utf-8",
    )
    code = (
        "import pathlib; "
        "print('HOOK' if pathlib.Path('.git/hooks/pre-commit').exists() else 'NO-HOOK')"
    )
    with WorktreeValidator(repo, root=tmp_path / "validator") as validator:
        result = validator.apply_and_test(
            GOOD_DIFF, [sys.executable, "-c", code], allow_write=("app.py",),
        )
    assert "NO-HOOK" in result.output


def test_cleanup_happens_even_when_the_test_command_explodes(repo: Path, tmp_path: Path) -> None:
    root = tmp_path / "validator"
    validator = WorktreeValidator(repo, root=root)
    result = validator.apply_and_test(GOOD_DIFF, [sys.executable, "-c", "import sys; sys.exit(7)"])
    validator.close()
    assert result.passed is False
    assert not any(root.glob("clone-*"))


def test_close_removes_the_root(repo: Path, tmp_path: Path) -> None:
    root = tmp_path / "validator"
    validator = WorktreeValidator(repo, root=root)
    validator.close()
    assert not root.exists() or not any(root.iterdir())



def _dump_env_command(out: Path) -> list[str]:
    return [
        sys.executable, "-c",
        f"import os,json; json.dump(dict(os.environ), open({str(out)!r}, 'w'))",
    ]


def test_the_test_command_runs_with_a_scrubbed_environment(
    repo: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    # M13.14 (#98): the validation child must not inherit host credentials.
    monkeypatch.setenv("GITHUB_TOKEN", "leaked")
    monkeypatch.setenv("MY_PROVIDER_KEY", "provider")
    out = tmp_path / "env.json"
    with WorktreeValidator(repo, root=tmp_path / "validator") as validator:
        result = validator.apply_and_test(
            GOOD_DIFF, _dump_env_command(out), allow_write=("app.py",),
        )
    assert result.passed is True
    data = json.loads(out.read_text(encoding="utf-8"))
    assert "GITHUB_TOKEN" not in data
    assert "MY_PROVIDER_KEY" not in data
    assert "PATH" in data
    assert data["HOME"] != os.environ["HOME"]


def test_config_listed_env_vars_reach_the_test_command(
    repo: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("MY_PROVIDER_KEY", "provider")
    out = tmp_path / "env.json"
    with WorktreeValidator(repo, root=tmp_path / "validator") as validator:
        validator.apply_and_test(
            GOOD_DIFF, _dump_env_command(out),
            allow_write=("app.py",), env_allow=("MY_PROVIDER_KEY",),
        )
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["MY_PROVIDER_KEY"] == "provider"


def test_captured_output_is_bounded_to_the_last_megabyte(
    repo: Path, tmp_path: Path,
) -> None:
    # M13.15 (#99): output is bounded to the last 1 MB.
    code = "import sys; sys.stdout.write('x' * 1_200_000); sys.stdout.write('SENTINEL')"
    with WorktreeValidator(repo, root=tmp_path / "validator") as validator:
        result = validator.apply_and_test(
            GOOD_DIFF, [sys.executable, "-c", code], allow_write=("app.py",),
        )
    assert len(result.output.encode("utf-8")) <= 1_048_576
    assert result.output.endswith("SENTINEL")


def test_timeout_kills_the_whole_process_group(repo: Path, tmp_path: Path) -> None:
    # a grandchild that outlives the direct child must be killed too
    marker = tmp_path / "grandchild-ran"
    grandchild = (
        "import time, pathlib; "
        f"time.sleep(1.0); pathlib.Path({str(marker)!r}).write_text('x')"
    )
    parent = (
        "import subprocess, sys, time; "
        f"subprocess.Popen([sys.executable, '-c', {grandchild!r}]); "
        "time.sleep(30)"
    )
    with WorktreeValidator(repo, root=tmp_path / "validator") as validator:
        result = validator.apply_and_test(
            GOOD_DIFF, [sys.executable, "-c", parent],
            allow_write=("app.py",), timeout=1,
        )
    assert result.passed is False
    assert "timed out" in result.output
    time.sleep(1.5)  # would have been long enough for a surviving grandchild
    assert not marker.exists(), "the grandchild survived the timeout"


def test_the_child_runs_with_resource_limits(repo: Path, tmp_path: Path) -> None:
    # M13.16 (#100): CPU, address-space and file-size limits are set in preexec_fn.
    code = (
        "import resource, json; "
        "print(json.dumps({"
        "'cpu': resource.getrlimit(resource.RLIMIT_CPU)[0], "
        "'as': resource.getrlimit(resource.RLIMIT_AS)[0], "
        "'fsize': resource.getrlimit(resource.RLIMIT_FSIZE)[0]}))"
    )
    with WorktreeValidator(repo, root=tmp_path / "validator") as validator:
        result = validator.apply_and_test(
            GOOD_DIFF, [sys.executable, "-c", code],
            allow_write=("app.py",), timeout=42,
        )
    limits = json.loads(result.output.strip().splitlines()[-1])
    import resource

    assert limits["fsize"] == 256 * 1024 * 1024
    assert limits["cpu"] == 42
    # Linux honours RLIMIT_AS; macOS refuses to lower it (best-effort).
    assert limits["as"] in (2 * 1024 * 1024 * 1024, resource.RLIM_INFINITY)


def test_container_mode_runs_the_command_via_docker(
    repo: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    # M13.18 (#102): with a container image configured, the command runs under
    # `docker run` with the isolation flags (the docker client is faked here).
    from markov_ci.engine import validation

    captured: dict[str, list[str]] = {}

    def fake_run(
        command: Sequence[str], *, cwd: object, env: object, timeout: object,
    ) -> tuple[int, str, bool]:
        captured["command"] = list(command)
        return 0, "ok", False

    monkeypatch.setattr(validation, "_run_bounded", fake_run)
    with WorktreeValidator(
        repo, root=tmp_path / "validator", container_image="python:3.12-slim",
    ) as validator:
        result = validator.apply_and_test(
            GOOD_DIFF, ["pytest", "-q"], allow_write=("app.py",),
        )
    argv = captured["command"]
    assert argv[:3] == ["docker", "run", "--rm"]
    assert "--network=none" in argv
    assert "--read-only" in argv
    assert argv[-2:] == ["pytest", "-q"]
    assert result.passed is True


def test_a_missing_test_command_is_reported_not_crashed(
    repo: Path, tmp_path: Path,
) -> None:
    with WorktreeValidator(repo, root=tmp_path / "validator") as validator:
        result = validator.apply_and_test(
            GOOD_DIFF, ["definitely-not-a-real-binary-xyz"], allow_write=("app.py",),
        )
    assert result.applied is True
    assert result.passed is False
    assert "could not run test command" in result.output


def test_a_rename_reports_both_paths(repo: Path, tmp_path: Path) -> None:
    diff = (
        "diff --git a/app.py b/renamed.py\n"
        "similarity index 100%\n"
        "rename from app.py\n"
        "rename to renamed.py\n"
    )
    with WorktreeValidator(repo, root=tmp_path / "validator") as validator:
        result = validator.apply_and_test(
            diff, [sys.executable, "-c", "print('ok')"], allow_write=("**",),
        )
    assert result.applied is True
    assert result.passed is True


def test_the_resource_limiter_sets_cpu_as_and_fsize(monkeypatch: pytest.MonkeyPatch) -> None:
    # the preexec_fn runs in the child, so exercise it directly (M13.16).
    import resource

    from markov_ci.engine.validation import _resource_limiter

    recorded: list[tuple[int, tuple[int, int]]] = []
    monkeypatch.setattr(resource, "setrlimit", lambda which, value: recorded.append((which, value)))
    limiter = _resource_limiter(42)
    assert limiter is not None
    limiter()
    assert len(recorded) == 3
    assert recorded[0] == (resource.RLIMIT_CPU, (42, 47))


def test_kill_process_group_falls_back_to_kill(monkeypatch: pytest.MonkeyPatch) -> None:
    import os as _os

    from markov_ci.engine import validation

    class FakeProcess:
        pid = 4321
        killed = False

        def kill(self) -> None:
            self.killed = True

    def _raise(*_args: object) -> None:
        raise ProcessLookupError

    monkeypatch.setattr(_os, "killpg", _raise)
    process = FakeProcess()
    validation._kill_process_group(process)  # type: ignore[arg-type]
    assert process.killed is True
