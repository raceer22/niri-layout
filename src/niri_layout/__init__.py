"""niri-layout package."""

__version__ = "0.1.0"


class NiriLayoutError(RuntimeError):
    """Base error for niri-layout."""


class NiriIPCError(NiriLayoutError):
    """Raised when niri IPC execution fails."""


class NiriIPCJSONError(NiriLayoutError):
    """Raised when niri IPC returns invalid JSON."""
