#!/usr/bin/env python3
"""Generate the general control-regime escalation seed.

The metastability gap, observed twice in one week (docs/
metastable_regime_escalation.md): a controller relates to a metastable
condition only through evidence events that occur INSIDE it, so it can
neither notice it is chasing a fixed point that does not exist (F-16
jammed rudder: no zero-sideslip equilibrium, divergence at the 100 s
horizon) nor that it is trapped in a fixed point that is not the goal
(humanoid epochs 16-18: standing while commanding the running attractor,
three byte-identical inert episodes because no support-cycle event ever
fires a learning channel).

This seed is the general half of the fix, mirroring impasse_escalation's
order-N ladder at the control grain: EXPECTED-EVIDENCE ABSENCE IS A
FIRST-CLASS RESIDUAL.  v3.0.0 corrects the design docs/
regime_pareto_frontier_prereg.md names exactly: a measured negative
(four architectures, n=100 x 100 s) traced every failure to WHAT THERE
WAS TO DECIDE BETWEEN, not WHEN TO DECIDE.  Regime selection is a
PARETO FRONTIER over Pareto-INCOMPARABLE regimes, not a total-order
ladder: `regime_ordinal` is an IDENTIFIER a consumer's candidates
declare, never a rung position, and the collapse that used to publish
an Argmax over per-rung "support" scalars (the smuggled winner-selection
score `docs/embodied_pareto_profiles.md` forbids) now REUSES the shared
`embodied_pareto_profile` primitive's relational dominance and adds only
an EXPLICIT, declared selection policy over whatever survives it.

Contract (attrs on any node reachable by agent -holds_control_regime->):

  regime_monitor_enabled          0/1 -- the whole mechanism is opt-in.
  regime_clock_seq                stamped by the world adapter each
                                  action (mechanical clock mirror).
  regime_evidence_seq             bumped BY DOMAIN RULES whenever the
                                  active regime's promised evidence is
                                  observed (progress, cycle completion,
                                  band entry -- the domain decides what
                                  counts; this seed only reads absence).
  regime_evidence_horizon_actions the absence-integral level (in
                                  urgency-1 action equivalents) at which
                                  the residual is minted; consumers
                                  derive it from their own declared
                                  time constants, never a bare duration.
  regime_urgency                  OPTIONAL dimensionless divergence
                                  measure written by the consumer (its
                                  current error over its own best);
                                  absent -> 1.0 (fixed-horizon
                                  semantics).
  regime_absence_integral         urgency-weighted evidence-less time,
                                  maintained by this seed.
  regime_absence_seq              integrator clock guard.
  regime_ordinal                  the IDENTIFIER of the regime currently
                                  held.  NOT a ladder position: a
                                  consumer's declared regimes are
                                  Pareto-INCOMPARABLE corners (each
                                  surrenders a different objective), so
                                  ordinals are opaque labels a
                                  Pareto-candidate's `candidate_regime_
                                  ordinal` attr proposes and this seed
                                  copies onto the regime verbatim -- no
                                  Max, no climb, no order relation is
                                  assumed between two ordinals.
  regime_max_ordinal              informational ceiling: which regime
                                  identifiers a consumer has declared
                                  AVAILABLE this episode (a consumer's
                                  own candidate-minting rules read it to
                                  decide whether to propose a given
                                  regime at all; this seed does not use
                                  it as an escalation stop condition --
                                  see `regime_terminal`).
  regime_terminal                 0/1, mirrored onto the regime from the
                                  SELECTED candidate's own
                                  `candidate_terminal` at publish time.
                                  Once set, absence integration and
                                  re-deliberation stop: some declared
                                  regimes are honestly terminal (no
                                  further flight-regime deliberation is
                                  meaningful), replacing the old
                                  `regime_ordinal < regime_max_ordinal`
                                  ladder-ceiling check now that ordinals
                                  carry no order.
  regime_pareto_dimension_count   consumer-declared axis count for the
                                  regime Pareto profile this seed mints
                                  fresh at every deliberation-open (pure
                                  bookkeeping -- no domain vocabulary,
                                  just a number the consumer supplies).
  regime_pareto_minted_seq        the clock at which the CURRENT
                                  deliberation's `EmbodiedParetoProfile`
                                  was minted; also stamped onto the
                                  profile node itself (`minted_seq`) so
                                  stale profiles from earlier
                                  deliberations in the same episode are
                                  never compared against fresh
                                  candidates -- each deliberation gets
                                  its own isolated coordinate system.
  regime_deliberating              1 while a higher-order collapse over
                                  the frontier is open; System 1 keeps
                                  flying the currently held regime the
                                  whole time (a TRIGGER, never an
                                  immediate switch).
  regime_deliberation_seq,
  regime_deliberation_opened_seq,
  regime_deliberation_integral    the deliberation's own urgency-weighted
                                  clock (v2.0.0 semantics, unchanged).
  regime_escalation_requested,
  regime_escalation_count,
  regime_last_escalation_seq,
  regime_last_verdict             telemetry (unchanged in spirit;
                                  `regime_escalation_count` now counts
                                  any regime CHANGE, not only an
                                  increase -- ordinals have no order to
                                  increase along).

Consumer's Pareto-candidate contract (any node reachable by
`profile -has_embodied_pareto_candidate-> candidate`, `profile` reached
via `regime -deliberates_over_pareto_profile-> profile`): the shared
`embodied_pareto_profile` primitive owns `has_embodied_pareto_value`,
`dominates_embodied_pareto_candidate`, `is_dominated_by_embodied_candidate`
and the `dominated` flag -- REUSED verbatim, never reimplemented here.
Two additional attrs are this seed's own selection contract, always on
the candidate node:

  candidate_regime_ordinal        the regime identifier this candidate
                                  represents; copied onto `regime_ordinal`
                                  verbatim if this candidate is selected.
  candidate_terminal               0/1, copied onto `regime_terminal` if
                                  selected.
  regime_situational_priority_value  the candidate's OWN achievable-margin
                                  value on WHICHEVER axis the current
                                  situation prioritises (terrain
                                  proximity favours the altitude axis,
                                  low airspeed favours the speed axis,
                                  etc.) -- the consumer decides which
                                  axis and writes the readout at mint
                                  time.  This is the EXPLICIT, declared
                                  selection policy `docs/
                                  embodied_pareto_profiles.md` requires:
                                  it never enters dominance (candidates
                                  dominate purely on their real
                                  multi-axis values), it is a single
                                  declared axis's own reading, never a
                                  weighted sum across axes, and the
                                  general seed only uses it to break
                                  ties AMONG the frontier the primitive
                                  already computed.

Publication (`cre_publish_regime_pareto_verdict`): among the current
deliberation's frontier candidates (no `dominated` flag), the one with
the greatest `regime_situational_priority_value` is selected -- decisive
immediately when that value is unambiguous (> 1.0, its own precondition
exceeded twofold: the same "reflex and deliberation are one process at
different depths" property v2.0.0 established), else at the window
backstop.  A consumer that opens a deliberation and mints no candidates
never publishes (an honest liveness requirement on the consumer, not a
silent auto-HOLD default): every consumer using this seed's soft-realtime
path must mint at least the "stay as I am" candidate alongside any
alternatives.

The rung SEMANTICS (what each candidate ordinal means -- e.g. the F-16's
metastable sideslip trim, the steady orbit, speed priority, roll
priority) and the achievable-margin FORMULAS live in consumer seeds
keyed on the ordinal.  Honest residual: escalation is no longer forced
one-way within an episode (a re-deliberation can select ANY frontier
member, including one closer to the fixed point, if the freshly measured
axes say conditions genuinely improved) -- this closes the v2.0.0
"no de-escalation" residual as a side effect of ordinals losing their
order, but it is unguarded against oscillation; nothing here has
measured whether that matters.

v6.0.0 -- HOW LONG UNTIL THE FIXPOINT IS GONE, AND HOW LONG UNTIL I CAN NO
LONGER DO ANYTHING ABOUT IT.

A fault does not sort a plant into parameter / stability / kind.  A
destabilised fixpoint is a KIND CHANGE THAT HAS NOT FINISHED HAPPENING YET,
and its onset timescale is set by the environment -- gust energy, the size
of the commanded manoeuvre, how long the episode runs -- not by the fault
alone.  THE SAME FAULT IS A DIFFERENT "CLASS" IN DIFFERENT CONDITIONS.  So
the plant is in one of two states, and everything in between is a TIME:

  T_transition  actions until the held regime's fixpoint is no longer
                attainable.
  T_option      actions until the ESCAPE from that regime is no longer
                available.

The gate fires on MIN of the two, because a projection of the first alone is
accurate and useless once the second has expired.  Both are minted in the
same integer action quanta everything else in this line uses, with the
consumer's declared horizon as an honest ceiling; both are projected FROM
THE TRAJECTORY by the SAME held order-N recursion the consumer runs on its
own margins, applied one level up to the streams of what that recursion
measured; and both are computed whether or not a deliberation is open,
because a projected time is only worth having if it arrives BEFORE the basin
collapses, while the authority to act still exists.

THE RESPONSE SET IS THREE REGIONS OF THAT ONE QUANTITY, not three classes,
and both boundaries are declared quantities rather than picked ones (ZERO is
the integer lattice's origin the operator projects to; the control horizon is
`regime_evidence_horizon_actions`, the loop's own slow time constant, which
this contract already declared):

  acting clock at or below zero      the fixpoint is GONE -- the full corner
                                     set is admissible, and surrendering an
                                     objective is the honest response to an
                                     objective that no longer exists.
  acting clock inside the horizon    a transition is COMING -- only a
                                     candidate that CHANGES THE OPERATING
                                     CONDITION so the fixpoint stays
                                     attainable (`candidate_restores_basin`)
                                     may be published.  Moving the plant to
                                     where the basin is bigger is not the
                                     same act as giving up an objective, and
                                     it is the one that is still cheap.
  acting clock beyond the horizon    RECALIBRATE.  "Never transitions" and
                                     "transitions beyond anything I can plan
                                     over" are the same response; which one
                                     it was is recorded in the minted time,
                                     not in a second route.

Measured consequence of not having this dimension
(docs/regime_pareto_frontier_results.md, block 3): 26 of 27 jammed-rudder
crashes ended on a corner that surrendered altitude, because the frontier
was being asked "what should I give up" at moments when the answer was
"nothing yet -- move".

Channel contract (any node reachable by `regime -has_regime_channel->`):

  channel_crossing        integer actions until this channel's own objective
                          is unattainable, projected by the consumer's own
                          held recursion at the MEASURED ORDER of that
                          margin's trajectory, and shifted so that ZERO
                          means the floor has been reached.
  channel_option_crossing integer actions until the ESCAPE this channel
                          funds is no longer available, same units, same
                          convention.  An option's expiry is a property of
                          the CURRENT STATE, never of the fault, so it is
                          projected from the trajectory exactly as the
                          transition is -- never read off a table.  A
                          channel that funds no escape publishes the
                          horizon.
  channel_sample_seq      the consumer's ACTION clock at which both were
                          stamped.  Differencing it is the one conversion
                          between the sample grain and the action grain,
                          and it is measured, not declared.
  channel_horizon         the consumer's declared saturation -- "beyond what
                          I can see".
Budget contract (declared by the OPERATOR on the regime):

  regime_viability_rung   published by the consumer: the highest viability
                          limit that still holds, on whatever ladder it
                          defines.  Higher is better; 0 is "nothing holds".
  regime_information_worth_log
                          declared by the operator: what KNOWING is worth, in
                          the same units.  Spending to find out which limits
                          still hold is a DIFFERENT PURCHASE from spending to
                          achieve the objective, and charging both to one
                          account is measurably wrong: with a single worth of
                          zero the loop stopped probing the moment viability
                          dipped, and a scenario that survived BY probing
                          stopped surviving (§92).  A mission worth no airframe
                          may still be worth the fuel to find out whether it
                          has one.  **Absent reads 0.**
  regime_goal_worth_log   declared by the operator: what this goal is worth, in
                          LOG-IRREVERSIBILITY.  The body is a budget spent in
                          service of a goal, not a constraint to be preserved,
                          so what may be spent is not a property of the body
                          and nothing inside the loop can supply it.
                          **Absent reads 0: spend nothing, preserve
                          everything** -- exactly what every consumer does
                          today.
  regime_rung_decade      declared by the operator: how many log units separate
                          ADJACENT rungs, i.e. how much more permanent each
                          loss is than the one below it.  This is the whole
                          value declaration and it is a RATIO, not a threshold
                          -- the ordering is logarithmic because nothing is
                          infinitely valuable: a pilot is orders of magnitude
                          above an airframe, and a goal of sufficient wider
                          impact still exceeds a pilot, because breadth
                          accumulates on the same scale.
                          **Absent or non-positive reads "spend nothing"**, so
                          an operator who declares no ratios authorises no
                          trades.

  Lexicographic ordering is the wrong model and is what absence degrades to
  SAFELY, not correctly: it makes the top rung infinitely valuable and forbids
  every trade across it.  Declaring the decade is what makes the trade
  available and merely expensive.

  The loop publishes `regime_spend_floor` -- the lowest rung it is authorised
  to end at -- and never descends below it deliberately.  A goal worth nothing
  authorises nothing; a goal worth the airframe authorises the airframe.

Region contract (any node reachable by `regime -has_regime_region-> region`):

  region_axis_ordinal     which channel this region is expressed on; it is
                          matched against `channel_axis_ordinal`.
  region_gap              the consumer's measured distance to the region, in
                          the same units as that channel's rate.  Zero or
                          negative means already inside it.
  region_sense            +1 a region to REACH, -1 a region to AVOID.  The
                          arithmetic is identical either way -- reaching a goal
                          and being reached BY a threat are the same closure
                          -- and the sense only says whether the number that
                          comes out is an opportunity or a deadline.

  A consumer that declares no regions gets no rule firings and is unchanged.
  Landing envelopes, ejection windows and incoming threats are all one
  declaration: a region, a distance to it, and which way you want it to go.

  channel_rate_measured   OPTIONAL.  The measured rate at which this channel
                          is losing its objective, in the consumer's own
                          units.  Absent means "not measured", never zero.
  channel_authority_measured
                          OPTIONAL.  The measured authority that OPPOSES that
                          loss, in the SAME units -- what the effectors have
                          actually demonstrated they can do about it, not what
                          they are specified to do.  Publishing both earns the
                          channel a second projection (below); publishing
                          neither leaves it exactly as it was.
  channel_history_window  optional bound on the memory, floored at 4.
  channel_transition_history,
  channel_option_history,
  channel_history_seq,
  channel_sample_spacing  maintained by this seed.
  channel_actions_to_transition,
  channel_actions_to_option_loss,
  channel_projected_seq   this seed's per-channel verdicts.

  channel_reserve_actions   OPTIONAL.  The consumer's own MEASURED reading of
                          the STOCK that funds this channel's escape, in the
                          same integer action quanta: how many more actions of
                          escape the stock it can see will pay for.
  channel_reserve_measured  0/1.  Is the above a measurement?  A consumer whose
                          plant exposes no stock at all publishes neither.
  channel_reserve_ceiling   OPTIONAL finite bound to start from; absent, the
                          channel's own declared horizon is used, which is
                          finite by construction.
  channel_reserve_held,
  channel_reserve_initialised,
  channel_reserve_seq       maintained by this seed.

v7.0.0 -- UNKNOWN IS NOT UNBOUNDED, AND AN UNMEASURED STOCK IS NOT AN INFINITE
ONE.

The mechanical half of a plant's state is not the whole ledger.  Something is
SPENT to keep a fixpoint attainable, that something comes out of a finite
stock, and the stock does not refill.  A monitor that tracks only the
mechanical half will watch its own margin recover after every excursion and
conclude the admissible set grew -- which is what happened, measured, in
docs/regime_pareto_frontier_results.md's block C: the energy option clock left
its ceiling and returned 5-45 times per fault episode, because thrust was being
read as free energy.

So the projected option is now the minimum of what the TRAJECTORY says and what
the RESERVE says, and the reserve obeys ONE law: it never rises.

  * A consumer that MEASURES its stock publishes `channel_reserve_actions` and
    `channel_reserve_measured = 1`, and the held bound REFINES to it -- by
    minimum, so a plant that reports more than it did before (a mis-read, a
    refuelling, a re-scaled sensor) never buys the agent an option it had
    already spent.
  * A consumer that measures NOTHING publishes nothing, and the held bound
    still falls -- by the measured sample spacing, one action of reserve per
    action of flight.  This is the whole point and it is not optional.  An
    unmeasured tank treated as infinite is an ASSERTION, not a withheld
    judgement; physics has limits and they are known even where they are not
    instrumented.  This is the same first-class-absence discipline the frontier
    uses at the opposite corner: there the graph stores that the sequence does
    NOT end, and here it stores that it DOES, even when it cannot see where.

The ceiling an unmeasured reserve starts from is the channel's own declared
horizon -- "beyond what I can see" -- which is finite, so the bound is finite
from the first action and monotone from then on.  No consumer is required to
publish anything for that to hold.

Regime-level contract attrs:

  regime_actions_to_transition,
  regime_actions_to_option_loss,
  regime_actions_to_act           the minima over channels, and their own
                                  minimum -- the quantity the gate reads.
  regime_reserve_actions          the minimum held reserve over channels;
                                  telemetry, and the quantity that makes the
                                  price of a basin-restoring manoeuvre
                                  representable (see below).
  regime_kind_horizon_actions     the ceiling used when a regime declares no
                                  channels at all.
  regime_class_gate_enabled       0/1, OPT-IN.  With it off the clocks are
                                  projected and minted but gate nothing, and
                                  this seed's behaviour is v4.0.0's exactly.
  regime_recalibration_requested  the clock at which "no transition inside
                                  the control horizon" asked the consumer to
                                  re-fit its model.  A rising edge; the
                                  consumer owns what recalibration means.

Candidate contract addition:

  candidate_restores_basin        0/1 on a Pareto candidate: this candidate
                                  changes the OPERATING CONDITION so the
                                  fixpoint stays attainable, rather than
                                  surrendering an objective.  A consumer
                                  declaring none of these will never publish
                                  a verdict inside the transition region,
                                  which is recorded as that consumer's gap.

RESTORING THE BASIN NOW HAS A PRICE, and it is representable without a single
new clause.  Moving the plant to where the basin is bigger is not free: it is
paid for out of the reserve, the one column that never refills.  Since
`regime_actions_to_act` is the MINIMUM of the transition clock and the option
clock, and the option clock is now itself bounded by the reserve, an exhausted
reserve drives the acting clock to zero -- and at zero the response is no
longer "restore the basin" but the full corner set.  So the admissible
response moves from restoring to surrendering EXACTLY when the stock that
would fund the restoration runs out.  The hypothesis this makes testable is
not "restore the basin" but "restore the basin WHILE THE FUEL TO DO IT
EXISTS", and an episode therefore contains a finite number of such manoeuvres.
Nothing here asserts that the manoeuvre works; it asserts only that its price
is on the ledger.

CLASSIFY BY TRAJECTORY, NEVER BY A POINT OR A POOLED SUMMARY.  Pooling to a
median destroyed exactly the separating information once already
(docs/regime_pareto_frontier_prereg.md, the FALSIFIED order-as-detector
prediction, and the superseded three-way sort after it).  No threshold on
any order VALUE appears anywhere in this seed.
"""
from __future__ import annotations

