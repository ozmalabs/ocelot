"""build_vision_eye_seed — EMIT seeds/vision_eye.json.

An authoring tool (CLAUDE.md: "tools/* — one-off authoring scripts that EMIT
seed manifests; deletable; not agent runtime"). It contains NO agent logic: it
is a JSON writer with named helpers so the Term-trees are readable.

THE EYE'S CALIBRATION FRONT END. Three mechanisms, each OFF behind
`EyeParams.eye = 0` so every committed vision result reproduces byte-identically:

  1. LOG RECEPTOR (Weber-Fechner)      — `ey_receptor_log`  / `ey_receptor_lin`
  2. ADAPTIVE REFERENCE theta (GCAL)   — `ey_xbar` / `ey_adapt_theta` / `ey_response`
  3. ENGBERT SELF-AVOIDING-WALK DRIFT  — `ey_saw_*`

THE THEORY (VISION_PRIOR_ART.md; the creator's framing). There is no view from
nowhere: the substrate is a log-weighted RELATIVE admissibility grammar, and in
log space only differences exist — log(a) - log(b) = log(a/b). The eye is the
layer that establishes the REFERENCE against which everything later is defined:

  * the receptor takes log I, so an illumination change x k becomes an ADDITIVE
    constant log k rather than a multiplicative gain;
  * theta is an adaptive reference point that tracks the cell's own mean drive,
    so `resp = max(log I - theta, 0)` SUBTRACTS that constant away and is
    invariant to k. In LINEAR mode the same theta cannot undo a multiplicative
    change, so the response moves with k. That contrast is the decisive gate.

theta's PLACEMENT is the second steal (VISION_PRIOR_ART.md 2.3): GCAL's theta
sits on the ACTIVATION FUNCTION, outside the learning rule, where it cannot flip
the sign of dw. BCM's theta sits INSIDE the rule and gates the sign of dw — and
when it outran activity this tree's BCM annihilated to 0.004. Both placements
ship here, selected by `theta_mode` as DATA, so the comparison is measured
rather than asserted.
"""
from __future__ import annotations

import json
import os

# ---------------------------------------------------------------- Term helpers
def lit(v):
    return {"type": "Lit", "value": v}


def var(n):
    return {"type": "Var", "name": n}


def attr(node, key):
    return {"type": "Attr", "node": node, "key": key}


def param(key):
    """Read a knob off the singleton EyeParams node."""
    return attr({"type": "Pick",
                 "source": {"type": "NodesOfType", "node_type": "EyeParams"}},
                key)


def plus(*xs):
    return {"type": "Plus", "items": list(xs)}


def times(*xs):
    return {"type": "Times", "items": list(xs)}


def minus(a, b):
    return {"type": "Minus", "a": a, "b": b}


def div(a, b):
    return {"type": "Div", "a": a, "b": b}


def mx(*xs):
    return {"type": "Max", "items": list(xs)}


def mn(*xs):
    return {"type": "Min", "items": list(xs)}


def transfer(drive, theta):
    """GCAL/LISSOM's activation function f: half-wave rectify at `theta`, then
    SATURATE at `rmax`.

        f(s) = min( max(s - theta, 0), rmax )

    THE SATURATION IS NOT OPTIONAL AND IS NOT A TUNED CONSTANT — it is REQUIRED
    by mu, which this seed already took from GCAL. mu = 0.024 is GCAL's TARGET
    AVERAGE ACTIVITY, and a target average is only meaningful as a FRACTION OF A
    MAXIMUM; taking their target rate while leaving the rate scale unbounded is
    an incoherent transcription of one equation. rmax = 1.0 IS that scale, so
    mu = 0.024 means what GCAL means by it: 2.4% of maximum.

    MEASURED, which is why this is here rather than in the first draft. With an
    unbounded f, theta rises in proportion to a response that can spike
    arbitrarily high (measured: 5.93) but falls at only lam*mu = 2.4e-4 per
    step. So one early spike ratchets theta far above the drive and the cell is
    silenced for ~13,500 steps. At the UNIT this silenced the theta-OUTSIDE arm
    completely — meanrate 0.000000, max|dw| 0.000e+00, weights frozen — and the
    arm then looked STABLE (||w||/||w0|| pinned at 0.6188 out to 6400 steps)
    while it was merely INERT. That is exactly the failure PROTOCOL §4 names:
    "a mechanism could pass by making itself inert". Bounding f bounds theta's
    rise to lam*(rmax - mu) per step and the ratchet cannot happen.
    """
    return mn(mx(minus(drive, theta), lit(0.0)), param("rmax"))


def log(a):
    return {"type": "Log", "arg": a}


def pow_(a, b):
    return {"type": "Pow", "a": a, "b": b}


def gt(a, b):
    return {"type": "Gt", "a": a, "b": b}


def lt(a, b):
    return {"type": "Lt", "a": a, "b": b}


def eq(a, b):
    return {"type": "Eq", "a": a, "b": b}


def and_(*xs):
    return {"type": "And", "items": list(xs)}


def neighbours(node, et):
    return {"type": "Neighbours", "node": node, "edge_type": et, "any_type": False}


def in_neighbours(node, et):
    return {"type": "InNeighbours", "node": node, "edge_type": et, "any_type": False}


def fold(source, var_name, acc_name, init, body):
    return {"type": "Fold", "source": source, "var_name": var_name,
            "acc_name": acc_name, "init": init, "body": body}


def argmin(source, var_name, value):
    return {"type": "Argmin", "source": source, "var_name": var_name,
            "value": value, "default": None}


def term(t):
    return {"__term__": t}


# ---- the knob idiom: an arm is DATA on EyeParams, never a Python code path ---
ON = gt(param("eye"), lit(0.5))            # master switch, default 0
NOT_FROZEN = lt(param("frozen"), lit(0.5))  # a probe must move no weight

