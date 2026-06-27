"""Package exception hierarchy."""


class SecurityUniversesError(Exception):
    """Base exception for security-universes errors."""


class ValidationError(SecurityUniversesError):
    """Raised when domain validation fails."""


class UniverseNotFoundError(SecurityUniversesError):
    """Raised when a universe cannot be found."""


class DuplicateUniverseError(SecurityUniversesError):
    """Raised when a universe already exists."""


class DuplicateMemberError(SecurityUniversesError):
    """Raised when a security is already a universe member."""

