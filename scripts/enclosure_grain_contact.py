"""enclosure_grain_contact -- WHAT DOES A GROUND COMPONENT'S BORDER CONTACT
LOOK LIKE?  *** POST-HOC. ***

*** THIS IS POST-HOC.  It is NOT one of VISION_ENCLOSURE_GRAIN_PREREG.md's
pre-registered statistics. *** It extends that prereg's M1 line -- "number of
GROUND components and the share of cells they hold ... WHAT ENCLOSURE CALLS
BACKGROUND" -- with the one quantity that separates the two live readings of
the main result, and it is labelled POST-HOC everywhere it is reported.

The main measurement refuted this rung's P1: on structureless input observed
enclosure equals the geometric null to within 1%, while on natural frames it
falls to 0.04-0.49 of the null for large components.  So `bo_bgflood` is NOT
computing window-fit.  Large equal-value regions really do reach the frame
edge.  TWO READINGS SURVIVE THAT, and they have different next rungs:

  (A) THE REGIONS ARE GENUINELY BACKGROUND.  A sky/wall/floor runs off the
      picture on a LONG stretch, usually of MORE THAN ONE side.  Then the
      predicate is right, there is nothing to rescue, and no mechanism is
      warranted.

  (B) THEY ARE BRUSHING THE EDGE.  A large region is vetoed by a handful of
      cells touching one side -- the value-flood rung's recorded disease
      ("the gate lets ONE touching cell veto an entire component", the
      inversion of "a circle with a bit out isn't a discontinuous circle").
      Then contact EXTENT is the missing quantity.

The discriminator is CONTACT, measured RELATIVE to the component's own
perimeter -- a ratio of like quantities, so no absolute length is chosen and
nothing here is compared against a literal (s13).  This script decides
nothing; it reports a distribution.

It draws NO seed.  It is a pure read-out over the same corpora, frames and
incumbent k as the main measurement.
"""
from __future__ import annotations

import importlib.util
import json
import os
import sys
import time

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "domains"))

from domains import engine_provenance as ep                  # noqa: E402

ep.engine_preamble()


def _mod(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


EG = _mod("eg", os.path.join(ROOT, "scripts", "enclosure_grain_measure.py"))


def contact_stats(lab, n, L):
    """Per component: size, cells ON the border ring, distinct sides touched,
    and the component's own boundary length (cells with a 4-neighbour outside
    the component OR outside the field).

    `contact / boundary` is a ratio of LIKE QUANTITIES: what share of a
    component's own outline is the picture edge rather than a real contour.
    """
    H, W = lab.shape
    flat = lab.ravel()
    counts = np.bincount(flat, minlength=n)

    ring = np.zeros((H, W), bool)
    ring[0, :] = ring[-1, :] = True
    ring[:, 0] = ring[:, -1] = True
    contact = np.bincount(lab[ring], minlength=n)

    sides = np.zeros((n, 4), bool)
    sides[lab[0, :], 0] = True
    sides[lab[-1, :], 1] = True
    sides[lab[:, 0], 2] = True
    sides[lab[:, -1], 3] = True
    n_sides = sides.sum(axis=1)

    # boundary: a cell of the component with a differently-labelled
    # 4-neighbour, or with a neighbour off the field.
    diff = np.zeros((H, W), bool)
    diff[:, :-1] |= lab[:, :-1] != lab[:, 1:]
    diff[:, 1:] |= lab[:, :-1] != lab[:, 1:]
    diff[:-1, :] |= lab[:-1, :] != lab[1:, :]
    diff[1:, :] |= lab[:-1, :] != lab[1:, :]
    diff |= ring
    boundary = np.bincount(lab[diff], minlength=n)

    idx = np.flatnonzero(counts > 0)
    return {"size": counts[idx], "contact": contact[idx],
            "sides": n_sides[idx], "boundary": boundary[idx],
            "is_ground": contact[idx] > 0}


def main():
    t0 = time.time()
    prov = ep.provenance_line()
    print(prov)
    print(f"[load] start {EG.loadavg()}")
    if "WRONG ENGINE" in prov or "DIVERGED" in prov:
        raise SystemExit("ENGINE PROVENANCE FAILED -- RUN VOID")

    vp = _mod("vp", os.path.join(ROOT, "scripts", "video_probe_measure.py"))
    out = {"POST_HOC": True, "provenance": prov,
           "loadavg_start": EG.loadavg(), "corpora": {}}

    for cid, epi, pin in EG.CORPORA:
        frames, meta = vp.jellyfin_frames(EG.N_DECODE, every=2, start_s=300,
                                          size=EG.GRID, episode_index=epi)
        if not str(meta["episode_id"]).startswith(pin):
            raise SystemExit(f"PIN MISMATCH {cid} -- RUN VOID")
        qs = [EG.quantize(frames[fi], EG.K_INCUMBENT) for fi in EG.FRAMES_WIDE]
        rows = {}
        for L in EG.GRAINS:
            S, C, SD, B = [], [], [], []
            for q in qs:
                for t in EG.tiles_of(q, L):
                    lab, n = EG.label(np.asarray(t, int), 0)
                    st = contact_stats(lab, n, L)
                    g = st["is_ground"]
                    S.append(st["size"][g]); C.append(st["contact"][g])
                    SD.append(st["sides"][g]); B.append(st["boundary"][g])
            size = np.concatenate(S); con = np.concatenate(C)
            sd = np.concatenate(SD); bnd = np.concatenate(B)
            if size.size == 0:
                continue
            frac = con / np.maximum(bnd, 1)
            bands = []
            for lo, hi in EG.BANDS:
                if lo > int(size.max(initial=0)):
                    break
                m = (size >= lo) & (size < hi)
                if not m.any():
                    continue
                bands.append({
                    "lo": lo, "hi": hi, "n": int(m.sum()),
                    "contact_median": float(np.median(con[m])),
                    "contact_p10": float(np.percentile(con[m], 10)),
                    "sides_median": float(np.median(sd[m])),
                    "sides_hist": [int((sd[m] == s).sum()) for s in (1, 2, 3, 4)],
                    "outline_share_median": float(np.median(frac[m])),
                    "outline_share_p10": float(np.percentile(frac[m], 10)),
                    # A ground component has at least one ring cell BY
                    # DEFINITION, so 1 is the ARITHMETIC FLOOR of `contact`,
                    # not a level anyone chose.  Reported as a count.
                    "at_minimum_contact": int((con[m] == 1).sum()),
                })
            rows[str(L)] = {"n_ground": int(size.size), "bands": bands}
            big = bands[-1] if bands else None
            print(f"[{cid}] L={L:2d} ground={size.size:7d}  "
                  f"largest band {big['lo'] if big else '-'}+: n={big['n'] if big else 0} "
                  f"contact_med={big['contact_median'] if big else '-'} "
                  f"sides_med={big['sides_median'] if big else '-'} "
                  f"outline_share_med={big['outline_share_median'] if big else '-'}")
        out["corpora"][cid] = rows

    out["loadavg_end"] = EG.loadavg()
    out["secs"] = round(time.time() - t0, 1)
    out["provenance_after"] = ep.provenance_line()
    path = os.path.join(ROOT, "results", "enclosure_grain_contact.json")
    with open(path, "w") as fh:
        json.dump(out, fh, indent=1, default=lambda o: (
            o.tolist() if isinstance(o, np.ndarray) else float(o)))
    print(f"[load] end {out['loadavg_end']}  {out['secs']}s")
    print(f"[written] {path}")


if __name__ == "__main__":
    main()
