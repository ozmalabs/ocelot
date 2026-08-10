"""Gates for BLOCK 229000 — OBSERVE-AND-GROUND remote causality (the 228 correction).

The agent interacts for real, OBSERVES the actual before->after remote change
(perception), and MINTS a persistent grounded causes(cross,rotation) fact FROM the
observed effect — refusing when the NATURAL TIMELINE shows the remote thing changing
without interaction (coincidence). NOT a simulated counterfactual. The grounded fact
PERSISTS and is USABLE (the agent reads it and acts). Every decision is a graph rule;
the grounding is mechanical perception -> graph write.
"""
import json
import os
import sys

import numpy as np

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (_ROOT, os.path.join(_ROOT, "scripts"), os.path.join(_ROOT, "runners", "dsl", "python")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from worlds.remote_causal_ground import (  # noqa: E402
    make_scenario, natural_timeline, run_ground_vignette, correct_ground_verdict,
    run_knows_and_acts_episode, GroundPlanner, observe_change,
)
from domains.remote_causal_ground_seed import RULES, manifest  # noqa: E402
from domains import remote_causal_ground_seed as seedmod  # noqa: E402
from substrate.boot_core import boot_core  # noqa: E402
from domains import reflective_faculty as rf  # noqa: E402


def _pair_rate(arm, n=12, seed=229000):
    rng = np.random.default_rng(seed)
    hits = 0
    for _ in range(n):
        scnA = make_scenario(rng, "A")
        scnB = make_scenario(rng, "B")
        tlA = natural_timeline(rng, scnA["cause_id"])
        tlB = natural_timeline(rng, scnB["cause_id"])
        okA = correct_ground_verdict(run_ground_vignette(rng, scnA["truth"], scnA["objects"], arm, tlA),
                                     "A", scnA["truth"])
        okB = correct_ground_verdict(run_ground_vignette(rng, scnB["truth"], scnB["objects"], arm, tlB),
                                     "B", scnB["truth"])
        hits += int(okA and okB)
    return hits / n


# --------------------------------------------------------------------------
# G-observe-and-ground (HEADLINE)
# --------------------------------------------------------------------------
def test_observe_grounds_and_controls_do_not():
    assert _pair_rate("observe") == 1.0
    assert _pair_rate("no_natural_timeline") == 0.0   # confabulates on Family B
    assert _pair_rate("blind") == 0.0                 # never observes -> misses Family A


def test_grounded_fact_absent_before_present_after_and_persists():
    rng = np.random.default_rng(229001)
    scn = make_scenario(rng, "A")
    tl = natural_timeline(rng, scn["cause_id"])
    res = run_ground_vignette(rng, scn["truth"], scn["objects"], "observe", tl)
    assert res["grounded_before"] == 0            # absent before
    assert res["grounded_after"] >= 1             # present after
    assert any(f["effect"] == "rotation" for f in res["facts"])
    assert res["causes_edges"] == [("cross", "rotation")]  # the causes(cross,rotation) edge


def test_grounding_persists_and_is_mint_once():
    rng = np.random.default_rng(229002)
    scn = make_scenario(rng, "A")
    tl = natural_timeline(rng, scn["cause_id"])
    pl = GroundPlanner("observe", scn["objects"])
    # observe a clean natural timeline + a real interact->change
    pl.add_observation(interact=0.0, remote_changed=0.0, cause_id="", effect_kind="none")
    pl.add_observation(interact=1.0, remote_changed=1.0, cause_id=scn["cause_id"], effect_kind="rotation")
    pl.step_decide()
    assert len(pl.facts()) == 1
    # re-run: it PERSISTS and is NOT re-minted (mint-once)
    pl.step_decide()
    pl.step_decide()
    assert len(pl.facts()) == 1


# --------------------------------------------------------------------------
# G-grounded-from-observation-not-simulation (the correction)
# --------------------------------------------------------------------------
def test_grounding_refuses_when_natural_timeline_shows_spontaneous_change():
    """The natural-timeline no-op is REAL negative evidence: a distal change observed
    WITHOUT interaction refutes the link (coincidence)."""
    pl = GroundPlanner("observe", [{"obj_id": "cross", "r": 3.0, "c": 3.0}])
    pl.add_observation(interact=0.0, remote_changed=1.0, cause_id="", effect_kind="rotation")  # spontaneous
    pl.add_observation(interact=1.0, remote_changed=1.0, cause_id="cross", effect_kind="rotation")  # coincidence
    pl.step_decide()
    assert pl.facts() == []


def test_grounding_reads_observed_not_simulated_source_audit():
    """SOURCE AUDIT: the grounding rule reads Observation.remote_changed (OBSERVED) +
    the natural-timeline no-op (Not Exists over Observations), NEVER eff_act/eff_noop
    (the 228 SIMULATED counterfactual keys)."""
    def keys(node, out):
        if isinstance(node, dict):
            for k, v in node.items():
                if k == "key" and isinstance(v, str):
                    out.append(v)
                keys(v, out)
        elif isinstance(node, list):
            for v in node:
                keys(v, out)
    ground = next(r for r in RULES if r["name"] == "rcg_ground")
    ks = []
    keys(ground["where"], ks); keys(ground["effects"], ks)
    assert "remote_changed" in ks and "interact" in ks
    assert "eff_act" not in ks and "eff_noop" not in ks
    wj = json.dumps(ground["where"])
    assert '"Not"' in wj and '"Exists"' in wj and '"has_obs"' in wj  # the natural-timeline no-op


def test_observe_change_is_a_real_before_after_diff():
    """observe_change is a REAL perception op: it returns rotation iff AFTER == rot90(BEFORE)."""
    before = np.zeros((4, 4), dtype=np.int32); before[0, :3] = 1; before[:2, 0] = 1
    changed, kind = observe_change(before, np.rot90(before))
    assert changed == 1.0 and kind == "rotation"
    changed, kind = observe_change(before, before)
    assert changed == 0.0 and kind == "none"


# --------------------------------------------------------------------------
# G-knows-and-acts
# --------------------------------------------------------------------------
def test_grounded_fact_is_usable_agent_acts():
    rng = np.random.default_rng(229003)
    scn = make_scenario(rng, "A")
    tl = natural_timeline(rng, scn["cause_id"])
    r_obs = run_knows_and_acts_episode(rng, scn["truth"], scn["objects"], "observe", tl, block_rc=(3, 3))
    assert r_obs["grounded"] and r_obs["win"]


def test_without_grounded_fact_agent_cannot_act():
    rng = np.random.default_rng(229004)
    scn = make_scenario(rng, "A")
    tl = natural_timeline(rng, scn["cause_id"])
    r_blind = run_knows_and_acts_episode(rng, scn["truth"], scn["objects"], "blind", tl, block_rc=(3, 3))
    assert not r_blind["grounded"] and not r_blind["win"]


# --------------------------------------------------------------------------
# G-graph-native / discipline
# --------------------------------------------------------------------------
def test_source_audit_no_domain_tokens_in_logic():
    banned = ("cross", "rotation", "rotate", "ls20", "doom", "lever", "door", "shape")

    def lits(node, out):
        if isinstance(node, dict):
            if node.get("type") == "Lit":
                out.append(node.get("value"))
            for v in node.values():
                lits(v, out)
        elif isinstance(node, list):
            for v in node:
                lits(v, out)
    for r in RULES:
        got = []
        lits(r.get("where", {}), got); lits(r.get("effects", []), got)
        for L in got:
            assert not (isinstance(L, str) and L.lower() in banned), (r["name"], L)


def test_every_rule_guarded_on_ground_on():
    for r in RULES:
        assert "ground_on" in json.dumps(r["where"]), r["name"]


def test_default_off_no_rule_fires():
    s, ag = boot_core()
    n = rf._native_eval2(s)
    for r in RULES:
        n.add_rule(r)
    g = s.add_node("Game", {"arm": "observe", "symbol_matches_goal": 0.0})  # NO ground_on
    p = s.add_node("Ping", {}); n.add_edge_unchecked(g, "has_ping", p)
    o = s.add_node("SalientObject", {"obj_id": "cross", "r": 5.0, "c": 5.0})
    n.add_edge_unchecked(g, "has_object", o)
    obs = s.add_node("Observation", {"interact": 1.0, "remote_changed": 1.0,
                                     "cause_id": "cross", "effect_kind": "rotation"})
    n.add_edge_unchecked(g, "has_obs", obs)
    n.run_rules()
    assert list(s.neighbours(g, "has_causal_fact")) == []
    assert (s.node(g)["attrs"].get("waypoint") or "") == ""


def test_seed_roundtrips_source_match():
    built = manifest()
    onfile = json.load(open(os.path.join(_ROOT, "seeds", "remote_causal_ground.json")))
    assert json.dumps(built, sort_keys=True) == json.dumps(onfile, sort_keys=True)


def test_manifest_shape():
    m = manifest()
    assert m["id"] == "remote_causal_ground" and m["version"] == "1.0.0"
    names = {r["name"] for r in m["rules"]}
    assert {"rcg_ground", "rcg_knows_and_acts", "rcg_pass"} <= names
