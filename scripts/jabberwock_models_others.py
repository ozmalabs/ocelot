#!/usr/bin/env python3
"""jabberwock_models_others -- TIER 5 SYSTEM-MODEL COGNITION gate, console
form.

Companion to tests/test_system_model_cognition.py (the fast pytest
regression this script's assertions mirror). Demonstrates, on real booted
agents, that `domains/system_model.py`'s `SystemModel` (the generalisation
of TIER 4's `CollapseModel` from SELF to an ARBITRARY target: self /
subgraph / foreign_snapshot / meta) is now a COGNITIVE FACULTY the agent
USES, not just a measurement a host prints: two rules the agent AUTHORS
ITSELF via the composer (`ground_concern([..., "regard", ...])` -> `seeds/
composer_system_model_graph.json`'s meta-rule) --

  1. model_other_belief_<tag>            -- the AUDIENCE-MODEL/theory-of-mind
                                             shape: a GROUNDED model of a
                                             FOREIGN system predicted to
                                             diverge forms a Belief the other
                                             is diverging; an ungrounded or
                                             convergent model never does
  2. recognize_modeling_terminates_<tag> -- TIER-5 REFLEXIVE SELF-RECOGNITION,
                                             one level up from TIER 4's own
                                             recognize_self_<tag>: a model of
                                             the agent's OWN modelling
                                             machinery (target_kind:"meta")
                                             recognises its termination
                                             anchors (settled_system_model /
                                             frozen_drive) WITHOUT ever
                                             mutating them

`domains/system_model_dispatch.py:scan_and_model` is the ONLY host-side call
this script makes beyond graph I/O -- the mechanical hook that calls
`domains.system_model.model_system` (chains predict_collapse / imagine /
grounding_reach, all in-process Python that cannot execute inside a Rust
rule effect) for every pending `ModelRequest` and wires `agent
-has_system_model-> model` so the agent's own rules have something to match.
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import substrate_rs as srs                                 # noqa: E402
from substrate.boot_core import boot_core                  # noqa: E402
from substrate.seed_loader import manifest_for              # noqa: E402
import domains.reflective_faculty as rf                     # noqa: E402
from domains import system_model_dispatch as smd            # noqa: E402
from domains.system_model import META                       # noqa: E402


class _Agent:
    def __init__(self, s, agent_node):
        self.s = s
        self.inner = s._inner
        self.agent = agent_node


def _fresh_agent() -> _Agent:
    s, agent_node = boot_core()
    ag = _Agent(s, agent_node)
    ag.s._inner.load_seed_manifest(manifest_for("relation_vocabulary"), ag.agent)
    ag.s._inner.load_seed_manifest(manifest_for("composer_dispatch"), ag.agent)
    ag.s._inner.load_seed_manifest(manifest_for("autonomy"), ag.agent)
    return ag


def _ground(ag, cue_clause, name_hint):
    ind = rf.induce_concern(ag, [cue_clause], name_hint=name_hint)
    assert ind.get("minted") is True, ind
    g = rf.ground_concern(ag, [ind["capability_key"]])
    assert g.get("grounded") is True and g.get("served_by") == "graph", g
    return g


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
    print("=" * 78)
    print("TIER 5 -- the graph models ANOTHER system, and its own modelling, "
          "graph-authored (CLAUDE.md)")
    print("=" * 78)

    # ---- THE AGENT AUTHORS THE TWO RULES -----------------------------------
    print("\n--- THE JABBERWOCK AUTHORS model_other_belief / "
          "recognize_modeling_terminates ---")
    ag = _fresh_agent()
    g = _ground(ag, ["regard", "OTHER", "SYSTEM"], "system_model_demo")
    print(f"AUTHORED (system_model): path={g['path']}  served_by={g['served_by']}")
    for r in g["rules"]:
        print(f"\n  RULE {r['name']!r}")
        print(f"    match : {r['match']}")
        print(f"    where : {r['where']}")
        print(f"    effect: {r['effects']}")

    # ---- MODEL-ANOTHER-SYSTEM: divergent, grounded -> belief ---------------
    print("\n--- MODEL-ANOTHER-SYSTEM: grounded + DIVERGENT foreign system ---")
    ag_div = _fresh_agent()
    _ground(ag_div, ["regard", "OTHER", "SYSTEM"], "sm_div")
    smd.mint_model_request(ag_div, {"kind": "foreign_snapshot", "graph": _build_divergent_foreign_graph()})
    res_div = smd.scan_and_model(ag_div, horizon=3, imagine_steps=3)[0]
    print(f"SystemModel: target_kind={res_div.target_kind}  converged={res_div.converged}  "
          f"grounded={res_div.grounded}  frontier_growth_rate={res_div.frontier_growth_rate}")
    assert res_div.converged is False and res_div.grounded is True
    ag_div.inner.run_rules(2000)
    beliefs_div = [n for n in ag_div.s.nodes("Belief") if ag_div.s.node(n)["attrs"].get("kind") == "other_diverging"]
    print(f"Belief{{kind:other_diverging}} formed: {len(beliefs_div)} (must be >= 1)")
    assert beliefs_div
    assert ag_div.s.has_edge(ag_div.agent, "expects", beliefs_div[0])
    assert ag_div.s.has_edge(beliefs_div[0], "about_model", res_div.model_node)

    # ---- MODEL-ANOTHER-SYSTEM: convergent, grounded -> no belief -----------
    print("\n--- MODEL-ANOTHER-SYSTEM: grounded + CONVERGENT foreign system (control) ---")
    ag_conv = _fresh_agent()
    _ground(ag_conv, ["regard", "OTHER", "SYSTEM"], "sm_conv")
    smd.mint_model_request(ag_conv, {"kind": "foreign_snapshot", "graph": _build_convergent_foreign_graph()})
    res_conv = smd.scan_and_model(ag_conv, horizon=3, imagine_steps=3)[0]
    print(f"SystemModel: target_kind={res_conv.target_kind}  converged={res_conv.converged}  "
          f"grounded={res_conv.grounded}")
    assert res_conv.converged is True and res_conv.grounded is True
    ag_conv.inner.run_rules(2000)
    beliefs_conv = [n for n in ag_conv.s.nodes("Belief") if ag_conv.s.node(n)["attrs"].get("kind") == "other_diverging"]
    print(f"Belief{{kind:other_diverging}} formed: {len(beliefs_conv)} (must be 0 -- discriminative)")
    assert beliefs_conv == []

    # ---- MODEL-ANOTHER-SYSTEM: ungrounded -> not trusted --------------------
    print("\n--- MODEL-ANOTHER-SYSTEM: DIVERGENT but UNGROUNDED (control) ---")
    ag_ung = _fresh_agent()
    _ground(ag_ung, ["regard", "OTHER", "SYSTEM"], "sm_ung")
    sm_ung = ag_ung.s.add_node("SystemModel", {
        "target_kind": "foreign_snapshot", "target_id": "ungrounded_probe",
        "converged": False, "residual": 1.0, "grounded": False,
    })
    ag_ung.s.add_edge(ag_ung.agent, "has_system_model", sm_ung)
    ag_ung.inner.run_rules(2000)
    beliefs_ung = [n for n in ag_ung.s.nodes("Belief") if ag_ung.s.node(n)["attrs"].get("kind") == "other_diverging"]
    print(f"Belief{{kind:other_diverging}} formed on an UNGROUNDED divergent model: {len(beliefs_ung)} "
          f"(must be 0 -- 'I only trust what I observed')")
    assert beliefs_ung == []

    # ---- REASON-OVER-OWN-MODELING (TIER 5) ----------------------------------
    print("\n--- REASON-OVER-OWN-MODELING: SystemModel{target_kind:'meta'} ---")
    ag_meta = _fresh_agent()
    _ground(ag_meta, ["regard", "OTHER", "SYSTEM"], "sm_meta")
    smd.mint_model_request(ag_meta, META)
    res_meta = smd.scan_and_model(ag_meta)[0]
    print(f"SystemModel: target_kind={res_meta.target_kind}  "
          f"fixed_points categories={sorted(res_meta.fixed_points.keys())}")
    assert res_meta.target_kind == "meta"
    assert res_meta.fixed_points.get("frozen_drive"), "the frozen 'understand' Drive must be a fixed point"
    ag_meta.inner.run_rules(2000)
    fixed_ids = set(ag_meta.inner.neighbours(res_meta.model_node, "fixed_point"))
    recognized = set(ag_meta.inner.neighbours(ag_meta.agent, "recognizes_modeling_terminates"))
    print(f"fixed_point sample={len(fixed_ids)}  recognized (termination anchors)={len(recognized)}  "
          f"fixed<=recognized: {fixed_ids <= recognized}")
    assert fixed_ids and fixed_ids <= recognized
    drives = {n for n in fixed_ids if ag_meta.s.node(n)["type"] == "Drive"}
    print(f"the frozen 'understand' Drive is among the recognised termination anchors: {bool(drives)}")
    assert drives
    before = dict(ag_meta.s.node(next(iter(drives)))["attrs"])
    ag_meta.inner.run_rules(2000)
    after = dict(ag_meta.s.node(next(iter(drives)))["attrs"])
    print(f"frozen Drive attrs unchanged by recognize_modeling_terminates: {before == after}")
    assert before == after

    # ---- REASON-OVER-OWN-MODELING: non-meta control (discriminative) -------
    print("\n--- REASON-OVER-OWN-MODELING: a non-meta SystemModel never triggers it (control) ---")
    recognized_ctrl = list(ag_div.inner.neighbours(ag_div.agent, "recognizes_modeling_terminates"))
    print(f"recognizes_modeling_terminates edges on the foreign_snapshot agent: {len(recognized_ctrl)} "
          f"(must be 0)")
    assert recognized_ctrl == []

    print("\n" + "=" * 78)
    print("PASS -- tier 5 is a cognitive faculty: the agent forms a trusted "
          "belief about ANOTHER system only when its model of it is grounded "
          "AND predicted to diverge, and reflexively recognises its own "
          "modelling-of-modelling as well-founded (terminates at the frozen "
          "core), never confusing the two, never mutating what it recognises.")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    sys.exit(main())
