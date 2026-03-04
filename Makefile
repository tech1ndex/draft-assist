.DEFAULT_GOAL := help
PYMODULE := draft_assist
TESTS := tests
INSTALL_STAMP := .install.stamp
POETRY := $(shell command -v poetry 2> /dev/null)
MYPY := $(shell command -v mypy 2> /dev/null)

.PHONY: help
help:
	@echo "Please use 'make <target>' where <target> is one of"
	@echo ""
	@echo "  install     install packages and prepare environment"
	@echo "  lint        run the code linters"
	@echo "  test        run all the tests"
	@echo "  all         install, lint, and test"
	@echo "  clean       remove all temporary files"
	@echo ""

install: $(INSTALL_STAMP)
$(INSTALL_STAMP): pyproject.toml poetry.lock
	@if [ -z $(POETRY) ]; then echo "Poetry could not be found. See https://python-poetry.org/docs/"; exit 2; fi
	$(POETRY) install --with dev,test
	touch $(INSTALL_STAMP)

.PHONY: lint
lint: $(INSTALL_STAMP)
ifdef MYPY
	$(POETRY) run mypy src/$(PYMODULE) --config-file=pyproject.toml
endif
	$(POETRY) run ruff check src/$(PYMODULE) $(TESTS)
	$(POETRY) run ruff format --check src/$(PYMODULE) $(TESTS)

.PHONY: format
format: $(INSTALL_STAMP)
	$(POETRY) run ruff check --fix src/$(PYMODULE) $(TESTS)
	$(POETRY) run ruff format src/$(PYMODULE) $(TESTS)

.PHONY: test
test: $(INSTALL_STAMP)
	$(POETRY) run pytest $(TESTS) -v --cov=src/$(PYMODULE)

.PHONY: all
all: install lint test

.PHONY: clean
clean:
	find . -type d -name "__pycache__" | xargs rm -rf {};
	rm -rf $(INSTALL_STAMP) .coverage .mypy_cache .pytest_cache .ruff_cache
