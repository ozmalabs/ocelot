"""WHOLE-CURRICULUM WAVE 1: the standing study loop + flow retirement.

Part A -- flow retirement (domains/flow_retire.py, seeds/curriculum_study.json's
`study_flow_retirable`): a settled StudyLesson's Wave-1A flow/unit-scoped working
nodes are swept once its extraction products are on the graph; products (taught
ShapeSignatures, SelfConcern gaps, the StudyLesson/Curriculum nodes themselves)
persist; a live (mid-extraction) flow is never touched.

Part B -- the study loop (domains/curriculum_study.py): a held-Argmin pick over
`order` among `queued` StudyLessons, routed through the UNCHANGED
`code_curriculum.learn_from_lesson` path; the lifecycle rules
(`study_lesson_blocked_on_unanswered_exercise` / `_done_clean`) decide
blocked-vs-done from this attempt's own exercises_attempted/exercises_answered
counts; `study_lesson_reopen_on_growth` re-arms a blocked lesson when
`Agent.write_codebook_epoch` (bumped by `code_write_growth._teach_shape` on
genuine LIVE-GRAPH novelty -- persistence-independent, see its own comment) grows
past the lesson's own `decoded_epoch`.

Part C -- the emitter roadmap (domains/curriculum_study.py's `emitter_roadmap` /
`run_emitter_roadmap`): a demand-ranked frequency table over open code_write/
code_read gap reasons, weighted by distinct lessons blocked; surfaced over NL
("what blocks your learning?") via question_targets + reflective_faculty._DISPATCH,
the `_run_self_gaps`/`code_capabilities` precedent.

Run: PYTHONPATH=runners/dsl/python:.:scripts OZMA_NO_LLM=1 python3 -m pytest \
     tests/test_curriculum_study_migrated.py -p no:randomly -q
"""
from __future__ import annotations

import os
import sys
import tempfile

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

srs = pytest.importorskip("substrate_rs")

from substrate.world_adapter import WorldAdapter          # noqa: E402
from substrate.boot_all import load_all_seeds             # noqa: E402
from domains import code_reading as cdr                   # noqa: E402
from domains import code_write_growth as cwg              # noqa: E402
from domains import curriculum_study as cs                # noqa: E402
from domains import flow_retire as fr                     # noqa: E402

FIXTURE_DIR = os.path.join(ROOT, "tests", "fixtures", "code_curriculum")


@pytest.fixture(autouse=True)
def _no_real_seed_writes(monkeypatch):
    monkeypatch.setenv("OZMA_SEED_PERSIST_DISABLED", "1")


@pytest.fixture()
def full_agent():
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    return a


def _write_lesson(tmp_path, name: str, text: str) -> str:
    p = os.path.join(str(tmp_path), name)
    with open(p, "w", encoding="utf-8") as f:
        f.write(text)
    return p


def _n_all(agent) -> int:
    return len(list(agent.s.nodes(None)))


def _n_flow(agent, flow_id) -> int:
    n = 0
    for nid in agent.s.nodes(None):
        at = agent.s.node(nid)["attrs"]
        if at.get("flow") == flow_id or at.get("unit") == flow_id:
            n += 1
    return n


# =========================================================================== #
#  PART B -- lesson lifecycle: queued -> reading -> extracted -> done/blocked.
# =========================================================================== #
def test_lesson_lifecycle_clean_lesson_settles_done(full_agent, tmp_path):
    a = full_agent
    text = "This is a short piece of prose with no exercise in it at all."
    path = _write_lesson(tmp_path, "clean.txt", text)
    cs.install_curriculum(a, "lifecycle-clean", [(1, "clean", path)])
    r = cs.study_tick(a)
    assert r["picked"] is not None
    lid = r["picked"]
    at = a.s.node(lid)["attrs"]
    assert at["status"] == "done"
    assert at["exercises_attempted"] == 0.0
    assert at["record_written"] == 1.0


