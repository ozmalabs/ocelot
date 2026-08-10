"""test_self_correction -- the CAPSTONE gate: AUTONOMOUS self-correction,
closing the loop tier 4 (`domains/collapse_model.py`) opens. Fast pytest
regression for `domains/self_correction.py` -- mirrors `scripts/
jabberwock_corrects_divergence.py`'s console narrative in pytest form.

FIXTURES REUSE THE REAL, ALREADY-TESTED AXIS-RUNAWAY RECONSTRUCTION:
`_shape_decode_agent` + `_add_pending_observation` are the SAME shapes
`tests/test_collapse_model.py` / `tests/test_collapse_cognition.py` already
use (`boot_core()` + `domains.reflective_faculty._ensure_shape_decode_loop`
-- fast fixtures only, never a full 386-seed `load_all_seeds`). The
divergence this file drives is the REAL `sd_mint_quantum` novelty-guard
pathology `domains/collapse_model.py`'s own module docstring names (the
2026-07-03 axis-runaway incident): the forward-look's per-round recurrence
re-tags a structurally-identical residual under a FRESH `Observation.key`
every round (`domains.collapse_model._synthesize_recurrence_hypothesis`,
simulating continuous per-frame perception), which the real novelty guard's
`key`-keyed identity check does not catch.

TWO PROVENANCE FIXTURES, deliberately different, isolated per-test agent
graphs (nothing here mutates any seed file or any OTHER agent):

  - `_frozen_provenance`: `domains.self_model.ensure_self_model` (real,
    disk-scan-based -- reads the ACTUAL `seeds/shape_decode_loop.json` to
    learn `sd_mint_quantum`/`sd_dedup_existing` really do come from that
    seed) + a `SeedSummary{seed_id:'shape_decode_loop', skippable:0.0}`
    (mirrors what a real `load_all_seeds` boot would have minted, since
    `shape_decode_loop` genuinely is in `substrate.boot_all._FROZEN_SEED_
    IDS`). This is the TRUE production provenance.
  - `_skippable_provenance`: a deliberately-labelled TEST-ONLY substitution
    -- `RuleSummary{name, from_seed:'self_correction_test_seed'}` +
    `SeedSummary{seed_id:'self_correction_test_seed', skippable:1.0}` on a
    SEPARATE agent instance, isolating the denylist gate's discriminative
    behaviour (allow vs. deny) using the SAME validated rule mechanics
    without needing a second, independently-authored divergence scenario.
    This does not claim `shape_decode_loop` is skippable anywhere -- it is
    a distinct graph, a distinct `RuleSummary` entry, never touching the
    real seed's own frozen status.
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import pytest

pytest.importorskip("substrate_rs")

import substrate_rs as srs                                          # noqa: E402
from substrate.boot_core import boot_core                            # noqa: E402
import domains.reflective_faculty as rf                              # noqa: E402
from domains import self_model as sm                                 # noqa: E402
from domains.collapse_model import predict_collapse                  # noqa: E402
from domains.self_correction import (                                # noqa: E402
    imagine_and_check_convergence, intervene_on_divergence,
    _default_candidates, _infer_growth_rule,
)


def _shape_decode_agent():
    s, ag = boot_core()
    native = rf._native_eval2(s)
    rf._ensure_shape_decode_loop(s, native, ag)
    return s, ag, native


def _add_pending_observation(s, ag, key: str):
    obs = s.add_node("Observation", {"signature": [[key, "X"]], "key": [key], "status": "pending"})
    s.add_edge(ag, "observed", obs)
    return obs


def _seed_runaway(s, ag, *, n: int = 3, tag: str = "run"):
    return [_add_pending_observation(s, ag, f"zzz{tag}{i}") for i in range(n)]


def _frozen_provenance(s, ag):
    """Real, disk-scan-based provenance: sd_mint_quantum/sd_dedup_existing
    genuinely come from seeds/shape_decode_loop.json, genuinely frozen."""
    class _A:
        def __init__(self):
            self.s = s
            self.inner = s._inner
            self.agent = ag
    sm.ensure_self_model(_A())
    s.add_node("SeedSummary", {"seed_id": "shape_decode_loop", "skippable": 0.0})


def _skippable_provenance(s):
    """Test-only provenance substitution (see module docstring) -- an
    isolated agent graph, never touching the real seed's frozen status."""
    s.add_node("RuleSummary", {"name": "sd_mint_quantum", "from_seed": "self_correction_test_seed"})
    s.add_node("RuleSummary", {"name": "sd_dedup_existing", "from_seed": "self_correction_test_seed"})
    s.add_node("SeedSummary", {"seed_id": "self_correction_test_seed", "skippable": 1.0})


