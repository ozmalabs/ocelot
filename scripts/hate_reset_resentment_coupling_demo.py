"""Live demo of HATE_RESET_RESENTMENT_COUPLING_PREREG.md -- prints the 4
registered predictions. Output pasted verbatim into the paired RESULTS
doc.
"""
import json

import substrate_rs as sr
from substrate.seed_loader import engine_rules_only

from domains.can_self_worth_bridge import ensure_can_seed
from domains.hate_attribution import mint_target_pattern, record_hate_incident


def fresh(name):
    s = sr.Substrate()
    inner = s._inner
    ensure_can_seed(inner)
    for seed_path in ("seeds/shared_arousal.json", "seeds/hate_attribution.json"):
        d = json.load(open(seed_path))
        inner.load_seed_manifest(engine_rules_only(d))
    mt = inner.add_node("Microtheory", {"name": name, "temperature": 1.5})
    return inner, mt


print("=== Prediction 1: at zero arousal, specific_act is still an exact full reset ===")
inner, mt = fresh("mt1")
pat = mint_target_pattern(inner, mt, "Alex")
ir = inner.add_node("IncidentReport", {"target": "Alex", "signal": 1.0, "status": "pending"})
inner.add_edge(mt, "has_incident_report", ir, {})
inner.add_edge(ir, "about_pattern", pat, {})
inner.set_attr(pat, "confirm_streak", 5.0)
inner.set_attr(pat, "incident_count", 1)
arousal_node = next(iter(inner.neighbours(pat, "tracks_arousal")))
inner.set_attr(arousal_node, "level", 0.0)
inner.force_all_dirty()
inner.run_rules(3000)
print("staged streak=5.0, arousal=0.0 -> post-exception streak=%.4f"
      % inner.node(pat)["attrs"]["confirm_streak"])

print()
print("=== Prediction 2: elevated arousal leaves a strictly positive residue ===")
inner2, mt2 = fresh("mt2")
pat2 = mint_target_pattern(inner2, mt2, "Alex")
ir2 = inner2.add_node("IncidentReport", {"target": "Alex", "signal": 1.0, "status": "pending"})
inner2.add_edge(mt2, "has_incident_report", ir2, {})
inner2.add_edge(ir2, "about_pattern", pat2, {})
inner2.set_attr(pat2, "confirm_streak", 5.0)
inner2.set_attr(pat2, "incident_count", 1)
arousal_node2 = next(iter(inner2.neighbours(pat2, "tracks_arousal")))
inner2.set_attr(arousal_node2, "level", 1.0)
inner2.force_all_dirty()
inner2.run_rules(3000)
print("staged streak=5.0, arousal=1.0 (retained_fraction=0.5) -> post-exception streak=%.4f"
      % inner2.node(pat2)["attrs"]["confirm_streak"])

print()
print("=== Prediction 3: the residue matches the formula exactly, live ===")
inner3, mt3 = fresh("mt3")
pat3 = mint_target_pattern(inner3, mt3, "Alex")
r0 = record_hate_incident(inner3, mt3, pat3, negative=True)
r_confirm = record_hate_incident(inner3, mt3, pat3, negative=True)
r_exception = record_hate_incident(inner3, mt3, pat3, negative=False)
expected = r_confirm["confirm_streak"] * (r_confirm["arousal_level"] / (1.0 + r_confirm["arousal_level"]))
print("pre-exception streak=%.4f arousal=%.4f -> residue=%.4f (expected %.4f)"
      % (r_confirm["confirm_streak"], r_confirm["arousal_level"],
         r_exception["confirm_streak"], expected))

print()
print("=== Prediction 4: resented streak stays ahead of forgiven streak at a matched step ===")


def run(hot_level):
    inner_r, mt_r = fresh("mt_run_%s" % hot_level)
    pat_r = mint_target_pattern(inner_r, mt_r, "Alex")
    inner_r.set_attr(pat_r, "confirm_streak", 1.0)
    inner_r.set_attr(pat_r, "incident_count", 1)
    regard = next(iter(inner_r.neighbours(pat_r, "tracks_concept")))
    inner_r.set_attr(regard, "external_field", -2.0)
    arousal_node_r = next(iter(inner_r.neighbours(pat_r, "tracks_arousal")))
    inner_r.set_attr(arousal_node_r, "level", hot_level)
    r_exc = record_hate_incident(inner_r, mt_r, pat_r, negative=False)
    r_confirm = record_hate_incident(inner_r, mt_r, pat_r, negative=True)
    return r_exc["confirm_streak"], r_confirm["confirm_streak"]


hot_residue, hot_after = run(hot_level=1.0)
cold_residue, cold_after = run(hot_level=0.0)
print("hot (arousal=1.0 at exception): residue=%.4f -> streak after resumed confirmation=%.4f"
      % (hot_residue, hot_after))
print("cold (arousal=0.0 at exception): residue=%.4f -> streak after resumed confirmation=%.4f"
      % (cold_residue, cold_after))
