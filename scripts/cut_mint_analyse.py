"""CUT-MINT POLICY — THE PRE-REGISTERED DECISION RULE, APPLIED MECHANICALLY.

`VISION_CUT_MINT_POLICY_PREREG.md` section 5, committed at `9c0ac19d` BEFORE
any number. Every threshold and every predicted value in this file is READ FROM
THE PRE-REGISTRATION, not chosen here.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# ---- FIXED IN THE PRE-REGISTRATION, BEFORE ANY MEASUREMENT -----------------
# The accumulation rung's own prediction, stated numerically (prereg section 1).
PREDICTED_INHERITED = {"C1": +0.0625, "C2": +0.0474}
# My prediction (prereg section 1.1): the handicap scales with f, the fraction
# of the incumbent's mints that sit on a cut (0.188 / 0.194).
PREDICTED_MINE_CA = {"C1": +0.0410, "C2": +0.0135}
PREDICTED_MINE_CB = {"C1": +0.0050, "C2": +0.0081}
TOLERANCE = 0.02          # prereg section 5 decision rule 1
F_FRACTION = {"C1": 0.188, "C2": 0.194}
DEFICIT = {"C1": 0.0265, "C2": 0.0420}


def sep(d):
    """CI excludes zero."""
    return bool(d["lo"] is not None and (d["lo"] > 0 or d["hi"] < 0))


def main():
    src = ROOT / (sys.argv[1] if len(sys.argv) > 1 else "results/cut_mint.json")
    D = json.loads(src.read_text())
    out = {"source": str(src.name), "prereg": "9c0ac19d", "corpora": {}}

    for cid, R in D["corpora"].items():
        c = R["contrast"]
        CA, CB, CC, CD = (c["C_A_ABSTAIN_minus_UNIFORM"],
                          c["C_B_ABSTAIN_minus_NOABSTAIN_SUB"],
                          c["C_C_NOABSTAIN_SUB_minus_UNIFORM"],
                          c["C_D_ABSTAIN_minus_NOABSTAIN_PRE"])
        pi, pm = PREDICTED_INHERITED[cid], PREDICTED_MINE_CA[cid]
        v = {
            "K_abstain": R["K_abstain"], "K_noabstain": R["K_noabstain"],
            "reproduces_incumbent_growth": R["reproduces_incumbent_growth"],
            "C_A": CA, "C_B": CB, "C_C": CC, "C_D": CD,
            # ---- decision rule 1: the INHERITED prediction ----------------
            "CA_predicted_inherited": pi,
            "CA_predicted_mine": pm,
            "CA_error_vs_inherited": CA["mean"] - pi,
            "CA_error_vs_mine": CA["mean"] - pm,
            "inherited_within_tolerance": bool(abs(CA["mean"] - pi) <= TOLERANCE),
            "mine_within_tolerance": bool(abs(CA["mean"] - pm) <= TOLERANCE),
            "CA_separated": sep(CA),
            # ---- decision rule 2/3: the POLICY, isolated ------------------
            "CB_predicted_mine": PREDICTED_MINE_CB[cid],
            "CB_separated": sep(CB),
            "CB_unpowered": bool(
                not sep(CB)
                and CB["lo"] is not None
                and CB["lo"] <= 0 <= CB["hi"]
                and CB["lo"] <= PREDICTED_MINE_CB[cid] <= CB["hi"]),
            # ---- the cost, never netted into the benefit -----------------
            "n_prevented_mints": R["fp"]["n_prevented_mints"],
            "false_positive_steps": R["fp"]["false_positive_steps"],
            "missed_reference_steps": R["fp"]["missed_reference_steps"],
            "prevented_frames": R["fp"]["prevented_frames"],
            "cutfree_marked": R["fp"]["cutfree"]["marked"],
            "cutfree_n_steps": R["fp"]["cutfree"]["n_steps"],
            "cutfree_would_veto": len(R["fp"]["cutfree"]["would_veto_mints"]),
            "f_measured": (R["fp"]["n_prevented_mints"] / R["K_noabstain"]
                           if R["K_noabstain"] else None),
            "f_predicted": F_FRACTION[cid],
        }
        pv = R["fp"].get("prevented_value") or []
        v["prevented_value"] = {
            "n": len(pv),
            "total_obs_improved": sum(x["n_obs_improved"] for x in pv),
            "n_entries_that_improve_nothing":
                sum(1 for x in pv if x["n_obs_improved"] == 0),
            "max_drop": max([x["max_drop"] for x in pv], default=0.0),
            "mean_of_mean_drop":
                (sum(x["mean_drop"] for x in pv) / len(pv)) if pv else 0.0,
            "total_argmax": sum(x["n_argmax"] for x in pv),
        }
        # gate 1's verdict at this K, for both non-abstaining size-matches
        v["VERDICT_inherited_prediction"] = (
            "CONFIRMED" if (v["inherited_within_tolerance"]
                            and (cid != "C2" or v["CA_separated"]))
            else "NOT CONFIRMED")
        v["VERDICT_policy_isolated"] = (
            "POSITIVE" if v["CB_separated"] and CB["mean"] > 0 else
            "NEGATIVE" if v["CB_separated"] else
            "UNPOWERED" if v["CB_unpowered"] else "NULL")
        out["corpora"][cid] = v

        print(f"[{cid}] K_a={v['K_abstain']} K_n={v['K_noabstain']} "
              f"f={v['f_measured']:.3f} (predicted {v['f_predicted']:.3f})")
        for k, d in (("C-A ABSTAIN-UNIFORM", CA),
                     ("C-B ABSTAIN-NOABST_SUB", CB),
                     ("C-C NOABST_SUB-UNIFORM", CC),
                     ("C-D ABSTAIN-NOABST_PRE", CD)):
            print(f"     {k:24s} {d['mean']:+.4f} "
                  f"[{d['lo']:+.4f}, {d['hi']:+.4f}] sep={sep(d)}")
        print(f"     C-A predicted: inherited {pi:+.4f} (err "
              f"{v['CA_error_vs_inherited']:+.4f}) | mine {pm:+.4f} (err "
              f"{v['CA_error_vs_mine']:+.4f})")
        print(f"     INHERITED PREDICTION: {v['VERDICT_inherited_prediction']}"
              f"   POLICY ISOLATED: {v['VERDICT_policy_isolated']}")
        print(f"     cost: {v['n_prevented_mints']} mints prevented at frames "
              f"{v['prevented_frames']}; FP steps {v['false_positive_steps']}; "
              f"cut-free run marks {len(v['cutfree_marked'])}/"
              f"{v['cutfree_n_steps']} -> would veto {v['cutfree_would_veto']}")
        print(f"     prevented-mint value: {v['prevented_value']}")

    p = ROOT / "results/cut_mint_analysis.json"
    p.write_text(json.dumps(out, indent=1, default=float))
    print(f"wrote {p}")


if __name__ == "__main__":
    main()
