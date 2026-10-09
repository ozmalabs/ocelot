"""Wave 5 EXIT GATE: THE AGENT AUTHORS ITS OWN IMPROVEMENT — no hand-authored
variant anywhere in this file.

The vertical slice (every decision graph-resident, Python mechanical, per
CLAUDE.md):

  converse an uncovered instruction ("Condense the data." — no rule routes
  'condense') -> the gap rule files SelfConcern{kind:'instruction'} + the
  honest in-turn floor reply -> NL-promote it ("Work on the condense data
  gap." — steer_promote_concern marks; jd._steer_tick executes the EXISTING
  human-gated promote; kind 'instruction' now takes the conversation
  experiment bundle) -> jd._concern_tick grounds it -> the held
  `variation_pick` Program (seeds/variation_ops.json, the composer_pick
  precedent) selects the cue_set_edit family (requires_kind 'instruction'
  read via a graph join inside the Term — NOT a Python branch), and the held
  `cue_route_pick` Program proposes a route from cue_set_edit's own
  route_pool -> the agent's own author rule mints Experiment{game:
  'conversation'} whose SeedDelta carries `add_concepts` (a Concept, the
  cue-set edit) -> experiment_dispatch spawns scripts/convo_child_run.py (a
  real subprocess) -> the child ADDS the Concept and replays the corpus: the
  previously-unhandled flagged turn now routes (reply changes from the
  gap-filing floor), nothing regresses, score positive -> the agent's own
  judge rule reads supported -> mark_adopt_ready accepts the cue delta ->
  perform_adoptions TEACHES the winning Concept into the owning seed
  (comprehend_instruction, via the documented teach() facility) + mints the
  Adoption record -> the PARENT now handles "Condense the data." without
  filing a gap.

Also gated here:
  * the self-repairable-choice gate: EDITING a VariationOp node flips which
    family the pick chooses (no rule/Python edit);
  * the pick's defaults reproduce the old Python chain's branches exactly;
  * the cue builder's honest abstains (non-instruction concern; an
    already-routed verb; zero-overlap verb).

(No-op and regression-inducing deltas judging inconclusive/refuted are Wave
3's standing gates — tests/test_convo_experiment_migrated.py — re-run
unchanged as part of this wave's bench.)
"""
from __future__ import annotations

import json
import os
import sys
import time

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "scripts"))

from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds

jd = pytest.importorskip("jabberwock_daemon")

import domains.reflective_faculty as rf                                  # noqa: E402
from domains.experiment_dispatch import scan_and_dispatch, _INFLIGHT     # noqa: E402

_GUARDED_SEEDS = (
    os.path.join(ROOT, "seeds", "experiment_conclusions.json"),   # close_experiment_loop teach()es verdicts
    os.path.join(ROOT, "seeds", "comprehend_instruction.json"),   # cue adoption teach()es the winning Concept
)


@pytest.fixture(autouse=True)
def _guard_seed_files():
    """Snapshot/restore the seeds the adoption path writes (the same guard
    test_convo_experiment_migrated applies to experiment_conclusions)."""
    before = {}
    for p in _GUARDED_SEEDS:
        before[p] = open(p).read() if os.path.exists(p) else None
    try:
        yield
    finally:
        for p, content in before.items():
            if content is not None:
                with open(p, "w") as f:
                    f.write(content)
            elif os.path.exists(p):
                os.unlink(p)


@pytest.fixture()
def agent():
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    return a


@pytest.fixture()
def light_agent():
    """A bare substrate for the pick-level gates — rf._pick_variation_op's own
    _ensure_seed_chain loads seeds/variation_ops.json onto it (idempotent)."""
    return WorldAdapter(seeds=())


def _instruction_gaps(a, content=None):
    out = []
    for sc in a.s.nodes("SelfConcern"):
        if not a.s.has_node(sc):
            continue
        at = a.s.node(sc)["attrs"]
        if at.get("kind") == "instruction" and (content is None or at.get("content") == content):
            out.append(at)
    return out


def _dispatch_until(a, runs_dir, exp, timeout_s=300.0):
    _INFLIGHT.clear()
    t0 = time.time()
    scan_and_dispatch(a, str(runs_dir))
    while time.time() - t0 < timeout_s:
        status = a.s.node(exp)["attrs"].get("status")
        if status not in ("requested", "running"):
            return status
        time.sleep(0.5)
        scan_and_dispatch(a, str(runs_dir))
    return a.s.node(exp)["attrs"].get("status")


# --- THE EXIT GATE -------------------------------------------------------------