import json
from pathlib import Path

try:
    from scripts.gen_embodied_motor_program_seed import (
        And,
        Argmax,
        Eq,
        Exists,
        Filter,
        Gt,
        If,
        L,
        Lt,
        Max,
        Min,
        Minus,
        Neighbours,
        Not,
        Or,
        P0,
        Plus,
        T,
        Times,
        V,
    )
except ModuleNotFoundError:
    from gen_embodied_motor_program_seed import (
        And,
        Argmax,
        Eq,
        Exists,
        Filter,
        Gt,
        If,
        L,
        Lt,
        Max,
        Min,
        Minus,
        Neighbours,
        Not,
        Or,
        P0,
        Plus,
        T,
        Times,
        V,
    )


ROOT = Path(__file__).resolve().parents[1]


def MaxOver(source, var_name, value, default):
    return {
        "type": "MaxOver",
        "source": source,
        "var_name": var_name,
        "value": value,
        "default": default,
    }


def IDiv(a, b):
    return {"type": "IDiv", "a": a, "b": b}


def Div(a, b):
    """Real division -- a CROSS-FRAME map, never an in-frame coordinate.

    Every in-frame quantity this seed publishes is an integer count of
    actions, so a ratio only ever appears on the way to one and is floored
    back with `IDiv` before it is stored (the frame/continuum invariant in
    the root CLAUDE.md).
    """
    return {"type": "Div", "a": a, "b": b}


def Append(seq, item):
    return {"type": "Append", "seq": seq, "item": item}


def Count(source):
    return {"type": "Count", "source": source}


def ListDrop(list_, index):
    return {"type": "ListDrop", "list": list_, "index": index}


def MapList(source, var_name, value):
    return {"type": "MapList", "source": source, "var_name": var_name,
            "value": value}


def Vec(*items):
    return {"type": "Vec", "items": list(items)}


def Attr(var, key):
    """The RAW attr (never coerced to a number) -- a history LIST."""
    return {"type": "Attr", "node": V(var), "key": key}


