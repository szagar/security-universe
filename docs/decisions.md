# Decisions

Accepted decisions:

- `Security` is the primary instrument identity object.
- Every tradable instrument is represented by a `Security`.
- `Security` must not contain universe-specific information.
- `Universe` is the first-class collection object.
- Watchlists, whitelists, restricted lists, bot input lists, index lists,
  screener results, and portfolios are represented as `UniverseType` values.
- `UniverseMember` is first-class and represents the relationship between one
  `Security` and one `Universe`.
- `Universe` owns collection metadata only.
- `UniverseMember` owns membership context only.
- Resolvers operate on `Security` only.
- Resolvers never modify `UniverseMember`.
- Resolvers are deterministic, local, stateless, and thread-safe.
- Canonical identity is `security_id`.
- If `security_id` is unavailable, fallback identity is `symbol`.
- Listed option identity uses `option_root`.
- Option-root rules live in package data and may be overridden by users.
- The resolver parses identity; configuration enriches semantics.
- Storage is abstracted behind `UniverseStore`.
- In-memory and SQLite stores must satisfy the same behavioral contract.

Open implementation details:

- exact exception hierarchy
- final SQLite DDL
- unresolved-security fallback key if symbol alone proves ambiguous
- final import/export schemas
