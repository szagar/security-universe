from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from security_universes import (
    DuplicateMemberError,
    DuplicateUniverseError,
    InMemoryUniverseStore,
    Security,
    SecurityType,
    Universe,
    UniverseMember,
    UniverseType,
)


def test_universe_crud() -> None:
    store = InMemoryUniverseStore()
    universe = store.create_universe(
        Universe(name="restricted", universe_type=UniverseType.RESTRICTED)
    )

    assert universe.name == "restricted"
    assert store.get_universe("restricted") == universe
    assert store.list_universes() == [universe]

    store.delete_universe("restricted")

    assert store.get_universe("restricted") is None
    assert store.list_universes() == []


def test_duplicate_universe_raises() -> None:
    store = InMemoryUniverseStore()
    store.create_universe(Universe(name="restricted"))

    with pytest.raises(DuplicateUniverseError):
        store.create_universe(Universe(name="restricted"))


def test_add_remove_contains_member() -> None:
    store = InMemoryUniverseStore()
    store.create_universe(Universe(name="restricted"))
    member = UniverseMember(
        universe_name="restricted",
        security=Security(symbol="AAPL", security_type=SecurityType.STOCK),
        reason="manual restriction",
    )

    stored = store.add_member(member)

    assert stored == member
    assert store.contains("restricted", "AAPL")
    assert store.list_members("restricted") == [member]

    store.remove_member("restricted", "AAPL")

    assert not store.contains("restricted", "AAPL")
    assert store.list_members("restricted") == []


def test_duplicate_member_uses_security_id_with_symbol_fallback() -> None:
    store = InMemoryUniverseStore()
    store.create_universe(Universe(name="options"))
    store.add_member(
        UniverseMember(
            universe_name="options",
            security=Security(
                symbol="SPXW260619C06100000",
                security_id="option:SPXW:2026-06-19:call:6100",
            ),
        )
    )

    with pytest.raises(DuplicateMemberError):
        store.add_member(
            UniverseMember(
                universe_name="options",
                security=Security(
                    symbol="OTHER",
                    security_id="option:SPXW:2026-06-19:call:6100",
                ),
            )
        )


def test_active_and_expired_member_filtering() -> None:
    store = InMemoryUniverseStore()
    store.create_universe(Universe(name="restricted"))
    now = datetime.now(timezone.utc)
    active = UniverseMember(
        universe_name="restricted",
        security=Security(symbol="AAPL"),
    )
    inactive = UniverseMember(
        universe_name="restricted",
        security=Security(symbol="MSFT"),
        active=False,
    )
    expired = UniverseMember(
        universe_name="restricted",
        security=Security(symbol="TSLA"),
        expires_at=now - timedelta(days=1),
    )

    store.add_member(active)
    store.add_member(inactive)
    store.add_member(expired)

    assert [member.security.symbol for member in store.list_members("restricted")] == [
        "AAPL"
    ]
    assert [member.security.symbol for member in store.list_members("restricted", active_only=False)] == [
        "AAPL",
        "MSFT",
        "TSLA",
    ]
    assert not store.contains("restricted", "MSFT")
    assert not store.contains("restricted", "TSLA")


def test_store_returns_copies() -> None:
    store = InMemoryUniverseStore()
    store.create_universe(Universe(name="restricted"))
    member = store.add_member(
        UniverseMember(
            universe_name="restricted",
            security=Security(symbol="AAPL"),
            metadata={"source": "test"},
        )
    )

    member.metadata["source"] = "mutated"
    member.security.symbol = "MSFT"

    stored = store.list_members("restricted")[0]
    assert stored.security.symbol == "AAPL"
    assert stored.metadata == {"source": "test"}


def test_nested_option_security_round_trip() -> None:
    store = InMemoryUniverseStore()
    store.create_universe(Universe(name="options"))
    member = UniverseMember(
        universe_name="options",
        security=Security(
            symbol="AAPL1260918C00100000",
            security_id="option:AAPL1:2026-09-18:call:100",
            security_type=SecurityType.OPTION,
            option_root="AAPL1",
            underlying="AAPL",
            strike=Decimal("100"),
            contract_multiplier=Decimal("100"),
            deliverable={"cash": 12.37, "shares": {"AAPL": 100}},
        ),
        tags={"adjusted"},
        metadata={"source_file": "manual.yaml"},
    )

    store.add_member(member)
    stored = store.list_members("options")[0]

    assert stored == member