# ── TWO CLOCKS, ONE OPERATOR, ONE LEVEL UP ───────────────────────────────
#
# STABILITY IS NOT A THIRD CLASS.  A destabilised fixpoint is a kind change
# that has not finished happening yet, and its onset timescale is set by the
# environment -- gust energy, the size of the commanded manoeuvre, how long
# the episode runs -- not by the fault alone.  Perturb a marginally-stable
# plant enough, or wait long enough, and the trajectory leaves the shrinking
# basin, at which point the fixpoint is gone FOR THAT TRAJECTORY.  So the
# plant is in one of two states -- it either still has an attainable fixpoint
# or it does not -- and everything in between is HOW LONG UNTIL IT DOES NOT.
# That is a TIME, in the same integer action quanta everything else in this
# line uses, and it is the same quantity the order-N projection machinery
# already computes, applied one level up.
#
# TWO clocks, and the second expires first:
#
#   T_transition  actions until the held regime's fixpoint is no longer
#                 attainable.
#   T_option      actions until the ESCAPE from that regime is no longer
#                 available.
#
# A projection of the first alone is accurate and useless once the second has
# expired -- fifty metres further into the storm drain the pond is exactly
# where you predicted and reversing is no longer possible.  Only T_option
# makes a projection ACTIONABLE rather than merely predictive, so the
# response gate fires on the MINIMUM of the two.  An option's expiry is a
# property of the CURRENT STATE, never of the fault, so it is projected from
# the trajectory exactly as the transition is.
#
# Both are read the same way, by the SAME held recursion the consumer runs on
# its own margins, applied to the streams of what that recursion measured --
# the move this substrate makes repeatedly (strokes to characters, regimes to
# cognition).  `robust` is set for the reason the consumer sets it: a real
# stream sampled into integer quanta never has an EXACTLY constant difference
# level at any depth, and the exact witness is right to floor there.
_CHANNEL_SAMPLE_TYPE = "ControlOrderSample"

# A walk bound, never an order cap -- and INERT by construction.  The
# deliberation-grain reading below never compares against this number: it is
# multiplied by the measured sample spacing and then MINIMISED against both
# the point reading and the consumer's own declared horizon, either of which
# is always the smaller.  Any sufficiently large value is byte-identical.
_CHANNEL_PROJECTION_HORIZON = 1024


def TimeInfer(sequence, field):
    return {
        "type": "TimeInfer",
        "sequence": sequence,
        "codebook_type": _CHANNEL_SAMPLE_TYPE,
        "max_b": 8,
        "max_steps": _CHANNEL_PROJECTION_HORIZON,
        "robust": True,
        "field": field,
    }


def _sample_frames(history_attr):
    """A scalar sample stream in the frame shape `TimeInfer` reads.

    One relation per sample, `("m", v)`, with slot 1 declared `coord:v` by
    the held `ControlOrderSample` part.  Nothing in the Term knows what the
    coordinate measures, or that the ordering is deliberations.
    """
    return MapList(Attr("channel", history_attr), "sample",
                   Vec(Vec(L("m"), V("sample"))))


def _projected_actions(point_attr, history_attr):
    """ONE clock, read at TWO grains and minimised -- no threshold anywhere.

      the POINT reading   `channel_<x>_crossing`: the actions this channel's
                          own margin has left, already projected by the
                          consumer at the MEASURED ORDER of that margin's
                          trajectory over its whole sample window.  It is a
                          trajectory reading at the ACTION grain, not a
                          point in the sense that matters.
      the SAMPLE reading  the same operator applied to the STREAM of those
                          projections: how many samples until the deadline
                          ITSELF reaches zero, converted to actions by the
                          measured spacing between samples.  This is the
                          reading that catches a deadline which is
                          comfortable at every single sample and collapsing
                          across them -- the identical argument the consumer
                          makes one level down ("the first difference says
                          plenty of time and the second says otherwise").

    The MINIMUM, because either arrival is arrival, and then capped at the
    consumer's own declared horizon so "beyond what I can see" is an honest
    ceiling rather than a fabricated number.

    No evidence guard is needed and none is written: below the recursion's
    own requirement (`robust_order_min` needs three difference samples) the
    fit floors, `crossing` returns its saturation value, the sample reading
    becomes enormous, and the minimum silently falls back to the point
    reading.  That IS the honest behaviour -- with no trajectory of
    projections yet, the projection you have is the one you use.
    """
    samples = TimeInfer(_sample_frames(history_attr), "crossing")
    spacing = Max(P0("channel", "channel_sample_spacing"), L(1.0))
    return Min(
        Max(P0("channel", "channel_horizon"), L(0.0)),
        Min(
            Max(P0("channel", point_attr), L(0.0)),
            Times(samples, spacing),
        ),
    )


def channel_sample_frame_node() -> dict:
    """The dim-typed part `TimeInfer` reads its coordinate slot from.

    Data, not a rule: one relation `("m", v)` whose slot 0 is the predicate
    and slot 1 the coordinate.  Declaring the frame as graph data is what
    keeps the recursion dimension-generic -- nothing in the Term knows what
    this coordinate measures or what indexes it.  A dedicated node type
    because `load_parts` takes `dim_types` from the FIRST part it finds of
    the named type, so sharing a type with any other consumer's codebook
    would make this seed's frame depend on which other seeds are loaded.
    """
    return {
        "local_id": 1,
        "type": _CHANNEL_SAMPLE_TYPE,
        "attrs": {
            "name": "control_regime_channel_sample",
            "signature": json.dumps([["m", 0]]),
            "kind": "faculty",
            "faculty": "control_regime_channel_sample",
            "dim_types": ["pred", "coord:v"],
        },
    }


def accumulate_channel_samples_rule() -> dict:
    """Mechanical accumulation: the classifier's memory of one channel.

    No decision -- the consumer publishes what its own held projection
    measured, and this appends it to a bounded stream and records how far
    apart the samples were.  Every value is floored to an integer because
    these are IN-FRAME coordinates (the frame/continuum invariant: a float
    here would be a category error; the continuous structure lives in the
    projection that produced them, which is a map between frames).

    The spacing is the consumer's own action clock differenced -- the ONE
    conversion between the sample grain and the action grain, taken from
    data the consumer already publishes rather than declared as a constant.
    """
    window = Max(P0("channel", "channel_history_window"), L(4.0))

    def bounded(history_attr, sample):
        grown = Append(Attr("channel", history_attr), sample)
        return If(Gt(Count(grown), window), ListDrop(grown, L(0.0)), grown)

    return {
        "name": "cre_accumulate_channel_samples",
        "area": "control_regime_escalation",
        "latency_class": "soft_realtime",
        "order": -49.8,
        "batch": False,
        "match": [
            ["agent", "holds_control_regime", "regime"],
            ["regime", "has_regime_channel", "channel"],
        ],
        "where": And(
            Gt(P0("regime", "regime_monitor_enabled"), L(0.5)),
            Gt(
                P0("channel", "channel_sample_seq"),
                P0("channel", "channel_history_seq"),
            ),
        ),
        "effects": [
            ["set_attr", "channel", "channel_transition_history", T(bounded(
                "channel_transition_history",
                IDiv(P0("channel", "channel_crossing"), L(1.0)),
            ))],
            ["set_attr", "channel", "channel_option_history", T(bounded(
                "channel_option_history",
                IDiv(P0("channel", "channel_option_crossing"), L(1.0)),
            ))],
            ["set_attr", "channel", "channel_sample_spacing", T(IDiv(Max(
                Minus(
                    P0("channel", "channel_sample_seq"),
                    P0("channel", "channel_history_seq"),
                ),
                L(1.0),
            ), L(1.0)))],
            ["set_attr", "channel", "channel_history_seq", T(
                P0("channel", "channel_sample_seq")
            )],
        ],
    }


def _reserve_ceiling():
    """The finite bound an unmeasured reserve starts from.

    A consumer may declare one; absent that it is the channel's own declared
    horizon, which is the honest "beyond what I can see" and is FINITE.  There
    is no branch here that yields an unbounded value, and that is deliberate.
    """
    return If(
        Gt(P0("channel", "channel_reserve_ceiling"), L(0.0)),
        P0("channel", "channel_reserve_ceiling"),
        Max(P0("channel", "channel_horizon"), L(1.0)),
    )


def _reserve_held():
    """The held bound, or the ceiling before the first ratchet has run."""
    return If(
        Gt(P0("channel", "channel_reserve_initialised"), L(0.5)),
        P0("channel", "channel_reserve_held"),
        _reserve_ceiling(),
    )


def ratchet_channel_reserve_rule() -> dict:
    """The reserve NEVER RISES, whether or not anyone is measuring it.

    Two branches, one law.  With a measurement the held bound refines to the
    smaller of what it held and what was measured -- so a plant that reports
    MORE stock than before never returns an option the agent had already
    spent.  With no measurement at all the bound simply falls by the measured
    sample spacing: one action of reserve per action of flight.

    The second branch is the point of this version.  It is not a placeholder
    for a real measurement and it is not a conservatism knob -- it is the
    refusal to assert that an uninstrumented stock is infinite.  A consumer
    that publishes real values gets a tighter bound; a consumer that publishes
    nothing still gets a monotone one, and no consumer is required to publish
    anything for the ledger to stay honest.

    Every value is floored to an integer: these are IN-FRAME coordinates on the
    same action lattice as both clocks.
    """
    held = _reserve_held()
    spend = Max(P0("channel", "channel_sample_spacing"), L(1.0))
    proposed = If(
        Gt(P0("channel", "channel_reserve_measured"), L(0.5)),
        Max(P0("channel", "channel_reserve_actions"), L(0.0)),
        Minus(held, spend),
    )
    return {
        "name": "cre_ratchet_channel_reserve",
        "area": "control_regime_escalation",
        "latency_class": "soft_realtime",
        "order": -49.75,
        "batch": False,
        "match": [
            ["agent", "holds_control_regime", "regime"],
            ["regime", "has_regime_channel", "channel"],
        ],
        "where": And(
            Gt(P0("regime", "regime_monitor_enabled"), L(0.5)),
            Gt(
                P0("channel", "channel_history_seq"),
                P0("channel", "channel_reserve_seq"),
            ),
        ),
        "effects": [
            ["set_attr", "channel", "channel_reserve_held", T(IDiv(
                Max(Min(held, proposed), L(0.0)), L(1.0)
            ))],
            ["set_attr", "channel", "channel_reserve_initialised", 1.0],
            ["set_attr", "channel", "channel_reserve_seq", T(
                P0("channel", "channel_history_seq")
            )],
        ],
    }


def project_channel_clocks_rule() -> dict:
    """Mint BOTH clocks for one channel, in integer action quanta.

    Runs on every accumulated sample and is NOT gated on a deliberation
    being open.  That is deliberate and it is the whole planning point:
    every escalation in this line so far has been REACTIVE -- wait for
    evidence to starve, then deliberate -- and a projected time is only
    worth having if it is available BEFORE the basin collapses, while the
    authority to act still exists.
    """
    return {
        "name": "cre_project_channel_clocks",
        "area": "control_regime_escalation",
        "latency_class": "soft_realtime",
        "order": -49.7,
        "batch": False,
        "match": [
            ["agent", "holds_control_regime", "regime"],
            ["regime", "has_regime_channel", "channel"],
        ],
        "where": And(
            Gt(P0("regime", "regime_monitor_enabled"), L(0.5)),
            Gt(
                P0("channel", "channel_history_seq"),
                P0("channel", "channel_projected_seq"),
            ),
        ),
        "effects": [
            ["set_attr", "channel", "channel_actions_to_transition", T(
                _projected_actions("channel_crossing",
                                   "channel_transition_history")
            )],
            # THE OPTION EXPIRES AT THE EARLIER OF TWO THINGS: the trajectory
            # carrying the escape's own margin to its floor, and the RESERVE
            # that funds the escape running out.  Block C measured only the
            # first and watched it recover after every excursion; the second is
            # monotone by construction, so the ledger the two of them form
            # cannot refill.
            ["set_attr", "channel", "channel_actions_to_option_loss", T(Min(
                _projected_actions("channel_option_crossing",
                                   "channel_option_history"),
                _reserve_held(),
            ))],
            ["set_attr", "channel", "channel_projected_seq", T(
                P0("channel", "channel_history_seq")
            )],
        ],
    }


