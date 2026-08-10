"""test_self_correct_cognition -- TIER 5 COGNITION: the agent's OWN authored
decisions on top of `domains/self_correction.py`'s machinery (capstone
commit 3c3ce133). Fast pytest twin of `scripts/jabberwock_decides_to_
correct.py` (read that script's module docstring for the full narrative).

THE MACHINERY (read-only here, never modified): `domains/self_correction.py`
(`imagine_and_check_convergence` / `intervene_on_divergence` -- imagine a
candidate fix, predict whether it converges, veto against the frozen-core
denylist, adopt-or-propose). That module's own docstring names the follow-on
seam this file closes: "WHETHER to even ATTEMPT self-correction" and "WHICH
candidate is best when more than one converges".

THIS FILE covers the follow-on: the agent's OWN decision about WHICH
predicted-divergence Impasse is worth correcting, and WHICH converging
candidate to prefer. Per CLAUDE.md's discipline, no test here hand-installs
the attempt-gate/rank artefacts -- every test either (a) drives `induce_
concern` -> `ground_concern` and reads back what the agent's own composer
(`seeds/composer_self_correct_graph.json`, dispatched via the new 'correct'
RelationCue + ComposerCue) authored, or (b) drives the full predict ->
gate -> dispatch pipeline on a real booted agent and reads the graph state
back.

`domains/self_correct_dispatch.py` is the mechanical host hook exercised
here (`scan_and_self_correct` / `rank_candidates`) -- it makes no decision
itself, only calls `domains.self_correction.intervene_on_divergence` (an
in-process Python call a Rust rule effect cannot make) after reading the
agent's own gate/rank verdicts back off the graph.

No seed file is mutated at runtime by anything this file exercises (`teach`
is never called by `ground_concern`'s composer-dispatch path, nor by
`domains.collapse_watch.scan_and_predict` / `domains.self_correct_dispatch.
scan_and_self_correct`) so no snapshot-guard fixture is needed for seeds/
relation_vocabulary.json / seeds/composer_dispatch.json / seeds/composer_
self_correct_graph.json / seeds/composer_collapse_watch_graph.json -- the
same claim tests/test_collapse_cognition.py makes for its own seeds.
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

from substrate.boot_core import boot_core                # noqa: E402
from substrate.seed_loader import manifest_for            # noqa: E402
import domains.reflective_faculty as rf                   # noqa: E402
from domains import collapse_watch as cw                  # noqa: E402
from domains import self_correct_dispatch as scd          # noqa: E402
from domains import self_model as sm                      # noqa: E402


class _Agent:
    """Minimal duck-typed agent wrapper -- identical shape to
    tests/test_collapse_cognition.py's own `_Agent` (harness glue only, no
    source modified)."""
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


def _ground_collapse_watch(ag, tag="cw_t"):
    return _ground(ag, ["predict", "COLLAPSE", "of", "DIVERGENCE"], tag)


def _ground_self_correct(ag, tag="sc_t"):
    return _ground(ag, ["correct", "DIVERGENCE", "by", "CANDIDATE"], tag)


def _shape_decode_ready(ag):
    native = rf._native_eval2(ag.s)
    rf._ensure_shape_decode_loop(ag.s, native, ag.agent)


def _add_pending_observation(ag, key: str):
    obs = ag.s.add_node("Observation", {"signature": [[key, "X"]], "key": [key], "status": "pending"})
    ag.s.add_edge(ag.agent, "observed", obs)
    return obs


def _skippable_provenance(ag):
    ag.s.add_node("RuleSummary", {"name": "sd_mint_quantum", "from_seed": "self_correct_cog_test_seed"})
    ag.s.add_node("RuleSummary", {"name": "sd_dedup_existing", "from_seed": "self_correct_cog_test_seed"})
    ag.s.add_node("SeedSummary", {"seed_id": "self_correct_cog_test_seed", "skippable": 1.0})


def _frozen_provenance(ag):
    class _A:
        def __init__(self):
            self.s = ag.s
            self.inner = ag.s._inner
            self.agent = ag.agent
    sm.ensure_self_model(_A())
    ag.s.add_node("SeedSummary", {"seed_id": "shape_decode_loop", "skippable": 0.0})


def _impasses(ag):
    return [n for n in ag.s.nodes("Impasse") if ag.s.node(n)["attrs"].get("kind") == "predicted_divergence"]


def _probe_rule_fixture():
    probe = {"name": "probe_rule", "active": True, "match": [["a", "e", "b"]],
             "where": {"type": "Eq", "a": {"type": "Attr", "node": {"type": "Var", "name": "b"}, "key": "x"},
                       "b": {"type": "Lit", "value": 1}},
             "effects": [["set_attr", "b", "x", 2]]}
    cheap = dict(probe)
    cheap["name"] = "probe_rule_cheap"
    expensive = {"name": "probe_rule_expensive",
                 "match": [["a", "e", "b"], ["b", "e2", "c"], ["c", "e3", "d"]],
                 "where": {"type": "And", "items": [probe["where"]] * 5},
                 "effects": [["set_attr", "b", "x", 2], ["set_attr", "c", "y", 3],
                             ["add_edge", "b", "extra", "c"]]}
    return probe, cheap, expensive


# ---------------------------------------------------------------------------
# 1. the vocabulary genuinely walls before this change (proof, not assumed)
# ---------------------------------------------------------------------------
def test_existing_vocabulary_walls_on_correct_before_new_cue():
    s, agent_node = boot_core()
    ag = _Agent(s, agent_node)
    m = dict(manifest_for("relation_vocabulary"))
    m["nodes"] = [n for n in m["nodes"] if n["attrs"].get("name") != "self_correct_action"]
    ag.s._inner.load_seed_manifest(m, ag.agent)

    ind = rf.induce_concern(ag, [["correct", "DIVERGENCE", "by", "CANDIDATE"]], name_hint="wall_probe")
    assert ind.get("minted") is True
    res = rf.ground_concern(ag, [ind["capability_key"]])
    assert res.get("grounded") is False
    assert res.get("path") == "predicate_grounding"


def test_correct_cue_loads_and_dispatches_to_self_correct_composer():
    ag = _fresh_agent()
    name = rf._pick_composer(ag.s, ag.inner, ag.agent, {"correct"})
    assert name == "self_correct"


# ---------------------------------------------------------------------------
# 2. the jabberwock AUTHORS the attempt-gate rule + rank program via composer
# ---------------------------------------------------------------------------
def test_agent_authors_gate_and_rank_via_graph_composer():
    ag = _fresh_agent()
    ind = rf.induce_concern(ag, [["correct", "DIVERGENCE", "by", "CANDIDATE"]], name_hint="sc_authors")
    key = ind["capability_key"]
    before = ag.inner.rule_count()
    g = rf.ground_concern(ag, [key])
    after = ag.inner.rule_count()

    assert g.get("grounded") is True, g.get("wall")
    assert g.get("served_by") == "graph"
    assert g.get("path") == "compose_self_correct_rule"
    assert after - before == 1, "exactly one Rule authored (the Program is not a Rule)"

    gate = g["rule"]
    assert gate["name"] == "self_correct_gate_" + key
    assert gate["match"] == [["ag", "surprised_by", "mi"], ["mi", "about_model", "cm"]]
    assert gate["effects"][0][:4] == ["set_attr", "mi", "correct_ready", True]

    prog = g["program"]
    assert prog["type"] == "Argmin"
    assert prog["source"]["source"]["node_type"] == "CorrectionCandidate"


def test_re_grounding_is_idempotent_no_rechurn():
    ag = _fresh_agent()
    ind = rf.induce_concern(ag, [["correct", "DIVERGENCE", "by", "CANDIDATE"]], name_hint="sc_idem")
    key = ind["capability_key"]
    rf.ground_concern(ag, [key])
    rc1 = ag.inner.rule_count()
    rf.ground_concern(ag, [key])
    rc2 = ag.inner.rule_count()
    assert rc1 == rc2


# ---------------------------------------------------------------------------
# 3. THE ATTEMPT-GATE -- discriminative: fast growth gated, slow growth not.
# ---------------------------------------------------------------------------
def test_gate_marks_correct_ready_on_fast_growing_divergence():
    ag = _fresh_agent()
    _ground_collapse_watch(ag)
    _ground_self_correct(ag)
    _shape_decode_ready(ag)
    for i in range(3):
        _add_pending_observation(ag, f"zzzgatehi{i}")

    res = cw.scan_and_predict(ag)
    assert res.converged is False
    ag.inner.run_rules(2000)

    imp = _impasses(ag)
    assert len(imp) == 1
    assert ag.s.node(imp[0])["attrs"].get("correct_ready") is True


def test_gate_leaves_slow_growing_divergence_unmarked():
    ag = _fresh_agent()
    _ground_collapse_watch(ag)
    _ground_self_correct(ag)
    _shape_decode_ready(ag)
    _add_pending_observation(ag, "zzzgatelo0")   # a single observation -> growth_rate=1.0, below threshold

    res = cw.scan_and_predict(ag)
    assert res.converged is False, "still a genuine (if slow) divergence"
    ag.inner.run_rules(2000)

    imp = _impasses(ag)
    assert len(imp) == 1
    assert ag.s.node(imp[0])["attrs"].get("correct_ready") is None, \
        "below the agent's own cost-worth-it threshold -- never marked (discriminative)"


def test_scan_and_self_correct_skips_impasse_not_marked_correct_ready():
    ag = _fresh_agent()
    _ground_collapse_watch(ag)
    _ground_self_correct(ag)
    _shape_decode_ready(ag)
    _add_pending_observation(ag, "zzzskip0")
    cw.scan_and_predict(ag)
    ag.inner.run_rules(2000)
    imp = _impasses(ag)
    assert ag.s.node(imp[0])["attrs"].get("correct_ready") is None

    before_rc = ag.inner.rule_count()
    out = scd.scan_and_self_correct(ag)
    after_rc = ag.inner.rule_count()
    assert out == [], "the agent chose not to spend correction effort on this one"
    assert before_rc == after_rc
    assert ag.s.node(imp[0])["attrs"].get("self_correction_attempted") is None


def test_absent_correct_ready_never_attempts_even_with_predicted_divergence():
    """Contrast: WITHOUT the self_correct concern grounded at all (no gate
    rule ever authored), a genuine predicted-divergence Impasse still
    escalates (predict_intervene_<tag> is unconditional) but is NEVER
    marked correct_ready, so scan_and_self_correct leaves it alone --
    the gate is genuinely earned by the composer, not always-on."""
    ag = _fresh_agent()
    _ground_collapse_watch(ag)
    _shape_decode_ready(ag)
    for i in range(3):
        _add_pending_observation(ag, f"zzznogate{i}")

    res = cw.scan_and_predict(ag)
    assert res.converged is False
    ag.inner.run_rules(2000)

    imp = _impasses(ag)
    assert len(imp) == 1, "the tier-4 guard must still escalate"
    assert ag.s.node(imp[0])["attrs"].get("correct_ready") is None

    out = scd.scan_and_self_correct(ag)
    assert out == []


# ---------------------------------------------------------------------------
# 4. THE RANK -- prefers the cheaper/less-invasive candidate, order-independent.
# ---------------------------------------------------------------------------
def test_rank_prefers_cheaper_candidate_regardless_of_input_order():
    ag = _fresh_agent()
    _ground_self_correct(ag, "rank_t")
    native = rf._native_eval2(ag.s)
    probe, cheap, expensive = _probe_rule_fixture()
    native.add_rule(probe)

    cands_a = [{"label": "cheap_fix", "rules": {"probe_rule": cheap}},
               {"label": "expensive_fix", "rules": {"probe_rule": expensive}}]
    cands_b = [{"label": "expensive_fix", "rules": {"probe_rule": expensive}},
               {"label": "cheap_fix", "rules": {"probe_rule": cheap}}]

    ranked_a = scd.rank_candidates(ag, native, cands_a)
    ranked_b = scd.rank_candidates(ag, native, cands_b)
    assert ranked_a[0]["label"] == "cheap_fix", ranked_a
    assert ranked_b[0]["label"] == "cheap_fix", ranked_b
    assert {c["label"] for c in ranked_a} == {c["label"] for c in ranked_b} == {"cheap_fix", "expensive_fix"}


def test_rank_mints_correction_candidate_audit_nodes():
    ag = _fresh_agent()
    _ground_self_correct(ag, "rank_audit")
    native = rf._native_eval2(ag.s)
    probe, cheap, expensive = _probe_rule_fixture()
    native.add_rule(probe)
    before = len(list(ag.s.nodes("CorrectionCandidate")))
    scd.rank_candidates(ag, native, [{"label": "cheap_fix", "rules": {"probe_rule": cheap}},
                                      {"label": "expensive_fix", "rules": {"probe_rule": expensive}}])
    after = len(list(ag.s.nodes("CorrectionCandidate")))
    assert after - before == 2


def test_rank_falls_back_unchanged_when_fewer_than_two_usable_candidates():
    ag = _fresh_agent()
    _ground_self_correct(ag, "rank_single")
    native = rf._native_eval2(ag.s)
    cands = [{"label": "only_one", "rules": {"probe_rule": {"name": "x"}}}, {"label": "inert", "rules": {}}]
    ranked = scd.rank_candidates(ag, native, cands)
    assert ranked == cands, "nothing to rank -- returned unchanged, never a fabricated preference"


def test_rank_falls_back_unchanged_when_concern_never_grounded():
    ag = _fresh_agent()   # self_correct never grounded on this agent -- no rank Program exists
    native = rf._native_eval2(ag.s)
    probe, cheap, expensive = _probe_rule_fixture()
    native.add_rule(probe)
    cands = [{"label": "cheap_fix", "rules": {"probe_rule": cheap}},
             {"label": "expensive_fix", "rules": {"probe_rule": expensive}}]
    ranked = scd.rank_candidates(ag, native, cands)
    assert ranked == cands


# ---------------------------------------------------------------------------
# 5. THE AUTONOMOUS LOOP STILL CLOSES -- ticks-only, agent gates + ranks.
# ---------------------------------------------------------------------------
def test_full_loop_non_frozen_divergence_gated_corrected_converges():
    ag = _fresh_agent()
    _ground_collapse_watch(ag)
    _ground_self_correct(ag)
    _shape_decode_ready(ag)
    _skippable_provenance(ag)
    for i in range(3):
        _add_pending_observation(ag, f"zzzloopnfA{i}")

    cw.scan_and_predict(ag)
    ag.inner.run_rules(2000)
    imp = _impasses(ag)
    assert ag.s.node(imp[0])["attrs"].get("correct_ready") is True

    # continued perception -- the backlog the first run_rules pass drained keeps arriving,
    # the SAME "simulating continuous per-frame perception" scenario domains/collapse_
    # model.py's own module docstring names for the real 2026-07-03 axis-runaway incident.
    for i in range(3):
        _add_pending_observation(ag, f"zzzloopnfB{i}")

    before_rc = ag.inner.rule_count()
    out = scd.scan_and_self_correct(ag)
    after_rc = ag.inner.rule_count()

    assert len(out) == 1
    result = out[0]["result"]
    assert result["escalated"] is False
    assert result["adopted"] is True
    assert result["chosen"] == "dedup_identity_fix"
    assert result["model_final"].converged is True
    assert after_rc > before_rc
    assert ag.s.node(imp[0])["attrs"].get("self_correction_attempted") is True
    # re-scanning does not re-attempt the same impasse
    out2 = scd.scan_and_self_correct(ag)
    assert out2 == []


def test_full_loop_frozen_divergence_gated_proposal_raised_no_live_mutation():
    ag = _fresh_agent()
    _ground_collapse_watch(ag)
    _ground_self_correct(ag)
    _shape_decode_ready(ag)
    _frozen_provenance(ag)
    for i in range(3):
        _add_pending_observation(ag, f"zzzloopfrA{i}")

    cw.scan_and_predict(ag)
    ag.inner.run_rules(2000)
    imp = _impasses(ag)
    assert ag.s.node(imp[0])["attrs"].get("correct_ready") is True

    for i in range(3):
        _add_pending_observation(ag, f"zzzloopfrB{i}")

    before_rc = ag.inner.rule_count()
    before_active = sorted(r.get("name") for r in ag.inner.export_rules()
                            if isinstance(r, dict) and r.get("active", True))
    out = scd.scan_and_self_correct(ag)
    after_rc = ag.inner.rule_count()
    after_active = sorted(r.get("name") for r in ag.inner.export_rules()
                           if isinstance(r, dict) and r.get("active", True))

    assert len(out) == 1
    result = out[0]["result"]
    assert result["chosen"] == "dedup_identity_fix", "a working fix WAS found in imagination"
    assert result["adopted"] is False
    assert result["escalated"] is True
    assert result["denied"], "both sd_mint_quantum and sd_dedup_existing are frozen-provenance"

    proposal = result["proposal"]
    assert ag.s.has_node(proposal)
    assert ag.s.node(proposal)["attrs"]["status"] == "pending_human_approval"

    # THE SAFETY BOUNDARY: no frozen rule mutated -- denylist enforcement is
    # entirely inside domains/self_correction.py, untouched by this task.
    assert after_rc == before_rc
    assert after_active == before_active
