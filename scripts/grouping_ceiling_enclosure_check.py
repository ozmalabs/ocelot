"""grouping_ceiling_enclosure_check -- THE POST-HOC CROSS-CHECK, kept separate.

*** THIS IS POST-HOC. It is NOT one of VISION_GROUPING_CEILING_PREREG.md's
pre-registered statistics. *** It exists because that pre-registration's M4
named an enclosure confound as a caveat, and the first draft of the results
reasoned about the caveat instead of measuring it -- reporting a 33x
"the aperture fragments large regions" effect that is ~90% definitional.

It answers one question with no mechanism and no new hypothesis:

    OF THE >=60-CELL COMPONENTS THE FLOOD ACTUALLY PRODUCES, HOW MANY
    SURVIVE `bo_bgflood`'s ENCLOSURE TEST, AT EACH GRAIN?

It draws NO seed. It is a pure read-out over the same corpora, the same
frames and the same incumbent k as the main measurement, and its numbers are
reported in VISION_GROUPING_CEILING_RESULTS.md s3 labelled POST-HOC
throughout. Building anything on it requires its own prospective
pre-registration (s5).
"""
from __future__ import annotations

import importlib.util
import json
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from domains import engine_provenance as ep                  # noqa: E402

ep.engine_preamble()

TARGET = 60          # the brief's own target size; s2.2's curve is in the
                     # main measurement -- this check reads ONE point of it.
CORPORA = (("C1", 0, "08630d4b"), ("C2", 3, "119eca43"))


def main():
    spec = importlib.util.spec_from_file_location(
        "gc", os.path.join(ROOT, "scripts", "grouping_ceiling_measure.py"))
    gc = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gc)
    vp = gc._vp()
    origins = gc.region_origins()

    prov = ep.provenance_line()
    print(prov)
    if "WRONG ENGINE" in prov or "DIVERGED" in prov:
        raise SystemExit("ENGINE PROVENANCE FAILED -- RUN VOID")

    out = {"provenance": prov, "POST_HOC": True, "target": TARGET, "rows": []}
    for cid, ep_i, pin in CORPORA:
        frames, meta = vp.jellyfin_frames(
            gc.N_DECODE, every=2, start_s=300, size=gc.GRID,
            episode_index=ep_i)
        if not str(meta["episode_id"]).startswith(pin):
            raise SystemExit(f"PIN MISMATCH {cid} -- RUN VOID")
        for grain in ("tile", "whole"):
            big = big_enc = tot = tot_enc = 0
            for fi in gc.SAMPLED_FRAMES:
                q = gc.quantize(frames[fi], gc.K_INCUMBENT)
                fields = ([q[r0:r0 + gc.REGION, c0:c0 + gc.REGION]
                           for r0, c0 in origins] if grain == "tile" else [q])
                for f in fields:
                    st = gc.field_stats(f, f, 0)
                    tot += len(st["sizes"])
                    tot_enc += len(st["enc_sizes"])
                    big += sum(1 for x in st["sizes"] if x >= TARGET)
                    big_enc += sum(1 for x in st["enc_sizes"] if x >= TARGET)
            row = {"corpus": cid, "grain": grain, "components": tot,
                   "components_ge_target": big,
                   "enclosed_components": tot_enc,
                   "enclosed_ge_target": big_enc,
                   "survival_share": big_enc / max(1, big)}
            out["rows"].append(row)
            print(f"{cid} {grain:5s}: comps={tot:6d} >={TARGET}={big:4d} | "
                  f"enclosed={tot_enc:6d} >={TARGET}={big_enc:4d} | "
                  f"survival={row['survival_share']:.3f}")

    # The geometric account, computed rather than asserted: the share of
    # centre positions from which a TARGET-cell disc clears the field border.
    r = int(np.ceil(np.sqrt(TARGET / np.pi)))
    out["geometry"] = {str(L): float(((L - 2 * r) / L) ** 2)
                       for L in (gc.REGION, gc.GRID)}
    for L, v in out["geometry"].items():
        print(f"L={L}: centres clear of the border = {v:.4f}")

    path = os.path.join(ROOT, "results", "grouping_ceiling_enclosure.json")
    with open(path, "w") as fh:
        json.dump(out, fh, indent=1)
    print(f"[written] {path}")


if __name__ == "__main__":
    main()
