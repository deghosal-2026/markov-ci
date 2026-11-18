#!/usr/bin/env python3
"""M14 field-test runner (v0.1.1) — re-runnable, captures raw evidence.

Runs the fixes outside the unit suite and writes per-case logs into this directory:

- M14.2 offline demos 01–07 (documented commands; exit codes, event streams, --seed stability)
- M14.3 FIX-01 injection payloads against the real runner (no marker file)
- M14.4 FIX-02 adversarial diffs through a real git repo (a2 + guardrail report, no s3)
- M14.6 budget & isolation (remaining-timeout -> a3 with event; scrubbed env; process-group kill)

Usage:  python3 field-test/v0.1.1/run-field-test.py
"""

from __future__ import annotations

import json
import os
import re
import shlex
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PY = sys.executable
ENV = {**os.environ, "PYTHONPATH": str(ROOT / "src")}
DEFAULT_CONFIG = (ROOT / "src" / "markov_ci" / "data" / "default.yaml").read_text(encoding="utf-8")

RESULTS: list[tuple[str, str, str]] = []


def record(case: str, ok: bool, detail: str) -> None:
    RESULTS.append((case, "PASS" if ok else "FAIL", detail))
    print(f"[{'PASS' if ok else 'FAIL'}] {case}: {detail}", flush=True)


def write(name: str, text: str) -> None:
    (HERE / name).write_text(text, encoding="utf-8")


def cli(*args: str, cwd: Path = ROOT) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [PY, "-m", "markov_ci", *args], cwd=cwd, env=ENV, capture_output=True, text=True,
    )


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)


def config_text(
    *, events: Path, wall_clock: int | None = None, harness: str | None = None,
) -> str:
    """The packaged default config with telemetry/wall-clock/harness overridden."""
    text = DEFAULT_CONFIG.replace("  path: .markov-ci/events.jsonl", f"  path: {events}")
    if wall_clock is not None:
        text = re.sub(r"wall_clock_seconds: \d+", f"wall_clock_seconds: {wall_clock}", text)
    if harness is not None:
        text = text.replace(
            "  adapter: simulated\n",
            "  adapter: harness\n  harness:\n    name: field-test\n"
            f"    command_template: '{harness}'\n",
        )
    return text


def _base_repo(tmp_path: Path, files: dict[str, str]) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "ft@example.com")
    _git(repo, "config", "user.name", "ft")
    for name, content in files.items():
        path = repo / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", "base")
    return repo


def _junit(tmp_path: Path, message: str = "AssertionError: 1 != 2") -> Path:
    junit = tmp_path / "report.xml"
    junit.write_text(
        "<testsuites><testsuite><testcase name='t' classname='c'>"
        f"<failure message=\"{message}\" type=\"AssertionError\">trace</failure>"
        "</testcase></testsuite></testsuites>",
        encoding="utf-8",
    )
    return junit


