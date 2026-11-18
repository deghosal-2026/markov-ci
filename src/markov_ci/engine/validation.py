"""Worktree validation apply-and-test (docs/spec/0011-engine-runtime.md §2).

A patch is applied in a disposable git worktree and reverted by simply discarding
the worktree — the PR branch and ``main`` are never touched. The worktree is
removed in a ``finally`` block, so cleanup happens even if the test command
explodes.

This is **worktree validation**, not a security sandbox (ADR-0012): it is not a
kernel-level boundary.
"""

from __future__ import annotations

import contextlib
import os
import shutil
import signal
import subprocess
import tempfile
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from markov_ci.engine.container import container_command
from markov_ci.guardrails import check_paths
from markov_ci.scrub import scrubbed_env

# Captured output is bounded to the last 1 MB (ADR-0012 §3).
MAX_OUTPUT_BYTES = 1_048_576
# Per-child resource ceilings (ADR-0012 §4).
MEMORY_LIMIT_BYTES = 2 * 1024**3
FILE_SIZE_LIMIT_BYTES = 256 * 1024**2


def _resource_limiter(cpu_seconds: int) -> Callable[[], None] | None:
    """Return a ``preexec_fn`` that caps CPU, address space and file size (POSIX)."""
    if os.name != "posix":  # pragma: no cover - Windows uses a Job Object
        return None
    import resource  # noqa: PLC0415 - POSIX-only

    def _limit() -> None:
        for which, value in (
            (resource.RLIMIT_CPU, (cpu_seconds, cpu_seconds + 5)),
            (resource.RLIMIT_AS, (MEMORY_LIMIT_BYTES, MEMORY_LIMIT_BYTES)),
            (
                resource.RLIMIT_FSIZE,
                (FILE_SIZE_LIMIT_BYTES, FILE_SIZE_LIMIT_BYTES),
            ),
        ):
            # best effort: macOS refuses RLIMIT_AS
            with contextlib.suppress(OSError, ValueError):
                resource.setrlimit(which, value)

    return _limit


def _kill_process_group(process: subprocess.Popen[bytes]) -> None:
    """Kill the child and every descendant (ADR-0012 §3).

    POSIX: the child is its own session leader (``start_new_session=True``), so
    ``os.killpg`` reaps the whole tree. Windows would use a Job Object; here we
    fall back to killing the direct child.
    """
    if os.name == "posix":
        try:
            os.killpg(os.getpgid(process.pid), signal.SIGKILL)
            return
        except (ProcessLookupError, PermissionError):
            pass
    process.kill()


def _run_bounded(
    command: Sequence[str],
    *,
    cwd: Path,
    env: dict[str, str],
    timeout: int,
) -> tuple[int, str, bool]:
    """Run ``command`` in its own process group, returning ``(code, output, timed_out)``."""
    process = subprocess.Popen(
        list(command),
        cwd=cwd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        start_new_session=(os.name == "posix"),
        preexec_fn=_resource_limiter(timeout),
    )
    timed_out = False
    try:
        raw, _ = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        timed_out = True
        _kill_process_group(process)
        raw, _ = process.communicate()
    tail = (raw or b"")[-MAX_OUTPUT_BYTES:]
    return process.returncode, tail.decode("utf-8", "replace"), timed_out


@dataclass(frozen=True, slots=True)
class ValidationResult:
    """The result of applying and testing a patch in isolation."""

    applied: bool
    passed: bool
    output: str
    guardrail_report: tuple[str, ...] = ()
    timed_out: bool = False


class WorktreeValidator:
    """A disposable worktree rooted at a temporary directory."""

    def __init__(
        self,
        repo: str | Path,
        *,
        root: str | Path | None = None,
        container_image: str | None = None,
    ) -> None:
        self._repo = Path(repo).resolve()
        self._container_image = container_image
        self._root = (
            Path(root) if root is not None
            else Path(tempfile.mkdtemp(prefix="markov-validation-"))
        )
        self._root.mkdir(parents=True, exist_ok=True)
        self._home = self._root / "home"
        self._home.mkdir(parents=True, exist_ok=True)

    def _git(self, *args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", "-C", str(cwd or self._repo), *args],
            capture_output=True,
            text=True,
            check=False,
        )

    def _changed_paths(self, worktree: Path) -> tuple[str, ...]:
        """Paths git reports as changed in ``worktree`` (renames: both sides).

        The applied patch is staged first so newly-created files (which ``git diff``
        would otherwise treat as untracked) are included — the worktree is
        disposable, so staging is harmless.
        """
        self._git("add", "-A", cwd=worktree)
        diff = self._git("diff", "--cached", "--name-status", "-M", cwd=worktree)
        paths: list[str] = []
        for line in diff.stdout.splitlines():
            fields = line.split("\t")
            if len(fields) >= 3 and fields[0][:1] in {"R", "C"}:
                paths.extend((fields[1], fields[2]))
            elif len(fields) >= 2:
                paths.append(fields[1])
        return tuple(dict.fromkeys(paths))

    def apply_and_test(
        self,
        diff: str,
        command: Sequence[str],
        *,
        timeout: int = 600,
        allow_write: Sequence[str] = ("**",),
        deny_write: Sequence[str] = (),
        env_allow: Sequence[str] = (),
    ) -> ValidationResult:
        """Apply ``diff`` in a fresh clone and run ``command`` there.

        A clone (``git clone --no-hardlinks --local``) is used rather than a shared
        ``git worktree`` so the host repo's hooks, config and credentials are not
        shared with the untrusted patch (ADR-0012 §1).
        """
        clone = self._root / f"clone-{uuid4().hex[:8]}"
        try:
            cloned = subprocess.run(
                [
                    "git", "clone", "--no-hardlinks", "--local", "--quiet",
                    str(self._repo), str(clone),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            if cloned.returncode != 0:
                return ValidationResult(False, False, f"clone failed: {cloned.stderr}")

            patch_file = self._root / "patch.diff"
            patch_file.write_text(diff, encoding="utf-8")
            apply = self._git("apply", str(patch_file), cwd=clone)
            if apply.returncode != 0:
                return ValidationResult(False, False, f"patch did not apply: {apply.stderr}")

            # Post-apply verification (spec 0005 §1): git is the source of truth for
            # what actually changed, so the allowlist is re-run before the tests.
            decision = check_paths(
                self._changed_paths(clone),
                allow_write=allow_write,
                deny_write=deny_write,
            )
            if not decision.allowed:
                return ValidationResult(
                    True, False,
                    f"post-apply allowlist denied: {decision.reason}",
                    decision.offending,
                )

            try:
                run_argv = (
                    container_command(
                        image=self._container_image, clone=clone, command=command,
                    )
                    if self._container_image
                    else list(command)
                )
                code, output, timed_out = _run_bounded(
                    run_argv,
                    cwd=clone,
                    env=scrubbed_env(home=self._home, allow=env_allow),
                    timeout=timeout,
                )
            except OSError as exc:
                return ValidationResult(True, False, f"could not run test command: {exc}")
            if timed_out:
                return ValidationResult(
                    True, False, f"test command timed out\n{output}", timed_out=True,
                )
            return ValidationResult(True, code == 0, output)
        finally:
            shutil.rmtree(clone, ignore_errors=True)

    def close(self) -> None:
        shutil.rmtree(self._root, ignore_errors=True)

    def __enter__(self) -> WorktreeValidator:
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()
