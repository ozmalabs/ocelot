"""curriculum_study — WHOLE-CURRICULUM WAVE 1, PARTS B/C: the standing study
loop over a whole published book, and the gap-aggregation roadmap.

`domains/code_curriculum.py` (commit a3c244a87) already proved the per-lesson
mechanics on three hand-picked Think Python 2e excerpts: code blocks found BY
SHAPE, taught by example with lesson provenance, exercise sentences run
through the real conversational request path, a beyond-boundary lesson
filing an honest gap. THIS module is PURE ROUTING that turns that one-shot
per-lesson call into a STANDING loop over an ordered `Curriculum` of many
`StudyLesson`s -- graph-native bookkeeping only. The lifecycle DECISIONS
(blocked vs done, reopen-on-growth, flow-retirable) are rules
(`seeds/curriculum_study.json`); this module writes the FACTS those rules
read (extraction outcome counts, `record_written`, `filed_gap` edges) and
executes what a rule has already decided (picks the next queued lesson via a
held `Argmin` Term -- the single-survivor idiom, never a Python min/sort;
sweeps a flow a rule marked retirable via `domains.flow_retire`).

ARCHITECTURE (CLAUDE.md): no Python decision over MEANING. "Which lesson is
next" is a held Argmin over an already-decided `status=='queued'` set,
ordered by an already-held `order` attr -- a query, not a ranking choice.
"Did this lesson finish clean or blocked" is the seed rule's call, from facts
this module writes mechanically (an extraction's own counts, and which
SelfConcern nodes exist -- both simple, undecided reads of what
`code_curriculum.learn_from_lesson` and the gap-filing rules already
produced).
"""
from __future__ import annotations

import os
from typing import Any, Optional

from domains import code_curriculum as cc
from domains import code_reading as cdr
from domains import flow_retire as fr
from domains import vision_curriculum as vis
from domains import voice_curriculum as vc


# --------------------------------------------------------------------------- #
#  RECONCILE (WAVE 2) — a resumed checkpoint's graph was saved BEFORE an
#  emitter-widening landed in `seeds/code_constructions.json`; `ensure_
#  codebook`'s own Seed{id:'code_constructions'} idempotency guard means a
#  bare re-boot would silently keep running the STALE (pre-widening) read
#  codebook (the SAME resumed-daemon gotcha CLAUDE.md documents for seed
#  rules -- `_reconcile_seed_rules`/`_reconcile_seed_typed_nodes` in
#  scripts/jabberwock_daemon.py). This is the read-codebook analogue: find
#  every ShapeSignature the manifest names but the graph does not yet
#  hold (by `name`, not by Seed-id presence), install it, and bump
#  `codebook_epoch` once per newly-installed construction so
#  `study_lesson_reopen_on_growth` (WAVE 2) sees the growth and re-arms
#  every blocked lesson for a fresh attempt. Mechanical seed I/O -- no
#  decision about WHICH lessons care, exactly like the write-side reopen's
#  own documented "no content-overlap filter" precedent.
# --------------------------------------------------------------------------- #
def reconcile_code_construction_seed(agent) -> dict:
    """Install any `code_construction` ShapeSignature named in `seeds/
    code_constructions.json` that the live graph does not already hold
    (matched by `name`) -- idempotent, additive, safe to call on every
    resume. Returns {installed: [names]}.

    Deliberately does NOT bump `codebook_epoch`: the sd loop's own
    epoch-gated re-decode (`sd_redecode`) re-arms EVERY held decode when
    that counter moves -- a whole-graph side effect the study reopen does
    not need (the read decode consults the codebook directly, no epoch
    dependency). The reopen rule is armed instead via
    `reconcile_lesson_epoch_tracking`'s stale marker (below)."""
    import json
    import os
    sub, _native, ag = cdr._resolve(agent)
    held = {sub.node(n)["attrs"].get("name")
            for n in sub.nodes("ShapeSignature")
            if sub.node(n)["attrs"].get("kind") == "code_construction"}
    path = os.path.join(cdr._ROOT, "seeds", "code_constructions.json")
    with open(path) as f:
        manifest = json.load(f)
    installed = []
    for nd in manifest.get("nodes", []):
        at = nd.get("attrs", {})
        if at.get("name") in held:
            continue
        sub.add_node(nd["type"], dict(at))
        installed.append(at.get("name"))
    # Initialise (never bump) the epoch counter if the graph has none yet --
    # the SAME "if None: set 0.0" move ensure_codebook itself makes, so the
    # reopen rule's Lt comparison always reads a real number.
    if ag is not None and sub.node(ag)["attrs"].get("codebook_epoch") is None:
        sub.set_attr(ag, "codebook_epoch", 0.0)
    return {"installed": installed}


