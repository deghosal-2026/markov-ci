#!/bin/sh
# Deep demo-01 re-check (the first attempt died on a quoting bug in the caller).
set -u
cd "$(git rev-parse --show-toplevel)"

echo "=== 4. deep demo-01: evidence, repo untouched, determinism ==="
docker compose run --rm --entrypoint sh demo-01 -c '
  markov-ci run /examples/01-lint-error/config.yaml --junit /examples/01-lint-error/report.xml --repo /examples/01-lint-error/repo --seed 42 --json > /tmp/r1.json
  echo "run_exit=$?"
  python3 <<PY
import json
d = json.load(open("/tmp/r1.json"))
print("ABSORBING", d["absorbing_state"])
print("VISITS", sorted(d["visits"]))
print("TOKENS", d["tokens_used"])
es = [json.loads(l) for l in open("/examples/01-lint-error/.markov-ci/events.jsonl")][:4]
print("EVENTS", len(es))
print("CATS", sorted({e["failure_category"] for e in es}))
print("ADAPTERS", sorted({e["adapter"] for e in es}))
print("HOPS", [e["from_state"] + ">" + e["to_state"] for e in es])
PY
  echo "REPO_DIRTY_LINES=$(git -C /examples/01-lint-error/repo status --porcelain | wc -l)"
  markov-ci run /examples/01-lint-error/config.yaml --junit /examples/01-lint-error/report.xml --repo /examples/01-lint-error/repo --seed 42 --json > /tmp/r2.json
  python3 <<PY
import json
a = json.load(open("/tmp/r1.json"))
b = json.load(open("/tmp/r2.json"))
keys = ("absorbing_state", "visits", "tokens_used")
same = all(a[k] == b[k] for k in keys)
print("DETERMINISM", "IDENTICAL" if same else "DRIFT")
print("R2_ABSORBING", b["absorbing_state"])
PY
'
