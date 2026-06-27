# GitHub and PyPI Release Plan

This document covers the work required to put `security-universe` on GitHub
and publish releases to PyPI.

## Release Goals

- public GitHub repository
- automated CI for tests, linting, and typing
- buildable Python package
- TestPyPI validation before first PyPI release
- PyPI release for `security-universe`
- repeatable release process

## Repository Setup

1. Choose the final license and replace the placeholder `LICENSE`.
2. Finalize package metadata in `pyproject.toml`.
3. Update root `README.md` with install, quick start, and documentation links.
4. Confirm `.gitignore` excludes local artifacts such as `.venv/`, caches,
   build outputs, and editor swap files.
5. Create a GitHub repository named `security-universe`.
6. Push the initial implementation branch.
7. Protect the default branch after CI is working.

Recommended GitHub repository settings:

- default branch: `main`
- require pull request review before merge
- require status checks before merge
- enable GitHub Actions
- enable trusted publishing to PyPI

## pyproject.toml Metadata

Before release, fill:

```toml
[project]
name = "security-universe"
description = "Security universe management for trading systems"
readme = "README.md"
requires-python = ">=3.12"
license = "MIT"
keywords = ["trading", "securities", "universes", "watchlists"]
classifiers = [
  "Development Status :: 3 - Alpha",
  "Programming Language :: Python :: 3",
  "Programming Language :: Python :: 3.12",
  "Typing :: Typed",
]

[project.urls]
Homepage = "https://github.com/szagar/security-universe"
Repository = "https://github.com/szagar/security-universe"
Issues = "https://github.com/szagar/security-universe/issues"
```

The planned CLI command is:

```toml
[project.scripts]
securities = "security_universe.cli:main"
```

## Package Data

Ensure packaged resolver YAML files are included in distributions:

```text
src/security_universe/resolvers/data/index_option_rules.yaml
src/security_universe/resolvers/data/adjusted_option_rules.yaml
```

The build backend must include these files in both wheel and sdist.

## CI Workflow

Create `.github/workflows/ci.yml`.

Required checks:

- install dependencies
- `ruff check .`
- `mypy src`
- `pytest`
- build package

Recommended command set:

```bash
uv sync --all-groups
uv run ruff check .
uv run mypy src
uv run pytest
uv build
```

## Release Workflow

Create `.github/workflows/release.yml`.

Recommended trigger:

- GitHub release publication

Use the separate TestPyPI workflow for manual pre-release validation.

Recommended release flow:

1. Run CI checks.
2. Build sdist and wheel.
3. Publish to PyPI using trusted publishing.

Use TestPyPI first until the package installs cleanly from a fresh virtual
environment.

## Manual First Release Checklist

Before first release:

- choose license: done
- update `pyproject.toml` metadata: done
- update CLI script to `securities`: done
- ensure package data is included: done
- replace placeholder example bodies with executable examples: done
- pass all tests: done locally
- pass lint and type checks: done locally
- build wheel and sdist: done locally
- inspect generated distributions: done locally
- install from local wheel in a clean virtual environment
- publish to TestPyPI
- install from TestPyPI in a clean virtual environment
- publish to PyPI
- create GitHub release notes

## Versioning

Use semantic versioning.

Initial implementation release:

```text
0.1.0
```

Patch releases fix bugs without changing public contracts.

Minor releases may add fields, stores, commands, or resolver capabilities.

Breaking changes require a major version once the package reaches `1.0.0`.

## First Release Acceptance Criteria

The first PyPI release is ready when:

- `pip install security-universe` works
- `import security_universe` works
- `from security_universe import Security, UniverseRegistry` works
- `securities --help` works
- README quick start runs
- examples run
- in-memory and SQLite stores pass the same contract tests
- OCC resolver tests pass
- packaged YAML rules load from installed wheel
- documentation links resolve