def reconcile_lesson_epoch_tracking(agent, *, stale: bool = False) -> dict:
    """Every pre-WAVE-2 `StudyLesson` was checkpointed without a
    `read_decoded_epoch` attr (the reopen rule's new second watch,
    above) -- initialise it wherever absent so the rule's `Lt` comparison
    always reads a real number, never a missing attr. With `stale=True`
    (pass it when `reconcile_code_construction_seed` actually installed a
    new construction), the backfill value is -1.0 -- a factual marker
    ("this lesson has NEVER been decoded against the current read
    codebook"), strictly below any real epoch, so the seeded reopen rule
    re-arms every blocked lesson for a fresh attempt WITHOUT a global
    `codebook_epoch` bump (see reconcile_code_construction_seed's note).
    With `stale=False` the backfill is the agent's CURRENT epoch (no
    reopen implied). Mechanical fixup, idempotent (a lesson that already
    carries the attr is left untouched). Returns {fixed: n}."""
    sub = getattr(agent, "s", agent)
    _sub2, _native2, ag = cdr._resolve(agent)
    cur_epoch = 0.0
    if ag is not None:
        cur_epoch = sub.node(ag)["attrs"].get("codebook_epoch") or 0.0
    value = -1.0 if stale else float(cur_epoch)
    n = 0
    for lid in sub.nodes("StudyLesson"):
        at = sub.node(lid)["attrs"]
        if "read_decoded_epoch" not in at or at.get("read_decoded_epoch") is None:
            sub.set_attr(lid, "read_decoded_epoch", value)
            n += 1
    return {"fixed": n, "value": value}


