"""Futures universe example."""

from security_universes import SecurityType, UniverseRegistry


def main() -> None:
    registry = UniverseRegistry.memory()
    registry.create_universe("equity-index-futures", universe_type="watchlist")
    registry.add_member(
        "equity-index-futures",
        "/ESU6",
        security_type=SecurityType.FUTURE,
    )
    print([member.security.symbol for member in registry.list_members("equity-index-futures")])


if __name__ == "__main__":
    main()
