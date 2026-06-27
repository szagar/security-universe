"""Typed security universe management for trading systems."""

from security_universes.exceptions import (
    DuplicateMemberError,
    DuplicateUniverseError,
    SecurityUniversesError,
    UniverseNotFoundError,
    ValidationError,
)
from security_universes.models import (
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
from security_universes.protocols import SecurityIdResolver
from security_universes.registry import UniverseRegistry
from security_universes.stores import InMemoryUniverseStore, SQLiteUniverseStore

__all__ = [
    "DuplicateMemberError",
    "DuplicateUniverseError",
    "ExpirationSession",
    "OptionType",
    "Security",
    "SecurityIdResolver",
    "SecurityType",
    "SecurityUniversesError",
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
    from security_universes.cli import main as cli_main

    raise SystemExit(cli_main())
