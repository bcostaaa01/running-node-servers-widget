"""Renders the dashboard card background: a rounded rect filled with a
soft top-to-bottom gradient. Built as a PIL image (rather than a flat
Tk canvas shape) so the fill can blend smoothly between two colors, then
handed to the canvas as one PhotoImage.

The corner mask is drawn hard-edged (no anti-aliasing) on purpose: the
window uses Tk's ``-transparentcolor`` color-keying to punch a
window-shaped hole for the rounded corners, which only works for pixels
that are an *exact* match to the magic color. An anti-aliased edge would
blend the card color into that magic color at the boundary, producing
pixels that are neither fully transparent nor fully opaque -- a faint
halo of the magic color around the card.
"""

from __future__ import annotations

from PIL import Image, ImageDraw, ImageOps


def render_card(width: int, height: int, radius: int, *, top: str, bottom: str, border: str, border_width: int = 1) -> Image.Image:
    """A ``width``x``height`` rounded rect, gradient-filled from ``top`` to
    ``bottom`` and stroked with ``border``, with fully transparent corners."""

    gradient = ImageOps.colorize(Image.linear_gradient("L").resize((width, height)), black=top, white=bottom).convert("RGB")

    mask = Image.new("L", (width, height), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, width - 1, height - 1), radius=radius, fill=255)

    card = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    card.paste(gradient, (0, 0), mask)
    ImageDraw.Draw(card).rounded_rectangle((0, 0, width - 1, height - 1), radius=radius, outline=border, width=max(1, border_width))

    return card


def _hex_to_rgb(color: str) -> tuple[int, int, int]:
    color = color.lstrip("#")
    return tuple(int(color[i : i + 2], 16) for i in (0, 2, 4))


def tone_between(top: str, bottom: str, t: float) -> str:
    """The gradient's own color at vertical fraction ``t`` (0 = top, 1 =
    bottom), as a hex string -- used to give hover pills and row highlights
    an idle fill that blends invisibly into the card instead of sitting on
    top of it as a flat, mismatched patch."""

    t = max(0.0, min(1.0, t))
    r1, g1, b1 = _hex_to_rgb(top)
    r2, g2, b2 = _hex_to_rgb(bottom)
    return f"#{round(r1 + (r2 - r1) * t):02x}{round(g1 + (g2 - g1) * t):02x}{round(b1 + (b2 - b1) * t):02x}"