# ---------------------------------------------------------------------------
# THE TWO PHASES — and where the separation actually lives
# ---------------------------------------------------------------------------
# The creator's correction, and it is not a tweak: WAVES CANNOT CALIBRATE
# PHOTOMETRIC RESPONSE TO EXTERNAL ILLUMINATION BEFORE PHOTOTRANSDUCTION WORKS.
# There are TWO calibrations, at different times, of different things:
#
#   PHASE 0 — pre-visual. Waves are endogenous, and what they can teach is
#     RELATIONAL: which nodes are neighbours, how signals propagate, which
#     pathways share a source, what the system's own noise looks like. They
#     cannot teach a gain, because a wave is not light.
#
#   PHASE 1 — the image. Light calibrates GAINS and ENVIRONMENTAL STATISTICS,
#     as a PERTURBATION OF AN ALREADY GROUNDED RELATIONAL STRUCTURE.
#
# THE SECOND CORRECTION, and it fixes an error this seed made: A CLOSED EYE'S
# PHOTOMETRY STILL WORKS. The lid is translucent — photoreceptors transduce
# diffuse, unpatterned light long before eye opening. So "eye opening" does NOT
# switch phototransduction on; it delivers a PATTERNED IMAGE. An earlier version
# gated every photometric rule on `eye_open`, which encoded the false claim that
# a closed eye is blind. THE LID IS OPTICS, NOT A NEURAL SWITCH: what changes is
# the LIGHT THAT ARRIVES, which is the adapter's business (mechanical I/O), not
# a guard on a rule.
#
# So where does "waves do not calibrate the gain" actually live? IN THE
# POPULATION SPLIT, structurally and already: the photometric rules read
# `EyeCell.lum` (light), and waves live on `RetinaCell.bursting` (endogenous
# activity). They are different node types. There is no path from a wave to
# theta — not by convention, but because the graph has no such edge. The
# `eye_open` gate was belt-and-braces over a separation the architecture already
# guarantees, and it bought a biological falsehood in exchange for nothing.
#
# `eye_open` is retained as DATA that records which regime the adapter is
# presenting (0 = closed lid, diffuse ambient light; 1 = patterned image). It
# gates no rule.
#
# This retro-explains a result elsewhere in this ladder: the calibration agent
# measured waves and no-input placing theta IDENTICALLY (48.4-49.1 vs 48.2-49.0)
# and read it as "the reference is set by the architecture, not the waves". Under
# the correction that is EXPECTED — theta is a photometric gain, and waves were
# being asked to do vision's job.
#
# AND IT IS THE FIX FOR THIS RUNG'S WORST NULL INSTRUMENT. A per-cell reference
# adapted to a STATIC SCENE memorises and cancels that exact scene: every cell
# converges to resp = mu exactly (mean == max, sd 0) and the image is ERASED.
# Ambient light through a closed lid is UNIFORM, so theta calibrates to the
# LEVEL and cannot memorise a pattern it never saw. Measured: with theta
# calibrated on diffuse light alone, a held-out image is read INVARIANTLY across
# two decades (patdiff 0.00087 vs a floor of 0.1159 = 0.75%), while the linear
# receptor shifts by its ENTIRE dynamic range (1.000000). The closed eye
# calibrates the gain; the open eye then sees.


def step_guard(stamp, holder="e"):
    """Fire at most once per step: this cell's stamp is behind the clock."""
    return lt(attr(var("c"), stamp), attr(var(holder), "step"))


def stamped(stamp, value_term, holder="e"):
    return ["set_attr", "c", stamp, term(attr(var(holder), "step"))]


RULES = []


def rule(name, comment, match_type, match, where, effects, extra_match=None):
    RULES.append({"name": name, "comment": comment, "match_type": match_type,
                  "match": list(match) + list(extra_match or []),
                  "where": where, "effects": effects})


# ============================================================================
# 1. THE LOG RECEPTOR — Weber-Fechner
# ============================================================================
# `lum` is the ONLY thing the adapter writes: raw luminance, mechanical ingest.
# Whether the cell takes its log is the GRAPH's configuration (`logr`), and the
# two arms are two rules over one datum — not a fork in the host.

rule(
    "ey_receptor_log",
    "WEBER-FECHNER: the photoreceptor responds to log(I). This is why vision "
    "spans ~10 orders of magnitude of illumination, and it is the FRAME FIX for "
    "this ladder: in log space an illumination change x k is the ADDITIVE "
    "constant log k, so the reference-subtraction downstream removes it exactly. "
    "`i0` is the dark light (Weber's I0) and is load-bearing for more than "
    "biology: the engine's Log returns -inf at 0, and a retina must have a "
    "finite response to a black pixel.",
    "EyeCell", [["e", "has_eyecell", "c"]],
    and_(ON, gt(param("logr"), lit(0.5)), step_guard("x_step")),
    [["set_attr", "c", "x", term(log(plus(attr(var("c"), "lum"), param("i0"))))],
     stamped("x_step", None)],
)

rule(
    "ey_receptor_lin",
    "The LINEAR arm — the control for the illumination-invariance gate, and the "
    "regime every earlier rung ran in. Same datum, same downstream theta, same "
    "rectification; only the receptor nonlinearity differs, selected by `logr` "
    "as data. Prediction: this arm's response MOVES with illumination, because "
    "an adaptive reference can subtract an additive constant but cannot undo a "
    "multiplicative gain.",
    "EyeCell", [["e", "has_eyecell", "c"]],
    and_(ON, lt(param("logr"), lit(0.5)), step_guard("x_step")),
    [["set_attr", "c", "x", term(attr(var("c"), "lum"))],
     stamped("x_step", None)],
)

# ============================================================================
# 2. THE ADAPTIVE REFERENCE — GCAL's homeostatic theta, on the ACTIVATION
# ============================================================================
# GCAL Eqs. 7-8 (VISION_PRIOR_ART.md 2.3), constants transcribed:
#     xbar(t) = beta*xbar(t-1) + (1-beta)*x(t)      beta = 0.991
#     theta(t) = theta(t-1) + lam*(xbar(t) - mu)    lam = 0.01, mu = 0.024
# theta shifts the cell's f-I curve. It NEVER appears in dw. That placement is
# the whole point: it is structurally unable to annihilate.

