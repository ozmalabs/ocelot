"""test_self_delta — closing the "SeedDelta is always trivial" gap.

Companion to tests/test_experiment_composer.py (the self-experiment MINT/
ANALYSE rule composer), covering the NEW non-trivial-delta machinery added
alongside it (see domains/reflective_faculty.py's `_compose_experiment_rule`
+ `close_experiment_loop`, substrate/boot_all.py's per-seed provenance,
seeds/relation_vocabulary.json's `embed_variant` cue,
seeds/composer_dispatch.json's 'embed' -> 'experiment' ComposerCue):

  1. seed provenance (SeedSummary nodes) is present after a full boot;
  2. the mint rule's SeedDelta.skip_seeds is picked BY A HELD TERM (an Argmax
     over SeedSummary word-overlap with the TRIGGERING axis's own residual),
     discriminatively — two topic-distinct triggering axes pick DIFFERENT
     seeds, each genuinely naming that topic;
  3. a variant rule is embedded into delta.add_rules ONLY when the concern
     also grounds 'embed' (back-compat: a bare test/vary/send/judge concern —
     tests/test_experiment_composer.py's own fixture shape — still gets
     add_rules:"[]", unchanged);
  4. close_experiment_loop() persists a judged Experiment's verdict via
     teach() and is idempotent.

Per CLAUDE.md's discipline: these tests never hand-install the mint/analyse/
variant rule text — they frame concerns and read back what the agent
authored, mirroring tests/test_experiment_composer.py's own approach.
"""
from __future__ import annotations

import json
import os
import time

import pytest

from substrate.boot_core import boot_core
from substrate.seed_loader import manifest_for
import domains.reflective_faculty as rf

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# OPTIONAL DEPENDENCIES (red-test triage 2026-08-12): absent 'cv2' is a SKIP with a
# named reason on the tests that need it, never a red. See tests/optional_deps.py.
from optional_deps import requires as _requires_optional  # noqa: E402

_CONCLUSIONS_SEED = os.path.join(ROOT, "seeds", "experiment_conclusions.json")


# ---------------------------------------------------------------------------
# guard: close_experiment_loop's teach() calls persist REAL data (by design —
# self-knowledge should survive a reboot) into a seed file this test suite
# doesn't otherwise own. Snapshot + restore its exact bytes around every test
# in this module, same shape as tests/test_speech_grounding.py's
# `_speech_enrollment_seed_guard`.
# ---------------------------------------------------------------------------
@pytest.fixture(autouse=True)
def _experiment_conclusions_seed_guard():
    existed = os.path.exists(_CONCLUSIONS_SEED)
    before = open(_CONCLUSIONS_SEED).read() if existed else None
    try:
        yield
    finally:
        if existed:
            with open(_CONCLUSIONS_SEED, "w") as f:
                f.write(before)
        elif os.path.exists(_CONCLUSIONS_SEED):
            os.unlink(_CONCLUSIONS_SEED)


class _Agent:
    """Minimal duck-typed agent wrapper — identical shape to
    tests/test_experiment_composer.py's own `_Agent` (harness glue only)."""
    def __init__(self, s, agent_node):
        self.s = s
        self.inner = s._inner
        self.agent = agent_node


def _fresh_agent_with_lexicon() -> _Agent:
    s, agent_node = boot_core()
    ag = _Agent(s, agent_node)
    ag.s._inner.load_seed_manifest(manifest_for("relation_vocabulary"), ag.agent)
    return ag


_SELF_EXPERIMENT_OBS_V2 = [
    ["test", "HYPOTHESIS", "about", "SELF"],
    ["vary", "SEED", "by", "DELTA"],
    ["send", "VARIANT", "to", "WORLD"],
    ["judge", "TRIAL", "by", "OUTCOME"],
    ["embed", "VARIANT", "as", "RULE"],
]


# ---------------------------------------------------------------------------
# 1 — the new 'embed_variant' RelationCue loads with the expected relation.
# ---------------------------------------------------------------------------
def test_embed_relation_cue_loads():
    ag = _fresh_agent_with_lexicon()
    cues = {at["name"]: at for at in (ag.s.node(n)["attrs"] for n in ag.s.nodes("RelationCue"))}
    assert "embed_variant" in cues
    assert json.loads(cues["embed_variant"]["relation"]) == ["embed", "VARIANT", "as", "RULE"]


# ---------------------------------------------------------------------------
# 2 — back-compat: a concern grounding ONLY test/vary/send/judge (no 'embed',
#     the exact fixture shape tests/test_experiment_composer.py uses) still
#     yields add_rules:"[]" and skip_seeds:"[]" on a lexicon-only boot with no
#     seed provenance (an empty Argmax source abstains) — unchanged behaviour.
# ---------------------------------------------------------------------------
def test_no_embed_relation_keeps_trivial_add_rules():
    ag = _fresh_agent_with_lexicon()
    ag.s.add_node("CapabilityAxis", {
        "is_axis": 1.0, "capability_keys": ["nv1"], "induced": 1.0,
        "residual_predicates": ["test", "vary", "send", "judge"], "from_observation": 1.0,
        "source": "concern_induction",
    })
    res = rf.ground_concern(ag, ["nv1"])
    assert res.get("grounded") is True
    rules_by_name = {r["name"]: r for r in res.get("rules", [])}
    mint = rules_by_name["author_experiment_from_residual_nv1"]
    delta_attrs = mint["effects"][1][3]
    assert delta_attrs.get("add_rules") == "[]", "no 'embed' grounded -> no variant embedded"


