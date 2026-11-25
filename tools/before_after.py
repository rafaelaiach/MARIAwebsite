"""Before/after pairs for the homepage slider, cut out of the side-by-side montages of the site.

For each montage: find the white band between the two photos, cut the two halves,
try to align the 'before' half on the 'after' half (SIFT points + similarity transform,
kept only if it is clearly reliable), then crop both to the same frame.

    python tools/before_after.py      (writes site/img/ba-<key>-before|after-2000.webp and data/before_after.json)
"""
import json
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
IMG = ROOT / "site" / "img"
images = json.loads((ROOT / "data" / "images.json").read_text("utf-8"))
source = json.loads((ROOT / "data" / "source.json").read_text("utf-8"))
GROUPS = {g["key"]: g for g in source["groups"]}

# key, group, item index, project slug, place, caption
PAIRS = [
    ("lacretelle-cuisine", "copie-de-av-de-fontainebleau-94-krem", 5, "paris-15-rue-lacretelle", "Rue Lacretelle, Paris 15e", "La cuisine"),
    ("stalingrad-sejour", "copie-de-rue-cotentin-75015", 6, "colombes-rue-de-stalingrad", "Rue de Stalingrad, Colombes", "Le séjour vu de l'entrée"),
    ("kremlin-sdb", "copie-de-rue-fleurus-75006", 3, "kremlin-bicetre-avenue-de-fontainebleau", "Le Kremlin-Bicêtre", "La salle de bains"),
]


def split(img):
    """Cut a side-by-side montage at the light (or dark) band nearest the middle."""
    h, w = img.shape[:2]
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY).astype(np.float32)
    lo, hi = int(w * .38), int(w * .62)
    cols = gray[:, lo:hi]
    score = cols.std(axis=0) - np.abs(cols.mean(axis=0) - 128) * .02   # a band = almost no variation top to bottom
    x = lo + int(np.argmin(score))
    # widen to the whole band
    band = np.where(gray[:, lo:hi].std(axis=0) < gray[:, x].std() + 6)[0] + lo
    band = band[(band > x - 40) & (band < x + 40)]
    left_end, right_start = (band.min(), band.max() + 1) if len(band) else (x, x + 1)
    return img[:, :left_end], img[:, right_start:]


def align(before, after):
    """Return before moved onto after (or None if no reliable match)."""
    sift = cv2.SIFT_create(5000)
    ka, da = sift.detectAndCompute(cv2.cvtColor(before, cv2.COLOR_BGR2GRAY), None)
    kb, db = sift.detectAndCompute(cv2.cvtColor(after, cv2.COLOR_BGR2GRAY), None)
    if da is None or db is None:
        return None, 0
    good = [m for m, n in cv2.BFMatcher().knnMatch(da, db, k=2) if m.distance < .7 * n.distance]
    if len(good) < 12:
        return None, len(good)
    pa = np.float32([ka[m.queryIdx].pt for m in good])
    pb = np.float32([kb[m.trainIdx].pt for m in good])
    M, inl = cv2.estimateAffinePartial2D(pa, pb, method=cv2.RANSAC, ransacReprojThreshold=5)
    n = int(inl.sum()) if inl is not None else 0
    scale = float(np.hypot(M[0, 0], M[1, 0])) if M is not None else 0
    if M is None or n < 12 or not (.75 < scale < 1.33):
        return None, n
    return M, n


def common_crop(before, after, M):
    h, w = after.shape[:2]
    if M is None:
        # no alignment: same size, centred
        bh, bw = before.shape[:2]
        H, W = min(h, bh), min(w, bw)
        cb = before[(bh - H) // 2:(bh - H) // 2 + H, (bw - W) // 2:(bw - W) // 2 + W]
        ca = after[(h - H) // 2:(h - H) // 2 + H, (w - W) // 2:(w - W) // 2 + W]
        return cb, ca
    moved = cv2.warpAffine(before, M, (w, h), flags=cv2.INTER_LANCZOS4)
    mask = cv2.warpAffine(np.full(before.shape[:2], 255, np.uint8), M, (w, h), flags=cv2.INTER_NEAREST)
    ys, xs = np.where(mask == 255)
    x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
    while mask[y0:y1 + 1, x0:x1 + 1].min() < 255:
        x0, x1, y0, y1 = x0 + 2, x1 - 2, y0 + 2, y1 - 2
    return moved[y0:y1 + 1, x0:x1 + 1], after[y0:y1 + 1, x0:x1 + 1]


# Reference points placed by hand on what did not move (in the full left/right halves):
# window corners, bathtub corners, ceiling corner. Used when automatic matching fails.
MANUAL = {
    "lacretelle-cuisine": ([(500, 458), (585, 640)], [(509, 513), (588, 699)]),
    "stalingrad-sejour": ([(434, 493), (627, 493), (439, 643)], [(276, 457), (586, 452), (293, 590)]),
    "kremlin-sdb": ([(477, 906), (975, 1062), (462, 395)], [(407, 926), (918, 1111), (400, 506)]),
}

out = []
for key, group, idx, slug, place, caption in PAIRS:
    it = GROUPS[group]["items"][idx]
    f = IMG / f"{images[it['uri']]['file']}-2000.webp"
    img = cv2.imread(str(f))
    b, a = split(img)
    M, n = align(b, a)
    if M is None and key in MANUAL:
        pb, pa = (np.float32(x) for x in MANUAL[key])
        M, _ = cv2.estimateAffinePartial2D(pb, pa, method=cv2.LMEDS)
        n = len(pb)
    cb, ca = common_crop(b, a, M)
    cv2.imwrite(str(IMG / f"ba-{key}-before-2000.webp"), cb, [cv2.IMWRITE_WEBP_QUALITY, 88])
    cv2.imwrite(str(IMG / f"ba-{key}-after-2000.webp"), ca, [cv2.IMWRITE_WEBP_QUALITY, 88])
    out.append({"key": key, "slug": slug, "place": place, "caption": caption, "w": int(ca.shape[1]), "h": int(ca.shape[0]),
                "aligned": M is not None})
    print(f"{key}: halves {b.shape[1]}+{a.shape[1]} px, {'aligned' if M is not None else 'not aligned'} ({n} points), frame {ca.shape[1]}x{ca.shape[0]}")
(ROOT / "data" / "before_after.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), "utf-8")