# --------------------------------------------------------------------------- #
#  INSTALL — mint a Curriculum + its ordered StudyLessons. Mechanical: one
#  node per lesson file, one edge per relation, nothing decided.
# --------------------------------------------------------------------------- #
def install_curriculum(agent, title: str, lessons: list, *, source: str = "") -> dict:
    """`lessons`: an ordered list of `(order:int, lesson_title:str,
    text_path:str)` -- the original CODE-CURRICULUM shape, routed through
    `code_curriculum.learn_from_lesson` (kind defaults to 'code', unchanged
    behaviour) -- OR, for a VOICE-EXPANSION lesson (WHOLE-CURRICULUM WAVE 3),
    a 4-tuple `(order, lesson_title, text_path, kind)` with
    `kind in {'morphology', 'vocabulary', 'construction'}`, routed through
    `voice_curriculum.learn_voice_from_lesson` by `study_tick`. Mints one
    `Curriculum` node, one `StudyLesson` per entry (status='queued'),
    `Agent -has_curriculum-> Curriculum` and `Curriculum -has_lesson->
    StudyLesson` edges. Idempotent by title: an existing Curriculum with the
    same `title` is reused (its lessons are NOT re-scanned/re-added --
    re-installing the same book twice is a no-op on the lesson set, so a
    resumed run never duplicates lessons)."""
    sub = getattr(agent, "s", agent)
    _sub2, _native2, ag = cdr._resolve(agent)
    # Lazily initialise the voice epoch counter (the SAME "if None: set 0.0"
    # idiom code_reading.ensure_codebook / reconcile_code_construction_seed
    # already use for codebook_epoch) so study_lesson_reopen_on_growth's Lt
    # comparison always reads a real number, never a missing attr.
    if ag is not None and sub.node(ag)["attrs"].get("voice_codebook_epoch") is None:
        sub.set_attr(ag, "voice_codebook_epoch", 0.0)
    # Same "if None: set 0.0" idiom for the vision counter (STAGE 2), so
    # study_lesson_reopen_on_growth's fourth Lt arm always reads a real
    # number rather than a missing attr.
    if ag is not None and sub.node(ag)["attrs"].get("vision_codebook_epoch") is None:
        sub.set_attr(ag, "vision_codebook_epoch", 0.0)
    for n in sub.nodes("Curriculum"):
        if sub.node(n)["attrs"].get("title") == title:
            return {"curriculum": n, "lessons": [], "reused": True}
    cur = sub.add_node("Curriculum", {"title": title, "source": source})
    sub.add_edge(ag, "has_curriculum", cur)
    ids = []
    for entry in lessons:
        if len(entry) >= 4:
            order, lesson_title, text_path, kind = entry[0], entry[1], entry[2], entry[3]
        else:
            order, lesson_title, text_path = entry
            kind = "code"
        lid = sub.add_node("StudyLesson", {
            "order": float(order), "title": lesson_title, "status": "queued",
            "text_path": text_path, "kind": kind,
            "decoded_epoch": 0.0, "read_decoded_epoch": 0.0, "voice_decoded_epoch": 0.0,
            "vision_decoded_epoch": 0.0,
            "flow_retired": 0.0,
            "flow_swept": 0.0, "record_written": 0.0, "shapes_learned": 0.0,
            "exercises_attempted": 0.0, "exercises_answered": 0.0,
        })
        sub.add_edge(cur, "has_lesson", lid)
        ids.append(lid)
    return {"curriculum": cur, "lessons": ids, "reused": False}


# --------------------------------------------------------------------------- #
#  PICK — a held Argmin over order among queued lessons. Never a Python
#  min()/sort() over the candidate set (the single-survivor idiom
#  `retire_duplicate_gap` established, pointed at `order` as the key).
# --------------------------------------------------------------------------- #
_PICK_NEXT_QUEUED_TERM = {
    "type": "Argmin",
    "source": {
        "type": "Filter",
        "source": {"type": "NodesOfType", "node_type": "StudyLesson"},
        "var_name": "y",
        "predicate": {
            "type": "Eq",
            "a": {"type": "Attr", "node": {"type": "Var", "name": "y"}, "key": "status"},
            "b": {"type": "Lit", "value": "queued"},
        },
    },
    "var_name": "z",
    "value": {"type": "Attr", "node": {"type": "Var", "name": "z"}, "key": "order"},
    "default": None,
}


def pick_next_queued_lesson(agent):
    """The held-Argmin pick, or `None` if no lesson is currently queued."""
    _sub, native, _ag = cdr._resolve(agent)
    try:
        picked = native.evaluate(_PICK_NEXT_QUEUED_TERM, {})
    except Exception:  # noqa: BLE001 -- honest non-pick, never a crash
        return None
    return picked


