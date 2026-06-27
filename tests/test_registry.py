from datetime import datetime, timedelta, timezone

import pytest

from security_universe import (
    Security,
    SecurityType,
    UniverseNotFoundError,
    UniverseRegistry,
    UniverseType,
)
from security_universe.resolvers import OCCSecurityIdResolver


def test_registry_creates_and_lists_universes() -> None:
    registry = UniverseRegistry.memory()

    registry.create_universe("restricted", universe_type="restricted", tags={"risk"})

    universe = registry.get_universe("restricted")
    assert universe is not None
    assert universe.universe_type == UniverseType.RESTRICTED
    assert universe.tags == {"risk"}
    assert registry.list_universes() == [universe]


def test_registry_adds_member_from_symbol() -> None:
    registry = UniverseRegistry.memory()
    registry.create_universe("restricted", universe_type=UniverseType.RESTRICTED)

    member = registry.add_member(
        "restricted",
        "AAPL",
        security_type=SecurityType.STOCK,
        reason="manual restriction",
        source="manual",
    )

    assert member.security == Security(symbol="AAPL", security_type=SecurityType.STOCK)
    assert member.reason == "manual restriction"
    assert member.source == "manual"
    assert member.member_id == "restricted:AAPL"
    assert registry.contains("restricted", "AAPL")


def test_registry_invokes_resolver_before_persistence() -> None:
    registry = UniverseRegistry.memory(security_id_resolver=OCCSecurityIdResolver.default())
    registry.create_universe("spx-options")

    member = registry.add_member("spx-options", "SPXW260619C06100000")

    assert member.security.security_id == "option:SPXW:2026-06-19:call:6100"
    assert member.member_id == "spx-options:option:SPXW:2026-06-19:call:6100"
    assert registry.contains("spx-options", "SPXW260619C06100000")


def test_registry_resolve_include_exclude_sets() -> None:
    registry = UniverseRegistry.memory()
    registry.create_universe("sp500", universe_type=UniverseType.INDEX)
    registry.create_universe("restricted", universe_type=UniverseType.RESTRICTED)

    registry.add_member("sp500", "AAPL", security_type=SecurityType.STOCK)
    registry.add_member("sp500", "MSFT", security_type=SecurityType.STOCK)
    registry.add_member("restricted", "AAPL", security_type=SecurityType.STOCK)

    tradable = registry.resolve(include=["sp500"], exclude=["restricted"])

    assert [security.symbol for security in tradable] == ["MSFT"]


def test_registry_resolve_skips_disabled_and_expired_members() -> None:
    registry = UniverseRegistry.memory()
    registry.create_universe("enabled")
    registry.create_universe("disabled", enabled=False)

    registry.add_member("enabled", "AAPL")
    registry.add_member("enabled", "MSFT", expires_at=datetime.now(timezone.utc) - timedelta(days=1))
    registry.add_member("disabled", "TSLA")

    assert [security.symbol for security in registry.resolve(include=["enabled", "disabled"])] == [
        "AAPL"
    ]


def test_registry_unknown_universe_raises() -> None:
    registry = UniverseRegistry.memory()

    with pytest.raises(UniverseNotFoundError):
        registry.add_member("missing", "AAPL")
