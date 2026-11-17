# How-to: run the examples in Docker

> **Status:** ships with **M9.6 ([#61](https://github.com/deghosal-2026/markov-ci/issues/61))**.
> The commands below are the contract for the Docker runner and are exercised by
> `tests/unit/test_docker.py`; the image is scanned by the release
> [security gate](https://github.com/deghosal-2026/markov-ci/issues/60).

The offline demos (01–04) are designed to be deterministic and network-free. A
container is the strongest way to prove that: it pins the Python interpreter
(3.11–3.13), `git`, and the dependencies, so **same seed → same output** holds on
any machine and in CI. It is also the fastest way to try the project without
setting up Python.

## Why a container

- **Reproducible** — the interpreter and dependencies are pinned, not inherited from
  your dev box.
- **Provably offline** — the demos run under `--network none`.
- **Zero setup** — one command, no virtualenv.

It is **not** the engine's sandbox: the governed loop still applies patches in a
disposable `git` worktree (spec [0011](../spec/0011-engine-runtime.md) §2). Docker
here is packaging for the examples and the docs.

## Build the image

```bash
docker build -t markov-ci:dev .
```

The image is `python:3.12-slim` plus `git`; it installs the package and copies the
examples in (so the demos are real git repositories for the worktree sandbox).

## Run a single demo

```bash
docker run --rm --network none \
  markov-ci:dev run /examples/01-lint-error/config.yaml \
    --junit /examples/01-lint-error/report.xml \
    --repo /examples/01-lint-error/repo \
    --seed 42
```

The process exit code **is** the outcome — the same stable contract as everywhere
(spec [0008](../spec/0008-cli-contract.md)):

| Exit | Absorbing state | Demo that produces it |
|---|---|---|
| `0` | `a1_ready_for_human_review` | 01, 04 |
| `2` | `a2_escalate_to_author` | 02, 03 |
| `3` | `a3_budget_exceeded` | — (budget guardrail) |
| `4` | invalid config | — |

## Run them all with Compose

```bash
docker compose run --rm demo-01   # lint error, first-pass green
docker compose run --rm demo-02   # assertion decay → escalate
docker compose run --rm demo-03   # infra timeout, zero tokens
docker compose run --rm demo-04   # runner-pool sizing
```

Each service runs its demo under `--network none` and asserts the expected exit
code, so a broken demo fails the container.

## Mounting the examples instead of copying

If you would rather bind-mount your own copy (for example to edit a fixture), run as
your own user to avoid permission mismatches:

```bash
docker run --rm --network none --user "$(id -u):$(id -g)" \
  -v "$PWD/examples:/examples" \
  markov-ci:dev run /examples/01-lint-error/config.yaml \
    --junit /examples/01-lint-error/report.xml \
    --repo /examples/01-lint-error/repo --seed 42
```

## What is out of scope

- **Container as the engine sandbox** — the sandbox stays a worktree; a container
  backend would need its own ADR.
- **Registry publishing / signing** — not needed to demo.
- **Demo 05 (GitHub Actions e2e)** — that one is *live* and requires secrets; it does
  not run in the container.

## See also

- [Quick start](../quick-start.md) · [Tutorial 01](../tutorials/01-lint-error-first-pass.md)
- [Integrate with GitHub Actions](integrate-github-actions.md) ·
  [GitLab / Jenkins](integrate-gitlab-jenkins.md)
