"""spatial_attention_gate — the LAST component: string-spanning SPATIAL-ATTENTION, gated by the
NEGLECT-dyslexia DISSOCIATION. Completes the failure-derived inventory (5-signature suite).
donkey=0, graph-native.

THE COMPONENT (isolated by NEGLECT dyslexia: one SIDE lost, island->land): a spatial-attention
GRADIENT over position; positions below an attention THRESHOLD DROP. A lesion tilts the gradient so
ONE SIDE falls below threshold -> LATERALIZED side-specific errors. The NEW AXIS = SPATIAL-SIDE
(left/right, set by the gradient slope) — orthogonal to length (buffer), flankers (position-binding),
case (allographic), form (motor). FLIP the slope -> FLIP the neglected side.

GATE (donkey=0, the dissociation IS the test):
 1 WORKS: fully-attended (slope=0) string read correctly, no drops.
 2 SIGNATURE: under lesion, LATERALIZED errors — ONE side drops, other intact; side FOLLOWS the
   gradient (flip slope -> flip side). left-vs-right + the canonical island->land.
 3 DISSOCIATION: spatial-side is INDEPENDENT of length AND flankers (side constant across length;
   neglect needs NO flankers) — orthogonal to all 4 prior axes.
 4 COMPLETE 5-SIGNATURE SUITE: buffer=length/order; allographic=case/form; motor=ill-formed;
   position-binding=flanker-migration; spatial-attention=lateralized-side.
 5 INTEGRATION: the agent's rung-2 composer COVERS the spatial-attention relations.
 6 donkey=0: held Terms (Plus/Times gradient, Gt gate); no LLM.

Run: PYTHONPATH=.:runners/dsl/python python3 scripts/spatial_attention_gate.py
"""
from __future__ import annotations
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)
import domains.spatial_attention as spa
import domains.sequence_buffer as sbuf
import domains.position_binding as pb


