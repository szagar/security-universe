from security_universe import Security, SecurityType
from security_universe.resolvers import EquitySecurityIdResolver, equity_security_id


def test_equity_security_id_helper_normalizes() -> None:
    assert equity_security_id(" aapl ") == "equity:AAPL"


def test_resolves_stock() -> None:
    out = EquitySecurityIdResolver().resolve(
        Security(symbol="AAPL", security_type=SecurityType.STOCK)
    )
    assert out.security_id == "equity:AAPL"
    assert out.root_symbol == "AAPL"
    assert out.underlying == "AAPL"
    assert out.short_name == "AAPL"


def test_resolves_etf() -> None:
    out = EquitySecurityIdResolver().resolve(
        Security(symbol="SPY", security_type=SecurityType.ETF)
    )
    assert out.security_id == "equity:SPY"


def test_ignores_non_equity_types() -> None:
    resolver = EquitySecurityIdResolver()
    for security_type in (SecurityType.OPTION, SecurityType.FUTURE, SecurityType.UNKNOWN):
        out = resolver.resolve(Security(symbol="AAPL", security_type=security_type))
        assert out.security_id is None


def test_preserves_existing_security_id() -> None:
    out = EquitySecurityIdResolver().resolve(
        Security(symbol="AAPL", security_type=SecurityType.STOCK, security_id="custom:1")
    )
    assert out.security_id == "custom:1"
