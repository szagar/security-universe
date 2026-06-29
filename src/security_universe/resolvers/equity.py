"""Equity / ETF security-id resolver."""

from __future__ import annotations

from security_universe.models import Security, SecurityType

_EQUITY_TYPES = (SecurityType.STOCK, SecurityType.ETF)


def equity_security_id(symbol: str) -> str:
    return f"equity:{symbol.strip().upper()}"


class EquitySecurityIdResolver:
    """Assign a canonical ``equity:{TICKER}`` id to stocks and ETFs.

    Applies only when ``security_type`` is ``STOCK`` or ``ETF`` — it does **not** guess from the
    symbol, because a bare ticker is ambiguous (it could be a future root, etc.). Securities of any
    other type are returned unchanged (``security_id`` left as-is, typically ``None``).
    """

    def resolve(self, security: Security) -> Security:
        if security.security_type not in _EQUITY_TYPES:
            return security

        ticker = security.symbol.strip().upper()
        return security.model_copy(
            update={
                "security_id": security.security_id or equity_security_id(ticker),
                "short_name": security.short_name or ticker,
                "root_symbol": security.root_symbol or ticker,
                "underlying": security.underlying or ticker,
            }
        )
