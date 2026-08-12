"""self_account_growth — the `self_account` sibling of `prog_read_growth.py`
(GROUND_CONCERN_SIX_KINDS_PREREG.md, Path 2).

MEASURED (this rung, live probe): a promoted `self_account` `SelfConcern`
falls through `_promote_relations_for_concern`'s `comprehend_first` default
into the generic `induce_concern`/`ground_concern` machinery, which installs
the SAME inert `comprehend_describe_directive_<tag>` rule A25 measured for
`prog_read`. WORSE than `reply_fix`/`knowledge`: `self_account` is not even
in the conversation-experiment kind list, so on the rare occasion its
content DOES trip `_content_suggests_experiment` (e.g. a self-question whose
stripped topic happens to be "rule" or "seed"), it falls into the ARC
`vary`/`gradient` self-improvement bundle instead — a mismatch just as bad
as the comprehension composer's dead rule (an ARC episode has nothing to do
with "how do you reason"). Neither existing pipeline value is safe for this
kind, so the routing fix below is UNCONDITIONAL (mirrors `code_write`/
`prog_read`'s own unconditional interception exactly).

EXISTING MECHANISM this module routes to, per CLAUDE.md's "self_processes"
section: `SelfProcess{process, aliases, account, source}` nodes the agent
HOLDS + `domains/self_model.py::find_self_process`/`run_self_process` --
"only faculties with NO held account still file a self_account gap." A
`self_account` SelfConcern's `content` is `self_account_topic`, the SAME
possessive-stripped noun/phrase `find_self_process` matches tokens of. This
module re-checks that lookup at promotion time: a `SelfProcess` account may
have been taught for this faculty SINCE the gap was filed (CLAUDE.md's own
changelog names several faculties -- collapse, imagining, attending --
accounted AFTER their gaps were first noticed).

NO-GO, precisely, on ever AUTO-AUTHORING a new `SelfProcess` account: an
account's `note`/`account` prose must describe REAL architecture (the
collapse loop, the sd loop, the adapter's ingest path) -- `run_self_process`'s
own docstring is explicit that a fabricated self-account is exactly what
must never happen. Synthesizing one from a seed/adapter-grain function would
violate that directly. So this module's job, like `prog_read_growth`'s, is
to STOP the wrong generic composer and report an honest, specific outcome:
either a genuinely-held account now exists (recognise it, real progress) or
it does not (name precisely which faculty has no held account, never invent
one).
"""
from __future__ import annotations

from typing import Any

from domains import self_model as sm


def work_on_self_account_gap(agent, about_text: str) -> dict[str, Any]:
    """The synchronous compose attempt `_process_self_account_standing`
    calls. `about_text` is the StandingConcern's own `about` (copied
    verbatim from the original SelfConcern's `content` -- the possessive-
    stripped faculty noun/phrase `note_self_account_gap` filed, e.g.
    "reasoning", "collapse"). Re-checks `find_self_process` (the SAME
    lookup `comprehend_text`'s manner branch uses) against the CURRENT held
    `SelfProcess` set: {ok, topic, reason, ...}, never fabricating an
    account."""
    topic = (about_text or "").strip()
    if not topic:
        return {"ok": False, "topic": topic,
                "reason": "no faculty named in %r -- nothing to check" % about_text}

    sub = getattr(agent, "s", agent)
    tokens = [w for w in topic.replace(",", " ").split() if w]
    found = sm.find_self_process(sub, tokens) if tokens else None
    if found is not None:
        return {"ok": True, "topic": topic, "process": found,
                "reason": "a held SelfProcess account for %r now exists "
                         "(process=%r) -- the gap is answerable" % (topic, found)}

    return {"ok": False, "topic": topic,
            "reason": ("no held SelfProcess account exists for %r -- closing this "
                      "honestly requires a SelfProcess{process, account} node "
                      "describing the REAL mechanism (grounded in the actual "
                      "architecture, e.g. the collapse loop / the sd decode loop / "
                      "the adapter's ingest path), never a fabricated one -- "
                      "authoring one is an architecture-documentation task, not a "
                      "seed/adapter-level compose") % topic}


def pending_self_account_gaps(agent) -> list:
    """Mechanical reader: every held, un-retired self_account SelfConcern —
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
        if at.get("kind") == "self_account" and at.get("status") != "retired":
            out.append(at)
    return out


__all__ = ["work_on_self_account_gap", "pending_self_account_gaps"]
