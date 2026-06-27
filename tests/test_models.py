from datetime import date, datetime, timezone
from decimal import Decimal

import pytest
from pydantic import ValidationError as PydanticValidationError

from security_universes import (
    ExpirationSession,
    OptionType,
    Security,
    SecurityType,
    SettlementType,
    SourceType,
    Universe,
    UniverseMember,
    UniverseType,
)


def test_security_defaults_and_identity_fallback() -> None:
    security = Security(symbol="AAPL")

    assert security.security_type == SecurityType.UNKNOWN
    assert security.security_id is None
    assert security.identity == "AAPL"
    assert security.display_name == "AAPL"
    assert security.deliverable == {}
    assert security.metadata == {}


def test_security_accepts_option_fields_with_precise_types() -> None:
    security = Security(
        symbol="SPXW260619C06100000",
        security_type="option",
        security_id="option:SPXW:2026-06-19:call:6100",
        short_name="SPXW 6100C 2026-06-19",
        option_root="SPXW",
        underlying="SPX",
        expiry=date(2026, 6, 19),
        strike="6100",
        option_type="call",
        expiration_session="pm",
        settlement_type="cash",
        contract_multiplier="100",
    )

    assert security.security_type == SecurityType.OPTION
    assert security.option_type == OptionType.CALL
    assert security.expiration_session == ExpirationSession.PM
    assert security.settlement_type == SettlementType.CASH
    assert security.strike == Decimal("6100")
    assert security.contract_multiplier == Decimal("100")
    assert security.identity == "option:SPXW:2026-06-19:call:6100"
    assert security.display_name == "SPXW 6100C 2026-06-19"


def test_security_keeps_adjusted_deliverable_data_on_security() -> None:
    security = Security(
        symbol="AAPL1260918C00100000",
        security_type=SecurityType.OPTION,
        option_root="AAPL1",
        underlying="AAPL",
        deliverable_type="adjusted",
        deliverable_description="Adjusted option contract from corporate action",
        deliverable={
            "cash": Decimal("12.37"),
            "shares": {"AAPL": 100},
        },
    )

    assert security.deliverable_type == "adjusted"
    assert security.deliverable["cash"] == Decimal("12.37")
    assert security.deliverable["shares"] == {"AAPL": 100}


def test_universe_defaults_and_coercion() -> None:
    universe = Universe(name="restricted", universe_type="restricted", tags=["risk"])

    assert universe.universe_type == UniverseType.RESTRICTED
    assert universe.enabled is True
    assert universe.source_type == SourceType.MANUAL
    assert universe.definition == {}
    assert universe.tags == {"risk"}
    assert universe.metadata == {}


def test_universe_member_owns_membership_metadata() -> None:
    added_at = datetime(2026, 1, 1, tzinfo=timezone.utc)
    expires_at = datetime(2026, 12, 31, tzinfo=timezone.utc)
    member = UniverseMember(
        universe_name="restricted",
        security=Security(symbol="AAPL", security_type=SecurityType.STOCK),
        weight="0.25",
        added_at=added_at,
        added_by="szagar",
        expires_at=expires_at,
        source="manual",
        reason="manual restriction",
        tags={"review"},
        metadata={"ticket": "RISK-1"},
    )

    assert member.security.symbol == "AAPL"
    assert member.weight == Decimal("0.25")
    assert member.active is True
    assert member.added_at == added_at
    assert member.expires_at == expires_at
    assert member.added_by == "szagar"
    assert member.source == "manual"
    assert member.reason == "manual restriction"
    assert member.tags == {"review"}
    assert member.metadata == {"ticket": "RISK-1"}


@pytest.mark.parametrize(
    ("model", "kwargs"),
    [
        (Security, {"symbol": ""}),
        (Universe, {"name": ""}),
        (
            UniverseMember,
            {"universe_name": "", "security": Security(symbol="AAPL")},
        ),
    ],
)
def test_names_must_not_be_empty(model, kwargs) -> None:
    with pytest.raises(PydanticValidationError):
        model(**kwargs)


def test_models_reject_unknown_fields() -> None:
    with pytest.raises(PydanticValidationError):
        Security(symbol="AAPL", reason="not allowed")
