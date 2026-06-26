"""Root conftest: add every example directory to sys.path at startup.

Ensures local helper modules (transport_lib, flow, etc.) are importable
whether --import-mode=importlib or default prepend mode is active.
"""
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent

# Pre-add every first-level example directory so local imports work in all tests.
for _d in sorted(_HERE.iterdir()):
    if _d.is_dir() and not _d.name.startswith(".") and _d.name != "_site":
        _s = str(_d)
        if _s not in sys.path:
            sys.path.insert(0, _s)
