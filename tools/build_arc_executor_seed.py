#!/usr/bin/env python3
"""EMIT `seeds/arc_executor.json` — AG-5, THE EXECUTOR AND THE STATUS LIFECYCLE.

`tools/*` are one-off AUTHORING scripts that EMIT seed manifests (CLAUDE.md:
"deletable; not agent runtime").  Nothing here runs at agent time.

WHY A BUILDER, AND WHY IT IMPORTS THE ARC-GOAL BUILDER.  Every Term idiom this
rung needs already exists one rung down — `MEASURE_EPOCH()`, the `ONE_OF`
serializer, the `HUB` match, the null-coalescing `ITE`.  Re-typing them is
exactly how a misspelled field name becomes a silent no-op (an unknown key on
an `And` makes it an EMPTY conjunction that returns True).  So they are
IMPORTED from `tools/build_arc_goals_seed.py` rather than copied, and if that
builder's idioms change this seed goes out of date LOUDLY.

WHAT THIS SEED IS.  Four rules and a two-node route table.

  ax_dispatch      THE COLLAPSE→ACTION SEAM.  `route_pick`'s own shape
                   (`seeds/research_agenda_dispatch.json`): an Argmin-by-
                   priority over the ExecClass cues whose `name` Eq the
                   SELECTED goal's `kind`.  A goal whose kind has no cue mints
                   NOTHING — the confinement is the empty Argmin, not a
                   promise.  The winner is bound by `ag_select`'s OWN stamp
                   (`arc_sel_agid`), so the executor can never disagree with
                   the collapse it is acting on, and the pool predicate is
                   re-asserted on the bound goal so a stale stamp cannot
                   dispatch a goal that has left the pool.
  ax_retired_epoch STAMPS the epoch a goal reached its terminal status.
                   `ag_remeasure_retire` (arc_goals, byte-frozen) writes the
                   status; this writes WHEN, because the anti-oscillation latch
                   is defined in epochs and the epoch had no producer until
                   this rung.
  ax_rearm         THE ANTI-OSCILLATION LATCH — the arc-goal design's §8.2
                   second guard, which that rung named as NOT implemented.  A
                   terminal goal re-enters the pool ONLY when BOTH (a) its
                   source residual is genuinely stale again AND (b) the
                   MEASUREMENT EPOCH HAS ADVANCED past its retirement.  Either
                   half alone is not enough, and that is the two-position
                   property the gate asserts in both directions.
  ax_close         Closes the order once its goal is terminal, so "an execution
                   that completed" is a countable graph fact rather than a
                   read of the adapter's return value.
  ax_impotent      A13/WH4(c) -- TERMINATE HONESTLY.  `ag_ask` fires on a TIE;
                   this fires on the case it cannot see, a non-empty pool in
                   which NOTHING is routable.  Quantifies over the WHOLE POOL
                   (`Not(Exists(POOL(), g, dispatchable(g)))`), never the
                   winner alone -- reuses `_routable`/`ROUTE` VERBATIM, the
                   same predicate `ax_dispatch` itself gates on.  Mints
                   `AgendaVerdict{kind:'impotent'}` once per distinct POOL
                   SIGNATURE (an ordered agid list, JSON-encoded via `MapList`
                   + `ToJsonString` -- comparable by Eq, no sort needed) and
                   lapses it through the EXISTING, UNMODIFIED
                   `gr_condition_lapse` (`seeds/goal_residuals.json`) via a
                   `fact_equals(arc_measure_epoch)` condition -- the SAME
                   "expire at the next measurement" idiom the testimony reply
                   already ships.  No new DSL Term, no new lapse mechanism.
  ax_world_probe_epoch  A18 -- a SECOND, narrower epoch producer that never
                   runs anything; see its own docstring below.
  ax_fallback_silent /
  ax_fallback_cleared   A19 -- THE SILENT ORDER-N FALLBACK, MADE OBSERVABLE.
                   WIRE_HANDS SS8.1 named it and did not build it: `SEL_AGID`'s
                   fallback to order-1 when `mg_sel_agid` is absent is silent
                   BY DESIGN (SS1.2 -- a hard dependency on `arc_magnitude`
                   would change every EX1-EX6 scene's boot), and nothing on
                   the graph said so except a per-order breadcrumb
                   (`selected_by`).  THE FALLBACK ITSELF IS UNTOUCHED -- these
                   two rules add a STANDING, QUERYABLE fact and read
                   `_order_n_is_not_live()` VERBATIM, the same Term `SEL_AGID`
                   itself branches on, so they can never disagree with
                   `ax_dispatch` about which collapse is live.
                   `ax_fallback_silent` mints `AgendaVerdict{kind:
                   'order_n_fallback', active:1.0}` (mint-once while active,
                   `ax_impotent`'s own idiom) the instant order-N is not
                   producing a stamp; `ax_fallback_cleared` flips `active` to
                   `0.0` the instant it is -- a DIRECT REVERSIBLE PAIR, the
                   same SHAPE as `gr_condition_lapse`/`gr_condition_hold`, but
                   keyed on the live Term rather than an epoch, because
                   `arc_magnitude` can be loaded onto an already-running
                   graph with no epoch bump anywhere in the scene (WH3 vs
                   WH1's own boots differ by exactly this).  No new DSL Term,
                   no new node type, no new edge type, no new adapter
                   function -- `agenda_verdicts(sub, "order_n_fallback")` is
                   already generic.
  ax_ask_divergence_active /
  ax_ask_divergence_cleared   A20 -- `ag_ask` VS `ax_dispatch`, READING
                   DIFFERENT COLLAPSES, MADE OBSERVABLE.  `ag_ask` is frozen
                   and asks about `arc_sel_agid` (order-1); `ax_dispatch`
                   acts on `SEL_AGID()` (order-N when live).  THE ASK ITSELF
                   IS UNTOUCHED -- `seeds/arc_goals.json` is byte-identical
                   to `HEAD` -- these two rules only compare two stamps both
                   `ag_ask` and `ax_dispatch` already read/write and mint/
                   clear a standing AgendaVerdict, the SAME direct-
                   reversible-pair shape A19 used for the order-N-fallback
                   question.  `ax_ask_divergence_active` mints
                   `AgendaVerdict{kind:'ask_dispatch_divergence',
                   active:1.0}` the instant the two stamps disagree;
                   `ax_ask_divergence_cleared` flips `active` to `0.0` the
                   instant they agree again.  `PROGRAM_SYNTHESIS_ARC6_
                   PREREG.md` amendment A20's own investigation proved a
                   STRUCTURAL BOUND on this seed's shipped policy (the
                   dispatch target can only ever be `ag_ask`'s winner or its
                   named runner-up, never an undisclosed third goal) and
                   measured how fragile it is (margin 32.7 against a 25.0
                   charge) -- this fact is what would catch a future policy
                   edit that breaks it.
  ax_impotent_pool_lapse /
  ax_impotent_pool_hold   A21 -- POOL-COMPOSITION DRIFT, CLOSED WITHOUT
                   TOUCHING `gr_condition_lapse`.  A13 SS8 item 1 / A14 SS9
                   item 6 named the gap: an `AgendaVerdict{kind:'impotent'}`
                   lapses (via `gr_condition_lapse`'s `fact_equals(arc_
                   measure_epoch)`) ONLY on an epoch bump, never merely
                   because the pool's MEMBERSHIP has since moved under it --
                   a reader had to compare `pool_agids` against the CURRENT
                   pool by hand to know which held verdict, if several, is
                   current.  THE MINT-ONCE GUARD AND `ax_impotent`'S OWN
                   `where`/`match` DO NOT CHANGE -- a distinct pool
                   signature still mints its own verdict, exactly as IM5
                   registered and gated; this only adds a SECOND, ORTHOGONAL
                   staleness axis to the verdicts already minted.  `stale`
                   (unmodified `gr_condition_lapse`) answers "has a
                   measurement happened since this was minted" -- an EPOCH
                   question.  The new `pool_stale` answers "does this
                   verdict's `pool_agids` still equal the pool's CURRENT
                   signature" -- a COMPOSITION question, live, no epoch
                   involved, exactly the shape A19/A20 already used for
                   their own non-epoch-shaped liveness questions (order-N
                   live; the two collapses agreeing) -- applied here
                   PER-NODE rather than as a global singleton, because IM5's
                   own design intentionally holds MULTIPLE distinct
                   `impotent` verdicts at once and a singleton flag would
                   collapse that history.  `ax_impotent_pool_lapse` sets
                   `pool_stale:1.0` the instant a verdict's OWN `pool_agids`
                   no longer equals the live `_pool_sig()`; `ax_impotent_
                   pool_hold` sets it back to `0.0` the instant they agree
                   again -- mutually exclusive by construction, the
                   `gr_condition_lapse`/`gr_condition_hold` SHAPE and NAMING
                   reused deliberately (this rung concluded the two-flag
                   idiom transfers; the ResidualCondition INDIRECTION does
                   not need to, because `_pool_sig()` is already a live,
                   graph-native Term with no Python probe behind it -- unlike
                   `fact_equals`, which is keyed to a `ResidualFact` a Python
                   adapter must stamp).  `gr_condition_lapse`'s closed
                   `MISMATCH` vocabulary is BYTE-UNCHANGED: `seeds/goal_
                   residuals.json` is not touched by this rung at all.

Run:  python tools/build_arc_executor_seed.py         (writes seeds/arc_executor.json)
      python tools/build_arc_executor_seed.py --check (fails if out of date)
"""
from __future__ import annotations

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

from build_arc_goals_seed import (  # noqa: E402
    A, AND, ARGMIN, COUNT, EQ, EXISTS, FILT, GT, HUB, ITE, L, MEASURE_EPOCH,
    NEIGH, NOT, NOT_, ONE_OF, OR, PLUS, POOL, SCAT, STR, T, V,
)


def IN_(node, edge_type):
    """`InNeighbours` -- the direction `Neighbours` doesn't reach: edges whose
    TARGET is `node`.  Needed once, by `ax_ask_impotent`'s own mint-once
    guard (A23): `ArcQuestion -asked_about_verdict-> AgendaVerdict` points
    FROM the question TO the verdict, so "has ANY question already asked
    about THIS verdict" is an in-edge existence check, not an out-edge one.
    Not defined in `build_arc_goals_seed.py` because nothing there needed it
    before this rung."""
    return {"type": "InNeighbours", "node": node, "edge_type": edge_type,
            "any_type": False}

OUT = os.path.join(ROOT, "seeds", "arc_executor.json")

RUNNER = "arc6_remeasure_row_verdict"
EXECUTABLE_KIND = "re_measure"
ARTIFACT = "results/arc6_verdict_pricing.json"
SOURCE_RID = "arc6.verdict.row_verdict_seed_only"

#  A15 -- THE SECOND ExecClass.  Same kind, different evidence_artifact and
#  source_rid, exactly the three-part key `_cue_matches`/`_routable` already
#  discriminate on -- ADDING THIS ROW REQUIRED ZERO CHANGES TO ANY RULE.
#  `ax_dispatch`, `ROUTE`, `_routable` and `_dispatchable` all filter over
#  EVERY `ExecClass` node, not a hard-coded one (confirmed by reading them,
#  PROGRAM_SYNTHESIS_ARC6_PREREG.md amendment A15's design investigation
#  item 5), so a second class is SEED DATA, not a rule edit.  Candidate
#  picked over the other four unwired residuals (seam A/B/C/D) because its
#  runner has no third-party dependency (unlike seam A's `sympy`, which is
#  not importable under this tree's default `python3` -- A15 item 8) and its
#  artifact is not shared with a sibling residual (unlike seam B/C, which
#  share `arc6_bc_ceiling.json`) -- see
#  PROGRAM_SYNTHESIS_ARC6_SECOND_EXECCLASS.md for the full candidate survey.
RUNNER_2 = "arc6_remeasure_structural"
ARTIFACT_2 = "results/arc6_structural_ceiling.json"
SOURCE_RID_2 = "arc6.structural.enum_op_table"

#  This engine has NO `unset_attr` and writing a null through an effect is not
#  a shipped idiom, so "the retirement stamp has been consumed" is carried by a
#  SENTINEL STRING rather than by absence.  `ax_retired_epoch` treats it
#  exactly as it treats absence; `ax_rearm` refuses on it.  Without this the
#  SECOND retirement would keep the FIRST one's epoch and the latch would
#  compare against a dead number — which reads as "the epoch has advanced" and
#  re-arms immediately, i.e. the oscillation the latch exists to prevent.
CONSUMED = "__consumed_by_ax_rearm__"


