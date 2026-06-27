"""Storage implementations."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from security_universe.exceptions import DuplicateMemberError, DuplicateUniverseError
from security_universe.models import Security, Universe, UniverseMember


def security_key(security: Security | str) -> str:
    if isinstance(security, Security):
        return security.identity
    return security


def member_is_current(member: UniverseMember, *, now: datetime | None = None) -> bool:
    if not member.active:
        return False
    if member.expires_at is None:
        return True

    comparison_now = now or datetime.now(timezone.utc)
    expires_at = member.expires_at
    if expires_at.tzinfo is None:
        comparison_now = comparison_now.replace(tzinfo=None)
    return expires_at > comparison_now


class InMemoryUniverseStore:
    def __init__(self) -> None:
        self._universes: dict[str, Universe] = {}
        self._members: dict[str, dict[str, UniverseMember]] = {}

    def create_universe(self, universe: Universe) -> Universe:
        if universe.name in self._universes:
            raise DuplicateUniverseError(f"Universe already exists: {universe.name}")

        stored = universe.model_copy(deep=True)
        self._universes[stored.name] = stored
        self._members[stored.name] = {}
        return stored.model_copy(deep=True)

    def delete_universe(self, name: str) -> None:
        self._universes.pop(name, None)
        self._members.pop(name, None)

    def get_universe(self, name: str) -> Universe | None:
        universe = self._universes.get(name)
        return universe.model_copy(deep=True) if universe else None

    def list_universes(self) -> list[Universe]:
        return [
            universe.model_copy(deep=True)
            for universe in sorted(self._universes.values(), key=lambda item: item.name)
        ]

    def add_member(self, member: UniverseMember) -> UniverseMember:
        key = security_key(member.security)
        universe_members = self._members.setdefault(member.universe_name, {})
        if key in universe_members:
            raise DuplicateMemberError(
                f"Security already exists in universe {member.universe_name}: {key}"
            )

        stored = member.model_copy(deep=True)
        universe_members[key] = stored
        return stored.model_copy(deep=True)

    def remove_member(self, universe_name: str, security: Security | str) -> None:
        universe_members = self._members.get(universe_name, {})
        key = security_key(security)
        if key in universe_members:
            del universe_members[key]
            return

        for member_key, member in list(universe_members.items()):
            if member.security.symbol == key:
                del universe_members[member_key]
                return

    def list_members(
        self,
        universe_name: str,
        *,
        active_only: bool = True,
    ) -> list[UniverseMember]:
        members = list(self._members.get(universe_name, {}).values())
        if active_only:
            members = [member for member in members if member_is_current(member)]
        return [
            member.model_copy(deep=True)
            for member in sorted(members, key=lambda item: item.security.identity)
        ]

    def contains(self, universe_name: str, security: Security | str) -> bool:
        universe_members = self._members.get(universe_name, {})
        key = security_key(security)
        if key in universe_members:
            return member_is_current(universe_members[key])
        return any(
            member.security.symbol == key and member_is_current(member)
            for member in universe_members.values()
        )


class SQLiteUniverseStore:
    def __init__(self, path: str | Path) -> None:
        self.path = path
        self._connection = sqlite3.connect(path)
        self._connection.row_factory = sqlite3.Row
        self._initialize()

    def _initialize(self) -> None:
        self._connection.execute(
            """
            CREATE TABLE IF NOT EXISTS universes (
                name TEXT PRIMARY KEY,
                payload TEXT NOT NULL
            )
            """
        )
        self._connection.execute(
            """
            CREATE TABLE IF NOT EXISTS members (
                universe_name TEXT NOT NULL,
                security_key TEXT NOT NULL,
                payload TEXT NOT NULL,
                PRIMARY KEY (universe_name, security_key),
                FOREIGN KEY (universe_name)
                    REFERENCES universes(name)
                    ON DELETE CASCADE
            )
            """
        )
        self._connection.commit()

    def create_universe(self, universe: Universe) -> Universe:
        stored = universe.model_copy(deep=True)
        try:
            self._connection.execute(
                "INSERT INTO universes (name, payload) VALUES (?, ?)",
                (stored.name, stored.model_dump_json()),
            )
        except sqlite3.IntegrityError as exc:
            raise DuplicateUniverseError(
                f"Universe already exists: {universe.name}"
            ) from exc
        self._connection.commit()
        return stored.model_copy(deep=True)

    def delete_universe(self, name: str) -> None:
        self._connection.execute("DELETE FROM members WHERE universe_name = ?", (name,))
        self._connection.execute("DELETE FROM universes WHERE name = ?", (name,))
        self._connection.commit()

    def get_universe(self, name: str) -> Universe | None:
        row = self._connection.execute(
            "SELECT payload FROM universes WHERE name = ?",
            (name,),
        ).fetchone()
        if row is None:
            return None
        return Universe.model_validate_json(row["payload"])

    def list_universes(self) -> list[Universe]:
        rows = self._connection.execute(
            "SELECT payload FROM universes ORDER BY name"
        ).fetchall()
        return [Universe.model_validate_json(row["payload"]) for row in rows]

    def add_member(self, member: UniverseMember) -> UniverseMember:
        stored = member.model_copy(deep=True)
        key = security_key(stored.security)
        try:
            self._connection.execute(
                """
                INSERT INTO members (universe_name, security_key, payload)
                VALUES (?, ?, ?)
                """,
                (stored.universe_name, key, stored.model_dump_json()),
            )
        except sqlite3.IntegrityError as exc:
            raise DuplicateMemberError(
                f"Security already exists in universe {stored.universe_name}: {key}"
            ) from exc
        self._connection.commit()
        return stored.model_copy(deep=True)

    def remove_member(self, universe_name: str, security: Security | str) -> None:
        key = security_key(security)
        cursor = self._connection.execute(
            "DELETE FROM members WHERE universe_name = ? AND security_key = ?",
            (universe_name, key),
        )
        if cursor.rowcount:
            self._connection.commit()
            return

        for row in self._connection.execute(
            "SELECT security_key, payload FROM members WHERE universe_name = ?",
            (universe_name,),
        ).fetchall():
            member = UniverseMember.model_validate_json(row["payload"])
            if member.security.symbol == key:
                self._connection.execute(
                    """
                    DELETE FROM members
                    WHERE universe_name = ? AND security_key = ?
                    """,
                    (universe_name, row["security_key"]),
                )
                self._connection.commit()
                return

    def list_members(
        self,
        universe_name: str,
        *,
        active_only: bool = True,
    ) -> list[UniverseMember]:
        rows = self._connection.execute(
            """
            SELECT payload FROM members
            WHERE universe_name = ?
            ORDER BY security_key
            """,
            (universe_name,),
        ).fetchall()
        members = [UniverseMember.model_validate_json(row["payload"]) for row in rows]
        if active_only:
            members = [member for member in members if member_is_current(member)]
        return members

    def contains(self, universe_name: str, security: Security | str) -> bool:
        key = security_key(security)
        row = self._connection.execute(
            """
            SELECT payload FROM members
            WHERE universe_name = ? AND security_key = ?
            """,
            (universe_name, key),
        ).fetchone()
        if row is not None:
            return member_is_current(UniverseMember.model_validate_json(row["payload"]))

        rows = self._connection.execute(
            "SELECT payload FROM members WHERE universe_name = ?",
            (universe_name,),
        ).fetchall()
        return any(
            member.security.symbol == key and member_is_current(member)
            for member in (
                UniverseMember.model_validate_json(row["payload"]) for row in rows
            )
        )

    def close(self) -> None:
        self._connection.close()