rule(
    "ey_xbar",
    "The cell's own trailing mean OUTPUT (GCAL Eq. 7, beta=0.991): "
    "xbar = beta*xbar + (1-beta)*resp. "
    "IT IS THE OUTPUT, NOT THE DRIVE, AND THAT IS THE WHOLE CONTROLLER. Measured "
    "the wrong way round first: EMA-ing the DRIVE makes theta a one-way ratchet "
    "— theta rises whenever x > mu, nothing it does to resp ever feeds back, and "
    "it climbs until every response is pinned at 0 (measured: mean resp exactly "
    "0.000000 at every illumination, in BOTH the log and linear arms — a null "
    "instrument that would have passed the invariance gate for the most trivial "
    "possible reason, 0 == 0). EMA-ing the OUTPUT closes the loop: theta rises "
    "only while the cell is firing ABOVE target and stops exactly when its mean "
    "output sits at mu. Gated on resp_step==step so it reads an output this step "
    "has already computed, and on `frozen` because adaptation IS plasticity: a "
    "probe must never let the reference chase the probe (rung 5 learned this the "
    "hard way — `oja=0` was not a freeze and moved weights by 47.9 per probe).",
    "EyeCell", [["e", "has_eyecell", "c"]],
    and_(ON, NOT_FROZEN, gt(param("homeo"), lit(0.5)),
         step_guard("xbar_step"),
         eq(attr(var("c"), "resp_step"), attr(var("e"), "step"))),
    [["set_attr", "c", "xbar",
      term(plus(times(param("beta"), attr(var("c"), "xbar")),
                times(minus(lit(1.0), param("beta")), attr(var("c"), "resp"))))],
     stamped("xbar_step", None)],
)

rule(
    "ey_adapt_theta",
    "GCAL Eq. 8: theta drifts to hold the cell's mean drive at the target rate "
    "mu. THE REFERENCE POINT, and it is the creator's claim made mechanical — "
    "there is no absolute zero, only a reference, and the eye is what "
    "establishes it. Placed OUTSIDE the learning rule (VISION_PRIOR_ART.md "
    "2.3): it shifts the activation function and cannot flip the sign of dw. "
    "`theta_mode<0.5` selects this placement; the BCM arm below is the same "
    "variable in the opposite place.",
    "EyeCell", [["e", "has_eyecell", "c"]],
    and_(ON, NOT_FROZEN, gt(param("homeo"), lit(0.5)),
         lt(param("theta_mode"), lit(0.5)),
         step_guard("theta_step"),
         eq(attr(var("c"), "xbar_step"), attr(var("e"), "step"))),
    [["set_attr", "c", "theta",
      term(plus(attr(var("c"), "theta"),
                times(param("lam"), minus(attr(var("c"), "xbar"), param("mu")))))],
     stamped("theta_step", None)],
)

rule(
    "ey_response",
    "THE CALIBRATED OUTPUT: resp = max(x - theta, 0). In log mode this is "
    "log(I) - theta = log(I/exp(theta)) — A RATIO against the cell's own adapted "
    "reference, and therefore invariant to illumination. That identity is the "
    "creator's claim in one line: log(a) - log(b) = log(a/b), so there is no "
    "absolute zero here, only a reference, and theta IS the reference. "
    "ORDERING: this fires as soon as the drive exists, using the theta the "
    "PREVIOUS step left. resp -> xbar -> theta -> (next step) resp is a feedback "
    "loop, and the one-step delay is what keeps it a loop rather than a race "
    "inside one fixpoint. Deliberately NOT gated by `frozen`: a frozen cell must "
    "still respond, or the probe measures silence (rung 6's lesson).",
    "EyeCell", [["e", "has_eyecell", "c"]],
    and_(ON, step_guard("resp_step"),
         eq(attr(var("c"), "x_step"), attr(var("e"), "step"))),
    [["set_attr", "c", "resp",
      term(transfer(attr(var("c"), "x"), attr(var("c"), "theta")))],
     stamped("resp_step", None)],
)

# ============================================================================
# 3. ENGBERT'S SELF-AVOIDING WALK — the eye's own motion
# ============================================================================
# Engbert, Mergenthaler, Sinn & Pikovsky (2011) PNAS 108:E765, verified in
# VISION_PRIOR_ART.md 3.2:
#     h_ij -> h_ij + 1          (occupied site)
#     h_kl -> (1-eps)*h_kl      (all sites — the SLOW relaxation makes persistence)
#     u(i,j) = lam*L*[((i-i0)/i0)^2 + ((j-j0)/j0)^2]
#     (i',j') = argmin over neighbours of { h_kl + u(k,l) }
# Self-avoidance makes the short-lag persistence; the potential makes the
# long-lag antipersistence.
#
# THE CARDINAL-AXIS ARTIFACT, and why this is the STOCHASTIC variant. 3.2 warns
# the deterministic 4-connected argmin only steps N/S/E/W — "a subtle way of
# telling the agent the answer". Two changes: the gaze lattice is wired
# 8-connected (`gaze_neighbour`, by the adapter, exactly as the retina's own
# 4-neighbourhood is), and the argmin runs over { h + u - temp*gum } where `gum`
# is a fresh IID Gumbel draw the adapter writes per cell per step. Argmin over
# (cost + Gumbel noise) IS an exact Boltzmann sample at temperature `temp`
# (the Gumbel-max trick), so this is softmax selection with no sampler in the
# host and no RNG Term in the engine. `temp=0` recovers Engbert's deterministic
# argmin exactly, as an arm.
#
# THE ENTROPY SPLIT IS THE PROTOCOL'S (0): the adapter supplies UNSTRUCTURED
# entropy (IID Gumbel, no spatial or temporal correlation) and a clock; the
# GRAPH makes the structure (the trail, the potential, the selection). That is
# the same split `WaveWorld.ignite` already runs under.

