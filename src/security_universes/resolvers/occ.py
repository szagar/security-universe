"""OCC listed option symbol resolver."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from importlib import resources
from pathlib import Path
from typing import Any, Mapping

import yaml

from security_universes.models import (
    ExpirationSession,
    OptionType,
    Security,
    SecurityType,
    SettlementType,
)

OCC_RE = re.compile(
    r"^(?P<option_root>[A-Z][A-Z0-9]{0,5})"
    r"(?P<yy>\d{2})"
    r"(?P<mm>\d{2})"
    r"(?P<dd>\d{2})"
    r"(?P<cp>[CP])"
    r"(?P<strike>\d{8})$"
)

DEFAULT_RULE_FILES = (
    "index_option_rules.yaml",
    "adjusted_option_rules.yaml",
)


@dataclass(frozen=True)
class ParsedOCCSymbol:
    option_root: str
    expiry: date
    option_type: OptionType
    strike: Decimal


def parse_occ_symbol(symbol: str) -> ParsedOCCSymbol:
    match = OCC_RE.match(symbol.replace(" ", "").upper())
    if not match:
        raise ValueError(f"Invalid OCC option symbol: {symbol}")

    parts = match.groupdict()
    expiry = date(
        2000 + int(parts["yy"]),
        int(parts["mm"]),
        int(parts["dd"]),
    )
    option_type = OptionType.CALL if parts["cp"] == "C" else OptionType.PUT
    strike = Decimal(parts["strike"]) / Decimal("1000")

    return ParsedOCCSymbol(
        option_root=parts["option_root"],
        expiry=expiry,
        option_type=option_type,
        strike=strike,
    )


def format_strike(strike: Decimal) -> str:
    formatted = format(strike.normalize(), "f")
    if "." in formatted:
        formatted = formatted.rstrip("0").rstrip(".")
    return formatted or "0"


def option_short_name(
    option_root: str,
    strike: Decimal,
    option_type: OptionType,
    expiry: date,
) -> str:
    cp = "C" if option_type == OptionType.CALL else "P"
    return f"{option_root} {format_strike(strike)}{cp} {expiry:%Y-%m-%d}"


def option_security_id(
    option_root: str,
    expiry: date,
    option_type: OptionType,
    strike: Decimal,
) -> str:
    return (
        f"option:{option_root}:{expiry:%Y-%m-%d}:"
        f"{option_type.value}:{format_strike(strike)}"
    )


def _read_yaml_mapping(path: str | Path) -> dict[str, dict[str, Any]]:
    with Path(path).open("r", encoding="utf-8") as file:
        data = yaml.safe_load(file) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Rule file must contain a mapping: {path}")
    return _normalize_rule_mapping(data)


def _read_package_yaml(name: str) -> dict[str, dict[str, Any]]:
    resource = resources.files("security_universes.resolvers.data").joinpath(name)
    data = yaml.safe_load(resource.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Packaged rule file must contain a mapping: {name}")
    return _normalize_rule_mapping(data)


def _normalize_rule_mapping(data: Mapping[Any, Any]) -> dict[str, dict[str, Any]]:
    normalized: dict[str, dict[str, Any]] = {}
    for root, rule in data.items():
        if not isinstance(root, str) or not isinstance(rule, dict):
            raise ValueError("Option-root rules must map root strings to mappings")
        normalized[root.upper()] = dict(rule)
    return normalized


def load_default_option_rules() -> dict[str, dict[str, Any]]:
    rules: dict[str, dict[str, Any]] = {}
    for file_name in DEFAULT_RULE_FILES:
        rules.update(_read_package_yaml(file_name))
    return rules


def _enum_or_none(enum_type, value: Any):
    if value is None:
        return None
    return enum_type(value)


def _decimal_or_none(value: Any) -> Decimal | None:
    if value is None:
        return None
    return Decimal(str(value))


class OCCSecurityIdResolver:
    def __init__(
        self,
        option_rules: Mapping[str, Mapping[str, Any]] | None = None,
    ) -> None:
        self._option_rules = _normalize_rule_mapping(option_rules or {})

    @classmethod
    def default(cls) -> "OCCSecurityIdResolver":
        return cls(load_default_option_rules())

    @classmethod
    def from_yaml(
        cls,
        path: str | Path,
        *,
        include_defaults: bool = True,
    ) -> "OCCSecurityIdResolver":
        rules = load_default_option_rules() if include_defaults else {}
        rules.update(_read_yaml_mapping(path))
        return cls(rules)

    @property
    def option_rules(self) -> Mapping[str, Mapping[str, Any]]:
        return self._option_rules

    def resolve(self, security: Security) -> Security:
        normalized_symbol = security.symbol.replace(" ", "").upper()
        if security.security_type != SecurityType.OPTION and not OCC_RE.match(
            normalized_symbol
        ):
            return security

        parsed = parse_occ_symbol(security.symbol)
        rule = self._option_rules.get(parsed.option_root, {})

        return security.model_copy(
            update={
                "security_type": SecurityType.OPTION,
                "security_id": security.security_id
                or option_security_id(
                    option_root=parsed.option_root,
                    expiry=parsed.expiry,
                    option_type=parsed.option_type,
                    strike=parsed.strike,
                ),
                "short_name": security.short_name
                or option_short_name(
                    option_root=parsed.option_root,
                    strike=parsed.strike,
                    option_type=parsed.option_type,
                    expiry=parsed.expiry,
                ),
                "option_root": security.option_root or parsed.option_root,
                "underlying": security.underlying
                or rule.get("underlying")
                or parsed.option_root,
                "expiry": security.expiry or parsed.expiry,
                "strike": security.strike or parsed.strike,
                "option_type": security.option_type or parsed.option_type,
                "expiration_session": security.expiration_session
                or _enum_or_none(ExpirationSession, rule.get("expiration_session"))
                or ExpirationSession.UNKNOWN,
                "settlement_type": security.settlement_type
                or _enum_or_none(SettlementType, rule.get("settlement_type"))
                or SettlementType.UNKNOWN,
                "contract_multiplier": security.contract_multiplier
                or _decimal_or_none(rule.get("contract_multiplier")),
                "deliverable_type": security.deliverable_type
                or rule.get("deliverable_type"),
                "deliverable_description": security.deliverable_description
                or rule.get("deliverable_description"),
                "deliverable": security.deliverable or rule.get("deliverable") or {},
            }
        )
