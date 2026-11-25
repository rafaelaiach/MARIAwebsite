"""Make the small photos of the site sharp with Real-ESRGAN (AI upscaling, on this computer).

Step 1  python tools/upscale.py prepare   copies the photos to enlarge into work/esr_in/, covers first
Step 2  (Real-ESRGAN, run separately)     work/esr_in -> work/esr_out (x4)
Step 3  python tools/upscale.py finish    blends AI 70% + classic resize 30% (keeps the natural
                                          texture of wood and walls), saves cache_hd/<id>.jpg
Then    python tools/images.py && python tools/build.py   (uses cache_hd/ when it exists)
"""
import json
import shutil
import sys
from pathlib import Path

from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parent.parent
IN, OUT, HD = ROOT / "work" / "esr_in", ROOT / "work" / "esr_out", ROOT / "cache_hd"
LONG_SIDE_UNDER = 1600   # photos smaller than this get enlarged
TARGET = 2400            # long side after enlargement (never more than x4)
AI_SHARE = 0.7


def todo():
    sharp = json.loads((ROOT / "data" / "sharpness.json").read_text("utf-8"))
    src = (ROOT / "tools" / "build.py").read_text("utf-8")
    ids = [k for k, v in sharp.items() if not v["drawing"] and max(v["w"], v["h"]) < LONG_SIDE_UNDER]
    # photos named in build.py (covers, hero) are not known by id there; put landscape photos first,
    # they are the ones shown widest, then the rest
    ids.sort(key=lambda k: (sharp[k]["w"] < sharp[k]["h"], -sharp[k]["w"]))
    return ids


def prepare():
    IN.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    n = 0
    for i, mid in enumerate(todo()):
        stem = mid.split("~")[0]
        if (HD / f"{stem}.jpg").exists():
            continue
        im = ImageOps.exif_transpose(Image.open(ROOT / "cache" / mid)).convert("RGB")
        im.save(IN / f"{i:03d}_{stem}.png")
        n += 1
    print(n, "photos ready in", IN)


def detail_transfer(classic, ai, radius=3, strength=AI_SHARE):
    """Only the fine detail comes from the AI; colours and light stay those of the real photo.

    The AI tends to shift colours (warmer, more contrast) and to invent patterns. So:
    - colour (Cb, Cr) is taken from the classic enlargement of the original, untouched;
    - brightness = the original's broad tones + the AI's fine edges (what blur removes), at 70 %.
    """
    import numpy as np
    from PIL import ImageFilter
    cy, ccb, ccr = classic.convert("YCbCr").split()
    ay = ai.convert("YCbCr").split()[0]
    c = np.asarray(cy, dtype=np.float32)
    a = np.asarray(ay, dtype=np.float32)
    c_low = np.asarray(cy.filter(ImageFilter.GaussianBlur(radius)), dtype=np.float32)
    a_low = np.asarray(ay.filter(ImageFilter.GaussianBlur(radius)), dtype=np.float32)
    detail = (a - a_low) * strength + (c - c_low) * (1 - strength)
    y = np.clip(c_low + detail, 0, 255).astype(np.uint8)
    return Image.merge("YCbCr", (Image.fromarray(y), ccb, ccr)).convert("RGB")


def finish():
    HD.mkdir(exist_ok=True)
    done = 0
    for out in sorted(OUT.glob("*.png")):
        stem = out.stem.split("_", 1)[1]
        src = Image.open(IN / out.name).convert("RGB")
        ai = Image.open(out).convert("RGB")
        scale = min(4, TARGET / max(src.size))
        size = (round(src.width * scale), round(src.height * scale))
        ai = ai.resize(size, Image.LANCZOS)
        classic = src.resize(size, Image.LANCZOS)
        detail_transfer(classic, ai).save(HD / f"{stem}.jpg", quality=95)
        done += 1
    print(done, "photos saved in", HD)


if __name__ == "__main__":
    {"prepare": prepare, "finish": finish}[sys.argv[1]]()