rule(
    "ey_saw_potential",
    "u(i,j) = lam*L*[((i-i0)/i0)^2 + ((j-j0)/j0)^2], Engbert's quadratic "
    "centering potential, VERBATIM including the L factor. The L is NOT "
    "decoration and was measured: h increments by exactly 1.0 per visit, so "
    "without L the potential maxes out at lam=1 at the lattice edge and the "
    "trail overwhelms it after a single visit — the walk then never turns "
    "around, and the long-lag ANTIpersistence (the half of Engbert's signature "
    "the potential is solely responsible for) is absent (measured: alpha_long "
    "1.164, i.e. still superdiffusive, where the paper reports 0.71). L puts "
    "the potential on the same scale as the trail it competes with. `L` is the "
    "lattice's own size, which the adapter states as geometry exactly as it "
    "states who neighbours whom; lam stays the published constant 1.0. Fires "
    "once per cell (u_set guard), being time-invariant.",
    "GazeCell", [["g", "has_gazecell", "c"]],
    and_(ON, lt(attr(var("c"), "u_set"), lit(0.5))),
    [["set_attr", "c", "u",
      term(times(param("saw_lam"), attr(var("g"), "L"),
                 plus(pow_(div(minus(attr(var("c"), "row"), attr(var("g"), "cy")),
                               attr(var("g"), "cy")), lit(2.0)),
                      pow_(div(minus(attr(var("c"), "col"), attr(var("g"), "cx")),
                               attr(var("g"), "cx")), lit(2.0)))))],
     ["set_attr", "c", "u_set", term(lit(1.0))]],
)

rule(
    "ey_saw_relax",
    "h -> (1-eps)*h at EVERY site. eps=1e-3: the relaxation is SLOW, and 3.2 is "
    "explicit that this is what makes the walk persistent — the trail has to "
    "outlive the walker for self-avoidance to bend the path.",
    "GazeCell", [["g", "has_gazecell", "c"]],
    and_(ON, gt(param("saw"), lit(0.5)), step_guard("h_step", "g")),
    [["set_attr", "c", "h",
      term(times(minus(lit(1.0), param("saw_eps")), attr(var("c"), "h")))],
     ["set_attr", "c", "h_step", term(attr(var("g"), "step"))]],
)

rule(
    "ey_saw_deposit",
    "h -> h + 1 at the OCCUPIED site: the walk lays its own trail, and the trail "
    "is what it then avoids. Guarded on h_step==step so the deposit lands AFTER "
    "this step's relaxation and is never itself decayed in the same pass.",
    "GazeCell", [["g", "gaze_at", "c"]],
    and_(ON, gt(param("saw"), lit(0.5)),
         eq(attr(var("c"), "h_step"), attr(var("g"), "step")),
         lt(attr(var("c"), "dep_step"), attr(var("g"), "step"))),
    [["set_attr", "c", "h", term(plus(attr(var("c"), "h"), lit(1.0)))],
     ["set_attr", "c", "dep_step", term(attr(var("g"), "step"))]],
)

rule(
    "ey_saw_move",
    "THE WALK: step to the neighbour minimising { h + u - temp*gum }. Self-"
    "avoidance (h) pushes it off its own trail — locally directional, which is "
    "the whole point: `gaze_walk` is ballistic-then-MEMORYLESS, so it has no "
    "direction correlation ACROSS epochs, and the signal it does carry within an "
    "epoch is averaged away. The potential (u) pulls it back to centre. The "
    "Gumbel term makes the selection a Boltzmann sample (see the module "
    "docstring) rather than the cardinal-axis-artifacted deterministic argmin. "
    "NO DIRECTION IS EVER TOLD TO THE MODEL: the walk is locally directional "
    "from its own trail and globally rotation-symmetric — 3.2's crux. "
    "STRUCTURE: `add_edge`'s target must be a MATCH VAR, not a computed Term, so "
    "the candidate `k` is matched over `c`'s neighbours and the winner is picked "
    "by identity-Eq against the Argmin — `Eq` compares Value::Node by id, the "
    "same idiom `retire_duplicate_gap` uses to choose one survivor from a fixed "
    "snapshot within a pass (CLAUDE.md).",
    "GazeCell", [["g", "gaze_at", "c"], ["c", "gaze_neighbour", "k"]],
    and_(ON, gt(param("saw"), lit(0.5)),
         eq(attr(var("c"), "dep_step"), attr(var("g"), "step")),
         lt(attr(var("g"), "move_step"), attr(var("g"), "step")),
         eq(var("k"),
            argmin(neighbours(var("c"), "gaze_neighbour"), "z",
                   minus(plus(attr(var("z"), "h"), attr(var("z"), "u")),
                         times(param("temp"), attr(var("z"), "gum")))))),
    [["del_edge", "g", "gaze_at", "c"],
     ["add_edge", "g", "gaze_at", "k"],
     ["set_attr", "g", "move_step", term(attr(var("g"), "step"))]],
)

# ============================================================================
# 4. THE LEARNED LAYER — the arena where theta's PLACEMENT is measured
# ============================================================================
# A minimal Hebbian unit over the receptors. It exists for ONE reason: to make
# "theta outside vs theta inside" an experiment rather than an argument. Both
# arms share the receptor, the input, the rectification and eta; they differ in
# WHERE theta sits, selected by `theta_mode` as data.

rule(
    "ey_unit_act",
    "The unit's drive: sum of weight * presynaptic resp.",
    "EyeUnit", [["e", "has_eyeunit", "u"]],
    and_(ON, lt(attr(var("u"), "act_step"), attr(var("e"), "step"))),
    [["set_attr", "u", "act",
      term(fold(in_neighbours(var("u"), "ey_post"), "sy", "acc", lit(0.0),
                plus(var("acc"),
                     times(attr(var("sy"), "weight"),
                           attr({"type": "Pick",
                                 "source": in_neighbours(var("sy"), "ey_pre")},
                                "resp")))))],
     ["set_attr", "u", "act_step", term(attr(var("e"), "step"))]],
)

