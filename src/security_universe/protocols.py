"""Public protocols for extension points."""

from __future__ import annotations

from typing import Protocol

from security_universe.models import Security, Universe, UniverseMember


class SecurityIdResolver(Protocol):
    def resolve(self, security: Security) -> Security: ...


class ActiveContractLookup(Protocol):
    """Resolve a futures root to its current front-month dated symbol (e.g. ``ES`` → ``/ESU6``).

    This is the one extension point allowed to be impure: implementations may hit the network,
    require credentials, and return different answers over time (the active contract rolls
    quarterly). Returning ``None`` signals "couldn't determine" — callers fall back to a
    deterministic id rather than failing.
    """

    def active_contract(self, root: str) -> str | None: ...


class UniverseStore(Protocol):
    def create_universe(self, universe: Universe) -> Universe: ...
    def delete_universe(self, name: str) -> None: ...
    def get_universe(self, name: str) -> Universe | None: ...
    def list_universes(self) -> list[Universe]: ...

    def add_member(self, member: UniverseMember) -> UniverseMember: ...
    def remove_member(self, universe_name: str, security: Security | str) -> None: ...
    def list_members(
        self,
        universe_name: str,
        *,
        active_only: bool = True,
    ) -> list[UniverseMember]: ...
    def contains(self, universe_name: str, security: Security | str) -> bool: ...