# --------------------------------------------------------------------------- #
#  THE ROUTE TABLE — `route_pick`'s own shape, applied to a goal's `kind`.
# --------------------------------------------------------------------------- #
def _cue_matches(cue_var, goal_var):
    """THE ROUTE KEY, AND IT IS TWO-PART FOR A MEASURED REASON.

    `kind` ALONE IS NOT ENOUGH, and that is not a precaution — it was measured.
    Running the loop with an unconditioned reply expires the testimony residual
    the reply minted, `ag_mint_remeasure` then fires **on the testimony**, and
    the goal it mints is
    `arc.remeasure.arc.testimony.missing_structural_primitive` with
    `kind: "re_measure"`.  A route keyed on `kind` alone would hand THAT to the
    row-verdict runner: same class name, completely different job, and the
    adapter would have re-run a measurement nobody asked for.

    So a cue declares **which measurement it can re-run** — the artifact — and
    the goal must name that same artifact.  A `re_measure` goal with no
    `evidence_artifact` (which is exactly what a testimony-sourced one has) can
    never match, because `Eq(null, <a string>)` is False and the explicit
    non-null guard refuses it first.
    """
    return AND(
        EQ(A(V(cue_var), "name"), A(V(goal_var), "kind")),
        EQ(A(V(cue_var), "evidence_artifact"),
           A(V(goal_var), "evidence_artifact")),
    )


def ROUTE(goal_var="g"):
    """The ExecClass cue for this goal, or NOTHING.

    `seeds/research_agenda_dispatch.json::route_pick` is
    `Argmin(Filter(cues, Eq(cue.kind, kind)), priority)` and this is that term
    with a two-part key.  An unroutable goal yields the Argmin's `default`
    (null), and `Attr(null, "runner")` is null — which is why `_routable` is a
    REQUIRED guard and not a nicety.
    """
    return ARGMIN(FILT(NOT_("ExecClass"), "ec", _cue_matches("ec", goal_var)),
                  "ec2", A(V("ec2"), "priority"), None)


def _routable(goal_var="g"):
    return AND(
        NOT(EQ(A(V(goal_var), "evidence_artifact"), L(None))),
        EXISTS(NOT_("ExecClass"), "ec3", _cue_matches("ec3", goal_var)),
        # THE THIRD KEY.  The runner knows how to re-ingest exactly ONE
        # residual — the ingest SPEC's dotted paths are per-rid — so the goal's
        # own mint source must be that residual.  Without this a future goal
        # pointed at the same artifact by some other route would be handed to a
        # re-ingest that cannot read it, and the failure would be a silently
        # skipped re-ingest rather than a refusal.
        EQ(A(ONE_OF(NEIGH(V(goal_var), "mint_source"), "msr"), "rid"),
           A(ROUTE(goal_var), "source_rid")),
    )


# --------------------------------------------------------------------------- #
#  WHICH COLLAPSE THE HANDS FOLLOW — A11's decision, AND IT IS THE RULE'S.
# --------------------------------------------------------------------------- #
def _order_n_is_not_live():
    """`mg_select` never fired on this graph, so there is no order-N selection.

    `Eq(attr, Lit null)` is this tree's ABSENT test, and it is the right
    predicate here for a reason that is structural rather than stylistic:
    `mg_sel_agid` is written by `mg_select` (`seeds/arc_magnitude.json`) and by
    nothing else, so its absence is exactly "the order-N collapse is not on this
    graph."  It is not a proxy for it.
    """
    return EQ(A(V("agenda"), "mg_sel_agid"), L(None))


def SEL_AGID():
    """THE SELECTION THE HANDS FOLLOW.  A11: **order-N when it is live.**

    AG-5 §8.9 measured that this graph carries TWO independent selections and
    that the hands followed the older one:

      arc_sel_agid  (ag_select,  order-1)          the 42-task blocker, 10.0
      mg_sel_agid   (mg_select,  order-N + scope)  the RE-MEASUREMENT goal, 7.7

    They disagree because MG2's attrition ladder does what it was built to do:
    the blocker's 42 tasks of paper inventory discount to 13.64 of order-N
    headroom, while the re-measurement goal's value is undiscounted because
    completing it unlocks nothing.  **Order-N picks the one goal this executor
    can actually run, with no human in the scene** — and the hands could not see
    it, because `_armed` compared against `arc_sel_agid`.

    A11's justification and its limit, quoted rather than paraphrased: order-1
    "credits paper inventory at ZERO discount and demonstrably misprices"; the
    magnitude rung measured 42 -> 13.64 -> ~1.9 expected, which is the arithmetic
    HS1 ran and which returned **0**.  Order-N is measurably better calibrated
    AND its attrition factors are read from artifacts.  It is **not** calibrated:
    the survival law's SHAPE is still authored (magnitude §8.2).

    THE DECISION IS A TERM, NOT A PYTHON BRANCH.  The adapter copies BOTH
    settled selections across the tick boundary verbatim — four reads, four
    writes, no comparison — and this `IfThenElse` is where "which one counts" is
    decided, from graph state.

    WHY A FALLBACK RATHER THAN A HARD DEPENDENCY.  `seeds/arc_magnitude.json` is
    `self_load_only` and is NOT in this seed's `depends_on`, so an executor may
    boot without the order-N collapse at all — every EX1-EX6 scene does exactly
    that.  Naming it a hard dependency would change what those scenes boot and
    would put an order-N collapse into every graph that wants hands.  A SOFT
    dependency leaves them byte-identical and lets a graph that holds the better
    collapse use it.  **The cost is that the fallback is SILENT**, so the order
    records which collapse it followed (`selected_by`) and both stamps as it saw
    them — the choice is a countable graph fact, not an inference from prose.
    """
    return ITE(_order_n_is_not_live(),
               A(V("agenda"), "arc_sel_agid"),
               A(V("agenda"), "mg_sel_agid"))


def SEL_VALUE():
    """The value of whichever selection `SEL_AGID` names — the second half of
    the two-tick agreement, and it must come from the SAME collapse or the
    agreement test would straddle two rankings."""
    return ITE(_order_n_is_not_live(),
               A(V("agenda"), "arc_sel_value"),
               A(V("agenda"), "mg_sel_value"))


def ARMED_AGID():
    """The armed copy of whichever selection `SEL_AGID` names."""
    return ITE(_order_n_is_not_live(),
               A(V("agenda"), "arc_exec_armed_agid"),
               A(V("agenda"), "arc_exec_armed_mg_agid"))


def ARMED_VALUE():
    return ITE(_order_n_is_not_live(),
               A(V("agenda"), "arc_exec_armed_value"),
               A(V("agenda"), "arc_exec_armed_mg_value"))


def COLLAPSE_NAME():
    """WHICH COLLAPSE THIS ORDER FOLLOWED, stamped on the order itself.

    The fallback above is silent by construction — a graph on which `mg_select`
    stops firing reverts to the collapse the magnitude rung measured as
    mispriced, and nothing would say so.  Stamping the name makes it readable
    off the order after the fact, which is the same move `retired_because` and
    `refused_because` already make in this seed."""
    return ITE(_order_n_is_not_live(),
               L("order_1_ag_select"), L("order_n_mg_select"))


def _armed(goal_var="g"):
    """THE TWO-TICK AGREEMENT TEST, AND IT IS NOT A FORMALITY — IT IS A FIX.

    MEASURED, on the shipped boot, with the first draft of this rule: an
    `ExecOrder` minted for
    `arc.remeasure.arc6.verdict.row_verdict_seed_only` while the fixpoint's
    FINAL `arc_sel_agid` was
    `arc.supply.…missing_structural_primitive` — i.e. **the executor ordered a
    job the collapse had not chosen.**  `run_rules` is a fixpoint with no rule
    ordering, so `ag_select`'s stamp is a TRANSIENT while `ag_mint_*` is still
    populating the pool and `ag_vocab_mint` is still pricing novelty; a rule
    that reads it in the same fixpoint reads whatever it happened to hold.
    This is the `children_of`-shaped hazard class exactly: nothing errors, the
    wrong thing simply happens.

    The fix is an AGREEMENT ACROSS TWO FIXPOINTS.  The adapter copies the
    settled selection into `arc_exec_armed_*` at the tick boundary — a verbatim
    copy with no comparison and no branch — and this guard requires the NEXT
    fixpoint's selection to agree with it on BOTH the winner and its value.
    **The comparison is the rule's; the adapter only carries the previous tick's
    conclusion across the boundary.**  A selection that is still moving cannot
    satisfy both halves.

    A11 (WH1): WHICH selection is `SEL_AGID`'s — order-N when the order-N
    collapse is live, order-1 when it is not.  The agreement test is UNCHANGED
    in shape; only the pair of stamps it reads moved, and BOTH sides of every
    comparison move together, so the guard can never straddle two rankings.
    The order-1 branch is the byte-identical predicate this rung inherited.
    """
    return AND(
        EQ(ARMED_AGID(), A(V(goal_var), "agid")),
        EQ(ARMED_AGID(), SEL_AGID()),
        EQ(ARMED_VALUE(), SEL_VALUE()),
        NOT(EQ(ARMED_AGID(), L(None))),
    )


def _in_pool(goal_var="g"):
    """`ag_select`'s POOL predicate, re-asserted on the BOUND goal.

    `ag_select` only rewrites `arc_sel_agid` while the pool is non-empty, so a
    stamp can outlive its goal's membership.  Re-asserting the predicate here
    makes "the executor acts only on a pool member" structural rather than
    inherited.  MEASURED HAZARD: `Gt(x, 0.0)` is TRUE for a MISSING `x`
    (`Gt(8.0, null)` is True on this engine), so the headroom read is
    coalesced explicitly — an unmeasured goal must not read as having headroom.
    """
    return AND(
        NOT(EQ(A(V(goal_var), "status"), L("retired"))),
        NOT(EQ(A(V(goal_var), "status"), L("settled"))),
        GT(ITE(EQ(A(V(goal_var), "headroom_n"), L(None)), L(0.0),
               A(V(goal_var), "headroom_n")), L(0.0)),
    )


# --------------------------------------------------------------------------- #
#  A13/WH4(c) -- THE IMPOTENCE TERM.  "terminate honestly", quantified over the
#  WHOLE POOL, never the winner.  Design: PROGRAM_SYNTHESIS_ARC6_WIRE_HANDS.md
#  SS5; bars: PROGRAM_SYNTHESIS_ARC6_PREREG.md amendment A13 (IM1-IM5).
# --------------------------------------------------------------------------- #
def MAPLIST(source, var_name, value):
    """`{n : n in source}` as an ORDERED LIST (`term.rs::TermNode::MapList`,
    evaluated by the SAME `evaluate()` the rule engine runs -- confirmed by
    reading the match arm, not assumed from the synth-only sub-language that
    also uses the name).  Not exported by `build_arc_goals_seed` (nothing
    there needs it), so it is a local, mechanical JSON constructor here, the
    same shape as every other Term builder in that module."""
    return {"type": "MapList", "source": source, "var_name": var_name,
            "value": value}


def _dispatchable(goal_var="g"):
    """`ax_dispatch`'s FULL per-goal routability, not just `_routable`'s
    partial reading.  `ax_dispatch`'s own `where` gates on `_routable(g)` AND
    a SEPARATE `Eq(Count(mint_source), 1)` clause (a goal with more than one
    mint-source edge is a shape `_routable`'s `ONE_OF` would silently pick an
    arbitrary survivor from); folding both in here means "dispatchable"
    matches EXACTLY what the executor can act on, not an approximation of it.
    """
    return AND(
        _routable(goal_var),
        EQ(COUNT(NEIGH(V(goal_var), "mint_source")), L(1)),
    )


def _pool_unroutable():
    """THE POOL-QUANTIFIED TEST, AND IT IS THE WHOLE POINT.

    A12/WH4 SS5.1 named the defect precisely: the current stop string
    (`no_executable_goal_was_selected`) is computed in a MEASUREMENT SCRIPT
    from the WINNER ALONE, so a pool holding one routable goal ranked second
    reads as impotent when it is not.  `Not(Exists(POOL(), g,
    dispatchable(g)))` is the correct quantifier -- it is FALSE the moment ANY
    pool member is dispatchable, regardless of rank -- and it costs nothing
    new: `POOL()` is `ag_select`'s own Filter (imported unchanged, so this
    inherits its EXACT membership semantics, including its known headroom-null
    exposure -- the same one `_in_pool` coalesces for the single-goal case;
    unmodified here on purpose, because "the pool" A13 quantifies over is
    THIS pool, not a hardened variant of it), and `_dispatchable` is
    `ax_dispatch`'s own guard, reused verbatim.
    """
    return NOT(EXISTS(POOL(), "gru", _dispatchable("gru")))


