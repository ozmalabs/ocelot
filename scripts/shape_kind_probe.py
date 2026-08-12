"""SHAPE_KIND_FIELD spike -- decisive measurement for predictions P2a/P2b.

Read-only probe. Does not touch the graph or boot an agent. Calls the same
native evaluator (`substrate_rs`) that `domains/reflective_faculty.py`'s
`_shared_shape` calls, reproducing its exact operation
(`reflective_faculty.py:7137-7154`) on constructed operands, to test:

  P2a: a genuinely cross-KIND pairing (CapabilityAxis-residual signature,
       CODEBOOK-kind, vs a seeded ShapeSignature{kind:'faculty'} signature,
       RELATION-PATTERN-kind) -- does it produce a spurious nonzero match?

  P2b: a genuinely SAME-KIND pairing (two Concept-authored RELATION-PATTERN
       signatures, structurally unrelated) -- does positional coincidence
       (no shared axis anchor, per author_signature's cue-scan-order layout)
       produce a spurious nonzero match anyway?

Run: python3 scripts/shape_kind_probe.py
"""
import json
import sys

import runners.dsl.python.substrate_rs as sr

s = sr.Substrate()
native = getattr(s, "_inner", s)


def shared_shape(sig_a, sig_b):
    """Verbatim reproduction of domains/reflective_faculty.py:7137-7154."""
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


print("=== §3 row-arity census: seeds/math_capability_shapes.json, kind='faculty' ===")
d = json.load(open("seeds/math_capability_shapes.json"))
faculty_lens = []
for n in d.get("nodes", []):
    a = n["attrs"]
    if a.get("kind") == "faculty":
        sig = json.loads(a["signature"])
        lens = [len(r) for r in sig]
        faculty_lens.extend(lens)
        print(f"  {a['name']}: row lengths {lens}")
print(f"  ALL faculty row lengths observed: {sorted(set(faculty_lens))}")
print()

print("=== P2a: CapabilityAxis-residual (CODEBOOK) vs ShapeSignature{kind:faculty} (RELATION-PATTERN) ===")
# A CapabilityAxis-residual signature exactly as learn_term_for_concern builds it
# (reflective_faculty.py:1110): [[p] for p in preds] -- always 1-element rows.
cap_axis_sig = [["scan"], ["gate"], ["focus"], ["route"]]
any_faculty = None
for nn in d.get("nodes", []):
    aa = nn["attrs"]
    if aa.get("kind") == "faculty":
        any_faculty = (aa["name"], json.loads(aa["signature"]))
        break
fname, fsig = any_faculty
res, fixed = shared_shape(cap_axis_sig, fsig)
print(f"  cap_axis_sig={cap_axis_sig}")
print(f"  faculty={fname!r} sig={fsig}")
print(f"  -> AntiUnify result={res}")
print(f"  -> fixed (shared leaves) = {fixed}")
p2a_confirmed = (fixed == 0)
print(f"  P2a (predicted fixed==0, accidental clean refusal): {'CONFIRMED' if p2a_confirmed else 'REFUTED -- spurious match found'}")
print()

print("=== P2b: two structurally-unrelated Concept-authored RELATION-PATTERN signatures ===")
# Built the same way author_signature (reflective_faculty.py:7112-7134) would build
# them: relation tuples straight from seeds/relation_vocabulary.json's RelationCue
# rows, in cue-scan order (NOT axis-sorted the way _concept_shape_vector is).
rv = json.load(open("seeds/relation_vocabulary.json"))
cues = {c["attrs"]["name"]: json.loads(c["attrs"]["relation"]) for c in rv.get("nodes", [])
        if c.get("type") == "RelationCue"}
# concept A: "self-referential recursion" flavoured cues (self_reference, build_from_prior, base_case)
concept_a_sig = [cues["self_reference"], cues["build_from_prior"], cues["base_case"]]
# concept B: a DIFFERENT, unrelated math idea -- symmetry/invariance. Genuinely no
# shared meaning with concept A's self-reference/recursion relations.
sym_cues = {n["attrs"]["name"]: json.loads(n["attrs"]["signature"])
            for n in d.get("nodes", []) if n["attrs"].get("name") == "symmetry"}
concept_b_sig = sym_cues.get("symmetry")
print(f"  concept_a (self-reference/recursion cues) = {concept_a_sig}")
print(f"  concept_b (symmetry, unrelated)            = {concept_b_sig}")
res2, fixed2 = shared_shape(concept_a_sig, concept_b_sig)
print(f"  -> AntiUnify result={res2}")
print(f"  -> fixed (shared leaves) = {fixed2}")
p2b_confirmed = (fixed2 > 0)
print(f"  P2b (predicted fixed>0, same-kind positional-coincidence spurious match): "
      f"{'CONFIRMED' if p2b_confirmed else 'REFUTED -- no spurious match'}")
print()

print("=== Verdict ===")
if p2a_confirmed and p2b_confirmed:
    print("Both predictions confirmed: the one live cross-kind site is already an "
          "accidental clean refusal (arity mismatch), and the live nonsense match "
          "found is SAME-kind, not cross-kind -- a `kind` tag would not have fixed it.")
    print("-> H2 REFUTED in the form registered. NO-GO on a kind-guard slice.")
    sys.exit(0)
else:
    print("At least one prediction refuted -- see SHAPE_KIND_FIELD_RESULTS.md for the "
          "revised analysis.")
    sys.exit(1)
