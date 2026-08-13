"""seeds/entity_concept_correspondence.json + domains/reasoning_can_bridge.py's
rewire -- the GENERAL SmEntity<->Microtheory identity-resolution mechanism.
See docs/research/engine_substrate/ENTITY_RESOLUTION_PREREG.md/_RESULTS.md.

Exercises the mechanism against REAL residents from seeds/bigville_cast100.json
(not synthetic single-token fixtures) referred to by surface forms that
DIFFER from worlds/bigville_can_beliefs.build_resident_can_mt's own literal
`f"{resident['name']}_beliefs"` naming convention -- the actual test of
generality the old naming-convention bridge could not pass.
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
from domains import name_variant_merge as nvm                            # noqa: E402
from worlds.bigville_can_beliefs import (                                # noqa: E402
    install_productions, build_resident_can_mt,
)

_CAN_SEED_PATHS = (
    "seeds/causal_attitude_networks.json",
    "seeds/shape_decode_loop.json",
    "seeds/can_native_reimplementation.json",
)

_CAST100 = json.load(open(os.path.join(_ROOT, "seeds", "bigville_cast100.json")))
_RESIDENTS_BY_NAME = {r["name"]: r for r in _CAST100["residents"]}


def _fresh_agent():
    a = WorldAdapter(seeds=())
    ig.ensure_seeds(a)
    install_productions(a.s)
    for path in _CAN_SEED_PATHS:
        d = json.load(open(os.path.join(_ROOT, path)))
        a.inner.load_seed_manifest(engine_rules_only(d))
    return a


def _real_resident(name):
    """A REAL bigville_cast100.json resident record, unmodified."""
    return dict(_RESIDENTS_BY_NAME[name])


# --------------------------------------------------------------------------- #
#  0. Grounding facts about the real corpus this suite's demo depends on --
#     checked live, not assumed (ENTITY_RESOLUTION_PREREG.md sec"GO bar").
# --------------------------------------------------------------------------- #
def test_ditchwater_surname_is_unique_in_the_real_cast():
    surnames = {}
    for r in _CAST100["residents"]:
        toks = r["name"].lower().split()
        if len(toks) >= 2:
            surnames.setdefault(toks[-1], []).append(r["name"])
    assert surnames["ditchwater"] == ["Ida Ditchwater"]


def test_peaseblossom_surname_is_genuinely_ambiguous_in_the_real_cast():
    surnames = {}
    for r in _CAST100["residents"]:
        toks = r["name"].lower().split()
        if len(toks) >= 2:
            surnames.setdefault(toks[-1], []).append(r["name"])
    assert len(surnames["peaseblossom"]) >= 2


# --------------------------------------------------------------------------- #
#  1. The OLD naming-convention bridge provably CANNOT resolve a real,
#     multi-token resident name referred to by surname alone.
# --------------------------------------------------------------------------- #
def test_old_literal_naming_convention_fails_on_a_real_multi_token_resident():
    a = _fresh_agent()
    build_resident_can_mt(a.s, _real_resident("Ida Ditchwater"))
    legacy_mt = rcb._find_mt_by_name(a.s, "ditchwater_beliefs")
    assert legacy_mt is None, (
        "the real Mt is named 'Ida Ditchwater_beliefs', not 'ditchwater_beliefs' "
        "-- the literal f'{entity}_beliefs' format was never going to reach it")


# --------------------------------------------------------------------------- #
#  2. Direction 1, live, on real data, surname-only reference: the NEW
#     mechanism resolves what the OLD one structurally cannot.
# --------------------------------------------------------------------------- #
def test_live_direction1_resolves_real_resident_by_surname_only_not_full_name():
    a = _fresh_agent()
    built = build_resident_can_mt(a.s, _real_resident("Ida Ditchwater"))
    ws = built["concepts"]["world_safe"]
    assert a.s.node(ws)["attrs"].get("external_field") is None

    pd.mint_logical_schema(a, "if X is calm, X is world safe")
    # SmEntity minted by the reading pipeline is named "ditchwater" (a real
    # lowercase single-token SURNAME reference) -- confirmed live, not
    # assumed: situation_model_reader lowercases the parsed argument
    # verbatim, never the resident's own two-token graph-record name.
    res = ig.read_and_infer(a, "Ditchwater is calm.")
    hit = res["logical"][0]
    assert hit["gap"]["entity"] == "ditchwater"
    assert hit["minted"] is True

    applied = rcb.apply_inference_hits_as_can_evidence(a, res["logical"])
    assert applied == [{"applied": True, "concept": ws, "entity": "ditchwater",
                         "attr": "world_safe", "evidence": 1.0, "alpha": 1.0}]
    assert a.s.node(ws)["attrs"].get("external_field") == 1.0

    # the correspondence really did go through the TOKEN-SUBSET rung, not
    # the exact rung (name "ditchwater" != resident name "Ida Ditchwater")
    ent = None
    for n in a.s.nodes("SmEntity"):
        if a.s.node(n)["attrs"].get("name") == "ditchwater":
            ent = n
    assert ent is not None
    denoted = list(a.inner.neighbours(ent, "denotes"))
    assert len(denoted) == 1
    assert a.s.node(denoted[0])["attrs"].get("name") == "Ida Ditchwater_beliefs"


def test_live_direction1_end_to_end_moves_real_can_settled_state_by_surname():
    """The headline live demonstration, mirroring REASONING_FACILITY_BRIDGE_
    RESULTS.md sec1.4's own shape, but on REAL cast data and a surface form
    (surname only) the OLD bridge could not have resolved at all."""
    def run(apply_bridge):
        a = _fresh_agent()
        rr = _real_resident("Ida Ditchwater")
        rr["params"] = dict(rr["params"])
        rr["params"]["prior_world_safe"] = 0.35   # near the update threshold
        built = build_resident_can_mt(a.s, rr)
        a.s.set_attr(built["mt_node"], "discrete_mode", "3state")
        a.s.set_attr(built["mt_node"], "can_tick", 0)
        pd.mint_logical_schema(a, "if X is calm, X is world safe")
        res = ig.read_and_infer(a, "Ditchwater is calm.")
        if apply_bridge:
            rcb.apply_inference_hits_as_can_evidence(a, res["logical"])
        a.inner.run_rules_scoped(3000, False, built["mt_node"])
        return a.s.node(built["concepts"]["world_safe"])["attrs"].get("state")

    baseline = run(False)
    with_bridge = run(True)
    assert baseline != with_bridge
    assert with_bridge == 1.0


# --------------------------------------------------------------------------- #
#  3. Direction 2, backward, on the SAME real resident+surname correspondence
#     already established: predications land on the surface form actually
#     used in the discourse, not a silently-substituted canonical name.
# --------------------------------------------------------------------------- #
def test_live_direction2_writes_predications_on_the_denoting_surface_form():
    a = _fresh_agent()
    rr = _real_resident("Ida Ditchwater")
    built = build_resident_can_mt(a.s, rr)
    a.s.set_attr(built["mt_node"], "discrete_mode", "3state")
    a.s.set_attr(built["mt_node"], "can_tick", 0)

    # establish the surname correspondence FIRST (as a real reading turn
    # would), exactly like direction 1 above -- entity "ditchwater" now
    # denotes Ida Ditchwater's Mt.
    pd.mint_logical_schema(a, "if X is calm, X is world safe")
    ig.read_and_infer(a, "Ditchwater is calm.")

    # settle the REAL network from her real prior (unrelated to the fact
    # above -- this is CAN's own dynamics, not a re-assertion of world_safe).
    a.inner.run_rules_scoped(3000, False, built["mt_node"])

    pd.mint_logical_schema(a, "if X is world safe, X is content")
    preds = rcb.can_state_as_predications(a, built["mt_node"])
    entities_written = {p["predication"][1] for p in preds
                         if p["predication"][0] == "is_a"}
    assert entities_written == {"ditchwater"}, (
        "predications must land on the surface form the discourse actually "
        "used ('ditchwater'), never a freshly-normalized full name "
        "('ida_ditchwater') the reading pipeline never introduced")

    after = ig.read_and_infer(a, "")
    hits = {h["gap"]["antecedent_attr"]: h for h in after["logical"]
            if h["gap"]["entity"] == "ditchwater"}
    if "world_safe" in hits:
        assert hits["world_safe"]["supplies"] == {"relation": "is_a", "attr": "content"}


# --------------------------------------------------------------------------- #
#  4. Negative control: a genuinely ambiguous surname refuses to resolve --
#     no-over-merge, a real null reported honestly, never a guess.
# --------------------------------------------------------------------------- #
def test_ambiguous_surname_refuses_to_resolve_honest_null():
    a = _fresh_agent()
    for name in ("Verity Peaseblossom", "Radella Peaseblossom"):
        build_resident_can_mt(a.s, _real_resident(name))
    res = rcb.apply_derived_fact_as_can_evidence(a, "peaseblossom", "world_safe")
    assert res["applied"] is False
    assert "no CAN correspondence found for entity 'peaseblossom'" in res["reason"]


# --------------------------------------------------------------------------- #
#  5. Old fixtures / honest-miss messages -- unchanged behaviour, still green
#     (regression, not a new claim).
# --------------------------------------------------------------------------- #
def test_honest_miss_when_nothing_corresponds_at_all():
    a = _fresh_agent()
    res = rcb.apply_derived_fact_as_can_evidence(a, "nobody", "world_safe")
    assert res["applied"] is False
    assert "nobody_beliefs" in res["reason"]


def test_exact_convention_case_still_resolves_via_the_exact_rule():
    a = _fresh_agent()
    build_resident_can_mt(a.s, {"name": "avery", "index": 0, "params": {
        "resolution_bins": 7, "arousal": 0.2, "mood_bias": 0.30,
        "w_supergraph": 0.50, "prior_world_safe": 0.5,
        "prior_self_worth": 0.5, "charm_weight": 0.5, "hostile_weight": 0.2,
        "prior_others_trust": 0.5, "claim_weight": 0.5, "w_spite": 0.1}})
    res = rcb.apply_derived_fact_as_can_evidence(a, "avery", "world_safe")
    assert res["applied"] is True


# --------------------------------------------------------------------------- #
#  6. Regression guard -- this rung never edits deduction/CAN facility
#     internals, nor name_variant_merge.py (reused, not modified).
# --------------------------------------------------------------------------- #
def test_source_audit_no_facility_internals_edited():
    import subprocess
    out = subprocess.run(
        ["git", "diff", "--stat", "main", "--",
         "domains/propositional_deduction.py", "domains/inference_generation.py",
         "domains/situation_model_reader.py", "domains/name_variant_merge.py",
         "seeds/inference_logical.json", "seeds/can_native_reimplementation.json",
         "seeds/can_decay_identity.json", "worlds/bigville_can_beliefs.py",
         "runners/dsl/src/can_ops.rs", "runners/dsl/src/term.rs"],
        cwd=_ROOT, capture_output=True, text=True)
    assert out.stdout.strip() == "", "facility internals changed:\n%s" % out.stdout


def test_name_tokens_reused_not_reimplemented():
    """The correspondence mechanism's tokenizer really is name_variant_merge's
    OWN _name_tokens (no parallel tokenizer invented)."""
    assert rcb._name_tokens_frozenset("Verity Peaseblossom") == frozenset(
        nvm._name_tokens("verity_peaseblossom"))
