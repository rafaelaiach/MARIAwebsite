"""Write work/comparaison.html: a before/after slider for every photo sharpened so far.

    python tools/upscale.py finish   (blend the photos the AI has finished)
    python tools/compare_page.py     (then open work/comparaison.html in Chrome)
"""
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
HD = ROOT / "cache_hd"
CACHE = ROOT / "cache"

cards = []
for n, hd in enumerate(sorted(HD.glob("*.jpg")), 1):
    orig = next(CACHE.glob(hd.stem + "*"), None)
    if not orig:
        continue
    o, h = Image.open(orig), Image.open(hd)
    cards.append(f"""
<section class="card">
  <p class="meta">Photo {n} · original {o.width}×{o.height} px → sharpened {h.width}×{h.height} px</p>
  <div class="cmp" style="aspect-ratio:{h.width}/{h.height}">
    <img class="after" src="../cache_hd/{hd.name}" alt="Sharpened">
    <div class="before-wrap"><img class="before" src="../cache/{orig.name}" alt="Original"></div>
    <div class="handle"><span>⟷</span></div>
    <p class="tag l">Before</p><p class="tag r">After</p>
  </div>
</section>""")

page = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Before / after: sharpened photos</title>
<style>
:root {{ --paper:#f3f0ea; --ink:#171614; --muted:#77716a; }}
* {{ box-sizing:border-box; }}
body {{ margin:0; background:var(--paper); color:var(--ink); font:15px/1.5 system-ui, sans-serif; }}
header {{ position:sticky; top:0; z-index:5; background:rgba(243,240,234,.92); backdrop-filter:blur(8px); padding:16px 24px; display:flex; flex-wrap:wrap; gap:12px 24px; align-items:center; border-bottom:1px solid rgba(0,0,0,.1); }}
h1 {{ font:500 22px/1.2 Georgia, serif; margin:0; }}
header p {{ margin:0; color:var(--muted); font-size:13px; }}
button {{ font:inherit; padding:7px 14px; border-radius:999px; border:1px solid var(--ink); background:var(--ink); color:var(--paper); cursor:pointer; }}
main {{ max-width:1200px; margin:0 auto; padding:24px; display:grid; gap:40px; }}
.meta {{ color:var(--muted); font-size:13px; margin:0 0 8px; }}
.cmp {{ position:relative; width:100%; overflow:hidden; background:#ddd; cursor:ew-resize; user-select:none; touch-action:pan-y; }}
.cmp img {{ position:absolute; inset:0; width:100%; height:100%; object-fit:cover; pointer-events:none; }}
.before-wrap {{ position:absolute; inset:0; clip-path:inset(0 50% 0 0); }}
.handle {{ position:absolute; top:0; bottom:0; left:50%; width:2px; background:#fff; box-shadow:0 0 0 1px rgba(0,0,0,.2); transform:translateX(-1px); }}
.handle span {{ position:absolute; top:50%; left:50%; transform:translate(-50%,-50%); width:40px; height:40px; border-radius:50%; background:#fff; display:grid; place-items:center; font-size:18px; box-shadow:0 2px 10px rgba(0,0,0,.25); }}
.tag {{ position:absolute; top:12px; margin:0; padding:3px 10px; border-radius:999px; background:rgba(0,0,0,.55); color:#fff; font-size:12px; letter-spacing:.08em; text-transform:uppercase; }}
.tag.l {{ left:12px; }} .tag.r {{ right:12px; }}
body.zoom .cmp {{ aspect-ratio:auto !important; height:80vh; }}
body.zoom .cmp img {{ width:300%; height:300%; left:-100%; top:-100%; object-fit:cover; }}
</style></head>
<body>
<header>
  <h1>Before / after: sharpened photos</h1>
  <p>{len(cards)} photos processed so far. Drag the slider on each photo.</p>
  <button type="button" id="zoom">Zoom ×3 on the centre</button>
</header>
<main>{''.join(cards)}</main>
<script>
document.querySelectorAll('.cmp').forEach(c => {{
  const wrap = c.querySelector('.before-wrap'), handle = c.querySelector('.handle');
  const set = x => {{ const r = c.getBoundingClientRect(); const p = Math.min(100, Math.max(0, (x - r.left) / r.width * 100));
    wrap.style.clipPath = `inset(0 ${{100 - p}}% 0 0)`; handle.style.left = p + '%'; }};
  let down = false;
  c.addEventListener('pointerdown', e => {{ down = true; c.setPointerCapture(e.pointerId); set(e.clientX); }});
  c.addEventListener('pointermove', e => {{ if (down) set(e.clientX); }});
  c.addEventListener('pointerup', () => down = false);
}});
document.getElementById('zoom').addEventListener('click', e => {{
  const on = document.body.classList.toggle('zoom');
  e.target.textContent = on ? 'Back to full photo' : 'Zoom ×3 on the centre';
}});
</script>
</body></html>"""

out = ROOT / "work" / "comparaison.html"
out.write_text(page, "utf-8")
print(len(cards), "photos in", out)
