"""domains/reasoning_can_bridge.py -- the deduction<->CAN bridge built in
docs/research/engine_substrate/REASONING_FACILITY_BRIDGE_PREREG.md /
_RESULTS.md. Both directions are exercised against REAL facility code
(propositional_deduction.py, inference_generation.py, worlds/bigville_can_
beliefs.py, the real can_native_reimplementation.json discrete-update
rules) -- no facility internals are edited by this module or this test
file.
"""
from __future__ import annotations

import json
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import pytest                                                            # noqa: E402

from substrate.world_adapter import WorldAdapter                         # noqa: E402
from substrate.seed_loader import engine_rules_only                      # noqa: E402
from domains import propositional_deduction as pd                        # noqa: E402
from domains import inference_generation as ig                           # noqa: E402
from domains import reasoning_can_bridge as rcb                          # noqa: E402
from worlds.bigville_can_beliefs import (                                # noqa: E402
    install_productions, build_resident_can_mt,
)

_CAN_SEED_PATHS = (
    "seeds/causal_attitude_networks.json",
    "seeds/shape_decode_loop.json",
    "seeds/can_native_reimplementation.json",
)


def _fresh_agent():
    a = WorldAdapter(seeds=())
    ig.ensure_seeds(a)
    install_productions(a.s)
    for path in _CAN_SEED_PATHS:
        d = json.load(open(os.path.join(_ROOT, path)))
        a.inner.load_seed_manifest(engine_rules_only(d))
    return a


def _resident(name, index=0, prior_world_safe=0.5):
    return {"name": name, "index": index, "params": {
        "resolution_bins": 7, "arousal": 0.2, "mood_bias": 0.30,
        "w_supergraph": 0.50, "prior_world_safe": prior_world_safe,
        "prior_self_worth": 0.5, "charm_weight": 0.5, "hostile_weight": 0.2,
        "prior_others_trust": 0.5, "claim_weight": 0.5, "w_spite": 0.1,
    }}


# --------------------------------------------------------------------------- #
#  DIRECTION 1 -- deduction's derived fact -> CAN evidence
# --------------------------------------------------------------------------- #
def test_honest_miss_when_no_can_microtheory_named_for_entity():
    a = _fresh_agent()
    res = rcb.apply_derived_fact_as_can_evidence(a, "nobody", "world_safe")
    assert res["applied"] is False
    assert "nobody_beliefs" in res["reason"]


def test_honest_miss_when_mt_exists_but_no_matching_concept():
    a = _fresh_agent()
    build_resident_can_mt(a.s, _resident("avery"))
    res = rcb.apply_derived_fact_as_can_evidence(a, "avery", "not_a_real_topic")
    assert res["applied"] is False
    assert "avery_beliefs" in res["reason"]


def test_apply_derived_fact_moves_external_field_via_the_real_primitive():
    a = _fresh_agent()
    built = build_resident_can_mt(a.s, _resident("avery"))
    ws = built["concepts"]["world_safe"]
    assert a.s.node(ws)["attrs"].get("external_field") is None
    res = rcb.apply_derived_fact_as_can_evidence(a, "avery", "world_safe")
    assert res == {"applied": True, "concept": ws, "entity": "avery",
                    "attr": "world_safe", "evidence": 1.0, "alpha": 1.0}
    assert a.s.node(ws)["attrs"].get("external_field") == 1.0


def test_negative_derived_fact_applies_negative_evidence():
    a = _fresh_agent()
    built = build_resident_can_mt(a.s, _resident("avery"))
    ws = built["concepts"]["world_safe"]
    rcb.apply_derived_fact_as_can_evidence(a, "avery", "world_safe", positive=False)
    assert a.s.node(ws)["attrs"].get("external_field") == -1.0


def test_batch_form_reads_resolve_implication_gap_shape_and_strips_not_prefix():
    a = _fresh_agent()
    built = build_resident_can_mt(a.s, _resident("avery"))
    hits = [
        {"minted": True, "gap": {"entity": "avery"},
         "supplies": {"relation": "is_a", "attr": "world_safe"}},
        {"minted": True, "gap": {"entity": "avery"},
         "supplies": {"relation": "is_a", "attr": "not_trust_mayor"}},
        {"minted": False, "gap": {"entity": "avery"}, "schema": None},  # skipped
    ]
    applied = rcb.apply_inference_hits_as_can_evidence(a, hits)
    assert len(applied) == 2
    assert applied[0]["attr"] == "world_safe" and applied[0]["evidence"] == 1.0
    assert applied[1]["attr"] == "trust_mayor" and applied[1]["evidence"] == -1.0
    assert a.s.node(built["concepts"]["world_safe"])["attrs"]["external_field"] == 1.0
    assert a.s.node(built["concepts"]["trust_mayor"])["attrs"]["external_field"] == -1.0