# ---------------------------------------------------------------------------
# 1. IMAGINE-A-FIX-CHECKS-CONVERGENCE -- discriminative.
# ---------------------------------------------------------------------------
def test_imagine_and_check_convergence_discriminates_correct_from_wrong_fix():
    s, ag, native = _shape_decode_agent()
    _seed_runaway(s, ag, tag="imag")

    before_dict = s._inner.graph_to_dict()
    before_rule_count = s._inner.rule_count()

    cands = _default_candidates(native, "sd_mint_quantum")
    labels = [c["label"] for c in cands]
    assert "dedup_identity_fix" in labels, labels
    assert len(cands) >= 2, "candidate space should offer more than one option"

    correct = next(c for c in cands if c["label"] == "dedup_identity_fix")
    wrong = next(c for c in cands if c["label"] != "dedup_identity_fix")

    r_correct = imagine_and_check_convergence(s, correct, horizon=3, imagine_steps=2)
    assert r_correct["model_before"].converged is False, "the divergence must be real"
    assert r_correct["converges"] is True, r_correct["model_after"].counts_trajectory
    assert r_correct["model_after"].frontier_growth_rate <= 0.0

    r_wrong = imagine_and_check_convergence(s, wrong, model_before=r_correct["model_before"],
                                             horizon=3, imagine_steps=2)
    assert r_wrong["converges"] is False, "a wrong candidate must not be reported as converging"

    # reversibility of the check itself, regardless of which candidate:
    after_dict = s._inner.graph_to_dict()
    after_rule_count = s._inner.rule_count()
    assert after_rule_count == before_rule_count, "imagine_and_check_convergence must never touch the live rule store"
    diff = srs._native.Substrate.graph_diff(before_dict, after_dict)
    assert diff["nodes_removed"] == []
    assert diff["nodes_changed"] == []
    assert diff["edges_removed"] == []
    added_types = {n["type"] for n in diff["nodes_added"]}
    assert added_types <= {"Imagination", "ImaginedConclusion", "CollapseModel"}, added_types


def test_dedup_identity_fix_is_inert_on_a_rule_with_no_identity_guard():
    from domains.self_correction import _dedup_identity_fix_candidate
    plain_rule = {"name": "no_guard_rule", "match": [["a", "e", "b"]],
                  "where": {"type": "Eq", "a": {"type": "Attr", "node": {"type": "Var", "name": "b"}, "key": "x"},
                            "b": {"type": "Lit", "value": 1}},
                  "effects": [["set_attr", "b", "x", 2]]}
    assert _dedup_identity_fix_candidate(plain_rule, "x_fix") is None


# ---------------------------------------------------------------------------
# 2. AUTONOMOUS LOOP (NON-FROZEN) -- ticks-only, zero human.
# ---------------------------------------------------------------------------
def test_autonomous_loop_adopts_validated_fix_on_non_frozen_divergence():
    s, ag, native = _shape_decode_agent()
    _seed_runaway(s, ag, tag="nf")
    _skippable_provenance(s)

    before_rule_count = s._inner.rule_count()
    trajectory_before = predict_collapse(s, horizon=3, imagine_steps=2)
    assert trajectory_before.converged is False, "diverging -> chosen fix -> adopted -> converged"

    result = intervene_on_divergence(s, target_rule="sd_mint_quantum", horizon=3, imagine_steps=2,
                                      model_before=trajectory_before)

    assert result["escalated"] is False, result
    assert result["adopted"] is True, result
    assert result["chosen"] == "dedup_identity_fix"
    assert len(result["adoptions"]) >= 1
    assert result["model_after_candidate"].converged is True
    assert result["model_final"].converged is True, result["model_final"].counts_trajectory
    assert result["model_final"].frontier_growth_rate <= 0.0

    # the live rule store WAS mutated (this is the autonomous-adopt case)
    after_rule_count = s._inner.rule_count()
    assert after_rule_count > before_rule_count
    names = {r.get("name") for r in native.export_rules() if isinstance(r, dict) and r.get("active", True)}
    assert "sd_mint_quantum" not in names, "the original diverging rule must be tombstoned"
    assert any(n.startswith("sd_mint_quantum_scfix_") for n in names), names

    # no escalation artefacts on the successful autonomous path
    assert list(s.nodes("SelfCorrectionProposal")) == []


def test_locates_diverging_rule_without_explicit_target():
    s, ag, native = _shape_decode_agent()
    _seed_runaway(s, ag, tag="loc")
    model = predict_collapse(s, horizon=3, imagine_steps=2)
    assert model.converged is False
    inferred = _infer_growth_rule(native, model)
    assert inferred == "sd_mint_quantum", inferred


def test_already_converged_graph_is_left_alone():
    s, ag, native = _shape_decode_agent()
    # no pending Observations at all -- an already-settled graph
    before_rule_count = s._inner.rule_count()
    result = intervene_on_divergence(s, horizon=3, imagine_steps=2)
    assert result["adopted"] is False
    assert result["escalated"] is False
    assert result["candidates_tried"] == []
    assert s._inner.rule_count() == before_rule_count