rule(
    "ey_unit_rate_outside",
    "THETA OUTSIDE (GCAL): the threshold is on the ACTIVATION FUNCTION — "
    "rate = max(act - utheta, 0). It shifts the f-I curve, and dw below reads "
    "`rate`, never `utheta`. There is no path by which this theta can change the "
    "SIGN of dw.",
    "EyeUnit", [["e", "has_eyeunit", "u"]],
    and_(ON, lt(param("theta_mode"), lit(0.5)),
         lt(attr(var("u"), "rate_step"), attr(var("e"), "step")),
         eq(attr(var("u"), "act_step"), attr(var("e"), "step"))),
    [["set_attr", "u", "rate",
      term(transfer(attr(var("u"), "act"), attr(var("u"), "utheta")))],
     ["set_attr", "u", "rate_step", term(attr(var("e"), "step"))]],
)

rule(
    "ey_unit_rate_inside",
    "THETA INSIDE (BCM): the activation function carries NO ADAPTIVE threshold — "
    "rate is the rectified, saturated drive with theta ABSENT, and theta appears "
    "instead inside dw, where it gates the sign. "
    "IDENTICAL TRANSFER FUNCTION, at a FIXED threshold of 0: the same "
    "rectification and the same rmax saturation as the outside arm. That is "
    "load-bearing for the comparison — if only one arm saturated, the contrast "
    "would confound theta's PLACEMENT (the thing under test) with the presence "
    "of a bound (a thing that is not). The arms differ in exactly one respect: "
    "WHERE theta sits.",
    "EyeUnit", [["e", "has_eyeunit", "u"]],
    and_(ON, gt(param("theta_mode"), lit(0.5)),
         lt(attr(var("u"), "rate_step"), attr(var("e"), "step")),
         eq(attr(var("u"), "act_step"), attr(var("e"), "step"))),
    [["set_attr", "u", "rate", term(transfer(attr(var("u"), "act"), lit(0.0)))],
     ["set_attr", "u", "rate_step", term(attr(var("e"), "step"))]],
)

rule(
    "ey_unit_actbar",
    "The unit's trailing mean rate (GCAL Eq. 7 at the unit grain).",
    "EyeUnit", [["e", "has_eyeunit", "u"]],
    and_(ON, NOT_FROZEN, gt(param("homeo"), lit(0.5)),
         lt(attr(var("u"), "actbar_step"), attr(var("e"), "step")),
         eq(attr(var("u"), "rate_step"), attr(var("e"), "step"))),
    [["set_attr", "u", "actbar",
      term(plus(times(param("beta"), attr(var("u"), "actbar")),
                times(minus(lit(1.0), param("beta")), attr(var("u"), "rate"))))],
     ["set_attr", "u", "actbar_step", term(attr(var("e"), "step"))]],
)

rule(
    "ey_unit_adapt_utheta",
    "GCAL Eq. 8 at the unit: utheta += lam*(actbar - mu). The OUTSIDE placement's "
    "homeostat.",
    "EyeUnit", [["e", "has_eyeunit", "u"]],
    and_(ON, NOT_FROZEN, gt(param("homeo"), lit(0.5)),
         lt(param("theta_mode"), lit(0.5)),
         lt(attr(var("u"), "utheta_step"), attr(var("e"), "step")),
         eq(attr(var("u"), "actbar_step"), attr(var("e"), "step"))),
    [["set_attr", "u", "utheta",
      term(plus(attr(var("u"), "utheta"),
                times(param("lam"), minus(attr(var("u"), "actbar"), param("mu")))))],
     ["set_attr", "u", "utheta_step", term(attr(var("e"), "step"))]],
)

rule(
    "ey_bcm_theta",
    "BCM's SLIDING THRESHOLD: btheta = EMA(rate^2)/mu. The classic "
    "Bienenstock-Cooper-Munro homeostat — and note it tracks the SQUARE of the "
    "rate, so it accelerates away from a rising cell far faster than GCAL's "
    "linear tracker. When it outruns activity, every synapse depresses.",
    "EyeUnit", [["e", "has_eyeunit", "u"]],
    and_(ON, NOT_FROZEN, gt(param("theta_mode"), lit(0.5)),
         lt(attr(var("u"), "btheta_step"), attr(var("e"), "step")),
         eq(attr(var("u"), "rate_step"), attr(var("e"), "step"))),
    [["set_attr", "u", "btheta",
      term(plus(times(param("beta"), attr(var("u"), "btheta")),
                times(minus(lit(1.0), param("beta")),
                      div(times(attr(var("u"), "rate"), attr(var("u"), "rate")),
                          param("mu")))))],
     ["set_attr", "u", "btheta_step", term(attr(var("e"), "step"))]],
)

rule(
    "ey_learn_outside",
    "THE OUTSIDE ARM'S LEARNING RULE: Oja. dw = eta*rate*(x - rate*w). "
    "Sign-fixed Hebbian plus the multiplicative decay that bounds it — which "
    "VISION_PRIOR_ART.md 2.4 establishes is GCAL's own divisive normalisation to "
    "first order (they use L1, this is L2; this tree's rung 2 rediscovered the "
    "field's standard stabiliser, and it should be cited as such, not claimed). "
    "`utheta` does NOT appear here. That is the entire architectural claim.",
    "EySynapse", [["p", "ey_pre", "sy"], ["sy", "ey_post", "u"]],
    and_(ON, NOT_FROZEN, lt(param("theta_mode"), lit(0.5)),
         lt(attr(var("sy"), "touched"), attr(var("u"), "rate_step"))),
    [["set_attr", "sy", "weight",
      term(plus(attr(var("sy"), "weight"),
                times(param("eta"), attr(var("u"), "rate"),
                      minus(attr(var("p"), "resp"),
                            times(attr(var("u"), "rate"),
                                  attr(var("sy"), "weight"))))))],
     ["set_attr", "sy", "touched", term(attr(var("u"), "rate_step"))]],
)

