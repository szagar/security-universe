# API Contract

This document defines the intended public Python API.

Concrete implementation may split classes across modules, but these names
should be exported from `security_universe`.

## Enums

```python
class SecurityType(StrEnum):
    STOCK = "stock"
    ETF = "etf"
    FUTURE = "future"
    OPTION = "option"
    CRYPTO = "crypto"
    FX = "fx"
    BOND = "bond"
    OTC = "otc"
    UNKNOWN = "unknown"


class UniverseType(StrEnum):
    WATCHLIST = "watchlist"
    WHITELIST = "whitelist"
    BLACKLIST = "blacklist"
    RESTRICTED = "restricted"
    BOT_INPUT = "bot_input"
    INDEX = "index"
    SCREENER_RESULT = "screener_result"
    PORTFOLIO = "portfolio"
    CUSTOM = "custom"


class SourceType(StrEnum):
    STATIC = "static"
    QUERY = "query"
    API = "api"
    BOT = "bot"
    MANUAL = "manual"
    IMPORT = "import"


class OptionType(StrEnum):
    CALL = "call"
    PUT = "put"


class ExpirationSession(StrEnum):
    AM = "am"
    PM = "pm"
    UNKNOWN = "unknown"


class SettlementType(StrEnum):
    CASH = "cash"
    PHYSICAL = "physical"
    UNKNOWN = "unknown"
```

## Security

```python
class Security(BaseModel):
    symbol: str
    security_type: SecurityType = SecurityType.UNKNOWN

    security_id: str | None = None
    short_name: str | None = None

    exchange: str | None = None
    currency: str | None = None

    underlying: str | None = None
    root_symbol: str | None = None
    option_root: str | None = None

    expiry: date | None = None
    strike: Decimal | None = None
    option_type: OptionType | None = None

    expiration_session: ExpirationSession | None = None
    settlement_type: SettlementType | None = None
    contract_multiplier: Decimal | None = None

    deliverable_type: str | None = None
    deliverable_description: str | None = None
    deliverable: dict[str, Any] = Field(default_factory=dict)

    metadata: dict[str, Any] = Field(default_factory=dict)
```

## Universe

```python
class Universe(BaseModel):
    name: str
    universe_type: UniverseType = UniverseType.CUSTOM

    description: str | None = None
    enabled: bool = True
    source_type: SourceType = SourceType.MANUAL
    definition: dict[str, Any] = Field(default_factory=dict)

    tags: set[str] = Field(default_factory=set)
    metadata: dict[str, Any] = Field(default_factory=dict)

    created_at: datetime | None = None
    updated_at: datetime | None = None
```

## UniverseMember

```python
class UniverseMember(BaseModel):
    universe_name: str
    security: Security

    member_id: str | None = None
    weight: Decimal | None = None
    active: bool = True

    added_at: datetime | None = None
    added_by: str | None = None
    expires_at: datetime | None = None

    source: str | None = None
    reason: str | None = None
    tags: set[str] = Field(default_factory=set)
    metadata: dict[str, Any] = Field(default_factory=dict)
```

## SecurityIdResolver

```python
class SecurityIdResolver(Protocol):
    def resolve(self, security: Security) -> Security: ...
```

Resolvers return a copied/enriched `Security` and must not mutate the input.

## UniverseStore

```python
class UniverseStore(Protocol):
    def create_universe(self, universe: Universe) -> Universe: ...
    def delete_universe(self, name: str) -> None: ...
    def get_universe(self, name: str) -> Universe | None: ...
    def list_universes(self) -> list[Universe]: ...

    def add_member(self, member: UniverseMember) -> UniverseMember: ...
    def remove_member(self, universe_name: str, security: Security | str) -> None: ...
    def list_members(self, universe_name: str, *, active_only: bool = True) -> list[UniverseMember]: ...
    def contains(self, universe_name: str, security: Security | str) -> bool: ...
```

## UniverseRegistry

Minimum public API:

```python
class UniverseRegistry:
    def create_universe(...): ...
    def delete_universe(...): ...
    def get_universe(...): ...
    def list_universes(...): ...

    def add_member(...): ...
    def remove_member(...): ...
    def contains(...): ...

    def resolve(...): ...
```

Recommended concrete shape:

```python
class UniverseRegistry:
    def __init__(
        self,
        store: UniverseStore | None = None,
        security_id_resolver: SecurityIdResolver | None = None,
    ) -> None: ...

    @classmethod
    def memory(
        cls,
        *,
        security_id_resolver: SecurityIdResolver | None = None,
    ) -> "UniverseRegistry": ...

    @classmethod
    def sqlite(
        cls,
        path: str | Path,
        *,
        security_id_resolver: SecurityIdResolver | None = None,
    ) -> "UniverseRegistry": ...

    def create_universe(
        self,
        name: str,
        *,
        universe_type: UniverseType | str = UniverseType.CUSTOM,
        description: str | None = None,
        enabled: bool = True,
        tags: set[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Universe: ...

    def delete_universe(self, name: str) -> None: ...
    def get_universe(self, name: str) -> Universe | None: ...
    def list_universes(self) -> list[Universe]: ...

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
    ) -> UniverseMember: ...

    def remove_member(self, universe_name: str, security: Security | str) -> None: ...
    def contains(self, universe_name: str, security: Security | str) -> bool: ...

    def list_members(
        self,
        universe_name: str,
        *,
        active_only: bool = True,
    ) -> list[UniverseMember]: ...

    def resolve(
        self,
        *,
        include: list[str],
        exclude: list[str] | None = None,
    ) -> list[Security]: ...
```

## Resolver Configuration Example

```python
resolver = OCCSecurityIdResolver.from_yaml("my_index_option_rules.yaml")

registry = UniverseRegistry.sqlite(
    "universe.db",
    security_id_resolver=resolver,
)
```
