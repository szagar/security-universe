# security-universes

`security-universes` is a lightweight Python package for representing tradable
instruments as `Security` objects and organizing them into reusable named
collections called `Universe` objects.

The package is intended for trading systems, research tools, screeners,
automation, and risk/compliance workflows where the same instrument may appear
in many different contexts.

## Core Concepts

- `Security` answers: what instrument is this?
- `UniverseMember` answers: why or how is this security in this universe?
- `Universe` answers: what collection am I working with?
- `UniverseRegistry` is the main public service object.

The package separates instrument identity from universe membership. A
`Security` never owns universe-specific data such as restriction reason, index
weight, import source, expiration window, or who added it. That information
belongs on `UniverseMember`.

## Example

```python
from security_universes import Security, SecurityType, UniverseRegistry

registry = UniverseRegistry.sqlite("universes.db")

registry.create_universe("restricted", universe_type="restricted")
registry.create_universe("sp500", universe_type="index")

registry.add_member(
    "restricted",
    Security(symbol="AAPL", security_type=SecurityType.STOCK),
    reason="manual restriction",
    source="manual",
)

tradable = registry.resolve(
    include=["sp500"],
    exclude=["restricted"],
)
```

## CLI Shape

The planned CLI command is `securities`.

```bash
securities universe create restricted --type restricted
securities universe add restricted AAPL --security-type stock --reason "manual restriction"
securities universe members restricted
securities universe resolve --include sp500 --exclude restricted
```

## Documentation Handoff

The implementation handoff starts here:

- [Documentation Index](docs/README.md)
- [Architecture](docs/architecture.md)
- [API Contract](docs/api.md)
- [Security Model](docs/security.md)
- [Resolver Contract](docs/resolver.md)
- [Storage Contract](docs/storage.md)
- [CLI Reference](docs/cli.md)
- [Implementation Plan](docs/implementation-plan.md)

## Non-Goals

This package does not fetch market data, connect to brokers, place orders,
manage portfolios, calculate risk, process corporate-action feeds, or replace
an enterprise security master.
