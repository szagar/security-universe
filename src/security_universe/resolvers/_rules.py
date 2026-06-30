"""Shared rule-table loading + value coercion for symbol resolvers.

Both the OCC option resolver and the future-option resolver enrich a parsed
contract from a per-root YAML rule table (settlement, multiplier, …). These
helpers are the common loading/normalization machinery; the resolvers own the
parsing and the field-mapping. Pure, offline, deterministic — no I/O beyond
reading packaged YAML.
"""

from __future__ import annotations

from decimal import Decimal
from importlib import resources
from pathlib import Path
from typing import Any, Mapping

import yaml

_DATA_PACKAGE = "security_universe.resolvers.data"


def normalize_rule_mapping(data: Mapping[Any, Any]) -> dict[str, dict[str, Any]]:
    """Upper-case the root keys and shallow-copy each rule mapping.

    Rejects anything that isn't ``{root_str: {field: value}}``.
    """
    normalized: dict[str, dict[str, Any]] = {}
    for root, rule in data.items():
        if not isinstance(root, str) or not isinstance(rule, dict):
            raise ValueError("Resolver rules must map root strings to mappings")
        normalized[root.upper()] = dict(rule)
    return normalized


def read_yaml_mapping(path: str | Path) -> dict[str, dict[str, Any]]:
    """Load a user-supplied rule file from disk."""
    with Path(path).open("r", encoding="utf-8") as file:
        data = yaml.safe_load(file) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Rule file must contain a mapping: {path}")
    return normalize_rule_mapping(data)


def read_package_yaml(name: str) -> dict[str, dict[str, Any]]:
    """Load a packaged rule file from ``security_universe.resolvers.data``."""
    resource = resources.files(_DATA_PACKAGE).joinpath(name)
    data = yaml.safe_load(resource.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Packaged rule file must contain a mapping: {name}")
    return normalize_rule_mapping(data)


def enum_or_none(enum_type, value: Any):
    """Coerce ``value`` to ``enum_type``, passing ``None`` through unchanged."""
    if value is None:
        return None
    return enum_type(value)


def decimal_or_none(value: Any) -> Decimal | None:
    """Coerce ``value`` to ``Decimal``, passing ``None`` through unchanged."""
    if value is None:
        return None
    return Decimal(str(value))
