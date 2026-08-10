r"""EMIT seeds/vision_onoff.json — RUNG 6: the SIGNED SIMPLE LAYER via an ON/OFF split.

Authoring tool (CLAUDE.md: "tools/* — one-off authoring scripts that EMIT seed
manifests"). Not agent runtime. Run:  python tools/build_vision_onoff_seed.py

WHY THIS SEED EXISTS — the measured blocker (VISION_RUNG5_PREREG.md):

    Oja on nonneg binary input from w0>0 keeps weights STRICTLY POSITIVE
    (frac(w<0)=0.0000) => act = sum of POSITIVE weights over a field that is
    ~50% on for ANY orientation => DC-DOMINATED (baseline/act=1.011) => the
    oriented structure that IS in the weights never reaches the RESPONSE
    (OSI 0.004 vs an ideal Gabor's 1.000).

    Isolated by a controlled comparison: GABOR vs GABOR+DC -> identical weight
    anisotropy 0.8672, OSI 1.0000 vs 0.0000. Positivity alone destroys it.

THE BIOLOGY — the sign comes from the PATHWAY, not the weight:

  * Real retinas split into ON (depolarise to increments) and OFF (decrements)
    bipolar/ganglion pathways. Cortex receives a SIGNED signal carried on TWO
    NON-NEGATIVE channels.
  * DALE'S LAW: a neuron's synapses are sign-constant. Weights stay >= 0; a
    Unit's EFFECTIVE RF is w_ON - w_OFF.
  * The sign inversion happens in the RETINA (ON bipolars invert via mGluR6;
    OFF bipolars are sign-conserving), NOT in the cortical weight. Both
    pathways are EXCITATORY onto the simple cell, which is why the effective
    filter is signed:

        act = SUM_i w+_i * x_i  +  SUM_i w-_i * (1 - x_i)
            = SUM_i (w+_i - w-_i) * x_i  +  SUM_i w-_i
              \_________________/          \__________/
               SIGNED effective RF          a constant

    The DC that killed rung 5 becomes an additive CONSTANT instead of an
    inescapable multiplier on an all-positive filter.
  * Hubel & Wiesel / Reid & Alonso: a simple cell's orientation selectivity
    comes from spatially aligned, ADJACENT ON and OFF subregions. Growing that
    alignment is the rung.
  * Gjorgjieva et al. 2009: burst-timing-dependent plasticity robustly guides
    ON/OFF segregation in LGN — waves drive the segregation.

WHY SUBTRACTIVE NORMALISATION IS THE LEARNING RULE (and not plain Oja).

  Oja converges to the leading eigenvector of the UNCENTERED second-moment
  matrix E[zz^T], maximising E[(w.z)^2] = Var(w.z) + (E[w.z])^2 . In the split
  representation z = [x; 1-x]:

      Var(w.z) = d^T Cov(x) d   with d = w+ - w-      <- the SIGNED, oriented term
      E[w.z]   = 0.5 * ||w||_1                        <- maximised by w+ = w- = uniform

  The mean^2 term scales with N (for a 7x7 RF, ~24.5 at ||w||_2=1) and swamps
  lambda_max of the centered covariance (~3-6). So plain Oja on the split is
  PREDICTED to collapse to w+ ~ w- (d ~ 0, no orientation) — the DC mode wins
  again, one level up. This is stated in advance, and `subnorm=0` runs exactly
  that arm so the prediction is testable rather than asserted.

  Miller & MacKay 1994 ("The role of constraints in Hebbian learning") is the
  canonical result: SUBTRACTIVE normalisation projects out the uniform/DC mode
  and is what makes ON/OFF segregation and oriented RFs form; MULTIPLICATIVE
  normalisation does not (it preserves the dominant uniform mode). Miller 1994
  (J Neurosci) builds simple-cell RFs with segregated adjacent ON/OFF
  subregions from exactly this: ON/OFF-center inputs + correlation-based
  Hebbian + subtractive normalisation + saturating weight bounds [0, wmax].

      dw_i = eta * y * (x_i - xbar)  , then clip to [0, wmax]

  SUM_i dw_i = 0 exactly => the uniform mode is projected out; the [0,wmax]
  bounds are what make the outcome SEGREGATE rather than sit at the mean
  (saturation is the symmetry-breaking, exactly as in Miller).

  Note vs GCAL (Stevens 2013), per VISION_PRIOR_ART.md: GCAL is plain Hebb +
  DIVISIVE (multiplicative) normalisation, which Taylor-expands to our Oja.
  That is the stabiliser we already have and it is precisely the one Miller &
  MacKay show does NOT segregate. GCAL gets orientation from lateral
  interactions + a homeostatic threshold on the ACTIVATION function; that is a
  different, later question (contrast invariance) and is NOT this rung.

WHY A THRESHOLD IS REQUIRED, AND WHY IT IS THE MODEL AND NOT THE MEASURE.

  MEASURED AT CALIBRATION, before any gate, on the ideal exemplar: the split
  ALONE gives an ideal split-Gabor cell **OSI 0.0006** — a PERFECT signed simple
  cell reads as unoriented. The cause, isolated analytically and confirmed in
  the graph:

      act = SUM (w+ - w-) x  +  SUM w-        with SUM w- = 5.613 for the ideal
                                              Gabor, vs a signal of ~ +-2.3

      => the OFF channel's TONIC DRIVE sits ABOVE the signal, so act never
         reaches 0 at ANY orientation, rectification max(act,0) never bites, and
         the mean-over-phase F0 is ~5.1 at EVERY orientation (0 deg 5.120 vs
         90 deg 5.055) => a FLAT tuning curve.

      with a threshold that cancels the tonic drive:
         F0(0 deg) 2.314 vs F0(90 deg) 0.000  =>  OSI 1.0000

  So the split makes the FILTER signed but not the RESPONSE. The missing
  component is the SPIKE THRESHOLD — real simple cells' orientation selectivity
  in the FIRING RATE comes from thresholding a signed membrane potential (the
  "iceberg effect"; Priebe & Ferster 2008, Neuron 57:482). A cell without a
  threshold has no selectivity no matter how good its RF is.

  `theta` is therefore an EMA of the cell's OWN mean drive, and the output is
      rate = max(act - theta, 0)
  i.e. the cell fires only ABOVE its own running average. Parameter-free (no
  hand-set target), adaptive to whatever the tonic drive happens to be, and
  exactly the mean-removal that sensory adaptation performs.

  PLACEMENT IS THE POINT (VISION_PRIOR_ART.md's GCAL lesson): theta lives on the
  ACTIVATION FUNCTION, entirely OUTSIDE the learning rule, where it CANNOT flip
  the sign of dw. That is what makes it structurally unable to annihilate the
  way our BCM did (BCM's threshold flips dw's sign and converged to 0.004
  structure = death). GCAL (Stevens 2013) puts its homeostatic threshold in
  exactly this place, for exactly this reason.

  THIS IS A MODEL FIX, NOT METRIC SURGERY (PROTOCOL 5). The MEASURE — OSI on the
  rectified F0 tuning curve, probe period 4.0, rung 5's instrument — is
  UNCHANGED and is not touched again. What changed is the AGENT: it grew a
  threshold, because a cell without one cannot be orientation-selective in
  principle. The discovery came from the ideal-exemplar calibration
  (PROTOCOL 1's first test) BEFORE any hypothesis was gated, which is what that
  test is for.

EVERY ABLATION IS GRAPH DATA (PROTOCOL 0), never a Python code path:

  onoff   0 = the whole layer is inert (DEFAULT — every committed result
              reproduces byte-identically)
  split   1 = OFF cells invert (x_OFF = 1 - x) — the SIGNED pathway
          0 = OFF cells behave as ON cells (x_OFF = x) — a SINGLE non-negative
              channel. THE CONTROL: identical anatomy, identical synapse count,
              identical rules; ONLY the sign inversion is removed. This is
              rung 5's condition, and it isolates the SIGN rather than the
              anatomy (rung 4's lesson: an ablation that also removes anatomy
              is not null).
  subnorm 1 = Miller subtractive normalisation
          0 = plain Oja on the split
  frozen  1 = A REAL FREEZE. Gates ALL learning rules in this seed.
              THIS IS THE BUG FIX: `oja=0` IS NOT A FREEZE — bh_potentiate /
              bh_depress / bh_scale are each gated on `WaveParams.oja == 0.0`,
              so setting oja=0 does not switch learning off, it switches the
              OTHER learning rule ON (measured: 47.9 max |dw| per probe).
              A probe must never train the thing it measures.
"""
from __future__ import annotations

