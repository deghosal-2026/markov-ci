"""Container isolation for validation (ADR-0012 §6).

When a container image is configured, the failing/regression command runs inside a
container instead of on the host:

- ``--network=none`` — no network;
- ``--read-only`` root filesystem, with the checkout mounted **read-only** at
  ``/src``;
- a **tmpfs work dir** (``/work``) the checkout is copied into, so the tests can
  write without touching the read-only source;
- a **non-root** user.

This is the real execution boundary; the host-clone path is the interim default.
"""

from __future__ import annotations

import os
from collections.abc import Sequence
from pathlib import Path

DEFAULT_CONTAINER_IMAGE = "python:3.12-slim"
CONTAINER_SRC = "/src"
CONTAINER_WORKDIR = "/work"
_COPY_AND_RUN = 'cp -R /src/. /work/ && exec "$@"'


def non_root_user() -> str:
    """Return a ``uid:gid`` string that is never root."""
    getuid = getattr(os, "getuid", None)
    getgid = getattr(os, "getgid", None)
    uid = getuid() if getuid is not None else 65534
    gid = getgid() if getgid is not None else 65534
    if uid == 0:
        return "65534:65534"
    return f"{uid}:{gid}"


def container_command(
    *,
    image: str,
    clone: str | Path,
    command: Sequence[str],
    user: str | None = None,
) -> list[str]:
    """Build the ``docker run`` argv that validates ``command`` in a container."""
    source = f"{os.path.abspath(clone)}:{CONTAINER_SRC}:ro"
    return [
        "docker",
        "run",
        "--rm",
        "--network=none",
        "--read-only",
        "--tmpfs",
        f"{CONTAINER_WORKDIR}:mode=1777",
        "--tmpfs",
        # the container's own /tmp tmpfs, not a host temp dir (ADR-0012 §6)
        "/tmp",  # nosec B108
        "--user",
        user or non_root_user(),
        "-e",
        "TMPDIR=/tmp",
        "-e",
        "PYTHONDONTWRITEBYTECODE=1",
        "-v",
        source,
        "-w",
        CONTAINER_WORKDIR,
        image,
        "sh",
        "-c",
        _COPY_AND_RUN,
        "_",
        *command,
    ]


__all__ = [
    "CONTAINER_SRC",
    "CONTAINER_WORKDIR",
    "DEFAULT_CONTAINER_IMAGE",
    "container_command",
    "non_root_user",
]
