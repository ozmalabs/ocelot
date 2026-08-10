#!/usr/bin/env python3
"""Generate the surprise-promotion seed: how a channel becomes a candidate.

There is no standing per-effector authority weight.  A channel is not a
candidate until the model is SURPRISED about it, by either route:

  (a) DETECTED  — a measurement contradicts its expectation
  (b) PREDICTED — the forward model projects it to a crossing, BEFORE contact

Surprise mints a candidate; the existing collapse decides among candidates.
Nothing here arbitrates and nothing here knows what a fall, a desk or a wall is.

The resolution chain (measured -> expected -> declared -> honest failure) is not
hygiene: **a dark channel cannot surprise you**, so an unresolved channel can
never promote and its effector can never be rescued.  Resolution is what makes
the collapse reachable at all.

Every resolved value carries its provenance, after the F16 pattern
(`state_remaining_fuel_kg_measured`): a declared default is usable and is never
confusable with an observation.

ENGINE CONSTRAINT (measured, not assumed): `Sum` over `Neighbours` evaluates to
0 inside a `where` while the identical term is correct in an effect.  Every
aggregate below therefore lives in an effect on an unconditional rule, as
`enl_settle_energy_balance` does.
"""
from __future__ import annotations

import json
from pathlib import Path


import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# ONE SOURCE FOR THE LOOP'S HORIZON. The ledger declares it; this seed reads
# the same declaration rather than copying the number, so the two cannot drift.
from scripts.gen_energy_ledger_seed import DEFAULT_HORIZON_ACTIONS  # noqa: E402

# A MAGIC NUMBER IS A QUANTITY WHOSE RELATUM YOU FAILED TO NAME. Three literals
# stood here; each was a ratio wearing the clothes of an absolute. What each is
# a ratio TO is now named, and read from graph data wherever the graph holds it:
#
#   tolerance  -> the CHANNEL'S OWN measurement quantum (`quantum_units`,
#                 declared by the adapter that owns the units, since only it
#                 knows how coarsely it samples).
#   horizon    -> the LOOP'S OWN declared control horizon
#                 (`EnergyLedger.horizon_actions` — the same window the
#                 affordability projection already commits to).
#   cost floor -> the LEDGER'S OWN reach (`stock_units` / `reachable_units`),
#                 because "unpriced must lose" means GREATER THAN ANYTHING
#                 REACHABLE, not "a big number I chose".
#
# One literal survives, and it is not arbitrary: the step of the integer
# lattice itself. This tree's frame/continuum invariant fixes it — in-frame
# coordinates ARE the integers, so the smallest in-frame difference is 1 by
# construction, not by choice. It appears only where "strictly more than" has
# to be expressed on that lattice.
LATTICE_STEP_UNITS = 1

# THE FLAT-ZERO PATHOLOGY, imported from the F16 frontier where it was measured
# twice in different clothes:
#
#   * a SURRENDERED axis scored flat 0.0 dominated a KEPT axis scored
#     unbounded-below, so the corner that gave up the most won;
#   * `effective_delta = MIN(declared, F_max*dt/m)` priced a WEAKER engine as a
#     CHEAPER escape, so the airframe that could do least read as safest.
#
# Both are one shape: **failing to have a property is priced better than having
# it imperfectly.**  An option that declares no cost is not free — it is
# unpriced, and an unpriced option must never compare as the cheapest one.
#
# The floor was a SENTINEL — a number picked large enough to lose — and a
# sentinel is wrong the moment a body has a budget larger than the guess. What
# "must lose" actually means is GREATER THAN ANYTHING REACHABLE, and the ledger
# already computes exactly that, twice over: `stock_units` is the amount
# ceiling and `reachable_units = min(stock, rate x horizon)` the rate-limited
# one. One step past the larger of them cannot be out-guessed, and it tracks a
# growing budget instead of being overtaken by it.


# ------------------------------------------------------- the approach stream
#
# Route (b) needs a SEQUENCE, and until now nothing built one: no rule attached
# a `TemporalProjection` to a channel, so the predicted route could not fire at
# all.  These constants declare how a channel's observation history is read as
# a stream.
#
# `STREAM_CODEBOOK_TYPE` is a DEDICATED codebook type rather than the general
# `ShapeSignature` one.  `TimeInfer` reads which slots are coordinates from the
# first codebook part that declares `dim_types`; pointed at `ShapeSignature` in
# a live agent it would pick up whichever unrelated part happened to be first.
# One part of our own type makes the reading exact.
STREAM_CODEBOOK_TYPE = "ChannelStreamSignature"