import json
import os

# --------------------------------------------------------------------------- #
#  Term helpers — plain JSON, the wire form the Rust evaluator reads
# --------------------------------------------------------------------------- #
def V(n):            return {"type": "Var", "name": n}
def L(v):            return {"type": "Lit", "value": v}
def A(node, key):    return {"type": "Attr", "node": node, "key": key}
def T(t):            return {"__term__": t}


def PARAM(seed_type, key):
    """Read a knob off the singleton params node — the `Pick(NodesOfType(...))`
    idiom every rule in vision_waves.json already uses for WaveParams."""
    return A({"type": "Pick", "source": {"type": "NodesOfType",
                                         "node_type": seed_type}}, key)


OO = lambda k: PARAM("OnOffParams", k)
WV = lambda k: PARAM("WaveParams", k)


def IN(node, et):    return {"type": "InNeighbours", "node": node,
                            "edge_type": et, "any_type": False}
def OUT(node, et):   return {"type": "Neighbours", "node": node,
                            "edge_type": et, "any_type": False}
def PICK(src):       return {"type": "Pick", "source": src}
def ITE(c, a, b):    return {"type": "IfThenElse", "cond": c, "then": a, "other": b}
def GT(a, b):        return {"type": "Gt", "a": a, "b": b}
def GTE(a, b):       return {"type": "Gte", "a": a, "b": b}
def LT(a, b):        return {"type": "Lt", "a": a, "b": b}
def LTE(a, b):       return {"type": "Lte", "a": a, "b": b}
def EQ(a, b):        return {"type": "Eq", "a": a, "b": b}
def AND(*xs):        return {"type": "And", "items": list(xs)}
def NOT(x):          return {"type": "Not", "arg": x}
def PLUS(*xs):       return {"type": "Plus", "items": list(xs)}
def TIMES(*xs):      return {"type": "Times", "items": list(xs)}
def MINUS(a, b):     return {"type": "Minus", "a": a, "b": b}
def DIV(a, b):       return {"type": "Div", "a": a, "b": b}
def MIN(*xs):        return {"type": "Min", "items": list(xs)}
def MAX(*xs):        return {"type": "Max", "items": list(xs)}
def FOLD(src, var, acc, init, body):
    return {"type": "Fold", "source": src, "var_name": var, "acc_name": acc,
            "init": init, "body": body}
