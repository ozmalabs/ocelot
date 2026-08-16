"""Live demonstration harness for domains/can_self_worth_bridge.py's
persistence layer (find_or_build_resident_can / record_incident_outcome).

Per docs/research/psychology_affect/PERSISTENT_SELF_WORTH_PREREG.md Sec3.

Run: python3 scripts/persistent_self_worth_demo.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "runners" / "dsl" / "python"))

import json  # noqa: E402

import substrate_rs as sr  # noqa: E402
from substrate.seed_loader import engine_rules_only  # noqa: E402
from domains.can_self_worth_bridge import (  # noqa: E402
    ensure_can_seed, find_or_build_resident_can, record_incident_outcome,
)

DISPUTE_SEED_PATHS = [
    "seeds/rule_dispute_escalation.json",
    "seeds/self_conscious_emotions.json",
    "seeds/rule_dispute_self_conscious_bridge.json",
]


def _appraise_dispute(inner, *, issue_severity, band_code, witnesses, held_self_worth):
    ctx = inner.add_node("DisputeContext", {
        "issue_severity": issue_severity, "band_code": band_code, "audience_gain": 0.15})
    for closeness in witnesses:
        w = inner.add_node("WitnessPresence", {"closeness": closeness})
        inner.add_edge(ctx, "has_witness", w, {})
    pattern = inner.add_node("SelfPattern", {"held_self_worth": float(held_self_worth)})
    inner.add_edge(ctx, "has_self_pattern", pattern, {})
    sig = inner.add_node("RuleDisputeSignal", {"status": "pending"})
    inner.add_edge(ctx, "has_signal", sig, {})
    inner.run_rules(50)
    sc_ctx = inner.neighbours(ctx, "bridged_to")[0]
    sc_sig = inner.neighbours(sc_ctx, "has_appraisal")[0]
    return inner.node(sc_sig)["attrs"]["emotion"]

CONFIDENT = {"name": "Confident", "index": 0, "params": {
    "resolution_bins": 8, "arousal": 0.2,
    "prior_world_safe": 0.6, "prior_self_worth": 0.9,
    "charm_weight": 0.5, "hostile_weight": 0.2, "prior_others_trust": 0.5,
    "claim_weight": 0.6, "w_supergraph": 0.5, "w_spite": 0.1,
    "mood_bias": 0.3,
}}


def main():
    s = sr.Substrate()
    inner = s._inner
    ensure_can_seed(inner)

    print("=" * 78)
    print("PREDICTION 1: force_all_dirty() is necessary")
    print("=" * 78)
    out = find_or_build_resident_can(inner, CONFIDENT)
    concepts = out["concepts"]
    sw = concepts["self_worth"]
    print("initial self_worth:", out["self_worth"])
    inner.concept_apply_evidence(sw, -1.0, 5.0)
    steps_without = inner.run_rules(3000)
    print("massive evidence applied, run_rules() WITHOUT force_all_dirty():",
          "steps=%d state=%s (unchanged -- the gotcha)" % (
              steps_without, inner.node(sw)["attrs"]["state"]))
    inner.force_all_dirty()
    steps_with = inner.run_rules(3000)
    print("SAME evidence, NOW with force_all_dirty():",
          "steps=%d state=%s" % (steps_with, inner.node(sw)["attrs"]["state"]))

    print()
    print("=" * 78)
    print("PREDICTION 2: repeated incidents flip a resident's basin")
    print("(fresh resident this time, via record_incident_outcome)")
    print("=" * 78)
    s2 = sr.Substrate()
    inner2 = s2._inner
    ensure_can_seed(inner2)
    out2 = find_or_build_resident_can(inner2, CONFIDENT)
    print("incident 0 (initial): self_worth=%s" % out2["self_worth"])
    for i in range(1, 8):
        sw2 = record_incident_outcome(
            inner2, out2["concepts"], standard_met=False,
            attribution_locus="global_self")
        print("incident %d (standard_met=False, global_self): self_worth=%s" % (i, sw2))

    print()
    print("=" * 78)
    print("PREDICTION 3: a circumstance-attributed incident does NOT move it")
    print("=" * 78)
    s3 = sr.Substrate()
    inner3 = s3._inner
    ensure_can_seed(inner3)
    out3 = find_or_build_resident_can(inner3, CONFIDENT)
    before = out3["self_worth"]
    for i in range(5):
        record_incident_outcome(
            inner3, out3["concepts"], standard_met=False,
            attribution_locus="circumstance")
    after = inner3.node(out3["concepts"]["self_worth"])["attrs"]["state"]
    print("self_worth before 5 circumstance-attributed incidents:", before)
    print("self_worth after:                                     ", after)
    print("unchanged:", before == after)

    print()
    print("=" * 78)
    print("PREDICTION 4: the SAME resident, appraised twice, persists")
    print("=" * 78)
    s4 = sr.Substrate()
    inner4 = s4._inner
    ensure_can_seed(inner4)
    first = find_or_build_resident_can(inner4, CONFIDENT)
    for _ in range(4):
        record_incident_outcome(inner4, first["concepts"], standard_met=False,
                                attribution_locus="global_self")
    drifted_state = inner4.node(first["concepts"]["self_worth"])["attrs"]["state"]
    second = find_or_build_resident_can(inner4, CONFIDENT)
    print("is_new on second lookup:", second["is_new"])
    print("drifted self_worth:", drifted_state, " re-fetched self_worth:", second["self_worth"])
    print("same node:", first["concepts"]["self_worth"] == second["concepts"]["self_worth"])

    print()
    print("=" * 78)
    print("PREDICTION 5: drift changes the outcome of a LATER, otherwise")
    print("identical dispute")
    print("=" * 78)
    s5 = sr.Substrate()
    inner5 = s5._inner
    ensure_can_seed(inner5)
    for path in DISPUTE_SEED_PATHS:
        d = json.load(open(path))
        inner5.load_seed_manifest(engine_rules_only(d))
    resident5 = find_or_build_resident_can(inner5, CONFIDENT)

    def _run_same_dispute(label):
        current_self_worth = inner5.node(resident5["concepts"]["self_worth"])["attrs"]["state"]
        emotion = _appraise_dispute(
            inner5, issue_severity=0.9, band_code=0, witnesses=[0.0, 0.0, 0.0],
            held_self_worth=current_self_worth)
        print("%-45s self_worth=%s -> %s" % (label, current_self_worth, emotion))

    _run_same_dispute("before any incidents")
    for i in range(6):
        record_incident_outcome(inner5, resident5["concepts"], standard_met=False,
                                attribution_locus="global_self")
    _run_same_dispute("after 6 repeated failures")


if __name__ == "__main__":
    main()