# The projection's forward bound, ONE LATTICE STEP BEYOND the loop's declared
# control horizon. `crossing` is capped at this value and also RETURNS it when
# the stream never reaches its origin, so cap and deadline are otherwise
# indistinguishable. Putting the cap outside the horizon keeps "no measured
# deadline" from reading as "crosses exactly at the horizon" — the recurring
# pathology in its temporal clothes: a channel that fails to have a deadline
# must not be priced as one about to cross.
#
# DECLARED, NOT DERIVED, and the reason is a real limitation rather than a
# preference: `TimeInfer`'s `max_steps` is a field of the Term itself, an
# integer fixed when the rule is authored, so it cannot read `horizon_actions`
# off the ledger the way the rules below do. It is at least tied to the SAME
# relatum — the ledger's own declared horizon — so the two cannot drift apart,
# and the projection publishes the bound it actually used as `horizon_units`
# so every consumer compares against graph data rather than this constant. A
# ledger whose horizon is later raised past this bound is handled by that
# published value, not by the constant: a crossing AT the bound is refused as
# "no measured deadline" either way.
STREAM_HORIZON_UNITS = DEFAULT_HORIZON_ACTIONS + LATTICE_STEP_UNITS

# A second difference needs three samples. Below this the stream is honestly
# unprojectable; it is never padded to reach the threshold.
MINIMUM_STREAM_SAMPLES = 3


def V(name): return {"type": "Var", "name": name}
def L(value): return {"type": "Lit", "value": value}
def A(name, key): return {"type": "Attr", "node": V(name), "key": key}
def Eq(a, b): return {"type": "Eq", "a": a, "b": b}
def Gt(a, b): return {"type": "Gt", "a": a, "b": b}
def Lte(a, b): return {"type": "Not", "arg": Gt(a, b)}
def And(*items): return {"type": "And", "items": list(items)}
def Not(arg): return {"type": "Not", "arg": arg}
def Abs(arg): return {"type": "Abs", "arg": arg}
def Max(*items): return {"type": "Max", "items": list(items)}
def Min(*items): return {"type": "Min", "items": list(items)}
def Plus(*items): return {"type": "Plus", "items": list(items)}
def Minus(a, b): return {"type": "Minus", "a": a, "b": b}
def Or(*items): return {"type": "Or", "items": list(items)}
def N(name, edge): return {"type": "Neighbours", "node": V(name), "edge_type": edge}
def Count(source): return {"type": "Count", "source": source}
def MapList(source, var, value): return {
    "type": "MapList", "source": source, "var_name": var, "value": value}
def FilterList(source, var, predicate): return {
    "type": "FilterList", "source": source, "var_name": var,
    "predicate": predicate}
def MaxOver(source, var, value, default): return {
    "type": "MaxOver", "source": source, "var_name": var, "value": value,
    "default": default}
def Append(seq, item): return {"type": "Append", "seq": seq, "item": item}
def Exists(source, var, predicate): return {
    "type": "Exists", "source": source, "var_name": var, "predicate": predicate}


def absent(source, var="prior"):
    return Not(Exists(source, var, L(True)))


def d0(name, key):
    return Plus(A(name, key), L(0))


def declared(name, key):
    """Is this attribute PRESENT, as opposed to present-and-zero?

    The engine distinguishes them: a raw `Attr` on a missing key evaluates to
    None, and `Eq(Attr, Lit None)` is True only then. The `Plus[Attr, Lit 0]`
    idiom used throughout this tree DESTROYS that distinction — which is the
    whole mechanism behind 4,122 rule-read attributes silently reading as 0.
    Where a missing value must not be treated as a measured zero, guard with
    this instead of coalescing.
    """
    return Not(Eq(A(name, key), L(None)))


# ---------------------------------------------------------------- resolution

def resolve_measured_rule():
    return {
        "name": "srp_resolve_channel_from_measurement",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "comment": (
            "A published observation is the strongest rung. Provenance says so, "
            "so nothing downstream can mistake it for an assumption."
        ),
        "match": [["channel", "has_channel_observation", "observation"]],
        "where": L(True),
        "effects": [
            ["set_attr", "channel", "value_units", {"__term__": d0("observation", "value_units")}],
            ["set_attr", "channel", "provenance", "measured"],
            ["set_attr", "channel", "measured", 1],
        ],
    }


def resolve_expected_rule():
    return {
        "name": "srp_resolve_channel_from_expectation",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "comment": (
            "WE EXPECT TO TURN, WE ASSUME WE HAVE. With no observation the "
            "efference copy's prediction stands in — usable, and flagged as an "
            "assumption rather than a reading."
        ),
        "match": [["channel", "has_channel_expectation", "expectation"]],
        "where": absent(N("channel", "has_channel_observation")),
        "effects": [
            ["set_attr", "channel", "value_units", {"__term__": d0("expectation", "value_units")}],
            ["set_attr", "channel", "provenance", "expected"],
            ["set_attr", "channel", "measured", 0],
        ],
    }


def resolve_declared_rule():
    return {
        "name": "srp_resolve_channel_from_declared_prior",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "comment": (
            "Neither read nor predicted: the declared prior, explicitly marked. "
            "This is the rung that replaces the silent zero — a channel with no "
            "information says so instead of reporting 0 like a measurement."
        ),
        "match": [["effector", "has_sensed_channel", "channel"]],
        "where": And(
            absent(N("channel", "has_channel_observation")),
            absent(N("channel", "has_channel_expectation")),
        ),
        "effects": [
            ["set_attr", "channel", "value_units", {"__term__": d0("channel", "declared_units")}],
            ["set_attr", "channel", "provenance", "declared"],
            ["set_attr", "channel", "measured", 0],
        ],
    }