def test_agent_authors_new_rule_end_to_end(agent, tmp_path):
    # (a) an uncovered instruction files a gap (the honest floor, not a dead end)
    a_reply = agent.converse("Hello.", speech_act="greeting")     # unflagged regression guard turn
    assert (a_reply or "").strip()
    floor = agent.converse("Condense the data.", speech_act="request")
    mid = agent._last_turn_inbound
    assert agent.s.node(mid)["attrs"].get("instruction_outcome") == "unhandled"
    assert "filed it as a gap" in floor.lower()
    assert len(_instruction_gaps(agent, "condense data")) == 1

    # (b) NL-promote it — the steering rule marks; the hook executes the
    # existing human-gated promote; instruction kind takes the conversation bundle
    steer = agent.converse("Work on the condense data gap.", speech_act="request")
    assert steer.lower().startswith("promoting:") and "condense data" in steer
    promoted = jd._steer_tick(agent)
    assert len(promoted) == 1 and promoted[0]["ok"] and promoted[0]["pipeline"] == "experiment"
    import substrate_rs as srs
    standing = srs.NodeID(int(promoted[0]["standing_concern"]))
    st = agent.s.node(standing)["attrs"]
    heads = {r[0] for r in (st.get("relations") or []) if r}
    assert {"test", "replay", "send", "judge", "adopt"} <= heads
    assert st.get("kind") == "instruction"

    # (c) ground: the VARIATION PICK selects cue_set_edit VIA THE GRAPH
    # (verified against the held Program itself, not a Python branch), and the
    # agent's own author rule mints the Experiment with the cue-edit delta.
    jd._concern_tick(agent)
    key = st.get("name")
    assert rf._pick_variation_op(agent, heads, key) == "cue_set_edit", (
        "the held variation_pick Program must choose the cue family for an "
        "instruction-kind concern with the conversation bundle")
    convo = [n for n in agent.s.nodes("Experiment")
             if agent.s.node(n)["attrs"].get("game") == "conversation"]
    assert len(convo) == 1, "exactly one conversation experiment expected"
    exp = convo[0]
    at = agent.s.node(exp)["attrs"]
    assert at.get("status") == "requested"
    assert at.get("axis_tag") == key
    da = {}
    for d in agent.inner.neighbours(exp, "has_delta"):
        if agent.s.has_node(d):
            da = agent.s.node(d)["attrs"]
            break
    assert da.get("cue_edit") == 1.0 and da.get("cue_concept_added") == "condense", da
    added = json.loads(da.get("add_concepts") or "[]")
    assert len(added) == 1 and added[0]["attrs"]["name"] == "condense"
    route = added[0]["attrs"]["instruction_route"]
    assert route == da.get("cue_route")
    # the route came from the cue_set_edit op's OWN route_pool (graph data)
    pools = [agent.s.node(n)["attrs"].get("route_pool") for n in agent.s.nodes("VariationOp")
             if agent.s.node(n)["attrs"].get("name") == "cue_set_edit"]
    assert pools and route in list(pools[0])
    # a cue-set edit removes/installs NO rules and skips NO seeds
    assert json.loads(da.get("remove_rules") or "[]") == []
    assert json.loads(da.get("add_rules") or "[]") == []
    assert json.loads(da.get("skip_seeds") or "[]") == []
    assert da.get("ablation") is None

    # (d) dispatch: real subprocess; the child adds the Concept and replays.
    status = _dispatch_until(agent, tmp_path / "runs", exp)
    assert status == "done", (status, agent.s.node(exp)["attrs"].get("error"))
    run = next(r for r in agent.inner.neighbours(exp, "produced") if agent.s.has_node(r))
    ra = agent.s.node(run)["attrs"]
    assert ra["status"] == "done"
    assert int(ra["frames"]) == 2, ("two behaviour probes: the greeting guard + the "
                                    "flagged instruction turn (the steering turn is a "
                                    "pipeline command, mechanically excluded)")
    child = json.load(open(os.path.join(agent.s.node(exp)["attrs"]["run_dir"], "result.json")))
    # TRANCHE 4 JUDGE: the variant routes "condense" to the cue_route_pick
    # winner. If that route yields a real reply the flagged turn is fixed
    # (+1, adopted); if it yields the adapter's fixed ERROR surface it is a
    # BROKEN fix (-1, refuted, never adopted). Measured on this tree the
    # picked route is comprehend_text, which errors for an instruction turn
    # (world_action would have handled it) -- the judge must catch that.
    assert child["flagged"] == 1 and child["regressions"] == 0
    fixed = child["flagged_changed"] == 1
    assert fixed != (child.get("broken_fixes") == 1), child

    agent.comprehend()
    at = agent.s.node(exp)["attrs"]
    if not fixed:
        assert int(ra["score"]) <= -1
        assert at.get("outcome") == "refuted", at
        assert not at.get("adopt_ready"), at
        rf.close_experiment_loop(agent)
        assert not agent.s.node(exp)["attrs"].get("adopted")
        live = [agent.s.node(n)["attrs"] for n in agent.s.nodes("Concept")
                if agent.s.node(n)["attrs"].get("name") == "condense"]
        assert not any(c.get("instruction_route") == route for c in live), \
            "a broken cue edit must not be taught into the parent"
        return

    # (e) the agent's OWN authored judge rule reads the run: supported
    assert int(ra["score"]) >= 1
    assert at.get("outcome") == "supported", at
    assert at.get("adopt_ready") is True, (
        "mark_adopt_ready must accept a cue-edit delta (cue_concept_added non-empty)")

    # (f) adoption TEACHES the winning Concept into the live parent + the owning seed
    records = rf.close_experiment_loop(agent)
    at = agent.s.node(exp)["attrs"]
    assert at.get("adopted") is True and not at.get("adopt_denied"), at
    adoptions = [n for n in agent.s.nodes("Adoption")
                 if agent.s.node(n)["attrs"].get("cue_concept_added") == "condense"]
    assert len(adoptions) == 1
    live = [agent.s.node(n)["attrs"] for n in agent.s.nodes("Concept")
            if agent.s.node(n)["attrs"].get("name") == "condense"]
    assert any(c.get("instruction_route") == route for c in live), "the parent holds the Concept live"
    cue_recs = [r for r in records if isinstance(r, dict) and r.get("cue_concept_added") == "condense"]
    assert len(cue_recs) == 1
    assert cue_recs[0]["cue_taught"]["category"] == "comprehend_instruction"

    # (g) the parent now HANDLES the previously-uncovered instruction — no gap
    reply = agent.converse("Condense the data.", speech_act="request")
    mid = agent._last_turn_inbound
    assert agent.s.node(mid)["attrs"].get("instruction_outcome") == "handled"
    assert "filed it as a gap" not in reply.lower()


