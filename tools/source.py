"""Turn what was read from the Wix site (data/raw/) into data/source.json:
one group of photos per page, in the site's order, with their captions."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
site = json.loads((RAW / "site.json").read_text("utf-8"))
ssr = json.loads((RAW / "pages.json").read_text("utf-8"))
common = set(ssr["home"]["images"])

# pages whose photos are in a grid the page data does not list: use the photos found in the page itself
SSR_PAGES = {
    "copie-de-espace-paysager-le-jardin": "paysage-cour",
    "copie-de-l-art": "paysage-jardin-partage",
    "copie-de-espace-paysager-cour-place": "paysage-avenue-du-maine",
    "copie-de-je-me-presente-1": "art",
}

# projects not to show on the site (asked on 2026-11-25)
EXCLUDE = {"copie-de-issy-les-moulineaux-92130-1", "copie-de-rue-de-l-amiral-roussin-6ème"}

groups = []
for key, page in site.items():
    if key.startswith("_") or key in EXCLUDE:
        continue
    items = []
    for gal in page.get("galleries", []):
        for it in gal:
            if it.get("uri"):
                items.append({"uri": it["uri"], "title": it.get("title", ""), "desc": it.get("desc", "")})
    if key in SSR_PAGES:
        for mid in ssr.get(key, {}).get("images", []):
            if mid not in common and all(mid != i["uri"] for i in items):
                items.append({"uri": mid, "title": "", "desc": ""})
    if items:
        groups.append({"key": key, "title": page["title"], "items": items})

(ROOT / "data" / "source.json").write_text(json.dumps({"groups": groups}, ensure_ascii=False, indent=1), "utf-8")
print(sum(len(g["items"]) for g in groups), "items in", len(groups), "groups")