def _pool_nonempty():
    """A pool of ZERO goals is not impotent, it is DONE -- `Not(Exists(...))`
    over an empty source is vacuously True, so this guard is required or an
    agenda that has finished everything would mint a false impotence verdict
    the moment the last goal retires."""
    return EXISTS(POOL(), "gpe", L(True))


def _pool_sig():
    """A comparable STRING signature of the pool's CURRENT membership -- the
    ordered agid list, `MapList`'d then `ToJsonString`'d (the same
    `Value::List` -> `serde_json::Array` path the engine coherence probe
    exercises).  Comparable by plain `Eq`, WITH NO SORT: two reads of the SAME
    graph state walk the SAME underlying `Filter`, so this is a same-run,
    same-graph signature, not a canonical cross-run one -- exactly what the
    mint-once guard below needs and no more.  (This tree has no string-
    ordering primitive to build a canonical cross-run signature --
    `ArcGoalPolicy.tie_break`'s own residual, `tools/build_arc_goals_seed.py`
    -- and does not need one here.)
    """
    return STR(MAPLIST(POOL(), "gsig", A(V("gsig"), "agid")))


def _nearest_unroutable_goal():
    """PURELY DESCRIPTIVE, never part of the firing guard.  The goal whichever
    collapse is currently live is armed on (`SEL_AGID` -- order-N when
    `arc_magnitude` is live, order-1 otherwise), looked up by its own stamped
    agid so this never re-ranks."""
    return ONE_OF(FILT(NEIGH(V("agenda"), "has_arc_goal"), "gnu",
                       EQ(A(V("gnu"), "agid"), SEL_AGID())), "gnu2")


def _r_impotent():
    return {
        "name": "ax_impotent",
        "comment": (
            "A13/WH4(c) -- TERMINATE HONESTLY, AND IT QUANTIFIES OVER THE "
            "WHOLE POOL, NOT THE WINNER.  ag_ask fires on a TIE (margin < "
            "threshold under mutual ignorance); this fires on the case it "
            "cannot see -- a non-empty pool in which NOTHING is routable, no "
            "tie anywhere.  THE GUARD: Not(Exists(POOL(), g, dispatchable(g))) "
            "AND the pool is non-empty -- dispatchable is ax_dispatch's OWN "
            "routability test (_routable AND Count(mint_source)==1), reused "
            "verbatim, so this rule can never disagree with ax_dispatch about "
            "what it can run.  A pool with ONE routable member ranked below "
            "the winner does NOT fire this -- that is the discriminator "
            "against the wrong, winner-only reading (A13 IM2; the SHIPPED "
            "BOOT is that scene, unmodified). "
            "MINT-ONCE BY POOL SIGNATURE, NOT BY TICK: the guard excludes "
            "minting only while a NON-STALE verdict with the SAME pool "
            "signature (the ordered agid list, JSON-encoded) already exists, "
            "so an unchanged impotent pool never double-mints across "
            "repeated run_rules passes, and a GENUINELY different impotent "
            "pool (even inside one epoch) mints its own verdict. "
            "LAPSES THROUGH THE EXISTING gr_condition_lapse, UNMODIFIED: the "
            "verdict carries a holds_under edge to a ResidualCondition with "
            "ckind='fact_equals' against arc_measure_epoch, EXACTLY the "
            "'expire at the next measurement' idiom TestimonyPolicy's "
            "unconditioned replies already use -- gr_condition_lapse's match "
            "(seeds/goal_residuals.json) carries NO type constraint on the "
            "node it lapses, so this rides it for free, zero new mechanism. "
            "nearest_unroutable_* is DESCRIPTIVE ONLY (SEL_AGID -- whichever "
            "collapse is live) and is never read by the firing guard. "
            "A21 -- ADDITIVE ONLY: the verdict is now also stamped "
            "pool_stale:0.0 at mint (true by construction -- its own "
            "pool_agids trivially equals the CURRENT pool signature the "
            "instant it mints), read and flipped by ax_impotent_pool_lapse/"
            "ax_impotent_pool_hold below.  This where/match/mint-once guard "
            "is BYTE-UNCHANGED by A21."),
        "batch": True,
        "match": HUB,
        "where": AND(
            _pool_nonempty(),
            _pool_unroutable(),
            NOT(EXISTS(NOT_("AgendaVerdict"), "avq",
                       AND(EQ(A(V("avq"), "kind"), L("impotent")),
                           NOT(EQ(A(V("avq"), "stale"), L(1.0))),
                           EQ(A(V("avq"), "pool_agids"), _pool_sig())))),
        ),
        "effects": [
            ["add_node", "av", "AgendaVerdict", {
                "kind": "impotent",
                "epoch": T(MEASURE_EPOCH()),
                "pool_n": T(COUNT(POOL())),
                "pool_agids": T(_pool_sig()),
                "exec_classes_held": T(STR(MAPLIST(NOT_("ExecClass"), "ecl",
                                                    A(V("ecl"), "name")))),
                "nearest_unroutable_agid": T(SEL_AGID()),
                "nearest_unroutable_kind": T(A(_nearest_unroutable_goal(),
                                               "kind")),
                "stale": 0.0,
                "pool_stale": 0.0,
                "_the_decision_lives_here": (
                    "the firing guard is Not(Exists(POOL(), g, "
                    "dispatchable(g))) -- the adapter never computes this, "
                    "never decides it and never even reads it except to "
                    "render it back for a human."),
            }],
            ["add_edge", "agenda", "has_agenda_verdict", "av"],
            ["add_node", "avc", "ResidualCondition", {
                "ckind": "fact_equals",
                "filter_value": "arc_measure_epoch",
                "expected_str": T(MEASURE_EPOCH()),
                "why": (
                    "this verdict describes the pool AS OF this measurement "
                    "epoch; a new measurement may move the world, so it must "
                    "be re-read rather than re-used once one runs -- the SAME "
                    "expiry idiom TestimonyPolicy's unconditioned replies "
                    "already carry (default_condition_fact = "
                    "arc_measure_epoch)."),
            }],
            ["add_edge", "av", "holds_under", "avc"],
        ],
    }


# --------------------------------------------------------------------------- #
#  NODES
# --------------------------------------------------------------------------- #
def _nodes():
    return [
        {"local_id": 4000, "type": "ExecPolicy", "attrs": {
            "name": "default_exec_policy",
            "priority": 1,
            "_confinement_is_STRUCTURAL_not_promised": (
                "The executor can act on exactly the goal kinds for which an "
                "ExecClass cue exists.  There are TWO (A15), and the dispatch "
                "route is an Argmin over the cues matching the goal's THREE-"
                "PART key (kind + evidence_artifact + source_rid) -- so a "
                "supply_blocker / source_claim / self_concern winner, or a "
                "re_measure goal naming neither wired artifact, routes to "
                "NOTHING and mints no order.  Adding a class is a seed edit, "
                "visible in a diff; it is not something a rule can do."),
        }},
        {"local_id": 4010, "type": "ExecClass", "attrs": {
            "name": EXECUTABLE_KIND,
            "runner": RUNNER,
            "priority": 1,
            "evidence_artifact": ARTIFACT,
            "source_rid": SOURCE_RID,
            "denominator_unit": "mbpp_tasks",
            "_the_route_key_is_THREE_PART": (
                "kind + evidence_artifact + source_rid.  MEASURED: `kind` "
                "alone is not enough -- an expired unconditioned testimony "
                "mints arc.remeasure.arc.testimony.<region> with "
                "kind:'re_measure' and NO evidence_artifact, and a kind-only "
                "route would have handed that to this runner."),
            "description": (
                "THE FIRST EXECUTABLE CLASS -- re-measures the row-verdict "
                "residual.  A re-measurement goal names an artifact, a "
                "condition and a denominator, and the measurement it asks "
                "for ALREADY EXISTS AS A SCRIPT -- so executing it is "
                "re-running that script on the current binary, which is "
                "mechanical I/O."),
            "_runner_is_a_NAME_not_a_command": (
                "The adapter resolves this name against a frozen capability "
                "table.  A name with no table entry is REFUSED and recorded; "
                "the string is never a path, never an argv and never a shell "
                "word."),
        }},
        {"local_id": 4011, "type": "ExecClass", "attrs": {
            "name": EXECUTABLE_KIND,
            "runner": RUNNER_2,
            "priority": 1,
            "evidence_artifact": ARTIFACT_2,
            "source_rid": SOURCE_RID_2,
            "denominator_unit": "mbpp_tasks",
            "_the_route_key_is_THREE_PART": (
                "IDENTICAL shape to the first ExecClass -- same three-part "
                "key, disambiguated from it by evidence_artifact and "
                "source_rid, which is exactly what lets TWO ExecClass rows "
                "coexist with ZERO change to _cue_matches/ROUTE/_routable."),
            "description": (
                "THE SECOND EXECUTABLE CLASS (A15) -- re-measures the "
                "structural-ceiling residual (`arc6.structural."
                "enum_op_table`).  Picked over the other three unwired "
                "residuals (seam A/B/C/D) because its runner "
                "(`scripts/arc6_structural_ceiling.py`) has NO third-party "
                "dependency and its evidence artifact is not shared with a "
                "sibling residual -- see "
                "PROGRAM_SYNTHESIS_ARC6_SECOND_EXECCLASS.md.  Confirmed "
                "live: re-running it on this rung's engine produced "
                "GENUINELY DIFFERENT content from the committed evidence "
                "(witness_ids grew 7 -> 9), the same 'this is not a "
                "tautology, it can move' standard AG-5 SS2.2 applies to the "
                "row-verdict residual's own condition."),
            "_runner_is_a_NAME_not_a_command": (
                "Same capability-table permission boundary as the first "
                "class -- a name with no table entry is REFUSED and "
                "recorded; the string is never a path, never an argv and "
                "never a shell word."),
        }},
    ]


def _edges():
    return [{"src": {"local": 4000}, "tgt": {"local": 4010},
             "type": "has_exec_class", "attrs": {}},
            {"src": {"local": 4000}, "tgt": {"local": 4011},
             "type": "has_exec_class", "attrs": {}}]


