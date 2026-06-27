# Documentation Index

This directory is the canonical implementation handoff for
`security-universes`.

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
- `src/security_universes/resolvers/data/*.yaml` contains packaged resolver
  configuration data.
- `diagrams/` contains visual architecture aids.
- Root files such as `README.md`, `CHANGELOG.md`, `CONTRIBUTING.md`, and
  `LICENSE` are package/project metadata, not implementation contracts.

## Current Implementation Status

The project is still pre-implementation. The current package skeleton exists,
but the domain models, registry, stores, resolvers, CLI, and tests still need
to be built from these docs.
