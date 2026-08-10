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
    assert int(ra["score"]) >= 1
    child = json.load(open(os.path.join(agent.s.node(exp)["attrs"]["run_dir"], "result.json")))
    assert child["flagged"] == 1 and child["flagged_changed"] == 1 and child["regressions"] == 0

    # (e) the agent's OWN authored judge rule reads the run: supported
    agent.comprehend()
    at = agent.s.node(exp)["attrs"]
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
    aat = agent.s.node(adoptions[0])["attrs"]
    assert aat.get("cue_route") == route and aat.get("rule_removed") == "" and aat.get("rule_added") == ""
    live = [agent.s.node(n)["attrs"] for n in agent.s.nodes("Concept")
            if agent.s.node(n)["attrs"].get("name") == "condense"]
    assert any(c.get("instruction_route") == route for c in live), "the parent holds the Concept live"
    # the adoption filed the Concept through teach() UNDER THE OWNING SEED
    # (comprehend_instruction — the manifest a fresh boot re-holds it from).
    # NOTE: tests/conftest.py's session guard (OZMA_SEED_PERSIST_DISABLED)
    # blocks every real-seeds-dir write for the whole bench — the DISK write
    # is deliberately not exercised here (teach()'s write/guard mechanics have
    # their own gate, test_seed_guard_migrated); the record proves the
    # adoption targeted the right seed, and the live node above proves the
    # parent holds it NOW. Verified live (guard off) during the wave's
    # bring-up: seeds/comprehend_instruction.json gains the Concept node.
    cue_recs = [r for r in records if isinstance(r, dict) and r.get("cue_concept_added") == "condense"]
    assert len(cue_recs) == 1
    taught = cue_recs[0]["cue_taught"]
    assert taught["category"] == "comprehend_instruction"
    assert taught["seed"].endswith(os.path.join("seeds", "comprehend_instruction.json"))

    # (g) the parent now HANDLES the previously-uncovered instruction — no gap
    n_gaps = len(_instruction_gaps(agent))
    reply = agent.converse("Condense the data.", speech_act="request")
    mid = agent._last_turn_inbound
    assert agent.s.node(mid)["attrs"].get("instruction_outcome") == "handled"
    assert "filed it as a gap" not in reply.lower()
    assert (reply or "").strip() != floor.strip()
    assert len(_instruction_gaps(agent)) == n_gaps, "no new instruction gap filed"


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

    # 3. zero character overlap -> abstain, never a random route
    _wire_concern(a, "k_zero", "instruction", "zzz")
    r = rf._compose_cue_variant(a, ["k_zero"], "t3")
    assert r["built"] is False and "abstained" in r["wall"]

    # 4. and the genuine case builds a Concept whose route is pooled
    _wire_concern(a, "k_real", "instruction", "condense")
    r = rf._compose_cue_variant(a, ["k_real"], "t4")
    assert r["built"] is True and r["concept"]["attrs"]["name"] == "condense"
    assert r["route"] in ("world_action", "comprehend_text")
