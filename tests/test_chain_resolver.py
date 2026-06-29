from security_universe import Security, SecurityType
from security_universe.resolvers import ChainResolver


def test_default_chain_resolves_each_family() -> None:
    chain = ChainResolver.default()

    opt = chain.resolve(
        Security(symbol="AAPL  250117C00150000", security_type=SecurityType.OPTION)
    )
    assert opt.security_id == "option:AAPL:2025-01-17:call:150"

    eq = chain.resolve(Security(symbol="AAPL", security_type=SecurityType.STOCK))
    assert eq.security_id == "equity:AAPL"

    fut = chain.resolve(Security(symbol="/ESM6", security_type=SecurityType.FUTURE))
    assert fut.security_id == "future:ES:M6"

    crypto = chain.resolve(Security(symbol="BTC-USD", security_type=SecurityType.CRYPTO))
    assert crypto.security_id == "crypto:BTC-USD"


def test_chain_returns_unresolved_when_no_member_applies() -> None:
    out = ChainResolver.default().resolve(
        Security(symbol="WEIRD", security_type=SecurityType.UNKNOWN)
    )
    assert out.security_id is None


def test_chain_uses_occ_self_detection_without_a_type() -> None:
    out = ChainResolver.default().resolve(Security(symbol="SPXW  260619P06100000"))
    assert out.security_id == "option:SPXW:2026-06-19:put:6100"
    assert out.underlying == "SPX"


def test_resolvers_property_exposes_members() -> None:
    assert len(ChainResolver.default().resolvers) == 4
