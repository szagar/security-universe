"""to_tt — the symbology inverse, round-tripping against ResolverChain."""

from __future__ import annotations

from decimal import Decimal

import pytest

from security_universe import OptionType, Security, SecurityType, to_tt
from security_universe.resolvers import ResolverChain

chain = ResolverChain.default()


@pytest.mark.parametrize(
    "symbol",
    [
        "SPY   260117C00505000",  # equity option
        "SPXW  260117P05000000",  # index option
        "SPY   260117C00072500",  # fractional strike (72.5)
        "./ESU6 E1CN6 260701C6325",  # future option (opaque order symbol)
    ],
)
def test_to_tt_round_trips_resolved_symbol(symbol):
    sec = chain.resolve(Security(symbol=symbol))
    assert to_tt(sec) == symbol


def test_to_tt_future_option_requires_order_symbol():
    sec = Security(
        symbol="x",
        security_type=SecurityType.FUTURE_OPTION,
        expiry=None,
        strike=Decimal("6325"),
        option_type=OptionType.CALL,
    )
    with pytest.raises(ValueError, match="order_symbol"):
        to_tt(sec)


def test_to_tt_stock_returns_native_symbol():
    sec = chain.resolve(Security(symbol="AAPL", security_type=SecurityType.STOCK))
    assert to_tt(sec) == "AAPL"


def test_to_tt_prefers_explicit_order_symbol_for_non_options():
    sec = Security(symbol="native", security_type=SecurityType.FUTURE, order_symbol="/ESU6")
    assert to_tt(sec) == "/ESU6"
