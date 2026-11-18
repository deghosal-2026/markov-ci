"""M4.3 (#24) — headless harness adapter (docs/spec/0006 §3, ADR-0007/ADR-0016).

M13.1 (#85) — argv-only invocation: the template is split with `shlex.split`
*before* `%PROMPT%` is substituted, the prompt becomes a single argv element, and
the process runs with `shell=False` (ADR-0016).

All tests inject a fake runner, so they are fully offline.
"""

from __future__ import annotations

import os
import stat
import subprocess
from collections.abc import Sequence
from pathlib import Path

import pytest

from markov_ci.agents import AgentAdapter, PatchProposal, RepairContext
from markov_ci.agents.harness import (
    HarnessAgent,
    HarnessError,
    HarnessSpec,
    HarnessTimeout,
    Runner,
    parse_harness_output,
)
from markov_ci.triage import FailureCategory

FENCED = """some chatter
```diff
--- a/src/example.py
+++ b/src/example.py
@@ -1 +1 @@
-old
+new
```
tokens_used: 1834
"""


class FakeRunner:
    def __init__(
        self, stdout: str = "", returncode: int = 0, raises: Exception | None = None,
    ) -> None:
        self.stdout = stdout
        self.returncode = returncode
        self.raises = raises
        self.calls: list[tuple[list[str], int]] = []
        self.kwargs: list[dict[str, object]] = []

    def __call__(
        self,
        argv: Sequence[str],
        *,
        timeout: int,
        cwd: str | Path | None = None,
        env: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        self.calls.append((list(argv), timeout))
        self.kwargs.append({"cwd": cwd, "env": env})
        if self.raises is not None:
            raise self.raises
        return subprocess.CompletedProcess(
            args=list(argv), returncode=self.returncode, stdout=self.stdout, stderr="",
        )


def _context(context: str = "AssertionError: 1 != 2") -> RepairContext:
    return RepairContext(
        category=FailureCategory.UNIT_ASSERTION,
        attempt=1,
        max_attempts=3,
        context=context,
    )


def _agent(runner: FakeRunner, template: str = 'harness --msg "%PROMPT%"') -> HarnessAgent:
    return HarnessAgent(HarnessSpec(command_template=template, timeout_seconds=120), runner=runner)


def test_is_an_adapter() -> None:
    assert isinstance(_agent(FakeRunner()), AgentAdapter)


def test_id_comes_from_the_spec() -> None:
    spec = HarnessSpec(command_template="x %PROMPT%", id="claude-code")
    assert HarnessAgent(spec, runner=FakeRunner()).id == "claude-code"


def test_runner_receives_an_argv_list() -> None:
    runner = FakeRunner()
    _agent(runner).repair(_context())
    argv, _ = runner.calls[0]
    assert isinstance(argv, list)
    assert all(isinstance(part, str) for part in argv)
    assert argv[:2] == ["harness", "--msg"]


def test_prompt_is_substituted_into_the_command() -> None:
    runner = FakeRunner()
    _agent(runner).repair(_context())
    argv, _ = runner.calls[0]
    assert all("%PROMPT%" not in part for part in argv)
    assert "AssertionError" in argv[2]


def test_prompt_is_a_single_argv_element() -> None:
    runner = FakeRunner()
    _agent(runner, template="harness --msg %PROMPT%").repair(
        _context("a b c d e f g"),
    )
    argv, _ = runner.calls[0]
    assert argv == ["harness", "--msg", _expected_prompt("a b c d e f g")]


def test_prompt_is_not_quote_escaped() -> None:
    runner = FakeRunner()
    _agent(runner).repair(_context('assert "x" == "y"'))
    argv, _ = runner.calls[0]
    assert '\\"' not in argv[2]
    assert 'assert "x" == "y"' in argv[2]


def test_default_runner_uses_no_shell(monkeypatch: pytest.MonkeyPatch) -> None:
    from markov_ci.agents import harness

    captured: dict[str, object] = {}

    def fake_run(argv: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        captured["argv"] = argv
        captured.update(kwargs)
        return subprocess.CompletedProcess(args=argv, returncode=0, stdout="", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)
    harness._default_runner(["echo", "hi"], timeout=5)
    assert captured["shell"] is False
    assert captured["argv"] == ["echo", "hi"]


def test_timeout_is_passed_to_the_runner() -> None:
    runner = FakeRunner()
    _agent(runner).repair(_context())
    assert runner.calls[0][1] == 120


def test_diff_is_extracted_from_a_fenced_block() -> None:
    proposal = _agent(FakeRunner(stdout=FENCED)).repair(_context())
    assert isinstance(proposal, PatchProposal)
    assert "+new" in proposal.diff
    assert "-old" in proposal.diff


def test_token_usage_is_parsed() -> None:
    proposal = _agent(FakeRunner(stdout=FENCED)).repair(_context())
    assert proposal.tokens_used == 1834


def test_files_changed_are_derived_from_the_diff() -> None:
    proposal = _agent(FakeRunner(stdout=FENCED)).repair(_context())
    assert "src/example.py" in proposal.files_changed


def test_non_zero_exit_yields_no_patch() -> None:
    proposal = _agent(FakeRunner(stdout="", returncode=2)).repair(_context())
    assert proposal.diff == ""
    assert "exit" in proposal.rationale


def test_timeout_raises_harness_timeout() -> None:
    runner = FakeRunner(raises=subprocess.TimeoutExpired(cmd="x", timeout=1))
    with pytest.raises(HarnessTimeout):
        _agent(runner).repair(_context())


def test_missing_harness_raises_harness_error() -> None:
    runner = FakeRunner(raises=FileNotFoundError("no such harness"))
    with pytest.raises(HarnessError):
        _agent(runner).repair(_context())


def test_parse_harness_output_handles_no_diff() -> None:
    diff, tokens = parse_harness_output("just some logs, no patch")
    assert diff == ""
    assert tokens is None


def test_parse_harness_output_reads_tokens_without_a_diff() -> None:
    _, tokens = parse_harness_output('{"tokens_used": 42}')
    assert tokens == 42


def test_real_usage_is_parsed_from_json_output() -> None:
    # M13.21 (#105): claude -p --output-format json reports usage
    _, tokens = parse_harness_output(
        '{"result": "done", "usage": {"input_tokens": 1200, "output_tokens": 340}}',
    )
    assert tokens == 1540


def test_unknown_usage_is_none_not_zero() -> None:
    _, tokens = parse_harness_output("a harness that prints no usage")
    assert tokens is None


def _expected_prompt(context: str) -> str:
    """The prompt the adapter must build — no quote escaping (ADR-0016)."""
    return (
        f"Fix this unit_assertion failure (attempt 1/3).\n\n{context}"
    )


class FileReadingRunner:
    """Reads the `%PROMPT_FILE%` path *during* the call, before cleanup."""

    def __init__(self) -> None:
        self.captured: list[tuple[list[str], str, int, bool]] = []

    def __call__(
        self,
        argv: Sequence[str],
        *,
        timeout: int,
        cwd: str | Path | None = None,
        env: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        path = argv[-1]
        existed = os.path.exists(path)
        content = Path(path).read_text(encoding="utf-8") if existed else ""
        mode = stat.S_IMODE(os.stat(path).st_mode) if existed else 0
        self.captured.append((list(argv), content, mode, existed))
        return subprocess.CompletedProcess(
            args=list(argv), returncode=0, stdout="", stderr="",
        )


def _prompt_file_agent(runner: Runner) -> HarnessAgent:
    return HarnessAgent(
        HarnessSpec(command_template="harness --prompt-file %PROMPT_FILE%"),
        runner=runner,
    )


def test_prompt_file_placeholder_keeps_the_prompt_off_argv() -> None:
    # M13.4 (#88): the prompt goes to a 0600 temp file, not argv (ps / ARG_MAX).
    runner = FileReadingRunner()
    _prompt_file_agent(runner).repair(_context("secret prompt text"))
    argv, content, mode, existed = runner.captured[0]
    assert existed
    assert content == _expected_prompt("secret prompt text")
    assert mode == 0o600
    assert all("secret prompt text" not in part for part in argv)
    assert "%PROMPT_FILE%" not in " ".join(argv)


def test_prompt_file_is_removed_after_the_run() -> None:
    runner = FileReadingRunner()
    _prompt_file_agent(runner).repair(_context())
    path = runner.captured[0][0][-1]
    assert not os.path.exists(path)


def test_prompt_file_is_removed_even_when_the_harness_times_out() -> None:
    captured: list[str] = []

    def runner(
        argv: Sequence[str],
        *,
        timeout: int,
        cwd: str | Path | None = None,
        env: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        captured.append(argv[-1])
        raise subprocess.TimeoutExpired(cmd=argv, timeout=timeout)

    with pytest.raises(HarnessTimeout):
        _prompt_file_agent(runner).repair(_context())
    assert captured and not os.path.exists(captured[0])


def test_the_harness_runs_with_the_given_cwd_and_a_scrubbed_env() -> None:
    # M13.19 (#103): the harness runs in the validation copy with a scrubbed env.
    runner = FakeRunner()
    agent = HarnessAgent(
        HarnessSpec(command_template="harness %PROMPT%"),
        runner=runner, cwd="/tmp/validation-copy",
    )
    agent.repair(_context())
    assert runner.kwargs[0]["cwd"] == "/tmp/validation-copy"
    env = runner.kwargs[0]["env"]
    assert isinstance(env, dict)
    assert "PATH" in env
    assert "GITHUB_TOKEN" not in env



def _git_repo(path: Path) -> None:
    path.mkdir(parents=True)
    subprocess.run(["git", "-C", str(path), "init", "-q"], check=True)
    subprocess.run(["git", "-C", str(path), "config", "user.email", "t@e.com"], check=True)
    subprocess.run(["git", "-C", str(path), "config", "user.name", "T"], check=True)
    (path / "app.py").write_text("VALUE = 1\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(path), "add", "-A"], check=True)
    subprocess.run(["git", "-C", str(path), "commit", "-qm", "base"], check=True)


def test_the_proposal_is_derived_from_the_git_diff_of_the_tree(tmp_path: Path) -> None:
    # the harness edits the tree; the proposal is `git diff` of that tree, not stdout
    repo = tmp_path / "copy"
    _git_repo(repo)

    def runner(
        argv: Sequence[str],
        *,
        timeout: int,
        cwd: str | Path | None = None,
        env: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        (Path(str(cwd)) / "app.py").write_text("VALUE = 2\n", encoding="utf-8")
        return subprocess.CompletedProcess(
            args=argv, returncode=0, stdout="chatter, no diff fence\n", stderr="",
        )

    agent = HarnessAgent(
        HarnessSpec(command_template="harness %PROMPT%"), runner=runner, cwd=str(repo),
    )
    proposal = agent.repair(_context())
    assert "-VALUE = 1" in proposal.diff
    assert "+VALUE = 2" in proposal.diff
    assert "app.py" in proposal.files_changed


def test_a_malformed_json_line_is_skipped() -> None:
    _, tokens = parse_harness_output('{"broken": ')
    assert tokens is None


def test_the_prompt_includes_the_previous_diff() -> None:
    runner = FakeRunner()
    agent = HarnessAgent(HarnessSpec(command_template="h %PROMPT%"), runner=runner)
    agent.repair(
        RepairContext(
            category=FailureCategory.UNIT_ASSERTION,
            attempt=2,
            max_attempts=3,
            context="assertion failed",
            diff="--- a/x.py\n+++ b/x.py\n",
        ),
    )
    argv, _ = runner.calls[0]
    assert "Diff so far" in argv[-1]


def test_validate_template_rejects_an_empty_template() -> None:
    from markov_ci.agents.harness import validate_template

    with pytest.raises(ValueError, match="empty"):
        validate_template("   ")


def test_validate_template_strips_a_windows_exe_suffix() -> None:
    from markov_ci.agents.harness import validate_template

    with pytest.raises(ValueError, match="shell"):
        validate_template("bash.exe -c 'tool %PROMPT%'")


def test_git_diff_in_includes_untracked_files(tmp_path: Path) -> None:
    from markov_ci.agents.harness import git_diff_in

    repo = tmp_path / "r"
    _git_repo(repo)
    (repo / "new.py").write_text("x = 1\n", encoding="utf-8")
    diff = git_diff_in(repo)
    assert "new.py" in diff
