"""Flow stand-in for urikvm: capture a monitor, return an image id."""

from __future__ import annotations

from typing import Any


def capture(monitor: int = 0, host: str = "host") -> dict[str, Any]:
    # A real driver would grab the framebuffer; here we return a deterministic image
    # id that the OCR step downstream knows how to resolve.
    image_id = f"shot-mon{monitor}"
    return {"image_id": image_id, "monitor": monitor, "width": 1920, "height": 1080}
