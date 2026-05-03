"""
Detect yellow glow-sticker dots on the salon-table map photo,
cluster into individual dots, and write their normalised positions
to a JSON file consumable by the insights page.

Approach:
  1. HSV-style colour filter for bright yellow (allows for camera flash variance)
  2. Mask out: TEDx logo (bottom-right), white note papers (left), wood table edges
  3. Connected-component label → dot centroids + areas
  4. Identify 4 corresponding landmarks in photo and clean map
  5. Compute homography (4-point perspective transform) photo → clean-map coords
  6. Output: list of (x, y) in clean-map normalised 0-1 space, plus an annotated debug PNG
"""
import json, pathlib
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.ndimage import label, center_of_mass

ROOT = pathlib.Path(".")
PHOTO = ROOT / "Map Photo.png"
CLEAN = ROOT / "Night Culture.png"

img = np.array(Image.open(PHOTO).convert("RGB"))
H, W = img.shape[:2]
R, G, B = img[..., 0].astype(int), img[..., 1].astype(int), img[..., 2].astype(int)

# ---- Colour filter ----
# Bright yellow: high R, high G, low B, R~G; allow some camera-flash washout
luminance = 0.299*R + 0.587*G + 0.114*B
yellow = (
    (R > 170) & (G > 150) & (B < 160) &
    (np.abs(R - G) < 60) &
    (R > B + 30) &
    (luminance > 150)
)

# ---- Mask out non-map regions ----
mask = np.ones_like(yellow, dtype=bool)
mask[int(H*0.68):, int(W*0.66):] = False   # bottom-right: TEDx logo
mask[int(H*0.55):, :int(W*0.18)] = False   # bottom-left: white notes
mask[:int(H*0.04), :] = False              # top edge: bezel
mask[int(H*0.97):, :] = False              # bottom edge: wood
mask[:, int(W*0.985):] = False             # right edge: wood/table
yellow = yellow & mask

# ---- Connected components ----
labels, n = label(yellow)
print(f"Raw clusters: {n}")

# Filter clusters by size
sizes = np.bincount(labels.ravel())
sizes[0] = 0   # background
keep = np.where((sizes >= 4) & (sizes <= 250))[0]
print(f"Plausible dots: {len(keep)} (sizes {sizes[keep].min()}–{sizes[keep].max()})")

centroids = []
for k in keep:
    cy, cx = center_of_mass(labels == k)
    centroids.append((float(cx), float(cy)))
centroids.sort()

# ---- Save annotated debug image ----
debug = Image.open(PHOTO).convert("RGB").copy()
draw = ImageDraw.Draw(debug)
for cx, cy in centroids:
    r = 8
    draw.ellipse([cx-r, cy-r, cx+r, cy+r], outline=(255, 0, 255), width=2)
debug.save("_crops/dots_detected.png")

# ---- 4-point perspective transform: photo → clean-map ----
# Manually-picked landmarks visible in BOTH images.
# Coordinates are (x, y) in pixels; first list is photo, second is clean map.
# Landmarks (chosen so they're far apart for stability):
#   1. Tip of Newcastle East peninsula (right-side cape jutting into ocean)
#   2. Top-left harbour edge — where the dark land meets water (top of map)
#   3. Where the foreshore curve bottoms out near the harbour pavilion
#   4. Bottom-left of visible streets (residential corner)
#
# Photo coords measured by inspection at 1862×924; clean coords at 7021×4967.
photo_pts = np.array([
    [ 580, 130],    # foreshore edge mid-harbour (where land meets water)
    [1690,  85],    # eastern tip of Newcastle East peninsula
    [1620, 440],    # south coast of NE peninsula meeting ocean
    [ 240, 880],    # bottom-left visible streets (residential)
], dtype=float)

map_pts = np.array([
    [1800,  900],   # foreshore edge in clean map
    [5750,  450],   # NE peninsula east tip in clean map
    [5550, 2900],   # NE peninsula south coast in clean map
    [ 250, 4500],   # bottom-left clean-map streets
], dtype=float)