# ---------------------------------------------------------------------------
# 3 — 'embed' grounding produces a genuine variant-of-the-judge-rule embedded
#     into delta.add_rules (well-formed, distinct name, real match/effects).
# ---------------------------------------------------------------------------
def test_embed_relation_embeds_variant_rule():
    ag = _fresh_agent_with_lexicon()
    ag.s.add_node("CapabilityAxis", {
        "is_axis": 1.0, "capability_keys": ["ev1"], "induced": 1.0,
        "residual_predicates": ["test", "vary", "send", "judge", "embed"], "from_observation": 1.0,
        "source": "concern_induction",
    })
    res = rf.ground_concern(ag, ["ev1"])
    assert res.get("grounded") is True
    assert sorted(r[0] for r in res.get("grounded_relations", [])) == ["embed", "judge", "send", "test", "vary"]
    mint = {r["name"]: r for r in res["rules"]}["author_experiment_from_residual_ev1"]
    delta_attrs = mint["effects"][1][3]
    add_rules = json.loads(delta_attrs["add_rules"])
    assert len(add_rules) == 1
    variant = add_rules[0]
    assert variant["name"] == "judge_experiment_outcome_variant_ev1"
    assert variant["match"] == [["exp", "produced", "run"]]
    assert variant["effects"][0][0] == "set_attr" and variant["effects"][0][1:3] == ["exp", "outcome"]
    assert variant["effects"][1] == ["add_edge", "exp", "analysed", "run"]
    # the mint rule's own SeedDelta.skip_seeds/skip_seed_id are Term-valued (picked
    # by the agent's own Argmax at rule-apply-time, not a Python literal here).
    assert isinstance(delta_attrs.get("skip_seeds"), dict) and "__term__" in delta_attrs["skip_seeds"]
    assert isinstance(delta_attrs.get("skip_seed_id"), dict) and "__term__" in delta_attrs["skip_seed_id"]


# ---------------------------------------------------------------------------
# 4 — provenance: a full boot mints SeedSummary nodes, frozen seeds excluded.
# ---------------------------------------------------------------------------
@pytest.fixture(scope="module")
def full_agent():
    from substrate.world_adapter import WorldAdapter
    from substrate.boot_all import load_all_seeds
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    a.set_self_teacher(lambda q: "D")
    return a


def test_seed_provenance_present(full_agent):
    a = full_agent
    summaries = list(a.s.nodes("SeedSummary"))
    assert len(summaries) > 100, "one SeedSummary per loaded seed expected (~386)"
    by_id = {a.s.node(n)["attrs"]["seed_id"]: a.s.node(n)["attrs"] for n in summaries}
    assert by_id["autonomy"]["skippable"] == 0.0, "the frozen understand-Drive seed must not be skippable"
    assert by_id["decision_core"]["skippable"] == 0.0, "core cognition seeds must not be skippable"
    assert by_id["astronomy_foundation"]["skippable"] == 1.0, "an ordinary topic seed must be skippable"
    assert "astronomy" in by_id["astronomy_foundation"]["keywords_text"]


# ---------------------------------------------------------------------------
# 5 — THE DISCRIMINATIVE CHECK: two topic-distinct triggering axes pick
#     DIFFERENT seeds, each genuinely naming that topic (real Argmax pick,
#     not a coincidence) — over the SAME installed mint rule.
# ---------------------------------------------------------------------------
@_requires_optional('cv2')
def test_skip_seeds_pick_is_discriminative(full_agent):
    from worlds.arc import ArcWorld
    from arc3_env import NavigateEnv

    a = full_agent
    S, I = a.s, a.inner
    # the mint rule's 'send' branch reads WHICH world/game from the agent's OWN
    # perceived WorldInstance (never host-supplied) — perceive one first, exactly
    # like scripts/jabberwock_varies_itself.py's stage0.
    if not any(S.node(n)["attrs"].get("world_type") == "Game" for n in S.nodes("WorldInstance")):
        w = ArcWorld(NavigateEnv())
        sub, ctx = w.reset()
        a.perceive_frame(sub)
        a.tick()
    ind = rf.induce_concern(a, _SELF_EXPERIMENT_OBS_V2, name_hint="self_experiment_concern_test5")
    key = ind.get("capability_key")
    assert ind.get("minted") is True
    g = rf.ground_concern(a, [key])
    assert g.get("grounded") is True and g.get("path") == "compose_experiment_rule"

    ind_a = rf.induce_concern(a, [["astronomy", "ME", "about", "STARS"]], name_hint="astronomy_gap_t5")
    ind_b = rf.induce_concern(a, [["agriculture", "ME", "about", "FARMING"]], name_hint="agriculture_gap_t5")
    assert ind_a.get("minted") and ind_b.get("minted")
    axis_a = next(n for n in S.nodes("CapabilityAxis") if str(n) == str(ind_a.get("axis_id")))
    axis_b = next(n for n in S.nodes("CapabilityAxis") if str(n) == str(ind_b.get("axis_id")))

    a.tick()
    I.run_rules()
    exp_a = next(iter(I.neighbours(axis_a, "tested_by")), None)
    exp_b = next(iter(I.neighbours(axis_b, "tested_by")), None)
    assert exp_a is not None and exp_b is not None

    def _delta(exp):
        for d in I.neighbours(exp, "has_delta"):
            if I.has_node(d):
                return S.node(d)["attrs"]
        return {}

    da, db = _delta(exp_a), _delta(exp_b)
    skip_a, skip_b = da.get("skip_seed_id", ""), db.get("skip_seed_id", "")
    assert skip_a and skip_b, "both topic-specific axes must yield a genuine (non-empty) pick"
    assert skip_a != skip_b, "topic-distinct axes must pick DIFFERENT seeds"
    assert "astronomy" in skip_a.lower()
    assert "agriculture" in skip_b.lower()
    assert da.get("skip_seeds") == json.dumps([skip_a])
    assert db.get("skip_seeds") == json.dumps([skip_b])