def EXISTS(src, var, pred):
    return {"type": "Exists", "source": src, "var_name": var, "predicate": pred}


# The layer is live only when `onoff` is selected. Every rule carries this.
LIVE = GT(OO("onoff"), L(0.5))
# A real freeze — gates every LEARNING rule (never the activation rules: a
# frozen cell must still RESPOND, or the probe would measure silence).
AWAKE = LT(OO("frozen"), L(0.5))

# x for THIS synapse's presynaptic Bipolar (its burst this step).
PRE_B = A(PICK(IN(V("sy"), "oo_pre")), "bursting")


# --------------------------------------------------------------------------- #
#  RULES
# --------------------------------------------------------------------------- #
def rule_bipolar_burst():
    """THE ON/OFF SPLIT ITSELF — one wave field, two non-negative channels.

    Each Bipolar reads the SAME RetinaCell (its `drives` source) and the SAME
    burst-within-window latency the rest of the ladder uses. ON bursts when its
    cell burst within the window; OFF bursts when it did NOT. So the waves drive
    BOTH channels — ON/OFF segregation is an OUTCOME of what the Units learn,
    never an input (stage II cholinergic waves drive ON and OFF alike; hand-
    segregating the waves would be the bolt-on error).

    `split=0` makes OFF cells behave exactly like ON cells (x_OFF = x): a single
    non-negative channel, i.e. rung 5's condition, with the anatomy untouched.
    """
    X = ITE(LTE(MINUS(A(V("r"), "step"), A(V("c"), "last_burst")),
                WV("window_steps")), L(1.0), L(0.0))
    inverted = MINUS(L(1.0), X)
    return {
        "name": "oo_bipolar_burst",
        "comment": (
            "THE SIGNED PATHWAY. ON (polarity>0) bursts iff its RetinaCell burst "
            "within WaveParams.window_steps; OFF bursts iff it did NOT (x_OFF = "
            "1 - x_ON). Both channels are NON-NEGATIVE and both are driven by the "
            "SAME wave field — segregation is what the Units must GROW, not what "
            "they are handed. The sign inversion is retinal (mGluR6 in ON "
            "bipolars), which is why cortical weights can stay >= 0 (Dale) while "
            "the EFFECTIVE RF w+ - w- is signed. `split=0` collapses OFF onto ON "
            "(x_OFF = x) = a single non-negative channel = rung 5's condition, "
            "with identical anatomy and identical synapse count, so the ablation "
            "isolates the SIGN and nothing else. Phase-guarded by bstep so it "
            "fires once per cell per step and oo_sunit_activate cannot race it."),
        "match_type": "Bipolar",
        "match": [["r", "has_bipolar", "b"], ["c", "drives", "b"]],
        "where": AND(LIVE, LT(A(V("b"), "bstep"), A(V("r"), "step"))),
        "effects": [
            ["set_attr", "b", "bursting",
             T(ITE(GT(A(V("b"), "polarity"), L(0.0)),
                   X,
                   ITE(GT(OO("split"), L(0.5)), inverted, X)))],
            ["set_attr", "b", "bstep", T(A(V("r"), "step"))],
        ],
    }


