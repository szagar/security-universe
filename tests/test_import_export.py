import json
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from security_universes import Security, SecurityType, UniverseRegistry
from security_universes.resolvers import OCCSecurityIdResolver


def test_registry_json_export_import_round_trip(tmp_path) -> None:
    export_path = tmp_path / "members.json"
    source = UniverseRegistry.memory(security_id_resolver=OCCSecurityIdResolver.default())
    source.create_universe("options")
    source.add_member(
        "options",
        "SPXW260619C06100000",
        security_type=SecurityType.OPTION,
        weight=Decimal("0.5"),
        source="manual",
        reason="test option",
        tags={"index"},
        metadata={"ticket": "OPT-1"},
    )

    exported = source.export_members("options", export_path)

    target = UniverseRegistry.memory()
    target.create_universe("options")
    imported = target.import_members("options", export_path)

    assert len(exported) == 1
    assert imported == exported


def test_registry_csv_export_import_preserves_security_json(tmp_path) -> None:
    export_path = tmp_path / "members.csv"
    source = UniverseRegistry.memory(security_id_resolver=OCCSecurityIdResolver.default())
    source.create_universe("options")
    source.add_member("options", "AAPL1260918C00100000", security_type="option")

    source.export_members("options", export_path)

    target = UniverseRegistry.memory()
    target.create_universe("options")
    imported = target.import_members("options", export_path)

    assert imported[0].security.security_id == "option:AAPL1:2026-09-18:call:100"
    assert imported[0].security.deliverable == {"cash": 12.37, "shares": {"AAPL": 100}}


def test_registry_imports_simple_json_symbols_with_resolver(tmp_path) -> None:
    import_path = tmp_path / "members.json"
    import_path.write_text(
        json.dumps(
            [
                {
                    "security": {
                        "symbol": "SPXW260619C06100000",
                        "security_type": "option",
                    },
                    "reason": "seed",
                }
            ]
        ),
        encoding="utf-8",
    )
    registry = UniverseRegistry.memory(security_id_resolver=OCCSecurityIdResolver.default())
    registry.create_universe("options")

    imported = registry.import_members("options", import_path)

    assert imported[0].security.security_id == "option:SPXW:2026-06-19:call:6100"
    assert imported[0].reason == "seed"


def test_registry_export_active_only_by_default(tmp_path) -> None:
    export_path = tmp_path / "members.json"
    registry = UniverseRegistry.memory()
    registry.create_universe("restricted")
    registry.add_member("restricted", Security(symbol="AAPL"))
    registry.add_member(
        "restricted",
        Security(symbol="MSFT"),
        expires_at=datetime.now(timezone.utc) - timedelta(days=1),
    )

    exported = registry.export_members("restricted", export_path)

    assert [member.security.symbol for member in exported] == ["AAPL"]