def _productions():
    return [
        {"provenance": "seed:arc_executor:has_exec_class-0",
         "src": {"type": "ExecPolicy", "var": "s"}, "edge_type": "has_exec_class",
         "tgt": {"type": "ExecClass", "var": "t"}},
        {"provenance": "seed:arc_executor:has_exec_order-1",
         "src": {"type": "ArcGoal", "var": "s"}, "edge_type": "has_exec_order",
         "tgt": {"type": "ExecOrder", "var": "t"}},
        {"provenance": "seed:arc_executor:has_exec_order-2",
         "src": {"type": "ArcAgenda", "var": "s"}, "edge_type": "has_exec_order",
         "tgt": {"type": "ExecOrder", "var": "t"}},
        #  A13/WH4(c) -- the impotence term.
        {"provenance": "seed:arc_executor:has_agenda_verdict-0",
         "src": {"type": "ArcAgenda", "var": "s"}, "edge_type": "has_agenda_verdict",
         "tgt": {"type": "AgendaVerdict", "var": "t"}},
        {"provenance": "seed:arc_executor:holds_under-0",
         "src": {"type": "AgendaVerdict", "var": "s"}, "edge_type": "holds_under",
         "tgt": {"type": "ResidualCondition", "var": "t"}},
        #  A23 -- candidate (a), native form: the impotence-ask's own
        #  mint-once guard reads this edge (InNeighbours(av,
        #  asked_about_verdict)), the class-scoped twin of the already-
        #  declared ArcQuestion -asked_about-> ArcGoal production above.
        #  ArcImpotenceQuestion, NOT ArcQuestion -- a DISTINCT node type
        #  (caught live during AR23c, see ax_ask_impotent's own comment):
        #  reusing ArcQuestion would make this question answerable by the
        #  EXISTING, unmodified ag_reply_mints_testimony_conditioned/
        #  unconditioned rules (generic over TypeOf(q)=='ArcQuestion'),
        #  silently minting testimony -- candidate (b)'s territory -- by
        #  accident on every reply.
        {"provenance": "seed:arc_executor:asked_about_verdict-0",
         "src": {"type": "ArcImpotenceQuestion", "var": "s"},
         "edge_type": "asked_about_verdict",
         "tgt": {"type": "AgendaVerdict", "var": "t"}},
        #  ("ArcAgenda", "sent", "Message") is ALREADY admissible via
        #  arc_goals.json's own production (this seed depends_on arc_goals;
        #  the grammar is cumulative over the loaded seed set) -- not
        #  redeclared here.
        {"provenance": "seed:arc_executor:answered_by-0",
         "src": {"type": "ArcImpotenceQuestion", "var": "s"},
         "edge_type": "answered_by",
         "tgt": {"type": "Message", "var": "t"}},
        {"provenance": "seed:arc_executor:responds_to-0",
         "src": {"type": "Message", "var": "s"}, "edge_type": "responds_to",
         "tgt": {"type": "ArcImpotenceQuestion", "var": "t"}},
        #  A24 -- the reply side.  ax_ask_impotent_testify's own mint-once
        #  guard reads this edge (Neigh(q, mints_testimony)); the target
        #  type is DISTINCT from GoalResidual on purpose (design
        #  investigation: gr_move_penalty's own MATCH refuses every
        #  candidate this pool can ever contain, so a GoalResidual here
        #  would be inert by construction, not a reuse).
        {"provenance": "seed:arc_executor:mints_testimony-0",
         "src": {"type": "ArcImpotenceQuestion", "var": "s"},
         "edge_type": "mints_testimony",
         "tgt": {"type": "ArcImpotenceTestimony", "var": "t"}},
        #  holds_under already exists as an edge TYPE (AgendaVerdict ->
        #  ResidualCondition, above) -- this is a NEW production triple for
        #  the SAME edge type off a new src type, riding gr_condition_lapse's
        #  own type-agnostic match for free (zero new lapse mechanism).
        {"provenance": "seed:arc_executor:holds_under-1",
         "src": {"type": "ArcImpotenceTestimony", "var": "s"},
         "edge_type": "holds_under",
         "tgt": {"type": "ResidualCondition", "var": "t"}},
    ]


# --------------------------------------------------------------------------- #
#  RULES
# --------------------------------------------------------------------------- #
def _r_dispatch():
    return {
        "name": "ax_dispatch",
        "comment": (
            "AG-5, THE COLLAPSE->ACTION SEAM, AND IT IS route_pick's OWN SHAPE. "
            "The DECISION of what to run is this rule; running it is the "
            "adapter's mechanical I/O.  Three things are load-bearing and each "
            "has a measured reason. "
            "(1) THE WINNER IS BOUND BY THE COLLAPSE'S OWN STAMP, never "
            "re-ranked -- the ag_select_audit / ag_ask precedent -- AND THE "
            "STAMP MUST HAVE SETTLED.  MEASURED: reading the stamp inside the "
            "same fixpoint that writes it reads a TRANSIENT, and the first "
            "draft of this rule ordered the RUNNER-UP on the shipped boot while "
            "the fixpoint's final winner was a different goal.  `_armed` is the "
            "two-tick agreement test that closes it, on the winner AND its "
            "value. "
            "(1b) A11/WH1 -- WHICH COLLAPSE.  This graph carries TWO "
            "selections: ag_select's order-1 arc_sel_agid and mg_select's "
            "order-N + constraints mg_sel_agid, and AG-5 SS8.9 measured that "
            "with the tier ladder installed THEY DISAGREE -- order-1 picks the "
            "42-task blocker (paper inventory at zero discount, no ExecClass, "
            "unrunnable) and order-N picks the RE-MEASUREMENT goal, the one "
            "this executor can run, WITH NO HUMAN IN THE SCENE.  The hands now "
            "follow order-N when it is live and order-1 when it is not (see "
            "SEL_AGID) -- a SOFT dependency, because arc_magnitude is "
            "self_load_only and every EX1-EX6 scene boots without it.  The "
            "fallback is silent, so the order STAMPS which collapse it followed "
            "and both stamps as it saw them. "
            "(2) CONFINEMENT IS THE EMPTY ARGMIN.  The route is "
            "Argmin(Filter(ExecClass, <the THREE-PART key of _cue_matches plus "
            "_routable's source_rid check>), priority) and ONE ExecClass ships, "
            "so a goal that does not match on ALL THREE routes to null and the "
            "Exists guard refuses the mint.  kind ALONE IS NOT THE KEY, and "
            "that was measured, not foreseen -- see _cue_matches.  On the "
            "SHIPPED graph the winner IS unroutable (the 42-task blocker goal), "
            "so this branch is exercised by the boot itself, not by a fixture. "
            "(3) THE POOL PREDICATE IS RE-ASSERTED ON THE BOUND GOAL.  "
            "ag_select writes arc_sel_agid only while the pool is non-empty, so "
            "the stamp can outlive its goal's membership; without this the "
            "executor could run a goal that had already retired. "
            "SERIALISED TWO WAYS: at most one outstanding order globally, and "
            "at most one order per (goal, measurement epoch) -- so re-running "
            "the fixpoint cannot mint a second order for the same job, and a "
            "job may only recur once a NEW MEASUREMENT has happened."),
        "batch": True,
        "match": HUB + [["agenda", "has_arc_goal", "g"]],
        "where": AND(
            _armed("g"),
            _in_pool("g"),
            _routable("g"),
            EQ(COUNT(NEIGH(V("g"), "mint_source")), L(1)),
            NOT(EXISTS(NOT_("ExecOrder"), "o1", EQ(A(V("o1"), "status"),
                                                   L("ordered")))),
            NOT(EXISTS(NOT_("ExecOrder"), "o2",
                       AND(EQ(A(V("o2"), "agid"), A(V("g"), "agid")),
                           EQ(A(V("o2"), "ordered_epoch"), MEASURE_EPOCH())))),
        ),
        "effects": [
            ["add_node", "o", "ExecOrder", {
                "agid": T(A(V("g"), "agid")),
                "goal_kind": T(A(V("g"), "kind")),
                "runner": T(A(ROUTE("g"), "runner")),
                "exec_class": T(A(ROUTE("g"), "name")),
                "source_rid": T(A(ONE_OF(NEIGH(V("g"), "mint_source"), "ms"),
                                  "rid")),
                "evidence_artifact": T(A(V("g"), "evidence_artifact")),
                "ordered_epoch": T(MEASURE_EPOCH()),
                "status": "ordered",
                #  A11/WH1.  WHICH COLLAPSE THESE HANDS FOLLOWED, and what BOTH
                #  collapses said at the moment the order minted.  The fallback
                #  in SEL_AGID is silent by construction; this makes the choice
                #  a COUNTABLE GRAPH FACT rather than an inference from prose,
                #  and it makes "the executor acted on a goal order-1 did not
                #  choose" readable off the order itself.
                "selected_by": T(COLLAPSE_NAME()),
                "selected_value": T(SEL_VALUE()),
                "order1_sel_agid": T(A(V("agenda"), "arc_sel_agid")),
                "orderN_sel_agid": T(A(V("agenda"), "mg_sel_agid")),
                "_the_decision_lives_here": (
                    "which job to run is this rule's Argmin over the route "
                    "table applied to the collapse's own winner.  The adapter "
                    "reads `runner` and looks it up in a frozen table; it "
                    "chooses nothing."),
            }],
            ["add_edge", "g", "has_exec_order", "o"],
            ["add_edge", "agenda", "has_exec_order", "o"],
            ["set_attr", "g", "status", "pursued"],
            ["set_attr", "g", "pursued_epoch", T(MEASURE_EPOCH())],
        ],
    }


def _r_retired_epoch():
    return {
        "name": "ax_retired_epoch",
        "comment": (
            "WHEN a goal reached its terminal status.  ag_remeasure_retire "
            "(seeds/arc_goals.json, byte-frozen and gated) writes THAT it "
            "retired; the anti-oscillation latch below is defined in "
            "MEASUREMENT EPOCHS, and until this rung the epoch had no producer, "
            "so there was nothing to stamp.  Fires on an ABSENT stamp "
            "(`Eq(attr, Lit null)` is this tree's 'absent' test) OR on one "
            "ax_rearm has CONSUMED -- the second disjunct is what makes a "
            "SECOND retirement get its own epoch instead of inheriting the "
            "first one's.  Disjoint from ax_rearm's guard by construction, so "
            "the two never contend for the same goal in one pass."),
        "batch": True,
        "match": HUB + [["agenda", "has_arc_goal", "g"]],
        "where": AND(
            EQ(A(V("g"), "status"), L("retired")),
            OR(EQ(A(V("g"), "retired_epoch"), L(None)),
               EQ(A(V("g"), "retired_epoch"), L(CONSUMED))),
        ),
        "effects": [
            ["set_attr", "g", "retired_epoch", T(MEASURE_EPOCH())],
        ],
    }


def _r_rearm():
    return {
        "name": "ax_rearm",
        "comment": (
            "THE ANTI-OSCILLATION LATCH, AND IT IS TWO-SIDED BY CONSTRUCTION. "
            "The arc-goal design's SS8.2 guard -- 'a selected goal moves to a "
            "terminal status and only re-enters the pool on a measure_epoch "
            "bump' -- recorded by that rung as NOT implemented because a "
            "terminal status with no executor empties the pool with nothing "
            "done.  Now there is an executor. "
            "A retired re-measurement goal comes back ONLY when BOTH hold: its "
            "source residual is GENUINELY STALE AGAIN (gr_condition_lapse's own "
            "verdict, read off the residual -- this rule never re-evaluates a "
            "condition), AND the MEASUREMENT EPOCH HAS ADVANCED past the epoch "
            "it retired in.  The second half is what makes it a latch rather "
            "than a flap: the moment after a re-measurement the residual is "
            "un-stale AND the epoch is the retirement epoch, so BOTH halves "
            "refuse.  A condition that re-fails inside the same epoch waits; a "
            "new measurement without a re-failed condition changes nothing. "
            "WHY NOT ag_mint_remeasure.  That rule's mint-once guard is the "
            "monotone `remeasure_goal` EDGE LATCH and this engine has no "
            "remove_edge, so it can never fire twice for one residual.  "
            "Re-arming the EXISTING goal is therefore the only re-entry there "
            "is, and it is the better one: the pool never grows a duplicate, "
            "and `rearm_count` makes oscillation COUNTABLE."),
        "batch": True,
        "match": HUB + [["agenda", "has_arc_goal", "g"], ["r", "remeasure_goal", "g"]],
        "where": AND(
            EQ(A(V("g"), "status"), L("retired")),
            EQ(A(V("r"), "stale"), L(1.0)),
            NOT(EQ(A(V("g"), "retired_epoch"), L(None))),
            NOT(EQ(A(V("g"), "retired_epoch"), L(CONSUMED))),
            NOT(EQ(A(V("g"), "retired_epoch"), MEASURE_EPOCH())),
        ),
        "effects": [
            ["set_attr", "g", "status", "minted"],
            ["set_attr", "g", "rearmed_epoch", T(MEASURE_EPOCH())],
            ["set_attr", "g", "rearmed_because",
             "source_residual_stale_again_at_a_LATER_measurement_epoch"],
            ["set_attr", "g", "rearm_count",
             T(PLUS(ITE(EQ(A(V("g"), "rearm_count"), L(None)), L(0.0),
                        A(V("g"), "rearm_count")), L(1.0)))],
            # The retirement stamp must be CONSUMED, or the second retirement
            # would keep the first one's epoch and the latch would compare
            # against a dead number.  No unset_attr on this engine, so the
            # sentinel does the work and ax_retired_epoch re-stamps over it.
            ["set_attr", "g", "retired_epoch", CONSUMED],
        ],
    }


