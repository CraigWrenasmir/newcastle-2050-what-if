"""
Rebuild night-culture-heatmap.png from whatever's currently in dots.json.

Run this after editing dots.json (e.g. via dot_editor.html).
"""
import json, pathlib
from PIL import Image, ImageDraw, ImageFilter

dots = json.loads(pathlib.Path("dots.json").read_text())

img = Image.open("Night Culture.png").convert("RGB")
target_w = 1800
scale = target_w / img.width
target_h = int(img.height * scale)
img = img.resize((target_w, target_h), Image.LANCZOS)

overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
draw = ImageDraw.Draw(overlay, "RGBA")

for d in dots["dots"]:
    cx = d["x"] * target_w
    cy = d["y"] * target_h
    for r, alpha in [(28, 22), (20, 38), (14, 70), (9, 110)]:
        draw.ellipse([cx-r, cy-r, cx+r, cy+r], fill=(255, 220, 80, alpha))
    draw.ellipse([cx-4, cy-4, cx+4, cy+4], fill=(255, 245, 160, 245))

glow = overlay.filter(ImageFilter.GaussianBlur(radius=3))
img = Image.alpha_composite(img.convert("RGBA"), glow).convert("RGB")
img.save("night-culture-heatmap.png", optimize=True, quality=92)

import os
sz = os.path.getsize("night-culture-heatmap.png")
print(f"Rebuilt night-culture-heatmap.png with {dots['count']} dots — {target_w}×{target_h} ({sz/1024:.0f} KB)")
