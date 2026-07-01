"""Core domain models for securities and universe membership."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class SecurityType(StrEnum):
    STOCK = "stock"
    ETF = "etf"
    INDEX = "index"
    FUTURE = "future"
    OPTION = "option"
    FUTURE_OPTION = "future_option"
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


class DomainModel(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=False,
        extra="forbid",
        populate_by_name=True,
        str_strip_whitespace=True,
        validate_assignment=True,
    )


class Security(DomainModel):
    symbol: str = Field(
        description=(
            "The native symbol exactly as supplied by the caller (broker, vendor, "
            "or user). Provenance is the caller's: this is NOT guaranteed to be the "
            "broker order symbol or a normalized form. Use `security_id` for "
            "canonical identity and `order_symbol` for the broker order symbol."
        )
    )
    security_type: SecurityType = SecurityType.UNKNOWN

    security_id: str | None = None
    short_name: str | None = None

    order_symbol: str | None = Field(
        default=None,
        description=(
            "The broker order symbol (e.g. the TastyTrade futures-option symbol "
            "`./ESU6 E1CN6 260701C6325`). For most families it is algorithmic from "
            "`security_id`; for options-on-futures it is opaque (carries a CME series "
            "code) and must be carried. A market-data source that read the chain is "
            "its authoritative populator; resolvers may set it as a best-effort "
            "fallback when the input `symbol` is itself a recognized order symbol."
        ),
    )

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

    @field_validator("symbol")
    @classmethod
    def symbol_must_not_be_empty(cls, value: str) -> str:
        if not value:
            raise ValueError("symbol must not be empty")
        return value

    @property
    def identity(self) -> str:
        return self.security_id or self.symbol

    @property
    def display_name(self) -> str:
        return self.short_name or self.symbol


class Universe(DomainModel):
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

    @field_validator("name")
    @classmethod
    def name_must_not_be_empty(cls, value: str) -> str:
        if not value:
            raise ValueError("name must not be empty")
        return value


class UniverseMember(DomainModel):
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

    @field_validator("universe_name")
    @classmethod
    def universe_name_must_not_be_empty(cls, value: str) -> str:
        if not value:
            raise ValueError("universe_name must not be empty")
        return value

