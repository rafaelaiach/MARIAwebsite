"""Measure how sharp and how big each photo of the site is.

Sharpness = variance of the Laplacian on a 1000 px wide grey version
(the usual blur measure: low value = soft or blurry photo).
Writes data/sharpness.json and prints a summary.
"""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
images = json.loads((ROOT / "data" / "images.json").read_text("utf-8"))


def laplacian_var(path):
    im = Image.open(path).convert("L")
    if im.width > 1000:
        im = im.resize((1000, round(im.height * 1000 / im.width)), Image.LANCZOS)
    a = np.asarray(im, dtype=np.float32)
    lap = -4 * a[1:-1, 1:-1] + a[:-2, 1:-1] + a[2:, 1:-1] + a[1:-1, :-2] + a[1:-1, 2:]
    return float(lap.var())


out = {}
for mid, info in images.items():
    if "file" not in info:
        continue
    src = ROOT / "cache" / mid
    out[mid] = {"file": info["file"], "w": info["w"], "h": info["h"], "drawing": info["drawing"],
                "sharp": round(laplacian_var(src), 1)}
(ROOT / "data" / "sharpness.json").write_text(json.dumps(out, indent=1), "utf-8")

photos = [v for v in out.values() if not v["drawing"]]
small = [v for v in photos if max(v["w"], v["h"]) < 1600]
soft = [v for v in photos if v["sharp"] < 60]
print(f"{len(photos)} photos (plans excluded)", file=sys.stderr)
print(f"  long side under 1600 px: {len(small)}", file=sys.stderr)
print(f"  soft (sharpness < 60):   {len(soft)}", file=sys.stderr)
print(f"  both:                    {len([v for v in small if v in soft])}", file=sys.stderr)
print("  sizes:", sorted({max(v['w'], v['h']) for v in photos})[:12], "...", file=sys.stderr)
