"""test_ground_concern_six_kinds_migrated — GROUND_CONCERN_SIX_KINDS_PREREG.md
gates, Path 2 (the honesty investigation's own §5 recommendation, applied to
the six concern kinds still routing through `_concern_tick`'s generic
fallback per its own §2 table row).

Background: `GROUND_CONCERN_COMPREHENSION_HONESTY_RESULTS.md` proved LIVE
that `domains/reflective_faculty.py::_compose_comprehension_rule`'s
unconditional terminal branch cannot be gated from what it receives without
breaking currently-relied-upon callers (`build_describe_faculty`,
`recount_faculty`). Its own §5 named Path 2 — a dedicated routing check per
concern KIND at the promotion/tick layer, mirroring `code_write`/`prog_read`
exactly (`PROGRAM_SYNTHESIS_ARC6_PROGREAD_SELFIMPROVE.md`, amendment A25) —
as the safe, minimal close. This rung's own PREREG (§0) measured the six
kinds LIVE before building anything and found the population is NOT
uniform: `knowledge`/`self_account` always fall through the generic
fallback; `reply_fix` falls through only on its `comprehend_first`
sub-case (its `experiment` sub-case was ALREADY correctly wired); and
`instruction`/`performance`/`comprehension` NEVER fall through (an
unconditional kind-membership check in `_promote_relations_for_concern`
routes them straight to the genuine conversation-experiment composer) — so
this file gates three real fixes and one "already safe, nothing built"
demonstration, not six copies of the same test.
"""
from __future__ import annotations

