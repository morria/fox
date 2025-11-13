.PHONY: help install install-dev test test-cov lint format type-check clean all

help:
	@echo "Fox BBS Development Commands"
	@echo "============================"
	@echo "install        Install production dependencies"
	@echo "install-dev    Install development dependencies"
	@echo "test           Run tests"
	@echo "test-cov       Run tests with coverage report"
	@echo "lint           Run linters (flake8)"
	@echo "format         Format code with black and isort"
	@echo "type-check     Run type checking with mypy"
	@echo "clean          Remove build artifacts and cache files"
	@echo "all            Run format, lint, type-check, and test"

install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements.txt
	pip install -r requirements-dev.txt

test:
	pytest tests/ -v

test-cov:
	pytest tests/ -v --cov=src --cov-report=term-missing --cov-report=html

lint:
	flake8 src/ tests/ fox_bbs.py

format:
	isort src/ tests/ fox_bbs.py
	black src/ tests/ fox_bbs.py

type-check:
	mypy src/ fox_bbs.py

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name '*.pyc' -delete

all: format lint type-check test
