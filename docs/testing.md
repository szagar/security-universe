# Testing Guide

Testing should scale with the contracts.

## Unit Tests

- Pydantic model defaults and validation
- enum values
- identity formatting
- OCC symbol parsing
- strike formatting
- option-root rule loading and merging

## Resolver Tests

See [Resolver Contract](resolver.md#required-resolver-tests).

## Store Contract Tests

Every `UniverseStore` implementation must run the same contract suite:

- in-memory store
- SQLite store
- future stores

The contract suite should verify behavior rather than implementation details.

## Registry Tests

- creates, gets, lists, and deletes universes
- adds and removes members
- invokes resolver before persistence
- returns `UniverseMember` from `add_member`
- supports `contains`
- resolves include/exclude sets
- preserves membership metadata

## CLI Tests

- command parsing
- non-zero exits for invalid commands
- JSON/text output modes
- import/export round trip
- resolver rules option
- `doctor`

## Documentation Tests

README and examples should execute successfully before release.