def test_lesson_lifecycle_unanswered_exercise_blocks(full_agent, tmp_path):
    a = full_agent
    text = "Write a function called frobnicate that frobnicates a widget."
    path = _write_lesson(tmp_path, "blocked.txt", text)
    cs.install_curriculum(a, "lifecycle-blocked", [(1, "blocked", path)])
    r = cs.study_tick(a)
    lid = r["picked"]
    at = a.s.node(lid)["attrs"]
    assert at["status"] == "blocked"
    assert at["exercises_attempted"] == 1.0
    assert at["exercises_answered"] == 0.0


def test_study_tick_picks_in_order_not_insertion_order(full_agent, tmp_path):
    a = full_agent
    p1 = _write_lesson(tmp_path, "l1.txt", "A short lesson with no exercises here.")
    p2 = _write_lesson(tmp_path, "l2.txt", "Another short lesson, also with none.")
    # inserted in REVERSE order -- the pick must still respect `order`, not
    # insertion sequence (the held-Argmin idiom, never insertion order).
    cs.install_curriculum(a, "order-test", [(2, "second", p2), (1, "first", p1)])
    r1 = cs.study_tick(a)
    assert a.s.node(r1["picked"])["attrs"]["title"] == "first"
    r2 = cs.study_tick(a)
    assert a.s.node(r2["picked"])["attrs"]["title"] == "second"
    r3 = cs.study_tick(a)
    assert r3["picked"] is None


def test_study_tick_idle_when_nothing_queued(full_agent):
    a = full_agent
    r = cs.study_tick(a)
    assert r["picked"] is None
    assert r["swept"]["total_deleted"] == 0


# =========================================================================== #
#  PART A -- flow retirement.
# =========================================================================== #
def test_flow_retirement_sweeps_working_nodes_keeps_products(full_agent, tmp_path):
    a = full_agent
    text = _open_fixture("lesson_boolean_functions.txt")
    path = _write_lesson(tmp_path, "boolean.txt", text)
    cs.install_curriculum(a, "retire-test", [(1, "boolean", path)])

    r = cs.study_tick(a)
    lid = r["picked"]
    flow_id = r["flow_id"]
    assert flow_id is not None
    assert r["swept"]["total_deleted"] > 0, "the flow's own working nodes must be swept"
    assert _n_flow(a, flow_id) == 0, "no flow-scoped node should survive retirement"

    at = a.s.node(lid)["attrs"]
    assert at["flow_retired"] == 1.0 and at["flow_swept"] == 1.0

    # PRODUCTS persist: the taught ShapeSignature, and the Lesson/Curriculum
    # nodes themselves.
    taught = [n for n in a.s.nodes("ShapeSignature")
             if a.s.node(n)["attrs"].get("name") == "taught_is_divisible"]
    assert taught, "the taught shape must survive flow retirement"
    assert a.s.has_node(lid)
    for n in a.s.nodes("Curriculum"):
        assert a.s.node(n)["attrs"].get("title") == "retire-test"


def test_flow_retirement_keeps_gap_selfconcern(full_agent, tmp_path):
    a = full_agent
    text = "Write a function called frobnicate that frobnicates a widget."
    path = _write_lesson(tmp_path, "gapped.txt", text)
    cs.install_curriculum(a, "retire-gap-test", [(1, "gapped", path)])
    r = cs.study_tick(a)
    flow_id = r["flow_id"]
    assert _n_flow(a, flow_id) == 0
    gaps = cwg.pending_code_write_gaps(a)
    assert any("frobnicate" in g["content"] for g in gaps), \
        "the filed capability gap must survive flow retirement"


def test_sweep_never_touches_a_live_not_yet_retired_flow(full_agent, tmp_path):
    """A StudyLesson still `status='reading'` (mid-extraction, `flow_retired`
    never set) must be a complete no-op for the sweep -- retirement fires
    strictly AFTER extraction, never mid-flow."""
    a = full_agent
    sub = a.s
    lid = sub.add_node("StudyLesson", {
        "order": 1.0, "title": "midflow", "status": "reading",
        "text_path": "x", "decoded_epoch": 0.0, "flow_retired": 0.0,
        "flow_swept": 0.0, "record_written": 0.0, "flow_id": 999999.0,
    })
    marker = sub.add_node("SentenceParse", {"sentence": "x", "flow": 999999.0})
    out = fr.sweep_retired_flows(a)
    assert out["total_deleted"] == 0
    assert sub.has_node(marker), "a live flow's working node must not be deleted"