def _r_world_probe_epoch():
    return {
        "name": "ax_world_probe_epoch",
        "comment": (
            "A18 -- THE RE-ARM DEADLOCK, CLOSED WITHOUT RUNNING ANYTHING. "
            "PROGRAM_SYNTHESIS_ARC6_EXECUTOR.md SS5: 'the executor is the "
            "epoch's producer, but it only produces one by RUNNING a goal, "
            "and a retired goal is not in the pool to be run.  With exactly "
            "one executable goal, a genuinely re-failed condition cannot "
            "bring it back on its own.'  MEASURED (PREREG A18 item 3, "
            "reusing PROGRAM_SYNTHESIS_ARC6_SECOND_EXECCLASS.md SS6's own "
            "live probe): the NATURAL trajectory with BOTH shipped "
            "ExecClasses retires both re_measure goals and leaves ZERO "
            "executable pool members, not one -- the deadlock's precondition "
            "is the ORDINARY end state of this loop, not a corner case. "
            "THIS RULE IS NOT A SECOND ax_rearm.  It does not touch that "
            "rule, does not read arc_measure_epoch to decide anything about "
            "a goal's re-entry, and does not widen ax_rearm's own "
            "conjunction.  It decides exactly one, narrower thing: whether a "
            "RETIRED goal's source residual has genuinely re-failed on TWO "
            "SEPARATE, EXTERNALLY-TRIGGERED world probes (r.stale == 1.0 "
            "confirmed against r.stale_at_last_probe -- the adapter's own "
            "carry of the PREVIOUS refresh_evidence_facts call's reading, "
            "the ARM_CARRY precedent applied at the probe-call boundary "
            "instead of the fixpoint-tick boundary) while the clock has been "
            "stuck since retirement (retired_epoch == the CURRENT epoch, "
            "i.e. nothing else has advanced it yet).  A SINGLE probe cannot "
            "satisfy this -- stale_at_last_probe still holds the PRIOR, "
            "pre-drift reading on the first sighting -- which is the "
            "discriminator against collapsing EX4's cell C into cell D "
            "(this rung's own AR18b).  Investigated and REJECTED before "
            "this rule was written: coupling the epoch bump directly to the "
            "SAME single detection event `stale` is already computed from "
            "would do exactly that. "
            "The adapter reads the resulting fact (world_drift_confirmed) as "
            "a PURE QUERY -- the same shape as pending_orders -- and calls "
            "the SAME agi.bump_measure_epoch that run_order already calls, "
            "mechanically, OUTSIDE run_rules(), so ax_rearm's own "
            "epoch-advance check is satisfied only on the NEXT fixpoint, "
            "exactly as EX4's cell D already requires manually.  This rule "
            "only widens WHICH real-world events can produce the epoch bump "
            "ax_rearm has always read; it never runs a measurement and never "
            "touches the latch."),
        "batch": True,
        "match": HUB + [["agenda", "has_arc_goal", "g"], ["r", "remeasure_goal", "g"]],
        "where": AND(
            EQ(A(V("g"), "status"), L("retired")),
            EQ(A(V("r"), "stale"), L(1.0)),
            EQ(A(V("r"), "stale_at_last_probe"), L(1.0)),
            NOT(EQ(A(V("g"), "retired_epoch"), L(None))),
            NOT(EQ(A(V("g"), "retired_epoch"), L(CONSUMED))),
            EQ(A(V("g"), "retired_epoch"), MEASURE_EPOCH()),
        ),
        "effects": [
            ["set_attr", "g", "world_drift_confirmed", 1.0],
            ["set_attr", "g", "world_drift_confirmed_epoch", T(MEASURE_EPOCH())],
        ],
    }


# --------------------------------------------------------------------------- #
#  A19 -- THE SILENT ORDER-N FALLBACK, MADE OBSERVABLE.
#  Design: PROGRAM_SYNTHESIS_ARC6_WIRE_HANDS.md SS8.1; bars:
#  PROGRAM_SYNTHESIS_ARC6_PREREG.md amendment A19 (AR19a-AR19d).
#  THE FALLBACK ITSELF (SEL_AGID reverting to order-1 when mg_sel_agid is
#  absent) IS UNTOUCHED -- these two rules only read _order_n_is_not_live()
#  (the SAME Term SEL_AGID branches on, imported verbatim, never re-derived)
#  and mint/clear a standing AgendaVerdict.  Neither rule appears in
#  ax_dispatch's own where, and ax_dispatch's where is byte-unchanged.
# --------------------------------------------------------------------------- #
def _fallback_verdict_active():
    """Whether a currently-ACTIVE AgendaVerdict{kind:'order_n_fallback'}
    already exists.  Mirrors ax_impotent's own mint-once-by-signature guard,
    simplified: there is only ONE possible "signature" here (the fallback is
    either live or it is not), so the guard is `active`, not a pool-shaped
    string comparison."""
    return EXISTS(NOT_("AgendaVerdict"), "avfa",
                  AND(EQ(A(V("avfa"), "kind"), L("order_n_fallback")),
                      EQ(A(V("avfa"), "active"), L(1.0))))


def _r_fallback_silent():
    return {
        "name": "ax_fallback_silent",
        "comment": (
            "A19 -- THE FALLBACK, MADE OBSERVABLE (the ON direction).  "
            "WIRE_HANDS SS8.1: 'the fallback is silent... nothing raises an "
            "alarm.'  Fires the instant the order-N collapse is not "
            "producing a stamp (_order_n_is_not_live(), the SAME Term "
            "SEL_AGID itself branches on -- this rule can never disagree "
            "with ax_dispatch about which collapse is live, by "
            "construction) AND no currently-active verdict of this kind "
            "already exists (mint-once, ax_impotent's own shape).  Mints "
            "AgendaVerdict{kind:'order_n_fallback', active:1.0} off the "
            "SAME agenda hub ax_impotent uses -- a standing, queryable "
            "graph fact a self-monitoring agent (or a human, or a future "
            "rung) can check PROACTIVELY, rather than inferring the "
            "fallback's state order by order from `selected_by`.  Mutually "
            "exclusive with ax_fallback_cleared by construction: one reads "
            "the Term true, the other reads it false."),
        "batch": True,
        "match": HUB,
        "where": AND(
            _order_n_is_not_live(),
            NOT(_fallback_verdict_active()),
        ),
        "effects": [
            ["add_node", "avf", "AgendaVerdict", {
                "kind": "order_n_fallback",
                "active": 1.0,
                "epoch": T(MEASURE_EPOCH()),
                "reason": "mg_sel_agid_absent_order_n_collapse_not_"
                          "producing_a_stamp",
                "_the_decision_lives_here": (
                    "the firing guard is _order_n_is_not_live(), the SAME "
                    "Term SEL_AGID reads to pick which collapse the hands "
                    "follow -- the adapter never computes this and never "
                    "decides it."),
            }],
            ["add_edge", "agenda", "has_agenda_verdict", "avf"],
        ],
    }


def _r_fallback_cleared():
    return {
        "name": "ax_fallback_cleared",
        "comment": (
            "A19 -- THE FALLBACK, MADE OBSERVABLE (the OFF direction, and "
            "it is not decoration: a one-way mint would itself be a claim "
            "that cannot be revised -- the gr_condition_lapse/gr_condition_"
            "hold precedent, quoted almost verbatim).  Fires the instant "
            "order-N IS live (Not(_order_n_is_not_live())) while a "
            "previously-minted verdict is still marked active, and flips "
            "`active` to 0.0.  DELIBERATELY NOT the epoch-shaped "
            "fact_equals(arc_measure_epoch) idiom ax_impotent uses: "
            "arc_magnitude can be loaded onto an ALREADY-RUNNING graph "
            "with no epoch bump anywhere in the scene (exactly how "
            "test_wh3_* vs test_wh1_* differ -- one boots without it, one "
            "with), so a self-monitoring agent's 'is the fallback active "
            "RIGHT NOW' question needs the CURRENT truth of the Term, not "
            "a description that stays valid only until the next "
            "measurement.  Mutually exclusive with ax_fallback_silent by "
            "construction, so the two never contend for the same node in "
            "one pass."),
        "batch": True,
        "match": HUB + [["agenda", "has_agenda_verdict", "avf"]],
        "where": AND(
            NOT(_order_n_is_not_live()),
            EQ(A(V("avf"), "kind"), L("order_n_fallback")),
            EQ(A(V("avf"), "active"), L(1.0)),
        ),
        "effects": [
            ["set_attr", "avf", "active", 0.0],
            ["set_attr", "avf", "cleared_epoch", T(MEASURE_EPOCH())],
        ],
    }


# --------------------------------------------------------------------------- #
#  A20 -- `ag_ask` vs `ax_dispatch`, MADE OBSERVABLE (the A19 pattern, applied
#  to a DIFFERENT question).  A19 asked "is the order-N collapse live at
#  all"; this asks "given that it IS live, does it name the SAME goal
#  `ag_ask` asked about."  `PROGRAM_SYNTHESIS_ARC6_PREREG.md` amendment A20's
#  own design investigation (item 2) proved a STRUCTURAL BOUND on this
#  seed's shipped policy weights -- the dispatch target can only ever be
#  `arc_sel_agid` (A, ag_ask's WINNER candidate) or `arc_sel_runner_up_agid`
#  (B, ag_ask's OTHER candidate), never a third goal neither was asked about
#  -- and AR20b's adversarial scope-charge probe measured how FRAGILE that
#  bound is (a single scope declaration comes within 7.7 of breaking it: the
#  measured AGID-over-SB_BUDGET dominance margin is 32.7, the scope charge
#  weight is 25.0).  A bound that holds today but is not asserted anywhere
#  and could flip on a future policy-weight edit is exactly the case for a
#  STANDING FACT rather than a comment: `ax_ask_divergence_active` mints the
#  instant `ax_dispatch`'s target differs from `ag_ask`'s named WINNER,
#  `ax_ask_divergence_cleared` flips it off the instant they agree again --
#  the SAME direct-reversible-pair shape A19 used for the SAME reason (this
#  question is not epoch-shaped either: a scope reply or a testimony reply
#  can move `arc_sel_agid` or `SEL_AGID()` with no epoch bump anywhere in
#  the scene, exactly as arc_magnitude loading did for A19).
#
#  `ag_ask` IS NOT TOUCHED.  Both rules read stamps `ag_ask`/`ax_dispatch`
#  ALREADY read (`arc_sel_agid`, `arc_sel_runner_up_agid`, `SEL_AGID()`) --
#  zero new DSL Term, zero new node type, zero new edge type, zero new
#  adapter function (`agenda_verdicts(sub, kind=...)` is already generic,
#  A19's own finding, unchanged here), zero edit to `seeds/arc_goals.json`.
# --------------------------------------------------------------------------- #
def _dispatch_differs_from_ask_winner():
    """TRUE iff `ax_dispatch`'s own target (`SEL_AGID()`, order-N when live,
    order-1 otherwise -- the IDENTICAL Term `ax_dispatch`'s `where` branches
    on) is not null, `ag_ask`'s WINNER candidate (`arc_sel_agid`) is not
    null, and the two disagree.  Reading `SEL_AGID()` here can never drift
    from what `ax_dispatch` itself acts on, by construction -- the same
    guarantee `_order_n_is_not_live()` gives A19's pair."""
    return AND(
        NOT(EQ(SEL_AGID(), L(None))),
        NOT(EQ(A(V("agenda"), "arc_sel_agid"), L(None))),
        NOT(EQ(SEL_AGID(), A(V("agenda"), "arc_sel_agid"))),
    )


def _ask_divergence_verdict_active():
    """Whether a currently-ACTIVE AgendaVerdict{kind:'ask_dispatch_
    divergence'} already exists -- ax_impotent's / A19's own mint-once-while-
    active guard, the same single-signature simplification A19 uses (the
    divergence is either live or it is not)."""
    return EXISTS(NOT_("AgendaVerdict"), "avd",
                  AND(EQ(A(V("avd"), "kind"), L("ask_dispatch_divergence")),
                      EQ(A(V("avd"), "active"), L(1.0))))


