# ai-pr-review-agent

A GitHub Action that posts an **advisory** AI review on pull requests: correctness bugs, security issues, missing tests, ranked by severity. A human reviewer always makes the call.

## Features
- Splits big diffs into batches under a size budget (oversized files are truncated, never silently dropped)
- Skips lockfiles, minified assets, images and build output
- Tolerant parsing: a malformed model reply yields an empty review instead of a crash
- `--dry-run` to preview locally; `--fail-on-high` to gate merges on high-severity findings
- Standard library HTTP only; the single dependency is the model SDK

## Setup
1. Add repository secret `ANTHROPIC_API_KEY`.
2. Copy `.github/workflows/pr-review.yml` and the `reviewer/` package into your repo (or call it from a shared workflow).
3. Open a PR. A comment appears within a minute.

## Local use
```bash
git diff main...HEAD > change.diff
ANTHROPIC_API_KEY=... python -m reviewer.cli --diff-file change.diff
```
`REVIEW_MODEL` selects the model.

## Security notes
- The workflow skips forked PRs (secrets are not available there, and untrusted code should not trigger paid calls).
- Diffs are sent to the model provider: do not enable on repositories whose code your policy forbids sharing.
- Treat output as a prompt for human attention, not an approval.

## Tests
```bash
pytest -q
```