# --------------------------------------------------------------------------- #
#  ONE STUDY TICK — pick, read (the UNCHANGED code_curriculum path), record
#  the mechanical outcome facts the seed rules decide over, sweep any flow a
#  PRIOR tick's rules already marked retirable.
# --------------------------------------------------------------------------- #
def study_tick(agent, *, base_dir: Optional[str] = None) -> dict:
    """Advance the study loop by exactly one lesson (or do nothing, honestly,
    if none is queued). Returns a report dict describing what happened --
    never a decision, a factual account of this tick's mechanical work."""
    sub = getattr(agent, "s", agent)
    # Give any PENDING decision (in particular study_lesson_reopen_on_growth,
    # if something outside this tick taught a new write shape since the last
    # rule fixpoint ran) a chance to fire BEFORE picking, so a just-reopened
    # lesson is visible to the pick on the SAME tick that reopened it.
    # comprehend() IS run_rules() (see WorldAdapter.comprehend) -- cheap, no
    # NL pipeline.
    if hasattr(agent, "comprehend"):
        agent.comprehend()
    elif hasattr(agent, "tick"):
        agent.tick()
    lesson = pick_next_queued_lesson(agent)
    if lesson is None:
        swept = fr.sweep_retired_flows(agent)
        return {"picked": None, "swept": swept}

    at = sub.node(lesson)["attrs"]
    title = at.get("title")
    text_path = at.get("text_path")
    kind = at.get("kind") or "code"

    # Re-attempt bookkeeping (REOPEN, part B): reset the per-attempt working
    # flags so this cycle's flow gets its OWN retirement decision, never
    # inheriting a stale flow_retired/flow_swept/record_written from a prior
    # (now-superseded) attempt at the same lesson.
    sub.set_attr(lesson, "status", "reading")
    sub.set_attr(lesson, "flow_retired", 0.0)
    sub.set_attr(lesson, "flow_swept", 0.0)
    sub.set_attr(lesson, "record_written", 0.0)

    path = text_path if (base_dir is None or os.path.isabs(text_path)) \
        else os.path.join(base_dir, text_path)
    text = open(path, encoding="utf-8").read()

    # VOICE-EXPANSION lessons (WHOLE-CURRICULUM WAVE 3): routed by the
    # lesson's OWN `kind` graph attr (mechanical read, never a Python content
    # sniff) to voice_curriculum.learn_voice_from_lesson instead of the
    # code_curriculum path below. See _study_tick_voice.
    if kind in ("morphology", "vocabulary", "construction"):
        return _study_tick_voice(agent, sub, lesson, title, text, kind)

    # DEVELOPMENTAL VISION lessons (STAGE 2): routed by the lesson's OWN
    # `kind` graph attr, exactly like the voice branch above, to
    # vision_curriculum.learn_vision_from_lesson. See _study_tick_vision.
    if kind in vis.VISION_KINDS:
        return _study_tick_vision(agent, sub, lesson, title, text, kind)

    try:
        res = cc.learn_from_lesson(agent, text, lesson_source=title)
    except Exception as e:  # noqa: BLE001 -- ONE pathological chapter must never
        # halt a whole-book run; record the honest fact and move on (status
        # 'error' is a terminal, non-queued status, so the held-Argmin pick
        # never re-selects it and the loop proceeds to the next lesson).
        # This is I/O resilience (a crash is not a decision), not a judgement
        # about the lesson's content.
        sub.set_attr(lesson, "status", "error")
        sub.set_attr(lesson, "error_note", "%s: %s" % (type(e).__name__, e))
        sub.set_attr(lesson, "record_written", 1.0)
        swept = fr.sweep_retired_flows(agent)
        return {"picked": lesson, "title": title, "status": "error",
               "error": "%s: %s" % (type(e).__name__, e), "swept": swept}
    learned_ok = [r for r in res["learned"] if r.get("ok")]
    answered = [r for r in res["requests"]
               if "Here is the function" in str(r.get("reply", ""))]
    flow_id = (res.get("document_read") or {}).get("flow")

    # Correlate every code_write gap this lesson's OWN exercise attempts
    # filed -- a factual join (this lesson's request text == the SelfConcern's
    # content), never a decision about whether the gap matters.
    attempted_texts = {r["request"] for r in res["requests"]}
    for n in sub.nodes("SelfConcern"):
        sat = sub.node(n)["attrs"]
        if sat.get("kind") == "code_write" and sat.get("content") in attempted_texts:
            sub.add_edge(lesson, "filed_gap", n)

    _sub2, _native2, ag = cdr._resolve(agent)
    cur_write_epoch = sub.node(ag)["attrs"].get("write_codebook_epoch", 0.0) or 0.0
    cur_read_epoch = sub.node(ag)["attrs"].get("codebook_epoch", 0.0) or 0.0
    sub.set_attr(lesson, "shapes_learned", float(len(learned_ok)))
    sub.set_attr(lesson, "exercises_attempted", float(len(res["requests"])))
    sub.set_attr(lesson, "exercises_answered", float(len(answered)))
    if flow_id is not None:
        sub.set_attr(lesson, "flow_id", flow_id)
    sub.set_attr(lesson, "decoded_epoch", float(cur_write_epoch))
    # WAVE 2: stamp the READ-codebook epoch too (study_lesson_reopen_on_growth
    # now watches BOTH codebooks) -- a lesson blocked on an emitter-scope
    # residual (not just a missing WRITE shape) reopens when the READ-side
    # construction codebook grows (e.g. an emitter-widening landing on a
    # resumed graph via `reconcile_code_construction_seed`).
    sub.set_attr(lesson, "read_decoded_epoch", float(cur_read_epoch))
    # record_written LAST -- everything above is on the graph before the
    # seed rules (study_lesson_blocked_on_gap / _done_clean / _flow_retirable)
    # get a chance to see this lesson as 'extracted', so retirement can never
    # fire mid-extraction.
    sub.set_attr(lesson, "record_written", 1.0)
    sub.set_attr(lesson, "status", "extracted")

    if hasattr(agent, "comprehend"):
        agent.comprehend()
    elif hasattr(agent, "tick"):
        agent.tick()

    swept = fr.sweep_retired_flows(agent)
    return {"picked": lesson, "title": title, "shapes_learned": len(learned_ok),
           "exercises_attempted": len(res["requests"]), "exercises_answered": len(answered),
           "flow_id": flow_id, "status": sub.node(lesson)["attrs"].get("status"),
           "swept": swept}


