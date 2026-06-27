# Examples Guide

The `examples/` directory should contain executable examples once the package
implementation exists.

Planned examples:

- `basic.py` - in-memory registry, create universes, add members, resolve
- `sqlite.py` - SQLite-backed registry
- `options.py` - OCC option resolution and option-root rules
- `futures.py` - futures securities in universes
- `custom_resolver.py` - custom `SecurityIdResolver`

All examples should be included in documentation tests before release.
