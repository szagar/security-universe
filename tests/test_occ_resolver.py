from datetime import date
from decimal import Decimal

import pytest

from security_universes import (
    ExpirationSession,
    OptionType,
    Security,
    SecurityType,
    SettlementType,
)
from security_universes.resolvers import (
    OCCSecurityIdResolver,
    format_strike,
    load_default_option_rules,
    option_security_id,
    option_short_name,
    parse_occ_symbol,
)


def test_parse_occ_symbol_normalizes_spaces_and_case() -> None:
    parsed = parse_occ_symbol(" spxw 260619 c06100000 ")

    assert parsed.option_root == "SPXW"
    assert parsed.expiry == date(2026, 6, 19)
    assert parsed.option_type == OptionType.CALL
    assert parsed.strike == Decimal("6100")


def test_parse_occ_symbol_rejects_invalid_symbol() -> None:
    with pytest.raises(ValueError, match="Invalid OCC option symbol"):
        parse_occ_symbol("SPX-2026-06-19-C-6100")


@pytest.mark.parametrize(
    ("strike", "expected"),
    [
        (Decimal("6100.000"), "6100"),
        (Decimal("12.340"), "12.34"),
        (Decimal("0.125"), "0.125"),
        (Decimal("0"), "0"),
    ],
)
def test_format_strike(strike: Decimal, expected: str) -> None:
    assert format_strike(strike) == expected


def test_option_identity_and_short_name_helpers() -> None:
    assert (
        option_security_id("SPXW", date(2026, 6, 19), OptionType.CALL, Decimal("6100"))
        == "option:SPXW:2026-06-19:call:6100"
    )
    assert (
        option_short_name("SPXW", Decimal("6100"), OptionType.CALL, date(2026, 6, 19))
        == "SPXW 6100C 2026-06-19"
    )


@pytest.mark.parametrize(
    ("symbol", "underlying", "session"),
    [
        ("SPX260619C06100000", "SPX", ExpirationSession.AM),
        ("SPXW260619C06100000", "SPX", ExpirationSession.PM),
        ("NDX260619P21000000", "NDX", ExpirationSession.AM),
        ("NDXP260619P21000000", "NDX", ExpirationSession.PM),
    ],
)
def test_default_index_option_rules(symbol: str, underlying: str, session: ExpirationSession) -> None:
    resolved = OCCSecurityIdResolver.default().resolve(Security(symbol=symbol))

    assert resolved.security_type == SecurityType.OPTION
    assert resolved.underlying == underlying
    assert resolved.expiration_session == session
    assert resolved.settlement_type == SettlementType.CASH


def test_resolve_spxw_option_security() -> None:
    resolved = OCCSecurityIdResolver.default().resolve(
        Security(symbol="SPXW260619C06100000")
    )

    assert resolved.security_id == "option:SPXW:2026-06-19:call:6100"
    assert resolved.short_name == "SPXW 6100C 2026-06-19"
    assert resolved.option_root == "SPXW"
    assert resolved.underlying == "SPX"
    assert resolved.expiry == date(2026, 6, 19)
    assert resolved.strike == Decimal("6100")
    assert resolved.option_type == OptionType.CALL
    assert resolved.expiration_session == ExpirationSession.PM
    assert resolved.settlement_type == SettlementType.CASH


def test_resolver_preserves_explicit_caller_fields() -> None:
    security = Security(
        symbol="SPXW260619C06100000",
        security_id="custom-id",
        short_name="Custom Name",
        underlying="CUSTOM",
        expiry=date(2026, 1, 1),
        strike=Decimal("1"),
        option_type=OptionType.PUT,
        expiration_session=ExpirationSession.AM,
        settlement_type=SettlementType.PHYSICAL,
        contract_multiplier=Decimal("10"),
        deliverable_type="custom",
        deliverable_description="custom deliverable",
        deliverable={"custom": True},
    )

    resolved = OCCSecurityIdResolver.default().resolve(security)

    assert resolved.security_id == "custom-id"
    assert resolved.short_name == "Custom Name"
    assert resolved.underlying == "CUSTOM"
    assert resolved.expiry == date(2026, 1, 1)
    assert resolved.strike == Decimal("1")
    assert resolved.option_type == OptionType.PUT
    assert resolved.expiration_session == ExpirationSession.AM
    assert resolved.settlement_type == SettlementType.PHYSICAL
    assert resolved.contract_multiplier == Decimal("10")
    assert resolved.deliverable_type == "custom"
    assert resolved.deliverable_description == "custom deliverable"
    assert resolved.deliverable == {"custom": True}


def test_unknown_option_root_falls_back_to_root_and_unknown_metadata() -> None:
    resolved = OCCSecurityIdResolver.default().resolve(
        Security(symbol="ABC260619C00012500")
    )

    assert resolved.security_id == "option:ABC:2026-06-19:call:12.5"
    assert resolved.underlying == "ABC"
    assert resolved.expiration_session == ExpirationSession.UNKNOWN
    assert resolved.settlement_type == SettlementType.UNKNOWN


def test_user_yaml_overrides_defaults(tmp_path) -> None:
    rule_file = tmp_path / "rules.yaml"
    rule_file.write_text(
        "\n".join(
            [
                "SPXW:",
                "  underlying: CUSTOM_SPX",
                "  expiration_session: am",
                "  settlement_type: physical",
                "  contract_multiplier: 50",
            ]
        ),
        encoding="utf-8",
    )

    resolved = OCCSecurityIdResolver.from_yaml(rule_file).resolve(
        Security(symbol="SPXW260619C06100000")
    )

    assert resolved.underlying == "CUSTOM_SPX"
    assert resolved.expiration_session == ExpirationSession.AM
    assert resolved.settlement_type == SettlementType.PHYSICAL
    assert resolved.contract_multiplier == Decimal("50")


def test_adjusted_deliverable_enrichment() -> None:
    resolved = OCCSecurityIdResolver.default().resolve(
        Security(symbol="AAPL1260918C00100000")
    )

    assert resolved.option_root == "AAPL1"
    assert resolved.underlying == "AAPL"
    assert resolved.settlement_type == SettlementType.PHYSICAL
    assert resolved.contract_multiplier == Decimal("100")
    assert resolved.deliverable_type == "adjusted"
    assert resolved.deliverable_description == "Adjusted option contract from corporate action"
    assert resolved.deliverable == {"cash": 12.37, "shares": {"AAPL": 100}}


def test_resolver_does_not_mutate_input_security() -> None:
    original = Security(symbol="SPXW260619C06100000")

    resolved = OCCSecurityIdResolver.default().resolve(original)

    assert resolved is not original
    assert original.security_id is None
    assert original.option_root is None
    assert resolved.security_id == "option:SPXW:2026-06-19:call:6100"


def test_default_rules_load_from_package_data() -> None:
    rules = load_default_option_rules()

    assert rules["SPX"]["expiration_session"] == "am"
    assert rules["SPXW"]["expiration_session"] == "pm"
    assert rules["AAPL1"]["deliverable_type"] == "adjusted"
