import sys
import types
from dataclasses import dataclass

import pytest

from security_universe.resolvers import (
    ResolverChain,
    TastytradeActiveContractLookup,
)


@dataclass
class _FakeFuture:
    symbol: str
    active_month: bool


def _install_fake_sdk(monkeypatch: pytest.MonkeyPatch, chain, calls: list[str]) -> None:
    """Install a fake ``tastytrade.instruments`` module exposing ``Future.get_future_chain``."""

    class Future:
        @staticmethod
        def get_future_chain(session: object, root: str):
            calls.append(root)
            return chain

    pkg = types.ModuleType("tastytrade")
    instruments = types.ModuleType("tastytrade.instruments")
    instruments.Future = Future  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "tastytrade", pkg)
    monkeypatch.setitem(sys.modules, "tastytrade.instruments", instruments)


def test_returns_active_month_symbol(monkeypatch: pytest.MonkeyPatch) -> None:
    chain = [
        _FakeFuture("/ESM6", active_month=False),
        _FakeFuture("/ESU6", active_month=True),
        _FakeFuture("/ESZ6", active_month=False),
    ]
    calls: list[str] = []
    _install_fake_sdk(monkeypatch, chain, calls)

    lookup = TastytradeActiveContractLookup(session=object())
    assert lookup.active_contract("/ES") == "/ESU6"
    assert calls == ["ES"]  # prefix stripped, upper-cased


def test_caches_per_root(monkeypatch: pytest.MonkeyPatch) -> None:
    chain = [_FakeFuture("/ESU6", active_month=True)]
    calls: list[str] = []
    _install_fake_sdk(monkeypatch, chain, calls)

    lookup = TastytradeActiveContractLookup(session=object())
    assert lookup.active_contract("ES") == "/ESU6"
    assert lookup.active_contract("/ES") == "/ESU6"  # served from cache
    assert calls == ["ES"]

    lookup.clear_cache()
    assert lookup.active_contract("ES") == "/ESU6"
    assert calls == ["ES", "ES"]


def test_no_active_month_returns_none(monkeypatch: pytest.MonkeyPatch) -> None:
    chain = [_FakeFuture("/ESM6", active_month=False)]
    _install_fake_sdk(monkeypatch, chain, [])

    lookup = TastytradeActiveContractLookup(session=object())
    assert lookup.active_contract("ES") is None


def test_sdk_failure_degrades_to_none(monkeypatch: pytest.MonkeyPatch) -> None:
    class Future:
        @staticmethod
        def get_future_chain(session: object, root: str):
            raise RuntimeError("network down")

    pkg = types.ModuleType("tastytrade")
    instruments = types.ModuleType("tastytrade.instruments")
    instruments.Future = Future  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "tastytrade", pkg)
    monkeypatch.setitem(sys.modules, "tastytrade.instruments", instruments)

    lookup = TastytradeActiveContractLookup(session=object())
    assert lookup.active_contract("ES") is None


def test_missing_extra_raises_importerror(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(sys.modules, "tastytrade", None)
    monkeypatch.setitem(sys.modules, "tastytrade.instruments", None)

    lookup = TastytradeActiveContractLookup(session=object())
    with pytest.raises(ImportError, match="security-universe\\[tastytrade\\]"):
        lookup.active_contract("ES")


def test_chain_with_tastytrade_resolves_active_contract(monkeypatch: pytest.MonkeyPatch) -> None:
    from security_universe import Security, SecurityType

    chain = [_FakeFuture("/ESU6", active_month=True)]
    _install_fake_sdk(monkeypatch, chain, [])

    resolver = ResolverChain.with_tastytrade(session=object())
    out = resolver.resolve(Security(symbol="/ES", security_type=SecurityType.FUTURE))
    assert out.security_id == "future:ES:U6"
