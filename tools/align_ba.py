"""Align the before/after photos of rue de Heyrault on the back wall, then crop both to the same frame.

The two photos were not taken from the same spot and the walls changed, so automatic
matching fails. Reference points were placed by hand on what did not move: the window
corners on both sides of the mullion, the top of the radiator, the floor line at the back.
A similarity transform (scale, rotation, shift: no distortion) is fitted to them, the
'before' photo is moved onto the 'after' one, and both are cropped to their common area.

    python tools/align_ba.py      (after tools/build.py has written ba-before/after-2000.webp)
"""
from pathlib import Path

import cv2
import numpy as np

IMG = Path(__file__).resolve().parent.parent / "site" / "img"
OFF = np.float32([300, 200])  # the points below were read on crops starting at (300, 200)
BEFORE = np.float32([[405, 240], [405, 400], [520, 240], [520, 400], [330, 402], [520, 512]]) + OFF
AFTER = np.float32([[520, 303], [520, 460], [615, 305], [615, 460], [497, 462], [615, 560]]) + OFF

before = cv2.imread(str(IMG / "ba-before-2000.webp"))
after = cv2.imread(str(IMG / "ba-after-2000.webp"))
h, w = after.shape[:2]

M, _ = cv2.estimateAffinePartial2D(BEFORE, AFTER, method=cv2.LMEDS)
scale = float(np.hypot(M[0, 0], M[1, 0]))
moved = cv2.warpAffine(before, M, (w, h), flags=cv2.INTER_LANCZOS4, borderValue=(0, 0, 0))
mask = cv2.warpAffine(np.full(before.shape[:2], 255, np.uint8), M, (w, h), flags=cv2.INTER_NEAREST)

# largest rectangle (same ratio as the photo) fully covered by the moved 'before' photo
ys, xs = np.where(mask == 255)
x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
while True:
    if mask[y0:y1 + 1, x0:x1 + 1].min() == 255:
        break
    x0, x1, y0, y1 = x0 + 2, x1 - 2, y0 + 2, y1 - 2
err = np.linalg.norm(cv2.transform(BEFORE[None], M)[0] - AFTER, axis=1)
cv2.imwrite(str(IMG / "ba-before-2000.webp"), moved[y0:y1 + 1, x0:x1 + 1], [cv2.IMWRITE_WEBP_QUALITY, 88])
cv2.imwrite(str(IMG / "ba-after-2000.webp"), after[y0:y1 + 1, x0:x1 + 1], [cv2.IMWRITE_WEBP_QUALITY, 88])
print(f"scale {scale:.3f}, mean error {err.mean():.1f} px, max {err.max():.1f} px, frame {x1 - x0 + 1}x{y1 - y0 + 1}")
