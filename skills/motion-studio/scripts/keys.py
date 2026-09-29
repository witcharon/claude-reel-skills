"""Mattes for putting motion behind or in front of things in a take. Import from a film script:

    import sys; sys.path.insert(0, '<skill>/scripts'); from keys import *

All functions take BGR uint8/float images in source resolution and return float mattes 0..1 (1 = foreground).
Write cut-outs as RGBA PNG (plate pixels + matte as alpha) and stack them above the layer that should sit behind.
"""
import numpy as np
import cv2

def _to_u8(img): return img if img.dtype == np.uint8 else img.clip(0, 255).astype(np.uint8)

def hand_matte(img, region=None, min_area=300):
    """Hands/sleeves over a dark screen: warm-toned bright blob, thin text opened away, holes filled, small bits dropped
    (an orange app icon is small; a hand is big). region: uint8 mask limiting where to look (e.g. the dilated screen quad)."""
    hsv = cv2.cvtColor(_to_u8(img), cv2.COLOR_BGR2HSV)
    warm = (hsv[..., 0] < 20) | (hsv[..., 0] > 160)
    h = ((hsv[..., 2] > 70) & (hsv[..., 1] > 25) & warm).astype(np.uint8)
    if region is not None: h &= (region > 0).astype(np.uint8)
    h = cv2.morphologyEx(h, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)))
    h = cv2.morphologyEx(h, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9)))
    ff = h.copy(); cv2.floodFill(ff, np.zeros((h.shape[0] + 2, h.shape[1] + 2), np.uint8), (0, 0), 1); h = h | (1 - ff)
    nc, lab, st, _ = cv2.connectedComponentsWithStats(h)
    h = np.isin(lab, [c for c in range(1, nc) if st[c, cv2.CC_STAT_AREA] > min_area]).astype(np.float32)
    return cv2.GaussianBlur(cv2.dilate(h, np.ones((3, 3), np.uint8)), (0, 0), 1.0)

def hue_key(img, keep, dark_below=None, dark_min_x=None):
    """Foreground by hue bands, e.g. a canopy against sky: keep=[(0, 25, 90), (165, 180, 90), (78, 98, 90)] as (h_lo, h_hi, s_min).
    dark_below: also keep pixels darker than this V (straps, risers), optionally only right of dark_min_x so they don't eat a letter."""
    hsv = cv2.cvtColor(_to_u8(img), cv2.COLOR_BGR2HSV).astype(np.int16)
    h, s, v = hsv[..., 0], hsv[..., 1], hsv[..., 2]
    m = np.zeros(h.shape, bool)
    for lo, hi, smin in keep: m |= (h >= lo) & (h <= hi) & (s > smin)
    if dark_below is not None:
        d = v < dark_below
        if dark_min_x is not None: d[:, :dark_min_x] = False
        m |= d
    m = cv2.morphologyEx(m.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
    return cv2.GaussianBlur(cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8)).astype(np.float32), (0, 0), 1.2)

def horizon_fit(img, band=(380, 620), cols=None, step=10):
    """Fisheye horizon as y = a x^2 + b x + c (source px): strongest bright-to-dark drop going down inside band,
    robust refit. Pass cols=[(20,230),(490,700)] to skip a ridge or subject in the middle. Check the fit by drawing it."""
    v = cv2.GaussianBlur(cv2.cvtColor(_to_u8(img), cv2.COLOR_BGR2HSV)[..., 2].astype(np.float32), (0, 0), 2)
    xs, ys = [], []
    ranges = cols or [(20, img.shape[1] - 20)]
    for lo, hi in ranges:
        for x in range(lo, hi, step):
            col = np.diff(v[band[0]:band[1], x]); y = band[0] + int(np.argmin(col))
            if col.min() < -3: xs.append(x); ys.append(y + .5)
    xs, ys = np.array(xs, float), np.array(ys, float); keep = np.ones(len(xs), bool)
    for _ in range(3):
        p = np.polyfit(xs[keep], ys[keep], 2); r = ys - np.polyval(p, xs)
        keep = np.abs(r) < max(4, 2.5 * np.median(np.abs(r[keep])))
    return p

def below_curve_matte(shape, coeffs, feather=5.0):
    """Foreground = everything below y = a x^2 + b x + c (e.g. clouds under the horizon), feathered."""
    H, W = shape[:2]; ys = np.arange(H, dtype=np.float32)[:, None]; xs = np.arange(W, dtype=np.float32)[None, :]
    a, b, c = coeffs; return np.clip((ys - (a * xs ** 2 + b * xs + c - feather / 2)) / feather, 0, 1)

def write_cutout(path, plate_bgr, matte):
    """Plate pixels with the matte as alpha, resized to the plate if needed."""
    if matte.shape[:2] != plate_bgr.shape[:2]:
        matte = cv2.resize(matte, (plate_bgr.shape[1], plate_bgr.shape[0]), interpolation=cv2.INTER_LINEAR)
    cv2.imwrite(path, np.dstack([_to_u8(plate_bgr), (matte * 255).clip(0, 255).astype(np.uint8)]))
