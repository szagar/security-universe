"""SQLite-backed registry example."""

from tempfile import TemporaryDirectory

from security_universes import SecurityType, UniverseRegistry


def main() -> None:
    with TemporaryDirectory() as tmpdir:
        registry = UniverseRegistry.sqlite(f"{tmpdir}/universes.db")
        registry.create_universe("restricted", universe_type="restricted")
        registry.add_member("restricted", "AAPL", security_type=SecurityType.STOCK)
        print([member.security.symbol for member in registry.list_members("restricted")])


if __name__ == "__main__":
    main()