# --------------------------------------------------------------------------- #
#  VOICE-EXPANSION (WHOLE-CURRICULUM WAVE 3) — a morphology/vocabulary/
#  construction lesson is routed to voice_curriculum.learn_voice_from_lesson
#  instead of code_curriculum.learn_from_lesson. The mechanical bookkeeping
#  is the SAME shape as the code path above (write attempted/answered/
#  decoded-epoch facts, mark extracted, let the SAME kind-agnostic seed rules
#  -- study_lesson_blocked_on_unanswered_exercise / _done_clean / _flow_
#  retirable / _reopen_on_growth -- decide blocked/done/retirable/reopen from
#  those facts): zero new lifecycle rules were needed for voice lessons, only
#  the reopen rule's Or clause grew a third arm (voice_codebook_epoch).
# --------------------------------------------------------------------------- #
def _study_tick_voice(agent, sub, lesson, title: str, text: str, kind: str) -> dict:
    try:
        world = vc.fresh_voice_world(agent)
        res = vc.learn_voice_from_lesson(agent, world, text, kind)
    except Exception as e:  # noqa: BLE001 -- ONE pathological chunk must never
        # halt the whole curriculum; record the honest fact and move on,
        # exactly the code path's own resilience precedent above.
        sub.set_attr(lesson, "status", "error")
        sub.set_attr(lesson, "error_note", "%s: %s" % (type(e).__name__, e))
        sub.set_attr(lesson, "record_written", 1.0)
        swept = fr.sweep_retired_flows(agent)
        return {"picked": lesson, "title": title, "kind": kind, "status": "error",
               "error": "%s: %s" % (type(e).__name__, e), "swept": swept}

    _sub2, _native2, ag = cdr._resolve(agent)
    cur_write_epoch = sub.node(ag)["attrs"].get("write_codebook_epoch", 0.0) or 0.0
    cur_read_epoch = sub.node(ag)["attrs"].get("codebook_epoch", 0.0) or 0.0
    cur_voice_epoch = sub.node(ag)["attrs"].get("voice_codebook_epoch", 0.0) or 0.0
    sub.set_attr(lesson, "shapes_learned", float(res.get("grounded", 0)))
    sub.set_attr(lesson, "exercises_attempted", float(res.get("attempted", 0)))
    sub.set_attr(lesson, "exercises_answered", float(res.get("answered", 0)))
    # No flow is minted for a voice lesson (no route_reading/Source pass) --
    # flow_id stays absent, so sweep_retired_flows is a harmless no-op for it
    # (see flow_retire.sweep_retired_flows: `if flow_id is not None`).
    sub.set_attr(lesson, "decoded_epoch", float(cur_write_epoch))
    sub.set_attr(lesson, "read_decoded_epoch", float(cur_read_epoch))
    sub.set_attr(lesson, "voice_decoded_epoch", float(cur_voice_epoch))
    sub.set_attr(lesson, "record_written", 1.0)
    sub.set_attr(lesson, "status", "extracted")

    if hasattr(agent, "comprehend"):
        agent.comprehend()
    elif hasattr(agent, "tick"):
        agent.tick()

    swept = fr.sweep_retired_flows(agent)
    return {"picked": lesson, "title": title, "kind": kind,
           "attempted": res.get("attempted", 0), "answered": res.get("answered", 0),
           "grounded": res.get("grounded", 0),
           "status": sub.node(lesson)["attrs"].get("status"), "swept": swept}


