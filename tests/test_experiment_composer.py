"""test_experiment_composer — the self-build composer's METASCIENCE path (new
`_compose_experiment_rule` in domains/reflective_faculty.py, dispatched via
seeds/composer_dispatch.json's 'experiment' composer, grounded via the 4 new
RelationCue nodes in seeds/relation_vocabulary.json: hypothesis_test/vary_self/
dispatch_variant/judge_outcome -> test/vary/send/judge relation heads).

Per CLAUDE.md's discipline: the AGENT authors the mint/analyse rules itself, from a
framed concern, via induce_concern -> ground_concern -> the composer registry. This
file never hand-installs the experiment-minting/outcome-judging rule; it only frames
concerns, mints trigger observations, and reads back what the agent authored.

Fast tests (0-4) use `boot_core()` + the lightweight `Agent` duck-type wrapper (the
SAME harness `tests/fixtures/composer_driver_parity/capture.py` uses) with only the
`relation_vocabulary` seed manually loaded — `induce_concern`/`ground_concern` lazily
bootstrap the rest of what they need (shape_decode_loop, composer_dispatch) on
demand, so no full `load_all_seeds()` boot is needed for these. The one truly
end-to-end test (spawning a real offline child process via
`domains.experiment_dispatch.scan_and_dispatch`) is marked `slow`, mirroring
`tests/test_experiment_dispatch.py`'s own pattern.
"""
from __future__ import annotations

import time

import pytest

from substrate.boot_core import boot_core
from substrate.seed_loader import manifest_for
import domains.reflective_faculty as rf


# ---------------------------------------------------------------------------
# Minimal duck-typed agent wrapper for induce_concern/ground_concern (identical
# shape to tests/fixtures/composer_driver_parity/capture.py's `Agent` — harness
# glue only, no source modified).
# ---------------------------------------------------------------------------
class _Agent:
    def __init__(self, s, agent_node):
        self.s = s
        self.inner = s._inner
        self.agent = agent_node


def _fresh_agent_with_lexicon() -> _Agent:
    s, agent_node = boot_core()
    ag = _Agent(s, agent_node)
    ag.s._inner.load_seed_manifest(manifest_for("relation_vocabulary"), ag.agent)
    return ag


_SELF_EXPERIMENT_OBS = [
    ["test", "HYPOTHESIS", "about", "SELF"],
    ["vary", "SEED", "by", "DELTA"],
    ["send", "VARIANT", "to", "WORLD"],
    ["judge", "TRIAL", "by", "OUTCOME"],
]


# ---------------------------------------------------------------------------
# 1 — the 4 new RelationCue nodes load with the expected relation tuples.
# ---------------------------------------------------------------------------
def test_relation_cues_load():
    ag = _fresh_agent_with_lexicon()
    cues = {at["name"]: at for at in (ag.s.node(n)["attrs"] for n in ag.s.nodes("RelationCue"))}
    for name in ("hypothesis_test", "vary_self", "dispatch_variant", "judge_outcome"):
        assert name in cues, f"missing RelationCue {name!r}"
    import json
    assert json.loads(cues["hypothesis_test"]["relation"]) == ["test", "HYPOTHESIS", "by", "TRIAL"]
    assert json.loads(cues["vary_self"]["relation"]) == ["vary", "SELF", "by", "DELTA"]
    assert json.loads(cues["dispatch_variant"]["relation"]) == ["send", "VARIANT", "to", "WORLD"]
    assert json.loads(cues["judge_outcome"]["relation"]) == ["judge", "TRIAL", "by", "RESULT"]


# ---------------------------------------------------------------------------
# 2 — a residual that grounds to test/vary/send/judge picks the 'experiment'
#     composer (seeds/composer_dispatch.json) and it authors + installs BOTH
#     rules (mint + analyse) live.
# ---------------------------------------------------------------------------
def test_composer_selected_from_grounded_experiment_relations():
    ag = _fresh_agent_with_lexicon()
    ag.s.add_node("CapabilityAxis", {
        "is_axis": 1.0, "capability_keys": ["k1"], "induced": 1.0,
        "residual_predicates": ["test", "vary", "send", "judge"], "from_observation": 1.0,
        "source": "concern_induction",
    })
    before = ag.inner.rule_count()
    res = rf.ground_concern(ag, ["k1"])
    after = ag.inner.rule_count()

    assert res.get("grounded") is True
    assert res.get("path") == "compose_experiment_rule"
    assert res.get("form") == "experiment_rule"
    assert sorted(r[0] for r in res.get("grounded_relations", [])) == ["judge", "send", "test", "vary"]
    assert after - before == 2, "the composer must install exactly the mint + analyse rules"
    names = sorted(r["name"] for r in res.get("rules", []))
    assert names == ["author_experiment_from_residual_k1", "judge_experiment_outcome_k1"]


