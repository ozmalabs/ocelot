"""Gates for BLOCK 228000 — REMOTE CAUSATION ("the switch affects a remote thing").

The agent, out of EXHAUSTION + SALIENCE (no prior causal model), explores the only
un-visited salient object, INTERVENES, and DISCOVERS the remote-causal link by the
interventional do-contrast (act->effect vs no-op->no-effect), attributing B's change
ACROSS SPACE; then acts on the confirmed link -> pass. Every decision is a graph rule;
the adapter is mechanical. The SAME rules run ls20 (cross->shape) AND Doom (lever->door).
"""
import json
import os
import sys

import numpy as np

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (_ROOT, os.path.join(_ROOT, "scripts"), os.path.join(_ROOT, "runners", "dsl", "python")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from worlds.remote_causal import (  # noqa: E402
    make_attribution_scenario, run_attribution_vignette, correct_verdict,
    make_remote_board, run_grid_episode, RemotePlanner, observe_intervention,
)
from domains.remote_causal_seed import RULES, manifest  # noqa: E402
from substrate.boot_core import boot_core  # noqa: E402
from domains import reflective_faculty as rf  # noqa: E402


def _attr_rate(arm, family, n=12, flavour="ls20", seed=228000):
    rng = np.random.default_rng(seed)
    hits = 0
    for _ in range(n):
        scn = make_attribution_scenario(rng, family, flavour=flavour)
        res = run_attribution_vignette(scn["truth"], scn["objects"], arm)
        hits += int(correct_verdict(res, family, scn["truth"], scn["objects"]))
    return hits / n


# --------------------------------------------------------------------------
# G-remote-attribution (HEADLINE): the treatment attributes across space vs BOTH controls.
# --------------------------------------------------------------------------
def test_remote_attributes_across_space_family_A():
    """Family A (confounded remote): the treatment CONFIRMS the true remote cause and
    REFUTES the local distractor; attributes across space."""
    assert _attr_rate("remote", "A") == 1.0


def test_local_only_control_MISSES_the_remote_cause_family_A():
    """The local-only control can only attribute at B's location -> never posits the
    remote cause -> misses it. THE GATE CAN FAIL, and this control fails it."""
    assert _attr_rate("local_only", "A") == 0.0


def test_no_intervention_control_CONFABULATES_family_B():
    """Family B (coincidence): without intervention, the no-intervention control
    confabulates a link from passive co-occurrence -> wrong. The interventional
    treatment REFUSES the link -> correct."""
    assert _attr_rate("no_intervention", "B") == 0.0
    assert _attr_rate("remote", "B") == 1.0


def test_interventional_teeth_the_do_contrast_decides():
    """A confirmed link requires eff_act==1 AND eff_noop==0 (intervention makes the
    difference). If B changes REGARDLESS of the intervention (eff_noop==1) the link is
    REFUTED — coincidence is not causation."""
    # remote cause: act->change, no-op->no-change  => confirmed
    ea, en, _ = observe_intervention({"controls": {"x": True}, "spontaneous": False}, "x")
    assert (ea, en) == (1.0, 0.0)
    # coincidence: B changes with or without acting  => eff_act==eff_noop => refuted
    ea, en, _ = observe_intervention({"controls": {"x": False}, "spontaneous": True}, "x")
    assert ea == en == 1.0


# --------------------------------------------------------------------------
# G-exhaustion-drives-exploration: reach the novel salient object with NO prior model.
# --------------------------------------------------------------------------
def test_exhaustion_drives_exploration_reaches_the_switch():
    rng = np.random.default_rng(228005)
    for _ in range(8):
        scn = make_remote_board(rng, flavour="ls20")
        res = run_grid_episode(scn, "remote", budget=200)
        assert res["reached_cross"], "exhaustion+salience must drive the agent to the switch"


def test_causal_prior_control_never_explores_THE_GATE_CAN_FAIL():
    """The causal_prior control only moves toward an ALREADY-hypothesised object; it
    never forms a hypothesis for an un-visited object -> never goes -> cycles."""
    rng = np.random.default_rng(228005)
    for _ in range(8):
        scn = make_remote_board(rng, flavour="ls20")
        res = run_grid_episode(scn, "causal_prior", budget=200)
        assert not res["reached_cross"], "causal_prior must never reach the un-hypothesised switch"
        assert not res["win"]


def test_exploration_precedes_the_causal_model():
    """The go-to-switch decision is PRIOR to any causal hypothesis: on the trace the
    agent enters explore_mode and heads to the switch BEFORE attributed_remote."""
    rng = np.random.default_rng(228007)
    scn = make_remote_board(rng, flavour="ls20")
    res = run_grid_episode(scn, "remote", budget=200, trace=True)
    tr = res["trace"]
    seek = next(t for t in tr if t["waypoint"] == "object")
    attrib = next(t for t in tr if t["attributed_remote"] == 1.0)
    assert seek["step"] < attrib["step"], "explore/interact must come BEFORE the causal model"
    assert seek["attributed_remote"] == 0.0, "no causal model when the exploration decision is made"


# --------------------------------------------------------------------------
# G-pass-via-remote: the full loop passes vs the local model that cannot.
# --------------------------------------------------------------------------
def test_pass_via_remote_vs_local_only():
    rng = np.random.default_rng(228009)
    rw, lw = 0, 0
    for _ in range(8):
        scn = make_remote_board(rng, flavour="ls20")
        rw += int(run_grid_episode(scn, "remote", budget=200)["win"])
        lw += int(run_grid_episode(scn, "local_only", budget=200)["win"])
    assert rw == 8, "the remote loop passes the genuinely-remote board"
    assert lw == 0, "the local-only model cannot pass when the effect is non-local"


def test_action_that_furthers_the_posit_is_interact_not_local_probe():
    """The action taken to further/confirm the posit is INTERACT-WITH-THE-SWITCH +
    observe the remote effect, NOT a local block-probe."""
    rng = np.random.default_rng(228007)
    scn = make_remote_board(rng, flavour="ls20")
    res = run_grid_episode(scn, "remote", budget=200, trace=True)
    assert res["reached_cross"] and res["attributed_remote"] == 1.0 and res["win"]
    assert res["confirmed"] == [scn["remote_obj_id"]]


# --------------------------------------------------------------------------
# G-general: the SAME rules work on a Doom-shaped board (lever -> remote door).
# --------------------------------------------------------------------------
def test_generality_same_rules_on_doom_board():
    rng = np.random.default_rng(228011)
    for _ in range(6):
        scn = make_remote_board(rng, flavour="doom")
        res = run_grid_episode(scn, "remote", budget=200)
        assert res["win"] and res["attributed_remote"] == 1.0
        # local_only fails on the doom board too (same mechanism)
        lres = run_grid_episode(scn, "local_only", budget=200)
        assert not lres["win"]


def test_generality_attribution_on_doom():
    assert _attr_rate("remote", "A", flavour="doom") == 1.0
    assert _attr_rate("local_only", "A", flavour="doom") == 0.0
    assert _attr_rate("no_intervention", "B", flavour="doom") == 0.0


# --------------------------------------------------------------------------
# G-graph-native / source-audit.
# --------------------------------------------------------------------------
def test_source_audit_no_domain_tokens_in_logic():
    from remote_causal_measure import source_audit
    a = source_audit()
    assert a["banned_tokens_found"] == [], "rules must name no ls20/doom/cross/lever/door token"
    assert a["explore_reads_only_visited_salience"], \
        "the go-to-switch decision reads ONLY visited/salience/exhaustion"
    assert a["confirm_without_intervention_shortcut"] == [], \
        "no rule confirms a link without the interventional (or passive) observation"
    assert a["clean"]


def test_seed_round_trips():
    from remote_causal_measure import source_match
    assert source_match(), "domains/remote_causal_seed.py -> seeds/remote_causal.json is byte-stable"


# --------------------------------------------------------------------------
# G-discipline: default-OFF byte-identical.
# --------------------------------------------------------------------------
def test_every_rule_guarded_on_remote_on():
    """Every rule's where-clause requires remote_on==1 (default-OFF)."""
    for r in RULES:
        assert '"remote_on"' in json.dumps(r["where"]), f"{r['name']} must be guarded on remote_on"


def test_default_off_no_rule_fires():
    """A graph WITHOUT remote_on set fires none of the rules (byte-identical)."""
    s, ag = boot_core()
    n = rf._native_eval2(s)
    for r in RULES:
        n.add_rule(r)
    g = s.add_node("Game", {"arm": "remote", "known_option_tried": 1.0,
                            "explore_mode": 1.0, "symbol_matches_goal": 0.0, "waypoint": ""})
    p = s.add_node("Ping", {}); n.add_edge_unchecked(g, "has_ping", p)
    o = s.add_node("SalientObject", {"obj_id": "x", "r": 1.0, "c": 1.0, "is_local": 0.0,
                                     "salient": 1.0, "visited": 0.0, "interacted": 1.0,
                                     "eff_act": 1.0, "eff_noop": 0.0, "passive_cooccur": 1.0})
    n.add_edge_unchecked(g, "has_object", o)
    n.run_rules()
    assert s.node(g)["attrs"].get("waypoint") in ("", None), "no waypoint without remote_on"
    assert list(s.neighbours(g, "has_posit")) == [], "no posit minted without remote_on"


def test_manifest_shape():
    m = manifest()
    assert m["id"] == "remote_causal" and m["depends_on"] == []
    assert len(m["rules"]) == 12
