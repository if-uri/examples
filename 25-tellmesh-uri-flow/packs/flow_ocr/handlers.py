"""Flow stand-in for uriocr: turn an image id into text."""

from __future__ import annotations

from typing import Any

# Deterministic "scanned" content keyed by the image id the kvm step emits.
_FIXTURES = {
    "shot-mon0": "INVOICE  Acme Corp  TOTAL DUE: 42.00 USD  due 2026-07-01",
    "shot-mon1": "MEETING NOTES  ship v2  due 2026-08-15  owner: tom",
}


def extract_text(image_id: str = "", host: str = "host") -> dict[str, Any]:
    text = _FIXTURES.get(image_id, f"<no text recognized for {image_id}>")
    return {"image_id": image_id, "text": text, "chars": len(text)}
