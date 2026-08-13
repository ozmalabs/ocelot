"""GAMMA_PRODUCTION_ADOPT_HANDLER: the missing `gamma_production`
StandingConcern -> judge -> adopt handler, closing the honest gap
GAMMA_COLLAPSE_ALGORITHM_RESULTS.md's Q2 named (no dedicated handler existed;
a promoted `gamma_production` concern fell through to the generic
`comprehend_first` default).

See docs/research/engine_substrate/GAMMA_PRODUCTION_ADOPT_HANDLER_PREREG.md
and _RESULTS.md. This file is the `test_gamma_collapse_algorithm_migrated.py`
precedent extended one rung further: recurrence -> mint -> promote ->
`_concern_tick` JUDGES (never adopts) -> the explicit, human-gated
`adopt_gamma_production_standing` ADOPTS -> `is_edge_admissible` flips on the
exact triple, stays False on an unrelated one, the original SelfConcern
resolves. Theorem XII (reference-monitor containment) is checked explicitly
throughout: no rule anywhere calls `add_production`; only the one explicit
adopt call does, and only for the exact adopted triple.
"""
from __future__ import annotations

import json
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds
from substrate_rs import NodeID as _NodeID

jd = pytest.importorskip("jabberwock_daemon")


@pytest.fixture(autouse=True)
def _no_real_seed_writes(monkeypatch):
    monkeypatch.setenv("OZMA_SEED_PERSIST_DISABLED", "1")


@pytest.fixture()
def agent():
    # Fresh, isolated agent per test — the `gamma_residual_capture` flag and
    # the GammaResidual population are process-wide, same reasoning as
    # test_gamma_collapse_algorithm_migrated.py's own fixture.
    a = WorldAdapter(seeds=())
    load_all_seeds(a)  # sweeps seeds/*.json, including gamma_residual.json AND
                       # gamma_production_adopt.json
    return a


def _self_concerns(agent, kind=None):
    out = []
    for n in agent.s.nodes("SelfConcern"):
        attrs = agent.s.node(n)["attrs"]
        if kind is None or attrs.get("kind") == kind:
            out.append((n, attrs))
    return out


def _register_vocab_for_clean_type1(agent, edge_type):
    """The test_gamma_collapse_algorithm_migrated.py precedent, verbatim:
    registers GammaSpikeFoo/GammaSpikeBar/`edge_type` in the live grammar's
    vocabulary WITHOUT admitting GammaSpikeFoo -[edge_type]-> GammaSpikeBar —
    a genuine Type-1 rejection setup."""
    agent.s.add_production({"src": {"type": "GammaSpikeFoo", "var": "x"},
                            "edge_type": "gs_unrelated",
                            "tgt": {"type": "GammaSpikeFoo", "var": "y"}})
    agent.s.add_production({"src": {"type": "GammaSpikeBar", "var": "x"},
                            "edge_type": edge_type,
                            "tgt": {"type": "GammaSpikeBar", "var": "y"}})


def _mint_and_promote_gamma_production(agent, edge_type):
    """Recurrence (support >= 2) -> mint -> promote, through the REAL
    pipeline (not a hand-authored SelfConcern) so this exercises the exact
    content-string format `judge_gamma_production_gap` must parse. Returns
    (sc_node, standing_node_id_int, promote_result)."""
    agent.s._inner.set_gamma_residual_capture(True)
    a_node = agent.s.add_node("GammaSpikeFoo", {})
    b1 = agent.s.add_node("GammaSpikeBar", {})
    b2 = agent.s.add_node("GammaSpikeBar", {})
    _register_vocab_for_clean_type1(agent, edge_type)
    for t in (b1, b2):
        with pytest.raises(Exception):
            agent.s.add_edge(a_node, edge_type, t)
        agent.s.tick()

    concerns = _self_concerns(agent, kind="gamma_production")
    target = next((n, a) for n, a in concerns if edge_type in a["content"])
    sc_node, sc_attrs = target
    id_str = str(sc_node.value if hasattr(sc_node, "value") else sc_node)
    res = jd.promote_self_concern(agent, id_str)
    assert res["ok"], res
    assert res["pipeline"] == "comprehend_first", (
        "promotion itself is UNCHANGED (GAMMA_COLLAPSE_ALGORITHM_RESULTS.md Q2's "
        "own GO bar) -- the dedicated handler routes at _concern_tick, not here")
    return sc_node, res["standing_concern"], res


