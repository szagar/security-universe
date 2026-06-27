# Documentation Index

This directory is the canonical implementation handoff for
`security-universe`.

Read these documents in order:

1. [Architecture](architecture.md)
2. [API Contract](api.md)
3. [Security Model](security.md)
4. [Resolver Contract](resolver.md)
5. [Storage Contract](storage.md)
6. [CLI Reference](cli.md)
7. [Examples Guide](examples.md)
8. [Testing Guide](testing.md)
9. [Implementation Plan](implementation-plan.md)
10. [GitHub and PyPI Release Plan](release.md)
11. [Decisions](decisions.md)
12. [Roadmap](roadmap.md)

## Handoff Rules

- `docs/` is the source of truth for implementation.
- `src/security_universe/resolvers/data/*.yaml` contains packaged resolver
  configuration data.
- `diagrams/` contains visual architecture aids.
- Root files such as `README.md`, `CHANGELOG.md`, `CONTRIBUTING.md`, and
  `LICENSE` are package/project metadata, not implementation contracts.

## Current Implementation Status

The first implementation slice exists on the feature branch. Core models,
resolvers, in-memory and SQLite stores, registry operations, import/export,
CLI commands, examples, and tests are implemented. The remaining release work
is TestPyPI/PyPI validation and any polish found during review.