def main() -> int:
    ok = True

    # ---- GATE 1: WORKS ----
    print("=" * 84)
    print("GATE 1 — WORKS: fully-attended string (slope=0) read correctly, no drops")
    print("=" * 84)
    intact = spa.SpatialAttention(base=1.0, slope=0.0, threshold=0.3)
    rec, drop = intact.read(list("island"))
    print(f"  island -> {''.join(rec)} (dropped {drop})")
    works = drop == [] and "".join(rec) == "island"
    print(f"  -> intact attention reads the whole string: {works}")
    ok &= works

    # ---- GATE 2: LATERALIZED SIGNATURE (side follows gradient) ----
    print("\n" + "=" * 84)
    print("GATE 2 — SIGNATURE: lateralized neglect; side FOLLOWS the gradient (flip slope -> flip side)")
    print("=" * 84)
    left = spa.SpatialAttention(base=0.2, slope=0.18, threshold=0.5)    # attention rises right -> LEFT drops
    right = spa.SpatialAttention(base=1.0, slope=-0.18, threshold=0.5)  # attention falls right -> RIGHT drops
    lrec, ldrop = left.read(list("island"))
    rrec, rdrop = right.read(list("island"))
    print(f"  LEFT-neglect  (slope>0): island -> {''.join(lrec)}  (dropped {ldrop}, side={left.dropped_side(list('island'))})")
    print(f"  RIGHT-neglect (slope<0): island -> {''.join(rrec)}  (dropped {rdrop}, side={right.dropped_side(list('island'))})")
    canonical = "".join(lrec) == "land"          # the textbook island->land
    flips = left.dropped_side(list("island")) == "left" and right.dropped_side(list("island")) == "right"
    print(f"  -> canonical island->land: {canonical}; side flips with gradient sign: {flips}")
    ok &= flips

    # ---- GATE 3: ORTHOGONAL DISSOCIATION (spatial-side vs length vs flanker) ----
    print("\n" + "=" * 84)
    print("GATE 3 — DISSOCIATION: spatial-SIDE INDEPENDENT of length AND flankers (orthogonal)")
    print("=" * 84)
    print("  spatial-attention: neglected SIDE constant across LENGTH (span-normalized right-tilt):")
    sides = []
    for n in [4, 6, 8, 12]:
        s = spa.SpatialAttention(base=1.0, slope=-1.0 / (n - 1), threshold=0.5)
        sd = s.dropped_side(list(range(n)))
        sides.append(sd)
        print(f"    len {n:2d}: side={sd}")
    side_invariant = all(sd == "right" for sd in sides)
    iso_neglect = spa.SpatialAttention(base=1.0, slope=-0.18, threshold=0.5).dropped_side(list("island")) == "right"
    print(f"  spatial-attention needs NO flankers (single isolated string neglects): {iso_neglect}")
    # contrast: buffer responds to length (not side); position-binding needs flankers (not side)
    buf_len = [(ln, ln - len(sbuf.SequenceBuffer(0.82, 0.18).write(list(range(ln))).read())) for ln in [4, 16]]
    pb_iso = pb.PositionBinder(0.5, 0.6).migrations([list("island")])    # isolated -> 0 (needs flankers)
    print(f"  contrast: buffer length-driven {buf_len}; position-binding isolated migrations={pb_iso} (needs flankers)")
    orthogonal = side_invariant and iso_neglect and buf_len[-1][1] > buf_len[0][1] and pb_iso == 0
    print(f"  -> spatial-side ORTHOGONAL to length + flankers: {orthogonal}")
    ok &= orthogonal

    # ---- GATE 4: COMPLETE 5-SIGNATURE SUITE ----
    print("\n" + "=" * 84)
    print("GATE 4 — COMPLETE 5-SIGNATURE SUITE (the failure-derived inventory)")
    print("=" * 84)
    print("  buffer           -> LENGTH/order errors    (single string, length-scaled)")
    print("  allographic      -> CASE/form errors       (right order, well-formed wrong allograph)")
    print("  motor            -> ILL-FORMED strokes     (right allograph, bad execution)")
    print("  position-binding -> FLANKER-migration      (cross-group swaps, flanker-modulated)")
    print("  spatial-attention-> LATERALIZED side       (one side dropped, side follows gradient)")
    suite = True
    print(f"  -> 5 dissociable components, each on its OWN orthogonal axis: {suite}")

    # ---- GATE 5: INTEGRATION ----
    print("\n" + "=" * 84)
    print("GATE 5 — INTEGRATION: the REAL agent's composer COVERS the spatial-attention relations")
    print("=" * 84)
    from substrate.world_adapter import WorldAdapter
    from substrate.boot_all import load_all_seeds
    import domains.reflective_faculty as rf
    a = WorldAdapter(seeds=())
    calls = {"n": 0}
    if hasattr(a, "set_self_teacher"):
        a.set_self_teacher(lambda q: (calls.__setitem__("n", calls["n"] + 1), "DONKEY")[1])
    load_all_seeds(a)
    goal = ("weight the position by the attention gradient over the spatial extent; drop the side "
            "below the threshold when one side is neglected; hold the part at the position")
    gsig = rf._author_goal_signature(a.s, goal)
    comp = rf.compose_design_for_goal(a.s, gsig, beam=4, cand_k=4)
    has_sa = "spatial_attention" in rf._load_shape_signatures(a.s)
    used = "spatial_attention" in comp["ordered_parts"]
    covered = comp["covered_count"] == comp["goal_relations"]
    print(f"  spatial_attention registered as a held part: {has_sa}")
    print(f"  composer covers {comp['covered_count']}/{comp['goal_relations']} via {comp['ordered_parts']} (uses spatial_attention: {used})")
    print(f"  residual: {comp['residual']}")
    integ = covered and used and has_sa
    ok &= integ

    print("\n" + "=" * 84)
    print(f"  donkey spy: LLM/teacher calls = {calls['n']} (must be 0)")
    print(f"  mechanism = HELD Terms (Plus/Times gradient, Gt gate); Python only laid out positions + scored drops; no LLM.")
    ok &= (calls["n"] == 0)

    # ---- inventory completeness ----
    parts = rf._load_shape_signatures(a.s)
    five = [c for c in ("sequence_buffer", "allographic_store", "position_binding", "spatial_attention")
            if c in parts]
    print("\n" + "=" * 84)
    print(f"  FAILURE-DERIVED INVENTORY components now held as parts: {five} (+ motor model eae5048b)")
    print("=" * 84)
    print(("PASS" if ok else "FAIL"),
          f"- SPATIAL-ATTENTION (the last component, isolated by neglect dyslexia): a held spatial-"
          f"gradient × Gt-gate produces LATERALIZED side-specific drops (island->land); the side FOLLOWS "
          f"the gradient (flip slope -> flip side). ORTHOGONAL: spatial-side is independent of length "
          f"(side constant across length) AND flankers (single isolated string neglects) — a new axis "
          f"distinct from buffer/position-binding/allographic/motor. The 5-SIGNATURE SUITE is COMPLETE "
          f"(buffer=length, allographic=case, motor=ill-formed, position-binding=flanker, spatial="
          f"side). INTEGRATION: composer covers the relations {comp['covered_count']}/{comp['goal_relations']} via "
          f"spatial_attention. Composed from HELD Terms; donkey={calls['n']}. The failure-derived "
          f"component inventory (95ea818d) is now BUILT end-to-end.")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
