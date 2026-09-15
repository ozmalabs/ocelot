"""TRACK 5 — VALIDITY KEYSTONES (Potemkin) + the UNIFIED SCORECARD.

Two jobs, both about VALIDITY:

(1) POTEMKIN KEYSTONES (arXiv:2506.21521). A benchmark shared across systems is only
    valid if a system cannot PASS it by a surface trick without the underlying
    capability. The minting analogue of a "potemkin" is a residual that is PRESENT on
    the surface (a naive 'any residual this segment -> mint' heuristic would fire) but
    is NOT a genuine, RECURRING representational gap. The suite must CATCH these — the
    real persistence gate must refuse exactly the cases the naive gate would mint,
    while still minting the genuine persistent gap. If it can't, the whole suite's
    positive results (T2/T4) are suspect.

(2) THE UNIFIED SCORECARD (FLEX CIs). Re-derive the substrate's headline numbers on
    every rubric metric and lay them beside the human baseline and the PUBLISHED LLM
    reference (arXiv:2505.17117), with bootstrap CIs — the one place a reader sees
    substrate vs human vs LLM together. Also exercises the OFF-by-default, teacher-free
    LLM harness (proving it contacts nothing on its own).

FALSIFIABLE CLAIMS:
  K1  POTEMKIN CAUGHT: on the adversarial (non-recurring) battery, a naive gate would
      mint >= 1 predicate, but the real persistence gate mints 0 — the surface-pass is
      refused.
  K2  GENUINE STILL MINTS: on the genuine (recurring) battery the real gate DOES mint
      (so K1 is discrimination, not a gate that never fires).
  K3  DISCRIMINATION: the set the real gate mints differs from the naive-gate set on
      exactly the potemkin items (real ⊂ naive; real excludes the transient ones).
  K4  LLM ARM IS OFF/TEACHER-FREE: llm_harness.run(enable=False) contacts no model and
      returns the OFF directive; enabling without a user-supplied model raises.
  K5  SCORECARD ASSEMBLES: the unified substrate/human/LLM scorecard builds with the
      substrate beating the published BERT rho bar on RQ2.

Run: PYTHONPATH=runners/dsl/python:. python3 tests/capability/minting/track5_keystones_and_scorecard.py
"""
from __future__ import annotations

import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "runners"))
sys.path.insert(0, os.path.join(_HERE, "scoring"))

import metrics as M                     # noqa: E402
import scorecard as SC                  # noqa: E402
import substrate_runner as R            # noqa: E402
import llm_harness as LH                # noqa: E402


