"""knowledge_growth — the `knowledge` sibling of `prog_read_growth.py`
(GROUND_CONCERN_SIX_KINDS_PREREG.md, Path 2).

MEASURED (this rung, live probe): a promoted `knowledge` `SelfConcern` falls
through `_promote_relations_for_concern`'s `comprehend_first` default (its
content is a bare topic word, essentially never matching
`_content_suggests_experiment`'s acting/seed/ablation keyword set) into the
generic `induce_concern`/`ground_concern` capability-axis machinery, which
installs the SAME inert `comprehend_describe_directive_<tag>` rule A25
measured for `prog_read` and reports `{"grounded": true}` — the identical
false-success-plus-dead-rule bug, for a structurally different concern kind.

UNLIKE `prog_read`, this kind's gap already has a WORKING resolution
mechanism elsewhere in this tree, documented in `CLAUDE.md`'s "Knowledge
gaps self-heal" section: `WorldAdapter.ground_unknowns` (the self-teacher
chain — dictionary/wiki, memoised under `taught_<form>`) plus
`WorldAdapter.answer_about` (the fact/taught-capability reader). This
module does NOT invent a new grounding mechanism — it re-invokes the SAME
one at promotion time, honestly, because a `knowledge` SelfConcern is only
ever filed (`seeds/gap_awareness.json::note_unresolved_topic_gap`) AFTER
that exact self-heal already ran once, synchronously, at ingest time, and
failed. Conditions can change between ingest and a human promoting the gap
(a related fact taught in the interim; the self-teacher's backing source
answering differently on a second attempt) — re-attempting is genuine work,
not theatre, and EITHER real success or a specific re-attempt failure is
recorded, never a fabricated one.

ARCHITECTURE (CLAUDE.md): the only thing this module DECIDES is whether
`ground_unknowns`/`answer_about`'s own return values indicate success — a
boolean read of an already-computed result, never a decision about MEANING.
Grounding a word's meaning is the teacher's job (`ground_unknowns`'s own
docstring: "the teacher decides meaning; the adapter is the per-word I/O
loop"), not this module's.
"""
from __future__ import annotations

from typing import Any


def work_on_knowledge_gap(agent, about_text: str) -> dict[str, Any]:
    """The synchronous compose attempt `_process_knowledge_standing` calls.
    `about_text` is the StandingConcern's own `about` (copied verbatim from
    the original SelfConcern's `content` at promotion time — the bare topic
    word/phrase `note_unresolved_topic_gap` filed). Re-attempts the EXISTING
    self-heal chain (`answer_about` -> miss -> `ground_unknowns` -> re-
    `answer_about`, the exact `world_adapter._answer_topic_reply` sequence)
    and reports the real outcome. Never fabricates an answer: {ok, topic,
    reason, ...}."""
    topic = (about_text or "").strip()
    if not topic:
        return {"ok": False, "topic": topic,
                "reason": "no topic named in %r -- nothing to ground" % about_text}

    answer_about = getattr(agent, "answer_about", None)
    if answer_about is None:
        return {"ok": False, "topic": topic,
                "reason": "agent carries no answer_about reader -- cannot check "
                         "or re-check grounding for %r" % topic}

    existing = answer_about(topic)
    if existing is not None:
        # Already grounded (a race, or grounded via some OTHER path since
        # the gap was filed) -- genuine progress, report it honestly rather
        # than re-run the teacher for no reason.
        return {"ok": True, "topic": topic, "answer": existing,
                "reason": "already grounded (found via answer_about, no re-teach needed)"}

    ground = getattr(agent, "ground_unknowns", None)
    if ground is None:
        return {"ok": False, "topic": topic,
                "reason": "agent carries no self-teacher (ground_unknowns unavailable) "
                         "-- cannot re-attempt grounding for %r" % topic}

    learnt = ground(topic)
    if not learnt:
        return {"ok": False, "topic": topic,
                "reason": "re-attempted the self-teacher chain (ground_unknowns) on "
                         "%r; the teacher still returned no payload -- still "
                         "ungrounded" % topic}

    ans = answer_about(topic)
    if ans is None:
        # The teacher grounded SOME word(s) in the topic phrase (ground_unknowns
        # grounds per-word), but answer_about's own subject-match still finds
        # no fact for the topic AS A WHOLE -- name this precisely rather than
        # claim success.
        return {"ok": False, "topic": topic, "learnt": learnt,
                "reason": "self-teacher grounded %r but answer_about still finds "
                         "no fact for the topic %r as a whole" % (learnt, topic)}

    return {"ok": True, "topic": topic, "learnt": learnt, "answer": ans,
            "reason": "re-attempting the self-teacher chain grounded %r" % learnt}


def pending_knowledge_gaps(agent) -> list:
    """Mechanical reader: every held, un-retired knowledge SelfConcern —
    the `pending_prog_read_gaps` precedent, kind-swapped."""
    sub = getattr(agent, "s", agent)
    inner = getattr(agent, "inner", None) or getattr(sub, "_inner", sub)
    ag_node = None
    for n in sub.nodes("Agent"):
        if not sub.node(n)["attrs"].get("is_class"):
            ag_node = n
            break
    if ag_node is None:
        return []
    out = []
    for sc in inner.neighbours(ag_node, "has_self_concern"):
        if not inner.has_node(sc):
            continue
        at = sub.node(sc)["attrs"]
        if at.get("kind") == "knowledge" and at.get("status") != "retired":
            out.append(at)
    return out


__all__ = ["work_on_knowledge_gap", "pending_knowledge_gaps"]