def rule_sunit_activate():
    """act = SUM over the SUnit's synapses of weight * pre-Bipolar burst.

    Both pathways arrive EXCITATORY (all weights >= 0, Dale); the signedness is
    already carried by the OFF channel's inversion, so this sum IS
    `SUM (w+ - w-) x + SUM w-`.

    ORDERING, not racing: the guard requires that NO presynaptic Bipolar is
    still stale (`Not Exists` one whose bstep < step) — the same data-dependency
    idiom `bh_sum_weights` uses to sequence itself after learning without any
    Python sequencing.
    """
    stale_pre = EXISTS(IN(V("u"), "oo_post"), "sy",
                       LT(A(PICK(IN(V("sy"), "oo_pre")), "bstep"),
                          A(V("r"), "step")))
    return {
        "name": "oo_sunit_activate",
        "comment": (
            "The signed simple cell's drive: sum of NON-NEGATIVE weights over "
            "BOTH channels = SUM (w+ - w-) x + SUM w-. The DC that rung 5 "
            "measured as an inescapable multiplier (baseline/act = 1.011) is now "
            "an additive constant, and the modulated part is a SIGNED filter. "
            "Guarded on every presynaptic Bipolar having already burst this step, "
            "so the fixpoint cannot read a stale channel."),
        "match_type": "SUnit",
        "match": [["r", "has_sunit", "u"]],
        "where": AND(LIVE, LT(A(V("u"), "act_step"), A(V("r"), "step")),
                     NOT(stale_pre)),
        "effects": [
            ["set_attr", "u", "act",
             T(FOLD(IN(V("u"), "oo_post"), "sy", "acc", L(0.0),
                    PLUS(V("acc"), TIMES(A(V("sy"), "weight"), PRE_B))))],
            ["set_attr", "u", "act_step", T(A(V("r"), "step"))],
        ],
    }


def rule_sunit_rate():
    """THE THRESHOLD — the cell's OUTPUT: rate = max(act - theta, 0).

    NOT gated by `frozen`: a frozen cell must still RESPOND, or a probe would
    measure silence. Freezing is about PLASTICITY, never about activation."""
    return {
        "name": "oo_sunit_rate",
        "comment": (
            "THE ICEBERG (Priebe & Ferster 2008): a simple cell's orientation "
            "selectivity in the FIRING RATE comes from thresholding a signed "
            "membrane potential. Measured at calibration: WITHOUT this, the ideal "
            "split-Gabor scores OSI 0.0006 — the OFF channel's tonic drive "
            "(SUM w- = 5.613) sits above the signal (~2.3), so act never reaches "
            "0 at any orientation, rectification never bites, and F0 is flat "
            "(5.120 at 0 deg vs 5.055 at 90 deg). WITH it, the same cell scores "
            "OSI 1.0000. The split makes the FILTER signed; the threshold is what "
            "makes the RESPONSE signed. Deliberately NOT gated by `frozen` — a "
            "frozen cell must still respond or the probe measures silence."),
        "match_type": "SUnit",
        "match": [["r", "has_sunit", "u"]],
        "where": AND(LIVE, LT(A(V("u"), "rate_step"), A(V("r"), "step")),
                     EQ(A(V("u"), "act_step"), A(V("r"), "step"))),
        "effects": [
            ["set_attr", "u", "rate",
             T(MAX(MINUS(A(V("u"), "act"), A(V("u"), "theta")), L(0.0)))],
            ["set_attr", "u", "rate_step", T(A(V("r"), "step"))],
        ],
    }


