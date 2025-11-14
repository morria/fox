# Claude Code Configuration

This directory contains configuration files for Claude Code to ensure high-quality, consistent code generation.

## Overview

The configuration files in this directory help Claude:
- Follow project coding standards
- Generate correct, type-safe code
- Write comprehensive tests
- Maintain code quality

## Files

- **README.md** (this file) - Overview of Claude configuration
- Future: Agent-specific configurations can be added here

## Using These Configurations

When Claude works on this project, it should:

1. **Read CLAUDE.md** for coding guidelines
2. **Follow the project structure** defined in docs/architecture.md
3. **Run quality checks** before committing:
   ```bash
   make format      # Format code
   make lint        # Check style
   make type-check  # Verify types
   make test        # Run tests
   ```

## Project Standards

See `CLAUDE.md` in the root directory for detailed coding guidelines including:

- Type hints requirements
- Testing requirements
- Code formatting standards
- Error handling patterns
- Thread safety guidelines
- Documentation requirements

## Quality Gates

All code must pass:
- ✓ Black formatting
- ✓ isort import sorting
- ✓ flake8 linting
- ✓ mypy type checking
- ✓ pytest test suite
- ✓ >80% code coverage

Run `make all` to verify all checks pass.
