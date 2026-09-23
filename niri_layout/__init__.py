from pathlib import Path

_PACKAGE_ROOT = Path(__file__).resolve().parent
_SRC_PACKAGE = _PACKAGE_ROOT.parent / "src" / "niri_layout"
__path__ = [str(_PACKAGE_ROOT), str(_SRC_PACKAGE)]

from src.niri_layout import (  # type: ignore
    NiriIPCError,
    NiriIPCJSONError,
    NiriLayoutError,
    __version__,
)

__all__ = [
    "NiriLayoutError",
    "NiriIPCError",
    "NiriIPCJSONError",
    "__version__",
]