def _min_over_channels(attr):
    return _min_over_channels_value(P0("chan", attr))


def _discounted_over_channels(attr):
    """The MIN over channels, RELATIVE rather than flat (v7.1.0).

    A flat `MIN` prices every declared objective identically: whichever channel
    reads lowest takes the whole regime's acting time, no matter what losing
    that channel would actually cost.  Measured on this line's own blocks, that
    is not a neutral choice, it is a wrong one — in healthy flight a commanded
    turn drives the SIDESLIP channel to its floor (a coordinated turn IS
    transient sideslip) and the flat minimum hands that reading authority over
    the regime, which is exactly the excursion that falsified the two-clock
    block; in a jammed rudder the HEADING channel pins it at zero on 0.89 of
    post-onset actions, and heading is the objective this line has established
    is cheap to abandon because heading is not energy.

    So a channel declares how much of its own loss is ALREADY PAID FOR
    ELSEWHERE in the ledger — `channel_surrender_discount` in [0, 1] — and the
    roll-up moves that channel's reading toward the horizon in proportion:

        weighted(channel) = clock + discount * (horizon - clock)

    A discount of 0 leaves the reading untouched.  A discount of 1 sends it to
    the horizon, so the channel never forces action on its own.  **P0 reads an
    absent attribute as ZERO, so a channel that declares no discount is priced
    in full and the roll-up is byte-identically the flat MIN it has always
    been** — a consumer that has never heard of this contract is unaffected,
    which is the only acceptable default for a general seed.

    The discount is NOT "this objective does not matter".  It is "the energy
    this objective's loss spends is counted in another channel's ledger, and
    counting it twice would let one spend speak with two voices."  That is why
    the funding channel — the one the option clock is projected from — is the
    channel that carries a discount of zero.

    Frame invariant: the clocks are IN-FRAME integer action quanta and the
    discount is a CROSS-FRAME ratio, so the weighted value is minted back onto
    the integer lattice before it is compared with anything.

    The OPTION roll-up is deliberately left flat.  Its channels declare an
    expiry only where they fund an escape, so its minimum is already taken over
    the channels that have a price; discounting it would be a second contract
    with no measurement behind it.
    """
    clock = P0("chan", attr)
    horizon = Max(P0("regime", "regime_kind_horizon_actions"), L(0.0))
    discount = Min(
        Max(P0("chan", "channel_surrender_discount"), L(0.0)), L(1.0)
    )
    return _min_over_channels_value(
        IDiv(Plus(clock, Times(discount, Minus(horizon, clock))), L(1.0))
    )


def _min_over_channels_value(value):
    return {
        "type": "MinOver",
        "source": Neighbours("regime", "has_regime_channel"),
        "var_name": "chan",
        "value": value,
        "default": Max(P0("regime", "regime_kind_horizon_actions"), L(0.0)),
    }


def _held_reserve_of(var):
    """The held reserve of a channel bound to `var` (see `_reserve_held`)."""
    return If(
        Gt(P0(var, "channel_reserve_initialised"), L(0.5)),
        P0(var, "channel_reserve_held"),
        If(
            Gt(P0(var, "channel_reserve_ceiling"), L(0.0)),
            P0(var, "channel_reserve_ceiling"),
            Max(P0(var, "channel_horizon"), L(1.0)),
        ),
    )


def publish_spend_authority_rule() -> dict:
    """What the operator has authorised spending, in rungs of viability.

    Every absolute bound in this line failed the same way (§80, §87): a limit
    was treated as a fact about the body when it is a PRICE.  "Do not exceed
    the structural envelope" is a quote, not a law -- exceeding it costs the
    airframe -- and whether that is worth paying depends on what the goal is
    worth, which is information the body does not have and cannot derive.

    So the budget is declared, not computed.  The consumer publishes which rung
    still holds; the operator declares how many rungs the goal is worth; this
    publishes the floor -- the lowest rung the loop is authorised to end at.

      spend floor = viability rung - (goal worth / rung decade), floored at 0

    The division is the log scale doing the work: each rung is `regime_rung_decade`
    log units more permanent than the one below, so a worth of two decades buys
    two rungs and a worth of half a decade buys none.  Nothing is infinitely
    valuable, and nothing is cheap by accident.

    A goal worth nothing authorises nothing and the loop preserves everything,
    which is what absent reads as and what every consumer does today.  A goal
    worth three rungs authorises spending the body to reach it.

    Nothing here decides anything: it publishes an authorisation a selection
    rule may consult.  The distinction matters -- the ladder makes prices
    legible, the operator sets the budget, and neither is allowed to be the
    other.
    """
    # Measured from the HIGH-WATER rung, not the current one: `rung - worth`
    # tracks the descent and can never be violated, which is a ratchet rather
    # than a budget.
    rung = Max(P0("regime", "regime_viability_rung"), L(0.0))
    high_water = Max(rung, P0("regime", "regime_rung_high_water"))
    # How many rungs the declared worth buys, on the log scale: worth divided
    # by the log distance between adjacent rungs.  A decade of zero or absent
    # buys nothing, which is the safe degradation to the lexicographic reading.
    decade = P0("regime", "regime_rung_decade")
    worth = If(
        Gt(decade, L(0.0)),
        IDiv(
            Max(P0("regime", "regime_goal_worth_log"), L(0.0)),
            decade,
        ),
        L(0.0),
    )
    info_worth = If(
        Gt(decade, L(0.0)),
        IDiv(
            Max(P0("regime", "regime_information_worth_log"), L(0.0)),
            decade,
        ),
        L(0.0),
    )
    return {
        "name": "cre_publish_spend_authority",
        "area": "control_regime_escalation",
        "latency_class": "soft_realtime",
        "order": -46.05,
        "batch": False,
        "match": [
            ["agent", "holds_control_regime", "regime"],
        ],
        "where": Gt(P0("regime", "regime_monitor_enabled"), L(0.5)),
        "effects": [
            ["set_attr", "regime", "regime_rung_high_water", T(high_water)],
            ["set_attr", "regime", "regime_spend_floor", T(
                Max(Minus(high_water, worth), L(0.0))
            )],
            ["set_attr", "regime", "regime_budget_exhausted", T(
                If(Lt(rung, Max(Minus(high_water, worth), L(0.0))),
                   L(1.0), L(0.0))
            )],
            # THE INFORMATION ACCOUNT -- the same arithmetic on a separate
            # declaration.  Two budgets, one scale.
            ["set_attr", "regime", "regime_info_spend_floor", T(
                Max(Minus(high_water, info_worth), L(0.0))
            )],
            ["set_attr", "regime", "regime_info_budget_exhausted", T(
                If(Lt(rung, Max(Minus(high_water, info_worth), L(0.0))),
                   L(1.0), L(0.0))
            )],
            # Is the loop currently authorised to spend anything at all?
            ["set_attr", "regime", "regime_spend_authorised", T(
                If(Gt(worth, L(0.0)), L(1.0), L(0.0))
            )],
            # The declared worth in rungs, so a trace shows what the operator
            # authorised and not merely what the loop did with it.
            ["set_attr", "regime", "regime_worth_in_rungs", T(worth)],
            ["set_attr", "regime", "regime_info_worth_in_rungs", T(info_worth)],
        ],
    }


def project_region_reachability_rule() -> dict:
    """How long until a declared region is reached -- by me, or by the threat.

    The manifold is bounded by regions to REACH and regions to AVOID, and both
    are the same computation.  `region_gap / channel_rate_measured` is the
    number of actions until the distance closes; whether that is an opportunity
    or a deadline is what `region_sense` records, and nothing here needs to know
    which.

    This is what a landing envelope, an ejection window and an incoming missile
    have in common: each is a region, a measured distance, and a direction you
    want that distance to go.  Nothing in the rule names an aircraft, a vehicle
    or a threat, and the same declaration serves a car approaching a collision
    or a joint approaching its stop.

    Published per region:

      region_actions          integer actions until the gap closes at the
                              measured rate -- the horizon when the gap is not
                              closing, since a region you are not approaching
                              is not on any clock;
      region_inside           1.0 when the gap is already closed.

    Nothing consumes these yet: they are the reach side of the viability ladder
    (docs/decision_making_spike.md §82, §84), and a consumer that declares no
    regions is byte-identical to before this existed.
    """
    def _magnitude(term):
        """|x| -- this generator defines no `Abs` helper."""
        return Max(term, Times(L(-1.0), term))

    gap = P0("region", "region_gap")
    rate = P0("channel", "channel_rate_measured")
    horizon = P0("channel", "channel_horizon")
    closing = Gt(Times(gap, rate), L(0.0))
    return {
        "name": "cre_project_region_reachability",
        "area": "control_regime_escalation",
        "latency_class": "soft_realtime",
        "order": -49.67,
        "batch": False,
        "match": [
            ["agent", "holds_control_regime", "regime"],
            ["regime", "has_regime_region", "region"],
            ["regime", "has_regime_channel", "channel"],
        ],
        "where": And(
            Gt(P0("regime", "regime_monitor_enabled"), L(0.5)),
            Eq(
                P0("region", "region_axis_ordinal"),
                P0("channel", "channel_axis_ordinal"),
            ),
        ),
        "effects": [
            ["set_attr", "region", "region_inside", T(
                If(Gt(gap, L(0.0)), L(0.0), L(1.0))
            )],
            ["set_attr", "region", "region_actions", T(IDiv(
                Min(
                    If(
                        closing,
                        Div(_magnitude(gap), Max(_magnitude(rate), L(0.000001))),
                        horizon,
                    ),
                    horizon,
                ),
                L(1.0),
            ))],
        ],
    }


