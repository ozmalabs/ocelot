"""CUT-MINT POLICY — POST-HOC DIAGNOSTICS. **NOT PRE-REGISTERED.**

Labelled post-hoc throughout, and none of it changes a verdict in
`cut_mint_analyse.py`. Three questions the confirmatory run RAISED:

- **D1 — the size-match lottery.** The two pre-registered size-matches differ
  by 3.7x on C1 (+0.0507 vs +0.0138). With `K_n - K_a = 1` the "matched"
  control is a single-entry draw, so the spread may be the VALUE OF THE ENTRY
  EACH ONE HAPPENED TO DISCARD rather than anything about the policy. Priced
  with the same leave-one-out method used for the prevented mints.
- **D2 — deferral, not deletion.** The set-difference shows the abstaining arm
  minting the SAME regions one frame later. Measured, not eyeballed.
- **D3 — the floors**, because a grown codebook raises its own noise floor and
  the accept-rate contrast is confounded by it (prereg section 4).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from domains import engine_provenance as ep  # noqa: E402

ep.engine_preamble()

import importlib.util as iu  # noqa: E402

import numpy as np  # noqa: E402

from domains import video_accumulation_world as aw  # noqa: E402

CORPORA = {"C1": 0, "C2": 3}


def _mod(name):
    spec = iu.spec_from_file_location(name, str(ROOT / "scripts" / f"{name}.py"))
    m = iu.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def main():
    cm = _mod("cut_mint_measure")
    vp = _mod("video_probe_measure")
    D = json.loads((ROOT / "results/cut_mint.json").read_text())
    out = {"POST_HOC": True, "changes_no_verdict": True, "corpora": {}}

    for cid, epi in CORPORA.items():
        R = D["corpora"][cid]
        frames, meta = vp.jellyfin_frames(150, every=2, start_s=300,
                                          size=aw.GRID, episode_index=epi)
        q = [aw.quantize(f) for f in frames]
        qr = [aw.regions_of(x) for x in q]
        gr = [aw.grey_regions_of(f) for f in frames]
        held = D["held"]
        nkeys = [(m["frame"], m["region"]) for m in R["mints_noabstain"]]
        akeys = [(m["frame"], m["region"]) for m in R["mints_abstain"]]
        sub = [tuple(x) for x in R["arm_keys"]["NOABSTAIN_SUB"]]
        pre = [tuple(x) for x in R["arm_keys"]["NOABSTAIN_PRE"]]

        # ---- D1: what did each size-match throw away? ---------------------
        dropped_sub = [k for k in nkeys if k not in sub]
        dropped_pre = [k for k in nkeys if k not in pre]
        d1 = {
            "dropped_by_SUB": [list(k) for k in dropped_sub],
            "dropped_by_PRE": [list(k) for k in dropped_pre],
            "value_dropped_by_SUB":
                cm.price_entries(nkeys, qr, gr, held, dropped_sub),
            "value_dropped_by_PRE":
                cm.price_entries(nkeys, qr, gr, held, dropped_pre),
        }
        d1["obs_improved_SUB"] = sum(x["n_obs_improved"]
                                     for x in d1["value_dropped_by_SUB"])
        d1["obs_improved_PRE"] = sum(x["n_obs_improved"]
                                     for x in d1["value_dropped_by_PRE"])

        # ---- D2: deferral, not deletion -----------------------------------
        vetoed = sorted({(int(a["obs_key"].split("_")[0]),
                          int(a["obs_key"].split("_")[1]))
                         for a in R["abstentions"]})
        deferred = [[f, i] for f, i in vetoed
                    if any(f2 > f and i2 == i for f2, i2 in akeys
                           if f2 not in {v[0] for v in vetoed})]
        first_after = {}
        for f, i in vetoed:
            later = sorted([f2 for f2, i2 in akeys if i2 == i and f2 > f])
            first_after[f"{f}_{i}"] = later[0] if later else None
        d2 = {"vetoed": [list(v) for v in vetoed],
              "n_vetoed": len(vetoed),
              "n_reminted_later_same_region": len(deferred),
              "first_later_mint_of_same_region": first_after,
              "abstain_only_mints": [list(k) for k in akeys
                                     if k not in nkeys],
              "noabstain_only_mints": [list(k) for k in nkeys
                                       if k not in akeys]}

        # ---- D3: the floors ------------------------------------------------
        d3 = {an: {"floor": v["floor"], "accept": v["accept"],
                   "mean_is_max": v["mean_is_max"]}
              for an, v in R["arms"].items()}

        out["corpora"][cid] = {"D1_size_match_lottery": d1,
                               "D2_deferral": d2, "D3_floors": d3}
        print(f"[{cid}] D1 SUB dropped {d1['dropped_by_SUB']} improving "
              f"{d1['obs_improved_SUB']}/800 obs; PRE dropped "
              f"{d1['dropped_by_PRE']} improving {d1['obs_improved_PRE']}/800")
        print(f"[{cid}] D2 vetoed {d2['n_vetoed']}, same region re-minted "
              f"later: {d2['n_reminted_later_same_region']}; "
              f"abstain-only mints {d2['abstain_only_mints']}")
        print(f"[{cid}] D3 floors " + " ".join(
            f"{a}={v['floor']:.4f}" for a, v in d3.items()))

    p = ROOT / "results/cut_mint_diagnose.json"
    p.write_text(json.dumps(out, indent=1, default=float))
    print(f"wrote {p}")


if __name__ == "__main__":
    main()
