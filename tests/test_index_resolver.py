from security_universe import Security, SecurityType, to_tt
from security_universe.resolvers import IndexSecurityIdResolver, index_security_id
from security_universe.resolvers.chain import ResolverChain


def test_index_security_id_helper_normalizes() -> None:
    assert index_security_id(" spx ") == "index:SPX"


def test_resolves_index() -> None:
    out = IndexSecurityIdResolver().resolve(
        Security(symbol="SPX", security_type=SecurityType.INDEX)
    )
    assert out.security_id == "index:SPX"
    assert out.root_symbol == "SPX"
    assert out.underlying == "SPX"
    assert out.short_name == "SPX"


def test_ignores_non_index_types() -> None:
    resolver = IndexSecurityIdResolver()
    for security_type in (
        SecurityType.STOCK,
        SecurityType.ETF,
        SecurityType.OPTION,
        SecurityType.FUTURE,
        SecurityType.UNKNOWN,
    ):
        out = resolver.resolve(Security(symbol="SPX", security_type=security_type))
        assert out.security_id is None


def test_preserves_existing_security_id() -> None:
    out = IndexSecurityIdResolver().resolve(
        Security(symbol="SPX", security_type=SecurityType.INDEX, security_id="custom:1")
    )
    assert out.security_id == "custom:1"


def test_default_chain_resolves_index_and_round_trips() -> None:
    chain = ResolverChain.default()
    for ticker in ("SPX", "XSP", "VIX", "NDX", "RUT"):
        out = chain.resolve(Security(symbol=ticker, security_type=SecurityType.INDEX))
        assert out.security_id == f"index:{ticker}"
        # An index's native symbol is its order/quote symbol (to_tt default branch).
        assert to_tt(out) == ticker
