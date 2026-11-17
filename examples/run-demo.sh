#!/bin/sh
# Run one demo and assert its documented exit code (M9.6 / #61).
#
# Usage: run-demo.sh <expected-exit> <command...>
#
# A broken demo (wrong exit code) fails the container, so `docker compose run`
# is a real assertion, not just a replay.
set -u

expected="$1"
shift

"$@"
code=$?

if [ "$code" -ne "$expected" ]; then
    echo "FAIL: expected exit $expected, got $code — $*" >&2
    exit 1
fi
echo "OK: $* exited $code"
