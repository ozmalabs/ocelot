"""jabberwock_grounds_or_escalates — THE CONFIDENT-WRONG-OUTSIDE-ITS-RANGE
GUARD, authored by the jabberwock, not hand-written.

THE THEORY (the creator's Graph Law): a cheap-model basin-snap that is
confidently WRONG has LOW residual within its own basin (it collapsed
cleanly onto a self-consistent local minimum), so residual alone cannot
distinguish it from a genuinely-correct collapse. What DOES distinguish them
is GROUNDING-REACHABILITY: does the collapse's grounding chain reach
something EXTERNAL to the agent's own generative loop (reality / a teacher /
an observed consequence / a sensor reading), or does it loop back into
itself? The guard: confident + low-residual BUT NOT grounding-reachable ->
don't trust it, escalate to ACTIVE cognition (the expensive, re-grounding
path) instead of the cheap snap.

THE SUBSTRATE (already built, commit 4fbf97b8, NOT touched here):
domains/grounding_reach.py — `ensure_grounding_edges` mints `grounded_in`
edges from existing signals (vision/audio perception, a real teacher
exchange, a judged Experiment outcome), `grounding_reach(node)` answers
reached/anchors/hops via the agent-installed native `ReachableFrom` Term,
and `flag_ungrounded_confident` mints a `GroundingGap` node for every
confident+low-residual+unreached node. That module only FLAGS.

THIS SCRIPT drives the RESPONSE, and the response is the agent's OWN
authored rule — never hand-written here:

  STEP 1 — try the EXISTING RelationCue vocabulary first (no new cue). A
  clause like ["ground","the","collapse","when","ungrounded"] is framed via
  induce_concern -> ground_concern; the result is an honest WALL
  (path=predicate_grounding, "the residual's predicates ground to NO held
  structural relation") — proven, not assumed, before touching any seed.

  STEP 2 — ONLY on that proven wall: ONE new RelationCue (`grounding_escalate`,
  seeds/relation_vocabulary.json) + ONE new ComposerCue (relation_head
  'escalate' -> composer 'grounding_guard', seeds/composer_dispatch.json) are
  the MINIMAL machinery added — vocabulary, not cognition.

  STEP 3 — the jabberwock AUTHORS the guard rule itself: framed as
  ["escalate","COLLAPSE","when","UNGROUNDED"], induce_concern mints a
  concern, ground_concern's composer dispatch resolves to the NEW
  'grounding_guard' composer, which mints `escalate_grounding_gap_<tag>`
  from the GRAPH-RESIDENT compose_grounding_guard_graph meta-rule (seeds/
  composer_grounding_guard_graph.json) — a Rule NODE the graph itself
  compiles and installs (`served_by` == 'graph'), not a Python function.

  The minted rule matches `agent -has_grounding_gap-> gap` (the mechanical
  exposure of an already-flagged GroundingGap —
  domains.reflective_faculty.ensure_grounding_gap_edges, the same
  trigger-wiring idiom induce_concern itself uses) and, instead of trusting
  the snap, mints an `Impasse{kind:'grounding_gap'}` + `agent -surprised_by->
  impasse` — REUSING the standing surprised_by/Impasse escalation channel
  (seeds/impasse_escalation.json, seeds/investigation_teacher.json,
  seeds/self_extension.json all use it to engage active cognition). When
  seeds/autonomy.json's ALREADY-SEEDED `mint_goal_from_surprise` is loaded
  too, it turns that edge into a wanted Goal on its own — this script does
  not reimplement "unexplained -> goal", it plugs a GroundingGap into that
  existing channel.

  THE DISCRIMINATIVE GATE: a confident+low-residual node grounded in a real
  anchor is NEVER flagged (flag_ungrounded_confident's own contract) so the
  authored rule never touches it — trust is the default. An ungrounded one
  IS flagged, IS escalated. And the residual-salience reconstruction: a
  SATURATED axis (residual~0, confidence high) with no live grounding is
  escalated (would have prevented the 2026-07-02 24x re-grind); the SAME
  shape axis grounded in a real judged Experiment (ConsequenceAnchor) is not.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_grounds_or_escalates.py
"""
from __future__ import annotations

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)


def _pass(ok: bool, label: str) -> bool:
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}")
    return ok