def rule_sunit_adapt_theta():
    """HOMEOSTASIS, IN GCAL'S PLACE: theta <- theta + theta_rate*(act - theta),
    an EMA of the cell's own drive, so the cell fires only above its own average.

    Parameter-free in the sense that matters: no hand-set target activity — the
    threshold finds whatever the tonic drive is. It sits on the ACTIVATION
    FUNCTION, entirely outside `oo_learn_*`, so it CANNOT flip the sign of dw —
    which is exactly why it cannot annihilate the way BCM did (BCM's sliding
    threshold flips dw's sign and converged to 0.004 structure, i.e. death).

    Gated by `frozen`: adaptation IS plasticity, and a probe that let theta chase
    the probe stimulus would be the instrument training itself — the same class
    of bug as `oja=0` is not a freeze."""
    return {
        "name": "oo_sunit_adapt_theta",
        "comment": (
            "GCAL's homeostatic threshold, in GCAL's PLACE (VISION_PRIOR_ART.md): "
            "on the activation function, OUTSIDE the learning rule, where it "
            "cannot flip dw's sign — structurally unable to annihilate, unlike "
            "BCM whose threshold does flip the sign and converged to death "
            "(0.004). theta is an EMA of the cell's own act, so it adapts to "
            "whatever tonic drive the OFF channel happens to impose rather than "
            "being hand-set. Guarded on rate_step==step so it can only move AFTER "
            "this step's rate has been read (no race), and gated by `frozen` "
            "because adaptation is plasticity: a probe must never let theta chase "
            "the probe."),
        "match_type": "SUnit",
        "match": [["r", "has_sunit", "u"]],
        "where": AND(LIVE, AWAKE, GT(OO("homeo"), L(0.5)),
                     LT(A(V("u"), "theta_step"), A(V("r"), "step")),
                     EQ(A(V("u"), "rate_step"), A(V("r"), "step"))),
        "effects": [
            ["set_attr", "u", "theta",
             T(PLUS(A(V("u"), "theta"),
                    TIMES(OO("theta_rate"),
                          MINUS(A(V("u"), "act"), A(V("u"), "theta")))))],
            ["set_attr", "u", "theta_step", T(A(V("r"), "step"))],
        ],
    }


def rule_sunit_burst_winner():
    """WINNER-TAKE-ALL over the signed layer — the competition that makes the
    population DIFFERENTIATE (the same Argmax/Eq single-survivor idiom
    `wv_unit_burst_winner` uses). Without it every SUnit chases the same
    component. Rung 5 measured the failure mode this must avoid: ONE unit won
    all 192 probes, i.e. a stimulus-INDEPENDENT population code."""
    return {
        "name": "oo_sunit_burst_winner",
        "comment": (
            "WTA over SUnits by act. Competition is the symmetry-breaking that "
            "makes the population differentiate rather than converge on one "
            "component; the pooling layer's LACK of it is what rung 5 diagnosed "
            "as its positive control's failure."),
        "match_type": "SUnit",
        "match": [["r", "has_sunit", "u"]],
        "where": AND(
            LIVE,
            LT(A(V("u"), "burst_step"), A(V("r"), "step")),
            EQ(A(V("u"), "rate_step"), A(V("r"), "step")),
            GT(A(V("u"), "rate"), L(0.0)),
            EQ(V("u"), {"type": "Argmax", "source": OUT(V("r"), "has_sunit"),
                        "var_name": "u2", "value": A(V("u2"), "rate"),
                        "default": None}),
        ),
        "effects": [
            ["set_attr", "u", "bursting", 1.0],
            ["set_attr", "u", "burst_step", T(A(V("r"), "step"))],
            ["set_attr", "u", "last_burst", T(A(V("r"), "step"))],
        ],
    }


