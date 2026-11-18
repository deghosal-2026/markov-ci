"""M13.41 (#125) — the whole suite proves it runs offline.

`tests/conftest.py` installs an autouse fixture that blocks outbound sockets; this
test asserts that block is actually in force, so "offline" is a checked claim.
"""

from __future__ import annotations

import socket

import pytest


def test_outbound_sockets_are_blocked() -> None:
    with pytest.raises(RuntimeError, match="blocked"):
        socket.create_connection(("1.1.1.1", 80), timeout=1)


def test_a_raw_socket_connect_is_blocked() -> None:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        with pytest.raises(RuntimeError, match="blocked"):
            sock.connect(("1.1.1.1", 80))
    finally:
        sock.close()
