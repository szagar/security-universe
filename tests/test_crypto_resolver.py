import pytest

from security_universe import Security, SecurityType
from security_universe.resolvers import (
    CryptoSecurityIdResolver,
    crypto_security_id,
    parse_crypto_symbol,
)


@pytest.mark.parametrize(
    ("symbol", "base", "quote"),
    [
        ("BTC-USD", "BTC", "USD"),
        ("ETH/USDT", "ETH", "USDT"),
        ("sol_usdc", "SOL", "USDC"),
        ("BTCUSD", "BTC", "USD"),
        ("ETHUSDT", "ETH", "USDT"),
        (" doge-usd ", "DOGE", "USD"),
        ("ETHBTC", "ETH", "BTC"),
    ],
)
def test_parse_crypto_symbol(symbol: str, base: str, quote: str) -> None:
    parsed = parse_crypto_symbol(symbol)
    assert parsed is not None
    assert (parsed.base, parsed.quote) == (base, quote)


def test_parse_crypto_symbol_rejects_unrecognized() -> None:
    assert parse_crypto_symbol("BTC") is None  # bare base, no quote currency


def test_crypto_security_id_helper() -> None:
    assert crypto_security_id("BTC", "USD") == "crypto:BTC-USD"


def test_resolves_pair() -> None:
    out = CryptoSecurityIdResolver().resolve(
        Security(symbol="BTC-USD", security_type=SecurityType.CRYPTO)
    )
    assert out.security_id == "crypto:BTC-USD"
    assert out.root_symbol == "BTC"
    assert out.underlying == "BTC"
    assert out.currency == "USD"


def test_resolves_concatenated_pair() -> None:
    out = CryptoSecurityIdResolver().resolve(
        Security(symbol="ETHUSDT", security_type=SecurityType.CRYPTO)
    )
    assert out.security_id == "crypto:ETH-USDT"
    assert out.currency == "USDT"


def test_resolves_bare_base_as_fallback() -> None:
    out = CryptoSecurityIdResolver().resolve(
        Security(symbol="btc", security_type=SecurityType.CRYPTO)
    )
    assert out.security_id == "crypto:BTC"
    assert out.root_symbol == "BTC"
    assert out.currency is None


def test_ignores_non_crypto_types() -> None:
    out = CryptoSecurityIdResolver().resolve(
        Security(symbol="BTC-USD", security_type=SecurityType.STOCK)
    )
    assert out.security_id is None


def test_preserves_existing_security_id() -> None:
    out = CryptoSecurityIdResolver().resolve(
        Security(symbol="BTC-USD", security_type=SecurityType.CRYPTO, security_id="custom:1")
    )
    assert out.security_id == "custom:1"