def test_live_end_to_end_derived_fact_changes_can_settled_state_confirmed_direction():
    """The headline live demonstration for direction 1: two agents run the
    IDENTICAL pipeline (mint a held implication whose consequent attr is a
    real CAN topic name, read a sentence that fires modus ponens for a
    resident's own name) -- the ONLY difference is whether the bridge
    applies the derived fact as CAN evidence. At this resident's prior
    (world_safe identity_field balanced near the update threshold, measured
    live in the investigation, not guessed), the two runs settle to
    DIFFERENT discrete states, in the CONFIRMED direction (positive
    evidence -> state moves toward +1, never away from it)."""
    def run(apply_bridge):
        a = _fresh_agent()
        built = build_resident_can_mt(a.s, _resident("avery", prior_world_safe=0.35))
        a.s.set_attr(built["mt_node"], "discrete_mode", "3state")
        a.s.set_attr(built["mt_node"], "can_tick", 0)
        pd.mint_logical_schema(a, "if X is calm, X is world safe")
        res = ig.read_and_infer(a, "Avery is calm.")
        if apply_bridge:
            rcb.apply_inference_hits_as_can_evidence(a, res["logical"])
        a.inner.run_rules_scoped(3000, False, built["mt_node"])
        return a.s.node(built["concepts"]["world_safe"])["attrs"].get("state")

    baseline = run(False)
    with_bridge = run(True)
    assert baseline != with_bridge, (
        "expected the bridge's applied evidence to move the settled state; "
        "got baseline=%r with_bridge=%r" % (baseline, with_bridge))
    assert with_bridge == 1.0, "positive evidence must settle toward +1, got %r" % with_bridge


# --------------------------------------------------------------------------- #
#  DIRECTION 2 -- CAN's settled state -> deduction fact
# --------------------------------------------------------------------------- #
def test_can_state_as_predications_reads_sign_and_uses_not_prefix_for_negative():
    a = _fresh_agent()
    built = build_resident_can_mt(a.s, _resident("blair"))
    a.s.set_attr(built["concepts"]["world_safe"], "state", 1.0)
    a.s.set_attr(built["concepts"]["claim_credible"], "state", -1.0)
    a.s.set_attr(built["concepts"]["trust_mayor"], "state", 0.0)  # undifferentiated
    preds = rcb.can_state_as_predications(a, built["mt_node"])
    got = sorted(p["predication"][2] for p in preds if p["predication"][0] == "is_a"
                 and p["predication"][1] == "blair")
    assert "world_safe" in got
    assert "not_claim_credible" in got
    assert "trust_mayor" not in got and "not_trust_mayor" not in got  # state==0 -> no fact


def test_can_state_as_predications_empty_when_all_undifferentiated():
    a = _fresh_agent()
    built = build_resident_can_mt(a.s, _resident("blair"))
    # no state set on any concept -> default None, nothing to assert
    preds = rcb.can_state_as_predications(a, built["mt_node"])
    assert preds == []


def test_live_end_to_end_can_settled_state_feeds_a_new_deduction_fact():
    """The headline live demonstration for direction 2: a real CAN network
    settles (via the REAL discrete-update rules, run_rules_scoped, no
    deduction fact involved on the way in), its state is read back as
    predications, and a held knowledge_logical implication -- unrelated to
    how the CAN state was produced -- derives a genuinely NEW fact that did
    not exist before the round trip and could not have been derived from
    text alone (no text about 'blair' was ever read)."""
    a = _fresh_agent()
    built = build_resident_can_mt(a.s, _resident("blair", prior_world_safe=0.9))
    a.s.set_attr(built["mt_node"], "discrete_mode", "3state")
    a.s.set_attr(built["mt_node"], "can_tick", 0)
    steps = a.inner.run_rules_scoped(3000, False, built["mt_node"])
    assert steps > 0, "the network must actually settle for this demo to mean anything"
    ws_state = a.s.node(built["concepts"]["world_safe"])["attrs"].get("state")
    assert ws_state == 1.0, "expected this resident's prior to settle world_safe to +1"

    before = ig.read_and_infer(a, "")
    assert before["logical"] == []  # no facts about blair exist yet at all

    pd.mint_logical_schema(a, "if X is world safe, X is content")
    preds = rcb.can_state_as_predications(a, built["mt_node"])
    assert any(p["predication"] == ["is_a", "blair", "world_safe"] for p in preds)

    after = ig.read_and_infer(a, "")
    hits = {h["gap"]["antecedent_attr"]: h for h in after["logical"]}
    assert hits["world_safe"]["minted"] is True
    assert hits["world_safe"]["supplies"] == {"relation": "is_a", "attr": "content"}


# --------------------------------------------------------------------------- #
#  Regression guard -- this module never edits either facility
# --------------------------------------------------------------------------- #
def test_source_audit_no_facility_internals_edited():
    import subprocess
    out = subprocess.run(
        ["git", "diff", "--stat", "main", "--",
         "domains/propositional_deduction.py", "domains/inference_generation.py",
         "domains/situation_model_reader.py", "domains/analogical_thinking.py",
         "seeds/inference_logical.json", "seeds/can_native_reimplementation.json",
         "seeds/can_decay_identity.json", "worlds/bigville_can_beliefs.py",
         "runners/dsl/src/can_ops.rs", "runners/dsl/src/term.rs"],
        cwd=_ROOT, capture_output=True, text=True)
    assert out.stdout.strip() == "", "facility internals changed:\n%s" % out.stdout
