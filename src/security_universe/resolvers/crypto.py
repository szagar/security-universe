"""Crypto security-id resolver."""

from __future__ import annotations

import re
from dataclasses import dataclass

from security_universe.models import Security, SecurityType

# Common quote currencies, longest-first so e.g. "USDT" is peeled before "USD".
QUOTE_CURRENCIES: tuple[str, ...] = (
    "USDT", "USDC", "BUSD", "TUSD", "USD", "EUR", "GBP", "JPY", "BTC", "ETH", "DAI",
)

# A base and quote separated by "-", "/", or "_".
CRYPTO_RE = re.compile(r"^(?P<base>[A-Z0-9]{2,10})[-/_](?P<quote>[A-Z0-9]{2,10})$")


@dataclass(frozen=True)
class ParsedCryptoSymbol:
    base: str
    quote: str


def parse_crypto_symbol(symbol: str) -> ParsedCryptoSymbol | None:
    """Parse a crypto pair (e.g. ``BTC-USD``, ``ETH/USDT``, ``BTCUSD``).

    Returns ``None`` if no quote currency can be identified (e.g. a bare ``BTC``).
    """
    normalized = symbol.replace(" ", "").upper()
    match = CRYPTO_RE.match(normalized)
    if match:
        parts = match.groupdict()
        return ParsedCryptoSymbol(base=parts["base"], quote=parts["quote"])
    # No separator — try to peel a known quote currency off the end.
    for quote in QUOTE_CURRENCIES:
        if normalized.endswith(quote) and len(normalized) > len(quote):
            return ParsedCryptoSymbol(base=normalized[: -len(quote)], quote=quote)
    return None


def crypto_security_id(base: str, quote: str) -> str:
    return f"crypto:{base}-{quote}"


class CryptoSecurityIdResolver:
    """Assign a canonical ``crypto:{BASE}-{QUOTE}`` id to crypto pairs.

    Applies only when ``security_type`` is ``CRYPTO``. A pair like ``BTC-USD``, ``ETH/USDT`` or
    ``BTCUSD`` becomes ``crypto:BTC-USD`` / ``crypto:ETH-USDT`` (base + quote), and the quote
    populates ``currency`` when unset. A symbol with no recognizable quote currency (e.g. a bare
    ``BTC``) falls back to ``crypto:{NORMALIZED}`` →  ``crypto:BTC``.
    """

    def resolve(self, security: Security) -> Security:
        if security.security_type != SecurityType.CRYPTO:
            return security

        parsed = parse_crypto_symbol(security.symbol)
        if parsed is not None:
            security_id = crypto_security_id(parsed.base, parsed.quote)
            base = parsed.base
            quote: str | None = parsed.quote
        else:
            base = security.symbol.replace(" ", "").upper()
            security_id = f"crypto:{base}"
            quote = None

        return security.model_copy(
            update={
                "security_id": security.security_id or security_id,
                "short_name": security.short_name or base,
                "root_symbol": security.root_symbol or base,
                "underlying": security.underlying or base,
                "currency": security.currency or quote,
            }
        )
