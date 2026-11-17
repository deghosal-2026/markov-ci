.DEFAULT_GOAL := help

PY ?= python3

.PHONY: help test lint typecheck cov docs build clean

help:
	@echo "markov-ci make targets:"
	@echo "  help       show this message"
	@echo "  test       run the test suite"
	@echo "  lint       ruff check"
	@echo "  typecheck  mypy --strict"
	@echo "  cov        run tests with coverage"
	@echo "  docs       build the mkdocs site (strict)"
	@echo "  build      build sdist + wheel"
	@echo "  clean      remove caches and build artifacts"

test:
	$(PY) -m pytest

lint:
	$(PY) -m ruff check .

typecheck:
	$(PY) -m mypy

cov:
	$(PY) -m pytest --cov=markov_ci --cov-report=term-missing

docs:
	$(PY) -m mkdocs build --strict

build:
	$(PY) -m build

clean:
	rm -rf build dist .pytest_cache .mypy_cache .ruff_cache .coverage htmlcov
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
