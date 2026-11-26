"""Generate the Costa Leona logo (SVG) and the PNG icons LibreChat expects.
Design: a gold sun-mane (the lioness) around a sea-teal disc with two waves."""
import math
from pathlib import Path

from PIL import Image, ImageDraw

OUT = Path(__file__).parent
TEAL, DEEP, GOLD, SAND, CORAL = "#0B4F6C", "#073B52", "#E0A630", "#FBF3E0", "#E4572E"


def petal_points(cx, cy, r_in, r_out, ang, half):
    a1, a2 = math.radians(ang - half), math.radians(ang + half)
    am = math.radians(ang)
    return [(cx + r_in * math.cos(a1), cy + r_in * math.sin(a1)),
            (cx + r_out * math.cos(am), cy + r_out * math.sin(am)),
            (cx + r_in * math.cos(a2), cy + r_in * math.sin(a2))]


def svg() -> str:
    c, parts = 256, []
    parts.append(f'<svg width="512" height="512" viewBox="0 0 512 512" xmlns="http://www.w3.org/2000/svg">')
    parts.append(f'<title>Costa Leona Resort</title><circle cx="{c}" cy="{c}" r="248" fill="{DEEP}"/>')
    for i in range(16):
        pts = petal_points(c, c, 150, 236, i * 22.5, 9.5)
        parts.append('<polygon points="' + " ".join(f"{x:.1f},{y:.1f}" for x, y in pts) + f'" fill="{GOLD}"/>')
    parts.append(f'<circle cx="{c}" cy="{c}" r="152" fill="{GOLD}"/><circle cx="{c}" cy="{c}" r="138" fill="{TEAL}"/>')
    parts.append(f'<circle cx="{c}" cy="196" r="34" fill="{GOLD}"/>')
    parts.append(f'<path d="M150 262 q26 -24 53 0 t53 0 t53 0 t53 0" fill="none" stroke="{SAND}" stroke-width="14" stroke-linecap="round"/>')
    parts.append(f'<path d="M150 310 q26 -24 53 0 t53 0 t53 0 t53 0" fill="none" stroke="{SAND}" stroke-width="14" stroke-linecap="round" opacity="0.75"/>')
    parts.append("</svg>")
    return "\n".join(parts)


def png(size: int, maskable: bool = False) -> Image.Image:
    s = 4  # supersample
    n = size * s
    img = Image.new("RGBA", (n, n), (0, 0, 0, 0) if not maskable else TEAL)
    d = ImageDraw.Draw(img)
    scale = n / 512 * (0.78 if maskable else 1)
    off = (n - 512 * scale) / 2

    def P(x, y):
        return (off + x * scale, off + y * scale)

    def circ(cx, cy, r, fill):
        d.ellipse([P(cx - r, cy - r), P(cx + r, cy + r)], fill=fill)

    circ(256, 256, 248, DEEP)
    for i in range(16):
        d.polygon([P(x, y) for x, y in petal_points(256, 256, 150, 236, i * 22.5, 9.5)], fill=GOLD)
    circ(256, 256, 152, GOLD)
    circ(256, 256, 138, TEAL)
    circ(256, 196, 34, GOLD)
    for y0, col in ((262, SAND), (310, "#C9D6D6")):
        pts = []
        for k in range(0, 213):
            x = 150 + k
            pts.append(P(x, y0 - 12 * math.sin(k / 53 * math.pi)))
        d.line(pts, fill=col, width=int(14 * scale), joint="curve")
    return img.resize((size, size), Image.LANCZOS)


if __name__ == "__main__":
    (OUT / "logo.svg").write_text(svg(), encoding="utf-8")
    for name, size, mask in [("favicon-16x16.png", 16, False), ("favicon-32x32.png", 32, False),
                             ("apple-touch-icon-180x180.png", 180, False), ("icon-192x192.png", 192, False),
                             ("maskable-icon.png", 512, True)]:
        png(size, mask).save(OUT / name)
    png(512).save(OUT / "logo-512.png")
    print("logo files written to", OUT)
