"""prog_read_growth — the `prog_read` sibling of `code_write_growth.py`
(ARC6 amendment A25, PROGRAM_SYNTHESIS_ARC6_PREREG.md).

`code_write_growth` supplies the two sanctioned closes for a `code_write`
`SelfConcern` (teach-by-example, compose-from-predication) — both widen
`seeds/code_write_constructions.json` FROM ALREADY-HELD DSL vocabulary
(the arithmetic `Times`/`Plus` Terms the engine already evaluates). This
module is the `prog_read` sibling: `_process_prog_read_standing`
(`scripts/jabberwock_daemon.py`) routes a promoted `prog_read`
`StandingConcern` here DIRECTLY, the same way `code_write` is routed to
`work_on_code_write_gap` — instead of falling through to the generic
`induce_concern`/`ground_concern` capability-axis composer, which was
MEASURED (A25, live) to mint an inert, misleadingly-named rule for a
`prog_read` concern (`comprehend_describe_directive_<tag>`, matched on a
literal Mention text `'describe'` about a `Scene` node — structurally
unrelated to extending a program-reading frame, and never recorded as
having failed).

WHY THIS MODULE HONESTLY EXHAUSTS ON EVERY BLOCKER TODAY (not a stub —
a measured, reasoned boundary, A25 §"design investigation"): a `prog_read`
blocker names an AST construct the emitter's fixed correspondence table
(`domains/prog_ir_emit.py`) has NO case for (`Lambda`, `KwargsCall`,
`StarArgsCall`/`StarArgsParam`, `Match`, `ClassDef`, `With`, `Yield`,
`Await`, `TryFinally`/`TryElse`/`MultiExcept`/`TypedExcept`,
`ComprehensionSet`/`ComprehensionDict`, `NamedExpr`, `DictUnpack`,
`StarElement`, `RecvMethod:<mutating method>`, ...). Unlike `code_write`'s
predication family (an ENGLISH request maps onto Terms the engine ALREADY
evaluates — `Times`/`Plus`), every one of these needs either a genuinely
NEW Rust `Term` variant (a `Lambda`/closure value with a captured
environment; a generator/`Yield` suspension model; pattern-matching
dispatch) or a new lvalue write-back path the engine does not have
(mutating recv-form calls) — confirmed by grep: zero `Lambda` (or any of
the above) hits anywhere in `runners/dsl/src/*.rs`. There is no
"compose-from-held-vocabulary" move available for READING an unsupported
construct — reading is decoding an existing syntax into IR the engine can
run, not composing a fresh expression from held primitives. This is
Rust-engine-level work (out of scope for this amendment — the same
boundary `compose_write_shape_from_predication` documents for `code_write`
requests outside its own small family, except here the family is empty
until new engine primitives land).

So `work_on_prog_read_gap` does the one thing that IS honestly available
at the seed/adapter grain today: it (a) STOPS the actively-wrong generic
composer from firing at all (the routing fix — `_process_prog_read_standing`
never falls through to `induce_concern`/`ground_concern`), and (b) records
a MECHANICAL, HONEST outcome fact (never a decision) naming, per blocker,
the Rust primitive an eventual close would need — the
`note_prog_read_composition_exhausted` rule (`seeds/prog_read_gap.json`,
the `note_code_write_composition_exhausted` precedent verbatim) reads that
fact and marks the StandingConcern `experiments_exhausted` — a human asking
"what happened to that gap" sees an honest, specific answer instead of the
prior silent, wrong "grounded: true".

ARCHITECTURE (CLAUDE.md): `_BLOCKER_RUST_NEED` below is a FIXED
correspondence table (the same status `prog_ir_emit.py`'s own
`NATIVE_ORACLES`/`_BINOP_AB` tables have — "the correspondence, the only
knowledge in this module", never a decision about meaning) naming what a
future close would require; looking a blocker name up in it is a lookup,
not a decision. The one thing this module DOES decide by construction
(never dynamically) is "no blocker in the population this amendment
measured has a seed-level close" — stated as fact, not computed.
"""
from __future__ import annotations

from typing import Any, Optional