# --------------------------------------------------------------------------- #
#  DEVELOPMENTAL VISION (STAGE 2) — a babble/... lesson is routed to
#  vision_curriculum.learn_vision_from_lesson. The mechanical bookkeeping is the
#  SAME shape as the voice path above (write attempted/answered/decoded-epoch
#  facts, mark extracted, let the SAME kind-agnostic seed rules decide
#  blocked/done/retirable/reopen): zero new lifecycle rules were needed for
#  vision lessons either, only the reopen rule's Or clause grew a fourth arm
#  (vision_codebook_epoch).
# --------------------------------------------------------------------------- #
def _study_tick_vision(agent, sub, lesson, title: str, text: str, kind: str) -> dict:
    try:
        world = vis.fresh_vision_world(agent)
        res = vis.learn_vision_from_lesson(agent, world, text, kind)
    except Exception as e:  # noqa: BLE001 -- ONE pathological chunk must never
        # halt the whole curriculum; record the honest fact and move on, the
        # code/voice paths' own resilience precedent.
        sub.set_attr(lesson, "status", "error")
        sub.set_attr(lesson, "error_note", "%s: %s" % (type(e).__name__, e))
        sub.set_attr(lesson, "record_written", 1.0)
        swept = fr.sweep_retired_flows(agent)
        return {"picked": lesson, "title": title, "kind": kind, "status": "error",
                "error": "%s: %s" % (type(e).__name__, e), "swept": swept}

    _sub2, _native2, ag = cdr._resolve(agent)
    at = sub.node(ag)["attrs"]
    sub.set_attr(lesson, "shapes_learned", float(res.get("grounded", 0)))
    sub.set_attr(lesson, "exercises_attempted", float(res.get("attempted", 0)))
    sub.set_attr(lesson, "exercises_answered", float(res.get("answered", 0)))
    sub.set_attr(lesson, "decoded_epoch", float(at.get("write_codebook_epoch", 0.0) or 0.0))
    sub.set_attr(lesson, "read_decoded_epoch", float(at.get("codebook_epoch", 0.0) or 0.0))
    sub.set_attr(lesson, "voice_decoded_epoch", float(at.get("voice_codebook_epoch", 0.0) or 0.0))
    sub.set_attr(lesson, "vision_decoded_epoch", float(at.get("vision_codebook_epoch", 0.0) or 0.0))
    sub.set_attr(lesson, "record_written", 1.0)
    sub.set_attr(lesson, "status", "extracted")

    if hasattr(agent, "comprehend"):
        agent.comprehend()
    elif hasattr(agent, "tick"):
        agent.tick()

    swept = fr.sweep_retired_flows(agent)
    return {"picked": lesson, "title": title, "kind": kind,
            "attempted": res.get("attempted", 0), "answered": res.get("answered", 0),
            "grounded": res.get("grounded", 0), "kernels": res.get("kernels", 0),
            "status": sub.node(lesson)["attrs"].get("status"), "swept": swept}


