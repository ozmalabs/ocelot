"""Gates for BLOCK 230000 — PERFORM THE ACTION ON THE CROSS (exhaust the ACTION
space on the reached object; DISCOVER the actuating action).

The owner insight: 229 REACHED and "interacted with" the cross but observed 0 distal
change, because "interacted" meant co-located / bumped — the agent never issued the
game's ACTION (use/select) ON the cross. This block EXTENDS the 226/228 exhaustion
principle from the OBJECT space to the ACTION space: at the reached object, try EVERY
available action ON it — the movement actions AND the interact/use action — and
DISCOVER which one actuates it by OBSERVING which produces a remote change. The
elicited change flows into 229's rcg_ground. Discovered, not hardcoded. Every
decision is a graph rule; the adapter only issues the chosen action and perceives.
"""
import json
import os
import sys

import numpy as np

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (_ROOT, os.path.join(_ROOT, "scripts"), os.path.join(_ROOT, "runners", "dsl", "python")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from worlds.remote_operate import (  # noqa: E402
    run_operate_vignette, correct_discover_verdict, correct_ground_verdict,
    run_operate_pass_episode, full_action_space, OperatePlanner, OperateWorld,
    exhaust_action_space, observe_change, MOVEMENTS, INTERACTS,
)
from domains.remote_operate_seed import RULES, manifest  # noqa: E402
from substrate.boot_core import boot_core  # noqa: E402
from domains import reflective_faculty as rf  # noqa: E402


def _pair_discover_rate(policy, n=12, seed=230000):
    rng = np.random.default_rng(seed)
    acts = full_action_space()
    hits = 0
    for _ in range(n):
        rA = run_operate_vignette(rng, "A", policy, acts)
        rB = run_operate_vignette(rng, "B", policy, acts)
        hits += int(correct_discover_verdict(rA, "A") and correct_discover_verdict(rB, "B"))
    return hits / n


# --------------------------------------------------------------------------
# G-discover-operate-action (HEADLINE)
# --------------------------------------------------------------------------
def test_exhaust_actions_discovers_operate_control_does_not():
    assert _pair_discover_rate("exhaust_actions") == 1.0    # discovers the actuator (A) + refuses (B)
    assert _pair_discover_rate("movement_only") == 0.0      # never issues use -> never discovers on A


def test_discovered_action_is_the_true_operate_action_and_non_movement():
    """The DISCOVERED action equals the world's true actuator (randomized per
    scenario) AND is a non-movement (interact/use) action — discovered, not hardcoded."""
    rng = np.random.default_rng(230001)
    acts = full_action_space()
    for _ in range(20):
        r = run_operate_vignette(rng, "A", "exhaust_actions", acts)
        assert r["discovered"]
        assert r["operate_action"] == r["true_operate_action"]
        assert r["true_operate_action"] in INTERACTS
        assert r["discovered_is_movement"] == 0.0
        assert r["operates_edges"] == [{"action": r["true_operate_action"],
                                        "object": "cross", "effect": "rotation"}]


def test_discovery_refuses_when_no_action_actuates():
    """Family B (inert object / triggered elsewhere): exhausting the whole action
    space produces NO remote change -> the agent discovers NOTHING (refuses)."""
    rng = np.random.default_rng(230002)
    r = run_operate_vignette(rng, "B", "exhaust_actions", full_action_space())
    assert not r["discovered"] and r["operates_edges"] == []
    assert r["issued_a_non_movement"]  # it DID try the non-movement action (just nothing happened)


# --------------------------------------------------------------------------
# G-exhaust-actions — "tried everything" includes the non-movement interact action
# --------------------------------------------------------------------------
def test_exhaust_actions_issues_the_non_movement_action_control_never_does():
    rng = np.random.default_rng(230003)
    acts = full_action_space()
    rE = run_operate_vignette(rng, "A", "exhaust_actions", acts)
    rM = run_operate_vignette(rng, "A", "movement_only", acts)
    # exhaust_actions tries the interact/use action AT the object; movement_only never does
    assert rE["issued_a_non_movement"] is True
    assert rM["issued_a_non_movement"] is False
    assert set(rM["issued_actions"]) <= set(MOVEMENTS)     # control: movements only


def test_exhaustion_covers_the_full_action_space_in_order():
    """The exhaustion tries every available action in ordinal order until it discovers
    the actuator (Family B, where nothing actuates, covers ALL of them)."""
    rng = np.random.default_rng(230004)
    r = run_operate_vignette(rng, "B", "exhaust_actions", full_action_space())
    assert r["issued_actions"] == MOVEMENTS + INTERACTS   # all six, in order


# --------------------------------------------------------------------------
# G-elicits-and-grounds (composes with 229) + G-pass
# --------------------------------------------------------------------------
def test_discovered_operate_elicits_change_that_229_grounds():
    rng = np.random.default_rng(230005)
    r = run_operate_vignette(rng, "A", "exhaust_actions", full_action_space())
    assert r["discovered"] and r["grounded"]
    assert any(f["status"] == "grounded" and f["effect"] == "rotation" for f in r["facts"])


def test_movement_only_never_grounds():
    rng = np.random.default_rng(230006)
    r = run_operate_vignette(rng, "A", "movement_only", full_action_space())
    assert not r["grounded"] and r["facts"] == []


def test_exhaust_actions_passes_movement_only_cannot():
    rng = np.random.default_rng(230007)
    acts = full_action_space()
    rE = run_operate_pass_episode(rng, "exhaust_actions", acts, obj_rc=(3, 3), block_rc=(6, 6))
    rM = run_operate_pass_episode(rng, "movement_only", acts, obj_rc=(3, 3), block_rc=(6, 6))
    assert rE["discovered"] and rE["grounded"] and rE["win"]
    assert (not rM["discovered"]) and (not rM["grounded"]) and (not rM["win"])


# --------------------------------------------------------------------------
# G-graph-native / source-audit
# --------------------------------------------------------------------------
def test_discover_rule_reads_observed_outcome_not_hardcoded_action_id():
    """The discover rule reads the OBSERVED remote_changed + joins the action id as a
    Var attr; it names NO Lit action id and does NOT read is_movement (the actuator is
    discovered from the observed change, not its kind)."""
    def keys(node, out):
        if isinstance(node, dict):
            for k, v in node.items():
                if k == "key" and isinstance(v, str):
                    out.append(v)
                keys(v, out)
        elif isinstance(node, list):
            for v in node:
                keys(v, out)

    def lits(node, out):
        if isinstance(node, dict):
            if node.get("type") == "Lit":
                out.append(node.get("value"))
            for v in node.values():
                lits(v, out)
        elif isinstance(node, list):
            for v in node:
                lits(v, out)
    disc = next(r for r in RULES if r["name"] == "ro_discover_operate")
    ks = []
    keys(disc["where"], ks)
    assert "remote_changed" in ks and "action_id" in ks
    assert "is_movement" not in ks              # discovery is observation-driven, not kind-driven
    got = []
    lits(disc["where"], got); lits(disc["effects"], got)
    action_ids = {"action1", "action2", "action3", "action4", "action5", "action6", "action7"}
    for L in got:
        assert not (isinstance(L, str) and L.lower() in action_ids), L   # no hardcoded action id


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


def test_observe_change_is_a_real_before_after_diff():
    before = np.zeros((4, 4), dtype=np.int32); before[0, :3] = 1; before[:2, 0] = 1
    changed, kind = observe_change(before, np.rot90(before))
    assert changed == 1.0 and kind == "rotation"
    assert observe_change(before, before) == (0.0, "none")


# --------------------------------------------------------------------------
# discipline — default-OFF, guarded, seed round-trip
# --------------------------------------------------------------------------
def test_every_rule_guarded_on_operate_on():
    for r in RULES:
        assert "operate_on" in json.dumps(r["where"]), r["name"]


def test_default_off_no_rule_fires():
    s, ag = boot_core()
    n = rf._native_eval2(s)
    for r in RULES:
        n.add_rule(r)
    g = s.add_node("Game", {"op_policy": "exhaust_actions", "at_object": 1.0,
                            "discovered": 0.0})  # NO operate_on
    a = s.add_node("GameAction", {"action_id": "ACTION5", "ordinal": 5.0,
                                  "is_movement": 0.0, "tried": 0.0})
    n.add_edge_unchecked(g, "has_action", a)
    oc = s.add_node("ActionOutcome", {"action_id": "ACTION5", "remote_changed": 1.0,
                                      "effect_kind": "rotation"})
    n.add_edge_unchecked(g, "has_outcome", oc)
    n.run_rules()
    assert list(s.neighbours(g, "has_operates")) == []
    assert (s.node(g)["attrs"].get("try_action") or "") == ""


def test_seed_roundtrips_source_match():
    built = manifest()
    onfile = json.load(open(os.path.join(_ROOT, "seeds", "remote_operate.json")))
    assert json.dumps(built, sort_keys=True) == json.dumps(onfile, sort_keys=True)


def test_manifest_shape():
    m = manifest()
    assert m["id"] == "remote_operate" and m["version"] == "1.0.0"
    names = {r["name"] for r in m["rules"]}
    assert {"ro_try_action", "ro_try_movement", "ro_discover_operate"} <= names
