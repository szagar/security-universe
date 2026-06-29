"""Tastytrade-backed active-contract lookup (optional, impure).

This is the *only* part of the resolver layer that performs network I/O and depends on
credentials. It is deliberately isolated behind the :class:`ActiveContractLookup` protocol and an
optional extra (``pip install security-universe[tastytrade]``) so the base package stays pure and
depends only on ``pydantic`` + ``pyyaml``.
"""

from __future__ import annotations


class TastytradeActiveContractLookup:
    """Resolve a futures root to its live front-month symbol via the tastytrade SDK.

    Implements :class:`security_universe.protocols.ActiveContractLookup`. Results are cached per
    instance — the active contract rolls only quarterly, so one lookup per root per session is
    plenty. Any failure (network, auth, unknown product) degrades to ``None`` so the resolver falls
    back to the deterministic ``future:{root}:active`` id rather than raising.
    """

    def __init__(self, session: object) -> None:
        # ``session`` is a ``tastytrade.Session``; typed as ``object`` so importing this module
        # never requires the optional dependency.
        self._session = session
        self._cache: dict[str, str | None] = {}

    def active_contract(self, root: str) -> str | None:
        key = root.replace(" ", "").lstrip("/@").upper()
        if key not in self._cache:
            self._cache[key] = self._lookup(key)
        return self._cache[key]

    def clear_cache(self) -> None:
        """Drop cached results (e.g. to pick up a contract roll without a new instance)."""
        self._cache.clear()

    def _lookup(self, root: str) -> str | None:
        try:
            from tastytrade.instruments import Future
        except ImportError as exc:  # pragma: no cover - only without the optional extra
            raise ImportError(
                "TastytradeActiveContractLookup requires the optional 'tastytrade' extra: "
                "pip install security-universe[tastytrade]"
            ) from exc

        try:
            chain = Future.get_future_chain(self._session, root)
        except Exception:
            # Network/auth/unknown-product failures degrade to a deterministic fallback.
            return None

        for contract in chain:
            if getattr(contract, "active_month", False):
                symbol = getattr(contract, "symbol", None)
                return str(symbol) if symbol else None
        return None