# ---------------------------------------------------------------------------
# 3. FROZEN SAFETY BOUNDARY -- the headline.
# ---------------------------------------------------------------------------
def test_frozen_divergence_imagines_a_working_fix_but_adoption_is_denied():
    s, ag, native = _shape_decode_agent()
    _seed_runaway(s, ag, tag="fr")
    _frozen_provenance(s, ag)

    before_rule_count = s._inner.rule_count()
    before_active_names = sorted(
        r.get("name") for r in native.export_rules() if isinstance(r, dict) and r.get("active", True))

    trajectory_before = predict_collapse(s, horizon=3, imagine_steps=2)
    assert trajectory_before.converged is False

    result = intervene_on_divergence(s, target_rule="sd_mint_quantum", horizon=3, imagine_steps=2,
                                      model_before=trajectory_before)

    # the agent DID find (imagine) a working fix ...
    assert result["chosen"] == "dedup_identity_fix"
    assert result["model_after_candidate"].converged is True, "the fix genuinely converges in imagination"
    # ... but adoption is denied, and escalated instead
    assert result["adopted"] is False
    assert result["escalated"] is True
    assert result["denied"], "both sd_mint_quantum and sd_dedup_existing are frozen-provenance"
    denied_names = {n for n, _reason in result["denied"]}
    assert "sd_mint_quantum" in denied_names
    for _name, reason in result["denied"]:
        assert "shape_decode_loop" in reason or "non-skippable" in reason, reason

    # a human-review proposal + rung-5 Impasse were minted, carrying the fix
    proposal = result["proposal"]
    assert s.has_node(proposal)
    pat = s.node(proposal)["attrs"]
    assert pat["status"] == "pending_human_approval"
    assert pat["target_rule"] == "sd_mint_quantum"
    assert "sd_mint_quantum" in pat["rule_names"]
    assert pat["model_after_converges"] is True

    impasse = result["impasse"]
    assert s.has_node(impasse)
    iat = s.node(impasse)["attrs"]
    assert iat["kind"] == "human"
    assert iat["to"] == "creator"
    assert iat["resolved"] == 0.0

    # THE ASSERTION: NO FROZEN RULE WAS MUTATED.
    after_rule_count = s._inner.rule_count()
    assert after_rule_count == before_rule_count, "adoption must be a complete no-op on denial"
    after_active_names = sorted(
        r.get("name") for r in native.export_rules() if isinstance(r, dict) and r.get("active", True))
    assert after_active_names == before_active_names, "the live ruleset is byte-for-byte unchanged"
    assert list(s.nodes("SelfCorrectionAdoption")) == [], "no adoption record -- nothing was adopted"


def test_frozen_boundary_is_provenance_specific_not_a_blanket_refusal():
    """Discriminative twin: the SAME candidate mechanics, on a NON-frozen
    provenance agent, DO adopt (test 2 above) -- so this denial is really
    about `shape_decode_loop`'s frozen provenance, not a hardcoded refusal."""
    s, ag, native = _shape_decode_agent()
    _seed_runaway(s, ag, tag="disc")
    _skippable_provenance(s)
    result = intervene_on_divergence(s, target_rule="sd_mint_quantum", horizon=3, imagine_steps=2)
    assert result["adopted"] is True
    assert result["escalated"] is False


# ---------------------------------------------------------------------------
# 4. REVERSIBILITY of the imagine-and-check primitive, standalone.
# ---------------------------------------------------------------------------
def test_reversibility_imagine_and_check_convergence_leaves_live_graph_alone():
    s, ag, native = _shape_decode_agent()
    _seed_runaway(s, ag, tag="rev")

    before_dict = s._inner.graph_to_dict()
    before_rule_count = s._inner.rule_count()

    cands = _default_candidates(native, "sd_mint_quantum")
    for cand in cands:
        imagine_and_check_convergence(s, cand, horizon=3, imagine_steps=2)

    after_dict = s._inner.graph_to_dict()
    after_rule_count = s._inner.rule_count()
    assert after_rule_count == before_rule_count

    diff = srs._native.Substrate.graph_diff(before_dict, after_dict)
    assert diff["nodes_removed"] == []
    assert diff["nodes_changed"] == []
    assert diff["edges_removed"] == []
    added_types = {n["type"] for n in diff["nodes_added"]}
    assert added_types <= {"Imagination", "ImaginedConclusion", "CollapseModel"}, added_types
    assert list(s.nodes("Commitment")) == [], "imagine-and-check is never a commit"
    assert list(s.nodes("SelfCorrectionAdoption")) == []
    assert list(s.nodes("SelfCorrectionProposal")) == []


def test_reversibility_detached_copy_mutation_never_reaches_live_graph():
    s, ag, native = _shape_decode_agent()
    _seed_runaway(s, ag, tag="det")
    cands = _default_candidates(native, "sd_mint_quantum")
    correct = next(c for c in cands if c["label"] == "dedup_identity_fix")
    result = imagine_and_check_convergence(s, correct, horizon=3, imagine_steps=2)
    dc = result["imagined"]
    dc.detached.add_node("Intruder", {})
    assert list(s.nodes("Intruder")) == []
