"""compilation_cycle — the ACTIVE-TO-MODEL-LAYER FLYWHEEL, MADE VISIBLE.

THE THEORY (creator's Graph Law review #2): the agent has two cognitive
modes. Cheap/fast/basin-bound MODEL-LAYER cognition (a pattern-snap) is
free but confidently wrong outside its range; expensive/flexible ACTIVE
cognition (change frame, admit dimensions, re-ground) is slow but correct.
These are not two separate systems -- they are ONE LOOP: active cognition
produces structure that gets COMPILED DOWN into the cheap model layer, so
the same problem is basin-snappable (free) NEXT time, freeing active
budget for harder frames. That compile-down step already happens,
repeatedly, all over this codebase -- it was never given a name or a
throughput number. This module gives it both, MECHANICALLY, over the
agent's OWN history: it does not decide anything, it only enumerates
records the codebase already writes for an unrelated reason and indexes
them as `CompilationEvent` nodes.

THE FIVE EXISTING COMPILATIONS (every one a `active artifact -> cheap
reflex` transition, already happening, never previously counted):

  teach_hint        -- domains/teach.py's `teach()` mints a `TaughtHint`
                        (or any taught type): a REASONED conclusion (an
                        adoption verdict, a teacher answer, a self-derived
                        lesson) becomes a cheap LOOKED-UP fact a future
                        boot just re-loads, no re-reasoning.
  adoption          -- domains.reflective_faculty.perform_adoptions mints
                        an `Adoption` node: a JUDGED experimental variant
                        (won a real dispatched-and-scored trial) is folded
                        INTO the parent rule set as a resident rule --
                        active experimentation compiled into a standing
                        reflex.
  composer_authored -- every graph-resident composer (control / grouping /
                        decision / grounding_guard / escalation_gate / ...)
                        mints a `ComposeRequest` and flips its `composed`
                        attr 0.0 -> 1.0 once its meta-rule has authored the
                        rule(s) the concern needed -- an ACTIVE concern
                        (induce_concern's residual) becomes an INSTALLED
                        graph meta-rule, callable for free from then on.
                        This is the composer-to-graph migration ITSELF,
                        one instance per concern actually composed.
  rung4_install     -- domains.proposal_install mints an `Install` record
                        (`ok=True`) when a sandbox-proven `ExtensionProposal`
                        is approved into the runtime: an authored spec
                        becomes a RUNTIME PRIMITIVE, the most expensive
                        compile (requires a restart) and the least
                        frequent.
  program_learned   -- domains.reflective_faculty.teach_program (called by
                        both `dynamic_extend`/`learn_term_for_concern`'s
                        rung-3 self-extension AND `ground_concern`'s
                        generate-from-residual path) mints a `Program`
                        node: an authored Term-tree becomes a HELD,
                        re-runnable program a fresh boot re-loads and runs
                        without recomposing it.

This module does not run, judge, or trigger any of the above -- it reads
what already happened. `compilation_events` mints one `CompilationEvent`
node per source record (idempotent: keyed on `(kind, from)`, re-running it
over an unchanged graph mints nothing new -- the same has_node/key-guard
idiom domains/grounding_reach.py's `_ground` and domains/self_model.py's
`ensure_rule_provenance` use). `compilation_throughput` is a pure read over
the minted index. Mechanical host I/O over the agent's OWN history; no
agent decision lives here.
"""
from __future__ import annotations

import time
from typing import Any, Optional

_EVENT_TYPE = "CompilationEvent"

# kind -> (source node type, human label) -- documents the five channels above.
_KINDS = ("teach_hint", "adoption", "composer_authored", "rung4_install", "program_learned")


def _resolve(agent):
    sub = getattr(agent, "s", agent)
    native = getattr(agent, "inner", None)
    if native is None:
        native = getattr(sub, "_inner", sub)
    return sub, native


def _existing_keys(sub) -> set:
    keys = set()
    for e in sub.nodes(_EVENT_TYPE):
        k = sub.node(e)["attrs"].get("key")
        if k is not None:
            keys.add(k)
    return keys


def _mint(sub, seen: set, minted: list, *, kind: str, from_: Any, to_: Any, ts: float, **extra) -> None:
    key = f"{kind}:{from_}"
    if key in seen:
        return
    attrs = {"kind": kind, "from": None if from_ is None else str(from_),
              "to": None if to_ is None else str(to_), "ts": float(ts), "key": key}
    attrs.update(extra)
    node = sub.add_node(_EVENT_TYPE, attrs)
    seen.add(key)
    minted.append({"event": node, **attrs})


