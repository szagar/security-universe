"""A chain-of-responsibility over several single-family identity resolvers.

"Chain" here means chain-of-responsibility (try each resolver in turn) — NOT an
option chain. This composes :class:`SecurityIdResolver` implementations; it has
nothing to do with option-chain market data.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence

from security_universe.models import Security
from security_universe.protocols import SecurityIdResolver
from security_universe.resolvers.crypto import CryptoSecurityIdResolver
from security_universe.resolvers.equity import EquitySecurityIdResolver
from security_universe.resolvers.future import FutureSecurityIdResolver
from security_universe.resolvers.index import IndexSecurityIdResolver
from security_universe.resolvers.future_option import FutureOptionSecurityIdResolver
from security_universe.resolvers.occ import OCCSecurityIdResolver


class ResolverChain:
    """Try each member resolver in order; return the first that assigns a ``security_id``.

    Each member returns the security unchanged when it doesn't apply, so a chain lets a single
    injected resolver cover a whole account (options + equities + futures + …). If no member assigns
    an id, the (possibly enriched) security is returned with ``security_id`` still ``None`` — callers
    can then fall back to the vendor symbol.
    """

    def __init__(self, resolvers: Iterable[SecurityIdResolver]) -> None:
        self._resolvers: tuple[SecurityIdResolver, ...] = tuple(resolvers)

    @property
    def resolvers(self) -> Sequence[SecurityIdResolver]:
        return self._resolvers

    def resolve(self, security: Security) -> Security:
        current = security
        for resolver in self._resolvers:
            current = resolver.resolve(current)
            if current.security_id:
                return current
        return current

    @classmethod
    def default(cls) -> "ResolverChain":
        """Future options + OCC options + equities + indices + futures + crypto — the common families.

        Pure, offline, deterministic: futures ``/ROOT`` symbols resolve to ``future:{root}:active``
        rather than a dated contract. Use :meth:`with_tastytrade` for live front-month resolution.
        The future-option resolver runs first (it self-detects ``./…``-prefixed symbols).
        """
        return cls(
            (
                FutureOptionSecurityIdResolver.default(),
                OCCSecurityIdResolver.default(),
                EquitySecurityIdResolver(),
                IndexSecurityIdResolver(),
                FutureSecurityIdResolver(),
                CryptoSecurityIdResolver(),
            )
        )

    @classmethod
    def with_tastytrade(cls, session: object) -> "ResolverChain":
        """Like :meth:`default`, but futures ``/ROOT`` resolves to the live front-month contract.

        Requires the optional ``tastytrade`` extra and a ``tastytrade.Session``. Network/auth
        failures degrade gracefully to the deterministic ``future:{root}:active`` id, so callers
        still get a usable chain when the lookup is unavailable.
        """
        from security_universe.resolvers.tastytrade import TastytradeActiveContractLookup

        return cls(
            (
                FutureOptionSecurityIdResolver.default(),
                OCCSecurityIdResolver.default(),
                EquitySecurityIdResolver(),
                IndexSecurityIdResolver(),
                FutureSecurityIdResolver(active_lookup=TastytradeActiveContractLookup(session)),
                CryptoSecurityIdResolver(),
            )
        )
