# Auralis Build System Makefile

.PHONY: help clean install test build package dev

help:		## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

clean:		## Clean build artifacts
	python build_auralis.py --clean
	rm -rf build/ dist/ __pycache__/ *.egg-info/
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -type d -exec rm -rf {} +

install:	## Install dependencies
	pip install -r requirements-desktop.txt
	pip install pyinstaller

test:		## Run test suite
	python run_all_tests.py

build:		## Build application (with tests)
	python build_auralis.py

build-fast:	## Build application (skip tests)
	python build_auralis.py --skip-tests

package:	## Build portable package only
	python build_auralis.py --skip-tests --portable-only

dev:		## Development setup
	pip install -e .
	pip install -r requirements-desktop.txt
	pip install pytest pytest-cov pyinstaller

# Platform-specific builds
build-linux:	## Build Linux packages
	python build_auralis.py --skip-tests

build-windows:	## Build Windows packages (Windows only)
	python build_auralis.py --skip-tests

build-macos:	## Build macOS packages (macOS only)
	python build_auralis.py --skip-tests

# Quality assurance
lint:		## Run code linting
	@echo "Running basic Python syntax check..."
	python -m py_compile auralis_gui.py
	find auralis/ -name "*.py" -exec python -m py_compile {} \;

typecheck:	## Run type checking (if mypy available)
	@if command -v mypy >/dev/null 2>&1; then \
		echo "Running mypy type checking..."; \
		mypy auralis_gui.py --ignore-missing-imports; \
	else \
		echo "mypy not available, skipping type checking"; \
	fi

# Release management
release:	## Create release build with all platforms
	$(MAKE) clean
	$(MAKE) test
	$(MAKE) build

# Docker builds (if needed)
docker-build:	## Build using Docker
	docker build -t auralis-builder .
	docker run --rm -v $(PWD)/dist:/app/dist auralis-builder

# Documentation
docs:		## Generate documentation
	@echo "Documentation available in docs/ directory"
	@echo "Main README: README.md"
	@echo "Cleanup summary: REPOSITORY_CLEANUP_SUMMARY.md"