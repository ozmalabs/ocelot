"""closure_lib -- MDL CONTOUR CLOSURE / TRANSITIVE GROUPING, in numpy.

PROTOCOL VISION_CLOSURE_PREREG.md.  The lever the phasefield rung earned:
a proto-object is the region bounded by a CLOSED contour -- a CYCLE in the
edge-adjacency graph -- not a connected component of a local flag.  The
distinctive operation is GAP-BRIDGING to complete a cycle, decided by whether
closing COMPRESSES (MDL), so no 'completion aggressiveness' knob is tuned.

THE MDL BRIDGE RULE (s1 of the prereg):
    BRIDGE iff  n_int*(mu_int - mu_gnd)**2 / (2*sigma**2*ln2)  >  g*lambda + K_model
  LHS  = residual BITS SAVED by coding the enclosed region separately from ground.
  RHS  = boundary bits for the g-px bridge + one region descriptor.

s13 -- every constant falls out (VISION_CLOSURE_PREREG.md s2):
  lambda   = log2(3)   chain-code entropy of a good-continuation contour step
                       (8-connected forward cone) -- LATTICE geometry, not chosen.
  sigma    = the per-frame noise floor (robust scale of near-flat adjacent-pixel
             differences) -- MEASURED, the CHANGE rung's / phasefield's floor.
  K_model  = log2(levels) bits to index a region mean -- the bit-depth entropy.
The load-bearing scale is the RATIO sigma^2*lambda; the VERDICT rides on its
ROBUSTNESS across +-1 decade, never on its exact value.

Coordinates stay INTEGER (the frame is the integer lattice, CLAUDE.md
frame/continuum invariant); the continuous quantities (PC, means, DL) live in
the cross-frame MAP, never in a coordinate.
"""
from __future__ import annotations

import math

import numpy as np
from scipy import ndimage

LAMBDA = math.log2(3.0)          # chain-code entropy -- FALLS OUT of the lattice
LN2 = math.log(2.0)
CROSS = np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]])   # 4-connectivity


# --------------------------------------------------------------------------
# sigma -- the per-frame noise floor (MEASURED, s13-clean)
# --------------------------------------------------------------------------
def noise_sigma(img):
    """Robust sensor-noise scale: 1.4826 * MAD of the FLATTEST HALF of adjacent
    absolute differences.  Near-flat neighbour pairs carry noise, not edges, so
    restricting to the low half isolates the noise floor.  Falls out of the
    frame's own statistics -- no picked number."""
    img = np.asarray(img, float)
    dh = np.abs(np.diff(img, axis=1)).ravel()
    dv = np.abs(np.diff(img, axis=0)).ravel()
    d = np.concatenate([dh, dv])
    if d.size == 0:
        return 1.0
    flat = d[d <= np.median(d)]            # the near-flat half
    if flat.size == 0:
        flat = d
    sig = 1.4826 * np.median(flat)
    return float(max(sig, 1e-6))


def k_model(img):
    """Bits to index a region mean = log2 of the distinct luminance levels the
    frame actually uses.  Falls out of the frame's dynamic range."""
    img = np.asarray(img, float)
    rng = float(img.max() - img.min())
    return math.log2(max(rng, 2.0))


# --------------------------------------------------------------------------
# Zhang-Suen thinning -- deterministic, parameter-free 1-px skeleton
# --------------------------------------------------------------------------
def _neighbours(P):
    # P2..P9 clockwise from north (Zhang-Suen ordering)
    return [P[0, 1], P[0, 2], P[1, 2], P[2, 2],
            P[2, 1], P[2, 0], P[1, 0], P[0, 0]]


def skeletonize(binary):
    """Zhang-Suen 1976 thinning to a 1-px skeleton."""
    img = (np.asarray(binary) > 0).astype(np.uint8)
    changed = True
    while changed:
        changed = False
        for step in (0, 1):
            pad = np.pad(img, 1)
            H, W = img.shape
            to_del = np.zeros_like(img)
            ys, xs = np.nonzero(img)
            for y, x in zip(ys, xs):
                P = pad[y:y + 3, x:x + 3]
                n = _neighbours(P)
                C = sum(1 for i in range(8)
                        if n[i] == 0 and n[(i + 1) % 8] == 1)  # 0->1 transitions
                N = sum(n)
                if not (2 <= N <= 6 and C == 1):
                    continue
                if step == 0:
                    if n[0] * n[2] * n[4] != 0:      # P2*P4*P6
                        continue
                    if n[2] * n[4] * n[6] != 0:      # P4*P6*P8
                        continue
                else:
                    if n[0] * n[2] * n[6] != 0:      # P2*P4*P8
                        continue
                    if n[0] * n[4] * n[6] != 0:      # P2*P6*P8
                        continue
                to_del[y, x] = 1
            if to_del.any():
                img[to_del == 1] = 0
                changed = True
    return img


def endpoints(skel):
    """Skeleton pixels with exactly ONE 8-connected skeleton neighbour = the
    terminals of an open contour (a gap terminal)."""
    s = (np.asarray(skel) > 0).astype(int)
    k = np.array([[1, 1, 1], [1, 0, 1], [1, 1, 1]])
    deg = ndimage.convolve(s, k, mode="constant")
    ys, xs = np.nonzero((s == 1) & (deg == 1))
    return list(zip(ys.tolist(), xs.tolist()))


# --------------------------------------------------------------------------
# flood + enclosure
# --------------------------------------------------------------------------
def flood(edge):
    """4-connected components of the NON-edge cells.  Returns (lab, n,
    border_labels).  Label 0 is the edge set."""
    non = ~(np.asarray(edge) > 0)
    lab, n = ndimage.label(non, structure=CROSS)
    border = set(lab[0, :]) | set(lab[-1, :]) | set(lab[:, 0]) | set(lab[:, -1])
    border.discard(0)
    return lab, n, border


