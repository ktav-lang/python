.DEFAULT_GOAL := help
.PHONY: help dev install test lint typecheck format fmt clean build sdist bench docs

help:  ## Show this help message
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

dev:  ## Build + install the extension in editable mode (debug profile)
	maturin develop

install:  ## Same as `dev` but with release-profile optimisations
	maturin develop --release

test:  ## Run the pytest suite (needs the extension to be installed)
	pytest -v

test-conformance:  ## Run the spec conformance subset only
	pytest -v tests/test_conformance.py

lint:  ## ruff check + ruff format check
	ruff check .
	ruff format --check .

typecheck:  ## mypy --strict on the Python source
	mypy python

rust-lint:  ## cargo fmt --check + cargo clippy -D warnings
	cargo fmt --check
	cargo clippy --all-targets -- -D warnings

format:  ## Autofix all formatting (ruff + cargo fmt)
	ruff check --fix .
	ruff format .
	cargo fmt

fmt: format  ## Alias for `format`

all:  ## Run lint + typecheck + rust-lint + test
	$(MAKE) lint
	$(MAKE) typecheck
	$(MAKE) rust-lint
	$(MAKE) test

clean:  ## Remove build artefacts
	rm -rf target/ dist/ build/ *.egg-info .pytest_cache .mypy_cache .ruff_cache

build:  ## Build a release wheel for the local platform
	maturin build --release --out dist

sdist:  ## Build a source distribution
	maturin sdist --out dist