rule(
    "ey_learn_bcm",
    "THE INSIDE ARM'S LEARNING RULE: dw = eta*rate*(rate - btheta)*x. `btheta` "
    "is INSIDE the rule and multiplies dw — when btheta > rate the term goes "
    "NEGATIVE and every synapse depresses. Same variable as the outside arm's "
    "utheta, opposite architecture; VISION_PRIOR_ART.md 2.3's prediction is that "
    "this placement is the one that can annihilate, and this tree already "
    "measured it doing so (0.004).",
    "EySynapse", [["p", "ey_pre", "sy"], ["sy", "ey_post", "u"]],
    and_(ON, NOT_FROZEN, gt(param("theta_mode"), lit(0.5)),
         lt(attr(var("sy"), "touched"), attr(var("u"), "rate_step"))),
    [["set_attr", "sy", "weight",
      term(mx(plus(attr(var("sy"), "weight"),
                   times(param("eta"), attr(var("u"), "rate"),
                         minus(attr(var("u"), "rate"), attr(var("u"), "btheta")),
                         attr(var("p"), "resp"))),
              lit(0.0)))],
     ["set_attr", "sy", "touched", term(attr(var("u"), "rate_step"))]],
)


# ============================================================================
# PHASE 0 — THE PRE-VISUAL PHASE. Waves teach RELATIONAL structure.
# ============================================================================
# THE CLAIM, and it is the creator's: waves cannot calibrate a gain, but they can
# teach the graph WHICH NODES ARE NEIGHBOURS — and downstream topology must be
# LEARNED, not wired.
#
# WHICH EDGES ARE PHYSICS AND WHICH ARE KNOWLEDGE — stated explicitly, because
# the whole value of this rung turns on the line:
#
#   PHYSICS (given, legitimately wired by the adapter):
#     * `Retina -has_cell-> RetinaCell` and the retina's own 4-neighbourhood.
#       Photoreceptors ARE physically adjacent; that is the sheet's geometry, not
#       something the agent could know or fail to know. rung 1 wires it and that
#       is correct.
#
#   KNOWLEDGE (must be EARNED, and is what this phase is for):
#     * WHICH RETINAL CELLS A DOWNSTREAM UNIT LISTENS TO — i.e. RETINOTOPY.
#       This is the one rung 4 hand-wired (`domains/cortex_sheet.py`) and then
#       measured a map largely made of its own wiring: "the ablated arm is NOT
#       null (-13.25): retinotopic RF overlap — ANATOMY THE ADAPTER WIRES —
#       accounts for most of the raw smoothness". Retinotopic refinement is
#       exactly what waves are FOR (Cang/Feller), so handing it over is handing
#       the agent the answer.
#
# THE BUILD. A `WUnit` starts connected to EVERY retinal cell with a small
# random weight — a DIFFUSE, NON-RETINOTOPIC projection carrying no spatial
# information whatsoever (the adapter supplies unstructured entropy; PROTOCOL §0).
# Waves then run, and Oja's rule refines the projection. The prediction is that
# each unit's RF CONTRACTS onto a localised patch, because a travelling wave is
# spatially correlated: cells that fire together are physically near, so the
# leading principal component of the wave covariance IS a localised blob. The
# retinotopy is then the graph's, grown from its own endogenous activity.
#
# THE CONTROL IS RUNG 1'S OWN, and it is the paradigm-forcing one: `propagate=0`
# on WaveParams is the SAME entropy with no wave circuit — identical ignition,
# identical duty cycle, no spatiotemporal correlation. If RFs localise under
# waves and not under noise, the structure was manufactured by the graph.
#
# NO PHOTOTRANSDUCTION IS INVOLVED: a WUnit reads `bursting` off RetinaCells,
# which is endogenous activity. Every photometric rule above is gated EYE_OPEN
# and cannot fire here.

rule(
    "ph0_wunit_act",
    "The pre-visual unit's drive: sum of weight * the presynaptic retinal cell's "
    "BURST. `bursting` is ENDOGENOUS activity — a wave, not a photon — so this "
    "rule involves no phototransduction and is deliberately NOT gated on "
    "eye_open. This is what a unit can know before the eye opens.",
    "WUnit", [["e", "has_wunit", "u"]],
    and_(ON, gt(param("phase0"), lit(0.5)),
         lt(attr(var("u"), "act_step"), attr(var("e"), "step"))),
    [["set_attr", "u", "act",
      term(fold(in_neighbours(var("u"), "w_post"), "sy", "acc", lit(0.0),
                plus(var("acc"),
                     times(attr(var("sy"), "weight"),
                           attr({"type": "Pick",
                                 "source": in_neighbours(var("sy"), "w_pre")},
                                "bursting")))))],
     ["set_attr", "u", "act_step", term(attr(var("e"), "step"))]],
)

rule(
    "ph0_wunit_rate",
    "The same bounded transfer function as phase 1, at a fixed threshold of 0: "
    "rectify and saturate at rmax. No adaptive theta here — theta is a "
    "PHOTOMETRIC gain and there is no light yet.",
    "WUnit", [["e", "has_wunit", "u"]],
    and_(ON, gt(param("phase0"), lit(0.5)),
         lt(attr(var("u"), "rate_step"), attr(var("e"), "step")),
         eq(attr(var("u"), "act_step"), attr(var("e"), "step"))),
    [["set_attr", "u", "rate", term(transfer(attr(var("u"), "act"), lit(0.0)))],
     ["set_attr", "u", "rate_step", term(attr(var("e"), "step"))]],
)

