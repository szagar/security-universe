# Security Model

`Security` represents one tradable instrument.

Every tradable instrument must be represented by a `Security`: stocks, ETFs,
futures, options, crypto, FX, bonds, and OTC instruments.

## Identity Fields

| Field | Purpose |
| --- | --- |
| `security_id` | Canonical application identifier |
| `symbol` | Vendor or broker symbol |
| `short_name` | Human-readable display name |

`short_name` precedence:

1. Explicit caller value
2. Resolver supplied value
3. `symbol`

## Non-Membership Rule

`Security` must not contain membership-specific information.

Do not store these on `Security`:

- watchlist reason
- restricted-list reason
- index weight
- `added_by`
- import source
- universe-specific expiration
- membership-specific tags

Those belong on `UniverseMember`.

## Option Identity

For listed options, canonical `security_id` uses option root:

```text
option:{option_root}:{expiry}:{call|put}:{strike}
```

Examples:

```text
SPX260619C06100000  -> option:SPX:2026-06-19:call:6100
SPXW260619C06100000 -> option:SPXW:2026-06-19:call:6100
AAPL260918P00250000 -> option:AAPL:2026-09-18:put:250
```

The option `short_name` also uses option root:

```text
SPX 6100C 2026-06-19
SPXW 6100C 2026-06-19
AAPL 250P 2026-09-18
```

AM/PM expiration session and settlement type are enrichment fields. They are
not embedded into canonical identity.

## Option Root vs Underlying

For some products, option root and underlying differ:

```text
option_root = SPXW
underlying  = SPX
```

This matters because `SPX` and `SPXW` are different listed option products even
though both reference the SPX index.

## Adjusted Options

Adjusted options can be represented through option-root rules:

```yaml
AAPL1:
  underlying: AAPL
  expiration_session: pm
  settlement_type: physical
  contract_multiplier: 100
  deliverable_type: adjusted
  deliverable_description: "Adjusted option contract from corporate action"
  deliverable:
    cash: 12.37
    shares:
      AAPL: 100
```

The parser identifies option identity. Configuration enriches deliverable
semantics. The package does not infer corporate-action deliverables from market
data or corporate-action feeds.
