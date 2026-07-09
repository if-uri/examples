"""Root conftest for if-uri/examples.

importlib mode prevents same-basename test file collisions. Each example dir
also needs its directory on sys.path so local helper modules (run, flow,
transport_lib ...) are importable. Problem: sys.modules caches 'run' from
example A and returns it to example B. Fix: evict example-local module entries
before entering a new example directory during collection.
"""
from __future__ import annotations

import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_URIRUN_PKG = _HERE.parent / "urirun" / "adapters" / "python"


def _ensure_urirun_package() -> None:
    """Keep the real urirun package ahead of the PEP-420 namespace shell at repo ``urirun/``."""
    if not _URIRUN_PKG.is_dir():
        return
    pkg = str(_URIRUN_PKG)
    if pkg not in sys.path:
        sys.path.insert(1, pkg)
    mod = sys.modules.get("urirun")
    if mod is not None and getattr(mod, "__file__", None) is None:
        for name in [n for n in list(sys.modules) if n == "urirun" or n.startswith("urirun.")]:
            del sys.modules[name]


def _example_key(p: Path) -> str:
    try:
        parts = p.relative_to(_HERE).parts
        # _site/* subdirs need a two-part key; otherwise all _site/ examples share one key
        # and modules from _site/19-all-connectors contaminate _site/20-runtime-transport-matrix.
        if parts[0] == "_site" and len(parts) > 1:
            return f"_site/{parts[1]}"
        return parts[0]
    except (ValueError, IndexError):
        return ""


_state: dict = {"cur_example": "", "modules_before": set(sys.modules)}


def pytest_collect_file(parent, file_path: Path):
    if file_path.suffix != ".py":
        return None

    dir_str = str(file_path.parent)
    ex_key = _example_key(file_path)

    if ex_key and ex_key != _state["cur_example"]:
        # Leaving previous example: evict any module that was freshly imported
        # from files inside _HERE (local helper modules, not installed packages).
        new_mods = set(sys.modules) - _state["modules_before"]
        for name in list(new_mods):
            mod = sys.modules.get(name)
            f = getattr(mod, "__file__", None) or ""
            if f and str(_HERE) in f:
                del sys.modules[name]
        # Record stable baseline (installed packages, stdlib) for next eviction pass
        _state["modules_before"] = set(sys.modules)
        _state["cur_example"] = ex_key

    # Put this example's dir at the FRONT so local imports resolve here first.
    if dir_str in sys.path:
        sys.path.remove(dir_str)
    sys.path.insert(0, dir_str)
    _ensure_urirun_package()

    return None