rule(
    "ph0_wunit_winner",
    "WINNER-TAKE-ALL — and this rung MEASURED why it is not optional. Without "
    "competition every unit sees the same wave, and Oja drives all of them to "
    "the same fixed point: the mean wave, which over an isotropic ensemble of "
    "wave locations is UNIFORM over the sheet. Measured exactly that — all six "
    "units at spread 6.52 against a diffuse floor of 6.52, i.e. no refinement, "
    "while the rule was demonstrably live (units active, max|dw| 1.8e-2). That "
    "is rung 5's result recurring at a third layer ('a contraction to the mean "
    "of an isotropic distribution is the mean'), and rung 1's own "
    "wv_unit_burst_winner already says so in its comment: 'without it every unit "
    "sees the same wave and the burst rule drives them all to the same receptive "
    "field'. So competition is the mechanism that makes a POPULATION differentiate "
    "— it breaks the symmetry between units, and each unit then specialises on "
    "the region it happens to win. NOTE WHAT THIS DOES AND DOES NOT HAND OVER: "
    "WTA supplies COMPETITION, not TOPOLOGY. No unit is told where to look; "
    "which region each one captures, and hence the whole map, still has to be "
    "grown out of the waves' own statistics. Same Argmax-over-`act` + identity-Eq "
    "idiom as rung 1 (Eq compares Value::Node by id). act>0 required, so a silent "
    "step crowns no winner.",
    "WUnit", [["e", "has_wunit", "u"]],
    and_(ON, gt(param("phase0"), lit(0.5)),
         lt(attr(var("u"), "win_step"), attr(var("e"), "step")),
         eq(attr(var("u"), "rate_step"), attr(var("e"), "step")),
         gt(attr(var("u"), "act"), lit(0.0)),
         eq(var("u"),
            {"type": "Argmax",
             "source": neighbours(var("e"), "has_wunit"),
             "var_name": "z", "value": attr(var("z"), "act"), "default": None})),
    [["set_attr", "u", "winner", term(lit(1.0))],
     ["set_attr", "u", "win_step", term(attr(var("e"), "step"))]],
)

rule(
    "ph0_learn_retinotopy",
    "RETINOTOPIC REFINEMENT — the rung's headline, and the one thing here that "
    "rung 4 was handed instead of growing. Oja on the wave burst: "
    "dw = eta*rate*(x - rate*w), the same contraction rung 2 established and the "
    "same one GCAL uses in its L1 form (VISION_PRIOR_ART.md §2.4 — a "
    "rediscovery, cited, not claimed). The unit begins connected to EVERY "
    "retinal cell with random weight — no retinotopy, no spatial prior — and "
    "Oja's fixed point is the leading PC of the input covariance. Under WAVES "
    "that covariance is spatially correlated, so the leading PC is a LOCALISED "
    "BLOB and the RF contracts onto a patch: the map is grown. Under rung 1's "
    "`propagate=0` NOISE control the covariance is white, every direction is "
    "degenerate, and there is nothing to contract onto — which is precisely the "
    "'contraction to the mean of an isotropic distribution is the mean' result "
    "that killed rungs 3 and 5, here used as the CONTROL rather than met as a "
    "surprise.",
    "WSynapse", [["p", "w_pre", "sy"], ["sy", "w_post", "u"]],
    and_(ON, gt(param("phase0"), lit(0.5)), NOT_FROZEN,
         # ONLY THE WINNER LEARNS. This is the gate that makes the population
         # differentiate instead of collapsing to one shared average.
         eq(attr(var("u"), "win_step"), attr(var("u"), "rate_step")),
         eq(attr(var("u"), "winner"), lit(1.0)),
         lt(attr(var("sy"), "touched"), attr(var("u"), "rate_step"))),
    [["set_attr", "sy", "weight",
      term(mx(plus(attr(var("sy"), "weight"),
                   times(param("ph0_eta"), attr(var("u"), "rate"),
                         minus(attr(var("p"), "bursting"),
                               times(attr(var("u"), "rate"),
                                     attr(var("sy"), "weight"))))),
              lit(0.0)))],
     ["set_attr", "sy", "touched", term(attr(var("u"), "rate_step"))]],
)


rule(
    "ph0_wsum",
    "The winner's total afferent weight, for the L1 normalisation below. Guarded "
    "on there being NO synapse of this unit still un-learned this step (the same "
    "'every presynaptic has already fired' idiom oo_sunit_activate uses), so the "
    "sum is taken AFTER learning and the fixpoint cannot race it.",
    "WUnit", [["e", "has_wunit", "u"]],
    and_(ON, gt(param("phase0"), lit(0.5)),
         eq(attr(var("u"), "winner"), lit(1.0)),
         eq(attr(var("u"), "win_step"), attr(var("e"), "step")),
         lt(attr(var("u"), "wsum_step"), attr(var("e"), "step")),
         {"type": "Not", "arg": {
             "type": "Exists",
             "source": in_neighbours(var("u"), "w_post"),
             "var_name": "sy",
             "predicate": lt(attr(var("sy"), "touched"),
                             attr(var("u"), "rate_step"))}}),
    [["set_attr", "u", "wsum",
      term(fold(in_neighbours(var("u"), "w_post"), "sy", "acc", lit(0.0),
                plus(var("acc"), attr(var("sy"), "weight"))))],
     ["set_attr", "u", "wsum_step", term(attr(var("e"), "step"))]],
)

rule(
    "ph0_normalize",
    "GCAL'S OWN NORMALISATION, VERBATIM: Sum_i w_ij = 1.0 enforced after every "
    "learning step (VISION_PRIOR_ART.md §2.4, their Eqs. 9-10). It is L1 where "
    "rung 2's Oja is L2 — 'the same contraction under a different norm', and §2.5 "
    "records that normalisation is in ALL FOUR of their models including the "
    "baseline. Not an addition to GCAL; a part of it this seed had omitted.\n"
    "MEASURED, and this is why it is not optional. WITHOUT it the units compete "
    "on TOTAL WEIGHT instead of on MATCH: act = Sum w_i x_i is dominated by "
    "whichever unit happens to hold the most weight, so that unit wins "
    "everywhere regardless of WHERE the wave is (measured: 79 of 200 wins to the "
    "unit with the largest act, and win rate uncorrelated with wave location), "
    "and every RF stayed at the diffuse floor (6.52 vs a floor of 6.52). It is "
    "rich-get-richer on magnitude, and there is no spatial signal in it to "
    "specialise on. WITH Sum w = 1 the drive is a weighted AVERAGE of the "
    "bursting cells, so a unit can only win by its weight PATTERN matching the "
    "wave's LOCATION — which is the positive feedback that makes a map.\n"
    "It also removes the saturation for free: with Sum w = 1 and burst in {0,1}, "
    "act <= 1 = rmax by construction, so f never clips and the response is "
    "graded again. A mechanism that fixes two measured failures at once is "
    "usually the right one.",
    "WSynapse", [["p", "w_pre", "sy"], ["sy", "w_post", "u"]],
    and_(ON, gt(param("phase0"), lit(0.5)), NOT_FROZEN,
         eq(attr(var("u"), "wsum_step"), attr(var("u"), "rate_step")),
         lt(attr(var("sy"), "normed"), attr(var("u"), "rate_step")),
         gt(attr(var("u"), "wsum"), lit(0.0))),
    [["set_attr", "sy", "weight",
      term(div(attr(var("sy"), "weight"), attr(var("u"), "wsum")))],
     ["set_attr", "sy", "normed", term(attr(var("u"), "rate_step"))]],
)


