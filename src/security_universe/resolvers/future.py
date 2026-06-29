"""Futures security-id resolver."""

from __future__ import annotations

import re
from dataclasses import dataclass

from security_universe.models import Security, SecurityType
from security_universe.protocols import ActiveContractLookup

# CME/standard futures month codes.
MONTH_CODES: dict[str, int] = {
    "F": 1, "G": 2, "H": 3, "J": 4, "K": 5, "M": 6,
    "N": 7, "Q": 8, "U": 9, "V": 10, "X": 11, "Z": 12,
}

# An optional leading "/", a 1-4 char root, a single month code, then a 1-2 digit year.
FUTURE_RE = re.compile(
    r"^/?(?P<root>[A-Z0-9]{1,4})(?P<month>[FGHJKMNQUVXZ])(?P<year>\d{1,2})$"
)


@dataclass(frozen=True)
class ParsedFutureSymbol:
    root: str
    month_code: str
    month: int
    year_token: str  # kept verbatim — a single-digit year is century-ambiguous


def parse_future_symbol(symbol: str) -> ParsedFutureSymbol | None:
    """Parse a dated futures symbol (e.g. ``/ESM6``). Returns ``None`` if it doesn't match."""
    match = FUTURE_RE.match(symbol.replace(" ", "").upper())
    if not match:
        return None
    parts = match.groupdict()
    return ParsedFutureSymbol(
        root=parts["root"],
        month_code=parts["month"],
        month=MONTH_CODES[parts["month"]],
        year_token=parts["year"],
    )


def future_security_id(root: str, month_code: str, year_token: str) -> str:
    return f"future:{root}:{month_code}{year_token}"


def future_short_name(root: str, month_code: str, year_token: str) -> str:
    """Display name for a dated contract: ``/`` + root + month code + last year digit (``/ESM6``)."""
    return f"/{root}{month_code}{year_token[-1]}"


def future_active_security_id(root: str) -> str:
    """Sentinel id for an unresolved active/front-month request: ``future:ES:active``."""
    return f"future:{root}:active"


class FutureSecurityIdResolver:
    """Assign a canonical id to futures.

    Applies only when ``security_type`` is ``FUTURE``. There are three forms:

    * **Dated** (``/ESM6``) → ``future:ES:M6``. The month/year tokens are kept verbatim — a
      single-digit year is century-ambiguous, so **no expiry is inferred**, keeping the id
      deterministic.
    * **Continuous** (``@ES``) → ``future:ES`` (display ``@ES``). A back-adjusted price series, not a
      tradeable contract.
    * **Active / front-month** (``/ES``) → the *current* dated contract when an ``active_lookup`` is
      injected (``/ES`` → ``future:ES:U6``), otherwise the deterministic sentinel
      ``future:ES:active`` (display ``/ES``). Injecting a lookup is the only way the result depends
      on the network/clock; the default resolver stays pure and offline.

    A bare root with no prefix (``ES``) is treated as continuous.
    """

    def __init__(self, active_lookup: ActiveContractLookup | None = None) -> None:
        self._active_lookup = active_lookup

    def resolve(self, security: Security) -> Security:
        if security.security_type != SecurityType.FUTURE:
            return security

        parsed = parse_future_symbol(security.symbol)
        if parsed is not None:
            security_id = future_security_id(parsed.root, parsed.month_code, parsed.year_token)
            root = parsed.root
            short_name = future_short_name(parsed.root, parsed.month_code, parsed.year_token)
        else:
            security_id, root, short_name = self._resolve_undated(security.symbol)

        return security.model_copy(
            update={
                "security_id": security.security_id or security_id,
                "short_name": security.short_name or short_name,
                "root_symbol": security.root_symbol or root,
                "underlying": security.underlying or root,
            }
        )

    def _resolve_undated(self, symbol: str) -> tuple[str, str, str]:
        """Resolve a non-dated symbol to ``(security_id, root, short_name)``."""
        cleaned = symbol.replace(" ", "")
        root = cleaned.lstrip("/@").upper()

        # Only a leading "/" (active/front-month) consults the live lookup; "@" is continuous.
        if cleaned.startswith("/"):
            if self._active_lookup is not None:
                dated = self._active_lookup.active_contract(root)
                parsed = parse_future_symbol(dated) if dated else None
                if parsed is not None:
                    return (
                        future_security_id(parsed.root, parsed.month_code, parsed.year_token),
                        parsed.root,
                        future_short_name(parsed.root, parsed.month_code, parsed.year_token),
                    )
            return future_active_security_id(root), root, f"/{root}"

        # Continuous contract (or bare root) — back-adjusted series, prefixed with "@".
        return f"future:{root}", root, f"@{root}"
