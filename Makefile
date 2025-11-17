.PHONY: help test test-verbose format lint check install clean run

# Default target
help:
	@echo "Available commands:"
	@echo "  make install      - Install dependencies with uv"
	@echo "  make test         - Run tests with pytest"
	@echo "  make test-verbose - Run tests with verbose output"
	@echo "  make format       - Format code with ruff"
	@echo "  make lint         - Check code style with ruff"
	@echo "  make check        - Run both lint and test"
	@echo "  make clean        - Remove cache files"
	@echo "  make run          - Run the browser without arguments"
	@echo "  make run URL=...  - Run the browser with a specific URL"

# Install dependencies
install:
	uv sync

# Run tests
test:
	uv run pytest tests/

# Run tests with verbose output
test-verbose:
	uv run pytest tests/ -v

# Format code
format:
	uv run ruff format .
	uv run ruff check --fix .

# Check code style
lint:
	uv run ruff check .

# Run both lint and test
check: lint test

# Clean cache files
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

# Run the browser
run:
ifdef URL
	uv run python url.py $(URL)
else
	uv run python url.py
endif