def homography(src, dst):
    """Compute 3x3 homography matrix mapping src→dst points (4 pairs)."""
    A = []
    for (x, y), (X, Y) in zip(src, dst):
        A.append([-x, -y, -1, 0, 0, 0, x*X, y*X, X])
        A.append([0, 0, 0, -x, -y, -1, x*Y, y*Y, Y])
    A = np.asarray(A)
    _, _, V = np.linalg.svd(A)
    H = V[-1].reshape(3, 3)
    return H / H[2, 2]


def apply_h(H, pts):
    pts = np.asarray(pts)
    n = pts.shape[0]
    homo = np.hstack([pts, np.ones((n, 1))])
    out = homo @ H.T
    return out[:, :2] / out[:, 2:3]


Hmat = homography(photo_pts, map_pts)
mapped = apply_h(Hmat, np.array(centroids))

# Filter dots that fall outside the clean-map bounds
clean_img_full = np.array(Image.open(CLEAN).convert("RGB"))
clean_h, clean_w = clean_img_full.shape[:2]
inside = (mapped[:, 0] >= 50) & (mapped[:, 0] <= clean_w - 50) & \
         (mapped[:, 1] >= 50) & (mapped[:, 1] <= clean_h - 50)
mapped = mapped[inside]
print(f"Dots inside clean-map bounds: {len(mapped)} of {len(centroids)}")

# Filter dots that land on water in the clean map.
# Water signature: dark navy (low R, low G, B between 50-85, B > R, B > G).
# Sample a 21×21 window around each dot; drop if >50% water.
def is_water_pixel(px):
    R, G, B = int(px[0]), int(px[1]), int(px[2])
    return R < 60 and G < 70 and 45 < B < 90 and B > R - 5 and B > G - 5

WIN = 10  # radius
on_land = []
for x, y in mapped:
    xi, yi = int(x), int(y)
    x0, x1 = max(0, xi-WIN), min(clean_w, xi+WIN+1)
    y0, y1 = max(0, yi-WIN), min(clean_h, yi+WIN+1)
    region = clean_img_full[y0:y1, x0:x1]
    R = region[..., 0].astype(int)
    G = region[..., 1].astype(int)
    B = region[..., 2].astype(int)
    water_mask = (R < 60) & (G < 70) & (B > 45) & (B < 90) & (B > R - 5) & (B > G - 5)
    water_frac = water_mask.mean()
    on_land.append(water_frac < 0.5)
mapped_land = mapped[np.array(on_land)]
print(f"Dots on land (after water filter): {len(mapped_land)} of {len(mapped)}")
mapped = mapped_land
clean = np.array([clean_w, clean_h])

# Normalise to 0-1 for portable rendering
norm = mapped / clean

out = {
    "count": int(len(mapped)),
    "photo_dim": [W, H],
    "clean_dim": [int(clean[0]), int(clean[1])],
    "dots": [{"x": round(float(p[0]), 4), "y": round(float(p[1]), 4)} for p in norm],
}
pathlib.Path("dots.json").write_text(json.dumps(out, indent=2))
print(f"Wrote dots.json with {out['count']} dots")

# ---- Save preview: dots overlaid on clean map ----
clean_img = Image.open(CLEAN).convert("RGB")
preview = clean_img.copy()
draw = ImageDraw.Draw(preview, "RGBA")
for p in mapped:
    x, y = float(p[0]), float(p[1])
    # Glow halo
    for r, alpha in [(60, 35), (40, 70), (24, 130)]:
        draw.ellipse([x-r, y-r, x+r, y+r], fill=(255, 230, 60, alpha))
    draw.ellipse([x-12, y-12, x+12, y+12], fill=(255, 230, 60, 220))
preview.thumbnail((2000, 2000))
preview.save("_crops/clean_with_dots.png", optimize=True)
print("Wrote _crops/clean_with_dots.png preview")