# =========================================================================== #
#  Node-count trajectory -- retirement keeps the substrate roughly flat across
#  many lessons instead of accumulating every flow's scaffolding forever.
# =========================================================================== #
def test_retirement_bounds_node_growth_across_many_lessons(tmp_path):
    lesson_texts = [
        "This is lesson number one, some short unremarkable prose about nothing much.",
        "This is lesson number two, some short unremarkable prose about nothing much.",
        "This is lesson number three, some short unremarkable prose about nothing much.",
        "This is lesson number four, some short unremarkable prose about nothing much.",
    ]
    paths = [_write_lesson(tmp_path, f"n{i}.txt", t) for i, t in enumerate(lesson_texts)]

    a_retired = WorldAdapter(seeds=())
    load_all_seeds(a_retired)
    cs.install_curriculum(a_retired, "growth-retired",
                          [(i, f"n{i}", p) for i, p in enumerate(paths)])
    deltas_retired = []
    for _ in range(len(paths)):
        before = _n_all(a_retired)
        cs.study_tick(a_retired)
        deltas_retired.append(_n_all(a_retired) - before)

    a_bare = WorldAdapter(seeds=())
    load_all_seeds(a_bare)
    cs.install_curriculum(a_bare, "growth-bare",
                          [(i, f"n{i}", p) for i, p in enumerate(paths)])
    deltas_bare = []
    for _ in range(len(paths)):
        before = _n_all(a_bare)
        lesson = cs.pick_next_queued_lesson(a_bare)
        at = a_bare.s.node(lesson)["attrs"]
        a_bare.s.set_attr(lesson, "status", "reading")
        text = open(at["text_path"], encoding="utf-8").read()
        from domains import code_curriculum as cc
        cc.learn_from_lesson(a_bare, text, lesson_source=at["title"])
        a_bare.s.set_attr(lesson, "status", "done")   # no retirement at all
        deltas_bare.append(_n_all(a_bare) - before)

    assert sum(deltas_retired) < sum(deltas_bare), (
        "cumulative node growth WITH retirement must be smaller than WITHOUT it",
        deltas_retired, deltas_bare)
    # every retired lesson's own per-tick delta must be smaller than its
    # un-retired twin's -- the sweep is doing real, per-lesson work, not just
    # winning on aggregate noise.
    assert all(dr <= db for dr, db in zip(deltas_retired, deltas_bare))


# =========================================================================== #
#  REOPEN -- a blocked lesson re-attempts when the write codebook grows.
# =========================================================================== #
def test_reopen_on_write_codebook_growth(full_agent, tmp_path):
    a = full_agent
    lesson_a_text = "Write a function called cube_it that returns a number raised to the third power."
    path_a = _write_lesson(tmp_path, "lesson_a.txt", lesson_a_text)
    cs.install_curriculum(a, "reopen-test", [(1, "lesson_a", path_a)])

    r0 = cs.study_tick(a)
    lid = r0["picked"]
    flow0 = r0["flow_id"]
    assert a.s.node(lid)["attrs"]["status"] == "blocked"

    _sub, _native, ag = cdr._resolve(a)
    epoch_before = a.s.node(ag)["attrs"].get("write_codebook_epoch", 0.0) or 0.0

    # LESSON B: a second lesson whose code region teaches EXACTLY the shape
    # lesson A's exercise needs -- run through the SAME curriculum path, then
    # taught with the SAME request_text as lesson A's own filed gap so the
    # exact-match resolve rule (seeds/code_write_gap.json) can also fire.
    res = cwg.teach_write_shape_from_example(
        a, "def cube_it(n):\n    return n ** 3\n", request_text=lesson_a_text)
    assert res["ok"], res

    epoch_after = a.s.node(ag)["attrs"].get("write_codebook_epoch", 0.0) or 0.0
    assert epoch_after > epoch_before, "teaching a genuinely NEW shape must bump the epoch"

    # a bare comprehend (no study_tick call) is enough for the reopen rule to
    # re-arm the lesson to 'queued' -- it is a graph decision, not something
    # the driver has to special-case.
    a.comprehend()
    assert a.s.node(lid)["attrs"]["status"] == "queued"

    r1 = cs.study_tick(a)
    assert r1["picked"] == lid
    assert r1["flow_id"] != flow0, "the reopened attempt must mint a FRESH flow"
    assert a.s.node(lid)["attrs"]["status"] == "done"
    assert a.s.node(lid)["attrs"]["exercises_answered"] == 1.0


