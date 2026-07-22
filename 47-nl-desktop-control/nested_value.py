"""Helpers for reading values from nested node response envelopes."""

from __future__ import annotations

from typing import Any


def find_value(value: Any, key: str) -> Any:
    """Return the first non-null value for ``key`` in nested dicts and lists."""
    if isinstance(value, dict):
        if key in value and value[key] is not None:
            return value[key]
        for child in value.values():
            found = find_value(child, key)
            if found is not None:
                return found
    if isinstance(value, list):
        for child in value:
            found = find_value(child, key)
            if found is not None:
                return found
    return None
