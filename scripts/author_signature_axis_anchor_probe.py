"""AUTHOR_SIGNATURE_AXIS_ANCHOR -- before/after demonstration.

Reproduces `SHAPE_KIND_FIELD_RESULTS.md` section 2.2's exact false-positive repro
(self-reference/recursion concept vs symmetry concept) through the REAL, live
`domains.reflective_faculty._shared_shape` (not a reimplementation), and additionally
runs a genuine TRUE-POSITIVE pairing (two concepts that both fire the SAME held
RelationCue) to confirm the fix does not also kill real matches.

"BEFORE" is reconstructed verbatim from the pre-fix source (git-shown, embedded here
as a frozen function so this script is a standalone, re-runnable artifact even after
the fix lands) -- it is byte-identical to the function this rung replaced
(`domains/reflective_faculty.py:7137-7154` at commit 6805175).

Run: PYTHONPATH=. python3 scripts/author_signature_axis_anchor_probe.py
"""
import json
import sys

from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds
from domains import reflective_faculty as rf


def shared_shape_BEFORE(agent, sig_a, sig_b):
    """Verbatim reproduction of the pre-fix `_shared_shape`
    (domains/reflective_faculty.py:7137-7154 at commit 6805175) -- naive positional zip."""
    sub = getattr(agent, "s", agent)
    native = getattr(sub, "_inner", sub)
    n = min(len(sig_a), len(sig_b))
    if n == 0:
        return None, 0
    a = [list(x) for x in sig_a[:n]]
    b = [list(x) for x in sig_b[:n]]
    res = native.evaluate(
        {"type": "AntiUnify", "values": {"type": "Lit", "value": [a, b]}, "wild": "·?·"}, {})
    fixed = native.evaluate(
        {"type": "FixedCount", "pattern": {"type": "Lit", "value": res}, "wild": "·?·"}, {})
    try:
        fixed = int(fixed)
    except Exception:
        fixed = 0
    return res, fixed


def main():
    print("Booting WorldAdapter + load_all_seeds (once)...")
    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)
    sub = agent.s

    rv = json.load(open("seeds/relation_vocabulary.json"))
    cues = {c["attrs"]["name"]: json.loads(c["attrs"]["relation"]) for c in rv.get("nodes", [])
            if c.get("type") == "RelationCue"}

    print("\n=== DEMO 1 (FALSE POSITIVE, SHAPE_KIND_FIELD_RESULTS.md sec.2.2 exact repro) ===")
    # concept_a: self-reference/recursion cues. concept_b: symmetry -- unrelated.
    concept_a_sig = [cues["self_reference"], cues["build_from_prior"], cues["base_case"]]
    d = json.load(open("seeds/math_capability_shapes.json"))
    sym_cues = {n["attrs"]["name"]: json.loads(n["attrs"]["signature"])
                for n in d.get("nodes", []) if n["attrs"].get("name") == "symmetry"}
    concept_b_sig = sym_cues["symmetry"]
    print(f"  concept_a (self-reference/recursion) = {concept_a_sig}")
    print(f"  concept_b (symmetry, unrelated)       = {concept_b_sig}")

    res_before, fixed_before = shared_shape_BEFORE(agent, concept_a_sig, concept_b_sig)
    print(f"  BEFORE (positional zip): result={res_before}")
    print(f"  BEFORE fixed (shared leaves) = {fixed_before}")

    res_after, fixed_after = rf._shared_shape(agent, concept_a_sig, concept_b_sig)
    print(f"  AFTER  (cue-identity keyed): result={res_after}")
    print(f"  AFTER  fixed (shared leaves) = {fixed_after}")

    p1_ok = (fixed_before == 1 and fixed_after == 0)
    print(f"  P1 (before==1, after==0): {'CONFIRMED' if p1_ok else 'REFUTED -- see output above'}")

    print("\n=== DEMO 2 (TRUE POSITIVE: two concepts genuinely sharing a named cue) ===")
    # concept_c and concept_d both fire self_reference AND build_from_prior (two
    # independently-authored 'recursive definition' style signatures, differently
    # ordered/padded to mimic two DIFFERENT concepts' own fired-cue lists -- exactly
    # what author_signature would emit for two unrelated-but-both-recursive concepts).
    concept_c_sig = [cues["build_from_prior"], cues["self_reference"], cues["base_case"]]
    concept_d_sig = [cues["self_reference"], cues["bounded"], cues["build_from_prior"]]
    print(f"  concept_c (fires build_from_prior, self_reference, base_case) = {concept_c_sig}")
    print(f"  concept_d (fires self_reference, bounded, build_from_prior)   = {concept_d_sig}")

    res_before2, fixed_before2 = shared_shape_BEFORE(agent, concept_c_sig, concept_d_sig)
    print(f"  BEFORE (positional zip): result={res_before2}")
    print(f"  BEFORE fixed (shared leaves) = {fixed_before2}")

    res_after2, fixed_after2 = rf._shared_shape(agent, concept_c_sig, concept_d_sig)
    print(f"  AFTER  (cue-identity keyed): result={res_after2}")
    print(f"  AFTER  fixed (shared leaves) = {fixed_after2}")

    p2_ok = (fixed_after2 > 0)
    print(f"  P2 (after fixed>0, true positive preserved): {'CONFIRMED' if p2_ok else 'REFUTED'}")

    print("\n=== DEMO 3 (P3: the two named call sites still resolve the pinned decision) ===")
    donkey = {"n": 0}
    agent.set_self_teacher(lambda q: (donkey.__setitem__("n", donkey["n"] + 1), "D")[1])
    from scripts.jabberwock_costs_its_frontier import author_cost_salience
    auth = author_cost_salience(agent)
    tf = auth.get("term_family")
    print(f"  author_cost_salience(agent)[\"term_family\"] = {tf!r} (expect 'residual_recurrence')")
    p3_ok = (tf == "residual_recurrence")
    print(f"  P3: {'CONFIRMED' if p3_ok else 'REFUTED'}")

    print("\n=== Verdict ===")
    if p1_ok and p2_ok and p3_ok:
        print("GO: false positive eliminated, true positive preserved, pinned decision unchanged.")
        return 0
    print("NO-GO on at least one predicate -- see output above.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
