"""TRACK 3 — COMPRESSION-MEANING BALANCE (Rubric A RQ3, the L objective).

Rubric A (arXiv:2505.17117) RQ3 scores where a system sits on the compression-meaning
frontier with
    L(X, C; beta) = I(X;C)  +  beta * (1/|X|) * sum_c sum_{i in c} || e_i - centroid_c ||^2
                    \_____/     \_________________________________________________/
                    complexity                       distortion
                    (bits)                       (within-cluster spread)
Lower L = more "efficient." The published finding: LLMs OVER-COMPRESS — they reach a
LOWER L than humans by discarding within-category detail; humans keep an "inefficient",
HIGHER-L representation that preserves fine meaning.

The gated-minting claim, in RQ3 terms: minting a fine axis ADDS within-category detail,
which RAISES the distortion term and moves L UP — toward the human "rich" band and AWAY
from the LLM over-compressed floor. This track measures exactly that, before vs after
the fine grain is applied (coarse = the pre-mint / over-compressed representation; fine
= the post-mint representation that keeps the detail).

Item embeddings = the substrate's own signature coordinate on the graded axis
(dynamical:commitment), read at each grain — so the geometry L scores is the substrate's
actual felt representation, not an external vector. Clustering C = the human categories
(the fixed labeling, as in the paper's human-side L).

FALSIFIABLE CLAIMS:
  L1  MINTING RAISES L: fine-grain L > coarse-grain L (minting moves toward the human
      rich band, away from the over-compressed floor).
  L2  THE MOVE IS DISTORTION, NOT COMPLEXITY: the complexity (bits) term is unchanged
      between coarse and fine (same category clustering); the entire L increase is the
      DISTORTION term = preserved within-category meaning.
  L3  COARSE IS THE OVER-COMPRESSED FLOOR: at coarse grain distortion = 0 (all items
      collapse to one coordinate) — the LLM-style maximal compression that discards
      the fine distinction.
  L4  DISCRETE QUANTA + TEACHER-FREE: the coordinates are integer steps; pure graph
      reads, no external answerer.

Run: PYTHONPATH=runners/dsl/python:. python3 tests/capability/minting/track3_compression_meaning.py
"""
from __future__ import annotations

import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "runners"))
sys.path.insert(0, os.path.join(_HERE, "scoring"))

import metrics as M                     # noqa: E402
import substrate_runner as R            # noqa: E402


AXIS = [("dynamical:commitment", "field")]


def _all_int_vecs(vecs) -> bool:
    return all(float(v).is_integer() for row in vecs for v in row)


def main() -> int:
    print("=" * 78)
    print("TRACK 3 — COMPRESSION-MEANING BALANCE (Rubric A RQ3, the L objective)")
    print("minting raises L toward the human 'rich' band, away from the LLM "
          "over-compressed floor")
    print("=" * 78)

    fx = R.load_fixture()
    cats = fx["categories"]
    s, nodes, names, labels, protos = R.build_multi_category(cats)
    print("\n  %d items across %d categories" % (len(names), len(cats)))

    ob_fine = R.observer(s, "fine_L", {"dynamical:commitment": 0.125})
    ob_coarse = R.observer(s, "coarse_L", {"dynamical:commitment": 4.0})
    vec_fine = [R.item_signature_vector(s, nodes[n], ob_fine, AXIS) for n in names]
    vec_coarse = [R.item_signature_vector(s, nodes[n], ob_coarse, AXIS) for n in names]

    Lf = M.l_objective(labels, vec_fine, beta=1.0)
    Lc = M.l_objective(labels, vec_coarse, beta=1.0)

    print("\n  COARSE (pre-mint / over-compressed):")
    print("     complexity=%.4f  distortion=%.4f  L=%.4f"
          % (Lc["complexity"], Lc["distortion"], Lc["L"]))
    print("  FINE (post-mint / detail preserved):")
    print("     complexity=%.4f  distortion=%.4f  L=%.4f"
          % (Lf["complexity"], Lf["distortion"], Lf["L"]))
    print("  delta L (fine - coarse) = %+.4f" % (Lf["L"] - Lc["L"]))
    print("  (Rubric A: humans sit HIGHER-L/richer; LLMs LOWER-L/over-compressed)")

    # ---- claims ----
    l1 = Lf["L"] > Lc["L"]
    l2 = abs(Lf["complexity"] - Lc["complexity"]) < 1e-9 and Lf["distortion"] > Lc["distortion"]
    l3 = abs(Lc["distortion"]) < 1e-9
    l4 = _all_int_vecs(vec_fine) and _all_int_vecs(vec_coarse)

    print("\n" + "=" * 78)
    print("CLAIMS")
    print("=" * 78)
    rows = [("L1 minting raises L (toward human rich band)", l1),
            ("L2 the move is distortion, not complexity", l2),
            ("L3 coarse is the over-compressed floor (dist=0)", l3),
            ("L4 discrete quanta + teacher-free", l4)]
    for name, ok in rows:
        print("  %-46s %s" % (name, "PASS" if ok else "FAIL"))
    allpass = all(ok for _, ok in rows)
    verdict = ("TRACK 3 PASS: minting the fine axis raises the compression-meaning "
               "objective from L=%.2f (coarse: distortion 0, the LLM-style "
               "over-compressed floor that discards the distinction) to L=%.2f (fine: "
               "the within-category detail preserved) — moving the substrate toward "
               "the human 'inefficient'/rich band and away from the over-compressed "
               "floor. The entire increase is the DISTORTION (meaning) term; "
               "complexity is unchanged. Discrete quanta; teacher-free."
               % (Lc["L"], Lf["L"])
               if allpass else
               "TRACK 3 HONEST RESULT: see failing claim(s) above.")
    print("\nVERDICT: %s" % verdict)
    print("=" * 78)

    summary = {"track": 3, "metric": "L_objective_compression_meaning",
               "coarse": {k: round(v, 4) for k, v in Lc.items()},
               "fine": {k: round(v, 4) for k, v in Lf.items()},
               "delta_L": round(Lf["L"] - Lc["L"], 4),
               "l1": l1, "l2": l2, "l3": l3, "l4": l4, "all_pass": allpass}
    print("SUMMARY_JSON " + json.dumps(summary))
    return 0 if allpass else 1


if __name__ == "__main__":
    raise SystemExit(main())
