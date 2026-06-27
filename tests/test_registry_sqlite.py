from security_universe import SecurityType, UniverseRegistry
from security_universe.resolvers import OCCSecurityIdResolver


def test_registry_sqlite_persists_members(tmp_path) -> None:
    path = tmp_path / "universe.db"
    registry = UniverseRegistry.sqlite(path)
    registry.create_universe("sp500", universe_type="index")
    registry.add_member("sp500", "AAPL", security_type=SecurityType.STOCK)

    reopened = UniverseRegistry.sqlite(path)

    assert [member.security.symbol for member in reopened.list_members("sp500")] == [
        "AAPL"
    ]


def test_registry_sqlite_invokes_resolver_before_persistence(tmp_path) -> None:
    registry = UniverseRegistry.sqlite(
        tmp_path / "universe.db",
        security_id_resolver=OCCSecurityIdResolver.default(),
    )
    registry.create_universe("spx-options")

    member = registry.add_member("spx-options", "SPXW260619C06100000")

    assert member.security.security_id == "option:SPXW:2026-06-19:call:6100"
    assert registry.contains("spx-options", "SPXW260619C06100000")
