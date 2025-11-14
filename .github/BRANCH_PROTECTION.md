# Branch Protection Configuration

This document provides instructions for configuring branch protection rules to require passing tests before merging.

## Overview

The Fox BBS repository has a GitHub Actions CI workflow (`.github/workflows/ci.yml`) that runs:
- Code formatting checks (black, isort)
- Linting (flake8)
- Type checking (mypy)
- Unit tests (pytest)
- Code coverage analysis

This document explains how to require these checks to pass before allowing merges.

## Configuration Steps

### 1. Navigate to Branch Protection Settings

1. Go to your GitHub repository: `https://github.com/morria/fox`
2. Click on **Settings** (you need admin access)
3. In the left sidebar, click **Branches**
4. Under "Branch protection rules", click **Add rule** (or edit existing rule)

### 2. Configure Protection Rule

#### Branch Name Pattern
Enter the branch name pattern: `main` (or `master` if that's your default branch)

You may also want to protect other important branches. Consider adding protection for:
- Pattern: `main` - protects the main branch
- Pattern: `master` - if using master as default
- Pattern: `claude/*` - protects all Claude-generated branches

#### Required Settings

**Enable the following settings:**

✅ **Require a pull request before merging**
   - Require approvals: 1 (recommended, or 0 if you're the only contributor)
   - Dismiss stale pull request approvals when new commits are pushed

✅ **Require status checks to pass before merging**
   - This is the CRITICAL setting for requiring tests to pass
   - Enable: "Require branches to be up to date before merging"

   **Status checks to require:**
   - `test` - This is the job name from `.github/workflows/ci.yml`

   Note: You may need to have at least one PR with the CI workflow running before
   GitHub recognizes the "test" status check as available to select.

✅ **Require conversation resolution before merging** (optional but recommended)
   - Ensures all PR comments are addressed

✅ **Do not allow bypassing the above settings** (recommended)
   - Prevents admins from bypassing these rules
   - Uncheck if you need emergency override capability

#### Optional but Recommended Settings

⬜ **Require linear history** (optional)
   - Enforces a clean git history
   - May require rebasing instead of merge commits

⬜ **Require signed commits** (optional)
   - Requires GPG/SSH commit signing
   - Adds extra security but requires setup

### 3. Python Version Matrix

The CI workflow tests against Python 3.9, 3.10, and 3.11. All versions must pass.
The status check name is `test` regardless of Python version.

### 4. Save Configuration

Click **Create** (or **Save changes**) at the bottom of the page.

## Verification

After configuring branch protection:

1. Create a test branch
2. Make a small change (e.g., add a comment)
3. Create a pull request to main
4. Verify that:
   - The CI workflow runs automatically
   - You cannot merge until all checks pass
   - A message appears: "Merging is blocked" until tests pass

## Troubleshooting

### "No status checks found" Error

If you don't see the "test" status check available:

1. Create a PR first (any small change)
2. Wait for the CI workflow to run
3. Go back to branch protection settings
4. The "test" check should now appear in the dropdown

### Tests Not Running on PRs

Verify that `.github/workflows/ci.yml` includes:
```yaml
on:
  pull_request:
    branches: [ main, master ]
```

### Blocking Your Own Merges

If you're the only contributor and don't want to wait for reviews:
- Set "Required approvals" to 0
- Keep "Require status checks to pass" enabled
- This allows you to merge after tests pass without waiting for review

## Alternative: GitHub API Configuration

If you have a GitHub personal access token with repo permissions, you can configure
branch protection via the API:

```bash
# Set your token
export GITHUB_TOKEN="your-token-here"

# Configure branch protection
curl -X PUT \
  -H "Authorization: token $GITHUB_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/repos/morria/fox/branches/main/protection \
  -d '{
    "required_status_checks": {
      "strict": true,
      "contexts": ["test"]
    },
    "enforce_admins": true,
    "required_pull_request_reviews": {
      "required_approving_review_count": 0
    },
    "restrictions": null
  }'
```

## Summary

**Key Point:** Once configured, no code can be merged to protected branches until:
- ✅ All formatting checks pass (black, isort)
- ✅ All linting checks pass (flake8)
- ✅ All type checks pass (mypy)
- ✅ All unit tests pass (pytest)
- ✅ Code coverage is acceptable

This ensures code quality and prevents broken code from being merged.
