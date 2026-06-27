"""Package exception hierarchy."""


class SecurityUniverseError(Exception):
    """Base exception for security-universe errors."""


class ValidationError(SecurityUniverseError):
    """Raised when domain validation fails."""


class UniverseNotFoundError(SecurityUniverseError):
    """Raised when a universe cannot be found."""


class DuplicateUniverseError(SecurityUniverseError):
    """Raised when a universe already exists."""


class DuplicateMemberError(SecurityUniverseError):
    """Raised when a security is already a universe member."""