# --- THE SELF-REPAIRABLE-CHOICE GATE -------------------------------------------

_CONVO_HEADS = ["test", "replay", "send", "judge", "adopt"]


def _mk_promoted(a, key="promoted_self_concern_test", kind="instruction"):
    a.s.add_node("StandingConcern", {"name": key, "kind": kind})
    return key


def test_variation_op_edit_flips_the_pick(light_agent):
    a = light_agent
    key = _mk_promoted(a, kind="instruction")
    assert rf._pick_variation_op(a, _CONVO_HEADS, key) == "cue_set_edit"

    # THE AGENT EDITING A VariationOp NODE CHANGES THE CHOICE — no rule edit,
    # no Python edit: push cue_set_edit below reply_ablation's priority.
    op = next(n for n in a.s.nodes("VariationOp")
              if a.s.node(n)["attrs"].get("name") == "cue_set_edit")
    a.s.set_attr(op, "priority", 99)
    assert rf._pick_variation_op(a, _CONVO_HEADS, key) == "reply_ablation", (
        "a VariationOp priority edit must flip which family the pick chooses")

    # restore, then flip via the kind gate instead
    a.s.set_attr(op, "priority", 10)
    assert rf._pick_variation_op(a, _CONVO_HEADS, key) == "cue_set_edit"
    a.s.set_attr(op, "requires_kind", "some_other_kind")
    assert rf._pick_variation_op(a, _CONVO_HEADS, key) == "reply_ablation"


def test_pick_defaults_match_old_chain(light_agent):
    """The reified defaults reproduce the retired Python chain exactly:
    conversation -> reply_ablation (cue_set_edit only for instruction kind);
    judge+structure -> structural (priority over gradient); judge+gradient ->
    threshold_shift; structure/gradient without judge -> nothing; no cue -> None."""
    a = light_agent
    # conversation bundle, non-instruction concern (e.g. a reply_fix flag)
    key = _mk_promoted(a, key="promoted_self_concern_rf", kind="reply_fix")
    assert rf._pick_variation_op(a, _CONVO_HEADS, key) == "reply_ablation"
    # conversation bundle, no StandingConcern at all (kind unreadable)
    assert rf._pick_variation_op(a, _CONVO_HEADS, "no_such_key") == "reply_ablation"
    # the ARC families
    assert rf._pick_variation_op(a, ["test", "send", "judge", "gradient"], "x") == "threshold_shift"
    assert rf._pick_variation_op(a, ["test", "judge", "gradient", "structure"], "x") == "structural_edit"
    assert rf._pick_variation_op(a, ["test", "structure"], "x") is None, "structure needs judge (old chain)"
    assert rf._pick_variation_op(a, ["test", "gradient"], "x") is None, "gradient needs judge (old chain)"
    assert rf._pick_variation_op(a, ["test", "judge"], "x") is None, "no family cued -> no variant"


