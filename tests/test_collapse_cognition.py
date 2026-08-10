"""test_collapse_cognition -- TIER 4 COGNITION: the agent's own authored
rules that USE the `CollapseModel` (`domains/collapse_model.py`'s
`predict_collapse` -- fixed points / volatile frontier / converged-or-
diverging), not just measure it. Fast pytest twin of
`scripts/jabberwock_watches_its_collapse.py` (read that script's module
docstring for the full narrative).

THE MACHINERY (read-only here, never modified): `domains/collapse_model.py`
(`predict_collapse` -- structural fixed-point/volatile-frontier enumeration
+ a bounded tier-3 forward-look, pure host measurement per that module's own
docstring) and `domains/collapse_watch.py` (`scan_and_predict` -- the
mechanical host hook that calls it and wires `agent -has_collapse_model->
model`, the same "mechanical exposure of an already-computed flag to the
rule engine" idiom `domains.reflective_faculty.ensure_grounding_gap_edges`
uses for `GroundingGap`).

THIS FILE covers the follow-on: the agent's OWN decision about WHAT TO DO
with the model. Per CLAUDE.md's discipline, no test here hand-installs the
three collapse-watch rules -- every test either (a) proves the concern
genuinely walls before the new cue exists, or (b) drives `induce_concern` ->
`ground_concern` and reads back what the agent's own composer (`seeds/
composer_collapse_watch_graph.json`, dispatched via the new 'collapse_watch'
RelationCue + 'predict' ComposerCue) authored, or (c) drives the full
predict -> attend/recognize/escalate -> (tier-3 imagination engage) pipeline
on a real booted agent and reads the graph state back.

No seed file is mutated at runtime by anything this file exercises (`teach`
is never called by `ground_concern`'s composer-dispatch path, nor by
`domains.collapse_watch.scan_and_predict`) so no snapshot-guard fixture is
needed for seeds/relation_vocabulary.json / seeds/composer_dispatch.json /
seeds/composer_collapse_watch_graph.json / seeds/composer_imagination_graph
.json -- the same claim tests/test_imagination_cognition.py makes for its
own seeds.
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
from domains import imagination_dispatch as idisp         # noqa: E402


class _Agent:
    """Minimal duck-typed agent wrapper -- identical shape to
    tests/test_imagination_cognition.py's own `_Agent` (harness glue only,
    no source modified)."""
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


def _ground_imagination(ag, tag="imag_t"):
    return _ground(ag, ["imagine", "COLLAPSE", "from", "IMPASSE"], tag)


def _shape_decode_ready(ag):
    native = rf._native_eval2(ag.s)
    rf._ensure_shape_decode_loop(ag.s, native, ag.agent)


def _add_pending_observation(ag, key: str):
    obs = ag.s.add_node("Observation", {"signature": [[key, "X"]], "key": [key], "status": "pending"})
    ag.s.add_edge(ag.agent, "observed", obs)
    return obs


# ---------------------------------------------------------------------------
# 1. the vocabulary genuinely walls before this change (proof, not assumed)
# ---------------------------------------------------------------------------
def test_existing_vocabulary_walls_on_predict_before_new_cue():
    s, agent_node = boot_core()
    ag = _Agent(s, agent_node)
    m = dict(manifest_for("relation_vocabulary"))
    m["nodes"] = [n for n in m["nodes"] if n["attrs"].get("name") != "collapse_watch"]
    ag.s._inner.load_seed_manifest(m, ag.agent)

    ind = rf.induce_concern(ag, [["predict", "COLLAPSE", "of", "DIVERGENCE"]], name_hint="wall_probe")
    assert ind.get("minted") is True
    res = rf.ground_concern(ag, [ind["capability_key"]])
    assert res.get("grounded") is False
    assert res.get("path") == "predicate_grounding"


def test_predict_cue_loads_and_dispatches_to_collapse_watch_composer():
    ag = _fresh_agent()
    name = rf._pick_composer(ag.s, ag.inner, ag.agent, {"predict"})
    assert name == "collapse_watch"


# ---------------------------------------------------------------------------
# 2. the jabberwock AUTHORS the three collapse-watch rules via the composer
# ---------------------------------------------------------------------------
def test_agent_authors_three_collapse_watch_rules_via_graph_composer():
    ag = _fresh_agent()
    ind = rf.induce_concern(ag, [["predict", "COLLAPSE", "of", "DIVERGENCE"]],
                             name_hint="cw_authors")
    key = ind["capability_key"]
    before = ag.inner.rule_count()
    g = rf.ground_concern(ag, [key])
    after = ag.inner.rule_count()

    assert g.get("grounded") is True, g.get("wall")
    assert g.get("served_by") == "graph"
    assert g.get("path") == "compose_collapse_watch_rule"
    assert after - before == 3, "exactly three rules authored"

    by_name = {r["name"]: r for r in g["rules"]}
    attend = by_name["attend_frontier_" + key]
    assert attend["match"] == [["ag", "has_collapse_model", "cm"], ["cm", "volatile_frontier", "vn"]]
    assert len(attend["effects"]) == 1
    assert attend["effects"][0][:4] == ["add_edge", "ag", "attends_frontier", "vn"]

    recog = by_name["recognize_self_" + key]
    assert recog["match"] == [["ag", "has_collapse_model", "cm"], ["cm", "fixed_point", "fp"]]
    assert len(recog["effects"]) == 1
    assert recog["effects"][0][:4] == ["add_edge", "ag", "recognizes_as_self", "fp"]
    # NEVER a set_attr on the matched fixed point (the frozen-core discipline)
    assert all(eff[0] != "set_attr" for eff in recog["effects"])

    intervene = by_name["predict_intervene_" + key]
    assert intervene["match"] == [["ag", "has_collapse_model", "cm"]]
    assert intervene["effects"][0][:3] == ["add_node", "mi", "Impasse"]
    assert intervene["effects"][0][3]["kind"] == "predicted_divergence"
    assert intervene["effects"][1][:4] == ["add_edge", "ag", "surprised_by", "mi"]
    assert intervene["effects"][2][:4] == ["add_edge", "mi", "about_model", "cm"]
    assert intervene["effects"][3][:4] == ["add_edge", "mi", "about_axis", "cm"]
    # never a set_attr on cm either (self-inclusion invariant)
    assert all(eff[0] != "set_attr" or eff[1] != "cm" for eff in intervene["effects"])


def test_re_grounding_is_idempotent_no_rechurn():
    ag = _fresh_agent()
    ind = rf.induce_concern(ag, [["predict", "COLLAPSE", "of", "DIVERGENCE"]], name_hint="cw_idem")
    key = ind["capability_key"]
    rf.ground_concern(ag, [key])
    rc1 = ag.inner.rule_count()
    rf.ground_concern(ag, [key])
    rc2 = ag.inner.rule_count()
    assert rc1 == rc2


# ---------------------------------------------------------------------------
# 3. PREDICT-INTERVENE -- discriminative: diverging escalates, converged
#    does not.
# ---------------------------------------------------------------------------
def test_predict_intervene_fires_on_diverging_graph():
    ag = _fresh_agent()
    _ground_collapse_watch(ag)
    _shape_decode_ready(ag)
    for i in range(3):
        _add_pending_observation(ag, f"zzzcogrun{i}")

    res = cw.scan_and_predict(ag)
    assert res.converged is False, res.counts_trajectory
    ag.inner.run_rules(2000)

    impasses = [n for n in ag.s.nodes("Impasse")
                if ag.s.node(n)["attrs"].get("kind") == "predicted_divergence"]
    assert len(impasses) >= 1, "a predicted divergence must escalate"
    assert ag.s.has_edge(ag.agent, "surprised_by", impasses[0])

    # reaches the SAME standing autonomy channel too (mint_goal_from_surprise
    # has no kind filter -- ANY surprised_by edge to an unresolved Impasse
    # becomes a wanted Goal on its own, regardless of kind)
    wanted = list(ag.inner.neighbours(ag.agent, "wants"))
    assert impasses[0] in wanted, "the standing mint_goal_from_surprise channel must also fire"


def test_predict_intervene_does_not_fire_on_converged_graph():
    ag = _fresh_agent()
    _ground_collapse_watch(ag)
    # no pending Observations added -- an already-settled forward-look
    res = cw.scan_and_predict(ag)
    assert res.converged is True
    ag.inner.run_rules(2000)

    impasses = [n for n in ag.s.nodes("Impasse")
                if ag.s.node(n)["attrs"].get("kind") == "predicted_divergence"]
    assert impasses == [], "a converged prediction must never escalate (discriminative)"


def test_absent_collapse_model_never_intervenes():
    ag = _fresh_agent()
    _ground_collapse_watch(ag)
    # never called scan_and_predict -- no has_collapse_model edge exists at all
    ag.inner.run_rules(2000)
    impasses = [n for n in ag.s.nodes("Impasse")
                if ag.s.node(n)["attrs"].get("kind") == "predicted_divergence"]
    assert impasses == []


# ---------------------------------------------------------------------------
# 4. ATTEND-FRONTIER -- discriminative: volatile gets marked, fixed does not
# ---------------------------------------------------------------------------
def test_attend_frontier_marks_volatile_not_fixed():
    ag = _fresh_agent()
    _ground_collapse_watch(ag)
    _shape_decode_ready(ag)
    for i in range(2):
        _add_pending_observation(ag, f"zzzattend{i}")

    res = cw.scan_and_predict(ag)
    ag.inner.run_rules(2000)

    fixed_ids = set(ag.inner.neighbours(res.model_node, "fixed_point"))
    volatile_ids = set(ag.inner.neighbours(res.model_node, "volatile_frontier"))
    assert volatile_ids, "the runaway scenario must produce a non-empty volatile frontier"
    attended = set(ag.inner.neighbours(ag.agent, "attends_frontier"))

    assert volatile_ids <= attended, "every sampled volatile-frontier node must be attended"
    assert not (fixed_ids & attended), "no fixed point may ever be marked as frontier (discriminative)"


# ---------------------------------------------------------------------------
# 5. RECOGNIZE-SELF -- discriminative: fixed (incl. frozen core) recognized,
#    volatile is not; and the frozen Drive's own attrs are NEVER mutated.
# ---------------------------------------------------------------------------
def test_recognize_self_marks_fixed_including_frozen_core_not_volatile():
    ag = _fresh_agent()
    _ground_collapse_watch(ag)
    _shape_decode_ready(ag)
    for i in range(2):
        _add_pending_observation(ag, f"zzzself{i}")

    drives = [n for n in ag.s.nodes("Drive") if ag.s.node(n)["attrs"].get("frozen")]
    assert drives, "the frozen 'understand' Drive must exist in this fixture"
    drive = drives[0]
    before_attrs = dict(ag.s.node(drive)["attrs"])

    res = cw.scan_and_predict(ag)
    ag.inner.run_rules(2000)

    fixed_ids = set(ag.inner.neighbours(res.model_node, "fixed_point"))
    volatile_ids = set(ag.inner.neighbours(res.model_node, "volatile_frontier"))
    assert drive in fixed_ids, "the frozen Drive must be in the CollapseModel's own fixed_point sample"

    recognized = set(ag.inner.neighbours(ag.agent, "recognizes_as_self"))
    assert drive in recognized, "the frozen core must be recognised as stable self"
    assert not (volatile_ids & recognized), "no volatile node may ever be recognised as self (discriminative)"

    after_attrs = dict(ag.s.node(drive)["attrs"])
    assert before_attrs == after_attrs, "recognize_self must NEVER mutate the frozen Drive's own attrs"


def test_re_scan_does_not_rechurn_recognition_edges():
    ag = _fresh_agent()
    _ground_collapse_watch(ag)
    cw.scan_and_predict(ag)
    ag.inner.run_rules(2000)
    n1 = len(list(ag.inner.neighbours(ag.agent, "recognizes_as_self")))
    ag.inner.run_rules(2000)
    n2 = len(list(ag.inner.neighbours(ag.agent, "recognizes_as_self")))
    assert n1 == n2, "the fixpoint guard must stop re-adding the same edge every pass"


# ---------------------------------------------------------------------------
# 6. THE STACK CLOSES -- tier 4 predicts -> tier 3 imagines. The predicted-
#    divergence Impasse reaches composer_imagination_graph.json's OWN
#    engage_imagine_cost_worth_<tag> rule (its kind-guard widened by one
#    Or-arm, see that seed's own updated description), which mints an
#    ImagineRequest -- the tier-4 -> tier-3 handoff, demonstrated live.
# ---------------------------------------------------------------------------
def test_stack_closes_predicted_divergence_reaches_imagination_engage_rule():
    ag = _fresh_agent()
    _ground_collapse_watch(ag)
    _ground_imagination(ag)
    _shape_decode_ready(ag)
    for i in range(3):
        _add_pending_observation(ag, f"zzzstack{i}")

    res = cw.scan_and_predict(ag)
    assert res.converged is False
    ag.inner.run_rules(2000)

    impasses = [n for n in ag.s.nodes("Impasse")
                if ag.s.node(n)["attrs"].get("kind") == "predicted_divergence"]
    assert len(impasses) == 1
    imp = impasses[0]

    requests = list(ag.s.nodes("ImagineRequest"))
    assert len(requests) >= 1, "the widened engage_imagine_cost_worth_<tag> rule must mint a request"
    # the request must be wired to THIS impasse via about_impasse
    linked = [r for r in requests if ag.s.has_edge(r, "about_impasse", imp)]
    assert linked, "the minted ImagineRequest must trace back to the predicted-divergence impasse"
    r = linked[0]
    assert ag.s.node(r)["attrs"]["status"] == "requested"
    axes = list(ag.inner.neighbours(r, "focuses_on_axis"))
    assert res.model_node in axes, "the request's focus must resolve to the CollapseModel itself"

    # imp.imagine_requested must now be set (the engage rule's own guard marker)
    assert ag.s.node(imp)["attrs"].get("imagine_requested") is True

    # run the mechanical dispatch hook -- imagine()/reground() cannot run
    # inside a Rust rule effect, exactly why domains/imagination_dispatch.py
    # exists. Even a trivial imagined intervention counts: this proves the
    # tier-4 -> tier-3 handoff actually fires end to end.
    before_imaginations = len(list(ag.s.nodes("Imagination")))
    touched = idisp.scan_and_imagine(ag)
    assert len(touched) >= 1
    after_imaginations = len(list(ag.s.nodes("Imagination")))
    assert after_imaginations > before_imaginations, \
        "scan_and_imagine must produce a genuine Imagination trace from the tier-4 escalation"


def test_predicted_divergence_never_reaches_imagine_without_imagination_grounded():
    """Contrast: WITHOUT the imagination concern grounded (no engage rule
    installed), the SAME predicted-divergence Impasse still escalates
    (mint_goal_from_surprise, kind-agnostic) but never mints an
    ImagineRequest -- the tier-3 hand-off is genuinely earned by the
    composer, not always-on."""
    ag = _fresh_agent()
    _ground_collapse_watch(ag)
    _shape_decode_ready(ag)
    for i in range(3):
        _add_pending_observation(ag, f"zzznoimag{i}")

    res = cw.scan_and_predict(ag)
    assert res.converged is False
    ag.inner.run_rules(2000)

    impasses = [n for n in ag.s.nodes("Impasse")
                if ag.s.node(n)["attrs"].get("kind") == "predicted_divergence"]
    assert len(impasses) == 1, "the guard must still escalate"
    assert list(ag.s.nodes("ImagineRequest")) == [], \
        "WITHOUT the imagination composer grounded, no ImagineRequest may appear"
