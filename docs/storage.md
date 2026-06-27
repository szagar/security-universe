# Storage Contract

Storage is abstracted behind `UniverseStore`.

Reference implementations:

- `InMemoryUniverseStore`
- `SQLiteUniverseStore`

Every store implementation must pass the same contract tests.

## Responsibilities

Stores persist:

- `Universe`
- `UniverseMember`
- nested `Security`
- resolver-enriched fields
- deliverable metadata
- tags and metadata

Stores do not run resolvers. Resolver invocation belongs to
`UniverseRegistry`.

## Membership Uniqueness

Preferred key:

```text
(universe_name, security.security_id)
```

Fallback if unresolved:

```text
(universe_name, security.symbol)
```

The unresolved fallback may be expanded during implementation if needed for
multi-asset ambiguity, but it must be deterministic.

## SQLite Requirements

SQLite should preserve all `Security` fields, including option fields:

- `option_root`
- `underlying`
- `expiry`
- `strike`
- `option_type`
- `expiration_session`
- `settlement_type`
- `contract_multiplier`
- `deliverable_type`
- `deliverable_description`
- `deliverable_json`

SQLite may normalize common fields and store complex values as JSON.

## Minimum Behavior

All stores must support:

- create universe
- delete universe
- get universe
- list universes
- add member
- remove member
- list members
- contains

## Contract Tests

Every store must pass tests for:

- universe CRUD
- duplicate universe handling
- member add/remove
- member uniqueness
- active/expired member filtering
- nested `Security` round trip
- resolver-enriched option field round trip
- adjusted deliverable round trip
- tags and metadata round trip
- behavior parity between in-memory and SQLite stores