# --- HONEST ABSTAINS OF THE CUE BUILDER ------------------------------------------

def _wire_concern(a, key, kind, verb):
    standing = a.s.add_node("StandingConcern", {"name": key, "kind": kind})
    sc = a.s.add_node("SelfConcern", {"kind": kind, "status": "promoted",
                                      "predicate": verb, "content": f"{verb} thing"})
    a.inner.add_edge_unchecked(sc, "promoted_to", standing)
    return standing


def test_cue_variant_abstains_honestly(light_agent):
    a = light_agent
    # Cases 1-3 pin the honest abstain with explore_unscored OFF (it is the
    # default since variation_ops v1.16.0, tranche 12; case 3b covers ON).
    rf._ensure_seed_chain(a.s, a.inner, a.agent, ("variation_ops",))
    for n in a.s.nodes("VariationOp"):
        if a.s.node(n)["attrs"].get("name") == "cue_set_edit":
            a.s.set_attr(n, "explore_unscored", 0)
    # route-carrying Concepts the pick scores against (the pool routes)
    for nm, rt in (("read", "comprehend_text"), ("run", "world_action"),
                   ("summarise", "self_report")):
        a.s.add_node("Concept", {"name": nm, "instruction_route": rt})

    # 1. not an instruction concern -> wall, nothing fabricated
    _wire_concern(a, "k_replyfix", "reply_fix", "condense")
    r = rf._compose_cue_variant(a, ["k_replyfix"], "t1")
    assert r["built"] is False and "instruction" in r["wall"]

    # 2. an ALREADY-ROUTED verb -> the held Program abstains (nothing to construct)
    _wire_concern(a, "k_routed", "instruction", "summarise")
    r = rf._compose_cue_variant(a, ["k_routed"], "t2")
    assert r["built"] is False and "abstained" in r["wall"]

    # 3. zero bigram overlap -> abstain when explore_unscored is off; since
    # variation_ops v1.16.0 (tranche 12, preregistered promotion) the default
    # proposes the best UNTRIED pooled route instead -- the replay judges it.
    _wire_concern(a, "k_zero", "instruction", "zzz")
    r = rf._compose_cue_variant(a, ["k_zero"], "t3")
    assert r["built"] is False and "abstained" in r["wall"]
    for n in a.s.nodes("VariationOp"):
        if a.s.node(n)["attrs"].get("name") == "cue_set_edit":
            a.s.set_attr(n, "explore_unscored", 1)
    _wire_concern(a, "k_zero2", "instruction", "zzzz")
    r = rf._compose_cue_variant(a, ["k_zero2"], "t3b")
    assert r["built"] is True and r["route"] in ("world_action", "comprehend_text")

    # 4. and the genuine case builds a Concept whose route is pooled.
    # RULE_SIGNATURE_PRODUCTION_WIRING v1.4.0: cue_route_pick's own scoring
    # moved from per-CHARACTER overlap to per-BIGRAM overlap (SHAPE_AUDIT.md
    # §2.2's "worst instance" fix — the old scoring made anagram-shaped verbs
    # like 'drop'/'prod' score byte-identically against every candidate).
    # 'condense' shared zero bigrams with this test's tiny 2-route pool
    # (it happened to share individual LETTERS with 'read', which is exactly
    # the coincidental-membership matching the fix removes) — 'running'
    # genuinely shares the bigrams 'ru'/'un' with the pooled 'run', so this
    # probe now exercises a real bigram match instead of a letter-bag
    # coincidence, preserving the test's own intent (a genuine case builds).
    _wire_concern(a, "k_real", "instruction", "running")
    r = rf._compose_cue_variant(a, ["k_real"], "t4")
    assert r["built"] is True and r["concept"]["attrs"]["name"] == "running"
    assert r["route"] in ("world_action", "comprehend_text")


# --- TRANCHE 5: a GENUINE self-repair under the corrected judge ----------------

def _conv_exps(a):
    return [n for n in a.s.nodes("Experiment")
            if a.s.node(n)["attrs"].get("game") == "conversation"]


