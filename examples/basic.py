"""Basic in-memory usage example.

This file should become executable once the package implementation exists.
It demonstrates the smallest intended workflow:

1. create a registry
2. create universes
3. add members
4. resolve include/exclude universe sets
"""


def main() -> None:
    # from security_universes import Security, SecurityType, UniverseRegistry
    #
    # registry = UniverseRegistry.memory()
    # registry.create_universe("restricted", universe_type="restricted")
    # registry.create_universe("sp500", universe_type="index")
    # registry.add_member(
    #     "restricted",
    #     Security(symbol="AAPL", security_type=SecurityType.STOCK),
    #     reason="manual restriction",
    # )
    # tradable = registry.resolve(include=["sp500"], exclude=["restricted"])
    # print(tradable)
    raise NotImplementedError("Example becomes executable after implementation.")


if __name__ == "__main__":
    main()