# ------------------------------------------------------------------ surprise

def expect_from_program_rule():
    """WE EXPECT TO TURN, WE ASSUME WE HAVE — the efference copy, as a rule.

    The commanded program already carries what it predicts. A channel declares
    WHICH of those predictions covers it (`predictor_kind`); this turns the two
    into an expectation the reading can then contradict. The adapter predicts
    nothing — it only records which program produced a reading.
    """
    return {
        "name": "srp_expect_channel_from_enacted_program",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "comment": (
            "An efference copy is not a measurement and not a policy: it is "
            "what the issued command already said would happen. A channel with "
            "no declared predictor mints nothing and stays unsurprisable, "
            "which is an honest statement about the body rather than a gap."
        ),
        "match": [
            ["channel", "has_channel_observation", "observation"],
            ["observation", "observed_under_motor_program", "program"],
        ],
        "where": And(
            Eq(A("channel", "predictor_kind"), L("peak_load")),
            # An UNDECLARED prediction is not a prediction of zero. Minting an
            # expectation from an absent attribute manufactures false surprise
            # — the same "failing to have a property is priced as having it"
            # shape the F16 frontier was measured on twice.
            declared("program", "predicted_peak_load_units"),
            absent(N("channel", "has_channel_expectation")),
        ),
        "effects": [
            ["add_node", "expectation", "ChannelExpectation", {
                "value_units": {"__term__": d0("program", "predicted_peak_load_units")},
                "predictor_kind": "peak_load",
                "integer_native": 1,
                "output_authority": 0,
            }],
            ["add_edge", "channel", "has_channel_expectation", "expectation"],
        ],
    }


def expect_vertical_rule():
    """The FALL channel's predictor.

    A second predictor kind, not a special case: the same mechanism bound to a
    different declared prediction. `base_height` is what leaving support moves,
    so giving it a predictor is what makes a fall surprisable at all.
    """
    rule = expect_from_program_rule()
    rule["name"] = "srp_expect_vertical_channel_from_enacted_program"
    rule["where"] = And(
        Eq(A("channel", "predictor_kind"), L("vertical")),
        declared("program", "predicted_vertical_units"),
        absent(N("channel", "has_channel_expectation")),
    )
    effects = json.loads(json.dumps(rule["effects"]))
    effects[0][3]["value_units"] = {
        "__term__": d0("program", "predicted_vertical_units")}
    effects[0][3]["predictor_kind"] = "vertical"
    rule["effects"] = effects
    return rule


def detect_surprise_rule():
    """Route (a): a reading contradicts the expectation."""
    discrepancy = Abs(Minus(d0("observation", "value_units"),
                            d0("expectation", "value_units")))
    return {
        "name": "srp_detect_surprise_from_violated_expectation",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "comment": (
            "Surprise is the reading against the expectation, over the channel's "
            "own declared tolerance. Both sides must exist: a channel with no "
            "expectation cannot be surprised, and neither can a dark one."
        ),
        "match": [
            ["channel", "has_channel_observation", "observation"],
            ["channel", "has_channel_expectation", "expectation"],
        ],
        "where": And(
            # A MISSING READING IS NOT A READING OF ZERO. Coalescing either
            # side of the discrepancy makes a blind observation contradict its
            # expectation by exactly the expectation's own size — surprise
            # manufactured out of absence, which is the defect this whole line
            # exists to remove. Both sides must be present before they can
            # disagree; a channel missing either is unsurprisable, and says so.
            declared("observation", "value_units"),
            declared("expectation", "value_units"),
            # A DISCREPANCY SMALLER THAN ONE MEASUREMENT STEP IS NOT A
            # DISCREPANCY. The floor is the channel's OWN declared quantum —
            # the adapter that owns the units is the only thing that knows how
            # coarsely it samples — never a literal chosen here. A channel
            # sampled on the integer lattice declares a quantum of one step
            # and contributes no floor beyond its stated tolerance; one that
            # resolves only to five units says so, and four units of
            # disagreement stop counting as news.
            Gt(discrepancy, Max(d0("channel", "tolerance_units"),
                                Minus(Max(d0("channel", "quantum_units"),
                                          L(LATTICE_STEP_UNITS)),
                                      L(LATTICE_STEP_UNITS)))),
            absent(N("channel", "has_surprise")),
        ),
        "effects": [
            ["add_node", "surprise", "SurpriseSignal", {
                "route": "detected",
                "surprise_units": {"__term__": discrepancy},
                "crossing_units": 0,
                "integer_native": 1,
                "output_authority": 0,
            }],
            ["add_edge", "channel", "has_surprise", "surprise"],
        ],
    }


