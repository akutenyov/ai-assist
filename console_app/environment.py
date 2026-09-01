"""Machine-specific Python and console compatibility safeguards."""

from __future__ import annotations

import sys
from pathlib import Path


def configure_runtime() -> None:
    """Prevent foreign dependency paths and unsafe console encoding failures.

    Some PyCharm/Codex configurations inject a different project's
    ``_codex_pydeps`` directory into ``sys.path``. It can override the virtual
    environment's ``pydantic`` before the Groq SDK imports it. The application
    only removes that explicitly named external helper path.
    """
    sys.path[:] = [
        entry for entry in sys.path if Path(entry).name.lower() != "_codex_pydeps"
    ]

    # Legacy Windows terminals can use CP1251. Replacing unsupported glyphs
    # avoids a fatal UnicodeEncodeError while retaining Ukrainian text.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(errors="replace")
