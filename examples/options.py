"""OCC option resolver example."""

from security_universe import Security, SecurityType, UniverseRegistry
from security_universe.resolvers.occ import OCCSecurityIdResolver


def main() -> None:
    resolver = OCCSecurityIdResolver.default()
    registry = UniverseRegistry.memory(security_id_resolver=resolver)
    registry.create_universe("spx-options", universe_type="watchlist")
    member = registry.add_member(
        "spx-options",
        Security(
            symbol="SPXW260619C06100000",
            security_type=SecurityType.OPTION,
        ),
    )
    print(member.security.security_id)


if __name__ == "__main__":
    main()