import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"),
           os.path.join(ROOT, "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

jd = pytest.importorskip("jabberwock_daemon")

from substrate.boot_all import load_all_seeds       # noqa: E402
from substrate.world_adapter import WorldAdapter     # noqa: E402
import domains.knowledge_growth as kng               # noqa: E402
import domains.self_account_growth as sag            # noqa: E402
import domains.reply_fix_growth as rfg               # noqa: E402


@pytest.fixture(autouse=True)
def _no_real_seed_writes(monkeypatch):
    monkeypatch.setenv("OZMA_SEED_PERSIST_DISABLED", "1")


@pytest.fixture()
def agent():
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    return a


def _mint_and_promote(agent, kind: str, content: str):
    sc = agent.s.add_node("SelfConcern", {
        "status": "noted", "source": "implicit", "kind": kind, "content": content,
    })
    agent.inner.add_edge_unchecked(agent.agent, "has_self_concern", sc)
    scid = jd._nid_value(sc)
    res = jd.promote_self_concern(agent, str(scid))
    assert res["ok"], res
    standing_id = None
    for n in agent.s.nodes("StandingConcern"):
        if agent.s.node(n)["attrs"].get("name") == "promoted_self_concern_%d" % scid:
            standing_id = n
            break
    assert standing_id is not None
    return sc, standing_id, res


def _no_dead_comprehension_rule(agent) -> bool:
    return not any(
        r.get("active") and "comprehend_describe_directive" in (r.get("name") or "")
        for r in agent.inner.export_rules())


# =========================================================================== #
#  KNOWLEDGE — routes to the EXISTING self-heal chain (ground_unknowns /
#  answer_about), not a new mechanism. Both branches: honest re-attempt
#  failure, and genuine re-grounding success.
# =========================================================================== #
def test_knowledge_gap_no_longer_installs_dead_comprehension_rule(agent):
    sc, standing_id, res = _mint_and_promote(agent, "knowledge", "photosynthesis")
    assert res["pipeline"] == "comprehend_first"
    jd._concern_tick(agent)
    at = agent.s.node(standing_id)["attrs"]
    assert at["status"] == "processed"
    assert at.get("knowledge_compose_ok") == 0.0
    assert "ground_unknowns" in at.get("knowledge_compose_reason", "")
    assert _no_dead_comprehension_rule(agent)
    assert agent.s.nodes("Experiment") == []


def test_knowledge_gap_resolves_when_self_teacher_now_grounds_it(agent, monkeypatch):
    # The real self-teacher contract (WorldAdapter.learn_from_teacher):
    # {"answer": ..., "learn": [{"phrase": ..., ...}]}. A bare {"concept": ...}
    # payload (no "learn" entries) is exactly the "teacher answered but
    # nothing gets registered" case ground_unknowns already handles as a
    # non-grounding — this fixture uses the real shape so the SUCCESS branch
    # is exercised, not just the failure branch already covered above.
    agent._self_teacher = lambda w: {
        "answer": "a sun-powered process",
        "learn": [{"phrase": w, "binding_pattern": "function_of_subject"}],
    }
    sc, standing_id, res = _mint_and_promote(agent, "knowledge", "photosynthesis")
    jd._concern_tick(agent)
    at = agent.s.node(standing_id)["attrs"]
    assert at.get("knowledge_compose_ok") == 1.0
    agent.s._inner.run_rules(400000)
    assert agent.s.node(sc)["attrs"].get("status") == "resolved"


def test_knowledge_gap_experiment_subcase_untouched(agent):
    # A knowledge concern whose content happens to name experiment vocabulary
    # (a rare edge case, already pre-existing behaviour) must NOT reach the
    # new dedicated function — _promote_relations_for_concern is unmodified.
    sc, standing_id, res = _mint_and_promote(agent, "knowledge", "grammar rules")
    assert res["pipeline"] == "experiment"
    jd._concern_tick(agent)
    at = agent.s.node(standing_id)["attrs"]
    assert "knowledge_compose_ok" not in at


def test_work_on_knowledge_gap_reader_unit():
    class _NoTeacher:
        answer_about = staticmethod(lambda t: None)
        ground_unknowns = None
    out = kng.work_on_knowledge_gap(_NoTeacher(), "")
    assert out["ok"] is False
    assert "no topic" in out["reason"]


# =========================================================================== #
#  SELF_ACCOUNT — routes to the EXISTING SelfProcess/find_self_process
#  lookup. Unconditional interception (measured: no safe existing pipeline
#  value for this kind). Both branches: no held account (honest exhaustion,
#  never fabricates), and a held account (real progress).
# =========================================================================== #
def test_self_account_gap_no_longer_installs_dead_comprehension_rule(agent):
    sc, standing_id, res = _mint_and_promote(agent, "self_account", "reasoning")
    assert res["pipeline"] == "comprehend_first"
    jd._concern_tick(agent)
    at = agent.s.node(standing_id)["attrs"]
    assert at["status"] == "processed"
    assert at.get("self_account_compose_ok") == 0.0
    reason = at.get("self_account_compose_reason", "")
    assert "no held SelfProcess account" in reason
    assert "reasoning" in reason
    assert _no_dead_comprehension_rule(agent)
    assert agent.s.nodes("Experiment") == []
    agent.s._inner.run_rules(400000)
    assert agent.s.node(sc)["attrs"].get("status") == "promoted"  # never fabricated -> stays open


def test_self_account_gap_resolves_when_a_held_account_already_exists(agent):
    # "collapse" is a real, seeded SelfProcess (seeds/self_processes.json) —
    # CLAUDE.md's own "self_processes" section names it accounted.
    sc, standing_id, res = _mint_and_promote(agent, "self_account", "collapse")
    jd._concern_tick(agent)
    at = agent.s.node(standing_id)["attrs"]
    assert at.get("self_account_compose_ok") == 1.0
    assert at.get("self_account_compose_reason", "").find("collapse") != -1
    agent.s._inner.run_rules(400000)
    assert agent.s.node(sc)["attrs"].get("status") == "resolved"


def test_self_account_never_fabricates_an_account(agent):
    out = sag.work_on_self_account_gap(agent, "some_totally_unheard_of_faculty")
    assert out["ok"] is False
    assert "never" in out["reason"] and "fabricated" in out["reason"]


# =========================================================================== #
#  REPLY_FIX — split per content tag. `upload_attachment_reply` closes by
#  loading the two named seeds (a real, mechanical fix); `upload_vision_
#  wiring` honestly NO-GOes (Rust/adapter boundary). The `experiment`
#  sub-case (content names acting/seed/ablation vocabulary) is untouched —
#  gated already by tests/test_self_improvement_visibility_migrated.py, and
#  re-checked here for this rung's own interception guard specifically.
# =========================================================================== #
def test_reply_fix_upload_attachment_tag_loads_the_missing_seeds_and_resolves(agent):
    assert not any(agent.s.node(n)["attrs"].get("id") == "conversation_attachment_route"
                   for n in agent.s.nodes("Seed"))
    sc, standing_id, res = _mint_and_promote(agent, "reply_fix", "upload_attachment_reply")
    assert res["pipeline"] == "comprehend_first"
    jd._concern_tick(agent)
    at = agent.s.node(standing_id)["attrs"]
    assert at.get("reply_fix_compose_ok") == 1.0
    assert "conversation_attachment_route" in at.get("reply_fix_compose_reason", "")
    assert any(agent.s.node(n)["attrs"].get("id") == "conversation_attachment_route"
              for n in agent.s.nodes("Seed"))
    assert _no_dead_comprehension_rule(agent)
    agent.s._inner.run_rules(400000)
    assert agent.s.node(sc)["attrs"].get("status") == "resolved"


def test_reply_fix_upload_attachment_tag_honestly_reports_when_already_loaded(agent):
    from substrate.seed_loader import manifest_for
    for sid in ("conversation_attachment_route", "conversation_attachment_reply"):
        agent.inner.load_seed_manifest(manifest_for(sid), agent.agent)
        agent.s.add_node("Seed", {"id": sid})
    sc, standing_id, res = _mint_and_promote(agent, "reply_fix", "upload_attachment_reply")
    jd._concern_tick(agent)
    at = agent.s.node(standing_id)["attrs"]
    assert at.get("reply_fix_compose_ok") == 0.0
    assert "ALREADY present" in at.get("reply_fix_compose_reason", "")


def test_reply_fix_upload_vision_tag_honestly_no_goes(agent):
    sc, standing_id, res = _mint_and_promote(agent, "reply_fix", "upload_vision_wiring")
    jd._concern_tick(agent)
    at = agent.s.node(standing_id)["attrs"]
    assert at.get("reply_fix_compose_ok") == 0.0
    reason = at.get("reply_fix_compose_reason", "")
    assert "GraphEye" in reason
    assert _no_dead_comprehension_rule(agent)
    agent.s._inner.run_rules(400000)
    at2 = agent.s.node(standing_id)["attrs"]
    assert at2.get("experiments_exhausted") is True
    assert "GraphEye" in at2.get("exhausted_note", "")


def test_reply_fix_experiment_subcase_reaches_the_genuine_composer_untouched(agent):
    sc, standing_id, res = _mint_and_promote(
        agent, "reply_fix", "ablate conversation seed and test acting variant")
    assert res["pipeline"] == "experiment"
    jd._concern_tick(agent)
    at = agent.s.node(standing_id)["attrs"]
    # the new dedicated function must NEVER have run for this sub-case.
    assert "reply_fix_compose_ok" not in at
    assert any(r.get("active") and "author_experiment_from_residual" in (r.get("name") or "")
              for r in agent.inner.export_rules())


def test_work_on_reply_fix_gap_generic_fallback_for_unknown_tag():
    out = rfg.work_on_reply_fix_gap(None, "some_freeform_reply_fix_note")
    assert out["ok"] is False
    assert "no known correspondence" in out["reason"]


# =========================================================================== #
#  INSTRUCTION / PERFORMANCE / COMPREHENSION — the "no bug, nothing built"
#  arm: unconditional kind-membership in _promote_relations_for_concern
#  already routes these three straight to the genuine conversation-
#  experiment composer, never through the buggy comprehend-first fallback.
#  This rung's job for them is proving that live, not building anything.
# =========================================================================== #
@pytest.mark.parametrize("kind,content", [
    ("instruction", "elaborate further details"),
    ("performance", "shadow-read comprehension latency exceeds its held ceiling"),
    ("comprehension", "comprehension classified this as question but heard statement"),
])
def test_instruction_performance_comprehension_never_reach_the_generic_fallback(
        agent, kind, content):
    sc, standing_id, res = _mint_and_promote(agent, kind, content)
    assert res["pipeline"] == "experiment"
    jd._concern_tick(agent)
    at = agent.s.node(standing_id)["attrs"]
    # no dedicated function exists for these three (by design, PREREG IPC-c) —
    # confirm no *_compose_ok datum from any of the new modules leaked in.
    for k in ("knowledge_compose_ok", "self_account_compose_ok", "reply_fix_compose_ok"):
        assert k not in at
    assert _no_dead_comprehension_rule(agent)
    assert any(r.get("active") and "author_experiment_from_residual" in (r.get("name") or "")
              for r in agent.inner.export_rules())
