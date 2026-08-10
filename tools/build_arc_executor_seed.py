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
    NEIGH, NOT, NOT_, ONE_OF, OR, PLUS, POOL, STR, T, V,
)

OUT = os.path.join(ROOT, "seeds", "arc_executor.json")

RUNNER = "arc6_remeasure_row_verdict"
EXECUTABLE_KIND = "re_measure"
ARTIFACT = "results/arc6_verdict_pricing.json"
SOURCE_RID = "arc6.verdict.row_verdict_seed_only"

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
            "collapse is live) and is never read by the firing guard."),
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
                "ExecClass cue exists.  There is ONE, and the dispatch route is "
                "an Argmin over the cues matching the goal's kind -- so a "
                "supply_blocker / source_claim / self_concern winner routes to "
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
                "THE ONE EXECUTABLE CLASS.  A re-measurement goal names an "
                "artifact, a condition and a denominator, and the measurement "
                "it asks for ALREADY EXISTS AS A SCRIPT -- so executing it is "
                "re-running that script on the current binary, which is "
                "mechanical I/O.  The other seven goals on the shipped agenda "
                "come from seam A's measured blocker split and from claims "
                "with no artifact: they require BUILDING something, and "
                "nothing here can do that."),
            "_runner_is_a_NAME_not_a_command": (
                "The adapter resolves this name against a frozen capability "
                "table.  A name with no table entry is REFUSED and recorded; "
                "the string is never a path, never an argv and never a shell "
                "word."),
        }},
    ]


def _edges():
    return [{"src": {"local": 4000}, "tgt": {"local": 4010},
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


def _rules():
    return [_r_dispatch(), _r_retired_epoch(), _r_rearm(), _r_close(),
            _r_impotent()]


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
        "version": "1.2.0",
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
            "condition -- zero new mechanism, zero new DSL Term."),
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