# --------------------------------------------------- the stream, as a stream

def _current_trial_observations():
    """This channel's observations from the CURRENT trial, in order.

    Scoping matters and is not bookkeeping: every trial begins with a reset, so
    samples from two trials are not one trajectory. Projecting across the reset
    would fit a generator to a discontinuity and report a deadline that no body
    is approaching. `stream_epoch` is the latest trial ordinal the channel has
    seen; the stream is exactly that trial's samples.
    """
    return FilterList(
        N("channel", "has_channel_observation"), "sample",
        Eq(d0("sample", "trial_ordinal"), d0("channel", "stream_epoch")),
    )


def scope_stream_rule():
    return {
        "name": "srp_scope_channel_stream_to_current_trial",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "comment": (
            "The channel's stream epoch is the latest trial its observations "
            "carry. UNCONDITIONAL, because `MaxOver` over `Neighbours` is an "
            "aggregate and aggregates read as their identity inside a `where` "
            "while being correct in an effect — measured, not assumed. It does "
            "not need a guard: it is a pure function of the observation set, so "
            "re-firing rewrites the same number."
        ),
        "match": [["effector", "has_sensed_channel", "channel"]],
        "where": L(True),
        "effects": [
            ["set_attr", "channel", "stream_epoch", {"__term__": MaxOver(
                N("channel", "has_channel_observation"), "sample",
                d0("sample", "trial_ordinal"), L(0))}],
        ],
    }


def stream_frames_rule():
    """The channel's history AS A STREAM the forward projection can read.

    A frame is one sample: a single relation whose one slot is a coordinate,
    which is the degenerate shape the projection is already written for. The
    whole stream is therefore `[[[v0]], [[v1]], ...]`.
    """
    return {
        "name": "srp_read_channel_history_as_a_stream",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "comment": (
            "Until this rule existed nothing in the graph turned a channel's "
            "observations into a sequence, so no projection could be attached "
            "and route (b) was unreachable — the predicted route was present in "
            "the rule set and dead in every run. UNCONDITIONAL for the same "
            "reason as the scope rule above: the aggregates must live in an "
            "effect. Note the RAW `value_units` read: a sample carrying no "
            "reading must poison the stream into no-fit, never coalesce to 0, "
            "because 0 is exactly the origin the crossing is measured to and a "
            "missing reading would otherwise report maximum urgency."
        ),
        "match": [["effector", "has_sensed_channel", "channel"]],
        "where": L(True),
        "effects": [
            ["set_attr", "channel", "stream_frames", {"__term__": MapList(
                _current_trial_observations(), "sample",
                Append(L([]), Append(L([]), A("sample", "value_units"))))}],
            ["set_attr", "channel", "stream_length", {
                "__term__": Count(_current_trial_observations())}],
        ],
    }


def _time_infer(field):
    return {
        "type": "TimeInfer",
        "sequence": A("channel", "stream_frames"),
        "codebook_type": STREAM_CODEBOOK_TYPE,
        "max_b": 8,
        "field": field,
        "max_steps": STREAM_HORIZON_UNITS,
    }


def project_stream_rule():
    """`time_axis` v1.2.0's forward reading, run on the channel's own stream.

    `order_fit` is the order the stream's generator was measured at and
    `crossing` is how many steps that generator takes to carry it to its frame
    origin — for a height, the ground. Nothing here knows that: the projection
    is the same domain-neutral operation whatever the channel measures.
    """
    return {
        "name": "srp_project_channel_stream_to_a_crossing",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "comment": (
            "The missing half of route (b). `crossing` at the MEASURED order is "
            "margin/rate generalised: an accelerating approach reports sooner "
            "than the linear reading, and the difference is the curvature the "
            "linear reading throws away. `horizon_units` is recorded ON the "
            "projection because `crossing` returns the bound BOTH when the "
            "stream crosses at it and when it never crosses at all; the "
            "consumer needs to tell a deadline from the absence of one."
        ),
        "match": [["effector", "has_sensed_channel", "channel"]],
        "where": And(
            Gt(d0("channel", "stream_length"), L(MINIMUM_STREAM_SAMPLES - 1)),
            absent(N("channel", "has_temporal_projection")),
        ),
        "effects": [
            ["add_node", "projection", "TemporalProjection", {
                "order_fit": {"__term__": _time_infer("order_fit")},
                "crossing": {"__term__": _time_infer("crossing")},
                "horizon_units": STREAM_HORIZON_UNITS,
                "stream_length": {"__term__": d0("channel", "stream_length")},
                "source": "channel_stream",
                "integer_native": 1,
                "output_authority": 0,
            }],
            ["add_edge", "channel", "has_temporal_projection", "projection"],
        ],
    }