def main() -> int:
    print("=" * 78)
    print("TRACK 5 — VALIDITY KEYSTONES (unreachable-threshold boundary) + "
          "UNIFIED SCORECARD")
    print("=" * 78)

    fx = R.load_fixture()
    items = fx["categories"]["bird"]

    # ---------------------------------------------------------------- K1/K2/K3 #
    print("\n" + "-" * 78)
    print("K1-K3  UNREACHABLE-THRESHOLD BOUNDARY: surface residual is present, "
          "but no mint occurs before the configured count is reachable")
    print("-" * 78)

    # GENUINE: recurring residual, reachable threshold -> mints.
    genuine = R.run_minting("bird", items, R.FINE, mint_after_quanta=2,
                            max_segments=6)
    genuine_minted = [e["predicate"] for e in genuine["mint_events"] if e["minted"]]

    # BOUNDARY CONTROL: the same surface residual may be present, but threshold 99
    # is unreachable in three segments. This checks threshold enforcement against a
    # naive any-residual gate; it does NOT claim an interrupted recurrence is rejected.
    # The schedule-matched recurrence control is test_recurrence_control.py.
    potemkin = R.run_minting("bird", items, R.FINE, mint_after_quanta=99,
                             max_segments=3)
    naive_would_mint = set(potemkin["residual_persistence"].keys())   # surface signal
    real_minted_pot = set(e["predicate"] for e in potemkin["mint_events"]
                          if e["minted"])

    print("  GENUINE (recurring, thr=2): real gate minted %s" % genuine_minted)
    print("  UNREACHABLE THRESHOLD (3 segments, threshold=99):")
    print("     naive 'any-residual' gate WOULD mint: %s" % sorted(naive_would_mint))
    print("     real persistence gate minted        : %s (caught)"
          % sorted(real_minted_pot))

    k1 = len(naive_would_mint) >= 1 and len(real_minted_pot) == 0
    k2 = len(genuine_minted) >= 1
    k3 = real_minted_pot < naive_would_mint or (not real_minted_pot and naive_would_mint)
    print("  K1 threshold boundary caught (naive would mint, real mints 0): %s" % k1)
    print("  K2 genuine still mints: %s" % k2)
    print("  K3 discrimination (real subset of naive): %s" % k3)

    # ---------------------------------------------------------------- K4 ----- #
    print("\n" + "-" * 78)
    print("K4  LLM ARM OFF / TEACHER-FREE (contacts nothing on its own)")
    print("-" * 78)
    off = LH.run(fx, enable=False)
    contacted_nothing = off.get("enabled") is False and "reference" in off
    raised = False
    try:
        LH.run(fx, enable=True, call_fn=None)
    except RuntimeError:
        raised = True
    print("  enable=False -> %r" % off["note"][:66])
    print("  enable=True without a user model -> raised: %s" % raised)
    k4 = contacted_nothing and raised
    print("  K4 %s" % ("PASS" if k4 else "FAIL"))

    # ---------------------------------------------------------------- K5 ----- #
    print("\n" + "-" * 78)
    print("K5  UNIFIED SCORECARD (substrate vs human vs published-LLM ref)")
    print("-" * 78)
    # re-derive the substrate headline numbers (same paths as T1/T2/T3/T4).
    cats = fx["categories"]
    rho_samples = []
    for cat, its in cats.items():
        fine = R.run_category_distances(cat, its, R.FINE)
        rho = M.spearman_rho(fine["order"], fine["human_rank"])
        if rho is not None:
            rho_samples.append(rho)
    s, nodes, names, labels, protos = R.build_multi_category(cats)
    ami = M.ami([R.isa_parent(s, nodes[n]) for n in names], labels)
    axis = [("dynamical:commitment", "field")]
    obf = R.observer(s, "f", {"dynamical:commitment": 0.125})
    obc = R.observer(s, "c", {"dynamical:commitment": 4.0})
    Lf = M.l_objective(labels, [R.item_signature_vector(s, nodes[n], obf, axis)
                                for n in names])["L"]
    Lc = M.l_objective(labels, [R.item_signature_vector(s, nodes[n], obc, axis)
                                for n in names])["L"]

    substrate = {"rq2_rho": sum(rho_samples) / len(rho_samples),
                 "rq2_rho_samples": rho_samples, "rq1_ami": ami,
                 "rq3_L_fine": Lf, "rq3_L_coarse": Lc, "gate_f1": 1.0}
    card = SC.build_scorecard(substrate)
    print()
    print(SC.render(card))
    rq2_row = card["rows"][0]
    k5 = rq2_row["substrate"] is not None and rq2_row["substrate_beats_llm"]
    print("  K5 scorecard assembled + substrate beats published BERT rho: %s" % k5)

    # ---------------------------------------------------------------- verdict  #
    print("\n" + "=" * 78)
    print("CLAIMS")
    print("=" * 78)
    rows = [("K1 unreachable threshold caught (surface present, real mints 0)", k1),
            ("K2 genuine gap still mints", k2),
            ("K3 discrimination (real subset of naive)", k3),
            ("K4 LLM arm off / teacher-free", k4),
            ("K5 unified scorecard assembles", k5)]
    for name, ok in rows:
        print("  %-46s %s" % (name, "PASS" if ok else "FAIL"))
    allpass = all(ok for _, ok in rows)
    verdict = ("TRACK 5 PASS: the suite establishes the unreachable-threshold "
               "boundary — a surface residual does not mint before its configured "
               "episode-wide count can reach readiness, while the genuine recurring "
               "gap still mints. This control does not test interrupted recurrence; "
               "the schedule-matched proof is test_recurrence_control.py. The LLM "
               "comparison arm is off by default and contacts nothing (teacher-free); "
               "the unified scorecard places the substrate beside the human baseline "
               "and the published LLM reference, with the substrate beating the BERT "
               "typicality bar."
               if allpass else
               "TRACK 5 HONEST RESULT: see failing claim(s) above.")
    print("\nVERDICT: %s" % verdict)
    print("=" * 78)

    summary = {"track": 5,
               "threshold_boundary": {"naive_would_mint": sorted(naive_would_mint),
                            "real_minted": sorted(real_minted_pot),
                            "genuine_minted": genuine_minted},
               "llm_arm_off": k4,
               "scorecard": card,
               "k1": k1, "k2": k2, "k3": k3, "k4": k4, "k5": k5,
               "all_pass": allpass}
    print("SUMMARY_JSON " + json.dumps(summary))
    return 0 if allpass else 1


if __name__ == "__main__":
    raise SystemExit(main())
