#!/usr/bin/env bash
# Composite-action entrypoint (M10.1 / #46).
#
# GitHub exports action inputs as INPUT_* env vars and collects step outputs from
# the file named by $GITHUB_OUTPUT. This script governs one run and writes the
# documented outputs. See docs/how-to/integrate-github-actions.md.
set -euo pipefail

: "${INPUT_JUNIT:?the 'junit' input is required}"

args=(run)
if [ -n "${INPUT_CONFIG:-}" ]; then
    args+=("$INPUT_CONFIG")
fi
args+=(--junit "$INPUT_JUNIT" --seed "${INPUT_SEED:-42}")
if [ -n "${INPUT_REPO:-}" ]; then
    args+=(--repo "$INPUT_REPO")
fi
if [ -n "${INPUT_ADAPTER:-}" ]; then
    args+=(--adapter "$INPUT_ADAPTER")
fi
if [ -n "${INPUT_CONTAINER:-}" ]; then
    args+=(--container-image "$INPUT_CONTAINER")
fi
if [ "${INPUT_PUBLISH:-false}" = "true" ]; then
    args+=(--publish)
fi
if [ -n "${INPUT_FAILING_COMMAND:-}" ]; then
    args+=(--failing-command "$INPUT_FAILING_COMMAND")
fi
if [ -n "${INPUT_REGRESSION_COMMAND:-}" ]; then
    args+=(--regression-command "$INPUT_REGRESSION_COMMAND")
fi
if [ -n "${INPUT_MAX_TOKENS:-}" ]; then
    args+=(--max-tokens "$INPUT_MAX_TOKENS")
fi
if [ -n "${INPUT_WALL_CLOCK:-}" ]; then
    args+=(--wall-clock "$INPUT_WALL_CLOCK")
fi
args+=(--json)

result="$(mktemp)"
patch="$(mktemp)"
args+=(--output-patch "$patch")
set +e
python3 -m markov_ci "${args[@]}" > "$result"
code=$?
set -e

python3 - "$result" "$code" >> "${GITHUB_OUTPUT:-/dev/stdout}" <<'PY'
import json
import sys

path, code = sys.argv[1], sys.argv[2]
try:
    with open(path) as handle:
        data = json.load(handle)
except (OSError, ValueError):
    data = {}  # e.g. a triage short-circuit, which prints a human line

# spec 0008: the exit code and the absorbing state are 1:1.
BY_CODE = {"0": "a1_ready_for_human_review", "1": "a2_escalate_to_author",
           "3": "a3_budget_exceeded"}


def emit(name: str, value: object) -> None:
    print(f"{name}={value}")


emit("absorbing-state", data.get("absorbing_state") or BY_CODE.get(code, ""))
emit("exit-code", code)
emit("run-id", data.get("run_id") or "")
emit("patch-branch", data.get("patch_branch") or "")
emit("events-path", data.get("events_path") or "")
emit("patch-path", data.get("patch_path") or "")
PY

exit "$code"