# ---------------------------------------------------------------------------
# 6 — close_experiment_loop: persists a judged Experiment's verdict via
#     teach(), idempotently, WHICH conclusion is the rule's data (not chosen
#     here) — this only supplies host-scaffolded graph state to close over.
# ---------------------------------------------------------------------------
def test_close_experiment_loop_teaches_and_is_idempotent():
    ag = _fresh_agent_with_lexicon()
    exp = ag.s.add_node("Experiment", {
        "status": "done", "hypothesis": "h", "game": "navigate", "run_dir": "",
        "outcome": "supported", "conclusion_ready": True, "axis_tag": "tag_x",
    })
    delta = ag.s.add_node("SeedDelta", {
        "skip_seeds": '["astronomy_foundation"]', "add_rules": "[]",
        "skip_seed_id": "astronomy_foundation",
    })
    ag.inner.add_edge_unchecked(exp, "has_delta", delta)

    recs = rf.close_experiment_loop(ag)
    assert len(recs) == 1 and recs[0].get("saved") is True
    assert ag.s.node(exp)["attrs"].get("taught") is True

    recs2 = rf.close_experiment_loop(ag)
    assert recs2 == [], "already-taught Experiment must be skipped (idempotent)"

    assert os.path.exists(_CONCLUSIONS_SEED)
    with open(_CONCLUSIONS_SEED) as f:
        saved = json.load(f)
    hints = [n for n in saved.get("nodes", []) if n.get("type") == "TaughtHint"]
    assert any(h["attrs"].get("topic") == "seed 'astronomy_foundation' ablation for tag_x" for h in hints)
    assert any(h["attrs"].get("answer") == "supported" for h in hints)


# ---------------------------------------------------------------------------
# 7 — SLOW, true end-to-end: dispatch a REAL offline child with a NON-TRIVIAL
#     skip_seeds (the ablated seed genuinely withheld from the child's boot),
#     a real embedded variant, judged, and taught.
# ---------------------------------------------------------------------------
@_requires_optional('cv2')
@pytest.mark.slow
def test_full_self_delta_loop_offline(full_agent, tmp_path):
    from domains.experiment_dispatch import scan_and_dispatch, _INFLIGHT
    from worlds.arc import ArcWorld
    from arc3_env import NavigateEnv

    _INFLIGHT.clear()
    a = full_agent
    S, I = a.s, a.inner

    w = ArcWorld(NavigateEnv())
    sub, ctx = w.reset()
    a.perceive_frame(sub)
    a.tick()

    ind = rf.induce_concern(a, _SELF_EXPERIMENT_OBS_V2, name_hint="self_experiment_concern_test7")
    key = ind.get("capability_key")
    g = rf.ground_concern(a, [key])
    assert g.get("grounded") is True and g.get("path") == "compose_experiment_rule"

    ind2 = rf.induce_concern(a, [["astronomy", "ME", "about", "STARS"]], name_hint="astronomy_gap_t7")
    axis2 = next(n for n in S.nodes("CapabilityAxis") if str(n) == str(ind2.get("axis_id")))
    a.tick()
    I.run_rules()
    exp = next(iter(I.neighbours(axis2, "tested_by")), None)
    assert exp is not None
    assert S.node(exp)["attrs"]["status"] == "requested"

    deltas = list(I.neighbours(exp, "has_delta"))
    da = S.node(deltas[0])["attrs"]
    assert da.get("skip_seed_id") == "astronomy_foundation"
    assert json.loads(da.get("add_rules") or "[]"), "a variant rule must be embedded"

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
    ea = S.node(exp)["attrs"]
    assert ea.get("outcome") in ("supported", "refuted", "inconclusive")
    assert ea.get("conclusion_ready") is True

    recs = rf.close_experiment_loop(a)
    assert any(r.get("saved") for r in recs) or S.node(exp)["attrs"].get("taught") is True