def test_refuted_route_is_excluded_and_the_retry_genuinely_repairs(agent, tmp_path):
    """The first cue edit routes 'condense' to comprehend_text, which errors on
    an instruction turn: refuted (broken fix), never adopted. A human-gated
    retry (repromote) asks the SAME held cue_route_pick, which now excludes the
    refuted route and proposes world_action. That variant really handles the
    turn: supported, adopted, taught, and the PARENT handles the instruction."""
    agent.converse("Hello.", speech_act="greeting")
    agent.converse("Condense the data.", speech_act="request")
    steer = agent.converse("Work on the condense data gap.", speech_act="request")
    assert steer.lower().startswith("promoting:")
    promoted = jd._steer_tick(agent)
    assert len(promoted) == 1 and promoted[0]["ok"]
    sc_id = str(promoted[0]["self_concern"])

    def attempt(label):
        jd._concern_tick(agent)
        exps = [e for e in _conv_exps(agent) if agent.s.node(e)["attrs"].get("status") == "requested"]
        assert len(exps) == 1, (label, [agent.s.node(e)["attrs"] for e in _conv_exps(agent)])
        exp = exps[0]
        delta = next(iter(agent.inner.neighbours(exp, "has_delta")))
        route = agent.s.node(delta)["attrs"].get("cue_route")
        assert _dispatch_until(agent, tmp_path / f"runs_{label}", exp) == "done"
        agent.comprehend()
        return exp, route, agent.s.node(exp)["attrs"]

    exp1, route1, at1 = attempt("first")
    assert route1 == "comprehend_text" and at1.get("outcome") == "refuted", at1
    rf.close_experiment_loop(agent)
    assert not agent.s.node(exp1)["attrs"].get("adopted")

    rep = jd.repromote_self_concern(agent, sc_id)
    assert rep.get("ok") and rep.get("repromoted"), rep
    exp2, route2, at2 = attempt("retry")
    assert route2 != route1, "the refuted route must not be proposed again"
    assert route2 == "world_action"
    assert at2.get("outcome") == "supported" and at2.get("adopt_ready") is True, at2
    rf.close_experiment_loop(agent)
    assert agent.s.node(exp2)["attrs"].get("adopted") is True

    reply = agent.converse("Condense the data.", speech_act="request")
    mid = agent._last_turn_inbound
    assert agent.s.node(mid)["attrs"].get("instruction_outcome") == "handled"
    assert "filed it as a gap" not in reply.lower()
    assert reply.strip() != "ERROR: no communicative response could be generated."


# --- TRANCHE 6: AGENT-INITIATED retry (graph marks, hook executes) -----------

def test_agent_requests_its_own_retry_and_stops_at_the_bound(agent):
    """No human re-promote: irr_request_retry marks the concern after its own
    experiment is refuted; _concern_tick executes the retry; the bound
    (InstructionRetryPolicy.max_retries) stops it; a supported verdict never
    triggers a retry."""
    import substrate_rs as srs
    agent.converse("Condense the data.", speech_act="request")
    agent.converse("Work on the condense data gap.", speech_act="request")
    p = jd._steer_tick(agent)
    sc = srs.NodeID(int(p[0]["self_concern"]))
    pol = [agent.s.node(n)["attrs"] for n in agent.s.nodes("InstructionRetryPolicy")]
    assert pol and pol[0]["max_retries"] == 2

    def judge_current(outcome):
        jd._concern_tick(agent)
        exps = [e for e in _conv_exps(agent) if agent.s.node(e)["attrs"].get("status") == "requested"]
        assert len(exps) == 1
        agent.s.set_attr(exps[0], "status", "done")
        agent.s.set_attr(exps[0], "outcome", outcome)
        agent.inner.run_rules()
        return agent.s.node(sc)["attrs"]

    at = judge_current("refuted")
    assert at.get("retry_requested") == 1 and at.get("retry_count") == 1
    at = judge_current("inconclusive")          # hook executed retry 1; this is attempt 2
    assert at.get("retry_requested") == 1 and at.get("retry_count") == 2
    # attempt 3: both pooled routes are excluded for 'condense', so the cue
    # builder abstains and (tranche 11) the empty experiment is closed
    # 'abstained' before dispatch rather than replayed; the bound is reached.
    jd._concern_tick(agent)
    agent.inner.run_rules()
    assert not [e for e in _conv_exps(agent) if agent.s.node(e)["attrs"].get("status") == "requested"]
    assert any(agent.s.node(e)["attrs"].get("outcome") == "abstained" for e in _conv_exps(agent))
    at = agent.s.node(sc)["attrs"]
    assert at.get("retry_requested") != 1 and at.get("retry_count") == 2


# --- TRANCHE 7: CONTENT-CONDITIONED routes, composer replay cue, knob exclusion ---

