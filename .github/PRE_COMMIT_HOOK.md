# Pre-Commit Hook Setup

This repository includes a pre-commit hook that automatically runs all CI checks before allowing commits. This ensures that all committed code passes the same checks that run in GitHub Actions.

## What the Hook Does

The pre-commit hook runs these checks (same as CI):

1. **Black formatting** - Ensures code follows black style
2. **isort** - Checks import sorting (if installed)
3. **Flake8 linting** - Checks for code quality issues
4. **Mypy type checking** - Verifies type hints are correct
5. **Python syntax** - Validates all Python files compile

**Note:** Unit tests are NOT run by the pre-commit hook (they run in GitHub Actions CI). Always monitor CI results after pushing to ensure tests pass.

If any check fails, the commit is blocked and you'll see exactly what needs to be fixed.

## Installation

The hook is already installed at `.git/hooks/pre-commit` and is executable.

**For new clones of the repository:**

```bash
# The hook file exists but may not be executable
chmod +x .git/hooks/pre-commit
```

## Usage

The hook runs automatically on every `git commit`. You don't need to do anything special.

### Example Success

```bash
$ git commit -m "Add new feature"
Running pre-commit checks...

1/5 Checking code formatting with black...
✅ Black formatting passed

2/5 Checking import sorting with isort...
✅ isort check passed

3/5 Linting with flake8...
✅ Flake8 linting passed

4/5 Type checking with mypy...
✅ Mypy type checking passed

5/5 Checking Python syntax...
✅ Python syntax valid

=========================================
✅ All pre-commit checks passed!
=========================================

⚠️  NOTE: Unit tests are NOT run by this hook.
    Tests will run in GitHub Actions CI.
    Monitor the CI results after pushing!

[main abc1234] Add new feature
 1 file changed, 10 insertions(+)
```

### Example Failure

```bash
$ git commit -m "Add buggy code"
Running pre-commit checks...

1/5 Checking code formatting with black...
would reformat src/example.py

❌ Black formatting failed!
Run: black src/ tests/ fox_bbs.py
Or: make format
```

## Fixing Issues

When the hook blocks a commit, follow the instructions to fix the issue:

### Formatting Issues

```bash
# Auto-fix formatting
black src/ tests/ fox_bbs.py
isort src/ tests/ fox_bbs.py

# Or use make
make format

# Then try committing again
git commit -m "Your message"
```

### Linting Issues

```bash
# Check what's wrong
make lint

# Fix the issues manually
# Then commit
git commit -m "Your message"
```

### Type Checking Issues

```bash
# Check what's wrong
make type-check

# Fix the type hints manually
# Then commit
git commit -m "Your message"
```

## Bypassing the Hook (NOT Recommended)

In rare cases where you need to bypass the hook (e.g., saving work in progress):

```bash
git commit --no-verify -m "WIP: save progress"
```

**WARNING:** Bypassing the hook will likely cause CI to fail on GitHub. Only use this for local WIP commits that you'll fix before pushing.

## Running Checks Manually

You can run all checks manually without committing:

```bash
# Run all checks
make format    # Auto-fix formatting
make lint      # Check linting
make type-check # Check types

# Or run everything at once
make all
```

## Benefits

✅ **Catch errors early** - Find issues before CI runs
✅ **Faster feedback** - Get immediate feedback locally vs waiting for GitHub Actions
✅ **Cleaner history** - No "fix linting" commits after the fact
✅ **Save CI minutes** - Reduce failed CI runs
✅ **Consistent quality** - Every commit meets quality standards

## Troubleshooting

### Hook doesn't run

```bash
# Make sure it's executable
chmod +x .git/hooks/pre-commit

# Verify it exists
ls -la .git/hooks/pre-commit
```

### Hook is too slow

The hook typically runs in 5-10 seconds. If it's slower:
- Make sure you're not checking too many files
- Consider running `make format` before committing to reduce checks

### isort not found

The hook gracefully skips isort if it's not installed. To install:

```bash
pip install isort
# Or
make install-dev
```

## Customization

To modify what the hook checks, edit `.git/hooks/pre-commit`.

**Note:** Changes to `.git/hooks/pre-commit` are local only (not tracked by git). To share changes, update this documentation and ask developers to update their hook manually.
