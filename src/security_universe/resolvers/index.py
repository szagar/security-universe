"""Index security-id resolver (e.g. SPX, XSP, VIX, NDX, RUT)."""

from __future__ import annotations

from security_universe.models import Security, SecurityType


def index_security_id(symbol: str) -> str:
    return f"index:{symbol.strip().upper()}"


class IndexSecurityIdResolver:
    """Assign a canonical ``index:{TICKER}`` id to cash-settled indices.

    Applies only when ``security_type`` is ``INDEX`` — like the equity resolver it
    does **not** guess from the symbol, because a bare ticker is ambiguous (SPX is an
    index, SPY an ETF, ES a future root). Securities of any other type are returned
    unchanged (``security_id`` left as-is, typically ``None``). The inverse
    (``symbology.to_tt``) returns the bare ticker via its default branch — an index's
    native symbol *is* its order/quote symbol.
    """

    def resolve(self, security: Security) -> Security:
        if security.security_type is not SecurityType.INDEX:
            return security

        ticker = security.symbol.strip().upper()
        return security.model_copy(
            update={
                "security_id": security.security_id or index_security_id(ticker),
                "short_name": security.short_name or ticker,
                "root_symbol": security.root_symbol or ticker,
                "underlying": security.underlying or ticker,
            }
        )