def test_content_conditioned_route_keeps_self_object_on_self_report(agent):
    """A route Concept scoped route_object_scope='other' claims "<verb> the
    data" without capturing "<verb> yourself" (comprehend_instruction v2.4.0 +
    instruction_understanding v1.1.0): the self turn's reply is byte-identical
    to the unedited agent's, the data turn leaves the gap floor."""
    before_self = agent.converse("Summarise yourself.", speech_act="request")
    before_data = agent.converse("Summarise the data.", speech_act="request")
    agent.s.add_node("Concept", {"name": "summarise", "instruction_route": "world_action",
                                 "route_object_scope": "other"})
    after_self = agent.converse("Summarise yourself.", speech_act="request")
    after_data = agent.converse("Summarise the data.", speech_act="request")
    assert after_self == before_self
    assert after_data != before_data


def test_cue_builder_proposes_scoped_route(agent):
    """Every cue edit is proposed content-conditioned, so adoption cannot
    regress a verb's existing self-object use."""
    agent.converse("Condense the data.", speech_act="request")
    agent.converse("Work on the condense data gap.", speech_act="request")
    p = jd._steer_tick(agent)
    assert p and p[0].get("ok")
    jd._concern_tick(agent)
    exps = [e for e in _conv_exps(agent) if agent.s.node(e)["attrs"].get("status") == "requested"]
    assert len(exps) == 1
    d = next(iter(agent.inner.neighbours(exps[0], "has_delta")))
    da = agent.s.node(d)["attrs"]
    assert da.get("cue_route_scope") == "other"
    import json as _j
    assert _j.loads(da["add_concepts"])[0]["attrs"]["route_object_scope"] == "other"


def test_replay_head_routes_reported_concern_to_experiment(light_agent):
    """composer_dispatch v1.1.0: a 'replay' relation head (only the
    conversation-experiment bundle grounds it) outranks 'communicate', whose
    keywords substring-match ordinary content words ('speaker')."""
    rf._ensure_seed_chain(light_agent.s, light_agent.inner, light_agent.agent, ("composer_dispatch",))
    cues = {light_agent.s.node(n)["attrs"].get("relation_head"): light_agent.s.node(n)["attrs"]
            for n in light_agent.s.nodes("ComposerCue")}
    assert cues["replay"]["composer"] == "experiment"
    assert cues["replay"]["priority"] < cues["communicate"]["priority"]


def test_knob_builder_excludes_knobs_already_tried(agent):
    """The knob_edit builder skips a knob this concern's own experiments
    already judged inconclusive/refuted, so a retry moves a different knob."""
    _fixed_step(agent)
    text = "you reform the topic too eagerly, test whether the threshold is too low"
    sc = agent.s.add_node("SelfConcern", {"kind": "reported", "status": "noted", "source": "explicit", "content": text})
    agent.inner.add_edge_unchecked(agent.agent, "has_self_concern", sc)
    p = jd.promote_self_concern(agent, str(sc.value))
    key = f"promoted_self_concern_{sc.value}"
    first = rf._compose_knob_variant(agent, [key], key)
    assert first.get("built")
    exp = agent.s.add_node("Experiment", {"axis_tag": key, "outcome": "inconclusive", "status": "done"})
    d = agent.s.add_node("SeedDelta", {"knob_attr": first["attr"]})
    agent.inner.add_edge_unchecked(exp, "has_delta", d)
    second = rf._compose_knob_variant(agent, [key], key)
    assert second.get("built") and second["attr"] != first["attr"]
    assert p.get("pipeline") == "experiment"


def test_shadow_read_runs_on_a_chat_turn():
    """reading_drive._LAAdapter mints the adapter lock serialized
    WorldAdapter methods take; before the fix every shadow read raised
    AttributeError and was recorded as shadow_error=1.0."""
    a = WorldAdapter(seeds=(), shadow_read=True)
    load_all_seeds(a)
    a.converse("The horse raced past the barn fell.", speech_act="statement")
    at = a.s.node(a._last_turn_inbound)["attrs"]
    assert at.get("shadow_error") != 1.0
    assert at.get("shadow_predicate") is not None


# --- TRANCHE 8: knob_edit POLARITY ----------------------------------------------

def _fixed_step(agent):
    """Pin the pre-tranche-12 fixed knob_step path (grain is the default since
    variation_ops v1.15.0; these tests cover the fixed step)."""
    rf._ensure_seed_chain(agent.s, agent.inner, agent.agent, ("variation_ops",))
    for n in agent.s.nodes("VariationOp"):
        if agent.s.node(n)["attrs"].get("name") == "knob_edit":
            agent.s.set_attr(n, "step_mode", "fixed")


def _knob_for(agent, text):
    sc = agent.s.add_node("SelfConcern", {"kind": "reported", "status": "noted", "source": "explicit", "content": text})
    agent.inner.add_edge_unchecked(agent.agent, "has_self_concern", sc)
    jd.promote_self_concern(agent, str(sc.value))
    key = f"promoted_self_concern_{sc.value}"
    return rf._compose_knob_variant(agent, [key], key)


