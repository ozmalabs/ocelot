"""reply_fix_growth — the `reply_fix` sibling of `prog_read_growth.py`
(GROUND_CONCERN_SIX_KINDS_PREREG.md, Path 2).

MEASURED (this rung, live probe): `_promote_relations_for_concern` already
routes a `reply_fix` concern to the SAFE conversation-replay `experiment`
composer when its content names acting/seed/ablation vocabulary
(`_content_suggests_experiment`) -- that branch is untouched by this module
and must stay untouched (`tests/test_self_improvement_visibility_migrated.py`
gates it). But BOTH real `reply_fix` mint sites in this tree
(`seeds/gap_awareness.json`'s `note_upload_reply_gap` /
`note_upload_vision_gap`) file FIXED, NAMED content tags
(`upload_attachment_reply` / `upload_vision_wiring`) that never trip that
keyword set -- so in practice EVERY currently-known `reply_fix` concern
falls into `comprehend_first`, and from there into the generic
`induce_concern`/`ground_concern` machinery, which installs the SAME inert
`comprehend_describe_directive_<tag>` rule A25 measured for `prog_read`.

UNLIKE `knowledge`/`self_account`, `reply_fix`'s content is drawn from a
SMALL, FIXED, KNOWN set of named tags (like `prog_read`'s blockers) --
each tag corresponds to a real, specific wiring status, not free text.
This module is a `_BLOCKER_RUST_NEED`-shaped correspondence table
(`_REPLY_FIX_NEED`), split by tag:

  - `upload_attachment_reply` fires (`seeds/gap_awareness.json`'s own
    `_upload_vision_note`, and confirmed by
    `tests/test_attachment_reply_migrated.py::
    test_upload_honest_floor_files_reply_fix_gap`) when the honest floor
    answers an upload question -- which that SAME test shows corresponds
    to the `conversation_attachment_route`/`conversation_attachment_reply`
    seeds being absent from the agent's loaded set. THIS IS CLOSEABLE: a
    full `load_all_seeds` boot (the daemon's own boot path) already installs
    both seeds, so checking-and-loading-if-missing is a real, mechanical,
    idempotent close (the `code_write_growth.ensure_growth_rules` precedent,
    kind-swapped) -- not a fabricated fix.
  - `upload_vision_wiring` fires when a SPECIFIC already-ingested image
    attachment lacks `vision_summary` (GraphEye did not run on it at
    ingest). NOT closeable at promotion time: nothing in the concern's own
    text carries the original image bytes to re-run vision on, and no
    seed/adapter-level action can retroactively perceive a document that
    was never perceived. Honestly exhausts, named precisely -- the same
    Rust/adapter-boundary shape `prog_read_growth`'s NO-GO blockers have.
  - any OTHER `reply_fix` content (a human-authored freeform note that
    doesn't match either known tag): no correspondence exists; honestly
    exhausts with a generic reason, exactly like `prog_read_growth`'s
    `_GENERIC_REASON` fallback for an unclassified blocker.

ARCHITECTURE (CLAUDE.md): the only thing this module DECIDES is (a) whether
a content tag matches the fixed correspondence table (a lookup, not a
decision about meaning) and (b) whether the two named seeds are ALREADY
present (a graph read of `Seed` nodes) -- everything else is table lookup
and a mechanical `load_seed_manifest` call, the same status
`code_write_growth._teach_shape`'s seed-install branch already has.
"""
from __future__ import annotations

from typing import Any, Optional


# --------------------------------------------------------------------------- #
#  THE FIXED CORRESPONDENCE — per known reply_fix content tag, what closes it
#  (or why it cannot close at the seed/adapter grain). NOT exhaustive over
#  every string a human might type as a reply_fix concern's content (that is
#  free text); a tag absent here gets the honest generic fallback.
# --------------------------------------------------------------------------- #
_CLOSEABLE_SEEDS: dict[str, tuple] = {
    "upload_attachment_reply": ("conversation_attachment_route",
                                "conversation_attachment_reply"),
}

_NO_GO_REASON: dict[str, str] = {
    "upload_vision_wiring": (
        "GraphEye did not run on the specific attachment that filed this gap "
        "-- nothing in the concern's own text carries the original image "
        "bytes to re-run vision on, and no seed/adapter-level action can "
        "retroactively perceive a document that was never perceived; this is "
        "a Rust/adapter-boundary limit, not a composable fix"),
}

_GENERIC_REASON = ("no known correspondence for this reply_fix content tag -- "
                   "needs investigation into what fixed the underlying reply "
                   "path, or a human-supplied narrower report")


def _seed_already_loaded(sub, seed_id: str) -> bool:
    for n in sub.nodes("Seed"):
        if sub.node(n)["attrs"].get("id") == seed_id:
            return True
    return False


def work_on_reply_fix_gap(agent, about_text: str) -> dict[str, Any]:
    """The synchronous compose attempt `_process_reply_fix_standing` calls
    (ONLY for the `comprehend_first`-pipelined sub-case -- an `experiment`-
    pipelined reply_fix concern is left untouched, per the module docstring).
    `about_text` is the StandingConcern's own `about` (the fixed content tag
    `note_upload_reply_gap`/`note_upload_vision_gap` filed). Looks the tag up
    in the fixed correspondence table: {ok, tag, reason, ...}, never a
    fabricated close."""
    tag = (about_text or "").strip()
    if not tag:
        return {"ok": False, "tag": tag,
                "reason": "no content tag in %r -- nothing to act on" % about_text}

    if tag in _CLOSEABLE_SEEDS:
        from substrate.seed_loader import manifest_for
        sub = getattr(agent, "s", agent)
        inner = getattr(agent, "inner", None) or getattr(sub, "_inner", sub)
        ag_node = getattr(agent, "agent", None)
        needed = _CLOSEABLE_SEEDS[tag]
        already = [sid for sid in needed if _seed_already_loaded(sub, sid)]
        missing = [sid for sid in needed if sid not in already]
        if not missing:
            # Both named seeds are ALREADY loaded -- the real cause of this
            # concern is something else this correspondence table doesn't
            # cover; report that honestly instead of claiming a close.
            return {"ok": False, "tag": tag, "seeds_checked": list(needed),
                    "reason": ("the seeds this tag's known fix would load "
                              "(%s) are ALREADY present -- the underlying "
                              "reply gap has some OTHER cause, outside this "
                              "correspondence table" % ", ".join(needed))}
        loaded_now = []
        for sid in missing:
            try:
                inner.load_seed_manifest(manifest_for(sid), ag_node)
                sub.add_node("Seed", {"id": sid})
                loaded_now.append(sid)
            except Exception as e:  # noqa: BLE001 -- report, never crash the tick loop
                return {"ok": False, "tag": tag, "loaded": loaded_now,
                        "reason": "loading seed %r failed: %s: %s" % (sid, type(e).__name__, e)}
        return {"ok": True, "tag": tag, "loaded": loaded_now,
                "reason": "loaded the missing seed(s) %s that this tag's known "
                         "fix requires" % ", ".join(loaded_now)}

    if tag in _NO_GO_REASON:
        return {"ok": False, "tag": tag, "reason": _NO_GO_REASON[tag]}

    return {"ok": False, "tag": tag,
            "reason": "%s (tag=%r)" % (_GENERIC_REASON, tag)}


def pending_reply_fix_gaps(agent) -> list:
    """Mechanical reader: every held, un-retired reply_fix SelfConcern —
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
        if at.get("kind") == "reply_fix" and at.get("status") != "retired":
            out.append(at)
    return out


__all__ = ["work_on_reply_fix_gap", "pending_reply_fix_gaps"]
