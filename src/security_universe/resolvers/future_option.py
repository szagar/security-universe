"""Future-option (options-on-futures) symbol resolver.

Futures options are NOT OCC-format. A TastyTrade futures-option order symbol
looks like::

    ./ESU6 E1CN6 260701C6325
      │     │     └────────── option expiry 26-07-01, Call, strike 6325
      │     └──────────────── option product/series code (CME)
      └────────────────────── underlying future contract ESU6

The option product/series code (``E1CN6``) is CME taxonomy — not computable from
``(future, expiry, right, strike)`` — so it cannot live in an algorithmic
``security_id``. This resolver captures it (the ``canonical.py`` parser in the
trading platform drops it) and stashes it in ``metadata`` so the native symbol
round-trips off the ``Security`` itself, no registry lookup required.

Pure / offline / deterministic, like every identity resolver: the product code
comes from the symbol, semantics from packaged ``future_option_rules.yaml``.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any, Mapping

from security_universe.models import (
    OptionType,
    Security,
    SecurityType,
    SettlementType,
)
from security_universe.resolvers._rules import (
    decimal_or_none,
    enum_or_none,
    normalize_rule_mapping,
    read_package_yaml,
    read_yaml_mapping,
)
from security_universe.resolvers.future import parse_future_symbol
from security_universe.resolvers.occ import format_strike

DEFAULT_RULE_FILE = "future_option_rules.yaml"

# Head: "./<future-contract> " — same shape as the platform's FUTURE_OPTION_PATTERN.
_HEAD_RE = re.compile(r"^\./(?P<future>[A-Z0-9]+[FGHJKMNQUVXZ]\d{1,2})\s+(?P<rest>.+)$")
# Trailing block: YYMMDD + C/P + strike — same shape as the platform's _FUT_OPT_TRAILING.
_TAIL_RE = re.compile(r"(?P<yymmdd>\d{6})(?P<cp>[CP])(?P<strike>\d+(?:\.\d+)?)$")


@dataclass(frozen=True)
class ParsedFutureOption:
    underlying_future: str  # "ESU6" — the dated future the option delivers
    product_code: str       # "E1CN6" — the option series; the token canonical.py drops
    expiry: date
    option_type: OptionType
    strike: Decimal


def parse_future_option_symbol(symbol: str) -> ParsedFutureOption | None:
    """Parse a TT futures-option order symbol. Returns ``None`` if it isn't one."""
    head = _HEAD_RE.match(symbol.strip().upper())
    if not head:
        return None
    rest = head.group("rest")
    tail = _TAIL_RE.search(rest)
    if not tail:
        return None
    # Everything between the future code and the trailing block is the series code.
    # Quarterly symbols may repeat the future code there; a bare symbol may omit it.
    product_code = rest[: tail.start()].strip() or head.group("future")
    yy = tail.group("yymmdd")
    return ParsedFutureOption(
        underlying_future=head.group("future"),
        product_code=product_code,
        expiry=date(2000 + int(yy[:2]), int(yy[2:4]), int(yy[4:6])),
        option_type=OptionType.CALL if tail.group("cp") == "C" else OptionType.PUT,
        strike=Decimal(tail.group("strike")),
    )


def future_option_security_id(
    root: str,
    contract: str,
    expiry: date,
    option_type: OptionType,
    strike: Decimal,
) -> str:
    """``future_option:ES:U6:2026-07-01:call:6325`` — mirrors ``future:{root}:{contract}``.

    Omits the product code: ``(future, expiry, right, strike)`` is already unique.
    """
    return (
        f"future_option:{root}:{contract}:"
        f"{expiry:%Y-%m-%d}:{option_type.value}:{format_strike(strike)}"
    )


def future_option_short_name(
    root: str,
    contract: str,
    expiry: date,
    option_type: OptionType,
    strike: Decimal,
) -> str:
    cp = "C" if option_type == OptionType.CALL else "P"
    return f"{root}{contract} {format_strike(strike)}{cp} {expiry:%Y-%m-%d}"


def load_default_future_option_rules() -> dict[str, dict[str, Any]]:
    return read_package_yaml(DEFAULT_RULE_FILE)


class FutureOptionSecurityIdResolver:
    """Assign ``future_option:…`` ids to options on futures.

    Applies when ``security_type`` is ``FUTURE_OPTION`` **or** the symbol parses
    as a futures-option order symbol (self-detection, like the OCC resolver).
    Securities of any other family are returned unchanged.
    """

    def __init__(
        self,
        rules: Mapping[str, Mapping[str, Any]] | None = None,
    ) -> None:
        self._rules = normalize_rule_mapping(rules or {})

    @classmethod
    def default(cls) -> "FutureOptionSecurityIdResolver":
        return cls(load_default_future_option_rules())

    @classmethod
    def from_yaml(
        cls,
        path: str | Path,
        *,
        include_defaults: bool = True,
    ) -> "FutureOptionSecurityIdResolver":
        rules = load_default_future_option_rules() if include_defaults else {}
        rules.update(read_yaml_mapping(path))
        return cls(rules)

    @property
    def rules(self) -> Mapping[str, Mapping[str, Any]]:
        return self._rules

    def resolve(self, security: Security) -> Security:
        parsed = parse_future_option_symbol(security.symbol)
        if parsed is None:
            # Not a futures-option symbol — leave it for another resolver.
            return security

        future = parse_future_symbol("/" + parsed.underlying_future)
        if future is None:  # pragma: no cover - head regex guarantees a dated future
            return security
        root = future.root
        contract = future.month_code + future.year_token  # e.g. "U6"
        rule = self._rules.get(root, {})

        return security.model_copy(
            update={
                "security_type": SecurityType.FUTURE_OPTION,
                "security_id": security.security_id
                or future_option_security_id(
                    root, contract, parsed.expiry, parsed.option_type, parsed.strike
                ),
                "short_name": security.short_name
                or future_option_short_name(
                    root, contract, parsed.expiry, parsed.option_type, parsed.strike
                ),
                "root_symbol": security.root_symbol or root,  # "ES"
                "underlying": security.underlying or parsed.underlying_future,  # "ESU6"
                "option_root": security.option_root or parsed.product_code,  # "E1CN6"
                "expiry": security.expiry or parsed.expiry,
                "strike": security.strike or parsed.strike,
                "option_type": security.option_type or parsed.option_type,
                "settlement_type": security.settlement_type
                or enum_or_none(SettlementType, rule.get("settlement_type"))
                or SettlementType.PHYSICAL,  # futures options deliver the future
                "contract_multiplier": security.contract_multiplier
                or decimal_or_none(rule.get("contract_multiplier")),
                # Non-lossy round-trip: the order symbol + series code live on the
                # Security itself, so to_tt(OF) is a field read, not a registry lookup.
                "metadata": {
                    **security.metadata,
                    "native_symbol": security.symbol,
                    "product_code": parsed.product_code,
                    "underlying_future": parsed.underlying_future,
                },
            }
        )