def test_knob_direction_follows_concern_polarity(agent):
    _fixed_step(agent)
    eager = _knob_for(agent, "you reform the topic too eagerly, test whether the threshold is too low")
    rare = _knob_for(agent, "you reform the topic too rarely, test whether the threshold is too high")
    assert eager["built"] and rare["built"]
    assert eager["direction"] == "decrease_fires" and eager["new_value"] > eager["old_value"]
    assert rare["direction"] == "increase_fires" and rare["new_value"] < rare["old_value"]


def test_knob_judge_is_direction_aware(light_agent):
    a = light_agent
    rf._ensure_seed_chain(a.s, a.inner, a.agent, ("self_optimisation",))
    out = {}
    for direction, ctrl, var in (("increase_fires", 0, 1), ("decrease_fires", 0, 1),
                                 ("increase_fires", 1, 0), (None, 1, 0)):
        exp = a.s.add_node("Experiment", {"control_reforms": ctrl, "variant_reforms": var, "regressions": 0})
        dat = {"knob_edit": 1.0}
        if direction:
            dat["knob_direction"] = direction
        d = a.s.add_node("SeedDelta", dat)
        run = a.s.add_node("Run", {})
        a.inner.add_edge_unchecked(exp, "has_delta", d)
        a.inner.add_edge_unchecked(exp, "analysed", run)
        out[(direction, ctrl, var)] = exp
    a.inner.run_rules()
    got = {k: a.s.node(e)["attrs"].get("outcome") for k, e in out.items()}
    assert got == {("increase_fires", 0, 1): "supported", ("decrease_fires", 0, 1): "refuted",
                   ("increase_fires", 1, 0): "refuted", (None, 1, 0): "supported"}


# --- TRANCHE 8: shape_mint child witness ------------------------------------------

def test_shape_mint_witness_counts_classified_parties():
    """convo_child_run._classified_party_count is party-independent: an
    atypical party (casual+medium+ornate+agitated) fits no held shape; once
    the builder's minted shape is installed it is classified, so the count
    rises -- the witness a shape_mint verdict reads (the old active-party fit
    read a typical party and never moved)."""
    sys.path.insert(0, os.path.join(ROOT, "scripts"))
    import convo_child_run as C
    from domains import interlocutor_model as im
    a = WorldAdapter(seeds=(), shadow_read=True)
    load_all_seeds(a)
    for t in ("yeah nah, this whole conversation is kinda ridiculous!!",
              "yeah, gonna say your explanation was unbelievable!!",
              "dunno mate, gonna lose it, everything keeps breaking!!"):
        a.converse(t, speech_act="statement")
    before = C._classified_party_count(a)
    party = im._active_party(a)
    assert a.s.node(party)["attrs"].get("poor_fit_streak", 0) >= 1
    a.s.add_node("InterlocutorShape", {"name": "t8_atypical", "sig_register": "casual", "sig_cadence": "medium",
                                       "sig_style": "ornate", "sig_affect": "agitated"})
    assert C._classified_party_count(a) > before


# --- TRANCHE 10: grain-quantised knob steps ---------------------------------------

def test_grain_step_is_exact_and_guards_degenerate_gates():
    g = rf._grain_step
    vals = [0.0, 2.0, 3.0, 4.0, 6.0]
    assert g(vals, "Gte", 1.0, "decrease_fires")[0] == 3.0      # 2 stops firing
    assert g(vals, "Gte", 3.0, "increase_fires")[0] == 2.0      # 2 starts firing
    assert g(vals, "Gt", 2.5, "decrease_fires")[0] == 3.0
    assert g([0.0, 0.5], "Gte", 0.5, "increase_fires")[0] is None   # would fire on everything
    assert g([0.0, 0.5], "Gte", 0.5, "decrease_fires")[0] is None   # no value beyond 0.5
    assert g([1.0], "Gte", 1.0, "decrease_fires")[0] is None


def test_knob_gated_signal_found_structurally(agent):
    assert rf._knob_gated_signal(agent.inner, "reform_residual_threshold") == ("Gte", "residual_marker_count")
    assert rf._knob_gated_signal(agent.inner, "reform_swallowed_threshold") == ("Gte", "swallowed_ratio")