# --------------------------------------------------------------------------- #
#  ROADMAP — Part C: aggregate open code_write/code_read gap reasons by
#  refused-feature frequency, weighted by lessons blocked. Mechanical read +
#  count of facts already on the graph -- never a new ranking criterion.
# --------------------------------------------------------------------------- #
def emitter_roadmap(agent) -> dict:
    """{reasons: [{reason, count, lessons_blocked, example_contents}], ...} --
    a frequency table over every un-resolved `code_write`/`code_read`
    SelfConcern's `content` (the honest reason string filed at gap time),
    ordered by how many DISTINCT StudyLessons a reason has blocked (a
    demand-ranked signal, verbatim reasons, no invented taxonomy)."""
    sub = getattr(agent, "s", agent)
    gaps: dict[str, dict[str, Any]] = {}
    for n in sub.nodes("SelfConcern"):
        at = sub.node(n)["attrs"]
        if at.get("kind") not in ("code_write", "code_read"):
            continue
        if at.get("status") == "resolved":
            continue
        content = at.get("content") or "(no content)"
        row = gaps.setdefault(content, {"reason": content, "kind": at.get("kind"),
                                        "count": 0, "lessons_blocked": set(),
                                        "gap_ids": []})
        row["count"] += 1
        row["gap_ids"].append(n)
    for n in sub.nodes("StudyLesson"):
        for gid in sub.neighbours(n, "filed_gap") if hasattr(sub, "neighbours") else []:
            gat = sub.node(gid)["attrs"]
            content = gat.get("content")
            if content in gaps:
                gaps[content]["lessons_blocked"].add(n)
    ranked = sorted(gaps.values(),
                    key=lambda r: (-len(r["lessons_blocked"]), -r["count"], r["reason"]))
    return {"reasons": [
        {"reason": r["reason"], "kind": r["kind"], "count": r["count"],
         "lessons_blocked": len(r["lessons_blocked"])}
        for r in ranked]}


def run_emitter_roadmap(substrate, meta_arg: Optional[str] = None) -> dict:
    """SELF-QUERY: 'what blocks your learning?' -- the `run_code_capabilities`
    pattern, pointed at the roadmap instead of the capability report. Never
    invented content, a mechanical read + first-person format."""
    rm = emitter_roadmap(substrate)
    reasons = rm["reasons"]
    if not reasons:
        note = "Nothing is blocking my learning right now -- no open code capability gaps."
    else:
        top = reasons[:5]
        parts = ["%r (blocking %d lesson(s), filed %d time(s))" %
                (r["reason"], r["lessons_blocked"], r["count"]) for r in top]
        note = ("What blocks my learning, ranked by how many lessons it has stopped: "
               + "; ".join(parts) + ".")
    return {"emitter_roadmap": True, "report": rm, "note": note}


def ensure_roadmap_dispatch() -> None:
    try:
        from domains import reflective_faculty as _rf
    except ImportError:
        return
    _rf._DISPATCH.setdefault("emitter_roadmap", run_emitter_roadmap)


ensure_roadmap_dispatch()


__all__ = ["install_curriculum", "pick_next_queued_lesson", "study_tick",
          "emitter_roadmap", "run_emitter_roadmap", "ensure_roadmap_dispatch",
          "reconcile_code_construction_seed", "reconcile_lesson_epoch_tracking"]