def _r_ask_divergence_active():
    return {
        "name": "ax_ask_divergence_active",
        "comment": (
            "A20 -- `ag_ask` VS `ax_dispatch`, MADE OBSERVABLE (the ON "
            "direction).  WIRE_HANDS SS8 item 4: 'the agent can ask about "
            "one goal while acting on another in the same fixpoint... "
            "nothing asserts it either way.'  Fires the instant "
            "ax_dispatch's OWN target (SEL_AGID()) disagrees with ag_ask's "
            "WINNER candidate (arc_sel_agid) AND no currently-active "
            "verdict of this kind already exists (mint-once, ax_impotent's "
            "/ax_fallback_silent's own shape).  Mints AgendaVerdict{kind:"
            "'ask_dispatch_divergence', active:1.0} off the SAME agenda hub "
            "ax_impotent/ax_fallback_silent use -- a standing, queryable "
            "graph fact a self-monitoring agent (or a human, or a future "
            "rung) can check PROACTIVELY, instead of comparing an "
            "ArcQuestion's agid_a against an ExecOrder's agid order by "
            "order after the fact.  Also stamps whether the dispatch "
            "target at least matches ag_ask's OTHER candidate "
            "(arc_sel_runner_up_agid) -- descriptive only, never read by "
            "any guard -- because A20's own design investigation proved "
            "this is true on every scene this seed's shipped policy can "
            "reach (the structural bound), and a future policy edit "
            "breaking it is precisely the thing this fact exists to catch."),
        "batch": True,
        "match": HUB,
        "where": AND(
            _dispatch_differs_from_ask_winner(),
            NOT(_ask_divergence_verdict_active()),
        ),
        "effects": [
            ["add_node", "avd", "AgendaVerdict", {
                "kind": "ask_dispatch_divergence",
                "active": 1.0,
                "epoch": T(MEASURE_EPOCH()),
                "asked_about_agid": T(A(V("agenda"), "arc_sel_agid")),
                "asked_about_runner_up_agid":
                    T(A(V("agenda"), "arc_sel_runner_up_agid")),
                "dispatch_target_agid": T(SEL_AGID()),
                "dispatch_matches_runner_up":
                    T(EQ(SEL_AGID(), A(V("agenda"), "arc_sel_runner_up_agid"))),
                "reason": "ax_dispatch_is_acting_on_a_goal_ag_ask_did_not_"
                          "name_as_its_winner",
                "_the_decision_lives_here": (
                    "the firing guard compares SEL_AGID() -- the IDENTICAL "
                    "Term ax_dispatch's where branches on -- against "
                    "arc_sel_agid; the adapter never computes this and "
                    "never decides it, and ag_ask is not read, only its "
                    "OWN stamp is."),
            }],
            ["add_edge", "agenda", "has_agenda_verdict", "avd"],
        ],
    }


def _r_ask_divergence_cleared():
    return {
        "name": "ax_ask_divergence_cleared",
        "comment": (
            "A20 -- THE OFF DIRECTION, and not decoration: a one-way mint "
            "would itself be a claim that cannot be revised -- the "
            "gr_condition_lapse/gr_condition_hold precedent, A19's own "
            "citation of it, applied a third time.  Fires the instant the "
            "two stamps AGREE (or either goes null) while a previously-"
            "minted verdict is still marked active, and flips `active` to "
            "0.0.  DELIBERATELY NOT epoch-shaped, same reason as A19's "
            "ax_fallback_cleared: a scope or testimony reply can move "
            "arc_sel_agid or SEL_AGID() with no epoch bump anywhere in the "
            "scene, so a self-monitoring agent's 'do they agree RIGHT NOW' "
            "question needs the CURRENT truth of the comparison, not a "
            "description valid only until the next measurement.  Mutually "
            "exclusive with ax_ask_divergence_active by construction."),
        "batch": True,
        "match": HUB + [["agenda", "has_agenda_verdict", "avd"]],
        "where": AND(
            NOT(_dispatch_differs_from_ask_winner()),
            EQ(A(V("avd"), "kind"), L("ask_dispatch_divergence")),
            EQ(A(V("avd"), "active"), L(1.0)),
        ),
        "effects": [
            ["set_attr", "avd", "active", 0.0],
            ["set_attr", "avd", "cleared_epoch", T(MEASURE_EPOCH())],
        ],
    }


# --------------------------------------------------------------------------- #
#  A21 -- POOL-COMPOSITION DRIFT, CLOSED WITHOUT TOUCHING `gr_condition_
#  lapse`.  PROGRAM_SYNTHESIS_ARC6_IMPOTENCE_TERM.md SS8 item 1 / PROGRAM_
#  SYNTHESIS_ARC6_IMPOTENCE_CAMPAIGN.md SS9 item 6: `ax_impotent`'s verdict
#  lapses (gr_condition_lapse, unmodified) only on an EPOCH bump, never on
#  the pool's own MEMBERSHIP moving under it within one epoch -- a reader
#  had to compare pool_agids against the current pool by hand.  These two
#  rules add a SECOND, ORTHOGONAL staleness axis (`pool_stale`) to each
#  `impotent` verdict, live, keyed on the SAME `_pool_sig()` Term
#  `ax_impotent` itself mints against -- so this can never disagree with
#  ax_impotent about what the pool's signature is, by construction.  NEITHER
#  rule appears in ax_impotent's own where/match, and ax_impotent's mint-once
#  guard is byte-unchanged: a genuinely different impotent pool composition
#  still mints its OWN verdict (IM5's own registered behaviour), and these
#  two rules only add a currentness marker ON TOP of that, per node, never
#  collapsing the multi-verdict history into one global flag the way a
#  literal reuse of A19/A20's SINGLETON shape would have.
# --------------------------------------------------------------------------- #
def _r_impotent_pool_lapse():
    return {
        "name": "ax_impotent_pool_lapse",
        "comment": (
            "A21 -- POOL DRIFT, THE ON DIRECTION.  Fires the instant an "
            "impotent verdict's OWN pool_agids no longer equals the LIVE "
            "_pool_sig() -- i.e. the pool's membership has moved since this "
            "verdict minted, whether or not arc_measure_epoch has advanced. "
            "Sets pool_stale:1.0.  Deliberately NOT epoch-shaped, the SAME "
            "reason A19/A20 gave for their own reversible pairs: a goal can "
            "leave the pool (headroom_n -> 0, a status retirement, a "
            "further supply/claim resolution) with no epoch bump anywhere "
            "in the scene, and 'does this verdict still describe the "
            "CURRENT pool' needs the CURRENT truth of that comparison, not "
            "a description honest only until the next measurement.  PER-"
            "NODE, not a singleton EXISTS guard: every impotent verdict on "
            "the graph is independently compared against the SAME live "
            "signature, so IM5's multi-verdict history (one verdict per "
            "distinct pool composition) is preserved, not collapsed.  "
            "Mutually exclusive with ax_impotent_pool_hold by construction "
            "(Eq vs Not(Eq) against the same comparison), so the two never "
            "contend for the same node in one pass -- the gr_condition_"
            "lapse/gr_condition_hold SHAPE and NAMING, reused deliberately: "
            "gr_condition_lapse's own ResidualCondition INDIRECTION is not "
            "needed here because _pool_sig() is already a live, graph-"
            "native Term evaluated inside ax_impotent itself, with no "
            "Python probe behind it (unlike fact_equals, which reads a "
            "ResidualFact a Python adapter must stamp) -- so a fourth "
            "ckind in gr_condition_lapse's closed MISMATCH vocabulary would "
            "buy nothing this direct comparison does not already give, at "
            "the cost of coupling the GENERIC goal_residuals seed to this "
            "seed's own POOL()/_pool_sig() concept.  seeds/goal_"
            "residuals.json is BYTE-UNCHANGED by this rule."),
        "batch": True,
        "match": HUB + [["agenda", "has_agenda_verdict", "av"]],
        "where": AND(
            EQ(A(V("av"), "kind"), L("impotent")),
            NOT(EQ(A(V("av"), "pool_agids"), _pool_sig())),
            NOT(EQ(A(V("av"), "pool_stale"), L(1.0))),
        ),
        "effects": [
            ["set_attr", "av", "pool_stale", 1.0],
            ["set_attr", "av", "pool_stale_epoch", T(MEASURE_EPOCH())],
        ],
    }


def _r_impotent_pool_hold():
    return {
        "name": "ax_impotent_pool_hold",
        "comment": (
            "A21 -- POOL DRIFT, THE OFF DIRECTION, and not decoration: a "
            "one-way lapse would itself be an unrevisable claim -- the "
            "gr_condition_lapse/gr_condition_hold precedent, applied "
            "directly.  Fires the instant an impotent verdict's pool_agids "
            "AGREES with the live _pool_sig() again (true at mint, by "
            "construction; also true again if the pool's composition ever "
            "returns to exactly what this verdict recorded -- e.g. a "
            "re-arm brings a goal back and no further exit has happened) "
            "while pool_stale is still 1.0, and restores pool_stale to 0.0. "
            "Mutually exclusive with ax_impotent_pool_lapse by construction."),
        "batch": True,
        "match": HUB + [["agenda", "has_agenda_verdict", "av"]],
        "where": AND(
            EQ(A(V("av"), "kind"), L("impotent")),
            EQ(A(V("av"), "pool_agids"), _pool_sig()),
            EQ(A(V("av"), "pool_stale"), L(1.0)),
        ),
        "effects": [
            ["set_attr", "av", "pool_stale", 0.0],
            ["set_attr", "av", "pool_held_epoch", T(MEASURE_EPOCH())],
        ],
    }


def _r_close():
    return {
        "name": "ax_close",
        "comment": (
            "AN EXECUTION THAT COMPLETED IS A COUNTABLE GRAPH FACT.  The order "
            "closes when its own goal has reached the terminal status -- i.e. "
            "when ag_remeasure_retire fired, which happens only if the "
            "re-measurement actually un-staled the source residual.  So a "
            "CLOSED order is evidence the loop closed, and an order left at "
            "`ran` is evidence it did not: the two are distinguishable without "
            "reading any adapter return value."),
        "batch": True,
        "match": [["g", "has_exec_order", "o"]],
        "where": AND(
            EQ(A(V("o"), "status"), L("ran")),
            EQ(A(V("g"), "status"), L("retired")),
        ),
        "effects": [
            ["set_attr", "o", "status", "closed"],
            ["set_attr", "o", "closed_epoch", T(MEASURE_EPOCH())],
            ["set_attr", "o", "outcome",
             "goal_retired_source_residual_no_longer_stale"],
        ],
    }


