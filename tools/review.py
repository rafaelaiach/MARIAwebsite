"""Print each generated page's text and photo count, to check the build."""
import glob
import html
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
for f in sorted(glob.glob("site/projets/*/index.html")) + sorted(glob.glob("site/paysages/*/index.html")):
    s = Path(f).read_text("utf-8")
    m = re.search(r'<div class="prose reveal">(.*?)</div>', s, re.S)
    t = re.sub(r"<[^>]+>", " | ", m.group(1)) if m else ""
    n = len(re.findall(r"data-lb-item", s))
    print("=====", Path(f).parent.name, "photos:", n)
    print(html.unescape(re.sub(r"(\s*\|\s*)+", " | ", t))[:700])
