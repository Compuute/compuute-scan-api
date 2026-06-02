# Contributing to compuute-scan-api

Thank you for considering a contribution. This document is short and meant to get a contributor productive in 15 minutes.

## TL;DR

1. Read [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) for the local setup.
2. Open an issue first if your change is non-trivial — it's faster to align on direction than to rewrite a PR.
3. Branch per issue: `git checkout -b fix/issue-N-short-name`.
4. Commit message **must reference the issue**: `fix: short summary (#N)` — the pre-commit hook enforces this.
5. Run `pytest tests/ -q && ruff check api/ main.py tests/` locally before pushing.
6. Open a PR against `main`. The CI workflow will run pytest + ruff + bandit automatically.
7. Sign-off your commits with `git commit --signoff` (DCO; we add Contributor Covenant via `CODE_OF_CONDUCT.md`).

## Scope of contributions we welcome

- Bug fixes for existing endpoints
- New L0/L1 detection rules in the underlying [compuute-scan](https://github.com/Compuute/compuute-scan) repo (PRs against that repo bump our pinned `COMPUUTE_SCAN_REF` automatically)
- Documentation improvements
- Test coverage (we target ≥10 fixtures per rule; we are nowhere near that)
- Performance improvements with reproducible benchmark numbers
- Security findings reported via [SECURITY.md](SECURITY.md) — do NOT open public issues for security

## Scope we deliberately do NOT accept

- Adding generic SCA features that duplicate Snyk/Aikido/Socket. See [docs/STRATEGY.md](docs/STRATEGY.md) for position lock.
- Removing the `_disclaimer` field from response payloads. The honesty pin is core product.
- Adding more package ecosystems beyond `npm/pypi/go/cargo/maven/nuget` without buyer demand signal.
- Suppressing false-positive findings without filing the FP class as a tracked upstream issue at `Compuute/compuute-scan` first.

## Code style

- `from __future__ import annotations` at the top of every Python file.
- Pydantic v2 (`ConfigDict`, `Field(..., description=...)`).
- Type hints on every public function.
- Docstrings on services + routes (FastAPI surfaces them in OpenAPI).
- `structlog` for logging — never `print`, never `logging.info`.
- No emojis in code, comments, or commit messages.

## PR review process

For a solo-maintained project this is short:

1. Author opens PR linked to an issue.
2. CI runs pytest + ruff + bandit. Author addresses any failures.
3. Daniel reviews within 7 days. Often faster.
4. Squash-merge to `main` with the PR title as commit message (must reference issue).
5. CI auto-runs release workflow if the merge results in a tag.

## What you can expect from us

- Acknowledge non-trivial PRs within 3 business days.
- Decision (accept / decline / change-request) within 7 business days.
- Credit in the [SECURITY-HALL-OF-FAME.md](SECURITY-HALL-OF-FAME.md) (planned) for security work, in CHANGELOG.md for feature work.
- A LinkedIn endorsement from Daniel Abbay for substantial contributions.

## Sign-off (DCO)

By contributing, you certify that you have the right to submit the work under the project's MIT license (Developer Certificate of Origin). Add `Signed-off-by: Your Name <you@example.com>` to each commit (`git commit --signoff`).

## Code of conduct

This project follows the [Contributor Covenant 2.1](CODE_OF_CONDUCT.md). In short: be respectful, focus on the technical work, no harassment.

Reports of unacceptable behavior: daniel@compuute.se.

## Questions

- Technical: open an issue
- Sales / partnerships: daniel@compuute.se
- Security: security@compuute.se (see SECURITY.md)