def _r_ask_impotent():
    return {
        "name": "ax_ask_impotent",
        "comment": (
            "A23 -- CANDIDATE (a), NATIVE FORM (PROGRAM_SYNTHESIS_ARC6_PREREG."
            "md amendment A23).  `ag_ask` (AG-4) only fires on a VALUE tie; "
            "`ax_impotent` fires on the case it cannot see -- a non-empty pool "
            "in which NOTHING is routable, no tie required.  Until this rule, "
            "an impotent pool went unasked-about entirely: the loop terminated "
            "honestly (mints AgendaVerdict{kind:'impotent'}) but said nothing "
            "to a human who could name a checkable reason. "
            "THE GUARD IS CLASS-SCOPED, NOT GOAL-SCOPED -- this is the whole "
            "point of this rule and the reason it is not a copy of ag_ask's "
            "own guard.  Keyed to the AgendaVerdict's OWN node identity "
            "(Not(Exists(InNeighbours(av, asked_about_verdict), qi, True))), "
            "the SAME mint-once-by-signature shape ax_impotent itself already "
            "uses for the SAME pool (av mints once per DISTINCT pool_agids, "
            "A13/WH4(c)), and the same SHAPE gap_awareness.json's content-dedup "
            "guard uses one seed over (note_unresolved_topic_gap/note_reported_"
            "gap: file once per distinct content, not once per triggering "
            "utterance).  A NAIVE reuse of ag_ask's own re-entry gate -- "
            "Not(Exists(ArcQuestion, region==REGION(g), asked_epoch=="
            "MEASURE_EPOCH())) -- is keyed PER GOAL, because REGION(g) falls "
            "back to g.agid whenever sig_seam is unset, true of every "
            "supply_blocker/source_claim/decomposition_tier goal this tree "
            "has ever minted (A14 design investigation finding 3), and would "
            "therefore re-fire every time testimony drifts nearest_unroutable_"
            "agid to a goal not yet asked about BY THAT AGID -- A22 SS3's own "
            "measured testimony chain drifts the live winner THREE times "
            "inside ONE measurement epoch, on the SAME unchanged 10-goal "
            "pool (PROGRAM_SYNTHESIS_ARC6_IMPOTENCE_RESWEEP.md SS3).  Keying "
            "to av's own identity instead means the WHOLE CHAIN -- however "
            "many times the winner drifts under testimony -- is still "
            "describing the SAME impotent state (A14's own headline finding: "
            "testimony reweights the pool WITHOUT changing its membership), "
            "so it is asked about EXACTLY ONCE.  AR23c measures this live, "
            "against a throwaway naive comparator built only in the "
            "measurement script (never shipped here). "
            "THE QUESTION NAMES THE PRESUPPOSITION EXPLICITLY (design "
            "investigation item 3, not a bare testimony request about one "
            "goal's content): whether the blocker belongs to the ONE "
            "nearest-ranked goal specifically, or to the WHOLE CLASS sharing "
            "its kind. "
            "DELIBERATELY MINTS NO GoalResidual/testimony -- candidate (b)'s "
            "territory (mint-a-capability-goal-adjacent), already NO-GO'd by "
            "A22, and out of THIS rule's scope by design: this rule only asks "
            "a different question, it does not reprice anything, which is "
            "also what keeps AR23c's fixed-point test honest (the ask "
            "stopping is never confounded with the pool changing). "
            "MINTS A DISTINCT NODE TYPE, ArcImpotenceQuestion, NOT ArcQuestion "
            "-- CAUGHT LIVE DURING AR23c's OWN MEASUREMENT, not designed in "
            "up front: an ArcQuestion-typed node here would ALSO match "
            "ag_reply_mints_testimony_conditioned/unconditioned's own "
            "TypeOf(q)=='ArcQuestion' guard (seeds/goal_residuals.json is "
            "untouched, but arc_goals.json's two reply rules are generic "
            "over EVERY ArcQuestion), so a REPLY to this question would "
            "SILENTLY mint testimony too -- exactly candidate (b)'s territory, "
            "by accident, defeating the whole 'this rule only asks, it does "
            "not reprice' design intent. A distinct type is the SAME cost as "
            "the `evidence_artifact`/`source_rid` three-part-key discriminator "
            "A15 finding 5 already relies on to keep two ExecClasses from "
            "colliding on a shared route: TYPE is the cheapest discriminator "
            "this engine has, and it costs zero new rules."),
        "batch": True,
        "match": HUB + [["agenda", "has_agenda_verdict", "av"]],
        "where": AND(
            EQ(A(V("av"), "kind"), L("impotent")),
            NOT(EQ(A(V("av"), "stale"), L(1.0))),
            NOT(EXISTS(IN_(V("av"), "asked_about_verdict"), "qi", L(True))),
        ),
        "effects": [
            ["add_node", "q", "ArcImpotenceQuestion", {
                "kind": "impotence",
                "region": T(A(V("av"), "nearest_unroutable_kind")),
                "agid_a": T(A(V("av"), "nearest_unroutable_agid")),
                "pool_n": T(A(V("av"), "pool_n")),
                "asked_epoch": T(MEASURE_EPOCH()),
                "answered": 0.0,
                "status": "open",
            }],
            ["add_edge", "q", "asked_about_verdict", "av"],
            ["add_node", "reply", "Message", {
                "from": "agent",
                "kind": "arc_impotence_question",
                "text": T(SCAT(
                    L("I hold "), STR(A(V("av"), "pool_n")),
                    L(" goals and NONE of them are currently routable. The "
                      "nearest candidate by rank is "),
                    A(V("av"), "nearest_unroutable_agid"),
                    L(" (kind "), A(V("av"), "nearest_unroutable_kind"),
                    L("), but that ranking is over the WHOLE POOL, not a "
                      "property of that one goal alone -- other goals of "
                      "the same kind may or may not share this gap. Is the "
                      "blocker specific to "),
                    A(V("av"), "nearest_unroutable_agid"),
                    L(", or does it apply to every "),
                    A(V("av"), "nearest_unroutable_kind"),
                    L(" goal in this pool? Answering either way lets me "
                      "stop re-asking about whichever goal happens to rank "
                      "first without re-litigating the whole class each "
                      "time it drifts."),
                )),
            }],
            ["add_edge", "agenda", "sent", "reply"],
            ["add_edge", "q", "answered_by", "reply"],
        ],
    }


def _r_ask_impotent_reply():
    return {
        "name": "ax_ask_impotent_reply",
        "comment": (
            "A23 -- closes `ax_ask_impotent`'s own open ArcQuestion when an "
            "interlocutor Message responds to it.  Deliberately does NOT mint "
            "a GoalResidual/testimony (candidate (a) only, not (b) -- AR23b): "
            "this rule only marks the class-scoped question answered, so "
            "`ax_ask_impotent`'s own mint-once guard (keyed to the SAME av "
            "node) has a stable, observable 'already asked' fact regardless "
            "of whether the reply itself ever changes VALUE ranking -- it "
            "never will, by this rule's own design.  Matched by TYPE "
            "(ArcImpotenceQuestion, not ArcQuestion -- see ax_ask_impotent's "
            "own comment for why the type is distinct) AND by the SAME edge "
            "its guard reads (asked_about_verdict), so an ordinary ag_ask "
            "value-tie question's reply is untouched by this rule, and this "
            "rule cannot fire on anything ag_ask minted."),
        "batch": True,
        "match": [["m", "responds_to", "q"]],
        "where": AND(
            EQ({"type": "TypeOf", "node": V("q")}, L("ArcImpotenceQuestion")),
            NOT(EQ(A(V("m"), "from"), L("agent"))),
            NOT(EQ(A(V("q"), "answered"), L(1.0))),
            EXISTS(NEIGH(V("q"), "asked_about_verdict"), "avx", L(True)),
        ),
        "effects": [
            ["set_attr", "q", "answered", 1.0],
            ["set_attr", "q", "status", "answered"],
            ["add_edge", "q", "answered_by", "m"],
        ],
    }


def _r_ask_impotent_testify():
    return {
        "name": "ax_ask_impotent_testify",
        "comment": (
            "A24 -- THE REPLY SIDE, AND IT IS CLASS-SCOPED BY kind, NOT A "
            "gr_move_penalty REUSE (PROGRAM_SYNTHESIS_ARC6_PREREG.md amendment "
            "A24's own design investigation).  gr_move_penalty's own MATCH "
            "(tools/build_goal_residual_seed.py) refuses any candidate with a "
            "null sig_seam UNCONDITIONALLY, before any of a residual's own "
            "wildcards are even read -- and every goal this pool has EVER "
            "named nearest_unroutable_kind (decomposition_tier/supply_blocker/"
            "source_claim, A23 SS2.3/SS4.2, already measured) is exactly the "
            "population that guard exists to exclude (A14 finding 1).  A "
            "GoalResidual minted here would be inert by construction, not "
            "merely mis-scoped, for every candidate this pool can ever "
            "contain -- so this rule mints a DIFFERENT, DISTINCT node type, "
            "ArcImpotenceTestimony, keyed by kind (the SAME class dimension "
            "ax_ask_impotent already copied onto ArcImpotenceQuestion.region "
            "at ask time), and touches NEITHER gr_move_penalty/MATCH/PENALTY "
            "NOR AG-2's VALUE formula -- zero changes to any Term three "
            "seeds already depend on for unrelated, already-measured "
            "properties. "
            "NO WEIGHT FIELD, ON PURPOSE (CLAUDE.md's SHAPES-not-numbers "
            "standing rule, 2026-08-06/07): nothing downstream reads a "
            "class-scoped testimony weight today, and authoring one anyway "
            "would be the exact 'scalar knob with no reader' anti-pattern "
            "that rule names.  The record is DESCRIPTIVE -- kind, which "
            "specific goal was nearest-ranked at ask time (agid_a), and the "
            "scope the reply itself named (scope, a structured field the "
            "reply's own Message carries, set the SAME way cond_kind already "
            "is on ag_reply_mints_testimony_conditioned -- mechanical "
            "translation of an external form, never parsed from the reply "
            "text; defaults to 'unspecified' when the field is absent). "
            "LAPSES THROUGH THE EXISTING, TYPE-AGNOSTIC gr_condition_lapse/"
            "gr_condition_hold, UNMODIFIED: a holds_under edge to a "
            "fact_equals(arc_measure_epoch) ResidualCondition, the SAME "
            "'expires at the next measurement' idiom every other testimony "
            "in this tree already uses -- zero new lapse mechanism. "
            "MINT-ONCE PER QUESTION, the cheapest guard this engine has: "
            "Not(Exists(Neigh(q, mints_testimony))), self-extinguishing, the "
            "SAME shape ax_ask_impotent's own re-entry gate uses one level "
            "up.  Matched by TYPE (ArcImpotenceQuestion) AND by the base "
            "reply guard ax_ask_impotent_reply already uses, so this rule "
            "cannot fire on an ordinary ag_ask value-tie question's reply. "
            "ax_ask_impotent_reply ITSELF IS BYTE-UNCHANGED by this rule -- "
            "it still only marks the question answered; this is a SEPARATE, "
            "additive rule reading the SAME reply edge, not an edit to A23's "
            "own rule, so A23's own 'this rule only asks, it does not "
            "reprice' statement about ax_ask_impotent_reply stays literally "
            "true."),
        "batch": True,
        "match": [["m", "responds_to", "q"]],
        "where": AND(
            EQ({"type": "TypeOf", "node": V("q")}, L("ArcImpotenceQuestion")),
            NOT(EQ(A(V("m"), "from"), L("agent"))),
            NOT(EXISTS(NEIGH(V("q"), "mints_testimony"), "qtx", L(True))),
        ),
        "effects": [
            ["add_node", "t", "ArcImpotenceTestimony", {
                "kind": T(A(V("q"), "region")),
                "agid_a": T(A(V("q"), "agid_a")),
                "scope": T(ITE(EQ(A(V("m"), "impotence_scope"), L(None)),
                               L("unspecified"),
                               A(V("m"), "impotence_scope"))),
                "asked_epoch": T(A(V("q"), "asked_epoch")),
                "reply_epoch": T(MEASURE_EPOCH()),
                "evidence_kind": "utterance",
                "reach_class": "testimony",
                "stale": 0.0,
                "_no_weight_by_design": (
                    "SHAPES-not-numbers (CLAUDE.md 2026-08-06/07): no rule in "
                    "this tree reads a class-scoped testimony weight yet, so "
                    "none is authored here -- a future consumer can add one "
                    "when it exists to read it."),
            }],
            ["add_edge", "q", "mints_testimony", "t"],
            ["add_node", "cond", "ResidualCondition", {
                "rid": T(SCAT(L("arc.impotence_testimony."), A(V("q"), "region"))),
                "ckind": "fact_equals",
                "filter_value": "arc_measure_epoch",
                "expected_str": T(MEASURE_EPOCH()),
                "why": ("expires at the next measurement -- the SAME "
                        "'unconditioned testimony' idiom ag_reply_mints_"
                        "testimony_unconditioned already ships."),
            }],
            ["add_edge", "t", "holds_under", "cond"],
        ],
    }


def _rules():
    return [_r_dispatch(), _r_retired_epoch(), _r_rearm(), _r_close(),
            _r_impotent(), _r_world_probe_epoch(), _r_fallback_silent(),
            _r_fallback_cleared(), _r_ask_divergence_active(),
            _r_ask_divergence_cleared(), _r_impotent_pool_lapse(),
            _r_impotent_pool_hold(), _r_ask_impotent(), _r_ask_impotent_reply(),
            _r_ask_impotent_testify()]


