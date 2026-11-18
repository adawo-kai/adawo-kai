"""One-off, local only (needs Pillow + numpy): turns the avatar into a character grid for the hero.
usage: python scripts/make_portrait.py path/to/avatar.jpg
Writes scripts/portrait.json: {"cols": N, "rows": M, "lum": [[0..9 or -1]]}   (-1 = background, left empty)."""
import json, os, sys
from collections import deque
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageOps

HERE = os.path.dirname(os.path.abspath(__file__))
COLS, ROWS = 100, 52
CROP = (100, 58, 348, 306)           # head and shoulders in the 460 px avatar
# things that are not me, as polygons in avatar pixels: shower head, curtain right of the head
ERASE = [[(80, 40), (152, 40), (152, 84), (80, 84)], [(262, 40), (360, 40), (360, 262), (300, 224), (262, 204)]]

im = Image.open(sys.argv[1]).convert('RGB').crop(CROP)
W, H = im.size
a = np.asarray(im).astype(np.float32)
mx = a.max(axis=2); mn = a.min(axis=2)
cand = (mx > 145) & ((mx - mn) < 58)             # bright and almost colourless: wall, curtain
em = Image.new('L', (W, H), 0)
for poly in ERASE:
    ImageDraw.Draw(em).polygon([(x - CROP[0], y - CROP[1]) for x, y in poly], fill=255)
erase = np.asarray(em) > 0
cand |= erase
# background = candidate pixels connected to the border (keeps phone case, logo, eye whites)
bg = np.zeros((H, W), bool)
q = deque()
for x in range(W):
    q.append((0, x)); q.append((H - 1, x))
for y in range(H):
    q.append((y, 0)); q.append((y, W - 1))
for y, x in zip(*np.nonzero(erase)):          # the erased areas are background too: grow from them as well
    q.append((int(y), int(x)))
while q:
    y, x = q.popleft()
    if y < 0 or x < 0 or y >= H or x >= W or bg[y, x] or not cand[y, x]:
        continue
    bg[y, x] = True
    q.extend(((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)))
bg |= erase

g = ImageOps.autocontrast(im.convert('L'), cutoff=1)
g = g.filter(ImageFilter.UnsharpMask(radius=14, percent=110, threshold=0))      # local contrast: eyes, brows, mouth against the skin
g = g.filter(ImageFilter.UnsharpMask(radius=3, percent=150, threshold=2))
# equalise tones over my pixels only, so the face does not collapse into two or three levels
eq = ImageOps.equalize(g, mask=Image.fromarray((~bg * 255).astype(np.uint8)))
g = Image.blend(g, eq, 0.6)
small = np.asarray(g.resize((COLS, ROWS), Image.LANCZOS)).astype(np.float32) / 255.0
fg = np.asarray(Image.fromarray((~bg * 255).astype(np.uint8)).resize((COLS, ROWS), Image.BOX)).astype(np.float32) / 255.0
small = np.clip(small, 0, 1) ** 0.9
keep = fg > 0.5
# keep only the biggest connected blob (me); stray specks of curtain and wall go
lab = np.zeros(keep.shape, int); best = (0, 0); cur = 0
for y0 in range(ROWS):
    for x0 in range(COLS):
        if keep[y0, x0] and not lab[y0, x0]:
            cur += 1; n = 0; st = [(y0, x0)]; lab[y0, x0] = cur
            while st:
                y, x = st.pop(); n += 1
                for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    if True:
                        yy, xx = y + dy, x + dx
                        if 0 <= yy < ROWS and 0 <= xx < COLS and keep[yy, xx] and not lab[yy, xx]:
                            lab[yy, xx] = cur; st.append((yy, xx))
            best = max(best, (n, cur))
keep = lab == best[1]
lum = np.where(keep, np.clip((small * 10).astype(int), 0, 9), -1)
json.dump({'cols': COLS, 'rows': ROWS, 'lum': lum.tolist()}, open(os.path.join(HERE, 'portrait.json'), 'w'))
print('portrait', COLS, ROWS, 'foreground cells', int((lum >= 0).sum()))
