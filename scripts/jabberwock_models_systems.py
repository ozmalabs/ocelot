#!/usr/bin/env python3
"""jabberwock_models_systems -- standalone demonstrator + DISCRIMINATIVE gate
for `domains/system_model.py`: the generalisation of TIER 4
(`domains/collapse_model.py`'s `predict_collapse`) to an ARBITRARY TARGET
SYSTEM -- self, a subgraph, a foreign snapshot, or the agent's own
collapse-modelling machinery (TIER 5, `target="meta"`).

Mirrors `scripts/jabberwock_models_its_collapse.py`'s console-report shape.
Sections:

  1. SELF PARITY -- model_system(target=SELF) agrees EXACTLY with
     predict_collapse on an identically-constructed graph.

  2. OTHER (the headline generalisation) -- a genuinely FOREIGN toy system
     (its own nodes + its own graph-resident Rule, no relation to the
     agent's own graph) is modelled, DISCRIMINATIVELY: a CONVERGENT rule
     (fires once, then vetoes itself) -> converged=True; a DIVERGENT rule
     (ungated, refires its own persistent trigger edge every pass) ->
     converged=False. Grounded in the agent's own SensorAnchor-mediated
     OBSERVATION of the foreign system, never in the foreign system's own
     internal ground (the audience-model shape).

  3. META (TIER 5) -- model the model: predict_collapse (tier 4) -> model_
     system(target=META) (tier 5) -> model_system(target=META) again (the
     would-be tier 6). Shows the tower is CONVERGENT (n_volatile identical
     at every level) and that its fixed points include the frozen core AND
     each prior level's own SystemModel node (self-inclusion) -- the
     recursion terminates.

  4. TRACTABILITY -- model_system's own measured runtime for every target
     kind, on a real fixture -- report only, no pass/fail threshold.

  5. FROZEN CORE CHECK -- runs `scripts/jabberwock_frozen_core_check.py`'s
     `main()` in-process (a full 386-seed boot) to confirm building this
     module did not disturb the frozen-core safety invariant.

Exit code: 0 iff every discriminative expectation in sections 1-3 holds AND
section 5's frozen-core check passes. Section 4 is a report only.
"""
from __future__ import annotations

import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if p not in sys.path:
        sys.path.insert(0, p)

import substrate_rs as srs                                          # noqa: E402
from substrate.boot_core import boot_core                           # noqa: E402
from substrate.seed_loader import manifest_for                      # noqa: E402
from domains import reflective_faculty as rf                        # noqa: E402
from domains.collapse_model import predict_collapse                 # noqa: E402
from domains.system_model import META, SELF, model_system           # noqa: E402


def _hr(title: str) -> None:
    print("\n" + "=" * 78)
    print(title)
    print("=" * 78)


def _shape_decode_agent():
    s, ag = boot_core()
    native = rf._native_eval2(s)
    rf._ensure_shape_decode_loop(s, native, ag)
    return s, ag, native


def _add_pending_observation(s, ag, key: str):
    obs = s.add_node("Observation", {"signature": [[key, "X"]], "key": [key], "status": "pending"})
    s.add_edge(ag, "observed", obs)
    return obs


def _build_convergent_foreign_graph() -> dict:
    s = srs.Substrate()
    a = s.add_node("Anchor", {})
    b = s.add_node("Target", {"done": 0.0})
    s._inner.add_edge_unchecked(a, "trig", b)
    s.add_node("Rule", {
        "id": "converge_once",
        "match": [["a", "trig", "b"]],
        "where": {"type": "Lt", "a": {"type": "Attr", "node": {"type": "Var", "name": "b"}, "key": "done"},
                  "b": {"type": "Lit", "value": 0.5}},
        "effect": [["set_attr", "b", "done", 1.0]],
    })
    return s._inner.graph_to_dict()


def _build_divergent_foreign_graph() -> dict:
    s = srs.Substrate()
    a = s.add_node("Anchor", {})
    b = s.add_node("Target", {})
    s._inner.add_edge_unchecked(a, "trig", b)
    s.add_node("Rule", {
        "id": "diverge_always",
        "match": [["a", "trig", "b"]],
        "where": {"type": "Lit", "value": True},
        "effect": [["add_node", "x", "Thing", {}]],
    })
    return s._inner.graph_to_dict()


