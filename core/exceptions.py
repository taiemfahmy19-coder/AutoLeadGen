"""AutoLeadGen v2 - Custom Application Exceptions."""


class AutoLeadGenError(Exception):
    """Base exception for all AutoLeadGen operations."""
    pass


class DatabaseError(AutoLeadGenError):
    """Raised when an error occurs during SQLite operations."""
    pass


class ValidationError(AutoLeadGenError):
    """Raised when data validation fails."""
    pass


class OutreachBlockedError(AutoLeadGenError):
    """Raised when attempting outreach to a DO_NOT_CONTACT or blocked lead."""
    pass


class WhatsAppSessionError(AutoLeadGenError):
    """Raised when WhatsApp Web session is expired, disconnected, or invalid."""
    pass