def refresh_projection_rule():
    """A STALE deadline is worse than none.

    The mint above fires once. Without this, a body that has stopped
    descending would keep reporting the crossing it had while it was — a
    projection that outlives its evidence. Scoped by `source` so a projection
    some other faculty attached to a channel is never overwritten here.
    """
    return {
        "name": "srp_refresh_channel_projection_from_the_current_stream",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "comment": (
            "Unconditional over the projections this seed minted, so the "
            "crossing is always the reading of the stream as it stands rather "
            "than the reading it had when the projection was first attached. A "
            "pure function of the stream, so re-firing rewrites the same "
            "numbers and the fixpoint terminates."
        ),
        "match": [["channel", "has_temporal_projection", "projection"]],
        "where": Eq(A("projection", "source"), L("channel_stream")),
        "effects": [
            ["set_attr", "projection", "order_fit", {
                "__term__": _time_infer("order_fit")}],
            ["set_attr", "projection", "crossing", {
                "__term__": _time_infer("crossing")}],
            ["set_attr", "projection", "stream_length", {
                "__term__": d0("channel", "stream_length")}],
        ],
    }


def predict_surprise_rule():
    """Route (b): the forward model projects a crossing before it happens.

    `TemporalProjection` is `time_axis` v1.2.0's order-N reading of the
    channel's own stream: `crossing` is how many steps its measured generator
    takes to carry it to the frame origin.  Read at the MEASURED order, an
    accelerating approach reports sooner than a linear reading would.
    """
    crossing = d0("projection", "crossing")
    return {
        "name": "srp_predict_surprise_from_projected_crossing",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "comment": (
            "ANTICIPATION, NOT REACTION. A projected crossing inside the "
            "declared horizon promotes with NO contact having occurred. This is "
            "the route that lets a falling body reach for the ground before it "
            "arrives, and nothing here knows what falling is."
        ),
        # THE HORIZON IS THE LOOP'S OWN, NOT A LITERAL. `horizon_actions` is
        # the window the affordability projection already commits to; asking
        # "is this crossing inside the horizon I control over" is asking about
        # exactly that window, so the ledger is matched in rather than a number
        # copied next to it. A channel may still declare a longer horizon of
        # its own; whichever is longer wins.
        "match": [
            ["episode", "has_energy_ledger", "ledger"],
            ["episode", "has_embodied_effector", "effector"],
            ["effector", "has_sensed_channel", "channel"],
            ["channel", "has_temporal_projection", "projection"],
        ],
        "where": And(
            Gt(d0("projection", "order_fit"), L(0)),
            # AN ABSENT CROSSING IS NOT A CROSSING AT ZERO. Coalesced, a
            # projection carrying no crossing reads as one arriving THIS STEP —
            # maximum urgency conjured from a missing number, the same shape as
            # a flat stream reading as a deadline at the horizon.
            declared("projection", "crossing"),
            Lte(crossing, Max(d0("channel", "predict_horizon_units"),
                              d0("ledger", "horizon_actions"))),
            # A CROSSING AT THE PROJECTION'S OWN BOUND IS NOT A CROSSING. The
            # forward walk returns its bound both when the stream reaches its
            # origin exactly there and when it never reaches it at all, so a
            # flat or receding stream comes back carrying the bound. Promoting
            # on it would price "no measured deadline" as "deadline at the
            # horizon" — failing to have the property, priced as having it.
            # A projection that declares no bound (one another faculty
            # attached) is left exactly as it was.
            Or(Eq(A("projection", "horizon_units"), L(None)),
               Gt(A("projection", "horizon_units"), crossing)),
            absent(N("channel", "has_surprise")),
        ),
        "effects": [
            ["add_node", "surprise", "SurpriseSignal", {
                "route": "predicted",
                "surprise_units": 0,
                "crossing_units": {"__term__": crossing},
                "integer_native": 1,
                "output_authority": 0,
            }],
            ["add_edge", "channel", "has_surprise", "surprise"],
        ],
    }


# ----------------------------------------------------------------- promotion

