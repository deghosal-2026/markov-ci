#!/bin/sh
# M9.6 (#61) deep validation — build the fixed image, run the compose acceptance,
# then exercise each demo's evidence beyond exit codes. Everything under
# network_mode: none (inherited from the compose services).
set -u
cd "$(git rev-parse --show-toplevel)"

echo "=== 1. build ==="
docker compose build
echo "build_exit=$?"

echo "=== 2. compose acceptance (exit-code assertions via run-demo.sh) ==="
for n in 01 02 03 04; do
  docker compose run --rm "demo-$n"
  echo "demo-$n wrapper_exit=$?"
done

echo "=== 3. image environment ==="
docker compose run --rm --entrypoint sh demo-01 -c '
  python3 --version
  git --version
  pytest --version
  python3 -c "import markov_ci, numpy, pydantic, yaml, typer, jsonschema; print(\"IMPORTS_OK\")"
  pip check
'

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
print("HOPS", [f'{e["from_state"]}>{e["to_state"]}' for e in es])
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
PY
'

echo "=== 5. deep demo-02: decay -> a2, five events, no third attempt ==="
docker compose run --rm --entrypoint sh demo-02 -c '
  markov-ci run /examples/02-unit-assertion-decay/config.yaml --junit /examples/02-unit-assertion-decay/report.xml --repo /examples/02-unit-assertion-decay/repo --seed 42 --json > /tmp/d2.json
  echo "run_exit=$?"
  python3 <<PY
import json
d = json.load(open("/tmp/d2.json"))
print("ABSORBING", d["absorbing_state"])
print("VISITS", sorted(d["visits"]))
print("HAS_S2_3", "s2_agent_reasoning#3" in d["visits"])
es = [json.loads(l) for l in open("/examples/02-unit-assertion-decay/.markov-ci/events.jsonl")]
print("EVENTS", len(es))
print("CATS", sorted({e["failure_category"] for e in es}))
PY
'

echo "=== 6. deep demo-03: triage short-circuit, zero events ==="
docker compose run --rm --entrypoint sh demo-03 -c '
  markov-ci run /examples/03-infra-timeout/config.yaml --junit /examples/03-infra-timeout/report.xml --seed 42
  echo "run_exit=$?"
  if [ -e /examples/03-infra-timeout/.markov-ci ]; then echo "EVENTS_DIR_PRESENT"; else echo "NO_EVENTS_DIR"; fi
'

echo "=== 7. deep demo-04: queue report shape ==="
docker compose run --rm --entrypoint sh demo-04 -c '
  markov-ci queue --lambda 120 --mu 30 --c 5 --simulate --json > /tmp/q.json
  python3 <<PY
import json
d = json.load(open("/tmp/q.json"))
print("POOLS", sorted(d["pools"]))
print("AGENT_RHO", d["pools"]["agent"]["rho"])
print("AGENT_SIM_KEYS", sorted(d["pools"]["agent"]["simulation"]))
print("ERLANG_P95_MIN", round(d["pools"]["agent"]["p95_wait"] * 60, 2))
print("SIM_P95_MIN", round(d["pools"]["agent"]["simulation"]["p95_wait"] * 60, 2))
PY
'

echo "=== 8. host: static docker-contract test against the fixed Dockerfile ==="
python3 -m pytest tests/unit/test_docker.py -q
echo "pytest_exit=$?"

echo "=== done ==="
