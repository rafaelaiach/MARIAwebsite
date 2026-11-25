"""Improve one of Maria's original photos (WhatsApp-compressed, dark, orange) while keeping it natural.

    python tools/enhance_original.py <stem>

1. AI cleanup with Real-ESRGAN (removes compression blocks and grain, sharpens edges):
   the photo is halved then enlarged x4, so the result (2x the half) has new clean detail.
   Only the detail comes from the AI; tones come from the photo (same method as upscale.py).
2. Exposure: gentle gamma towards a median brightness of 0.45 (highlights protected).
3. White balance: the orange cast of the warm bulbs is reduced by half.
The untouched file is kept in originaux/raw/. Result: originaux/<stem>.jpg (used by images.py as is).
"""
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parent.parent
ESRGAN = Path(r"C:\Users\rafae\outils\realesrgan\realesrgan-ncnn-vulkan.exe")
sys.path.insert(0, str(ROOT / "tools"))
from upscale import detail_transfer  # noqa: E402

stem = sys.argv[1]
orig = ROOT / "originaux" / f"{stem}.jpg"
raw = ROOT / "originaux" / "raw" / f"{stem}.jpg"
raw.parent.mkdir(exist_ok=True)
if not raw.exists():
    shutil.copy(orig, raw)
src = ImageOps.exif_transpose(Image.open(raw)).convert("RGB")
W, H = src.size
TARGET = (2000, round(2000 * H / W)) if W < H else (round(2000 * W / H), 2000)
if max(TARGET) < max(W, H):
    TARGET = (W, H)

work = ROOT / "work" / "enhance"
work.mkdir(parents=True, exist_ok=True)
half = src.resize((W // 2, H // 2), Image.LANCZOS)
half.save(work / "in.png")
subprocess.run([str(ESRGAN), "-i", str(work / "in.png"), "-o", str(work / "out.png"), "-n", "realesrgan-x4plus",
                "-s", "4", "-t", "128", "-j", "1:1:1"], check=True, capture_output=True, cwd=ESRGAN.parent)
ai = Image.open(work / "out.png").convert("RGB").resize(TARGET, Image.LANCZOS)
classic = src.resize(TARGET, Image.LANCZOS)
img = detail_transfer(classic, ai, strength=0.8)

rgb = np.asarray(img, dtype=np.float32) / 255.0
# white balance: move the average colour half-way towards neutral grey
mean = rgb.reshape(-1, 3).mean(axis=0)
gain = (mean.mean() / mean) ** 0.5
rgb = np.clip(rgb * gain, 0, 1)
# exposure: gentle gamma on luminance, highlights protected, colours kept
lum = 0.2126 * rgb[..., 0] + 0.7152 * rgb[..., 1] + 0.0722 * rgb[..., 2]
med = float(np.median(lum))
gamma = max(0.7, np.log(0.45) / np.log(max(med, 1e-3))) if med < 0.45 else 1.0
new = np.power(np.clip(lum, 1e-6, 1), gamma)
w = np.clip((lum - 0.85) / 0.15, 0, 1)
new = new * (1 - w) + lum * w
rgb = np.clip(rgb * (new / np.clip(lum, 1e-6, 1))[..., None], 0, 1)
out = Image.fromarray((rgb * 255 + .5).astype(np.uint8))
out.save(orig, quality=95)
print(f"{stem}: {W}x{H} -> {out.size[0]}x{out.size[1]}, white balance gains {gain.round(3)}, gamma {gamma:.2f}")
