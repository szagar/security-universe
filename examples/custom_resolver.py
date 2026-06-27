"""Custom SecurityIdResolver example."""

from security_universes import Security, UniverseRegistry


class PrefixResolver:
    def resolve(self, security: Security) -> Security:
        return security.model_copy(
            update={
                "security_id": security.security_id
                or f"{security.security_type}:{security.symbol}",
                "short_name": security.short_name or security.symbol,
            }
        )


def main() -> None:
    registry = UniverseRegistry.memory(security_id_resolver=PrefixResolver())
    registry.create_universe("watchlist")
    member = registry.add_member("watchlist", "AAPL")
    print(member.security.security_id)


if __name__ == "__main__":
    main()