# =========================================================================== #
#  JUDGE — synchronous, safe, read-only. Never adopts.
# =========================================================================== #
def test_concern_tick_judges_ready_for_adopt_not_generic_fallback(agent):
    sc_node, standing_id, res = _mint_and_promote_gamma_production(agent, "gp_judge_edge")
    standing = _NodeID(standing_id)

    jd._concern_tick(agent)

    at = agent.s.node(standing)["attrs"]
    assert at["status"] == "processed"
    assert at["gamma_production_judge_status"] == "ready_for_adopt"
    assert "GammaSpikeFoo" in at["gamma_production_judge_reason"]
    assert "gp_judge_edge" in at["gamma_production_judge_reason"]

    candidate = json.loads(at["gamma_production_candidate"])
    assert candidate["src"]["type"] == "GammaSpikeFoo"
    assert candidate["edge_type"] == "gp_judge_edge"
    assert candidate["tgt"]["type"] == "GammaSpikeBar"

    # THE JUDGE STEP MUST NOT HAVE ADOPTED ANYTHING.
    a_node = next(iter(agent.s.nodes("GammaSpikeFoo")))
    assert agent.s.is_edge_admissible(a_node, "gp_judge_edge", "GammaSpikeBar", None) is False
    # No ARC/conversation experiment was spawned for this kind.
    assert list(agent.s.nodes("Experiment")) == []


def test_run_rules_marks_awaiting_adopt_from_the_judge_datum(agent):
    sc_node, standing_id, res = _mint_and_promote_gamma_production(agent, "gp_awaiting_edge")
    standing = _NodeID(standing_id)

    jd._concern_tick(agent)
    assert not agent.s.node(standing)["attrs"].get("awaiting_adopt")

    agent.s._inner.run_rules(400000)
    at = agent.s.node(standing)["attrs"]
    assert at.get("awaiting_adopt") is True


# =========================================================================== #
#  ADOPT — the ONE gated call site. Live before/after + Theorem XII.
# =========================================================================== #
def test_adopt_gamma_production_standing_flips_check_edge_and_resolves_concern(agent):
    sc_node, standing_id, res = _mint_and_promote_gamma_production(agent, "gp_adopt_edge")
    standing = _NodeID(standing_id)

    jd._concern_tick(agent)
    agent.s._inner.run_rules(400000)
    assert agent.s.node(standing)["attrs"]["gamma_production_judge_status"] == "ready_for_adopt"

    a_node = next(iter(agent.s.nodes("GammaSpikeFoo")))
    assert agent.s.is_edge_admissible(a_node, "gp_adopt_edge", "GammaSpikeBar", None) is False, (
        "still inadmissible right up to the moment of the explicit adopt call")

    result = jd.adopt_gamma_production_standing(agent, str(standing_id))
    assert result["ok"], result
    assert tuple(result["triple"]) == ("GammaSpikeFoo", "gp_adopt_edge", "GammaSpikeBar")

    # THE EXACT TRIPLE is now admissible.
    assert agent.s.is_edge_admissible(a_node, "gp_adopt_edge", "GammaSpikeBar", None) is True
    b_node = next(iter(agent.s.nodes("GammaSpikeBar")))
    agent.s.add_edge(a_node, "gp_adopt_edge", b_node)  # must not raise now

    # AN UNRELATED TRIPLE (reverse direction) stays inadmissible — adoption
    # is scoped to the exact triple, not a blanket relaxation.
    assert agent.s.is_edge_admissible(b_node, "gp_adopt_edge", "GammaSpikeFoo", None) is False

    at = agent.s.node(standing)["attrs"]
    assert at["status"] == "adopted"
    assert agent.s.node(sc_node)["attrs"]["status"] == "resolved"


def test_adopt_gamma_production_standing_is_idempotent(agent):
    sc_node, standing_id, res = _mint_and_promote_gamma_production(agent, "gp_idempotent_edge")
    jd._concern_tick(agent)
    agent.s._inner.run_rules(400000)
    first = jd.adopt_gamma_production_standing(agent, str(standing_id))
    assert first["ok"], first
    second = jd.adopt_gamma_production_standing(agent, str(standing_id))
    assert second["ok"] is False
    assert "already adopted" in second["error"]


def test_adopt_refuses_before_judge_has_run(agent):
    """A StandingConcern still `pending` (never ticked by _concern_tick) has
    no `gamma_production_judge_status` at all — adopt must refuse, not guess
    or fall back to deriving a candidate itself."""
    sc_node, standing_id, res = _mint_and_promote_gamma_production(agent, "gp_premature_edge")
    result = jd.adopt_gamma_production_standing(agent, str(standing_id))
    assert result["ok"] is False
    assert "not ready for adopt" in result["error"]
    a_node = next(iter(agent.s.nodes("GammaSpikeFoo")))
    assert agent.s.is_edge_admissible(a_node, "gp_premature_edge", "GammaSpikeBar", None) is False


def test_adopt_refuses_unknown_or_wrong_kind_standing_concern(agent):
    bogus = jd.adopt_gamma_production_standing(agent, "999999999")
    assert bogus["ok"] is False

    # A comprehend_first-pipelined StandingConcern of a DIFFERENT kind must
    # be refused, not silently treated as a gamma_production adopt target.
    sc = agent.s.add_node("SelfConcern", {"status": "noted", "source": "implicit",
                                          "kind": "knowledge", "content": "photosynthesis"})
    agent.inner.add_edge_unchecked(agent.agent, "has_self_concern", sc)
    res = jd.promote_self_concern(agent, str(jd._nid_value(sc)))
    assert res["ok"]
    wrong_kind = jd.adopt_gamma_production_standing(agent, str(res["standing_concern"]))
    assert wrong_kind["ok"] is False
    assert "not a gamma_production concern" in wrong_kind["error"]


