"""closure_poscontrol -- THE INSTRUMENT'S ALIVENESS CHECK, BUILT FIRST.

VISION_CLOSURE_PREREG.md s4.  "A circle with a bit out isn't a discontinuous
circle" -- made a gate, BOTH directions.  The MDL closure operator PASSES iff:

  CLOSE          a ring (bright interior vs dark exterior) with a SHORT gap
                 closes to EXACTLY ONE enclosed region.
  REFUSE-uniform the SAME ring geometry+gap but NO luminance object (interior
                 == exterior) is REFUSED -- MDL declines because closing buys
                 no compression (Delta-mu ~ 0).  This is 'refusing
                 over-completion' -- the operator uses EVIDENCE, not geometry.
  REFUSE-arcs    two separate arcs that enclose NOTHING stay open (0 enclosed).

A mechanism that closes everything, or nothing, FAILS this.  And the
without-closure baseline on the CLOSE image (flood only) must give 0 enclosed
-- proving closure is what creates the enclosure, not the flood.

Seeds 115000-115009 (in-block) supply the sensor noise so noise_sigma is a
real measured quantity, not 0 (a clean synthetic has sigma->0, which would
make every bridge free -- the noise floor is a genuine part of the model).
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "scripts"))
sys.path.insert(0, os.path.join(ROOT, "domains"))

from domains import engine_provenance as ep                          # noqa: E402
import closure_lib as cl                                             # noqa: E402

EXPECT_ENGINE = "e039d2eec2dd"
G = 72
R = 15                    # ring radius
NOISE_SD = 3.0            # sensor noise (gray levels) -- so sigma is measurable
SEED_BASE = 115000


def ring_edge(gap_arc, cy=36, cx=36, r=R):
    """1-px ring edge map with an angular GAP of arc-length ~gap_arc px."""
    yy, xx = np.mgrid[0:G, 0:G]
    dist = np.sqrt((yy - cy) ** 2 + (xx - cx) ** 2)
    ring = np.abs(dist - r) < 0.7
    if gap_arc > 0:
        ang = np.arctan2(yy - cy, xx - cx)          # gap centred at angle 0
        half = (gap_arc / r) / 2.0
        ring &= ~(np.abs(ang) < half)
    return cl.skeletonize(ring)


def disc_lum(bright, dark, seed, cy=36, cx=36, r=R):
    """Luminance: bright disc interior, dark exterior, + sensor noise."""
    yy, xx = np.mgrid[0:G, 0:G]
    inside = (yy - cy) ** 2 + (xx - cx) ** 2 < r ** 2
    img = np.where(inside, float(bright), float(dark))
    img = img + np.random.RandomState(seed).normal(0, NOISE_SD, (G, G))
    return img


def two_arcs_edge():
    """Two separate arcs enclosing nothing: two facing brackets far apart."""
    e = np.zeros((G, G), bool)
    # left bracket: a short vertical bar with two nubs (an open [ )
    e[26:46, 20] = True
    e[26, 20:26] = True
    e[45, 20:26] = True
    # right bracket, mirrored, well separated (an open ] )
    e[26:46, 52] = True
    e[26, 47:53] = True
    e[45, 47:53] = True
    return cl.skeletonize(e)


def n_enclosed(edge):
    """Flood-only enclosed count (no closure)."""
    lab, n, border = cl.flood(edge)
    _, enc = cl.region_sizes(lab, n, border)
    return len(enc)


def main():
    ep.engine_preamble()
    prov = ep.provenance_line()
    if EXPECT_ENGINE not in prov:
        raise SystemExit(f"WRONG ENGINE: {prov}")
    print(prov)
    la0 = [round(x, 2) for x in os.getloadavg()]

    out = {"provenance": prov, "loadavg_start": la0, "cases": {}}

    # ---- CLOSE: short-gap ring, real luminance object ----
    e_close = ring_edge(gap_arc=5)
    img_close = disc_lum(200, 50, SEED_BASE + 0)
    base_close = n_enclosed(e_close)                 # flood-only: leaks -> 0
    r_close = cl.mdl_close(img_close, e_close, record=True)
    out["cases"]["close"] = {
        "flood_only_enclosed": base_close,
        "closed_enclosed": r_close["n_enclosed"],
        "closed_enc_median": r_close["enc_median"],
        "closed_enc_max": r_close["enc_max"],
        "n_bridges": r_close["n_bridges"],
        "sigma": r_close["sigma"],
    }

    # ---- REFUSE-uniform: same geometry, NO luminance object ----
    e_unif = ring_edge(gap_arc=5)
    img_unif = disc_lum(128, 128, SEED_BASE + 1)     # interior == exterior
    r_unif = cl.mdl_close(img_unif, e_unif, record=True)
    out["cases"]["refuse_uniform"] = {
        "closed_enclosed": r_unif["n_enclosed"],
        "n_bridges": r_unif["n_bridges"],
        "sigma": r_unif["sigma"],
    }

    # ---- REFUSE-arcs: two separate arcs enclose nothing ----
    e_arcs = two_arcs_edge()
    img_arcs = disc_lum(128, 128, SEED_BASE + 2)     # uniform field
    r_arcs = cl.mdl_close(img_arcs, e_arcs, record=True)
    out["cases"]["refuse_arcs"] = {
        "closed_enclosed": r_arcs["n_enclosed"],
        "n_bridges": r_arcs["n_bridges"],
    }

    # ---- VERDICT ----
    passed = (
        base_close == 0 and                          # flood alone leaks
        r_close["n_enclosed"] == 1 and               # closure creates 1 object
        r_unif["n_enclosed"] == 0 and                # refuse over-completion
        r_arcs["n_enclosed"] == 0                     # refuse: nothing to enclose
    )
    out["PASS"] = bool(passed)
    out["loadavg_end"] = [round(x, 2) for x in os.getloadavg()]
    with open(os.path.join(ROOT, "results", "closure_poscontrol.json"), "w") as fh:
        json.dump(out, fh, indent=1)
    print(json.dumps(out["cases"], indent=1))
    print("POSITIVE CONTROL PASS:", passed)
    if not passed:
        print("  close flood-only (want 0):", base_close,
              " closed (want 1):", r_close["n_enclosed"])
        print("  refuse-uniform (want 0):", r_unif["n_enclosed"])
        print("  refuse-arcs (want 0):", r_arcs["n_enclosed"])


if __name__ == "__main__":
    main()