def _stream(events: Path) -> list[dict[str, object]]:
    if not events.exists():
        return []
    return [
        json.loads(line)
        for line in events.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


# ---------------------------------------------------------------- M14.1 env

def _cmd(*args: str) -> str:
    return subprocess.run(args, capture_output=True, text=True).stdout.strip()


def case_env() -> None:
    text = "\n".join([
        f"date:    {_cmd('date', '-u')}",
        f"uname:   {_cmd('uname', '-a')}",
        f"python:  {sys.version.splitlines()[0]}",
        f"commit:  {_cmd('git', '-C', str(ROOT), 'rev-parse', 'HEAD')}",
        f"docker:  {_cmd('docker', 'version', '--format', '{{.Server.Version}}') or 'unavailable'}",
    ])
    write("env.txt", text + "\n")
    record("M14.1 environment", True, "env.txt written")


# ---------------------------------------------------------------- M14.2 demos

_CMD_LINE = re.compile(r"^\s*markov-ci\s+(\w+)")
_EXIT_LINE = re.compile(r"Exit code to expect:\*\*\s*`(\d)`")


def _demo_command(readme: str) -> list[str]:
    lines = readme.splitlines()
    for index, line in enumerate(lines):
        if _CMD_LINE.match(line):
            command = line.strip()
            while command.endswith("\\") and index + 1 < len(lines):
                index += 1
                command = command[:-1].rstrip() + " " + lines[index].strip()
            return shlex.split(command)[1:]
    return []


def _telemetry_path(example: Path) -> Path | None:
    config = example / "config.yaml"
    if not config.exists():
        return None
    match = re.search(r"^\s*path:\s*(\S+)\s*$", config.read_text(encoding="utf-8"), re.MULTILINE)
    return ROOT / match.group(1) if match else None


def case_demos() -> None:
    log_lines: list[str] = []
    for example in sorted((ROOT / "examples").glob("[0-9][0-9]-*")):
        readme_path = example / "README.md"
        if not readme_path.exists():
            continue
        readme = readme_path.read_text(encoding="utf-8")
        args = _demo_command(readme)
        exit_match = _EXIT_LINE.search(readme)
        if not args:
            log_lines.append(f"== {example.name}: no `markov-ci` command (workflow demo) — skipped")
            record(f"M14.2 {example.name}", True, "no CLI command (workflow demo)")
            continue
        expected = int(exit_match.group(1)) if exit_match else None

        events = _telemetry_path(example)
        if events is not None and events.exists():
            events.unlink()
        first = cli(*args)
        log_lines.append(f"== {example.name}: {' '.join(args)}")
        log_lines.append(f"   exit={first.returncode} expected={expected}")
        log_lines.append(f"   stdout: {first.stdout.strip()[:200]}")

        stream = [
            f"{event['from_state']} -> {event['to_state']}" for event in _stream(events)
        ] if events else []
        log_lines.append(f"   events({len(stream)}): {stream}")

        ok = expected is None or first.returncode == expected
        if args[0] == "run" and first.stdout.strip().startswith("{"):
            second = cli(*args)
            stable = json.loads(first.stdout)["visits"] == json.loads(second.stdout)["visits"]
            log_lines.append(f"   seed-stability: {stable}")
            ok = ok and stable
        record(f"M14.2 {example.name}", ok, f"exit={first.returncode} (expected {expected})")
    write("demos.log", "\n".join(log_lines) + "\n")


# ---------------------------------------------------------------- M14.3 injection

INJECTION_PAYLOADS = [
    "$(touch {marker})",
    "`touch {marker}`",
    'break"out ; touch {marker} ; echo "x',
    "a; touch {marker}",
    "a | touch {marker}",
    "a && touch {marker}",
    "line1\nline2; touch {marker}",
    "$HOME",
    "> {marker}",
]


def case_injection() -> None:
    log_lines: list[str] = []
    echo = f'"{PY}" -c "import sys; sys.stdout.write(sys.argv[1])" %PROMPT%'
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        repo = _base_repo(tmp_path, {"src/app.py": "VALUE = 1\n"})
        for index, payload in enumerate(INJECTION_PAYLOADS):
            marker = tmp_path / f"pwned-{index}"
            junit = _junit(tmp_path, payload.replace("{marker}", str(marker)))
            events = tmp_path / f"events-{index}.jsonl"
            config = tmp_path / "config.yaml"
            config.write_text(config_text(events=events, harness=echo), encoding="utf-8")
            result = cli("run", str(config), "--junit", str(junit), "--repo", str(repo), "--json")
            leaked = marker.exists()
            absorbing = (
                json.loads(result.stdout).get("absorbing_state")
                if result.stdout.strip().startswith("{") else None
            )
            log_lines.append(
                f"payload {payload!r}: exit={result.returncode} absorbing={absorbing} "
                f"marker_created={leaked}",
            )
            record(f"M14.3 payload[{index}]", not leaked, f"marker_created={leaked}")
        write("injection.log", "\n".join(log_lines) + "\n")


# ---------------------------------------------------------------- M14.4 guardrail

ADVERSARIAL = {
    "delete-ci": (
        "diff --git a/.github/workflows/ci.yml b/.github/workflows/ci.yml\n"
        "deleted file mode 100644\n"
        "--- a/.github/workflows/ci.yml\n+++ /dev/null\n"
        "@@ -1 +0,0 @@\n-name: ci\n"
    ),
    "rename-into-github": (
        "diff --git a/notes.md b/.github/workflows/evil.yml\n"
        "similarity index 100%\nrename from notes.md\nrename to .github/workflows/evil.yml\n"
    ),
    "quoted-octal": (
        'diff --git "a/\\056github/workflows/ci.yml" "b/\\056github/workflows/ci.yml"\n'
        "--- \"a/\\056github/workflows/ci.yml\"\n"
        "+++ \"b/\\056github/workflows/ci.yml\"\n"
        "@@ -1 +1 @@\n-name: ci\n+name: evil\n"
    ),
}


def case_guardrail() -> None:
    log_lines: list[str] = []
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        repo = _base_repo(tmp_path, {"src/app.py": "VALUE = 1\n", "notes.md": "notes\n"})
        junit = _junit(tmp_path)
        for name, diff in ADVERSARIAL.items():
            printer = tmp_path / f"print-{name}.py"
            printer.write_text(
                "import sys\nsys.stdout.write("
                + repr("```diff\n" + diff + "```")
                + ")\n",
                encoding="utf-8",
            )
            events = tmp_path / f"events-{name}.jsonl"
            config = tmp_path / f"config-{name}.yaml"
            config.write_text(
                config_text(events=events, harness=f'"{PY}" {printer} %PROMPT%'),
                encoding="utf-8",
            )
            result = cli(
                "run", str(config), "--junit", str(junit), "--repo", str(repo),
                "--failing-command", f'"{PY}" -c "pass"', "--json",
            )
            stream = [
                f"{event['from_state']} -> {event['to_state']}" for event in _stream(events)
            ]
            sandbox_invoked = any("s3_sandbox_validation" in hop for hop in stream)
            report = json.loads(result.stdout) if result.stdout.strip().startswith("{") else {}
            guardrail = report.get("guardrail_report") or []
            ok = result.returncode == 1 and bool(guardrail) and not sandbox_invoked
            log_lines.append(
                f"== {name}: exit={result.returncode} sandbox_invoked={sandbox_invoked} "
                f"guardrail={guardrail} hops={stream}",
            )
            record(
                f"M14.4 {name}", ok,
                f"exit={result.returncode}, sandbox_invoked={sandbox_invoked}",
            )
        write("guardrail.log", "\n".join(log_lines) + "\n")


# ---------------------------------------------------------------- M14.6 budget/isolation

def case_budget_isolation() -> None:
    log_lines: list[str] = []
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        repo = _base_repo(tmp_path, {"src/example.py": "def broken():\n    return 1\n"})
        junit = _junit(tmp_path)

        # 1) remaining-time timeout -> a3 with an event
        events = tmp_path / "events-timeout.jsonl"
        config = tmp_path / "cfg-timeout.yaml"
        config.write_text(config_text(events=events, wall_clock=1), encoding="utf-8")
        result = cli(
            "run", str(config), "--junit", str(junit), "--repo", str(repo),
            "--json", "--seed", "42",
            "--failing-command", f'"{PY}" -c "import time; time.sleep(30)"',
        )
        stream = _stream(events)
        last = stream[-1]["to_state"] if stream else None
        log_lines.append(f"timeout: exit={result.returncode} last_to={last} events={len(stream)}")
        record("M14.6 timeout->a3", result.returncode == 3 and last == "a3_budget_exceeded",
               f"exit={result.returncode}, last={last}")

        # 2) scrubbed env: GITHUB_TOKEN must not reach the child
        marker = tmp_path / "env.json"
        events2 = tmp_path / "events-env.jsonl"
        config2 = tmp_path / "cfg-env.yaml"
        config2.write_text(config_text(events=events2), encoding="utf-8")
        cli(
            "run", str(config2), "--junit", str(junit), "--repo", str(repo), "--seed", "42",
            "--failing-command",
            f'"{PY}" -c "import os,json; json.dump(dict(os.environ), open({str(marker)!r},\'w\'))"',
        )
        dumped = json.loads(marker.read_text(encoding="utf-8")) if marker.exists() else {}
        leaked = "GITHUB_TOKEN" in dumped
        log_lines.append(
            f"scrubbed-env: wrote={marker.exists()} GITHUB_TOKEN_present={leaked} "
            f"keys={sorted(dumped)[:6]}",
        )
        record("M14.6 scrubbed-env", marker.exists() and not leaked,
               f"wrote={marker.exists()}, GITHUB_TOKEN_present={leaked}")

        # 3) process-group kill: a grandchild must not outlive the timeout
        gc_marker = tmp_path / "grandchild-ran"
        grandchild = (
            "import time, pathlib; "
            f"time.sleep(1.0); pathlib.Path({str(gc_marker)!r}).write_text('x')"
        )
        parent = (
            "import subprocess, sys, time; "
            f"subprocess.Popen([sys.executable, '-c', {grandchild!r}]); time.sleep(30)"
        )
        events3 = tmp_path / "events-kill.jsonl"
        config3 = tmp_path / "cfg-kill.yaml"
        config3.write_text(config_text(events=events3, wall_clock=1), encoding="utf-8")
        cli(
            "run", str(config3), "--junit", str(junit), "--repo", str(repo), "--seed", "42",
            "--failing-command", f'"{PY}" -c "{parent}"',
        )
        time.sleep(1.5)
        log_lines.append(f"process-group: grandchild_ran={gc_marker.exists()}")
        record("M14.6 process-group-kill", not gc_marker.exists(),
               f"grandchild_ran={gc_marker.exists()}")
        write("budget-isolation.log", "\n".join(log_lines) + "\n")


def main() -> int:
    case_env()
    case_demos()
    case_injection()
    case_guardrail()
    case_budget_isolation()
    write("results.txt", "\n".join(f"{c}\t{v}\t{d}" for c, v, d in RESULTS) + "\n")
    failed = [case for case, verdict, _ in RESULTS if verdict == "FAIL"]
    print(f"\n{len(RESULTS)} cases, {len(failed)} failed: {failed}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