def promote_rule():
    """Surprise mints a candidate. The axes stay SEPARATE — no scalar."""
    # Urgency is read off the clock, never authored: a shorter crossing is more
    # urgent, and a detected surprise (crossing 0) is maximally so.
    horizon = Max(d0("channel", "predict_horizon_units"),
                  d0("ledger", "horizon_actions"))
    urgency = Minus(horizon, Min(d0("surprise", "crossing_units"), horizon))
    # GREATER THAN ANYTHING REACHABLE — derived, so it cannot be out-guessed by
    # a body with a bigger budget than any constant would have anticipated.
    # Both ceilings are consulted because they are different quantities and the
    # larger is the one that has to be beaten.
    unpriced_floor = Plus(Max(d0("ledger", "stock_units"),
                              d0("ledger", "reachable_units")),
                          L(LATTICE_STEP_UNITS))
    return {
        "name": "srp_promote_surprised_channel_to_candidate",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "comment": (
            "The whole of authority allocation. An effector no goal is using "
            "becomes contestable the moment something about it is surprising — "
            "which is why nothing is ever zero and why no standing weight is "
            "needed. The axes are carried SEPARATELY into the collapse; this "
            "rule invents no scalar and picks no winner."
        ),
        "match": [
            ["episode", "has_energy_ledger", "ledger"],
            ["episode", "has_embodied_effector", "effector"],
            ["effector", "has_sensed_channel", "channel"],
            ["channel", "has_surprise", "surprise"],
        ],
        "where": absent(N("surprise", "promoted_candidate")),
        "effects": [
            ["add_node", "candidate", "PromotedCandidate", {
                "route": {"__term__": A("surprise", "route")},
                # Read from graph data with declared floors — never invented.
                "goal_relevance_units": {"__term__": d0("effector", "goal_relevance_units")},
                "urgency_units": {"__term__": urgency},
                "damage_units": {"__term__": d0("channel", "damage_units")},
                # PRICED AT THE DECLARED DEMAND, never at zero. An effector
                # that declares no cost is UNPRICED, not free; pricing it at 0
                # would make ignorance the cheapest option and it would win
                # every comparison. The floor is one step past the ledger's own
                # reach, so an unpriced option is not merely expensive — it is
                # unaffordable BY CONSTRUCTION, whatever the budget turns out
                # to be, and stays that way as the budget grows.
                "energy_cost_units": {"__term__": {
                    "type": "IfThenElse",
                    "cond": Gt(d0("effector", "release_cost_units"), L(0)),
                    "then": d0("effector", "release_cost_units"),
                    "other": unpriced_floor,
                }},
                "cost_priced": {"__term__": {
                    "type": "IfThenElse",
                    "cond": Gt(d0("effector", "release_cost_units"), L(0)),
                    "then": L(1), "other": L(0),
                }},
                "recoverability_units": {"__term__": d0("effector", "recoverability_units")},
                "surprise_units": {"__term__": d0("surprise", "surprise_units")},
                "provenance": {"__term__": A("channel", "provenance")},
                "affordable": 0,
                # The candidate IS the Pareto candidate — no shadow copy to
                # drift. `cognitive_pareto`'s `ParetoDominates` reads these.
                "dominated": 0,
                "verified": 1,
                "integer_native": 1,
                "output_authority": 0,
            }],
            ["add_edge", "surprise", "promoted_candidate", "candidate"],
            ["add_edge", "effector", "has_promoted_candidate", "candidate"],
        ],
    }


def affordability_rule():
    """The ledger gates the spend. A catch you cannot afford is not available."""
    return {
        "name": "srp_mark_candidate_affordable_against_ledger",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "comment": (
            "Whether the collapse MAY take a candidate is separate from whether "
            "it wants to. Reachable = min(stock, rate x horizon) already keeps "
            "the amount and rate ceilings apart; a candidate costing more than "
            "is reachable is marked unaffordable and stays visible, so the "
            "refusal is legible rather than silent."
        ),
        "match": [
            ["episode", "has_energy_ledger", "ledger"],
            ["episode", "has_embodied_effector", "effector"],
            ["effector", "has_promoted_candidate", "candidate"],
        ],
        "where": L(True),
        "effects": [
            # AMOUNT: can the stock cover it at all. This is the only test that
            # can refuse a candidate outright.
            # AN UNPRICED CANDIDATE IS NOT AN AFFORDABLE ONE. Coalesced, a
            # candidate carrying no cost compares as costing nothing and is
            # marked affordable — ignorance priced as the cheapest option,
            # which is the exact shape imported from the F16 frontier. A cost
            # that was never written is unaffordable until someone writes it.
            ["set_attr", "candidate", "affordable", {"__term__": {
                "type": "IfThenElse",
                "cond": Or(Not(declared("candidate", "energy_cost_units")),
                           Gt(d0("candidate", "energy_cost_units"),
                              d0("ledger", "stock_units"))),
                "then": L(0), "other": L(1),
            }}],
            # RATE: a finite converter does not make an escape cheaper or
            # impossible — it makes it SLOWER. The F16 measured the opposite
            # reading as a defect (a weaker engine priced as a cheaper escape),
            # so the rate ceiling lands in DURATION, never in price.
            # Ceiling division: (cost + rate - 1) / rate.
            ["set_attr", "candidate", "actions_required", {"__term__": {
                "type": "IDiv",
                "a": Minus(Plus(d0("candidate", "energy_cost_units"),
                                Max(d0("ledger", "rate_ceiling_units"), L(1))),
                           L(1)),
                "b": Max(d0("ledger", "rate_ceiling_units"), L(1)),
            }}],
            ["set_attr", "candidate", "ledger_reachable_units", {
                "__term__": d0("ledger", "reachable_units")}],
            ["set_attr", "candidate", "ledger_stock_units", {
                "__term__": d0("ledger", "stock_units")}],
        ],
    }


# ---------------------------------------------------- into the real collapse

# Signed so that GREATER IS BETTER on every axis, which is what
# `ParetoDominates` assumes.  Cost is therefore carried NEGATED: it is the one
# axis where more is worse.  No axis is scaled against another and no axis is
# summed — the negation is a sign convention, not a weighting.
AUTHORITY_AXES = (
    (0, "authority_goal_relevance", "goal_relevance_units", False),
    (1, "authority_urgency", "urgency_units", False),
    (2, "authority_damage", "damage_units", False),
    (3, "authority_energy_cost", "energy_cost_units", True),
    (4, "authority_recoverability", "recoverability_units", False),
)