def region_sizes(lab, n, border):
    """(all_sizes, enclosed_sizes) over region labels 1..n."""
    sizes = np.bincount(lab.ravel(), minlength=n + 1)
    sizes[0] = 0
    labs = np.arange(len(sizes))
    live = labs[(sizes > 0) & (labs != 0)]
    alls = np.array([sizes[i] for i in live], int)
    enc = np.array([sizes[i] for i in live if i not in border], int)
    return alls, enc


# --------------------------------------------------------------------------
# bridge geometry
# --------------------------------------------------------------------------
def bres(p0, p1):
    """Integer straight line (Bresenham) between two lattice points, inclusive."""
    (y0, x0), (y1, x1) = p0, p1
    pts = []
    dy, dx = abs(y1 - y0), abs(x1 - x0)
    sy = 1 if y0 < y1 else -1
    sx = 1 if x0 < x1 else -1
    err = dx - dy
    y, x = y0, x0
    while True:
        pts.append((y, x))
        if y == y1 and x == x1:
            break
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            x += sx
        if e2 < dx:
            err += dx
            y += sy
    return pts


# --------------------------------------------------------------------------
# THE MDL CLOSURE OPERATOR -- greedy gap-bridging to a fixpoint
# --------------------------------------------------------------------------
def mdl_close(img, edge0, sigma=None, scale=1.0, dist_cap=20,
              max_iter=200, kmodel=None, record=False):
    """Greedily bridge gaps that COMPRESS, to a fixpoint.

    img      : luminance (for mu_int/mu_gnd/residual).
    edge0    : initial binary edge map (from PC threshold).
    sigma    : noise floor (measured if None).  `scale` multiplies sigma^2*lambda
               (the ROBUSTNESS axis; scale=1.0 is the derived operating point).
    dist_cap : COMPUTE bound on candidate gap length (assert no accepted bridge
               sits within 2 px of it, else the cap is load-bearing).

    Returns dict: final edge map, region stats, accepted bridges, and the
    max accepted bridge length (for the cap assertion)."""
    img = np.asarray(img, float)
    if sigma is None:
        sigma = noise_sigma(img)
    if kmodel is None:
        kmodel = k_model(img)
    denom = 2.0 * (sigma ** 2) * LN2
    rhs_per_g = LAMBDA * scale          # boundary bits per bridge pixel
    kmod = kmodel * scale

    edge = (np.asarray(edge0) > 0).copy()
    accepted = []
    max_len = 0
    for _ in range(max_iter):
        skel = skeletonize(edge)
        eps = endpoints(skel)
        if len(eps) < 2:
            break
        lab, n, border = flood(edge)
        # ground = the largest border-touching region (the leaking blob)
        sizes = np.bincount(lab.ravel(), minlength=n + 1)
        sizes[0] = 0
        gnd_candidates = [i for i in border]
        if not gnd_candidates:
            break
        gnd = max(gnd_candidates, key=lambda i: sizes[i])
        gnd_mean = float(img[lab == gnd].mean())

        # candidate gaps: endpoint pairs within dist_cap
        best = None
        eps_arr = np.array(eps)
        for a in range(len(eps)):
            ya, xa = eps[a]
            for b in range(a + 1, len(eps)):
                yb, xb = eps[b]
                g = math.hypot(ya - yb, xa - xb)
                if g > dist_cap or g < 1e-9:
                    continue
                # tentative bridge
                trial = edge.copy()
                for (yy, xx) in bres((ya, xa), (yb, xb)):
                    trial[yy, xx] = True
                lab2, n2, border2 = flood(trial)
                # interior = cells that were in the ground blob and are now
                # in a NON-border region (a cycle just enclosed them)
                enclosed_now = (lab == gnd) & np.isin(lab2, list(border2),
                                                      invert=True) & (lab2 != 0)
                n_int = int(enclosed_now.sum())
                if n_int == 0:
                    continue
                mu_int = float(img[enclosed_now].mean())
                # ground mean AFTER removing the interior
                rest = (lab == gnd) & ~enclosed_now
                if rest.sum() == 0:
                    continue
                mu_gnd = float(img[rest].mean())
                benefit = n_int * (mu_int - mu_gnd) ** 2 / denom
                cost = g * rhs_per_g + kmod
                delta = benefit - cost           # >0 => bridging compresses
                if delta > 0 and (best is None or delta > best[0]):
                    best = (delta, (ya, xa), (yb, xb), g, n_int)
        if best is None:
            break
        _, pa, pb, g, n_int = best
        for (yy, xx) in bres(pa, pb):
            edge[yy, xx] = True
        accepted.append({"a": pa, "b": pb, "g": round(g, 2), "n_int": n_int})
        max_len = max(max_len, g)

    lab, n, border = flood(edge)
    alls, enc = region_sizes(lab, n, border)
    H, W = img.shape
    out = {
        "sigma": float(sigma), "kmodel": float(kmodel), "scale": float(scale),
        "n_bridges": len(accepted),
        "max_bridge_len": float(max_len),
        "dist_cap": dist_cap,
        "n_regions": int(len(alls)),
        "n_enclosed": int(len(enc)),
        "enc_median": float(np.median(enc)) if len(enc) else None,
        "enc_max": int(enc.max()) if len(enc) else 0,
        "largest_frac": float(alls.max()) / (H * W) if len(alls) else 0.0,
        "all_sizes": alls.tolist(), "enc_sizes": enc.tolist(),
    }
    if record:
        out["accepted"] = accepted
        out["edge"] = edge
    return out
