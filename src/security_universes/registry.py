"""Application-facing universe registry."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

from security_universes.exceptions import UniverseNotFoundError
from security_universes.models import (
    Security,
    SecurityType,
    SourceType,
    Universe,
    UniverseMember,
    UniverseType,
)
from security_universes.protocols import SecurityIdResolver, UniverseStore
from security_universes.stores import (
    InMemoryUniverseStore,
    SQLiteUniverseStore,
    security_key,
)


class UniverseRegistry:
    def __init__(
        self,
        store: UniverseStore | None = None,
        security_id_resolver: SecurityIdResolver | None = None,
    ) -> None:
        self._store = store or InMemoryUniverseStore()
        self._security_id_resolver = security_id_resolver

    @classmethod
    def memory(
        cls,
        *,
        security_id_resolver: SecurityIdResolver | None = None,
    ) -> "UniverseRegistry":
        return cls(
            store=InMemoryUniverseStore(),
            security_id_resolver=security_id_resolver,
        )

    @classmethod
    def sqlite(
        cls,
        path: str | Path,
        *,
        security_id_resolver: SecurityIdResolver | None = None,
    ) -> "UniverseRegistry":
        return cls(
            store=SQLiteUniverseStore(path),
            security_id_resolver=security_id_resolver,
        )

    def create_universe(
        self,
        name: str,
        *,
        universe_type: UniverseType | str = UniverseType.CUSTOM,
        description: str | None = None,
        enabled: bool = True,
        tags: set[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Universe:
        now = datetime.now(timezone.utc)
        universe = Universe(
            name=name,
            universe_type=UniverseType(universe_type),
            description=description,
            enabled=enabled,
            source_type=SourceType.MANUAL,
            tags=tags or set(),
            metadata=metadata or {},
            created_at=now,
            updated_at=now,
        )
        return self._store.create_universe(universe)

    def delete_universe(self, name: str) -> None:
        self._store.delete_universe(name)

    def get_universe(self, name: str) -> Universe | None:
        return self._store.get_universe(name)

    def list_universes(self) -> list[Universe]:
        return self._store.list_universes()

    def add_member(
        self,
        universe_name: str,
        security: Security | str,
        *,
        security_type: SecurityType | str = SecurityType.UNKNOWN,
        weight: Decimal | None = None,
        source: str | None = None,
        reason: str | None = None,
        added_by: str | None = None,
        expires_at: datetime | None = None,
        tags: set[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> UniverseMember:
        self._require_universe(universe_name)
        resolved_security = self._coerce_security(security, security_type=security_type)
        member = UniverseMember(
            universe_name=universe_name,
            security=resolved_security,
            member_id=f"{universe_name}:{security_key(resolved_security)}",
            weight=weight,
            added_at=datetime.now(timezone.utc),
            added_by=added_by,
            expires_at=expires_at,
            source=source,
            reason=reason,
            tags=tags or set(),
            metadata=metadata or {},
        )
        return self._store.add_member(member)

    def remove_member(self, universe_name: str, security: Security | str) -> None:
        self._require_universe(universe_name)
        self._store.remove_member(universe_name, security)

    def contains(self, universe_name: str, security: Security | str) -> bool:
        self._require_universe(universe_name)
        return self._store.contains(universe_name, security)

    def list_members(
        self,
        universe_name: str,
        *,
        active_only: bool = True,
    ) -> list[UniverseMember]:
        self._require_universe(universe_name)
        return self._store.list_members(universe_name, active_only=active_only)

    def resolve(
        self,
        *,
        include: list[str],
        exclude: list[str] | None = None,
    ) -> list[Security]:
        excluded_keys = {
            member.security.identity
            for universe_name in (exclude or [])
            for member in self._active_enabled_members(universe_name)
        }

        resolved: dict[str, Security] = {}
        for universe_name in include:
            for member in self._active_enabled_members(universe_name):
                key = member.security.identity
                if key not in excluded_keys and key not in resolved:
                    resolved[key] = member.security

        return list(resolved.values())

    def _active_enabled_members(self, universe_name: str) -> list[UniverseMember]:
        universe = self._require_universe(universe_name)
        if not universe.enabled:
            return []
        return self._store.list_members(universe_name, active_only=True)

    def _require_universe(self, name: str) -> Universe:
        universe = self._store.get_universe(name)
        if universe is None:
            raise UniverseNotFoundError(f"Universe not found: {name}")
        return universe

    def _coerce_security(
        self,
        security: Security | str,
        *,
        security_type: SecurityType | str,
    ) -> Security:
        coerced = (
            security
            if isinstance(security, Security)
            else Security(symbol=security, security_type=SecurityType(security_type))
        )
        if self._security_id_resolver is None:
            return coerced
        return self._security_id_resolver.resolve(coerced)
