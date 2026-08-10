"""jabberwock_transfers_mechanism — CLOSE THE ANALOGICAL-TRANSFER GAP.

The rule-index build cc98b4eb diagnosed a DISCONNECT: the agent RECOGNISES a
concern's meta-shape (categorise_by_shape -> selective_gating) but its composer
(compose_design_for_goal / ShapeDecode) decodes by SURFACE predicate overlap, so
a concern written in a NEW domain's vocabulary shares no leaf with a mechanism
written in another domain's, decodes to total_fit=0/residual, and mint-as-novel
fires as a false fallback. The shape-recogniser and the mechanism-library were
never connected.

This script proves the fix — SHAPE->MECHANISM INDEX + retrieve-and-transfer:
  (a) THE CLASS CLOSES: the foveation/rule-index case, verbatim before->after
      (total_fit:0/residual  ->  AUTHORED plan built from the TRANSFERRED spatial
      foveation mechanism).
  (b) GENERALISES: a SECOND, DIFFERENT meta-shape (feedback_control) transfers its
      held mechanism (homeostatic regulation) into a NEW domain (rule-firing-rate
      regulation) through the SAME code path — proving it is the CLASS.

BEFORE = the composer WITHOUT the mechanism index loaded (byte-identical to the
pre-fix agent). AFTER = the SAME composer WITH the index loaded. The only
difference is the held index; the transfer machinery is one code path.

Run: PYTHONPATH=runners/dsl/python:.:scripts OZMA_NO_LLM=1 python3 \
       scripts/jabberwock_transfers_mechanism.py
"""
from __future__ import annotations
import os, sys, json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)


# The two concerns, each in its OWN domain's relational vocabulary. Salient
# domain fillers are ALL-CAPS (the goal's own structural marking). Neither shares
# surface predicates with the mechanism it should recruit.
FOVEATION_GOAL = [
    ["scan", "EVERY", "RULE", "per", "EVENT"],
    ["match", "over", "the", "WHOLE", "FRAME", "SET"],
    ["gate", "the", "SCAN", "to", "the", "FOCUS"],
    ["index", "the", "RULES", "by", "EVENT", "TYPE"],
    ["decode", "only", "RULES", "in", "FOCUS", "for", "this", "TYPE"],
]

REGULATION_GOAL = [
    ["measure", "the", "current", "FIRING", "RATE"],
    ["compare", "RATE", "to", "the", "set_point", "BUDGET"],
    ["regulate", "by", "FEEDBACK", "toward", "the", "BUDGET"],
    ["correct", "the", "SCHEDULER", "toward", "the", "BUDGET"],
]


def _boot(with_index: bool):
    from substrate.world_adapter import WorldAdapter
    from substrate.seed_loader import manifest_for
    wa = WorldAdapter()
    seeds = ["shape_vocabulary", "seven_meta_shape_subsystems", "relation_vocabulary"]
    if with_index:
        seeds.append("mechanism_index")
    for seed in seeds:
        try:
            wa.inner.load_seed_manifest(manifest_for(seed), wa.agent)
        except Exception as e:
            print(f"  (note: {seed} not separately loadable: {e})")
    return wa


def _case(title, goal, expect_shape):
    from domains.reflective_faculty import (compose_design_for_goal,
                                            retrieve_and_transfer_mechanism)
    from domains.teach import categorise_by_shape

    print("\n" + "=" * 92)
    print(title)
    print("=" * 92)
    print("[goal, in its own domain vocabulary]")
    for g in goal:
        print("   ", g)

    # what the agent RECOGNISES the shape as (its own recogniser)
    wa_r = _boot(with_index=False)
    text = " ".join(str(t) for st in goal for t in st)
    shape = categorise_by_shape(wa_r, "GoalConcern", {"text": text})
    print(f"\n[categorise_by_shape] the agent files this concern under META-SHAPE: {shape!r}"
          f"   (expected {expect_shape!r})")

    # BEFORE — the composer with NO mechanism index (the pre-fix agent)
    wa_before = _boot(with_index=False)
    before = compose_design_for_goal(wa_before, goal)
    print("\n[BEFORE — composer WITHOUT the shape->mechanism index (pre-fix)]")
    print(f"   authored     = {before.get('authored')}")
    print(f"   total_fit    = {before.get('total_fit')}")
    print(f"   plan         = {before.get('plan')}")
    print(f"   residual     = {json.dumps(before.get('residual'))[:180]}")

    # AFTER — the SAME composer WITH the index loaded
    wa_after = _boot(with_index=True)
    rt = retrieve_and_transfer_mechanism(wa_after, goal)
    after = compose_design_for_goal(wa_after, goal)
    print("\n[AFTER — SAME composer WITH the index; retrieve-and-transfer fires]")
    print(f"   authored        = {after.get('authored')}")
    print(f"   authored_by     = {after.get('authored_by')}")
    print(f"   total_fit       = {after.get('total_fit')}")
    print(f"   transferred_from= {json.dumps(after.get('transferred_from'))}")
    print(f"   slot_map        = {json.dumps(after.get('slot_map'), indent=None)}")
    print(f"   AUTHORED plan   =")
    for step in (after.get("plan") or []):
        print("       ", step)
    print(f"   retrieved under shape {rt.get('meta_shape')!r}: {rt.get('retrieved')}")

    ok = (not before.get("authored") and not before.get("total_fit")
          and after.get("authored") and after.get("total_fit", 0) > 0
          and after.get("authored_by") == "mechanism_transfer")
    print(f"\n   GATE: before(total_fit:0, not authored) -> after(AUTHORED, transfer): "
          f"{'PASS' if ok else 'FAIL'}")
    return ok, before, after


def main():
    print("THE JABBERWOCK RETRIEVES A HELD MECHANISM FOR A RECOGNISED SHAPE AND TRANSFERS IT")

    ok_a, _, _ = _case(
        "(a) THE CLASS CLOSES — rule-indexing is selective_gating; transfer SPATIAL FOVEATION",
        FOVEATION_GOAL, "selective_gating")

    ok_b, _, _ = _case(
        "(b) GENERALISES — rule-rate regulation is feedback_control; transfer HOMEOSTATIC REGULATION",
        REGULATION_GOAL, "feedback_control")

    print("\n" + "=" * 92)
    print(f"CLASS-CLOSES (a): {'PASS' if ok_a else 'FAIL'}    GENERALISES (b): {'PASS' if ok_b else 'FAIL'}")
    print("Same one code path (retrieve_and_transfer_mechanism) closes BOTH — the CLASS, not the instance.")
    print("=" * 92)
    return 0 if (ok_a and ok_b) else 1


if __name__ == "__main__":
    sys.exit(main())