def rule_sunit_xbar():
    """PHASE 1 of subtractive normalisation — the mean input WITHIN EACH CHANNEL:
    xbar_on = mean of x over the ON synapses, xbar_off likewise over the OFF.

    WHY PER-CHANNEL, AND NOT ONE POOLED MEAN — measured, not guessed. The first
    cut used a single pooled xbar over all synapses. Because ON and OFF are
    complementary (x_OFF = 1 - x_ON), that pooled mean is EXACTLY 0.5 whatever
    the input; but the wave field is SPARSE (ON ~19.5% / OFF ~80.5% active), so
    every OFF synapse saw (x - 0.5) = +0.3 on average and every ON synapse -0.3.
    The rule therefore had a SYSTEMATIC drift with nothing to oppose it: every
    OFF weight saturated to wmax, every ON weight to 0, and the RF collapsed to a
    UNIFORM ONE-POLARITY BLOB — not segregated subregions. The convergence check
    measured exactly that: drift 0.005 -> 0.526, clumpiness 0.508 -> 1.000, and
    OSI DECAYING 0.40 -> 0.167, i.e. a transient, which PROTOCOL 2 forbids
    running arms on.

    Miller & MacKay's model never meets this because its ON and OFF input layers
    have SYMMETRIC statistics by construction. Ours do not — sparse waves are
    the honest input, so the constraint must be applied per pathway. That is also
    the more biological reading: homeostatic synaptic scaling is pathway-specific
    (ON and OFF thalamic afferents are distinct populations), so each channel
    normalises against its own mean.

    With per-channel centering, SUM_ON dw = 0 and SUM_OFF dw = 0 independently:
    no systematic drift in either channel, competition preserved WITHIN each, and
    the only thing left that can grow is genuine covariance structure — which is
    the ON/OFF subregion layout.

    Non-local across the unit's synapses (like `bh_sum_weights`' Fold) and
    phase-guarded by `xbar_step` so `oo_learn_sub` cannot race it. n_on/n_off are
    positional anatomy the adapter wired."""
    x = PRE_B
    on_sum = FOLD(IN(V("u"), "oo_post"), "sy", "acc", L(0.0),
                  PLUS(V("acc"), ITE(GT(A(V("sy"), "polarity"), L(0.0)),
                                     x, L(0.0))))
    off_sum = FOLD(IN(V("u"), "oo_post"), "sy", "acc", L(0.0),
                   PLUS(V("acc"), ITE(GT(A(V("sy"), "polarity"), L(0.0)),
                                      L(0.0), x)))
    return {
        "name": "oo_sunit_xbar",
        "comment": (
            "Subtractive normalisation, phase 1 (Miller & MacKay 1994), applied "
            "PER CHANNEL. A single pooled mean is exactly 0.5 here (ON and OFF are "
            "complementary), which does not center EITHER channel when the waves "
            "are sparse (ON ~19.5% / OFF ~80.5%): the rule then drifts "
            "systematically, every OFF weight saturates to wmax and every ON to 0, "
            "and the RF collapses to a uniform one-polarity BLOB — measured as "
            "drift 0.005 -> 0.526, clumpiness -> 1.000, OSI decaying 0.40 -> 0.167. "
            "Centering each pathway on its OWN mean makes SUM_ON dw = 0 and "
            "SUM_OFF dw = 0 independently, so no systematic drift exists in either "
            "channel and only real covariance structure can grow. Miller's model "
            "never hits this because its ON/OFF layers are symmetric by "
            "construction; sparse waves are not."),
        "match_type": "SUnit",
        "match": [["r", "has_sunit", "u"]],
        "where": AND(LIVE, AWAKE, GT(OO("subnorm"), L(0.5)),
                     EQ(A(V("u"), "bursting"), L(1.0)),
                     EQ(A(V("u"), "rate_step"), A(V("r"), "step")),
                     LT(A(V("u"), "xbar_step"), A(V("r"), "step"))),
        "effects": [
            ["set_attr", "u", "xbar_on", T(DIV(on_sum, A(V("u"), "n_on")))],
            ["set_attr", "u", "xbar_off", T(DIV(off_sum, A(V("u"), "n_off")))],
            ["set_attr", "u", "xbar_step", T(A(V("r"), "step"))],
        ],
    }


def rule_learn_sub():
    """PHASE 2 — MILLER'S RULE: dw = eta*y*(x - xbar), clipped to [0, wmax].

    SUM_i dw_i = 0 exactly, so the uniform mode is projected out and competition
    is zero-sum: 'this synapse grew' MEANS 'another shrank'. The [0, wmax]
    bounds are Dale (>= 0) plus the saturation that makes the outcome SEGREGATE
    instead of resting at the mean — in Miller's model the bounds are the
    symmetry-breaking, not a safety rail."""
    y = A(V("u"), "rate")
    x = A(PICK(IN(V("sy"), "oo_pre")), "bursting")
    xbar_pol = ITE(GT(A(V("sy"), "polarity"), L(0.0)),
                   A(V("u"), "xbar_on"), A(V("u"), "xbar_off"))
    dw = TIMES(OO("oo_eta"), y, MINUS(x, xbar_pol))
    return {
        "name": "oo_learn_sub",
        "comment": (
            "dw = eta*y*(x - xbar) then clip to [0, wmax]. Subtractive => "
            "SUM dw = 0 => the DC/uniform mode cannot grow, so the only mode "
            "left to grow is the SIGNED one (w+ vs w- differentiating by "
            "location) — which is exactly the ON/OFF subregion structure Hubel & "
            "Wiesel's simple cells have. Clipping at 0 is Dale's law; clipping at "
            "wmax is the saturation that makes it segregate rather than settle at "
            "the mean. Local: reads only this synapse, its pre Bipolar, and its "
            "post SUnit's own totals."),
        "match_type": "OOSynapse",
        "match": [["b", "oo_pre", "sy"], ["sy", "oo_post", "u"]],
        "where": AND(LIVE, AWAKE, GT(OO("subnorm"), L(0.5)),
                     LT(A(V("sy"), "touched"), A(V("u"), "xbar_step")),
                     EQ(A(V("u"), "bursting"), L(1.0))),
        "effects": [
            ["set_attr", "sy", "weight",
             T(MIN(MAX(PLUS(A(V("sy"), "weight"), dw), L(0.0)), OO("oo_wmax")))],
            ["set_attr", "sy", "touched", T(A(V("u"), "xbar_step"))],
        ],
    }


