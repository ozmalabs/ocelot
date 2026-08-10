"""THE JABBERWOCK PROPOSES A REFRAMING — and tests whether it holds.

SELF-IMPROVEMENT #6, the honest, bounded version of the capacity the CREATOR
exercised this session (the reframings that reorganized everything — "values are
relative positions", "a frame is a weighted dimension-set", "not two — N" — came
from the creator, NOT the agent). This gives the agent the ability to PROPOSE and
TEST candidate unifying abstractions over its OWN introspectable structure, and to
FLAG survivors for the creator to judge.

WHAT IT DOES (reuse, don't reinvent):
  · SCAN   — introspect a family of the agent's own faculties (real module
             docstrings) and read their RECURRING structure with the agent's OWN
             analogy faculty (analogical_thinking.find_analogies + shape_hits).
  · PROPOSE— mint a Reframing graph node ("these N faculties are all cases of
             ABSTRACTION"), flagged for_review.
  · VERIFY — the agent's NOT-FOOLING-ITSELF faculty (self_verification.verify_claim)
             with a DISCRIMINATIVE control: a real pattern survives, a spurious one
             the instances don't actually share is REJECTED.

HONEST SCOPE (say it plainly): the proposer SURFACES + TESTS candidates over its
own structure. It does NOT judge whether a reframing is a good/deep foundational
insight, and it does not originate foundational geometry. Survivors are candidates
the CREATOR reviews — graph nodes flagged for_review, not installed truths.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_proposes_reframing.py
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds
from domains import reframing_proposer as rp
from domains.analogical_thinking import shape_hits


def main() -> int:
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    donkey = {"n": 0}
    a.set_self_teacher(lambda q: (donkey.__setitem__("n", donkey["n"] + 1), "D")[1])

    bar = "=" * 88
    print(bar)
    print("THE JABBERWOCK PROPOSES A REFRAMING — over its OWN faculties, then tests it holds")
    print(bar)

    # -- SCAN: the agent's own analogy faculty reads the recurring structure --
    _mt, defs = rp.introspect_faculties(a)
    print("\n[SCAN] introspected faculties (definition = each module's own docstring):")
    for name in defs:
        shapes = sorted(shape_hits(a, defs[name]))
        print(f"   · {name:28s} shape-read -> {shapes}")

    candidates = rp.scan_for_recurring_structure(a, min_instances=3, min_order=4)
    print(f"\n[SCAN] recurring structures surfaced (>=3 faculties, analogous at order 4): "
          f"{len(candidates)}")
    for c in candidates:
        print(f"   candidate: {c['abstraction']!r}  over {c['n_instances']} faculties "
              f"(order {c['order_n']}): {c['instances']}")

    # -- PROPOSE + VERIFY the REAL recurring structure (headline) --
    #    The collapse-plug shape: predict -> residual -> learn. All four faculties
    #    plug the ONE collapse engine into a different domain.
    real = next((c for c in candidates if c["abstraction"] == "prediction_minus_observation"),
                candidates[0] if candidates else None)
    print("\n" + bar)
    print("[PROPOSE + VERIFY]  the REAL recurring structure (headline)")
    print(bar)
    real_node = rp.propose_reframing(a, real)
    real_res = rp.verify_reframing(a, real_node, defs)
    print(f"  PROPOSED reframing: \"these {real['n_instances']} faculties are all cases of "
          f"{real['abstraction']!r}\"")
    print(f"    instances : {real['instances']}")
    print(f"    (this is the DomainPlug-into-run_collapse shape: predict -> residual -> learn,")
    print(f"     the ONE collapse engine pointed at motion / a person / context / self-competence)")
    print(f"  VERDICT   : accepted={real_res['accepted']}  discriminates={real_res['discriminates']}"
          f"  grounded={real_res['grounded']}")
    print(f"    {real_res['reason']}")

    # -- DISCRIMINATIVE: a SPURIOUS abstraction the instances do NOT share --
    print("\n" + bar)
    print("[DISCRIMINATIVE]  a SPURIOUS pattern is proposed-then-REJECTED")
    print(bar)
    spurious = {
        "abstraction": "competitive_inhibition",   # winner-take-all — NOT what these do
        "kind": "meta_shape",
        "order_n": 4,
        "instances": real["instances"],            # SAME instances, SAME grounding
        "n_instances": real["n_instances"],
    }
    spur_node = rp.propose_reframing(a, spurious)
    spur_res = rp.verify_reframing(a, spur_node, defs)
    print(f"  PROPOSED (fake): \"these faculties are all cases of {spurious['abstraction']!r}\"")
    print(f"    same instances, same grounding — the ONLY difference is whether the")
    print(f"    abstraction actually holds across them (the agent's shape read).")
    print(f"  VERDICT   : accepted={spur_res['accepted']}  discriminates={spur_res['discriminates']}")
    print(f"    {spur_res['reason']}")

    # -- FLAGGED-NOT-ASSERTED: the honest boundary --
    print("\n" + bar)
    print("[FLAGGED, NOT ASSERTED]  the honest boundary")
    print(bar)
    ra = a.s.node(real_node)["attrs"]
    print(f"  the surviving Reframing node carries: verified={ra.get('verified')}  "
          f"for_review={ra.get('for_review')}")
    print("  -> even VERIFIED, it stays a CANDIDATE flagged for the creator. The proposer")
    print("     tested that the pattern HOLDS; it did NOT judge it a deep foundational insight,")
    print("     and it installed nothing as truth. That judgement is the creator's.")

    print(f"\n[donkey] LLM calls: {donkey['n']}  (0 = no model; scan + verify are held faculties)")
    print(bar)
    print("HONEST SCOPE: the agent PROPOSES + TESTS analogical generalizations over its OWN")
    print("introspectable structure. It does NOT originate foundational geometry; the great")
    print("reframings this session were the CREATOR's. Survivors are flagged for review.")
    print(bar)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
