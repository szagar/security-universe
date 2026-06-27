# Implementation Plan

The first implementation slice is underway on the feature branch. This document
tracks the remaining path to a first PyPI release.

## Phase 1: Package Foundation

- finalize package metadata
- choose license
- update `pyproject.toml`
- expose CLI command as `securities`
- add package exports
- add CI configuration

Status: implemented.

## Phase 2: Core Models

- implement enums
- implement `Security`
- implement `Universe`
- implement `UniverseMember`
- implement package exceptions

Acceptance:

- models import from `security_universe`
- model tests pass
- README model snippets are executable

Status: implemented.

## Phase 3: Resolver Layer

- implement `SecurityIdResolver`
- implement OCC parser in `security_universe/resolvers/occ.py`
- load packaged YAML rules from `resolvers/data/`
- support user overrides
- support adjusted deliverable enrichment

Acceptance:

- resolver tests from `docs/resolver.md` pass
- resolver does not mutate input security
- rules are loaded from package data, not hard-coded

Status: implemented.

## Phase 4: Storage Layer

- implement `UniverseStore` protocol
- implement in-memory store
- implement SQLite store
- write shared store contract tests

Acceptance:

- both stores pass identical contract tests
- nested `Security` and deliverable data round trip

Status: implemented for in-memory and SQLite stores.

## Phase 5: Registry

- implement `UniverseRegistry`
- invoke resolver before persistence
- implement include/exclude resolution
- implement membership checks

Acceptance:

- registry tests pass
- examples can use memory and SQLite registries

Status: implemented.

## Phase 6: Import/Export

- CSV import/export
- JSON import/export
- resolver-aware imports

Status: implemented.

## Phase 7: CLI

- implement `securities`
- mirror registry operations under `securities universe`
- support resolver inspection under `securities security`
- support packaged and custom option-root rules under `securities rules`
- support storage inspection under `securities store`
- support db and option-rules config
- support text and JSON output

Status: implemented.

## Phase 8: Examples and Documentation

- complete executable examples
- verify README
- verify docs and examples
- update changelog

Status: examples are executable; documentation and changelog should be kept in
sync as implementation changes.

## Phase 9: GitHub and PyPI Release

- finalize `pyproject.toml` metadata
- choose and commit license
- add GitHub Actions CI
- add release workflow
- validate package data in built wheel
- publish first to TestPyPI
- publish to PyPI

Status: metadata, license, CI, release workflow, and package-data validation are
in place. TestPyPI and PyPI publishing remain.

Acceptance:

- CI passes on GitHub
- `uv build` creates wheel and sdist
- clean environment install works from built wheel
- TestPyPI install works
- PyPI install works
- `securities --help` works after install

## Deferred

- PostgreSQL store
- dynamic universe execution
- audit history
- REST API
- web UI
- broker integrations
- market-data integrations
