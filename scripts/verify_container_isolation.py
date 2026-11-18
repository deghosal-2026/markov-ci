#!/usr/bin/env python3
"""Live container-isolation check for M13.18 (#102).

Drives the real `WorktreeValidator` in container mode end-to-end: a git repo is
cloned, a patch applied, and the command run inside `docker run` with a read-only
checkout, a tmpfs work dir, no network and a non-root user.

Usage: python3 scripts/verify_container_isolation.py [IMAGE]
Requires a Docker daemon; run manually or from a Docker-enabled CI job.
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from markov_ci.engine.validation import WorktreeValidator  # noqa: E402

PATCH = "--- a/app.py\n+++ b/app.py\n@@ -1 +1 @@\n-VALUE = 1\n+VALUE = 2\n"

CHECK = (
    "import os, pathlib, socket;"
    "print('APP=' + pathlib.Path('app.py').read_text().strip());"
    "pathlib.Path('scratch.txt').write_text('ok');"
    "print('WROTE=' + pathlib.Path('scratch.txt').read_text());"
    "print('UID=' + str(os.getuid()));"
    "s = socket.socket(); s.settimeout(2);"
    "print('NET=' + str(s.connect_ex(('1.1.1.1', 80))))"
)


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)


def main() -> int:
    image = sys.argv[1] if len(sys.argv) > 1 else "python:3.12-slim"
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp) / "repo"
        repo.mkdir()
        _git(repo, "init", "-q")
        _git(repo, "config", "user.email", "demo@example.com")
        _git(repo, "config", "user.name", "demo")
        (repo / "app.py").write_text("VALUE = 1\n", encoding="utf-8")
        _git(repo, "add", "-A")
        _git(repo, "commit", "-qm", "base")

        with WorktreeValidator(
            repo, root=Path(tmp) / "validator", container_image=image,
        ) as validator:
            result = validator.apply_and_test(
                PATCH, ["python3", "-c", CHECK], allow_write=("app.py",),
            )

        print(result.output)
        if result.output.strip():
            pass
        assert result.applied, "the patch did not apply"
        assert result.passed, f"the container command failed:\n{result.output}"
        out = result.output
        assert "APP=VALUE = 2" in out, "the patched checkout was not readable"
        assert "WROTE=ok" in out, "the tmpfs work dir was not writable"
        assert "UID=0" not in out, "the container ran as root"
        assert "NET=0" not in out, "the container had network access"
        # the host repo is untouched by the container run
        assert (repo / "app.py").read_text(encoding="utf-8") == "VALUE = 1\n"
        status = subprocess.run(
            ["git", "-C", str(repo), "status", "--porcelain"],
            check=True, capture_output=True, text=True,
        )
        assert status.stdout.strip() == "", "the host repo was modified"
    print("container isolation verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