# --------------------------------------------------------------------------- #
#  THE FIXED CORRESPONDENCE — what a future close of each NAMED blocker would
#  require. Not exhaustive over every blocker `prog_ir_emit.py` can emit
#  (that table is large and growing); a blocker absent here gets the honest
#  generic fallback message. Widening this table is safe (additive, never
#  changes behaviour for a blocker already covered) but each new entry is
#  ITSELF still an exhaustion reason until the named Rust primitive lands —
#  this table documents the boundary, it does not cross it.
# --------------------------------------------------------------------------- #
_BLOCKER_RUST_NEED: dict[str, str] = {
    "Lambda": "a closure Term carrying a captured environment (function "
              "VALUES, not just top-level DefFn, are not representable today)",
    "KwargsCall": "a keyword-argument binding Term (ProgCallExtern has no "
                 "named-argument slot)",
    "StarArgsCall": "a variadic-argument spread Term at the call site",
    "StarArgsParam": "a variadic-parameter binding Term at DefFnParam grain",
    "Yield": "a generator/suspension evaluation model (ProgEval has no "
            "resumable-frame representation)",
    "Await": "an async-suspension evaluation model, same gap as Yield",
    "Match": "a structural pattern-matching dispatch Term",
    "ClassDef": "a class/instance object model (no OO value representation exists)",
    "With": "a context-manager enter/exit protocol Term",
    "TryFinally": "a finally-clause guarantee on the existing TryOr Term",
    "TryElse": "a try-else (no-exception-taken) branch on the existing TryOr Term",
    "MultiExcept": "a multi-clause exception dispatch on the existing TryOr Term",
    "TypedExcept": "exception-type-selective catch (TryOr catches ANY trap today)",
    "ComprehensionSet": "a Set-typed comprehension result (ComprehensionList "
                        "only ever builds a List)",
    "ComprehensionDict": "a Dict-typed (key, value) comprehension result",
    "NamedExpr": "a walrus-assignment-as-expression Term",
    "DictUnpack": "a dict **-spread literal Term",
    "StarElement": "a *-spread Term inside a container literal",
    "Assert": "an assert-as-statement Term (distinct from a plain trap)",
    "Delete": "a del-statement Term (no binding-removal effect exists)",
    "GlobalNonlocal": "a non-local binding-scope Term",
    "Decorator": "a decorator-application Term wrapping DefFn",
    "IsinstanceMultiType": "an OR-of-type-names argument convention for the "
                           "isinstance native oracle",
    "IsinstanceComplexType": "a non-literal (dotted/variable) type-argument "
                             "resolution for the isinstance native oracle",
}

_GENERIC_REASON = ("no known engine correspondence for this construct — "
                   "needs investigation into what Rust Term/IR-variant "
                   "coverage it would require")


def _blocker_reason(blocker: str) -> str:
    if blocker.startswith("RecvMethod:"):
        return ("a mutating-call lvalue write-back path (the engine "
               "structurally refuses %r — no write-back path for a pure "
               "ProgCallExtern)" % blocker)
    if blocker.startswith("OpExt:"):
        return "a DSL Term for the %r operator (not yet in the widened set)" % blocker
    if blocker.startswith("GraphRepr:"):
        return "a graph-mode reader limitation, distinct from the AST reader (%r)" % blocker
    if blocker.startswith("Other:"):
        return "an unclassified emission residual (%r) — needs its own naming pass" % blocker
    return _BLOCKER_RUST_NEED.get(blocker, _GENERIC_REASON)


def _parse_prog_read_content(about: str) -> tuple[Optional[str], list]:
    """Mechanical text-prep: reverse `note_prog_read_gap`'s own StringConcat
    ('<frame> read blocked: <comma,joined,blockers>') back into (frame,
    blockers). A fixed split, never a decision about MEANING — the same
    status `code_write_growth._stem` already has."""
    marker = " read blocked: "
    if marker not in about:
        return None, []
    frame, _, rest = about.partition(marker)
    blockers = [b for b in rest.split(",") if b]
    return (frame or None), blockers


def work_on_prog_read_gap(agent, about_text: str) -> dict[str, Any]:
    """The synchronous compose attempt `_process_prog_read_standing` calls.
    Parses the StandingConcern's own `about` text (the SelfConcern's content,
    copied verbatim at promotion time) back into (frame, blockers), then
    checks each blocker against `_BLOCKER_RUST_NEED`/the classified prefixes
    above — NOT to find a close (none exists yet, by measured construction,
    module docstring), but to report EXACTLY what a future close needs,
    named per blocker, instead of a flat "unsupported". Always honestly
    exhausts today: {ok: False, reason: ..., frame, blockers, needs}."""
    frame, blockers = _parse_prog_read_content(about_text)
    if not blockers:
        return {"ok": False, "frame": frame, "blockers": [],
               "reason": "no blocker named in %r — nothing to act on" % about_text}
    needs = {b: _blocker_reason(b) for b in blockers}
    named = "; ".join("%s needs %s" % (b, needs[b]) for b in blockers)
    return {
        "ok": False, "frame": frame, "blockers": blockers, "needs": needs,
        "reason": ("extending the %s reading frame past %s is Rust-engine-level "
                  "work, not a seed/adapter-level close: %s"
                  % (frame or "<unknown>", ",".join(blockers), named)),
    }


def pending_prog_read_gaps(agent) -> list:
    """Mechanical reader: every held, un-retired prog_read SelfConcern —
    the `pending_code_write_gaps` precedent, kind-swapped."""
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
        if at.get("kind") == "prog_read" and at.get("status") != "retired":
            out.append(at)
    return out


__all__ = ["work_on_prog_read_gap", "pending_prog_read_gaps"]