def test_composer_only_test_relation_authors_only_mint_rule():
    """When only 'test' grounds (no judge), just the MINT rule is built — the parts
    the composer authors depend on WHICH relations grounded, not a fixed blob."""
    ag = _fresh_agent_with_lexicon()
    ag.s.add_node("CapabilityAxis", {
        "is_axis": 1.0, "capability_keys": ["k2"], "induced": 1.0,
        "residual_predicates": ["test"], "from_observation": 1.0, "source": "concern_induction",
    })
    res = rf.ground_concern(ag, ["k2"])
    assert res.get("grounded") is True
    names = [r["name"] for r in res.get("rules", [])]
    assert names == ["author_experiment_from_residual_k2"]
    # no 'send' relation grounded -> the mint rule's match never binds a WorldInstance
    assert res["rules"][0]["match"] == [["ag", "observed", "obs"], ["obs", "minted", "axis"]]


def test_composer_only_judge_relation_authors_only_analysis_rule():
    ag = _fresh_agent_with_lexicon()
    ag.s.add_node("CapabilityAxis", {
        "is_axis": 1.0, "capability_keys": ["k3"], "induced": 1.0,
        "residual_predicates": ["judge"], "from_observation": 1.0, "source": "concern_induction",
    })
    res = rf.ground_concern(ag, ["k3"])
    assert res.get("grounded") is True
    names = [r["name"] for r in res.get("rules", [])]
    assert names == ["judge_experiment_outcome_k3"]


# ---------------------------------------------------------------------------
# 3 — the AUTHORED mint rule fires from a genuinely-induced residual axis and
#     mints Experiment + SeedDelta *itself*, in run_rules — no host add_node.
# ---------------------------------------------------------------------------
def test_mint_rule_fires_without_host_add_node():
    ag = _fresh_agent_with_lexicon()

    ind = rf.induce_concern(ag, _SELF_EXPERIMENT_OBS, name_hint="self_experiment_concern")
    key = ind.get("capability_key")
    assert ind.get("minted") is True
    g = rf.ground_concern(ag, [key])
    assert g.get("grounded") is True and g.get("path") == "compose_experiment_rule"

    # test scaffolding (host I/O, CLAUDE.md-legitimate): a perceived game world —
    # mechanical, same shape WorldAdapter.perceive_frame's ingest() produces.
    wi = ag.s.add_node("WorldInstance", {"world_type": "Game", "world_id": "game", "name": "navigate"})
    ag.inner.add_edge_unchecked(ag.agent, "knows", wi)

    # the triggering condition: a SEPARATE, later-arising unexplained residual (a
    # genuine "I don't have a term for this" gap) — test scaffolding, per CLAUDE.md
    # ("reporting an observed fact" is legitimate ingest); the DECISION to mint an
    # Experiment for it is entirely the authored rule's.
    ind2 = rf.induce_concern(ag, [["puzzles", "ME", "about", "NAVIGATE"]], name_hint="navigate_efficacy_gap")
    assert ind2.get("minted") is True
    axis2 = next(n for n in ag.s.nodes("CapabilityAxis") if str(n) == str(ind2.get("axis_id")))

    before = set(ag.s.nodes("Experiment"))
    ag.inner.run_rules()
    after = set(ag.s.nodes("Experiment")) - before
    assert len(after) >= 1, "the agent's own mint rule must author at least the triggering axis's Experiment"

    exp = next(iter(ag.inner.neighbours(axis2, "tested_by")), None)
    assert exp is not None, "the triggering axis must carry a tested_by edge to ITS OWN Experiment"
    ea = ag.s.node(exp)["attrs"]
    assert ea.get("status") == "requested"
    assert ea.get("game") == "navigate"
    assert ea.get("hypothesis") == ("a concern induced from an observation no held term-shape "
                                     "covers: puzzles")

    deltas = list(ag.inner.neighbours(exp, "has_delta"))
    assert len(deltas) == 1
    da = ag.s.node(deltas[0])["attrs"]
    assert da.get("skip_seeds") == "[]" and da.get("add_rules") == "[]"
    assert da.get("varied") == 1.0, "'vary' grounded -> the delta is flagged intentionally-varied"

    # idempotent: re-running must NOT mint a second Experiment for the same axis
    before2 = set(ag.s.nodes("Experiment"))
    ag.inner.run_rules()
    assert set(ag.s.nodes("Experiment")) == before2