# ------------------------------------------------------------------ the manifest
PARAMS = {
    "local_id": 0,
    "type": "EyeParams",
    "attrs": {
        "name": "default",
        # MASTER SWITCH. 0 => not one rule in this seed fires, so every result
        # committed before this seed reproduces byte-identically (PROTOCOL 9).
        "eye": 0.0,
        # WHICH REGIME THE ADAPTER IS PRESENTING — data, gating no rule.
        # 0 = closed lid (diffuse ambient light; photometry RUNS, because a
        # closed eye's photometry works); 1 = patterned image. The separation
        # "waves do not calibrate the gain" is structural, not a guard: the
        # photometric rules read EyeCell.lum, waves live on RetinaCell.bursting,
        # and no edge joins them.
        "eye_open": 0.0,
        # phase0=1 arms the pre-visual wave-driven retinotopy learning.
        "phase0": 0.0,
        "ph0_eta": 0.0005,
        # --- receptor ---
        "logr": 1.0,     # 1 = Weber-Fechner log receptor; 0 = the linear control arm
        "i0": 1.0,       # dark light (Weber's I0); keeps Log finite at black
        # --- the adaptive reference (GCAL Eqs. 7-8, constants transcribed) ---
        "homeo": 1.0,
        "beta": 0.991,
        "lam": 0.01,
        "mu": 0.024,
        # rmax: the saturation of the activation function f. NOT a free constant
        # — mu=0.024 is GCAL's TARGET AVERAGE ACTIVITY, which only means
        # anything as a fraction of a maximum, and rmax IS that maximum. See
        # `transfer()` for the measurement that forced it in.
        "rmax": 1.0,
        # 0 = theta OUTSIDE the learning rule (GCAL); 1 = INSIDE it (BCM).
        "theta_mode": 0.0,
        "eta": 0.0005,
        "frozen": 0.0,
        # --- Engbert SAW (2011), constants from VISION_PRIOR_ART.md 3.2 ---
        "saw": 1.0,
        "saw_eps": 0.001,   # eps: the SLOW relaxation that makes persistence
        "saw_lam": 1.0,     # lambda: the quadratic potential's strength
        # temp>0 => Boltzmann selection via the Gumbel-max trick (the stochastic
        # variant, arXiv:2303.11941). temp=0 => Engbert's deterministic argmin,
        # kept as an arm precisely because 3.2 names it a cardinal-axis artifact.
        "temp": 1.0,
        "comment": "Every arm in this seed is DATA on this node, never a Python "
                   "code path (PROTOCOL 0). `eye=0` is the master default-off.",
    },
}

def prod(stype, et, ttype):
    """An admissible edge — Γ's vocabulary for this seed's own populations.
    The eye mints its OWN node types and never touches another rung's
    (`RetinaCell` / `SUnit` / `Bipolar` / `DUnit` are all absent here)."""
    return {"src": {"type": stype, "var": "a"}, "edge_type": et,
            "tgt": {"type": ttype, "var": "b"},
            "provenance": f"seed:vision_eye:{et}"}


PRODUCTIONS = [
    prod("Eye", "has_eyecell", "EyeCell"),
    # --- phase 0: the pre-visual population. `w_pre` starts DIFFUSE (every
    # retinal cell to every unit) and is what the waves must refine into a
    # retinotopic map. The RetinaCell sheet + its 4-neighbourhood are rung 1's
    # and are PHYSICS; which cells a WUnit listens to is KNOWLEDGE, and is grown.
    prod("Eye", "has_wunit", "WUnit"),
    prod("Retina", "has_wclock", "Eye"),
    prod("RetinaCell", "w_pre", "WSynapse"),
    prod("WSynapse", "w_post", "WUnit"),
    prod("Eye", "has_eyeunit", "EyeUnit"),
    prod("EyeCell", "ey_pre", "EySynapse"),
    prod("EySynapse", "ey_post", "EyeUnit"),
    prod("Gaze", "has_gazecell", "GazeCell"),
    prod("Gaze", "gaze_at", "GazeCell"),
    prod("GazeCell", "gaze_neighbour", "GazeCell"),
]

MANIFEST = {
    "id": "vision_eye",
    "version": "1.0.0",
    "depends_on": ["vision_waves"],
    "description": (
        "THE EYE'S CALIBRATION FRONT END. A log receptor (Weber-Fechner), an "
        "adaptive reference theta placed GCAL-style on the activation function "
        "(outside the learning rule, where it cannot flip dw's sign), and "
        "Engbert's self-avoiding-walk fixational drift. The eye is the layer "
        "that establishes the REFERENCE the rest of the substrate is defined "
        "against: in log space centre-minus-reference is a RATIO, so the "
        "response is invariant to illumination. eye=0 default."
    ),
    "microtheory": "vision_eye",
    "nodes": [PARAMS],
    "edges": [],
    "productions": PRODUCTIONS,
    "rules": RULES,
}


def main():
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out = os.path.join(here, "seeds", "vision_eye.json")
    with open(out, "w") as fh:
        json.dump(MANIFEST, fh, indent=1)
        fh.write("\n")
    print(f"wrote {out}: {len(RULES)} rules, {len(MANIFEST['nodes'])} nodes")


if __name__ == "__main__":
    main()
