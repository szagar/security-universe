import pytest

from security_universe import Security, SecurityType
from security_universe.resolvers import (
    FutureSecurityIdResolver,
    future_active_security_id,
    future_security_id,
    future_short_name,
    parse_future_symbol,
)


@pytest.mark.parametrize(
    ("symbol", "root", "month", "year_token"),
    [
        ("/ESM6", "ES", 6, "6"),
        ("ESM6", "ES", 6, "6"),
        ("/CLZ26", "CL", 12, "26"),
        (" /6EH6 ", "6E", 3, "6"),
        ("ZBH5", "ZB", 3, "5"),
    ],
)
def test_parse_future_symbol(symbol: str, root: str, month: int, year_token: str) -> None:
    parsed = parse_future_symbol(symbol)
    assert parsed is not None
    assert (parsed.root, parsed.month, parsed.year_token) == (root, month, year_token)


def test_parse_future_symbol_rejects_non_future() -> None:
    assert parse_future_symbol("AAPL") is None
    assert parse_future_symbol("/ES") is None  # continuous (no month/year)


def test_future_security_id_helper() -> None:
    assert future_security_id("ES", "M", "6") == "future:ES:M6"


def test_future_short_name_helper() -> None:
    assert future_short_name("ES", "M", "6") == "/ESM6"
    assert future_short_name("CL", "Z", "26") == "/CLZ6"  # last year digit only


def test_resolves_dated_future() -> None:
    out = FutureSecurityIdResolver().resolve(
        Security(symbol="/ESM6", security_type=SecurityType.FUTURE)
    )
    assert out.security_id == "future:ES:M6"
    assert out.root_symbol == "ES"
    assert out.underlying == "ES"
    assert out.short_name == "/ESM6"


def test_short_name_uses_last_year_digit_for_two_digit_year() -> None:
    out = FutureSecurityIdResolver().resolve(
        Security(symbol="/CLZ26", security_type=SecurityType.FUTURE)
    )
    assert out.short_name == "/CLZ6"


def test_active_future_without_lookup_falls_back_to_sentinel() -> None:
    out = FutureSecurityIdResolver().resolve(
        Security(symbol="/ES", security_type=SecurityType.FUTURE)
    )
    assert out.security_id == future_active_security_id("ES") == "future:ES:active"
    assert out.root_symbol == "ES"
    assert out.short_name == "/ES"


def test_resolves_continuous_future_with_at_prefix() -> None:
    out = FutureSecurityIdResolver().resolve(
        Security(symbol="@ES", security_type=SecurityType.FUTURE)
    )
    assert out.security_id == "future:ES"
    assert out.short_name == "@ES"  # continuous contracts are prefixed with "@"


def test_bare_root_treated_as_continuous() -> None:
    out = FutureSecurityIdResolver().resolve(
        Security(symbol="ES", security_type=SecurityType.FUTURE)
    )
    assert out.security_id == "future:ES"
    assert out.short_name == "@ES"


def test_active_future_with_lookup_resolves_to_dated_contract() -> None:
    class FakeLookup:
        def __init__(self) -> None:
            self.calls: list[str] = []

        def active_contract(self, root: str) -> str | None:
            self.calls.append(root)
            return "/ESU6"

    lookup = FakeLookup()
    out = FutureSecurityIdResolver(active_lookup=lookup).resolve(
        Security(symbol="/ES", security_type=SecurityType.FUTURE)
    )
    assert lookup.calls == ["ES"]
    assert out.security_id == "future:ES:U6"
    assert out.root_symbol == "ES"
    assert out.short_name == "/ESU6"


def test_active_future_with_lookup_miss_falls_back_to_sentinel() -> None:
    class NullLookup:
        def active_contract(self, root: str) -> str | None:
            return None

    out = FutureSecurityIdResolver(active_lookup=NullLookup()).resolve(
        Security(symbol="/ES", security_type=SecurityType.FUTURE)
    )
    assert out.security_id == "future:ES:active"
    assert out.short_name == "/ES"


def test_continuous_future_ignores_lookup() -> None:
    class BoomLookup:
        def active_contract(self, root: str) -> str | None:
            raise AssertionError("continuous (@) symbols must not consult the lookup")

    out = FutureSecurityIdResolver(active_lookup=BoomLookup()).resolve(
        Security(symbol="@ES", security_type=SecurityType.FUTURE)
    )
    assert out.security_id == "future:ES"
    assert out.short_name == "@ES"


def test_dated_future_ignores_lookup() -> None:
    class BoomLookup:
        def active_contract(self, root: str) -> str | None:
            raise AssertionError("dated symbols must not consult the lookup")

    out = FutureSecurityIdResolver(active_lookup=BoomLookup()).resolve(
        Security(symbol="/ESM6", security_type=SecurityType.FUTURE)
    )
    assert out.security_id == "future:ES:M6"


def test_ignores_non_future_types() -> None:
    out = FutureSecurityIdResolver().resolve(
        Security(symbol="/ESM6", security_type=SecurityType.STOCK)
    )
    assert out.security_id is None