def rule_learn_oja():
    """THE OTHER ARM, as graph data: plain Oja on the split (`subnorm=0`).

    w <- w(1 - eta*y^2) + eta*y*x — the identical rule `oja_learn` runs on the
    unsigned layer, here on the split input. PREDICTED IN ADVANCE to collapse to
    w+ ~ w- (no orientation), because Oja maximises the UNCENTERED second moment
    and its (E[w.z])^2 term is maximised by the uniform mode; see the module
    docstring. Shipping it as an arm is what makes that prediction testable."""
    y = A(V("u"), "rate")
    x = A(PICK(IN(V("sy"), "oo_pre")), "bursting")
    return {
        "name": "oo_learn_oja",
        "comment": (
            "Plain Oja on the signed input: w <- w(1 - eta*y^2) + eta*y*x. The "
            "MULTIPLICATIVE stabiliser (== GCAL's divisive normalisation to first "
            "order, VISION_PRIOR_ART.md) — which Miller & MacKay 1994 show "
            "preserves the uniform mode and therefore cannot segregate ON from "
            "OFF. Run as the `subnorm=0` arm so the prediction is measured, not "
            "asserted."),
        "match_type": "OOSynapse",
        "match": [["b", "oo_pre", "sy"], ["sy", "oo_post", "u"]],
        # NOTE: `r` (the Retina) is deliberately NOT referenced here. An earlier
        # cut guarded on `rate_step == r.step` while `r` was UNBOUND in `match`
        # — so this rule NEVER FIRED and the `subnorm=0` arm was silently "no
        # learning at all" rather than "plain Oja" (measured: max |dw| = 0.000000
        # at both etas, which is what exposed it). The `touched < rate_step`
        # guard already sequences this after `oo_sunit_rate`, exactly as
        # `oo_learn_sub` does, with no clock reference needed.
        "where": AND(LIVE, AWAKE, LT(OO("subnorm"), L(0.5)),
                     LT(A(V("sy"), "touched"), A(V("u"), "rate_step")),
                     EQ(A(V("u"), "bursting"), L(1.0))),
        "effects": [
            ["set_attr", "sy", "weight",
             T(MAX(PLUS(TIMES(A(V("sy"), "weight"),
                              MINUS(L(1.0), TIMES(OO("oo_eta"), y, y))),
                        TIMES(OO("oo_eta"), y, x)), L(0.0)))],
            ["set_attr", "sy", "touched", T(A(V("u"), "rate_step"))],
        ],
    }


