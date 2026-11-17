# syntax=docker/dockerfile:1
#
# Offline proof-suite runner (docs/how-to/run-in-docker.md, M9.6 / #61).
# A pinned interpreter plus git, so the demos reproduce on any machine and run
# under `--network none`. This is packaging for the examples — the engine's
# sandbox is still a git worktree (spec 0011 §2), not a container.
FROM python:3.12-slim

LABEL org.opencontainers.image.title="markov-ci examples" \
      org.opencontainers.image.source="https://github.com/deghosal-2026/markov-ci" \
      org.opencontainers.image.licenses="Apache-2.0"

# git is the sandbox's only external dependency.
RUN apt-get update \
    && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

# Install the package plus pytest (the offline demos' sandbox runs `pytest -q`).
WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir . pytest

# The demos, each made a real git repository (the sandbox creates git worktrees).
COPY examples /examples
RUN set -eux; \
    for repo in /examples/*/repo; do \
        git -C "$repo" init -q; \
        git -C "$repo" config user.email demo@example.com; \
        git -C "$repo" config user.name "markov-ci demo"; \
        git -C "$repo" add -A; \
        git -C "$repo" commit -qm "demo baseline"; \
    done

# Relative demo telemetry paths (`examples/<demo>/.markov-ci/...`) resolve from
# the root, matching the `/examples/...` paths in the docs.
WORKDIR /
ENTRYPOINT ["markov-ci"]
CMD ["--help"]