# =========================================================================== #
#  THE TWO OTHER JUDGE OUTCOMES — already_admissible (resolves directly, no
#  adopt) and unresolvable (experiments_exhausted, the note_prog_read_
#  composition_exhausted precedent).
# =========================================================================== #
def test_already_admissible_outcome_resolves_the_concern_without_any_adopt_call(agent):
    """Simulates the world having moved on between mint and judge (e.g. some
    OTHER out-of-band adopt already covered this exact triple) — the judge
    step must recognise this honestly and resolve the ORIGINAL SelfConcern
    directly, never needing (or permitting) a redundant adopt call."""
    sc_node, standing_id, res = _mint_and_promote_gamma_production(agent, "gp_already_edge")
    standing = _NodeID(standing_id)

    # Out-of-band: something else already made this triple admissible.
    agent.s.add_production({
        "src": {"type": "GammaSpikeFoo", "var": "x"},
        "edge_type": "gp_already_edge",
        "tgt": {"type": "GammaSpikeBar", "var": "y"},
        "provenance": "test:already_admissible_setup",
    })

    jd._concern_tick(agent)
    at = agent.s.node(standing)["attrs"]
    assert at["gamma_production_judge_status"] == "already_admissible"
    assert "gamma_production_candidate" not in at, "nothing to adopt -- no candidate is built"

    agent.s._inner.run_rules(400000)
    assert agent.s.node(sc_node)["attrs"]["status"] == "resolved"

    # adopt must now refuse (never "ready for adopt").
    refused = jd.adopt_gamma_production_standing(agent, str(standing_id))
    assert refused["ok"] is False


def test_unresolvable_content_marks_experiments_exhausted(agent):
    """A gamma_production SelfConcern whose content does NOT match
    note_gamma_production_gap's own StringConcat template (a malformed/
    hand-authored one, standing in for a future format drift) is honestly
    exhausted, never silently treated as ready or crashing the tick loop."""
    sc = agent.s.add_node("SelfConcern", {"status": "noted", "source": "implicit",
                                          "kind": "gamma_production",
                                          "content": "not the expected sentence shape at all"})
    agent.inner.add_edge_unchecked(agent.agent, "has_self_concern", sc)
    res = jd.promote_self_concern(agent, str(jd._nid_value(sc)))
    assert res["ok"]
    standing = _NodeID(res["standing_concern"])

    jd._concern_tick(agent)
    at = agent.s.node(standing)["attrs"]
    assert at["gamma_production_judge_status"] == "unresolvable"
    assert "could not parse" in at["gamma_production_judge_reason"]

    agent.s._inner.run_rules(400000)
    at = agent.s.node(standing)["attrs"]
    assert at["experiments_exhausted"] is True
    assert "could not parse" in at["exhausted_note"]


# =========================================================================== #
#  THEOREM XII — no rule anywhere calls add_production; only the explicit
#  gated adopt function does, for the exact adopted triple only.
# =========================================================================== #
def test_no_seed_rule_effect_calls_add_production():
    """Static check on the two seed files this rung touches/adds — the
    reference-monitor invariant must hold BY CONSTRUCTION, not just by
    observed behaviour."""
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for fname in ("gamma_residual.json", "gamma_production_adopt.json"):
        path = os.path.join(root, "seeds", fname)
        with open(path) as f:
            manifest = json.load(f)
        blob = json.dumps(manifest.get("rules", []))
        assert "add_production" not in blob, (
            "%s must never call add_production from a rule effect" % fname)


def test_gamma_production_growth_module_has_exactly_one_add_production_call_site():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(root, "domains", "gamma_production_growth.py")
    with open(path) as f:
        src = f.read()
    # One call site (adopt_gamma_production's own `sub.add_production(...)`)
    # plus this module's own docstring/comment mentions of the string —
    # the CALL SITE itself (`.add_production(`) must appear exactly once.
    assert src.count(".add_production(") == 1


def test_judge_alone_through_run_rules_never_changes_admissibility(agent):
    """Recurrence -> mint -> promote -> _concern_tick -> run_rules (the full
    JUDGE side of the pipeline, including every seed rule this rung adds)
    must never, by itself, flip is_edge_admissible for the triple."""
    sc_node, standing_id, res = _mint_and_promote_gamma_production(agent, "gp_theorem_edge")
    jd._concern_tick(agent)
    agent.s._inner.run_rules(400000)
    a_node = next(iter(agent.s.nodes("GammaSpikeFoo")))
    assert agent.s.is_edge_admissible(a_node, "gp_theorem_edge", "GammaSpikeBar", None) is False
