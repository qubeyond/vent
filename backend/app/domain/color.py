import colorsys
import re

_HEX_RE = re.compile(r"^#[0-9a-fA-F]{6}$")


def is_valid_hex(color: str | None) -> bool:
    return bool(color) and bool(_HEX_RE.match(color))


def fallback_color(seed: str) -> str:
    digest = sum((i + 1) * ord(ch) for i, ch in enumerate(seed))
    hue = (digest % 360) / 360
    r, g, b = colorsys.hls_to_rgb(hue, 0.55, 0.55)
    return f"#{int(r * 255):02x}{int(g * 255):02x}{int(b * 255):02x}"