def project_channel_assisted_clock_rule() -> dict:
    """A terminal channel is projected TWICE: with the authority that opposes
    its loss applied, and without.

    **A channel projected once cannot discriminate between options.**  Every
    candidate that reads it reads the same number, whatever authority each one
    declares it will spend, so the channel contributes nothing to a choice
    however urgent it becomes.  Measured on the consumer that exposed this: an
    attitude channel whose clock read 1 -- the objective a single action from
    being lost -- while the frontier was re-evaluated four times and returned
    HOLD every time, because that clock was identical across every candidate
    (docs/regime_pareto_frontier_results.md, blocks AB and AC).

    The channel that HAS two streams behaves differently for the same reason:
    an option that declares it will spend authority against the loss projects
    the assisted stream, one that declares it will not projects the raw one,
    and the difference between them is what makes the channel able to separate
    options at all.

    This is not a domain fact.  A wheel losing grip, a brake losing
    authority, a joint approaching its stop and a wing dropping are the same
    shape: something is being lost at a measured rate, and some effector has a
    measured ability to oppose it.  Both quantities come from the consumer --
    only IT knows what "rate" means in its world and which effectors act on
    which channel -- and both are MEASUREMENTS, so a plant that has lost the
    authority reports the two streams converging, which is the honest reading
    when nothing can be done.

    Publishing neither measurement leaves the channel exactly as it was, so
    every existing consumer is unaffected.
    """
    rate = P0("channel", "channel_rate_measured")
    authority = P0("channel", "channel_authority_measured")
    # What the loss rate becomes once the opposing authority is applied.
    # Floored, not clamped to zero: authority that exceeds the loss rate means
    # the objective is not being lost at all, which reads as the horizon.
    residual = Max(Minus(rate, authority), L(0.000001))
    raw = P0("channel", "channel_actions_to_transition")
    assisted = Times(raw, Div(Max(rate, L(0.000001)), residual))
    return {
        "name": "cre_project_channel_assisted_clock",
        "area": "control_regime_escalation",
        "latency_class": "soft_realtime",
        "order": -49.68,
        "batch": False,
        "match": [
            ["agent", "holds_control_regime", "regime"],
            ["regime", "has_regime_channel", "channel"],
        ],
        "where": And(
            Gt(P0("regime", "regime_monitor_enabled"), L(0.5)),
            # Absence of a measurement is not a measurement of zero.
            Gt(rate, L(0.0)),
        ),
        "effects": [
            ["set_attr", "channel", "channel_clock_assisted", T(
                IDiv(Min(assisted, P0("channel", "channel_horizon")), L(1.0))
            )],
        ],
    }


def project_regime_clocks_rule() -> dict:
    """Roll the per-channel clocks up to the regime, and take the minimum.

    `regime_actions_to_act` is the quantity the response gate reads, and it
    is MIN(T_transition, T_option) exactly as the storm-drain reading
    requires: the earliest of "this regime's fixpoint is gone" and "the
    escape from this regime is gone".  A projection of the first alone is
    accurate and useless once the second has expired.

    The three named regions are REGIONS OF THIS ONE QUANTITY, not
    categories, and both boundaries are declared quantities rather than
    picked ones: ZERO is the integer lattice's origin (the floor the
    operator projects to), and the control horizon is
    `regime_evidence_horizon_actions`, the loop's own slow time constant
    which this contract already declares.
    """
    return {
        "name": "cre_project_regime_clocks",
        "area": "control_regime_escalation",
        "latency_class": "soft_realtime",
        "order": -49.65,
        "batch": False,
        "match": [
            ["agent", "holds_control_regime", "regime"],
        ],
        "where": And(
            Gt(P0("regime", "regime_monitor_enabled"), L(0.5)),
            Gt(
                P0("regime", "regime_clock_seq"),
                P0("regime", "regime_clock_projection_seq"),
            ),
        ),
        "effects": [
            ["set_attr", "regime", "regime_actions_to_transition", T(
                _discounted_over_channels("channel_actions_to_transition")
            )],
            ["set_attr", "regime", "regime_actions_to_option_loss", T(
                _min_over_channels("channel_actions_to_option_loss")
            )],
            ["set_attr", "regime", "regime_actions_to_act", T(Min(
                _discounted_over_channels("channel_actions_to_transition"),
                _min_over_channels("channel_actions_to_option_loss"),
            ))],
            # The reserve, rolled up.  Telemetry only -- it has already done
            # its work inside each channel's own option clock -- but it is the
            # one column of the ledger that cannot refill, so it belongs where
            # a trace can read it.
            ["set_attr", "regime", "regime_reserve_actions", T(
                _min_over_channels_value(_held_reserve_of("chan"))
            )],
            ["set_attr", "regime", "regime_clock_projection_seq", T(
                P0("regime", "regime_clock_seq")
            )],
        ],
    }


def note_projected_transition_rule() -> dict:
    """The projection becomes graph data the agent HOLDS, once.

    Minted the first time the acting clock falls inside the declared control
    horizon -- the moment at which a transition (or the loss of the escape
    from it) is close enough to be this loop's business.  It carries BOTH
    clocks, so the record says which of the two is binding: a transition
    still far off with an option about to expire is a different situation
    from an imminent transition with the escape wide open, and the response
    to the first is to act NOW while acting is still possible.
    """
    return {
        "name": "cre_note_projected_transition",
        "area": "control_regime_escalation",
        "latency_class": "soft_realtime",
        "order": -49.6,
        "batch": False,
        "match": [
            ["agent", "holds_control_regime", "regime"],
        ],
        "where": And(
            Gt(P0("regime", "regime_monitor_enabled"), L(0.5)),
            Lt(
                P0("regime", "regime_actions_to_act"),
                P0("regime", "regime_evidence_horizon_actions"),
            ),
            Not(Gt(P0("regime", "regime_transition_noted"), L(0.5))),
        ),
        "effects": [
            ["add_node", "transition", "ControlRegimeTransition", {
                "kind": "projected_fixpoint_loss",
                "actions_to_transition": T(
                    P0("regime", "regime_actions_to_transition")
                ),
                "actions_to_option_loss": T(
                    P0("regime", "regime_actions_to_option_loss")
                ),
                "actions_to_act": T(P0("regime", "regime_actions_to_act")),
                "at_clock_seq": T(P0("regime", "regime_clock_seq")),
                "verified": 1.0,
            }],
            ["add_edge", "agent", "holds_regime_transition", "transition"],
            ["add_edge", "transition", "about_control_regime", "regime"],
            ["set_attr", "regime", "regime_transition_noted", 1.0],
        ],
    }


def _fixpoint_already_lost():
    return Not(Gt(P0("regime", "regime_actions_to_act"), L(0.0)))


def _transition_inside_control_horizon():
    return Lt(
        P0("regime", "regime_actions_to_act"),
        P0("regime", "regime_evidence_horizon_actions"),
    )


def route_no_projected_transition_rule() -> dict:
    """No transition inside the control horizon: RECALIBRATE.

    Whether the plant never transitions or transitions beyond anything this
    loop can plan over is the SAME response, and the difference between them
    is recorded in the minted time rather than in a second route.  There is
    no third class to invent here, and that is the point: the missing route
    the three-class reading kept running into was an artifact of the missing
    dimension.

    Ordered after the verdict so a published objective change always wins.
    """
    return {
        "name": "cre_route_no_projected_transition_to_recalibration",
        "area": "control_regime_escalation",
        "latency_class": "soft_realtime",
        "order": -48.9,
        "batch": False,
        "match": [
            ["agent", "holds_control_regime", "regime"],
        ],
        "where": And(
            Gt(P0("regime", "regime_class_gate_enabled"), L(0.5)),
            Gt(P0("regime", "regime_deliberating"), L(0.5)),
            Not(Lt(
                P0("regime", "regime_deliberation_integral"),
                P0("regime", "regime_evidence_horizon_actions"),
            )),
            Not(_transition_inside_control_horizon()),
        ),
        "effects": [
            ["set_attr", "regime", "regime_recalibration_requested", T(
                P0("regime", "regime_clock_seq")
            )],
            *_close_deliberation_effects(),
        ],
    }


def close_gated_deliberation_rule() -> dict:
    """A transition is projected and nothing on the frontier answers it.

    The consumer declared no candidate that CHANGES THE OPERATING CONDITION
    (`candidate_restores_basin`), so there is nothing to publish that would
    keep the fixpoint attainable, and surrendering an objective is not the
    response to a transition that has not happened.  Close honestly and
    record the gap as the consumer's, not as a missing class.
    """
    return {
        "name": "cre_close_gated_deliberation_without_verdict",
        "area": "control_regime_escalation",
        "latency_class": "soft_realtime",
        "order": -48.85,
        "batch": False,
        "match": [
            ["agent", "holds_control_regime", "regime"],
        ],
        "where": And(
            Gt(P0("regime", "regime_class_gate_enabled"), L(0.5)),
            Gt(P0("regime", "regime_deliberating"), L(0.5)),
            Not(Lt(
                P0("regime", "regime_deliberation_integral"),
                P0("regime", "regime_evidence_horizon_actions"),
            )),
            _transition_inside_control_horizon(),
        ),
        "effects": [
            ["add_node", "residual", "ControlRegimeResidual", {
                "kind": "no_operating_condition_candidate",
                "actions_to_act": T(P0("regime", "regime_actions_to_act")),
                "at_clock_seq": T(P0("regime", "regime_clock_seq")),
                "resolved": 0.0,
            }],
            ["add_edge", "agent", "has_control_regime_residual", "residual"],
            ["add_edge", "residual", "about_control_regime", "regime"],
            *_close_deliberation_effects(),
        ],
    }


def _close_deliberation_effects():
    """The same close every non-verdict route uses: the deliberation ends,
    a fresh evidence window opens, and System 1 never noticed."""
    return [
        ["set_attr", "regime", "regime_last_verdict", T(
            P0("regime", "regime_ordinal")
        )],
        ["set_attr", "regime", "regime_deliberating", 0.0],
        ["set_attr", "regime", "regime_deliberation_integral", 0.0],
        ["set_attr", "regime", "regime_evidence_seq", T(
            P0("regime", "regime_clock_seq")
        )],
        ["set_attr", "regime", "regime_absence_integral", 0.0],
        ["set_attr", "regime", "regime_escalation_requested", 0.0],
    ]


def integrate_evidence_absence_rule() -> dict:
    """Absence is an URGENCY-WEIGHTED integral, not a fixed count of actions.

    There are no absolute times in the contract, only ratios of the
    regime's own dynamics: each evidence-less clock tick adds
    `regime_urgency` — a DIMENSIONLESS divergence measure the consumer
    supplies (its current error over its own best-achieved error; absent
    -> 1.0, which reproduces the fixed-horizon semantics exactly, so
    every existing consumer is unchanged).  A regime diverging at ten
    times its own best escalates in a tenth of the window; a plateaued
    one waits the whole window.  Measured motivation: the damaged-wing
    fault rolled the airframe inverted in half the old fixed window —
    a constant horizon is always wrong for someone.
    """
    urgency = Min(Max(P0("regime", "regime_urgency"), L(1.0)), L(100.0))
    return {
        "name": "cre_integrate_evidence_absence",
        "area": "control_regime_escalation",
        "latency_class": "soft_realtime",
        "order": -51,
        "batch": False,
        "match": [
            ["agent", "holds_control_regime", "regime"],
        ],
        "where": And(
            Gt(P0("regime", "regime_monitor_enabled"), L(0.5)),
            Not(Gt(P0("regime", "regime_terminal"), L(0.5))),
            Gt(
                P0("regime", "regime_clock_seq"),
                P0("regime", "regime_absence_seq"),
            ),
        ),
        "effects": [
            # Evidence since the PREVIOUS integration resets the integral.
            # Comparing against this integrator's own last clock (not the
            # current tick) makes the semantics independent of rule-order
            # across areas: the consumer's evidence rule may run before or
            # after this one within a tick, and either way evidence counts
            # by the next integration (a one-tick lag, immaterial against
            # windows derived from the regime's slow time constants).
            ["set_attr", "regime", "regime_absence_integral", T(If(
                Not(Lt(
                    P0("regime", "regime_evidence_seq"),
                    P0("regime", "regime_absence_seq"),
                )),
                L(0.0),
                Plus(P0("regime", "regime_absence_integral"), urgency),
            ))],
            ["set_attr", "regime", "regime_absence_seq", T(
                P0("regime", "regime_clock_seq")
            )],
        ],
    }