def build() -> dict:
    return {
        "id": "vision_onoff",
        "version": "1.0.0",
        "depends_on": ["vision_waves"],
        "description": (
            "RUNG 6 — THE SIGNED SIMPLE LAYER via an ON/OFF RETINAL SPLIT. Rung 5 "
            "measured why the Units have no orientation-selective RESPONSE (OSI "
            "0.004 vs an ideal Gabor's 1.000): Oja on non-negative input keeps "
            "weights strictly positive (frac(w<0)=0.0000), so the response is "
            "DC-dominated and the oriented structure that IS in the weights never "
            "reaches it (GABOR vs GABOR+DC: identical anisotropy 0.8672, OSI "
            "1.0000 vs 0.0000). Biology does not force the sign into the WEIGHT — "
            "it splits the RETINA into ON and OFF pathways and keeps synapses "
            "sign-constant (Dale), so the effective RF w+ - w- is signed while "
            "every weight stays >= 0. One wave field drives BOTH channels "
            "(stage II cholinergic waves are not segregated; Gjorgjieva 2009 has "
            "burst-timing driving ON/OFF segregation), so aligned adjacent ON/OFF "
            "subregions (Hubel & Wiesel; Reid & Alonso) are an OUTCOME to grow, "
            "never an input. Learning is Miller & MacKay's subtractive "
            "normalisation, the canonical rule for exactly this: it projects out "
            "the uniform/DC mode that multiplicative/divisive normalisation "
            "(our Oja == GCAL's, to first order) preserves. onoff=0 by DEFAULT so "
            "every committed result reproduces byte-identically."),
        "microtheory": {
            "name": "vision_onoff",
            "description": (
                "the sign comes from the PATHWAY, not the weight: one wave field "
                "-> two non-negative retinal channels (ON: x, OFF: 1-x) -> a "
                "cortical cell with non-negative weights whose EFFECTIVE receptive "
                "field w+ - w- is signed; subtractive normalisation projects out "
                "the DC mode so the signed, oriented mode is the only one that can "
                "grow."),
        },
        "nodes": [{
            "local_id": 0,
            "type": "OnOffParams",
            "attrs": {
                "name": "default",
                "onoff": 0.0,
                "split": 1.0,
                "subnorm": 1.0,
                "frozen": 0.0,
                "oo_eta": 5e-4,
                "oo_wmax": 2.0,
                "theta_rate": 0.05,
                "homeo": 1.0,
                "comment": (
                    "ALL knobs are GRAPH DATA (PROTOCOL 0) — every ablation is the "
                    "agent's own configuration, never a Python code path. "
                    "onoff: 0 (DEFAULT) = the layer is inert, so every committed "
                    "result reproduces byte-identically (PROTOCOL 9). "
                    "split: 1 = OFF cells invert (x_OFF = 1-x), the SIGNED pathway; "
                    "0 = OFF behaves as ON (x_OFF = x) = a SINGLE non-negative "
                    "channel = rung 5's condition. The control changes ONLY the "
                    "sign — identical anatomy, identical synapse count, identical "
                    "rules — because rung 4 learned the hard way that an ablation "
                    "which also removes anatomy is not null. "
                    "subnorm: 1 = Miller & MacKay subtractive normalisation; 0 = "
                    "plain Oja (predicted to collapse to the uniform mode). "
                    "frozen: 1 = A REAL FREEZE gating every learning rule here. "
                    "THE BUG IT FIXES: `oja=0` IS NOT A FREEZE — bh_potentiate / "
                    "bh_depress / bh_scale are each gated on WaveParams.oja==0.0, "
                    "so oja=0 switches the OTHER learning rule ON (measured: "
                    "|dw| up to 47.9 across a single probe, driving three different "
                    "hand-set poolings to one attractor). A probe must never train "
                    "what it measures. "
                    "oo_eta: 5e-4, the regime rung 2's Oja check measured as stable "
                    "(2e-3 diverges; the eta*y^2 < 1 bound). "
                    "theta_rate: the EMA timescale of the spike threshold "
                    "(theta <- theta + theta_rate*(act - theta)), a timescale, "
                    "not a tuned optimum. homeo: 1 = the threshold adapts; 0 = it "
                    "is pinned (the no-threshold arm — measured to give the ideal "
                    "split-Gabor OSI 0.0006, i.e. no selectivity at all). "
                    "oo_wmax: the saturating upper bound. In Miller's model the "
                    "bounds are not a safety rail — saturation is the "
                    "symmetry-breaking that makes subregions SEGREGATE rather than "
                    "rest at the mean."),
            },
        }],
        "edges": [],
        "productions": [
            {"src": {"type": "Retina", "var": "a"}, "edge_type": "has_bipolar",
             "tgt": {"type": "Bipolar", "var": "b"},
             "provenance": "seed:vision_onoff:has_bipolar"},
            {"src": {"type": "RetinaCell", "var": "a"}, "edge_type": "drives",
             "tgt": {"type": "Bipolar", "var": "b"},
             "provenance": "seed:vision_onoff:drives"},
            {"src": {"type": "Bipolar", "var": "a"}, "edge_type": "oo_pre",
             "tgt": {"type": "OOSynapse", "var": "b"},
             "provenance": "seed:vision_onoff:oo_pre"},
            {"src": {"type": "OOSynapse", "var": "a"}, "edge_type": "oo_post",
             "tgt": {"type": "SUnit", "var": "b"},
             "provenance": "seed:vision_onoff:oo_post"},
            {"src": {"type": "Retina", "var": "a"}, "edge_type": "has_sunit",
             "tgt": {"type": "SUnit", "var": "b"},
             "provenance": "seed:vision_onoff:has_sunit"},
        ],
        "rules": [
            rule_bipolar_burst(),
            rule_sunit_activate(),
            rule_sunit_rate(),
            rule_sunit_adapt_theta(),
            rule_sunit_burst_winner(),
            rule_sunit_xbar(),
            rule_learn_sub(),
            rule_learn_oja(),
        ],
    }


if __name__ == "__main__":
    dst = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "seeds", "vision_onoff.json")
    with open(dst, "w") as fh:
        json.dump(build(), fh, indent=1)
        fh.write("\n")
    print(f"wrote {dst}")