def main() -> bool:
    from substrate.world_adapter import WorldAdapter
    from substrate.seed_loader import manifest_for
    from domains.reflective_faculty import induce_concern, ground_concern, ensure_grounding_gap_edges
    from domains import grounding_reach as gr

    overall = True
    print("=" * 92)
    print("THE JABBERWOCK'S CONFIDENT-WRONG-OUTSIDE-ITS-RANGE GUARD — I only frame the concern")
    print("=" * 92)

    wa = WorldAdapter(seeds=())
    wa.inner.load_seed_manifest(manifest_for("relation_vocabulary"), wa.agent)
    wa.inner.load_seed_manifest(manifest_for("autonomy"), wa.agent)   # mint_goal_from_surprise lives here

    # -------------------------------------------------------------------
    # STEP 1 — try EXISTING vocabulary first. Expect an honest wall.
    # -------------------------------------------------------------------
    print("\n-- STEP 1: try the held RelationCue lexicon AS-IS (no new cue yet) --")
    probe = induce_concern(wa, [["ground", "the", "collapse", "when", "ungrounded"]],
                            name_hint="grounding_guard_wall_probe")
    wall = None
    if probe.get("minted"):
        wall = ground_concern(wa, [probe["capability_key"]])
    print(f"  induce_concern minted={probe.get('minted')}")
    print(f"  ground_concern -> grounded={wall.get('grounded') if wall else None} "
          f"path={wall.get('path') if wall else None}")
    print(f"  wall: {wall.get('wall') if wall else '(induce_concern itself did not mint)'}")
    overall &= _pass(wall is not None and wall.get("grounded") is False,
                      "existing vocabulary genuinely WALLS on the confident-but-ungrounded concern")

    # -------------------------------------------------------------------
    # STEP 2 — minimal new vocabulary already added (seeds/relation_vocabulary
    # .json's grounding_escalate cue + seeds/composer_dispatch.json's
    # 'escalate' ComposerCue). STEP 3 — drive the composer for real.
    # -------------------------------------------------------------------
    print("\n-- STEP 2+3: the NEW 'escalate' cue -> the jabberwock AUTHORS the guard rule --")
    ind = induce_concern(wa, [["escalate", "COLLAPSE", "when", "UNGROUNDED"]],
                          name_hint="grounding_guard_concern")
    overall &= _pass(ind.get("minted") is True, "induce_concern mints a genuine concern (no held shape covers it)")
    key = ind.get("capability_key")

    before_rules = wa.inner.rule_count()
    g = ground_concern(wa, [key])
    after_rules = wa.inner.rule_count()
    overall &= _pass(g.get("grounded") is True, f"ground_concern grounds the concern ({g.get('wall')})")
    overall &= _pass(g.get("served_by") == "graph", "AUTHORED via the graph-resident composer, not Python")
    overall &= _pass(after_rules - before_rules == 1, "exactly one guard rule minted")
    print("\n  THE AUTHORED RULE:")
    print(json.dumps(g.get("rule"), indent=2, sort_keys=True))

    # -------------------------------------------------------------------
    # GATE — build 4 scenarios and let the flag + the authored rule speak.
    # -------------------------------------------------------------------
    print("\n-- GATE: grounded -> trust; ungrounded -> escalate (discriminative) --")
    s = wa.s
    ag = wa.agent

    percept = s.add_node("VisionPercept", {})
    s._inner.add_edge_unchecked(ag, "perceives", percept)

    trusted = s.add_node("Collapse", {"residual": 0.01, "confidence": 0.97, "label": "trusted (SensorAnchor)"})
    s._inner.add_edge_unchecked(trusted, "grounded_in", percept)   # chains to the SensorAnchor below
    untrusted = s.add_node("Collapse", {"residual": 0.01, "confidence": 0.97, "label": "untrusted (no anchor)"})

    # the RESIDUAL-SALIENCE RECONSTRUCTION (seeds/residual_salience.json's
    # 24x re-grind incident): a saturated axis with no live grounding.
    axis_sat_ungrounded = s.add_node("CapabilityAxis", {
        "residual": 0.0, "confidence": 0.99, "saturation": 1.0, "label": "saturated, ungrounded"})
    run = s.add_node("Run", {"status": "done", "score": 12.0, "frames": 12.0})
    exp = s.add_node("Experiment", {"status": "requested", "outcome": "supported"})
    s._inner.add_edge_unchecked(exp, "produced", run)
    axis_sat_grounded = s.add_node("CapabilityAxis", {
        "residual": 0.0, "confidence": 0.99, "saturation": 1.0, "label": "saturated, grounded (ConsequenceAnchor)"})
    s._inner.add_edge_unchecked(axis_sat_grounded, "grounded_in", exp)

    gr.ensure_grounding_edges(wa)
    flagged = gr.flag_ungrounded_confident(wa, node_types=["Collapse", "CapabilityAxis"])
    wired = ensure_grounding_gap_edges(wa)
    wa.inner.run_rules(2000)

    gap_by_node = {}
    for gnode in s.nodes("GroundingGap"):
        gap_by_node[s.node(gnode)["attrs"]["node"]] = gnode

    def _verdict(node, label):
        gap = gap_by_node.get(node)
        escalated = False
        wants_goal = False
        if gap is not None:
            for mi in s.nodes("Impasse"):
                if s.has_edge(mi, "about_gap", gap):
                    escalated = s.has_edge(ag, "surprised_by", mi)
                    wants_goal = s.has_edge(ag, "wants", mi)
                    break
        print(f"  {label:38s} flagged={gap is not None!s:5s} escalated={escalated!s:5s} wants_goal={wants_goal!s:5s}")
        return gap is not None, escalated, wants_goal

    tf, te, tw = _verdict(trusted, "trusted (grounded)")
    uf, ue, uw = _verdict(untrusted, "untrusted (no anchor)")
    saf, sae, saw = _verdict(axis_sat_ungrounded, "saturated axis, ungrounded")
    sgf, sge, sgw = _verdict(axis_sat_grounded, "saturated axis, grounded")

    overall &= _pass(not tf and not te, "grounded node is NEVER flagged/escalated -- trust is the default")
    overall &= _pass(uf and ue and uw,
                      "ungrounded node IS flagged, escalated, AND becomes a wanted Goal (active cognition engaged)")
    overall &= _pass(saf and sae and saw,
                      "RECONSTRUCTED 24x re-grind: saturated+ungrounded axis escalated instead of silently trusted")
    overall &= _pass(not sgf and not sge,
                      "the SAME saturated shape, grounded in a real judged Experiment, is NOT escalated -- "
                      "grounding (not confidence/residual) gates trust")

    print("\n" + "=" * 92)
    print("OVERALL:", "PASS" if overall else "FAIL")
    print("=" * 92)
    return overall


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
