"""RELATION_CUE_TOKEN_COLLISION spike -- Q1 live-consumer probe.

Demonstrates that `shape_fit` (runners/dsl/src/shape_decode.rs:1026-1045), the
scoring function inside the Rust `ShapeDecode` Term that backs
`compose_design_for_goal` / `induce_concern` / the whole SD-loop composer path, has
the SAME positional (non-axis-anchored) AntiUnify bug that `_shared_shape`
(domains/reflective_faculty.py) had BEFORE the just-merged author-signature
axis-anchor fix -- and that bug was NOT ported to `shape_fit`. Its own doc comment
says so explicitly: "(NOT predicate-matched -- this mirrors `_shared_shape`
exactly...)" -- describing the OLD, buggy `_shared_shape` behaviour as a deliberate
design choice that still stands in the Rust composer.

This script installs two synthetic ShapeSignature parts, A and B, that COVER THE
SAME residual relation (X) -- so their real, structural coverage ties (ncov=1 for
both, verified via covers_relation's own strict predicate+length+Covers check).
Part A additionally carries an UNRELATED second row (from a totally different held
cue) that happens to share ONE ACCIDENTAL TOKEN with the residual's second,
UNCOVERED relation (Y) -- purely a token-string coincidence, no shared cue, no
shared meaning. Part B carries no such row.

Because `shape_fit` truncates residual/psig to n=min(len) and AntiUnifies
POSITIONALLY (not axis-anchored), Part A's accidental token collision inflates its
`shape_fit` score above Part B's, even though both parts cover EXACTLY the same
real structure. Since `fit` is the composer's tie-break ordering key whenever
`covered.len()` ties (see `eval_shape_decode`'s `scored.sort_by`), this is a live,
exploitable defect: the composer's ranking preference between two structurally-tied
parts is decided by an accident of vocabulary reuse, not by real shared structure --
exactly what the just-merged `_shared_shape` fix eliminated at the Python layer.

Run: PYTHONPATH=".:runners/dsl/python" python3 scripts/shape_decode_shape_fit_collision_probe.py
"""
import json
import sys

from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds
from domains import reflective_faculty as rf


def main():
    print("Booting WorldAdapter + load_all_seeds (once)...")
    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)
    sub = agent.s

    rv = json.load(open("seeds/relation_vocabulary.json"))
    cues = {c["attrs"]["name"]: json.loads(c["attrs"]["relation"]) for c in rv.get("nodes", [])
            if c.get("type") == "RelationCue"}

    rel_X = cues["self_reference"]        # ["refers","NEW","to","SELF"]
    rel_Y = cues["map_part_to_part"]       # ["map","PART","to","PART"]  -- residual's 2nd, UNCOVERED relation
    rel_Q = cues["position_buffer"]        # ["hold","PART","at","POSITION"] -- Part A's own extra row
    print(f"  rel_X (goal, covered by both parts)      = {rel_X}   (cue: self_reference)")
    print(f"  rel_Y (goal, uncovered by either part)    = {rel_Y}   (cue: map_part_to_part)")
    print(f"  rel_Q (Part A's OWN extra row, unrelated) = {rel_Q}   (cue: position_buffer)")
    print(f"  rel_Y and rel_Q share ONLY the accidental token 'PART' at the same tuple slot;")
    print(f"  they are DIFFERENT cues, sharing no real structure.")

    # Part A: covers rel_X, plus an unrelated 2nd row (rel_Q) that collides positionally with rel_Y.
    a_id = sub.add_node("ShapeSignature", {
        "name": "probe_part_A", "kind": "probe",
        "signature": json.dumps([rel_X, rel_Q]),
    })
    # Part B: covers rel_X only -- the honest, minimal signature.
    b_id = sub.add_node("ShapeSignature", {
        "name": "probe_part_B", "kind": "probe",
        "signature": json.dumps([rel_X]),
    })
    print(f"\n  Installed probe_part_A (sig=[rel_X, rel_Q]) as node {a_id}")
    print(f"  Installed probe_part_B (sig=[rel_X])         as node {b_id}")

    goal_signature = [rel_X, rel_Y]
    print(f"\n  goal_signature (residual) = {goal_signature}")

    result = rf.compose_design_for_goal(agent, goal_signature, beam=3, max_steps=8, cand_k=3)
    print(f"\n  compose_design_for_goal result:")
    print(json.dumps(result, indent=2, default=str))

    plan = result.get("plan", []) if isinstance(result, dict) else []
    step0 = plan[0] if plan else {}
    chosen = step0.get("part")
    fit0 = step0.get("shape_fit")
    print(f"\n  Step 1 chosen part: {chosen!r}  shape_fit={fit0}")

    # Directly probe shape_fit's own scoring for A vs B via the ShapeDecode-adjacent
    # covers/fit math, reading back each candidate's OWN reported shape_fit if it
    # were tried alone against the SAME residual (isolate one part at a time by
    # excluding the other) -- the cleanest live demonstration that fit differs
    # despite identical coverage.
    result_a_only = rf.compose_design_for_goal(agent, goal_signature, beam=3, max_steps=8, cand_k=3,
                                               exclude=["probe_part_B"])
    result_b_only = rf.compose_design_for_goal(agent, goal_signature, beam=3, max_steps=8, cand_k=3,
                                               exclude=["probe_part_A"])
    fit_a = (result_a_only.get("plan") or [{}])[0].get("shape_fit")
    fit_b = (result_b_only.get("plan") or [{}])[0].get("shape_fit")
    cov_a = len((result_a_only.get("plan") or [{}])[0].get("covers", []))
    cov_b = len((result_b_only.get("plan") or [{}])[0].get("covers", []))
    print(f"\n  Part A alone: covers={cov_a} relations, shape_fit={fit_a}")
    print(f"  Part B alone: covers={cov_b} relations, shape_fit={fit_b}")

    tie_on_coverage = (cov_a == cov_b)
    fit_differs = (fit_a != fit_b)
    print(f"\n  Coverage ties (both cover exactly the SAME real structure): {tie_on_coverage}")
    print(f"  shape_fit differs despite tied coverage (spurious tie-break signal): {fit_differs}")

    if tie_on_coverage and fit_differs:
        print("\n  CONFIRMED: shape_fit's positional (non-axis-anchored) AntiUnify assigns "
              "different scores to two parts with IDENTICAL real coverage, purely from an "
              "accidental cross-cue token collision in an UNCOVERED, UNRELATED row. This is "
              "the same bug class fixed in `_shared_shape`, still live in the Rust ShapeDecode "
              "composer's `shape_fit`.")
        return 0
    print("\n  NOT CONFIRMED on this construction -- see output above.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
