"""``python -m markov_ci`` — run the CLI without relying on the console script.

The composite Action (action.yml) invokes this form so it does not depend on the
``markov-ci`` script being on PATH.
"""

from __future__ import annotations

from markov_ci.cli import app

if __name__ == "__main__":
    app()
