"""Typed security universe management for trading systems."""

from security_universe.exceptions import (
    DuplicateMemberError,
    DuplicateUniverseError,
    SecurityUniverseError,
    UniverseNotFoundError,
    ValidationError,
)
from security_universe.models import (
    ExpirationSession,
    OptionType,
    Security,
    SecurityType,
    SettlementType,
    SourceType,
    Universe,
    UniverseMember,
    UniverseType,
)
from security_universe.protocols import ActiveContractLookup, SecurityIdResolver
from security_universe.registry import UniverseRegistry
from security_universe.stores import InMemoryUniverseStore, SQLiteUniverseStore

__all__ = [
    "ActiveContractLookup",
    "DuplicateMemberError",
    "DuplicateUniverseError",
    "ExpirationSession",
    "OptionType",
    "Security",
    "SecurityIdResolver",
    "SecurityType",
    "SecurityUniverseError",
    "SettlementType",
    "SourceType",
    "InMemoryUniverseStore",
    "SQLiteUniverseStore",
    "Universe",
    "UniverseMember",
    "UniverseNotFoundError",
    "UniverseRegistry",
    "UniverseType",
    "ValidationError",
]


def main() -> None:
    from security_universe.cli import main as cli_main

    raise SystemExit(cli_main())