# ---------------------------------------------------------------------------
# compilation_events -- mechanically enumerate the five existing compile-down
# channels and mint a CompilationEvent per source record not yet indexed.
# ---------------------------------------------------------------------------
def compilation_events(agent) -> list:
    """Scan the agent's OWN history for the five existing active->cheap
    compilations (see module docstring) and mint one `CompilationEvent` per
    record not already indexed. Idempotent -- a re-run over an unchanged
    graph mints nothing (returns []). Returns the list of newly-minted
    events this call (each `{event, kind, from, to, ts, ...}`)."""
    sub, native = _resolve(agent)
    seen = _existing_keys(sub)
    minted: list = []
    now = time.time()

    # 1) teach() -> TaughtHint: a reasoned conclusion becomes a cheap fact.
    for n in sub.nodes("TaughtHint"):
        at = sub.node(n)["attrs"]
        _mint(sub, seen, minted, kind="teach_hint", from_=at.get("topic", n), to_=n, ts=now,
              node=str(n))

    # 2) perform_adoptions -> Adoption: a judged variant becomes a resident rule.
    for n in sub.nodes("Adoption"):
        at = sub.node(n)["attrs"]
        _mint(sub, seen, minted, kind="adoption", from_=at.get("experiment_id"), to_=at.get("rule_added"),
              ts=float(at.get("tick") or now), node=str(n))

    # 3) composer-to-graph: ComposeRequest{composed==1.0} -- an active concern
    #    (induce_concern's residual) becomes an installed graph meta-rule.
    for n in sub.nodes("ComposeRequest"):
        at = sub.node(n)["attrs"]
        if at.get("composed") != 1.0:
            continue
        _mint(sub, seen, minted, kind="composer_authored", from_=n, to_=at.get("tag"), ts=now,
              node=str(n))

    # 4) rung-4 install -> Install{ok==True}: an authored spec becomes a runtime primitive.
    for n in sub.nodes("Install"):
        at = sub.node(n)["attrs"]
        if not at.get("ok"):
            continue
        _mint(sub, seen, minted, kind="rung4_install", from_=at.get("proposal"), to_=n,
              ts=float(at.get("ts") or now), node=str(n))

    # 5) learn_term_for_concern / dynamic_extend -> Program: an authored Term
    #    becomes a held, re-runnable program.
    for n in sub.nodes("Program"):
        at = sub.node(n)["attrs"]
        _mint(sub, seen, minted, kind="program_learned", from_=at.get("name", n), to_=n, ts=now,
              node=str(n))

    return minted


# ---------------------------------------------------------------------------
# compilation_throughput -- pure read over the minted CompilationEvent index.
# ---------------------------------------------------------------------------
def compilation_throughput(agent, *, window: Optional[float] = None) -> dict:
    """How fast active results become cheap reflexes. Reads the
    `CompilationEvent` index (call `compilation_events` first to bring it
    up to date -- this function never mints). `window` (seconds), if given,
    restricts the count to events whose `ts` falls within `window` seconds
    of the newest event indexed. Returns {total, by_kind, rate, window}
    where `rate` is events/second across the indexed span (None if fewer
    than two distinct timestamps)."""
    sub, native = _resolve(agent)
    events = list(sub.nodes(_EVENT_TYPE))
    by_kind: dict = {k: 0 for k in _KINDS}
    tss: list = []
    records = []
    for e in events:
        at = sub.node(e)["attrs"]
        records.append(at)
        ts = at.get("ts")
        if ts is not None:
            tss.append(float(ts))
    newest = max(tss) if tss else None
    total = 0
    for at in records:
        ts = at.get("ts")
        if window is not None and newest is not None and ts is not None and (newest - float(ts)) > window:
            continue
        kind = at.get("kind", "unknown")
        by_kind[kind] = by_kind.get(kind, 0) + 1
        total += 1
    span = (max(tss) - min(tss)) if len(tss) >= 2 else None
    rate = (total / span) if span and span > 0 else None
    return {"total": total, "by_kind": by_kind, "rate": rate, "window": window}


__all__ = ["compilation_events", "compilation_throughput"]
