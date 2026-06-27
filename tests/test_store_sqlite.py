from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from security_universes import (
    DuplicateMemberError,
    DuplicateUniverseError,
    SQLiteUniverseStore,
    Security,
    SecurityType,
    Universe,
    UniverseMember,
    UniverseType,
)


def test_sqlite_universe_crud(tmp_path) -> None:
    store = SQLiteUniverseStore(tmp_path / "universes.db")
    universe = store.create_universe(
        Universe(name="restricted", universe_type=UniverseType.RESTRICTED)
    )

    assert store.get_universe("restricted") == universe
    assert store.list_universes() == [universe]

    store.delete_universe("restricted")

    assert store.get_universe("restricted") is None
    assert store.list_universes() == []


def test_sqlite_duplicate_universe_raises(tmp_path) -> None:
    store = SQLiteUniverseStore(tmp_path / "universes.db")
    store.create_universe(Universe(name="restricted"))

    with pytest.raises(DuplicateUniverseError):
        store.create_universe(Universe(name="restricted"))


def test_sqlite_add_remove_contains_member(tmp_path) -> None:
    store = SQLiteUniverseStore(tmp_path / "universes.db")
    store.create_universe(Universe(name="restricted"))
    member = UniverseMember(
        universe_name="restricted",
        security=Security(symbol="AAPL", security_type=SecurityType.STOCK),
        reason="manual restriction",
    )

    store.add_member(member)

    assert store.contains("restricted", "AAPL")
    assert store.list_members("restricted") == [member]

    store.remove_member("restricted", "AAPL")

    assert not store.contains("restricted", "AAPL")
    assert store.list_members("restricted") == []


def test_sqlite_duplicate_member_uses_security_id(tmp_path) -> None:
    store = SQLiteUniverseStore(tmp_path / "universes.db")
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


def test_sqlite_active_and_expired_member_filtering(tmp_path) -> None:
    store = SQLiteUniverseStore(tmp_path / "universes.db")
    store.create_universe(Universe(name="restricted"))
    now = datetime.now(timezone.utc)

    store.add_member(
        UniverseMember(universe_name="restricted", security=Security(symbol="AAPL"))
    )
    store.add_member(
        UniverseMember(
            universe_name="restricted",
            security=Security(symbol="MSFT"),
            active=False,
        )
    )
    store.add_member(
        UniverseMember(
            universe_name="restricted",
            security=Security(symbol="TSLA"),
            expires_at=now - timedelta(days=1),
        )
    )

    assert [member.security.symbol for member in store.list_members("restricted")] == [
        "AAPL"
    ]
    assert [
        member.security.symbol
        for member in store.list_members("restricted", active_only=False)
    ] == ["AAPL", "MSFT", "TSLA"]


def test_sqlite_nested_option_security_round_trip(tmp_path) -> None:
    store = SQLiteUniverseStore(tmp_path / "universes.db")
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

    assert store.list_members("options")[0] == member


def test_sqlite_persists_across_store_instances(tmp_path) -> None:
    path = tmp_path / "universes.db"
    first = SQLiteUniverseStore(path)
    first.create_universe(Universe(name="restricted"))
    first.add_member(
        UniverseMember(
            universe_name="restricted",
            security=Security(symbol="AAPL", security_type=SecurityType.STOCK),
            reason="manual restriction",
        )
    )
    first.close()

    second = SQLiteUniverseStore(path)

    assert second.get_universe("restricted") == Universe(name="restricted")
    assert second.list_members("restricted")[0].reason == "manual restriction"
