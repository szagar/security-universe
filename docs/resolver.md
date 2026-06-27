# Resolver Contract

Resolvers enrich `Security` objects only. They must not mutate or interpret
`Universe` or `UniverseMember`.

## Responsibilities

A resolver may:

- generate `security_id`
- generate `short_name`
- parse vendor or industry-standard symbols
- populate missing instrument identity fields
- enrich instrument fields from local configuration

A resolver must not:

- perform network I/O
- call broker APIs
- call market-data APIs
- modify `Universe`
- modify `UniverseMember`
- override explicit caller-supplied identity fields unless replacement behavior
  is explicitly requested

Resolvers must be deterministic, local, stateless, and thread-safe.

## Precedence

Resolvers preserve explicit caller-supplied values.

Default precedence:

1. Caller-supplied `security_id`
2. Resolver-generated `security_id`
3. Caller-supplied `short_name`
4. Resolver-generated `short_name`
5. Caller-supplied instrument fields
6. Parsed instrument fields
7. Config-enriched instrument fields
8. Resolver fallback values

## OCC Option Resolver

OCC format:

```text
{option_root}{YYMMDD}{C|P}{strike * 1000 padded to 8 digits}
```

Example:

```text
SPXW260619C06100000
```

Parsed fields:

```text
option_root = SPXW
expiry      = 2026-06-19
option_type = call
strike      = 6100
```

Canonical identity:

```text
option:{option_root}:{expiry}:{call|put}:{strike}
```

Display name:

```text
{option_root} {strike}{C|P} {expiry}
```

## Parser Requirements

The OCC parser must:

- remove spaces and uppercase input
- reject invalid OCC symbols
- parse option root using 1-6 uppercase alphanumeric characters, starting
  with a letter, so adjusted roots such as `AAPL1` are supported
- parse expiry as `20YY-MM-DD`
- parse `C` as call and `P` as put
- parse strike as `Decimal(strike_digits) / Decimal("1000")`
- normalize strike display by removing trailing zeroes and trailing decimal
  points

## Packaged Rules

Default package rules live in:

```text
src/security_universe/resolvers/data/index_option_rules.yaml
src/security_universe/resolvers/data/adjusted_option_rules.yaml
```

Resolvers must load these rules from package data. Rule tables must not be
hard-coded in resolver logic.

Users may extend or override package defaults with YAML.

Rules may define:

- `underlying`
- `expiration_session`
- `settlement_type`
- `contract_multiplier`
- `deliverable_type`
- `deliverable_description`
- `deliverable`

The resolver parses identity. Configuration enriches semantics.

## Initial Index Rules

```yaml
SPX:
  underlying: SPX
  expiration_session: am
  settlement_type: cash

SPXW:
  underlying: SPX
  expiration_session: pm
  settlement_type: cash

NDX:
  underlying: NDX
  expiration_session: am
  settlement_type: cash

NDXP:
  underlying: NDX
  expiration_session: pm
  settlement_type: cash
```

## Initial Adjusted Option Rules

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

## Resolution Algorithm

Given a `Security` with an OCC option symbol:

1. Normalize and parse the symbol.
2. Read `option_root`, `expiry`, `option_type`, and `strike`.
3. Load packaged index and adjusted option-root defaults.
4. Merge user-supplied option-root overrides.
5. Generate `security_id` if missing.
6. Generate `short_name` if missing.
7. Set `security_type = option`.
8. Populate missing parsed option fields.
9. Populate missing enrichment fields from option-root rules.
10. Fall back to `underlying = option_root`, `expiration_session = unknown`,
    and `settlement_type = unknown` when no rule exists.
11. Return a copied/enriched `Security`; do not mutate the original.

## Required Resolver Tests

- valid SPX AM cash option
- valid SPXW PM cash option
- valid NDX and NDXP options
- call and put parsing
- decimal strike normalization
- whitespace and lowercase normalization
- invalid OCC symbol rejection
- preservation of explicit `security_id`
- preservation of explicit `short_name`
- preservation of explicit caller-supplied fields
- unknown option root fallback behavior
- user override of package option-root rules
- adjusted deliverable enrichment
- original `Security` object is not mutated
