#!/usr/bin/env python3
"""Build Pulse macOS assets while preserving the approved source artwork."""

from __future__ import annotations

from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
IMAGE_DIR = ROOT / "app" / "static" / "images"
CANVAS = 1024


def build_master(source_path: Path) -> Image.Image:
    """Remove only border-connected near-white pixels; inner white marks stay intact."""
    source = Image.open(source_path).convert("RGBA")
    pixels = source.load()
    width, height = source.size
    pending = [(x, 0) for x in range(width)] + [(x, height - 1) for x in range(width)]
    pending += [(0, y) for y in range(1, height - 1)] + [(width - 1, y) for y in range(1, height - 1)]
    visited: set[tuple[int, int]] = set()
    while pending:
        x, y = pending.pop()
        if (x, y) in visited:
            continue
        visited.add((x, y))
        red, green, blue, _ = pixels[x, y]
        # The approved raster has a lightly antialiased white canvas around the
        # navy tile. A generous cutoff removes that connected halo without
        # reaching the isolated white bars inside the tile.
        if min(red, green, blue) < 180:
            continue
        pixels[x, y] = (red, green, blue, 0)
        if x:
            pending.append((x - 1, y))
        if x + 1 < width:
            pending.append((x + 1, y))
        if y:
            pending.append((x, y - 1))
        if y + 1 < height:
            pending.append((x, y + 1))
    return source.resize((CANVAS, CANVAS), Image.Resampling.LANCZOS)


def main() -> None:
    source_path = IMAGE_DIR / "pulse-logo-source.png"
    if not source_path.exists():
        raise SystemExit(f"Missing approved source artwork: {source_path}")
    master = build_master(source_path)
    png_path = IMAGE_DIR / "pulse-logo.png"
    master.save(png_path, optimize=True)

    master.save(
        IMAGE_DIR / "pulse-logo.icns",
        format="ICNS",
        sizes=[(16, 16), (32, 32), (64, 64), (128, 128), (256, 256), (512, 512), (1024, 1024)],
    )


if __name__ == "__main__":
    main()