def abandon_stale_deliberation_rule() -> dict:
    """A verdict whose premises have expired must be abandoned, not awaited.

    Block AA shortened the interval BETWEEN deliberations and could not fix
    what happens WITHIN one.  Measured on a damaged wing: the deliberation
    opens at 123 -- the right moment -- and returns HOLD, correctly, because at
    123 the objective is still reachable and the incumbent still dominates.
    The loop then acts on that verdict while the situation it judged ceases to
    exist, and the `Not(deliberating)` guard blocks reconsideration until it
    closes.  The aircraft inverted at 147.

    The test is the same principle one level in: **you cannot spend longer
    deciding than you have left.**  `regime_deliberation_integral` is how long
    this deliberation has been running; `regime_actions_to_act` is how long the
    plant says remains.  When the first exceeds the second, the deliberation is
    no longer deciding about the present -- it is deciding about a moment that
    has passed -- so it is closed and a fresh one may open against current
    evidence.

    This does not choose anything.  It withdraws a stale question so the loop
    can ask a current one, which is why it clears the escalation request too:
    the request belongs to the abandoned deliberation.

    A zero or absent projection cannot trigger it (a deliberation is never
    abandoned for want of a deadline), so a consumer that publishes no clocks
    is byte-identical to before this existed.
    """
    return {
        "name": "cre_abandon_stale_deliberation",
        "area": "control_regime_escalation",
        "latency_class": "soft_realtime",
        "order": -49.5,
        "batch": False,
        "match": [
            ["agent", "holds_control_regime", "regime"],
        ],
        "where": And(
            Gt(P0("regime", "regime_monitor_enabled"), L(0.5)),
            Gt(P0("regime", "regime_deliberating"), L(0.5)),
            Gt(P0("regime", "regime_actions_to_act"), L(0.0)),
            Gt(
                P0("regime", "regime_deliberation_integral"),
                P0("regime", "regime_actions_to_act"),
            ),
        ),
        "effects": [
            ["set_attr", "regime", "regime_deliberating", 0.0],
            ["set_attr", "regime", "regime_escalation_requested", 0.0],
            ["set_attr", "regime", "regime_deliberation_stale_count", T(
                Plus(P0("regime", "regime_deliberation_stale_count"), L(1.0))
            )],
        ],
    }


def note_evidence_absence_rule() -> dict:
    """Expected-evidence absence is a residual: mint it, open a deliberation.

    v3.0.0: opening a deliberation now also mints a FRESH
    `EmbodiedParetoProfile` — its own isolated coordinate system for this
    deliberation alone, so a consumer's candidate-minting rules have
    somewhere to publish alternatives and the shared `embodied_pareto_
    profile` primitive's dominance rule (reused, never reimplemented) has
    something to evaluate.  Stale profiles from earlier deliberations
    stay in the graph as an honest record but are never compared against
    fresh candidates (the primitive's dominance rule only ever compares
    candidates that share one `profile` node, and this deliberation's own
    `regime_pareto_minted_seq` singles its profile out).
    """
    return {
        "name": "cre_note_regime_evidence_absence",
        "area": "control_regime_escalation",
        "latency_class": "soft_realtime",
        "order": -50,
        "batch": False,
        "match": [
            ["agent", "holds_control_regime", "regime"],
        ],
        "where": And(
            Gt(P0("regime", "regime_monitor_enabled"), L(0.5)),
            Not(Gt(P0("regime", "regime_terminal"), L(0.5))),
            # YOU CANNOT WAIT LONGER THAN YOU HAVE.
            #
            # This was `absence_integral > evidence_horizon`: a fixed wait
            # before the loop may re-decide, regardless of how long the plant
            # says it has left.  Measured on a damaged wing, that is the whole
            # of the adoption latency.  Deliberation opened at action 128 --
            # when the objective was still reachable, so the incumbent
            # dominated and the verdict was HOLD -- and could not reconsider
            # until 316, because the horizon is 80 actions.  The aircraft
            # rolled inverted at 147.  The loop decided once, with the
            # information available at the moment it happened to look, and was
            # structurally unable to change its mind for 188 actions while the
            # situation it had judged ceased to exist.
            #
            # `regime_actions_to_act` is the loop's OWN projection of how many
            # actions remain before the thing it is watching is lost, already
            # computed every action by `cre_project_regime_clocks`.  Waiting
            # the full horizon when that projection reads 8 is not patience,
            # it is a deadline missed by an order of magnitude.  So the wait is
            # the SHORTER of the two: settle slowly when there is time, decide
            # now when there is not.
            #
            # Absent or zero projection falls back to the horizon, so a
            # consumer that publishes no clocks is byte-identical to before
            # this existed -- absence of a deadline is not a deadline of zero,
            # which would open a deliberation every action and churn.
            Gt(
                P0("regime", "regime_absence_integral"),
                Min(
                    P0("regime", "regime_evidence_horizon_actions"),
                    If(
                        Gt(P0("regime", "regime_actions_to_act"), L(0.0)),
                        P0("regime", "regime_actions_to_act"),
                        P0("regime", "regime_evidence_horizon_actions"),
                    ),
                ),
            ),
            Not(Gt(P0("regime", "regime_escalation_requested"), L(0.5))),
            Not(Gt(P0("regime", "regime_deliberating"), L(0.5))),
        ),
        "effects": [
            # The residual OPENS A DELIBERATION; it does not switch the
            # regime.  Escalation is the signal to START a higher-order
            # collapse, not to act -- System 1 keeps flying the current
            # regime while the collapse gathers per-candidate evidence
            # across ticks and publishes a verdict (which may be HOLD).
            ["set_attr", "regime", "regime_deliberating", 1.0],
            ["set_attr", "regime", "regime_deliberation_opened_seq", T(
                P0("regime", "regime_clock_seq")
            )],
            ["set_attr", "regime", "regime_deliberation_integral", 0.0],
            # The residual is graph data the agent holds about itself --
            # the control-grain analogue of an Impasse / SelfConcern.
            ["add_node", "impasse", "ControlRegimeImpasse", {
                "kind": "evidence_absence",
                "at_clock_seq": T(P0("regime", "regime_clock_seq")),
                "from_ordinal": T(P0("regime", "regime_ordinal")),
                "evidence_gap_actions": T(Minus(
                    P0("regime", "regime_clock_seq"),
                    P0("regime", "regime_evidence_seq"),
                )),
                "resolved": 0.0,
            }],
            ["add_edge", "agent", "has_control_regime_impasse", "impasse"],
            ["add_edge", "impasse", "about_control_regime", "regime"],
            ["set_attr", "regime", "regime_escalation_requested", 1.0],
            # A fresh, isolated Pareto coordinate system for THIS
            # deliberation, in the CORE primitive's own vocabulary
            # (`cognitive_pareto`): a `ParetoProfile` the general faculty
            # already knows how to evaluate and audit.  `dimension_count`
            # is a plain number the consumer declares -- no domain
            # vocabulary here, just the shape a bounded System-2
            # dominance evaluation needs.
            ["add_node", "pareto_profile", "ParetoProfile", {
                "context": "control_regime_escalation",
                "dimension_count": T(
                    P0("regime", "regime_pareto_dimension_count")
                ),
                "candidate_count": 0.0,
                "minted_seq": T(P0("regime", "regime_clock_seq")),
            }],
            ["add_edge", "regime", "deliberates_over_pareto_profile",
             "pareto_profile"],
            # THE HELD REGIME IS THE INCUMBENT GOAL, and it is what the
            # general goal-audit faculty falsifies.  Minting it here is
            # what lets `cp_falsify_dominated_incumbent_goal` do the
            # deciding: a dominating alternative is evidence the incumbent
            # is wrong relative to its OWN declared objective basis, and
            # the faculty emits a GoalRevisionRequest carrying that
            # concrete alternative rather than silently switching -- which
            # is exactly this seed's own "escalation is a TRIGGER, never
            # an immediate switch" law, held generally instead of
            # re-implemented here.
            ["add_node", "regime_goal", "Goal", {
                "kind": "hold_control_regime",
                "held_ordinal": T(P0("regime", "regime_ordinal")),
                "minted_seq": T(P0("regime", "regime_clock_seq")),
                "verified": 1,
            }],
            ["add_edge", "pareto_profile", "audits_goal", "regime_goal"],
            ["set_attr", "regime", "regime_pareto_minted_seq", T(
                P0("regime", "regime_clock_seq")
            )],
        ],
    }


def advance_deliberation_rule() -> dict:
    """The asynchronous half: a deliberation accrues while System 1 flies.

    Its own clock is the SAME urgency-weighted integral the absence rule
    uses (one deliberation window = one evidence window), so a fast-
    diverging regime deliberates briefly and a merely-plateaued one takes
    its time.  Unchanged from v2.0.0: this rule only advances the clock;
    what it is a clock FOR moved from per-rung "support" scalars to the
    Pareto frontier the consumer mints into `deliberates_over_pareto_
    profile` and the shared primitive evaluates.
    """
    urgency = Min(Max(P0("regime", "regime_urgency"), L(1.0)), L(100.0))
    return {
        "name": "cre_advance_regime_deliberation",
        "area": "control_regime_escalation",
        "latency_class": "soft_realtime",
        "order": -50,
        "batch": False,
        "match": [
            ["agent", "holds_control_regime", "regime"],
        ],
        "where": And(
            Gt(P0("regime", "regime_deliberating"), L(0.5)),
            Gt(
                P0("regime", "regime_clock_seq"),
                P0("regime", "regime_deliberation_seq"),
            ),
        ),
        "effects": [
            ["set_attr", "regime", "regime_deliberation_integral", T(Plus(
                P0("regime", "regime_deliberation_integral"), urgency
            ))],
            ["set_attr", "regime", "regime_deliberation_seq", T(
                P0("regime", "regime_clock_seq")
            )],
        ],
    }


