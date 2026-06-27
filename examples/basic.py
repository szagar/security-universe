"""Basic in-memory usage example."""

from security_universes import Security, SecurityType, UniverseRegistry


def main() -> None:
    registry = UniverseRegistry.memory()
    registry.create_universe("restricted", universe_type="restricted")
    registry.create_universe("sp500", universe_type="index")
    registry.add_member("sp500", "AAPL", security_type=SecurityType.STOCK)
    registry.add_member("sp500", "MSFT", security_type=SecurityType.STOCK)
    registry.add_member(
        "restricted",
        Security(symbol="AAPL", security_type=SecurityType.STOCK),
        reason="manual restriction",
    )

    tradable = registry.resolve(include=["sp500"], exclude=["restricted"])
    print([security.symbol for security in tradable])


if __name__ == "__main__":
    main()
