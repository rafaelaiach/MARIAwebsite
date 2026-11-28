"""Tone down an orange parquet without touching the rest of the photo (whites, walls, lights).

    python tools/calm_wood.py <stem> <saturation kept, e.g. 0.65> [<brightness kept, e.g. 0.92>] [--preview out.jpg]

Only orange pixels (hue 10-45 deg, saturated) are changed, with a soft mask, so there is no visible edge.
Source: originaux/<stem>.jpg as made by enhance_original.py (re-run that first to start again).
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
stem, keep_sat = sys.argv[1], float(sys.argv[2])
keep_val = float(sys.argv[3]) if len(sys.argv) > 3 and not sys.argv[3].startswith("--") else 1.0
preview = sys.argv[sys.argv.index("--preview") + 1] if "--preview" in sys.argv else None
src = ROOT / "originaux" / f"{stem}.jpg"
base = ROOT / "originaux" / "enhanced" / f"{stem}.jpg"   # the enhance_original.py result, kept so it can be redone
base.parent.mkdir(exist_ok=True)
if not base.exists():
    base.write_bytes(src.read_bytes())
hsv = np.asarray(Image.open(base).convert("HSV"), dtype=np.float32)
h = hsv[..., 0] * 360 / 255
s, v = hsv[..., 1] / 255, hsv[..., 2] / 255
# soft mask: orange hues, and only where the colour is strong
hue_w = np.clip(1 - np.abs(h - 27) / 22, 0, 1)
sat_w = np.clip((s - 0.25) / 0.2, 0, 1)
m = hue_w * sat_w
s2 = s * (1 - m * (1 - keep_sat))
v2 = v * (1 - m * (1 - keep_val))
out = np.stack([hsv[..., 0], s2 * 255, v2 * 255], -1).round().clip(0, 255).astype(np.uint8)
img = Image.fromarray(out, "HSV").convert("RGB")
if preview:
    img.save(preview, quality=90)
else:
    img.save(src, quality=95)
print(f"{stem}: orange areas {m.mean():.0%} of the photo, saturation x{keep_sat}, brightness x{keep_val}")
