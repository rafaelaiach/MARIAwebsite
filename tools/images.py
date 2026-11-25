"""Download the photos of the old Wix site and prepare them for the new one.

- Each photo is fetched once from Wix (at most 2400 px), then saved as WebP
  in two widths (1000 and 2000 px) in site/img/.
- Photos that are clearly too dark get a gentle, natural lift: a gamma curve
  that brightens the mid-tones and shadows, a soft shoulder that keeps the
  highlights (windows, white walls) from burning, and no change of colour.
  Plans and drawings are never touched.

Usage:  python tools/images.py            (reads data/source.json, writes data/images.json)
"""
import io
import json
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "site" / "img"
CACHE = ROOT / "cache"
OUT.mkdir(parents=True, exist_ok=True)
CACHE.mkdir(exist_ok=True)
UA = {"User-Agent": "Mozilla/5.0"}

TARGET_MEDIAN = 0.50   # median luminance aimed for (0..1)
DARK_BELOW = 0.42      # only photos darker than this are lifted
MAX_LIFT = 0.62        # strongest gamma allowed (1 = no change)


def fetch(media_id):
    cached = CACHE / media_id
    if cached.exists():
        return cached.read_bytes()
    ext = media_id.rsplit(".", 1)[-1]
    url = f"https://static.wixstatic.com/media/{media_id}/v1/fit/w_2400,h_2400,q_92/photo.{ext}"
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
        data = r.read()
    cached.write_bytes(data)
    return data


def is_drawing(rgb):
    """Plans and drawings: mostly near-white and almost no colour."""
    small = rgb[::8, ::8]
    lum = small.mean(axis=2)
    sat = small.max(axis=2) - small.min(axis=2)
    return (lum > 0.88).mean() > 0.55 and (sat < 0.08).mean() > 0.85


def lift(rgb):
    """Brighten a dark photo while keeping it natural. Returns (image, gamma)."""
    lum = 0.2126 * rgb[..., 0] + 0.7152 * rgb[..., 1] + 0.0722 * rgb[..., 2]
    med = float(np.median(lum))
    if med >= DARK_BELOW or med <= 0.02:
        return rgb, 1.0
    gamma = max(MAX_LIFT, np.log(TARGET_MEDIAN) / np.log(med))
    # Apply the curve to luminance, then scale the colour channels by the same
    # ratio: hues and white balance stay exactly as they were.
    new_lum = np.power(np.clip(lum, 1e-6, 1), gamma)
    # soft shoulder: above 0.85 the lift fades out so highlights keep detail
    w = np.clip((lum - 0.85) / 0.15, 0, 1)
    new_lum = new_lum * (1 - w) + lum * w
    ratio = (new_lum / np.clip(lum, 1e-6, 1))[..., None]
    out = np.clip(rgb * ratio, 0, 1)
    # keep a true black point and a touch of contrast so it does not look washed out
    lo = np.percentile(out, 0.5)
    out = np.clip((out - lo) / (1 - lo), 0, 1)
    return out, float(gamma)


def process(media_id):
    try:
        # a sharper version made by tools/upscale.py (Real-ESRGAN) wins over the Wix photo
        # priority: the original photo sent by Maria (originaux/), then the AI-sharpened one (cache_hd/), then Wix
        stem = media_id.split("~")[0]
        original = ROOT / "originaux" / (stem + ".jpg")
        hd = ROOT / "cache_hd" / (stem + ".jpg")
        img = Image.open(original if original.exists() else hd) if (original.exists() or hd.exists()) else Image.open(io.BytesIO(fetch(media_id)))
        img = ImageOps.exif_transpose(img).convert("RGB")
    except Exception as e:  # noqa: BLE001
        return media_id, {"error": str(e)}
    rgb = np.asarray(img, dtype=np.float32) / 255.0
    lum = 0.2126 * rgb[..., 0] + 0.7152 * rgb[..., 1] + 0.0722 * rgb[..., 2]
    before = float(np.median(lum))
    drawing = is_drawing(rgb)
    gamma = 1.0
    if not drawing:
        rgb, gamma = lift(rgb)
        img = Image.fromarray((rgb * 255 + 0.5).astype(np.uint8))
    stem = media_id.split("~")[0]
    for width in (1000, 2000):
        im = img if img.width <= width else img.resize((width, round(img.height * width / img.width)), Image.LANCZOS)
        im.save(OUT / f"{stem}-{width}.webp", "WEBP", quality=84, method=6)
    tiny = img.resize((24, max(1, round(img.height * 24 / img.width))), Image.LANCZOS)
    buf = io.BytesIO()
    tiny.save(buf, "WEBP", quality=40)
    import base64
    return media_id, {
        "file": stem, "w": img.width, "h": img.height, "drawing": bool(drawing),
        "median_before": round(before, 3), "gamma": round(gamma, 3),
        "lqip": "data:image/webp;base64," + base64.b64encode(buf.getvalue()).decode(),
    }


def main():
    source = json.loads((ROOT / "data" / "source.json").read_text("utf-8"))
    ids = []
    for group in source["groups"]:
        for it in group["items"]:
            if it["uri"] not in ids:
                ids.append(it["uri"])
    print(len(ids), "photos", file=sys.stderr)
    result = {}
    with ThreadPoolExecutor(8) as pool:
        for n, (mid, info) in enumerate(pool.map(process, ids), 1):
            result[mid] = info
            if n % 25 == 0:
                print(n, file=sys.stderr)
    (ROOT / "data" / "images.json").write_text(json.dumps(result, ensure_ascii=False, indent=1), "utf-8")
    lifted = [k for k, v in result.items() if v.get("gamma", 1) < 1]
    errors = [k for k, v in result.items() if "error" in v]
    print(f"done: {len(result)} photos, {len(lifted)} brightened, {len(errors)} errors", file=sys.stderr)


if __name__ == "__main__":
    main()
