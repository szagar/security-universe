"""Symbology inverse — ``Security`` -> broker (TastyTrade) order symbol.

The inverse of the identity resolvers (which parse a native symbol into a
``Security`` + ``security_id``). Algorithmic for equity/index options (OCC),
stock/ETF/index/future/crypto; options-on-futures are opaque (the order symbol
carries a CME series code that isn't recoverable from the parsed fields) so
``to_tt`` reads the carried ``order_symbol`` for those.

This is the round-trip partner of ``ResolverChain`` (resolve <-> name): a
``Security`` resolved from a symbol round-trips back to that symbol. It's the
registry-free naming path that lets a consumer reconstruct an order symbol from
stored identity without a symbol-registry lookup.
"""

from __future__ import annotations

from security_universe.models import OptionType, Security, SecurityType


def occ_symbol(security: Security) -> str:
    """Build the spaced OCC option symbol (e.g. ``SPY   260117C00505000``) from a
    resolved option ``Security``. Root left-justified to 6, ``YYMMDD``, ``C``/``P``,
    8-digit strike (strike*1000)."""
    root = security.option_root or security.root_symbol or security.underlying
    if not (root and security.expiry and security.strike is not None and security.option_type):
        raise ValueError(
            f"option to_tt requires option_root/expiry/strike/option_type: {security!r}"
        )
    cp = "C" if security.option_type == OptionType.CALL else "P"
    strike8 = f"{int((security.strike * 1000).to_integral_value()):08d}"
    return f"{root:<6}{security.expiry:%y%m%d}{cp}{strike8}"


def to_tt(security: Security) -> str:
    """Return the broker order symbol for a ``Security``.

    * ``FUTURE_OPTION`` — the opaque ``order_symbol`` (raises if absent).
    * ``OPTION`` — the algorithmic OCC symbol.
    * everything else (stock/ETF/index/future/crypto/…) — the native symbol is
      already the order symbol; prefer ``order_symbol`` if explicitly carried.
    """
    st = security.security_type
    if st == SecurityType.FUTURE_OPTION:
        if not security.order_symbol:
            raise ValueError(
                "future-option to_tt requires order_symbol (opaque CME series code); "
                f"it is not algorithmic from identity: {security!r}"
            )
        return security.order_symbol
    if st == SecurityType.OPTION:
        return occ_symbol(security)
    return security.order_symbol or security.symbol
