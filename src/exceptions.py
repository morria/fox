"""Custom exceptions for Fox BBS."""


class FoxBBSError(Exception):
    """Base exception for Fox BBS errors."""
    pass


class ConfigurationError(FoxBBSError):
    """Raised when there's a configuration error."""
    pass


class InvalidCallsignError(FoxBBSError):
    """Raised when an invalid callsign is provided."""
    pass


class ConnectionError(FoxBBSError):
    """Raised when there's a connection error."""
    pass


class AGWPEError(FoxBBSError):
    """Raised when there's an AGWPE protocol error."""
    pass
