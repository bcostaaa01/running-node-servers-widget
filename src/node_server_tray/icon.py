"""Draws the tray icon: a plain circle in Node's brand green."""

from __future__ import annotations

from PIL import Image, ImageDraw, ImageFont

SIZE = 64
GREEN = (83, 158, 67, 255)
WHITE = (255, 255, 255, 255)


def render() -> Image.Image:
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse((2, 2, SIZE - 2, SIZE - 2), fill=GREEN)
    draw.text((SIZE / 2, SIZE / 2), "N", fill=WHITE, anchor="mm", font=_font())
    return img


def _font() -> ImageFont.ImageFont:
    try:
        return ImageFont.truetype("arialbd.ttf", 34)
    except OSError:
        return ImageFont.load_default()
