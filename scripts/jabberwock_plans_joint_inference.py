"""THE JABBERWOCK PLANS THE JOINT INFERENCE — and names the FACULTY it lacks (which we then build). No teacher.

The diagnosis: BPL's ~96.7% is ONE joint generative-program inference (all latents inferred together), not
five addable cues. The teacher's first move is to diagnose what the student already HOLDS. So the agent maps
the joint model's required parts onto its held faculties; whatever has no holder is the FACULTY GAP -- the
one thing to build (in Rust) so the agent can compose the rest. A RequiredPart --satisfied_by--> HeldFaculty
when their roles match (Argmax over role-overlap); an unmatched RequiredPart is flagged as the gap.

Run:  PYTHONPATH=.:runners/dsl/python python -m scripts.jabberwock_plans_joint_inference
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

import substrate_rs as srs

SEP = "=" * 98

# what the agent already HOLDS (built across the arc), each with the roles it covers.
HELD = [
    {"name": "recursive marginal-descent operator", "roles": {"parse_marginal", "correspondence_marginal", "joint_compose"}},
    {"name": "free-energy marginalisation (Sum/Exp/Log soft-min)", "roles": {"marginalise", "soft_min"}},
    {"name": "sparse-coded primitive basis (Phase 1)", "roles": {"generative_basis", "primitive_library"}},
    {"name": "per-primitive deformation modes (Phase 2)", "roles": {"deformation_manifold", "deformation_prior"}},
    {"name": "shape-context + smooth-deform cues", "roles": {"global_shape", "smooth_deform"}},
    {"name": "predict/Argmax recogniser spine", "roles": {"decide", "argmax_candidate"}},
]
# what the JOINT inference REQUIRES, each with the role that must be filled.
REQUIRED = [
    {"name": "marginalise the PARSE (segmentation hypotheses)", "role": "parse_marginal"},
    {"name": "marginalise the CORRESPONDENCE (part assignment)", "role": "correspondence_marginal"},
    {"name": "the GENERATIVE LEAF: P(query-part | candidate primitive DEFORMED within its prior), "
             "integrated over the deformation -- analysis-by-synthesis at the base case",
     "role": "generative_deformable_likelihood"},
    {"name": "marginalise the DEFORMATION inside the leaf (integrate, not commit)", "role": "deformation_marginal"},
    {"name": "compose all latents under ONE model (the joint, not a sum of cues)", "role": "joint_compose"},
    {"name": "decide the candidate (argmax posterior)", "role": "argmax_candidate"},
]


def main():
    print(SEP)
    print("THE JABBERWOCK PLANS THE JOINT INFERENCE — maps requirements to held faculties; names the gap to build.")
    print(SEP)

    s = srs.Substrate()
    held = []
    for h in HELD:
        n = s.add_node("HeldFaculty", {"name": h["name"]})
        for r in h["roles"]:
            s.add_edge_unchecked(n, "covers_role", s.add_node("Role", {"name": r}))
        held.append((h, n))
    # role -> is it covered by any held faculty?
    covered = {r for h in HELD for r in h["roles"]}

    print("\n  the agent HOLDS (built across the arc):")
    for h in HELD:
        print(f"      [{', '.join(sorted(h['roles']))}]  {h['name']}")

    print("\n  the JOINT inference requires -- mapped to what the agent holds:\n")
    gaps = []
    for R in REQUIRED:
        ok = R["role"] in covered
        holder = next((h["name"] for h in HELD if R["role"] in h["roles"]), None)
        if ok:
            print(f"    [HELD]  {R['name']}")
            print(f"            satisfied by: {holder}\n")
        else:
            gaps.append(R)
            print(f"    [GAP ]  {R['name']}")
            print(f"            NO held faculty covers role '{R['role']}' -- BUILD IT.\n")

    print(f"  {SEP[:94]}")
    print("  THE PLAN: the agent COMPOSES the joint inference from its held faculties -- the recursive marginal-")
    print("  descent (parse x correspondence x compose) with free-energy marginalisation, over the sparse basis,")
    print("  deciding by argmax. It cannot compose ONE piece it lacks:")
    for g in gaps:
        print(f"     -> FACULTY TO BUILD: {g['name']}")
    print("  This is the analysis-by-synthesis BASE CASE: a leaf that scores how well a candidate's primitive,")
    print("  DEFORMED within its learned manifold and integrated over that deformation, GENERATES the query part.")
    print("  Build it as a Rust Term (closed-form ridge-regularised deformation fit -> marginal residual); then")
    print("  the agent drops it into the recursive operator's leaf and the joint inference is composed -- BPL the")
    print("  brain's way: one generative model, all latents marginalised together, learned where biology allows.")
    print(SEP)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
