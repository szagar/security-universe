"""Custom SecurityIdResolver example."""


def main() -> None:
    # from security_universes import Security, SecurityIdResolver, UniverseRegistry
    #
    # class PrefixResolver:
    #     def resolve(self, security: Security) -> Security:
    #         return security.model_copy(
    #             update={
    #                 "security_id": security.security_id
    #                 or f"{security.security_type}:{security.symbol}",
    #                 "short_name": security.short_name or security.symbol,
    #             }
    #         )
    #
    # registry = UniverseRegistry.memory(security_id_resolver=PrefixResolver())
    # ...
    raise NotImplementedError("Example becomes executable after implementation.")


if __name__ == "__main__":
    main()