def publish_regime_pareto_verdict_rule() -> dict:
    """The collapse publishes: adopt the POLICY-SELECTED frontier member.

    Replaces v2.0.0's `cre_publish_regime_deliberation`, which computed an
    Argmax over three fixed `regime_support_N` scalars -- precisely the
    smuggled winner-selection score `docs/embodied_pareto_profiles.md`
    forbids ("There are no weights, sums, or hidden winner-selection
    constants in the core... that choice must remain explicit and must
    not be smuggled into the Pareto substrate as a scalar score").

    The frontier itself is the shared primitive's relational dominance,
    reused verbatim (a candidate qualifies iff it carries no `dominated`
    flag).  Selection among the frontier is the one EXPLICIT, declared
    policy step the doc permits: greatest `regime_situational_priority_
    value` -- a single declared axis's own reading (never a weighted sum
    across axes, never folded into dominance).  Publication is decisive
    (order-zero, reflex-like) the moment that value is unambiguous
    (> 1.0 -- its own precondition exceeded twofold), else it waits for
    the deliberation's window backstop, exactly mirroring v2.0.0's
    "reflex and deliberation are one process at different depths."

    A candidate with NO worse value on any axis and no strictly-better
    alternative left on the frontier by construction; taking its declared
    `candidate_regime_ordinal` verbatim (never `Max`ed against the
    current ordinal -- ordinals carry no order to Max along) is therefore
    a straight copy, not a computed winner.

    v3.1.0 adds one clause to that policy: THE BURDEN OF PROOF IS ON THE
    CHANGE.  Leaving the currently-held regime requires a STRICT
    improvement on the declared priority axis over the frontier's own
    status-quo candidate; a tie publishes the status quo, which closes
    the deliberation and opens a fresh evidence window without touching
    what System 1 is flying.  This restores the HOLD verdict the ladder
    architecture had (and which the Pareto rewrite lost by handing ties
    to an arbitrary Argmax order) without reintroducing any ranking
    between regimes: incomparable corners stay incomparable, and the one
    being flown is simply not abandoned on no evidence.
    """
    frontier_source = Filter(
        Neighbours("profile", "has_pareto_candidate"),
        "peer",
        Not(Gt(P0("peer", "dominated"), L(0.5))),
    )
    best = Argmax(
        frontier_source,
        "peer",
        P0("peer", "regime_situational_priority_value"),
        V("regime"),
    )
    best_priority_value = MaxOver(
        frontier_source,
        "peer",
        P0("peer", "regime_situational_priority_value"),
        L(0.0),
    )
    # THE BURDEN OF PROOF IS ON THE CHANGE, and v4.0.0 stops re-deciding
    # that here.  `cognitive_pareto`'s goal-audit faculty already holds
    # it generally: the incumbent candidate is the held regime, a
    # DOMINATING alternative is a concrete counterexample to it, and
    # `cp_falsify_dominated_incumbent_goal` emits a GoalRevisionRequest
    # carrying that alternative instead of silently replacing the goal.
    # That is this seed's own "escalation is a TRIGGER, never an
    # immediate switch" law, stated once in the core rather than twice.
    #
    # So publication no longer computes a status-quo tie-break over the
    # declared priority axis (v3.1.0 did, and it was a domain-local
    # re-derivation of exactly this): a verdict that LEAVES the held
    # regime requires the faculty to have found a counterexample, which
    # is a strictly stronger and better-founded bar than "beats the
    # incumbent on one declared axis".  With no request, the incumbent
    # stands (`cre_publish_incumbent_stands`).
    revision_requested = Exists(
        Neighbours("profile", "has_goal_revision_request"),
        "request",
        Exists(
            Neighbours("request", "proposed_by_pareto_candidate"),
            "proposed",
            Eq(V("proposed"), V("candidate")),
        ),
    )
    verdict = P0("candidate", "candidate_regime_ordinal")
    terminal = P0("candidate", "candidate_terminal")
    return {
        "name": "cre_publish_regime_pareto_verdict",
        "area": "control_regime_escalation",
        "latency_class": "soft_realtime",
        "order": -49,
        "batch": False,
        "match": [
            ["agent", "holds_control_regime", "regime"],
            ["regime", "deliberates_over_pareto_profile", "profile"],
            ["profile", "has_pareto_candidate", "candidate"],
        ],
        "where": And(
            # Only the CURRENT deliberation's profile -- stale ones from
            # earlier in the episode are never candidates for selection.
            Eq(
                P0("profile", "minted_seq"),
                P0("regime", "regime_pareto_minted_seq"),
            ),
            # At least one full external tick separates minting from
            # selection, so the shared dominance rule (which runs on its
            # own schedule) has had a whole `run_rules` fixpoint to
            # settle before this rule ever reads `dominated` -- the same
            # same-tick cross-area ordering hazard the absence integrator
            # was rebuilt around once already (v1.1.0) is avoided by
            # construction here, not by hoping for a lucky rule order.
            Gt(
                P0("regime", "regime_clock_seq"),
                P0("regime", "regime_pareto_minted_seq"),
            ),
            Gt(P0("regime", "regime_deliberating"), L(0.5)),
            Gt(P0("regime", "regime_deliberation_integral"), L(0.0)),
            # v6.0.0, OPT-IN (`regime_class_gate_enabled`): WHICH RESPONSE
            # is admissible is a comparison of ONE projected time against
            # declared quantities, never a lookup on a label.
            #
            #   fixpoint already gone (acting clock at the lattice floor)
            #       -> the full corner set; surrendering an objective is
            #          the honest response to an objective that is gone.
            #   transition projected INSIDE the control horizon
            #       -> only a candidate that CHANGES THE OPERATING
            #          CONDITION so the fixpoint stays attainable.  A
            #          transition that has not happened is not a reason to
            #          give up an objective -- it is a reason to move the
            #          plant to where the basin is bigger, while the
            #          authority to move it still exists.
            #   otherwise -> no verdict here at all (see the recalibration
            #          route).
            #
            # With the gate off this clause is inert and the seed's
            # behaviour is v4.0.0's exactly.
            Or(
                Not(Gt(P0("regime", "regime_class_gate_enabled"), L(0.5))),
                Or(
                    _fixpoint_already_lost(),
                    And(
                        _transition_inside_control_horizon(),
                        Gt(P0("candidate", "candidate_restores_basin"),
                           L(0.5)),
                    ),
                ),
            ),
            # A CANDIDATE MAY DECLARE THAT IT IS ONLY FOR EMERGENCIES.
            #
            # `candidate_requires_change` is set by whoever minted it; absent
            # reads 0 so a candidate that says nothing is admissible exactly as
            # before.  One that says so is admissible only while the consumer
            # asserts `regime_change_required` -- the same flag the no-op clause
            # below reads, so "a change is required" has one meaning in this
            # seed and not two.
            #
            # This is what stops a loop giving an objective up merely because it
            # is tracking badly: the giving-up is declared by the candidate, the
            # licence is declared by the consumer, and neither alone suffices.
            Or(
                Not(Gt(P0("candidate", "candidate_requires_change"), L(0.5))),
                Gt(P0("regime", "regime_change_required"), L(0.5)),
            ),
            Not(Gt(P0("candidate", "dominated"), L(0.5))),
            # WHEN A CHANGE IS REQUIRED, A NO-OP IS NOT AN ANSWER.
            #
            # A consumer that has decided the incumbent is no longer viable
            # says so with `regime_change_required`; absent means 0 means "not
            # required", so a consumer that never sets it is byte-identical to
            # before this clause existed.  When it IS set, a candidate minted
            # at the held ordinal cannot be the verdict -- adopting it would
            # change nothing, and "change nothing" is the one answer already
            # ruled out.
            #
            # Measured on the F-16 (block AS): the only alternative that
            # dominated the incumbent was a probe minted at the held ordinal,
            # so it won every deliberation and the verdict was HOLD through an
            # entire departure.  It was not shadowing a better proposal -- it
            # was the only one -- which is why this clause arrives together
            # with a consumer rule that supplies real ones at that rung.
            Or(
                Not(Gt(P0("regime", "regime_change_required"), L(0.5))),
                Not(Eq(
                    P0("candidate", "candidate_regime_ordinal"),
                    P0("regime", "regime_ordinal"),
                )),
            ),
            # The faculty proposed THIS candidate as the counterexample …
            revision_requested,
            # … and among however many it proposed, the consumer's own
            # declared situational policy picks one.  Selection among
            # incomparable survivors is the one explicit policy step
            # docs/embodied_pareto_profiles.md permits; the DECISION that
            # the incumbent is falsified at all is the faculty's.
            Eq(V("candidate"), best),
            Or(
                Gt(best_priority_value, L(1.0)),
                Not(Lt(
                    P0("regime", "regime_deliberation_integral"),
                    P0("regime", "regime_evidence_horizon_actions"),
                )),
            ),
        ),
        "effects": [
            # The COUNT IS TAKEN FIRST: effects apply in order, so reading
            # `regime_ordinal` after the verdict has overwritten it compares
            # the verdict against itself and never counts anything (v3.0.0
            # shipped that way -- the telemetry read 0 through every real
            # regime change).
            ["set_attr", "regime", "regime_escalation_count", T(If(
                Not(Eq(verdict, P0("regime", "regime_ordinal"))),
                Plus(P0("regime", "regime_escalation_count"), L(1.0)),
                P0("regime", "regime_escalation_count"),
            ))],
            ["set_attr", "regime", "regime_ordinal", T(verdict)],
            ["set_attr", "regime", "regime_terminal", T(terminal)],
            ["set_attr", "regime", "regime_last_escalation_seq", T(
                P0("regime", "regime_clock_seq")
            )],
            ["set_attr", "regime", "regime_last_verdict", T(verdict)],
            ["set_attr", "regime", "regime_deliberating", 0.0],
            ["set_attr", "regime", "regime_deliberation_integral", 0.0],
            # Either way the new state earns a fresh evidence window.
            ["set_attr", "regime", "regime_evidence_seq", T(
                P0("regime", "regime_clock_seq")
            )],
            ["set_attr", "regime", "regime_absence_integral", 0.0],
            ["set_attr", "regime", "regime_escalation_requested", 0.0],
        ],
    }


def mark_incumbent_candidate_rule() -> dict:
    """The held regime IS the incumbent the goal-audit faculty falsifies.

    Purely relational and domain-free: among this deliberation's
    candidates, the one whose declared `candidate_regime_ordinal` is the
    ordinal currently held is what the agent is actually flying.  Marking
    it with the core primitive's own `has_incumbent_pareto_candidate`
    edge is what lets `cp_falsify_dominated_incumbent_goal` run --
    nothing here decides anything about it.
    """
    known = Neighbours("profile", "has_incumbent_pareto_candidate")
    return {
        "name": "cre_mark_incumbent_candidate",
        "area": "control_regime_escalation",
        "latency_class": "soft_realtime",
        "order": -49.4,
        "batch": False,
        "match": [
            ["agent", "holds_control_regime", "regime"],
            ["regime", "deliberates_over_pareto_profile", "profile"],
            ["profile", "has_pareto_candidate", "candidate"],
        ],
        "where": And(
            Eq(
                P0("profile", "minted_seq"),
                P0("regime", "regime_pareto_minted_seq"),
            ),
            Eq(
                P0("candidate", "candidate_regime_ordinal"),
                P0("regime", "regime_ordinal"),
            ),
            Not(Exists(known, "held", Eq(V("held"), V("candidate")))),
        ),
        "effects": [
            ["add_edge", "profile", "has_incumbent_pareto_candidate",
             "candidate"],
        ],
    }


