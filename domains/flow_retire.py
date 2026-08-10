"""flow_retire — WHOLE-CURRICULUM WAVE 1, PART A: mechanical GC for retired
reading flows.

The dynamic-thresholds wave (401ea41a5d) named the residual this closes: a
completed reading flow's WORKING nodes (SentenceParse / ClauseParse /
AnalysisStage / Goal / SmEntity / SmEvent / CoherencePair / CausalLink /
EnablingChain / the Source itself / every other node the Wave-1A `flow`/
`unit` stamp marks as belonging to one read -- ~23+ nodes per sentence, see
`domains/reading_drive.py`'s `_mint_sentence_parses` and its many
`attrs["flow"] = flow` / `unit=flow` sibling call sites) accumulate
MONOTONICALLY: a 19-chapter book is thousands of sentences on ONE substrate,
never retired.

The split (CLAUDE.md): a SEED RULE (`seeds/curriculum_study.json`'s
`study_flow_retirable`) DECIDES a flow is retirable -- once a StudyLesson's
extraction PRODUCTS (shapes taught, gaps filed, the per-lesson outcome
record) are on the graph and the lesson has settled to a terminal status
(`done`/`blocked`) -- and stamps `flow_retired=1` on the Lesson. THIS module
is the mechanical executor: it reads that decision and deletes the flow-
scoped WORKING nodes, never deciding retirability itself.

Retirement is keyed on the Wave-1A `flow`/`unit` stamp (the plain node-id
value of the flow's own Source, propagated onto every scratch node minted
during that read -- see `reading_drive.py:_ingest_source`/
`_mint_sentence_parses`). A node is swept iff (a) its OWN attr `flow` or
`unit` equals the retiring flow's id, AND (b) its node TYPE is not in
`NEVER_RETIRE` -- a belt-and-braces allowlist of the durable product types
this wave's own products land as, so a bug that ever stamped `flow`/`unit`
onto a product node (none do today) still cannot delete it.

Products PERSIST (HeldAnswer, taught ShapeSignatures, SelfConcern gaps, the
Curriculum/StudyLesson nodes themselves, the lesson outcome record) --
retirement never touches them, by type AND by construction (none of the
faculties that mint them stamp a flow/unit attr).
"""
from __future__ import annotations

from typing import Any

# Durable node types a flow retirement sweep must NEVER delete, even if one
# happened to carry a `flow`/`unit` attr matching the retiring id (none do
# today -- this is the explicit guard against that ever silently changing).
NEVER_RETIRE = frozenset({
    "Agent", "Curriculum", "StudyLesson", "SelfConcern", "StandingConcern",
    "HeldAnswer", "ShapeSignature", "Seed", "Microtheory", "Concept", "Rule",
    "TaughtHint", "FaithLesson", "Frame", "Reflex", "CapabilityAxis",
    "DimensionGenerator", "LatentDimension",
})


def _flow_scoped_victims(sub, flow_id: Any, keep: set) -> list:
    """Every node (any type) whose OWN `flow` or `unit` attr equals
    `flow_id`, excluding NEVER_RETIRE types and anything in `keep` (the
    Lesson node itself, so the sweep never deletes the record it is reading
    off of). Pure query -- no decision beyond the fixed allowlist."""
    victims = []
    for nid in list(sub.nodes(None)):
        if nid in keep:
            continue
        rec = sub.node(nid)
        if rec.get("type") in NEVER_RETIRE:
            continue
        at = rec.get("attrs", {})
        if at.get("flow") == flow_id or at.get("unit") == flow_id:
            victims.append(nid)
    return victims


def sweep_retired_flows(agent) -> dict:
    """Mechanical GC pass: every `StudyLesson` marked `flow_retired==1` and
    not yet `flow_swept==1` has its flow's working nodes deleted, then is
    marked `flow_swept=1` (idempotent -- a swept lesson is skipped on the
    next call). A LIVE (not-yet-retired) flow is never touched -- only a
    lesson the seed rule has already decided is retirable reaches here, so
    a flow still being read (mid-extraction) is always safe.

    Returns {swept: [{lesson, flow_id, deleted}], total_deleted}."""
    sub = getattr(agent, "s", agent)
    inner = getattr(agent, "inner", None)
    if inner is None:
        inner = getattr(sub, "_inner", sub)
    out = []
    total = 0
    for n in list(sub.nodes("StudyLesson")):
        at = sub.node(n)["attrs"]
        if at.get("flow_retired") != 1 or at.get("flow_swept") == 1:
            continue
        flow_id = at.get("flow_id")
        deleted = 0
        if flow_id is not None:
            for victim in _flow_scoped_victims(sub, flow_id, keep={n}):
                inner.remove_node(victim)
                deleted += 1
        sub.set_attr(n, "flow_swept", 1)
        out.append({"lesson": n, "flow_id": flow_id, "deleted": deleted})
        total += deleted
    return {"swept": out, "total_deleted": total}


__all__ = ["sweep_retired_flows", "NEVER_RETIRE"]
