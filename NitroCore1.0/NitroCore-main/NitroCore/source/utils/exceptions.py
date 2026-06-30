"""Custom exception classifications for NitroCore execution modules."""

class NitroCoreError(Exception):
    """Base application exception handler."""
    pass

class RegistryAccessDenied(NitroCoreError):
    """Raised when operating without elevated administrative privileges."""
    pass

class ServiceControlFailure(NitroCoreError):
    """Raised when the Windows Service Control Manager blocks an interaction request."""
    pass

class DiskCleanupLocked(NitroCoreError):
    """Raised when standard system cleanmgr handles are already open elsewhere."""
    pass
