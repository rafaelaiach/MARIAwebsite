"""Whole-page phone screenshot (390 px wide, like an iPhone) with headless Chrome.

    python tools/phone_shots.py / home          -> work/shots/home-full.png and home-sheet.jpg (cut in columns)
    python tools/phone_shots.py /projets/x/ x

The local server must run on 127.0.0.1:8090. The page is rendered in one very tall window;
the heights that depend on the screen height (slideshow, project top) are fixed to what
they would be on a 390 x 844 phone, and the appear-on-scroll animations are switched off.
"""
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
SITE, SHOTS = ROOT / "site", ROOT / "work" / "shots"
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
W, PHONE_H, TALL = 390, 844, 16000

path, name = sys.argv[1], sys.argv[2]
SHOTS.mkdir(parents=True, exist_ok=True)
src = (SITE / path.strip("/") / "index.html") if path.endswith("/") else SITE / path.strip("/")
inner = SITE / "_shot_inner.html"
page = SITE / "_shot.html"
# headless Chrome cannot make a window narrower than ~500 px: the page is laid out in a 390 px frame instead
page.write_text(f"""<!doctype html><style>body{{{{margin:0}}}}iframe{{{{border:0;width:{W}px;height:{TALL}px;display:block}}}}</style>
<iframe src="/_shot_inner.html?t={time.time():.0f}"></iframe>""".replace("{{","{").replace("}}","}"), "utf-8")
inner.write_text(src.read_text("utf-8").replace("</body>", f"""<style>
*,*::before,*::after{{transition:none!important;animation:none!important}}
.js .reveal{{opacity:1!important;transform:none!important}}
.hero{{height:{int(PHONE_H * .82)}px!important;min-height:0!important}}
.p-hero{{height:{int(PHONE_H * .86)}px!important;min-height:0!important}}
.top{{position:absolute!important}}
</style>
<script>document.querySelectorAll('img').forEach(i=>i.loading='eager');</script></body>"""), "utf-8")
out = SHOTS / f"{name}-full.png"
subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", f"--window-size=520,{TALL}",
                "--virtual-time-budget=10000", f"--user-data-dir={ROOT / 'work' / 'chrome-shots'}",
                f"--screenshot={out}", f"http://127.0.0.1:8090/_shot.html?t={time.time():.0f}"],
               capture_output=True, timeout=120)
page.unlink(missing_ok=True)
inner.unlink(missing_ok=True)

img = Image.open(out).convert("RGB")
a = np.asarray(img).astype(int)
# crop the empty bottom (same colour as the last row of the page background)
rows = np.where(np.abs(a - a[-1, 0]).sum(axis=(1, 2)) > 0)[0]
img = img.crop((0, 0, W, int(rows.max()) + 1 if len(rows) else img.height))
img.save(out)
# sheet: the page cut in columns of two phone screens, side by side
col_h = PHONE_H * 2
cols = (img.height + col_h - 1) // col_h
sheet = Image.new("RGB", (cols * (W + 12), col_h), (120, 120, 120))
for i in range(cols):
    sheet.paste(img.crop((0, i * col_h, W, min(img.height, (i + 1) * col_h))), (i * (W + 12), 0))
sheet.save(SHOTS / f"{name}-sheet.jpg", quality=82)
print(f"page height {img.height}px, {cols} columns -> {SHOTS / (name + '-sheet.jpg')}")
