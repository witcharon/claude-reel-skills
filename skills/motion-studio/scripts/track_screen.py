#!/usr/bin/env python3
"""Track a flat quad (a laptop lid or phone screen) through a shot and write its corners per frame.

  python3 track_screen.py --quad "220,577 531,584.5 525.5,773.5 224.5,769" --first 0 --last 77 \
      [--left-only-from 60] [--out track.json] [--sheet out/track_check.png]

--quad is the corners on --first, in source pixels, tl tr br bl (measure them on a 4x zoom crop with a grid).
Method: LK optical flow on features inside the quad, forward-backward check, RANSAC homography from the first
frame; features are topped up away from skin-toned pixels (hands) and carried back to the reference through H.
--left-only-from N fits only on the left half from frame N on, which keeps a hand coming in from the right from
dragging the fit. When the lid swings fast (motion blur, big perspective change), tracking gives out: mark those
few frames by hand on zoomed crops and override them in the film's own data.
"""
import argparse, json
import numpy as np
import cv2

ap = argparse.ArgumentParser()
ap.add_argument('--quad', required=True); ap.add_argument('--first', type=int, default=0); ap.add_argument('--last', type=int, required=True)
ap.add_argument('--left-only-from', type=int, default=None); ap.add_argument('--frames', default='frames/src_%04d.png')
ap.add_argument('--out', default='track.json'); ap.add_argument('--sheet', default='out/track_check.png')
a = ap.parse_args()
Q0 = np.float32([list(map(float, p.split(','))) for p in a.quad.split()])
def frame(i): return cv2.imread(a.frames % (i + 1))
def skin(bgr):
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    return (((hsv[..., 0] < 20) | (hsv[..., 0] > 160)) & (hsv[..., 1] > 25) & (hsv[..., 2] > 70)).astype(np.uint8) * 255
def mask_for(q, bgr):
    m = np.zeros(bgr.shape[:2], np.uint8); cv2.fillConvexPoly(m, np.int32(q), 255)
    return cv2.bitwise_and(m, cv2.bitwise_not(cv2.dilate(skin(bgr), np.ones((15, 15), np.uint8))))
lk = dict(winSize=(21, 21), maxLevel=3, criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 40, .01))
b0 = frame(a.first); prev = cv2.cvtColor(b0, cv2.COLOR_BGR2GRAY)
cur = cv2.goodFeaturesToTrack(prev, 500, .005, 4, mask=mask_for(Q0, b0), blockSize=5); ref = cur.copy()
left_x = Q0[:, 0].min() + .55 * (Q0[:, 0].max() - Q0[:, 0].min())
H = np.eye(3); quads = {a.first: Q0.tolist()}
for i in range(a.first + 1, a.last + 1):
    b = frame(i); g = cv2.cvtColor(b, cv2.COLOR_BGR2GRAY)
    nxt, st, _ = cv2.calcOpticalFlowPyrLK(prev, g, cur, None, **lk)
    back, st2, _ = cv2.calcOpticalFlowPyrLK(g, prev, nxt, None, **lk)
    ok = (st.ravel() == 1) & (st2.ravel() == 1) & (np.linalg.norm((back - cur).reshape(-1, 2), axis=1) < 2.0)
    ref, nxt = ref[ok], nxt[ok]
    use = np.ones(len(ref), bool) if a.left_only_from is None or i < a.left_only_from else (ref[:, 0, 0] < left_x)
    Hn, _ = cv2.findHomography(ref[use], nxt[use], cv2.RANSAC, 2.0)
    if Hn is not None: H = Hn
    q = cv2.perspectiveTransform(Q0[None], H)[0]; quads[i] = q.tolist()
    if i % 6 == 0 or len(ref) < 120:
        new = cv2.goodFeaturesToTrack(g, 400, .005, 5, mask=mask_for(q, b), blockSize=5)
        if new is not None:
            ref = np.vstack([ref, cv2.perspectiveTransform(new, np.linalg.inv(H)).astype(np.float32)]); nxt = np.vstack([nxt, new])
    cur, prev = nxt.astype(np.float32), g
json.dump({'first': a.first, 'last': a.last, 'quads': {str(k): v for k, v in quads.items()}}, open(a.out, 'w'))
picks = np.linspace(a.first, a.last, 8).round().astype(int)
x0, y0 = int(Q0[:, 0].min() - 60), int(Q0[:, 1].min() - 60); x1, y1 = int(Q0[:, 0].max() + 60), int(Q0[:, 1].max() + 60)
tiles = []
for i in picks:
    im = frame(i); cv2.polylines(im, [np.int32(np.round(np.array(quads[i]) * 8))], True, (0, 255, 255), 1, cv2.LINE_AA, shift=3)
    t = im[max(0, y0):y1, max(0, x0):x1].copy(); cv2.putText(t, str(i), (5, 22), 0, .7, (0, 0, 255), 2); tiles.append(t)
h = min(t.shape[0] for t in tiles); w = min(t.shape[1] for t in tiles)
cv2.imwrite(a.sheet, np.vstack([np.hstack([t[:h, :w] for t in tiles[:4]]), np.hstack([t[:h, :w] for t in tiles[4:]])]))
print(f'tracked {a.first}-{a.last} -> {a.out}; check {a.sheet} with your eyes (the quad must hug the lid edges)')
