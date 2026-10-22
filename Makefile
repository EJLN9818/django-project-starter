# Convenience targets for developing the template itself. Requires GNU make.
PYTHON ?= python
DEST ?= ../new-project

.DEFAULT_GOAL := help
.RECIPEPREFIX = >

.PHONY: help install test lint fmt generate

help: ## Show this help
> @grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-10s\033[0m %s\n", $$1, $$2}'

install: ## Install development dependencies
> $(PYTHON) -m pip install -r requirements-dev.txt

test: ## Run the template test suite
> $(PYTHON) -m pytest

lint: ## Check linting and formatting
> ruff check .
> black --check .

fmt: ## Auto-fix linting and formatting
> ruff check --fix .
> black .

generate: ## Generate a project: make generate DEST=../my-project
> copier copy "$(CURDIR)" "$(DEST)"