def adopt_simulator_effector_rule():
    """A world adapter attaches effectors to its CONNECTION; the episode is the
    graph's own unit of embodiment. Adopting one into the other is the graph's
    decision about what this body is for it, not the adapter's."""
    return {
        "name": "srp_adopt_simulator_effector_into_episode",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "comment": (
            "An attached simulator publishes effectors under its connection. "
            "The episode adopts them so the ledger and the frontier can reach "
            "them. The adapter never writes this edge itself."
        ),
        "match": [
            ["agent", "has_embodied_development_episode", "episode"],
            ["agent", "has_embodied_simulator_connection", "connection"],
            ["connection", "has_embodied_effector", "effector"],
        ],
        "where": Not(Exists(N("episode", "has_embodied_effector"), "held",
                            {"type": "Eq", "a": V("held"), "b": V("effector")})),
        "effects": [["add_edge", "episode", "has_embodied_effector", "effector"]],
    }


def open_profile_rule():
    return {
        "name": "srp_open_authority_pareto_profile",
        "area": "general_cognition",
        "latency_class": "soft_realtime",
        "comment": (
            "One frontier per episode, declaring how many objectives it "
            "compares. `dimension_count` is the number of axes, not a weighting "
            "of them."
        ),
        "match": [["agent", "has_embodied_development_episode", "episode"]],
        "where": absent(N("episode", "has_authority_pareto_profile")),
        "effects": [
            ["add_node", "profile", "ParetoProfile", {
                "status": "open",
                "pareto_suspended": 0,
                "dimension_count": len(AUTHORITY_AXES),
                "identity": "effector_authority",
                "integer_native": 1,
                "output_authority": 0,
            }],
            ["add_edge", "episode", "has_authority_pareto_profile", "profile"],
        ],
    }


def publish_candidate_rule():
    """Hand the candidate to the EXISTING collapse. Nothing new arbitrates.

    An UNAFFORDABLE candidate is not published: the amount ceiling is the one
    outright refusal, so an act the stock cannot cover is not an option to be
    compared. It survives as a legible record on the effector, which is how the
    refusal stays inspectable instead of silent.
    """
    effects = [["add_edge", "profile", "has_pareto_candidate", "candidate"]]
    for ordinal, objective, key, negated in AUTHORITY_AXES:
        value = d0("candidate", key)
        if negated:
            value = Minus(L(0), value)
        effects.append(["add_node", f"value_{ordinal}", "ParetoValue", {
            "dimension_ordinal": ordinal,
            "objective": objective,
            "signed_value": {"__term__": value},
            "verified": 1,
            "integer_native": 1,
            "output_authority": 0,
        }])
        effects.append(["add_edge", "candidate", "has_pareto_value", f"value_{ordinal}"])
    return {
        "name": "srp_publish_candidate_to_authority_frontier",
        "area": "general_cognition",
        "latency_class": "soft_realtime",
        "comment": (
            "The promotion layer's whole output: a candidate with its axes "
            "carried SEPARATELY onto the frontier the rest of cognition already "
            "uses. `cp_recognize_relational_dominance` does the comparing; this "
            "seed never picks a winner. Cost is the only negated axis, because "
            "it is the only one where more is worse."
        ),
        "match": [
            ["episode", "has_authority_pareto_profile", "profile"],
            ["episode", "has_embodied_effector", "effector"],
            ["effector", "has_promoted_candidate", "candidate"],
        ],
        "where": And(
            Eq(d0("candidate", "affordable"), L(1)),
            absent(N("candidate", "has_pareto_value")),
        ),
        "effects": effects,
    }