def test_epoch_bump_is_persistence_independent(full_agent):
    """A re-teach of an ALREADY-held shape must NOT bump the epoch (only
    genuine live-graph novelty does) -- teach()'s own `saved` flag is the
    WRONG signal under OZMA_SEED_PERSIST_DISABLED (always False), which this
    test's env (`_no_real_seed_writes`) exercises exactly."""
    a = full_agent
    _sub, _native, ag = cdr._resolve(a)
    src = "def sign_flip(x):\n    return -x\n"
    r1 = cwg.teach_write_shape_from_example(a, src, request_text="flip the sign")
    assert r1["ok"]
    e1 = a.s.node(ag)["attrs"].get("write_codebook_epoch", 0.0) or 0.0
    assert e1 >= 1.0
    r2 = cwg.teach_write_shape_from_example(a, src, request_text="flip the sign")
    assert r2["ok"]
    e2 = a.s.node(ag)["attrs"].get("write_codebook_epoch", 0.0) or 0.0
    assert e2 == e1, "re-teaching an already-held shape must not bump the epoch again"


# =========================================================================== #
#  PART C -- the emitter roadmap.
# =========================================================================== #
def test_roadmap_aggregation_is_deterministic_and_ranked_by_lessons_blocked(full_agent, tmp_path):
    a = full_agent
    p1 = _write_lesson(tmp_path, "r1.txt",
                       "Write a function called frobnicate that frobnicates a widget.")
    p2 = _write_lesson(tmp_path, "r2.txt",
                       "Write a function called snorkelize that snorkelizes a gadget.")
    p3 = _write_lesson(tmp_path, "r3.txt",
                       "Write a function called frobnicate that frobnicates a widget.")
    cs.install_curriculum(a, "roadmap-test", [(1, "r1", p1), (2, "r2", p2), (3, "r3", p3)])
    for _ in range(3):
        cs.study_tick(a)

    rm = cs.emitter_roadmap(a)
    reasons = rm["reasons"]
    assert reasons, reasons
    top = reasons[0]
    assert "frobnicate" in top["reason"]
    assert top["lessons_blocked"] == 2, reasons
    # deterministic on repeat calls (no re-decision, a pure re-read).
    rm2 = cs.emitter_roadmap(a)
    assert rm2 == rm


def test_nl_surface_what_blocks_your_learning_empty(full_agent):
    a = full_agent
    reply = a.converse("What blocks your learning?")
    assert "Nothing is blocking my learning" in reply


def test_nl_surface_what_blocks_your_learning_nonempty(full_agent, tmp_path):
    a = full_agent
    path = _write_lesson(tmp_path, "nl.txt",
                         "Write a function called frobnicate that frobnicates a widget.")
    cs.install_curriculum(a, "nl-test", [(1, "nl", path)])
    cs.study_tick(a)
    reply = a.converse("What blocks your learning?")
    assert "frobnicate" in reply
    assert "blocking 1 lesson" in reply


def _open_fixture(name: str) -> str:
    return open(os.path.join(FIXTURE_DIR, name), encoding="utf-8").read()