def main() -> int:
    ok_overall = True

    # -------------------------------------------------------------------
    _hr("1. SELF PARITY -- model_system(target=SELF) vs predict_collapse")

    def _mk():
        s, ag, _n = _shape_decode_agent()
        for i in range(3):
            _add_pending_observation(s, ag, f"zzzparity{i}")
        return s

    s_a = _mk()
    cm = predict_collapse(s_a, horizon=2, imagine_steps=2)
    s_b = _mk()
    sm = model_system(s_b, target=SELF, horizon=2, imagine_steps=2)
    print(f"predict_collapse:  converged={cm.converged} residual={cm.residual} "
          f"n_fixed={cm.n_fixed} n_volatile={cm.n_volatile} growth={cm.frontier_growth_rate}")
    print(f"model_system(SELF): converged={sm.converged} residual={sm.residual} "
          f"n_fixed={sm.n_fixed} n_volatile={sm.n_volatile} growth={sm.frontier_growth_rate}")
    ok1 = (sm.converged == cm.converged and sm.residual == cm.residual and sm.n_fixed == cm.n_fixed
           and sm.n_volatile == cm.n_volatile and sm.frontier_growth_rate == cm.frontier_growth_rate
           and sm.counts_trajectory == cm.counts_trajectory)
    print(f"expected: exact parity on every field: {ok1}")
    ok_overall = ok_overall and ok1

    # -------------------------------------------------------------------
    _hr("2. OTHER -- a genuinely FOREIGN system, discriminative + grounded")
    s2, ag2 = boot_core()
    conv = model_system(s2, target={"kind": "foreign_snapshot", "graph": _build_convergent_foreign_graph()},
                         horizon=3, imagine_steps=3)
    print(f"CONVERGENT foreign system: converged={conv.converged} growth={conv.frontier_growth_rate} "
          f"trajectory={conv.counts_trajectory} grounded={conv.grounded} anchors={conv.grounding.get('anchors')}")
    s3, ag3 = boot_core()
    div = model_system(s3, target={"kind": "foreign_snapshot", "graph": _build_divergent_foreign_graph()},
                        horizon=3, imagine_steps=3)
    print(f"DIVERGENT foreign system:  converged={div.converged} growth={div.frontier_growth_rate} "
          f"trajectory={div.counts_trajectory} grounded={div.grounded} anchors={div.grounding.get('anchors')}")
    ok2 = (conv.converged is True and div.converged is False and conv.grounded and div.grounded
           and "SensorAnchor" in conv.grounding.get("anchors", [])
           and "SensorAnchor" in div.grounding.get("anchors", []))
    print(f"expected: convergent->True, divergent->False, both grounded via SensorAnchor observation: {ok2}")
    print("(THE HEADLINE: the SAME faculty pointed at a system that is NOT the agent's self -- "
          "the target's own toy Rule dynamics, grounded in the agent's OBSERVATION of it, never in "
          "the foreign system's own internal ground -- the audience-model shape)")
    ok_overall = ok_overall and ok2

    # -------------------------------------------------------------------
    _hr("3. TIER 5 -- model the model; the tower converges, not explodes")
    s4, ag4 = boot_core()
    s4._inner.load_seed_manifest(manifest_for("relation_vocabulary"), ag4)
    s4._inner.load_seed_manifest(manifest_for("autonomy"), ag4)
    tier4 = predict_collapse(s4)
    tier5 = model_system(s4, target=META)
    tier6 = model_system(s4, target=META)
    print(f"tier4 (predict_collapse):        n_fixed={tier4.n_fixed} n_volatile={tier4.n_volatile}")
    print(f"tier5 (model_system META):       n_fixed={tier5.n_fixed} n_volatile={tier5.n_volatile}")
    print(f"tier6 (model_system META again): n_fixed={tier6.n_fixed} n_volatile={tier6.n_volatile}")
    frozen_present = bool(tier5.fixed_points.get("frozen_drive")) and bool(tier6.fixed_points.get("frozen_drive"))
    self_included = tier5.model_node in tier6.fixed_points.get("settled_system_model", [])
    no_growth = (tier5.n_volatile == tier4.n_volatile == tier6.n_volatile)
    ok3 = frozen_present and self_included and no_growth
    print(f"frozen core present at tier5 AND tier6: {frozen_present}")
    print(f"tier5's own SystemModel node is a settled fixed point of tier6: {self_included}")
    print(f"n_volatile identical across the whole tower (no growth): {no_growth}")
    print(f"expected: all three True -- the tower TERMINATES: {ok3}")
    ok_overall = ok_overall and ok3

    # -------------------------------------------------------------------
    _hr("4. TRACTABILITY -- model_system's own measured runtime per target kind")
    s5, ag5, native5 = _shape_decode_agent()
    for i in range(3):
        _add_pending_observation(s5, ag5, f"zzztiming{i}")
    timings = {}
    for label, target in (
        ("self", SELF),
        ("meta", META),
        ("subgraph", {"kind": "subgraph", "types": ["Observation"]}),
        ("foreign_snapshot", {"kind": "foreign_snapshot", "graph": _build_divergent_foreign_graph()}),
    ):
        t0 = time.time()
        r = model_system(s5, target=target, horizon=3, imagine_steps=2)
        dt = time.time() - t0
        timings[label] = dt
        print(f"  target={label:<18} wall={dt:.4f}s  self_reported={r.runtime_s:.4f}s  "
              f"node_count={r.node_count}")
    print("all target kinds are bounded by the TARGET's own node-set size (or, for SELF/META, the "
          "SAME O(tracked-types) proxy predict_collapse already uses) -- not by the live graph's "
          "total size (report only, no gate).")

    # -------------------------------------------------------------------
    _hr("5. FROZEN CORE INTACT (full 386-seed boot check, in-process)")
    from scripts.jabberwock_frozen_core_check import main as frozen_core_main
    fc_rc = frozen_core_main()
    ok5 = fc_rc == 0
    print(f"jabberwock_frozen_core_check.main() exit code: {fc_rc} (expected 0): {ok5}")
    ok_overall = ok_overall and ok5

    # -------------------------------------------------------------------
    _hr("SUMMARY")
    print(f"1 (self parity):                          {ok1}")
    print(f"2 (other -- discriminative + grounded -- THE HEADLINE): {ok2}")
    print(f"3 (tier-5 tower terminates):               {ok3}")
    print(f"4 (tractable):                             report only")
    print(f"5 (frozen core intact):                    {ok5}")
    print(f"\nALL DISCRIMINATIVE EXPECTATIONS HOLD: {ok_overall}")
    return 0 if ok_overall else 1


if __name__ == "__main__":
    raise SystemExit(main())