def publish_incumbent_stands_rule() -> dict:
    """The HOLD verdict, grounded: no counterexample inside the window.

    The window backstop passes and the goal-audit faculty has proposed no
    revision -- so nothing on the frontier is a counterexample to what is
    being flown.  Close the deliberation, open a fresh evidence window,
    and change nothing.  System 1 never noticed.

    This is the honest complement to `cre_publish_regime_pareto_verdict`:
    without it a deliberation that finds no counterexample stays open
    forever and blocks every later one (measured while building v3.1.0 --
    a synthetic frontier with no dominating alternative hung the monitor
    at `regime_deliberating = 1` indefinitely).
    """
    any_revision = Exists(
        Neighbours("profile", "has_goal_revision_request"),
        "request",
        L(True),
    )
    return {
        "name": "cre_publish_incumbent_stands",
        "area": "control_regime_escalation",
        "latency_class": "soft_realtime",
        "order": -49,
        "batch": False,
        "match": [
            ["agent", "holds_control_regime", "regime"],
            ["regime", "deliberates_over_pareto_profile", "profile"],
        ],
        "where": And(
            Eq(
                P0("profile", "minted_seq"),
                P0("regime", "regime_pareto_minted_seq"),
            ),
            # TWO full external ticks since minting, not one: the first
            # settles the core primitive's dominance, the second lets the
            # goal-audit faculty turn a dominated incumbent into a
            # GoalRevisionRequest.  With only one, "no counterexample was
            # found" could win the race against the counterexample still
            # being derived in the same fixpoint (measured: the decisive
            # publish test closed on the incumbent while an alternative
            # that dominates it was sitting on the frontier).
            Gt(
                P0("regime", "regime_clock_seq"),
                Plus(P0("regime", "regime_pareto_minted_seq"), L(1.0)),
            ),
            Gt(P0("regime", "regime_deliberating"), L(0.5)),
            # The deliberation ran its whole declared window …
            Not(Lt(
                P0("regime", "regime_deliberation_integral"),
                P0("regime", "regime_evidence_horizon_actions"),
            )),
            # … and the faculty never falsified the incumbent.
            Not(any_revision),
        ),
        "effects": [
            ["set_attr", "regime", "regime_last_verdict", T(
                P0("regime", "regime_ordinal")
            )],
            ["set_attr", "regime", "regime_deliberating", 0.0],
            ["set_attr", "regime", "regime_deliberation_integral", 0.0],
            ["set_attr", "regime", "regime_evidence_seq", T(
                P0("regime", "regime_clock_seq")
            )],
            ["set_attr", "regime", "regime_absence_integral", 0.0],
            ["set_attr", "regime", "regime_escalation_requested", 0.0],
        ],
    }


def close_inadmissible_deliberation_rule() -> dict:
    """THE THIRD CASE: proposals exist, and none of them is allowed.

    Two rules close a deliberation.  `cre_publish_regime_pareto_verdict` closes
    it by ADOPTING a candidate; `cre_publish_incumbent_stands` closes it when the
    faculty proposed NOTHING.  Neither covers the case where the faculty proposed
    something and every proposal is inadmissible -- and that case now exists,
    because `candidate_requires_change` gives the verdict a reason to refuse a
    proposal that is otherwise perfectly good.

    Measured (block BB): with the generated probe unregistered, the escape path
    proposes a surrendering corner in benign conditions, the verdict correctly
    refuses it because the consumer is not asserting `regime_change_required`,
    and the deliberation stays open forever -- `regime_deliberating` pinned at
    1.0, which is exactly the hazard `cre_publish_incumbent_stands` was written
    to prevent: *"a deliberation that finds no counterexample stays open forever
    and blocks every later one."*  Finding no ADMISSIBLE counterexample is the
    same situation and deserves the same verdict.

    So: HOLD, on the same terms.  Identical effects to the incumbent-stands
    close, because the outcome is identical -- nothing changes, the window
    reopens, and the loop is free to deliberate again when new evidence arrives.
    The window backstop is required here too, so a proposal that is merely still
    settling is never mistaken for one that is refused.
    """
    any_revision = Exists(
        Neighbours("profile", "has_goal_revision_request"),
        "request",
        L(True),
    )
    admissible_proposal = Exists(
        Neighbours("profile", "has_goal_revision_request"),
        "request",
        Exists(
            Neighbours("request", "proposed_by_pareto_candidate"),
            "proposal",
            And(
                Not(Gt(P0("proposal", "dominated"), L(0.5))),
                Or(
                    Not(Gt(
                        P0("proposal", "candidate_requires_change"), L(0.5)
                    )),
                    Gt(P0("regime", "regime_change_required"), L(0.5)),
                ),
                Or(
                    Not(Gt(
                        P0("regime", "regime_change_required"), L(0.5)
                    )),
                    Not(Eq(
                        P0("proposal", "candidate_regime_ordinal"),
                        P0("regime", "regime_ordinal"),
                    )),
                ),
            ),
        ),
    )
    return {
        "name": "cre_close_inadmissible_deliberation",
        "area": "control_regime_escalation",
        "latency_class": "soft_realtime",
        "order": -48.9,
        "batch": False,
        "match": [
            ["agent", "holds_control_regime", "regime"],
            ["regime", "deliberates_over_pareto_profile", "profile"],
        ],
        "where": And(
            Eq(
                P0("profile", "minted_seq"),
                P0("regime", "regime_pareto_minted_seq"),
            ),
            Gt(
                P0("regime", "regime_clock_seq"),
                Plus(P0("regime", "regime_pareto_minted_seq"), L(1.0)),
            ),
            Gt(P0("regime", "regime_deliberating"), L(0.5)),
            Not(Lt(
                P0("regime", "regime_deliberation_integral"),
                P0("regime", "regime_evidence_horizon_actions"),
            )),
            # Something WAS proposed …
            any_revision,
            # … and nothing proposed is admissible.
            Not(admissible_proposal),
        ),
        "effects": [
            ["set_attr", "regime", "regime_last_verdict", T(
                P0("regime", "regime_ordinal")
            )],
            ["set_attr", "regime", "regime_deliberating", 0.0],
            ["set_attr", "regime", "regime_deliberation_integral", 0.0],
            ["set_attr", "regime", "regime_evidence_seq", T(
                P0("regime", "regime_clock_seq")
            )],
            ["set_attr", "regime", "regime_absence_integral", 0.0],
            ["set_attr", "regime", "regime_escalation_requested", 0.0],
        ],
    }


def manifest() -> dict:
    return {
        "id": "control_regime_escalation",
        "version": "7.11.0",
        "depends_on": ["cognitive_pareto"],
        "area": "control_regime_escalation",
        "latency_class": "soft_realtime",
        "description": (
            "Expected-evidence absence is a first-class residual at the "
            "control grain, and it opens a deliberation over a Pareto "
            "frontier of consumer-declared, Pareto-INCOMPARABLE regimes "
            "(docs/regime_pareto_frontier_prereg.md) rather than climbing "
            "a total-order ladder.  The general half of the metastability "
            "fix (docs/metastable_regime_escalation.md): a regime that "
            "promises evidence and delivers none inside its horizon is "
            "escalated instead of replayed forever; WHICH regime it "
            "escalates to is the shared embodied_pareto_profile "
            "primitive's relational dominance plus one explicit, "
            "declared selection policy -- never a smuggled scalar."
        ),
        "microtheory": {
            "name": "control_regime_escalation",
            "description": (
                "no expected evidence inside the horizon -> mint a "
                "ControlRegimeImpasse -> open a deliberation over a fresh "
                "Pareto frontier of the consumer's declared regimes -> "
                "publish the frontier member the declared situational "
                "policy prefers.  The domain defines evidence, regime "
                "semantics, and the per-axis achievable-margin formulas."
            ),
        },
        "nodes": [channel_sample_frame_node()],
        "edges": [],
        "productions": [
            {
                "provenance": (
                    "seed:control_regime_escalation:has_regime_channel"
                ),
                "src": {"type": "EmbodiedMotorProgramEpisode", "var": "s"},
                "edge_type": "has_regime_channel",
                "tgt": {"type": "ControlRegimeChannel", "var": "t"},
            },
            {
                "provenance": (
                    "seed:control_regime_escalation:holds_regime_transition"
                ),
                "src": {"type": "Agent", "var": "s"},
                "edge_type": "holds_regime_transition",
                "tgt": {"type": "ControlRegimeTransition", "var": "t"},
            },
            {
                "provenance": (
                    "seed:control_regime_escalation:"
                    "transition_about_control_regime"
                ),
                "src": {"type": "ControlRegimeTransition", "var": "s"},
                "edge_type": "about_control_regime",
                "tgt": {"type": "EmbodiedMotorProgramEpisode", "var": "t"},
            },
            {
                "provenance": (
                    "seed:control_regime_escalation:"
                    "has_control_regime_residual"
                ),
                "src": {"type": "Agent", "var": "s"},
                "edge_type": "has_control_regime_residual",
                "tgt": {"type": "ControlRegimeResidual", "var": "t"},
            },
            {
                "provenance": (
                    "seed:control_regime_escalation:"
                    "residual_about_control_regime"
                ),
                "src": {"type": "ControlRegimeResidual", "var": "s"},
                "edge_type": "about_control_regime",
                "tgt": {"type": "EmbodiedMotorProgramEpisode", "var": "t"},
            },
            {
                "provenance": (
                    "seed:control_regime_escalation:holds_control_regime"
                ),
                "src": {"type": "Agent", "var": "s"},
                "edge_type": "holds_control_regime",
                "tgt": {"type": "EmbodiedMotorProgramEpisode", "var": "t"},
            },
            {
                "provenance": (
                    "seed:control_regime_escalation:has_control_regime_impasse"
                ),
                "src": {"type": "Agent", "var": "s"},
                "edge_type": "has_control_regime_impasse",
                "tgt": {"type": "ControlRegimeImpasse", "var": "t"},
            },
            {
                "provenance": (
                    "seed:control_regime_escalation:about_control_regime"
                ),
                "src": {"type": "ControlRegimeImpasse", "var": "s"},
                "edge_type": "about_control_regime",
                "tgt": {"type": "EmbodiedMotorProgramEpisode", "var": "t"},
            },
            {
                "provenance": (
                    "seed:control_regime_escalation:"
                    "deliberates_over_pareto_profile"
                ),
                "src": {"type": "EmbodiedMotorProgramEpisode", "var": "s"},
                "edge_type": "deliberates_over_pareto_profile",
                "tgt": {"type": "ParetoProfile", "var": "t"},
            },
        ],
        "rules": [
            integrate_evidence_absence_rule(),
            publish_spend_authority_rule(),
            project_region_reachability_rule(),
            project_channel_assisted_clock_rule(),
            note_evidence_absence_rule(),
            abandon_stale_deliberation_rule(),
            advance_deliberation_rule(),
            accumulate_channel_samples_rule(),
            ratchet_channel_reserve_rule(),
            project_channel_clocks_rule(),
            project_regime_clocks_rule(),
            note_projected_transition_rule(),
            mark_incumbent_candidate_rule(),
            publish_regime_pareto_verdict_rule(),
            publish_incumbent_stands_rule(),
            close_inadmissible_deliberation_rule(),
            route_no_projected_transition_rule(),
            close_gated_deliberation_rule(),
        ],
    }


def main() -> int:
    out = ROOT / "seeds" / "control_regime_escalation.json"
    payload = manifest()
    out.write_text(json.dumps(payload, indent=1) + "\n", encoding="utf-8")
    json.loads(out.read_text(encoding="utf-8"))
    print(f"wrote {out.relative_to(ROOT)} ({len(payload['rules'])} rules)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