def build():
    return {
        "_GENERATED_BY": "tools/build_arc_executor_seed.py",
        "_REGENERATION_IS_GATED_BYTE_IDENTICAL": (
            "tests/test_arc_executor_migrated.py::test_ex6_the_seed_"
            "REGENERATES_byte_identically re-runs this builder and diffs.  The "
            "Term idioms are IMPORTED from tools/build_arc_goals_seed.py, so if "
            "MEASURE_EPOCH or the pool predicate ever changes there, this seed "
            "goes out of date LOUDLY instead of silently diverging."),
        "self_load_only": True,
        "_SELF_LOAD_ONLY_RATIONALE": (
            "substrate/boot_all.py::_read_seeds GLOBS seeds/*.json and installs "
            "every match at boot, so a file here is live in EVERY agent in the "
            "tree the moment it lands.  seeds/arc_goals.json and "
            "seeds/arc_magnitude.json both ship self_load_only for that reason "
            "and this seed keeps the gating: an executor that dispatches jobs "
            "is the LAST thing that should arrive in every agent by a glob.  "
            "Activation is one key and a paired tree-wide sweep."),
        "id": "arc_executor",
        "version": "1.9.0",
        "depends_on": ["goal_residuals", "arc_goals"],
        "_SOFT_DEPENDENCY_ON_arc_magnitude": (
            "v1.1.0 (A11/WH1) wires ax_dispatch to the ORDER-N collapse "
            "(mg_sel_agid, seeds/arc_magnitude.json) when that collapse is live "
            "on the graph, and to the order-1 collapse (arc_sel_agid) when it "
            "is not.  arc_magnitude is DELIBERATELY NOT in depends_on: it is "
            "self_load_only, every EX1-EX6 scene boots without it, and making "
            "it hard would both change what those scenes boot and put an "
            "order-N collapse into every graph that merely wants hands.  The "
            "branch is a Term in the rule (SEL_AGID), never a Python "
            "conditional, and the order records which branch it took."),
        "description": (
            "AG-5 -- THE EXECUTOR AND THE STATUS LIFECYCLE.  Two independent "
            "rungs converged on this as the blocker: the arc-goal rung called "
            "itself 'a planning layer with no hands', and the magnitude rung "
            "found decomposition blocked because a parent goal must LEAVE THE "
            "POOL and nothing in this tree ever wrote a terminal status.  This "
            "seed is the missing seam, and it is four rules. "
            "ax_dispatch turns the arc-grain collapse's winner into an "
            "ExecOrder, routed by route_pick's own Argmin-over-cues shape, and "
            "is STRUCTURALLY INCAPABLE of ordering a goal whose kind has no "
            "ExecClass.  v1.1.0 (A11/WH1): the collapse it binds is the ORDER-N "
            "one (mg_sel_agid) whenever that collapse is live, falling back to "
            "order-1 (arc_sel_agid) when it is not -- because AG-5 SS8.9 "
            "measured that the two DISAGREE and that order-N picks the one goal "
            "the executor can run, with no human reply in the scene.  "
            "ax_retired_epoch stamps when a goal went terminal.  "
            "ax_rearm is the anti-oscillation latch: a retired goal re-enters "
            "the pool only when its source residual is genuinely stale again "
            "AND the measurement epoch has advanced.  ax_close makes a "
            "completed execution countable. "
            "THE EPOCH ITSELF: `arc_measure_epoch` was a counter with no "
            "producer, and every expiry mechanism in the two rungs below turns "
            "on it.  The adapter bumps it WHEN AND ONLY WHEN a measurement "
            "actually ran, so an unconditioned answer's one-epoch life is now "
            "measured in measurements. "
            "v1.2.0 (A13/WH4(c)) adds a fifth rule, ax_impotent: `ag_ask` fires "
            "on a TIE, and A11/A12 found the case it cannot see -- a non-empty "
            "pool in which NOTHING is routable, no tie anywhere, the loop "
            "stopping and saying nothing (WH2 SS3.1 iteration 1).  ax_impotent "
            "mints AgendaVerdict{kind:'impotent'} QUANTIFIED OVER THE WHOLE "
            "POOL (Not(Exists(POOL(), g, dispatchable(g))) -- dispatchable is "
            "ax_dispatch's OWN routability test, reused verbatim), never the "
            "winner alone, so a pool holding one routable goal ranked below "
            "the winner is correctly NOT impotent.  Mint-once is keyed on the "
            "pool's own SIGNATURE (its ordered agid list, JSON-encoded) rather "
            "than the tick, and the verdict lapses through the EXISTING, "
            "UNMODIFIED gr_condition_lapse via a fact_equals(arc_measure_epoch) "
            "condition -- zero new mechanism, zero new DSL Term. "
            "v1.3.0 (A15) adds a SECOND ExecClass row (local_id 4011): the "
            "structural-ceiling residual (arc6.structural.enum_op_table), "
            "re-measured by scripts/arc6_remeasure_structural.py.  ZERO new "
            "rules -- ax_dispatch/ROUTE/_routable/_dispatchable already filter "
            "over EVERY ExecClass node via the three-part key (kind + "
            "evidence_artifact + source_rid), so a second class is SEED DATA, "
            "not a rule edit.  This is the ceiling probe on the executor's own "
            "reach: A10-A14 each independently measured that reach as exactly "
            "ONE ExecClass; this is the second. "
            "v1.4.0 (A18) adds a SIXTH rule, ax_world_probe_epoch: EXECUTOR.md "
            "SS5 named, reported not patched, the re-arm DEADLOCK -- the epoch "
            "has exactly one producer (run_order, after RUNNING a measurement) "
            "and a retired goal cannot be run, so a genuinely re-failed "
            "condition on a retired goal could never bring it back on its "
            "own, and A15's own extension probe showed the natural end state "
            "of BOTH shipped ExecClasses retiring leaves ZERO executable pool "
            "members, not one -- the ordinary case, not a corner case.  "
            "ax_world_probe_epoch does not touch ax_rearm or its conjunction; "
            "it adds a SECOND, INDEPENDENT epoch producer that never runs "
            "anything: a retired goal whose condition is confirmed genuinely "
            "re-failed on TWO SEPARATE, externally-triggered probes (the "
            "adapter's refresh_evidence_facts, already existing, now carrying "
            "its own PRIOR reading across the probe-call boundary as "
            "stale_at_last_probe) while the epoch has sat still since its "
            "retirement gets `world_drift_confirmed` stamped; the adapter "
            "reads that as a pure query and bumps arc_measure_epoch the same "
            "mechanical way run_order does.  A SINGLE probe cannot satisfy "
            "the guard -- the discriminator against reintroducing the churn "
            "EX4 measured ax_rearm's own two-sided latch against. "
            "v1.5.0 (A19) adds a SEVENTH and EIGHTH rule, ax_fallback_silent "
            "and ax_fallback_cleared: WIRE_HANDS SS8.1 named, first on its "
            "own damage-ordered list, THE SILENT ORDER-N FALLBACK -- SEL_AGID "
            "reverting to order-1 when mg_sel_agid is absent is a deliberate, "
            "measured design (SS1.2, untouched by this rung), but nothing on "
            "the graph said so beyond a per-order breadcrumb (selected_by). "
            "THE FALLBACK ITSELF DOES NOT CHANGE.  ax_fallback_silent mints "
            "AgendaVerdict{kind:'order_n_fallback', active:1.0} the instant "
            "_order_n_is_not_live() holds -- the SAME Term SEL_AGID itself "
            "branches on, imported verbatim, never re-derived -- and no "
            "currently-active verdict of this kind already exists "
            "(ax_impotent's own mint-once shape).  ax_fallback_cleared flips "
            "`active` to 0.0 the instant order-N IS live: a DIRECT "
            "REVERSIBLE PAIR, the gr_condition_lapse/gr_condition_hold "
            "SHAPE, but keyed on the live Term rather than an epoch, because "
            "arc_magnitude can be loaded onto an ALREADY-RUNNING graph with "
            "no epoch bump anywhere in the scene (test_wh3_* vs test_wh1_* "
            "differ by exactly this).  Zero new DSL Term, zero new node "
            "type, zero new edge type (AgendaVerdict/has_agenda_verdict are "
            "already-declared productions), zero new adapter function -- "
            "agenda_verdicts(sub, 'order_n_fallback') is already generic. "
            "ax_dispatch/SEL_AGID/ARMED_AGID/ARMED_VALUE/COLLAPSE_NAME/"
            "_armed/ROUTE/_routable are BYTE-UNCHANGED: this rung only adds "
            "observability, it does not change when the fallback fires. "
            "v1.6.0 (A20) adds a NINTH and TENTH rule, ax_ask_divergence_"
            "active and ax_ask_divergence_cleared: the SAME direct-"
            "reversible-pair shape as A19, applied to a DIFFERENT question "
            "-- given that the order-N collapse IS live, does it name the "
            "SAME goal ag_ask asked about.  Mints/clears AgendaVerdict{kind:"
            "'ask_dispatch_divergence'} by comparing SEL_AGID() against "
            "arc_sel_agid, both stamps already read/written elsewhere.  ag_"
            "ask/seeds/arc_goals.json are BYTE-UNCHANGED. "
            "v1.7.0 (A21) adds an ELEVENTH and TWELFTH rule, ax_impotent_"
            "pool_lapse and ax_impotent_pool_hold: PROGRAM_SYNTHESIS_ARC6_"
            "IMPOTENCE_TERM.md SS8 item 1 / PROGRAM_SYNTHESIS_ARC6_"
            "IMPOTENCE_CAMPAIGN.md SS9 item 6 named the LAST originally-"
            "named remaining gap in this executor sub-thread -- an "
            "impotent verdict's condition lapses (gr_condition_lapse, "
            "unmodified) only on an EPOCH bump, never on the POOL'S OWN "
            "MEMBERSHIP moving under it within one epoch, so a reader had "
            "to compare pool_agids against the current pool by hand.  These "
            "two rules add a SECOND, ORTHOGONAL staleness axis "
            "(pool_stale) to each impotent verdict, keyed on the SAME "
            "_pool_sig() Term ax_impotent itself mints against, live, no "
            "epoch involved -- the A19/A20 direct-reversible-pair pattern, "
            "applied PER-NODE (not as a global singleton, which would have "
            "collapsed IM5's own multi-verdict history) rather than the "
            "epoch-shaped fact_equals idiom.  ax_impotent's OWN where/"
            "match/mint-once guard is BYTE-UNCHANGED (only its effects gain "
            "an additive pool_stale:0.0 stamp at mint), and gr_condition_"
            "lapse's closed MISMATCH vocabulary (seeds/goal_residuals.json) "
            "is BYTE-UNCHANGED and untouched by this rung. "
            "v1.8.0 (A23) adds a THIRTEENTH and FOURTEENTH rule, "
            "ax_ask_impotent and ax_ask_impotent_reply: candidate (a) "
            "(PROGRAM_SYNTHESIS_ARC6_IMPOTENCE_CAMPAIGN.md), built NATIVE, "
            "not as a naive reuse of ag_ask's own REGION-fallback re-entry "
            "gate (A22 SS6 named this the risk; A23's own design "
            "investigation confirms question_driver.py's gap-guard/contrast "
            "rules do not transfer to this data shape and costs more than "
            "the native alternative).  ax_ask_impotent asks a class-scoped "
            "question the instant a non-stale AgendaVerdict{kind:'impotent'} "
            "exists with no ArcQuestion asked about it yet -- mint-once by "
            "the VERDICT's own node identity (an InNeighbours edge-existence "
            "guard), the SAME shape ax_impotent itself already uses "
            "(pool-signature mint-once) and gap_awareness.json's content-"
            "dedup guard uses one seed over -- so a testimony chain that "
            "drifts nearest_unroutable_agid across several kinds within one "
            "epoch (A22 SS3, already measured) is still asked about EXACTLY "
            "ONCE, because it is still the SAME pool state throughout (A14's "
            "own headline finding).  ax_impotent/ag_ask/ROUTE/_routable/"
            "_dispatchable are BYTE-UNCHANGED: this rule only reads an "
            "existing AgendaVerdict, it does not change when one mints. "
            "Mints no GoalResidual/testimony (candidate (b) territory, "
            "already NO-GO'd by A22) -- ax_ask_impotent_reply only marks the "
            "question answered. "
            "v1.9.0 (A24) adds a FIFTEENTH rule, ax_ask_impotent_testify: "
            "the reply side.  A design investigation (PROGRAM_SYNTHESIS_"
            "ARC6_PREREG.md amendment A24) found gr_move_penalty's own MATCH "
            "guard refuses every candidate with a null sig_seam "
            "unconditionally -- and every kind this pool has ever named "
            "nearest_unroutable_kind is exactly that unsignatured "
            "population (A23 SS2.3/SS4.2), so a GoalResidual minted here "
            "would be inert by construction, not merely the wrong grain.  "
            "ax_ask_impotent_testify therefore mints a DISTINCT node type, "
            "ArcImpotenceTestimony, class-scoped by kind (the SAME class "
            "dimension ax_ask_impotent already copies onto "
            "ArcImpotenceQuestion.region), with NO weight field (SHAPES-"
            "not-numbers, CLAUDE.md 2026-08-06/07 -- nothing downstream "
            "reads one yet), lapsing through the EXISTING, UNMODIFIED "
            "gr_condition_lapse.  gr_move_penalty/MATCH/PENALTY, AG-2's "
            "VALUE, ax_ask_impotent, and ax_ask_impotent_reply are ALL "
            "BYTE-UNCHANGED by this rule."),
        "microtheory": "arc6_executor",
        "nodes": _nodes(),
        "edges": _edges(),
        "productions": _productions(),
        "rules": _rules(),
    }


def main() -> None:
    doc = build()
    text = json.dumps(doc, indent=2, sort_keys=False) + "\n"
    if "--check" in sys.argv:
        cur = open(OUT).read() if os.path.exists(OUT) else ""
        if cur != text:
            raise SystemExit("seeds/arc_executor.json is OUT OF DATE — re-run "
                             "tools/build_arc_executor_seed.py")
        print("up to date")
        return
    with open(OUT, "w") as fh:
        fh.write(text)
    print("wrote", OUT, "(%d bytes, %d rules)" % (len(text), len(doc["rules"])))


if __name__ == "__main__":
    main()
