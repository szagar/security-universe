# Architecture

## Purpose

`security-universe` manages named collections of tradable instruments without
becoming a broker SDK, market-data client, order router, risk engine, or
security master.

## Core Model

```text
Security
    ↓
UniverseMember
    ↓
Universe
    ↓
UniverseRegistry
        ├── UniverseStore
        └── SecurityIdResolver
```

## Security

`Security` is the primary domain object. Every tradable instrument is
represented by a `Security`, including stocks, ETFs, futures, options, crypto,
FX, bonds, and OTC instruments.

`Security` owns instrument identity:

- `security_id`
- `symbol`
- `short_name`
- `security_type`
- exchange and currency fields
- option identity fields
- resolver-enriched instrument metadata

`Security` must never contain universe-specific information.

## UniverseMember

`UniverseMember` is the first-class relationship between one `Security` and
one `Universe`.

It owns membership context:

- `member_id`
- `universe_name`
- `security`
- `weight`
- `active`
- `added_at`
- `added_by`
- `expires_at`
- `source`
- `reason`
- `tags`
- `metadata`

It must not own instrument identity.

## Universe

`Universe` owns collection metadata only:

- `name`
- `universe_type`
- `description`
- `tags`
- `enabled`
- `source_type`
- `definition`
- `metadata`

It does not own `Security` identity and should not directly store raw symbol
lists.

## UniverseRegistry

`UniverseRegistry` is the main application-facing service. It coordinates:

- validation
- resolver invocation
- persistence
- member management
- membership checks
- include/exclude resolution
- import/export

## Resolver Layer

Resolvers operate only on `Security`. They enrich identity and instrument
metadata, such as OCC option parsing and option-root rule enrichment.

Resolvers must be deterministic, stateless, thread-safe, and local. They must
not modify `Universe` or `UniverseMember`.

## Storage Layer

Storage is abstracted behind `UniverseStore`. In-memory and SQLite stores must
pass the same behavioral contract. SQLite may normalize or denormalize
internally, but public behavior must preserve the `Security` /
`UniverseMember` / `Universe` boundary.

## Boundaries

Owns:

- security identity
- universe management
- membership context
- resolver hooks
- local option-root enrichment
- supplied adjusted-option deliverable data
- persistence
- import/export
- CLI

Does not own:

- market data
- broker connectivity
- orders
- positions
- portfolio accounting
- risk calculations
- corporate-action feed processing
- enterprise security-master workflows