def test_grain_mode_builder_steps_onto_observed_values():
    a = WorldAdapter(seeds=(), shadow_read=True)
    load_all_seeds(a)
    for t in ("The kit includes a hammer, a saw and a drill.", "The bag includes a map and a torch.",
              "The box includes a pen, a cup, a lamp and a book.", "The cat sat on the mat."):
        a.converse(t, speech_act="statement")
    for n in a.s.nodes("VariationOp"):
        if a.s.node(n)["attrs"].get("name") == "knob_edit":
            a.s.set_attr(n, "step_mode", "grain")
    rep = _knob_for(a, "you reform list sentences too eagerly, test whether the residual marker threshold is too low")
    assert rep["built"] and rep["attr"] == "reform_residual_threshold"
    assert (rep["old_value"], rep["new_value"], rep["direction"]) == (1.0, 3.0, "decrease_fires")


def test_stale_retry_mark_is_cleared_when_a_family_judge_supports(agent):
    """irr_cancel_stale_retry: a retry marked on a provisional non-supported
    verdict is cleared once the concern's experiment is supported."""
    import substrate_rs as srs
    agent.converse("Condense the data.", speech_act="request")
    agent.converse("Work on the condense data gap.", speech_act="request")
    p = jd._steer_tick(agent)
    sc = srs.NodeID(int(p[0]["self_concern"]))
    jd._concern_tick(agent)
    exp = [e for e in _conv_exps(agent) if agent.s.node(e)["attrs"].get("status") == "requested"][0]
    agent.s.set_attr(exp, "status", "done")
    agent.s.set_attr(exp, "outcome", "inconclusive")
    agent.inner.run_rules()
    assert agent.s.node(sc)["attrs"].get("retry_requested") == 1
    agent.s.set_attr(exp, "outcome", "supported")          # the family judge's override
    agent.inner.run_rules()
    at = agent.s.node(sc)["attrs"]
    assert at.get("retry_requested") == 0 and at.get("retry_count") == 0


# --- TRANCHE 11: abstained variants are closed before dispatch --------------------

def test_abstained_cue_variant_is_never_dispatched(agent):
    """'sort' shares no bigram with any pooled route Concept, so cue_route_pick
    abstains; the delta is stamped variant_abstained and the experiment is
    closed 'abstained' by a graph rule -- never left 'requested' for a child.
    (explore_unscored is the default since variation_ops v1.16.0; turned off
    here to reproduce the abstain.)"""
    rf._ensure_seed_chain(agent.s, agent.inner, agent.agent, ("variation_ops",))
    for n in agent.s.nodes("VariationOp"):
        if agent.s.node(n)["attrs"].get("name") == "cue_set_edit":
            agent.s.set_attr(n, "explore_unscored", 0)
    agent.converse("Please sort the notes.", speech_act="request")
    agent.converse("Work on the sort notes gap.", speech_act="request")
    p = jd._steer_tick(agent)
    assert p and p[0].get("ok")
    jd._concern_tick(agent)
    agent.inner.run_rules()
    exps = _conv_exps(agent)
    assert exps and not [e for e in exps if agent.s.node(e)["attrs"].get("status") == "requested"]
    e = exps[0]
    d = next(iter(agent.inner.neighbours(e, "has_delta")))
    assert agent.s.node(d)["attrs"].get("variant_abstained") == 1.0
    assert agent.s.node(e)["attrs"].get("outcome") == "abstained"


# --- TRANCHE 12: grain-end step on the frame's own quantum ----------------------

def test_frame_quantum_and_grain_end_are_exact():
    from fractions import Fraction
    assert rf._frame_quantum([0.0, 0.5, 0.5]) == Fraction(1, 2)
    assert rf._frame_quantum([0.0, 2.0, 3.0, 5.0]) == Fraction(1)
    assert rf._frame_quantum([1.0]) is None
    assert rf._grain_end_step([0.0, 0.5], "Gte", 0.5, "decrease_fires")[0] == 1.0   # fires on none observed
    assert rf._grain_end_step([0.0, 0.5], "Gte", 0.5, "increase_fires")[0] == 0.0   # fires on all observed
    assert rf._grain_end_step([0.0, 0.5], "Gte", 1.0, "decrease_fires")[0] is None  # already fires on none


def test_grain_is_the_knob_edit_default():
    a = WorldAdapter(seeds=())
    rf._ensure_seed_chain(a.s, a.inner, a.agent, ("variation_ops",))
    at = [a.s.node(n)["attrs"] for n in a.s.nodes("VariationOp") if a.s.node(n)["attrs"].get("name") == "knob_edit"][0]
    assert at.get("step_mode") == "grain" and at.get("grain_end") == 1


def test_explore_unscored_is_the_cue_set_edit_default():
    a = WorldAdapter(seeds=())
    rf._ensure_seed_chain(a.s, a.inner, a.agent, ("variation_ops",))
    at = [a.s.node(n)["attrs"] for n in a.s.nodes("VariationOp") if a.s.node(n)["attrs"].get("name") == "cue_set_edit"][0]
    assert at.get("explore_unscored") == 1