# ---------------------------------------------------------------------------
# 4 — the AUTHORED analysis rule judges a produced Run by score-per-frame sign
#     (a held IfThenElse Term) and writes the verdict — all 3 branches.
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("score,frames,expected", [
    (1, 5, "supported"),
    (-2, 5, "refuted"),
    (0, 5, "inconclusive"),
])
def test_analysis_rule_judges_outcome(score, frames, expected):
    ag = _fresh_agent_with_lexicon()
    ag.s.add_node("CapabilityAxis", {
        "is_axis": 1.0, "capability_keys": ["k4"], "induced": 1.0,
        "residual_predicates": ["test", "vary", "send", "judge"], "from_observation": 1.0,
        "source": "concern_induction",
    })
    rf.ground_concern(ag, ["k4"])

    # a produced, finished Run — the exact vocabulary domains/experiment_dispatch.py's
    # _ingest_result mints (test scaffolding: simulating the host's own mechanical I/O,
    # not the agent's decision).
    exp = ag.s.add_node("Experiment", {"status": "running", "hypothesis": "h",
                                       "game": "navigate", "run_dir": ""})
    run = ag.s.add_node("Run", {"run_id": "r", "game": "navigate", "status": "done",
                                "frames": frames, "score": score})
    ag.inner.add_edge_unchecked(exp, "produced", run)

    ag.inner.run_rules()
    assert ag.s.node(exp)["attrs"].get("outcome") == expected

    # idempotent: a second run_rules must not re-fire / change the verdict
    ag.inner.run_rules()
    assert ag.s.node(exp)["attrs"].get("outcome") == expected


def test_analysis_rule_does_not_fire_on_unfinished_run():
    ag = _fresh_agent_with_lexicon()
    ag.s.add_node("CapabilityAxis", {
        "is_axis": 1.0, "capability_keys": ["k5"], "induced": 1.0,
        "residual_predicates": ["judge"], "from_observation": 1.0, "source": "concern_induction",
    })
    rf.ground_concern(ag, ["k5"])
    exp = ag.s.add_node("Experiment", {"status": "running", "hypothesis": "h",
                                       "game": "navigate", "run_dir": ""})
    run = ag.s.add_node("Run", {"run_id": "r", "game": "navigate", "status": "running",
                                "frames": 0, "score": 0})
    ag.inner.add_edge_unchecked(exp, "produced", run)
    ag.inner.run_rules()
    assert "outcome" not in ag.s.node(exp)["attrs"]


# ---------------------------------------------------------------------------
# 5 — SLOW, true end-to-end: a real offline child process (arc3_env 'navigate',
#     no network) dispatched by the UNCHANGED domains.experiment_dispatch
#     mechanism, from an Experiment the agent's OWN authored rule minted, judged
#     by the agent's OWN authored analysis rule once the child finishes. Mirrors
#     tests/test_experiment_dispatch.py's own pattern/timeout.
# ---------------------------------------------------------------------------
pytestmark_slow = pytest.mark.slow


@pytest.mark.slow
def test_full_self_experiment_loop_offline(tmp_path):
    from substrate.world_adapter import WorldAdapter
    from substrate.boot_all import load_all_seeds
    from domains.experiment_dispatch import scan_and_dispatch, _INFLIGHT
    from worlds.arc import ArcWorld
    from arc3_env import NavigateEnv

    _INFLIGHT.clear()
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    a.set_self_teacher(lambda q: "D")   # donkey=0 in spirit: no interpretive branching on the answer
    S, I = a.s, a.inner

    w = ArcWorld(NavigateEnv())
    sub, ctx = w.reset()
    a.perceive_frame(sub)
    a.tick()

    ind = rf.induce_concern(a, _SELF_EXPERIMENT_OBS, name_hint="self_experiment_concern")
    key = ind.get("capability_key")
    g = rf.ground_concern(a, [key])
    assert g.get("grounded") is True and g.get("path") == "compose_experiment_rule"

    ind2 = rf.induce_concern(a, [["puzzles", "ME", "about", "NAVIGATE"]], name_hint="navigate_efficacy_gap")
    axis2 = next(n for n in S.nodes("CapabilityAxis") if str(n) == str(ind2.get("axis_id")))
    a.tick()
    I.run_rules()
    exp = next(iter(I.neighbours(axis2, "tested_by")), None)
    assert exp is not None, "the agent's own mint rule must have authored an Experiment"
    assert S.node(exp)["attrs"]["status"] == "requested"
    assert S.node(exp)["attrs"]["game"] == "navigate"

    runs_dir = tmp_path / "runs"
    t0 = time.time()
    status = None
    while time.time() - t0 < 90:
        scan_and_dispatch(a, runs_dir)
        status = S.node(exp)["attrs"].get("status")
        if status not in ("requested", "running"):
            break
        time.sleep(0.5)
    assert status == "done", f"experiment ended {status!r}"

    I.run_rules()
    outcome = S.node(exp)["attrs"].get("outcome")
    assert outcome in ("supported", "refuted", "inconclusive"), (
        "the agent's OWN analysis rule must have written a verdict")
