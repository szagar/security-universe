"""Resolver implementations and packaged resolver data."""

from security_universe.resolvers.chain import ResolverChain
from security_universe.resolvers.crypto import (
    CryptoSecurityIdResolver,
    ParsedCryptoSymbol,
    crypto_security_id,
    parse_crypto_symbol,
)
from security_universe.resolvers.equity import (
    EquitySecurityIdResolver,
    equity_security_id,
)
from security_universe.resolvers.future import (
    FutureSecurityIdResolver,
    ParsedFutureSymbol,
    future_active_security_id,
    future_security_id,
    future_short_name,
    parse_future_symbol,
)
from security_universe.resolvers.occ import (
    OCCSecurityIdResolver,
    ParsedOCCSymbol,
    format_strike,
    load_default_option_rules,
    option_security_id,
    option_short_name,
    parse_occ_symbol,
)
from security_universe.resolvers.tastytrade import TastytradeActiveContractLookup

__all__ = [
    # composite
    "ResolverChain",
    # options (OCC)
    "OCCSecurityIdResolver",
    "ParsedOCCSymbol",
    "format_strike",
    "load_default_option_rules",
    "option_security_id",
    "option_short_name",
    "parse_occ_symbol",
    # equities
    "EquitySecurityIdResolver",
    "equity_security_id",
    # futures
    "FutureSecurityIdResolver",
    "ParsedFutureSymbol",
    "TastytradeActiveContractLookup",
    "future_active_security_id",
    "future_security_id",
    "future_short_name",
    "parse_future_symbol",
    # crypto
    "CryptoSecurityIdResolver",
    "ParsedCryptoSymbol",
    "crypto_security_id",
    "parse_crypto_symbol",
]
