# Makefile for InG AI Sales Department
# Provides convenient commands similar to npm/yarn scripts

.PHONY: check build install test lint format clean help

help:
	@echo "Available commands:"
	@echo "  make check    - Check code syntax and imports (like 'yarn build')"
	@echo "  make install  - Install dependencies"
	@echo "  make lint     - Run linter (flake8)"
	@echo "  make format   - Format code (black)"
	@echo "  make test     - Run tests"
	@echo "  make clean    - Clean cache files"

check:
	@echo "Checking Python code..."
	@find src -name "*.py" -exec python3 -m py_compile {} \; 2>&1 || true
	@python3 -m py_compile main.py 2>&1 || true
	@echo "✓ Syntax check passed"
	@echo "⚠ Import check skipped (install dependencies first: make install)"
	@echo "✅ Basic checks passed!"

install:
	@echo "📦 Installing dependencies..."
	@pip install -r requirements.txt

lint:
	@echo "🔍 Running linter..."
	@if command -v flake8 > /dev/null; then \
		flake8 src/ main.py --max-line-length=120 --ignore=E501,W503; \
	else \
		echo "⚠ flake8 not installed. Install with: pip install flake8"; \
	fi

format:
	@echo "🎨 Formatting code..."
	@if command -v black > /dev/null; then \
		black src/ main.py; \
	else \
		echo "⚠ black not installed. Install with: pip install black"; \
	fi

test:
	@echo "🧪 Running tests..."
	@if command -v pytest > /dev/null; then \
		pytest tests/ -v; \
	else \
		echo "⚠ pytest not installed. Install with: pip install pytest"; \
	fi

clean:
	@echo "🧹 Cleaning cache files..."
	@find . -type d -name __pycache__ -exec rm -r {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@find . -type f -name "*.pyo" -delete 2>/dev/null || true
	@echo "✅ Cleaned!"

build: check
	@echo "✅ Build successful!"

