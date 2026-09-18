"""Generate NitroCore application icon (assets/icon.ico)."""

import os

try:
    from PIL import Image, ImageDraw
except ImportError:
    raise SystemExit("Install Pillow first: pip install pillow")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "assets", "icon.ico")
os.makedirs(os.path.dirname(OUT), exist_ok=True)

SIZES = [16, 32, 48, 64, 128, 256]
images = []

for size in SIZES:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Dark rounded-square background
    margin = max(1, size // 16)
    draw.rounded_rectangle(
        [margin, margin, size - margin, size - margin],
        radius=size // 5,
        fill="#202225",
    )

    # Nitro orange lightning bolt
    cx, cy = size // 2, size // 2
    s = size * 0.35
    bolt = [
        (cx + s * 0.15, cy - s * 0.9),
        (cx - s * 0.35, cy + s * 0.05),
        (cx + s * 0.05, cy + s * 0.05),
        (cx - s * 0.15, cy + s * 0.9),
        (cx + s * 0.35, cy - s * 0.05),
        (cx - s * 0.05, cy - s * 0.05),
    ]
    draw.polygon(bolt, fill="#FF6B35")

    images.append(img)

images[0].save(OUT, format="ICO", sizes=[(s, s) for s in SIZES], append_images=images[1:])
print(f"Created {OUT}")