def manifest() -> dict:
    return {
        "id": "surprise_promotion",
        "version": "1.2.0",
        "depends_on": ["energy_ledger", "time_axis", "cognitive_pareto"],
        "description": (
            "SURPRISE IS THE PROMOTION MECHANISM. A channel is not a candidate "
            "for authority until the model is surprised about it — either a "
            "reading contradicts its expectation (detected) or the forward "
            "model projects it to a crossing before contact (predicted). "
            "Surprise mints a candidate carrying its axes separately; the "
            "existing collapse decides. No standing per-effector weight, no "
            "scalar, and no rule that knows what a fall, a desk or a wall is. "
            "The resolution chain (measured -> expected -> declared) is a "
            "precondition rather than hygiene: a dark channel cannot surprise "
            "you, so it can never promote and its effector can never be "
            "rescued. v1.1.0 BUILDS THE STREAM route (b) needs: a channel's "
            "own observation history, scoped to the current trial, is read as "
            "a sequence and projected forward to a crossing, so the predicted "
            "route is reachable instead of merely present. It also replaces "
            "three declared literals with the graph data they were ratios to "
            "— the channel's measurement quantum, the ledger's control "
            "horizon, and the ledger's own reach as the floor an unpriced "
            "option must lose to."
        ),
        "microtheory": "surprise_promotion",
        # THE ONE PIECE OF DATA THE PROJECTION NEEDS: what shape a channel
        # sample is. `TimeInfer` reads which slots are coordinates from a
        # codebook part's `dim_types`; a channel sample is one relation with a
        # single coordinate slot, so this part says exactly that and nothing
        # else. It is held graph data, not a constant in the Term.
        "nodes": [
            {"local_id": 1, "type": STREAM_CODEBOOK_TYPE, "attrs": {
                "name": "channel_sample",
                "signature": [[0]],
                "dim_types": ["coord:value"],
                "integer_native": 1,
                "output_authority": 0,
            }},
        ],
        "edges": [],
        "productions": [
            {"provenance": "seed:surprise_promotion:has_sensed_channel-0",
             "src": {"type": "EmbodiedEffector", "var": "s"},
             "edge_type": "has_sensed_channel",
             "tgt": {"type": "SensedChannel", "var": "t"}},
            {"provenance": "seed:surprise_promotion:has_channel_observation-1",
             "src": {"type": "SensedChannel", "var": "s"},
             "edge_type": "has_channel_observation",
             "tgt": {"type": "ChannelObservation", "var": "t"}},
            {"provenance": "seed:surprise_promotion:has_channel_expectation-2",
             "src": {"type": "SensedChannel", "var": "s"},
             "edge_type": "has_channel_expectation",
             "tgt": {"type": "ChannelExpectation", "var": "t"}},
            {"provenance": "seed:surprise_promotion:observation_program-12",
             "src": {"type": "ChannelObservation", "var": "s"},
             "edge_type": "observed_under_motor_program",
             "tgt": {"type": "EmbodiedMotorProgram", "var": "t"}},
            {"provenance": "seed:surprise_promotion:has_surprise-3",
             "src": {"type": "SensedChannel", "var": "s"},
             "edge_type": "has_surprise",
             "tgt": {"type": "SurpriseSignal", "var": "t"}},
            {"provenance": "seed:surprise_promotion:promoted_candidate-4",
             "src": {"type": "SurpriseSignal", "var": "s"},
             "edge_type": "promoted_candidate",
             "tgt": {"type": "PromotedCandidate", "var": "t"}},
            {"provenance": "seed:surprise_promotion:has_promoted_candidate-5",
             "src": {"type": "EmbodiedEffector", "var": "s"},
             "edge_type": "has_promoted_candidate",
             "tgt": {"type": "PromotedCandidate", "var": "t"}},
            {"provenance": "seed:surprise_promotion:has_embodied_effector-6",
             "src": {"type": "EmbodiedDevelopmentEpisode", "var": "s"},
             "edge_type": "has_embodied_effector",
             "tgt": {"type": "EmbodiedEffector", "var": "t"}},
            {"provenance": "seed:surprise_promotion:connection_effector-11",
             "src": {"type": "EmbodiedSimulatorConnection", "var": "s"},
             "edge_type": "has_embodied_effector",
             "tgt": {"type": "EmbodiedEffector", "var": "t"}},
            {"provenance": "seed:surprise_promotion:authority_profile-8",
             "src": {"type": "EmbodiedDevelopmentEpisode", "var": "s"},
             "edge_type": "has_authority_pareto_profile",
             "tgt": {"type": "ParetoProfile", "var": "t"}},
            {"provenance": "seed:surprise_promotion:profile_candidate-9",
             "src": {"type": "ParetoProfile", "var": "s"},
             "edge_type": "has_pareto_candidate",
             "tgt": {"type": "PromotedCandidate", "var": "t"}},
            {"provenance": "seed:surprise_promotion:candidate_value-10",
             "src": {"type": "PromotedCandidate", "var": "s"},
             "edge_type": "has_pareto_value",
             "tgt": {"type": "ParetoValue", "var": "t"}},
            {"provenance": "seed:surprise_promotion:channel_projection-7",
             "src": {"type": "SensedChannel", "var": "s"},
             "edge_type": "has_temporal_projection",
             "tgt": {"type": "TemporalProjection", "var": "t"}},
        ],
        "rules": [
            resolve_measured_rule(),
            resolve_expected_rule(),
            resolve_declared_rule(),
            expect_from_program_rule(),
            expect_vertical_rule(),
            detect_surprise_rule(),
            scope_stream_rule(),
            stream_frames_rule(),
            project_stream_rule(),
            refresh_projection_rule(),
            predict_surprise_rule(),
            promote_rule(),
            affordability_rule(),
            adopt_simulator_effector_rule(),
            open_profile_rule(),
            publish_candidate_rule(),
        ],
    }


def main() -> int:
    output = ROOT / "seeds" / "surprise_promotion.json"
    output.write_text(json.dumps(manifest(), indent=1) + "\n", encoding="utf-8")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
