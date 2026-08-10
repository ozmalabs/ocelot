"""build_vision_lateral_seed — RUNG 7: RETINAL LATERAL INHIBITION, so that
CENTRE-SURROUND *EMERGES* and the ON/OFF channels acquire INDEPENDENT
correlation structure.

Emits `seeds/vision_lateral.json`. Run:  python -m tools.build_vision_lateral_seed

WHY THIS RUNG EXISTS — rung 6's measured diagnosis
---------------------------------------------------
Rung 6 built the signed simple layer and removed rung 5's blocker (an ideal
split cell scores OSI 0.9115 through the identical probe on which rung 5's
units scored 0.004). But **waves developed nothing**, and the diagnosis was
structural, not a parameter problem:

    the complementary split `x_OFF = 1 - x_ON` is ITSELF DEGENERATE.

Knowing ON determines OFF *exactly*. Correlation is invariant under affine
maps up to sign, so

    C_ON,OFF(d) = Corr(x_ON(i), 1 - x_ON(j)) = -Corr(x_ON(i), x_ON(j))
                = -C_ON,ON(d)          IDENTICALLY, at every distance d.

The two channels therefore carry **no independent correlation structure**.
Miller (1994) gets ON/OFF segregation precisely from ON/OFF correlation
functions with **different spatial dependence** — which in the real retina come
from **centre-surround RFs of different sizes**. The ON/OFF *sign* is NECESSARY
(it removed rung 5's blocker) but NOT SUFFICIENT (it adds nothing for waves to
sculpt).

THE MECHANISM — lateral inhibition as a RULE, not a hand-built DoG
------------------------------------------------------------------
**The bolt-on error, explicitly rejected (PROTOCOL §0):** `substrate_rs/vision.py`
ships `lgn_pair(sigma_on, sigma_off)` / `dog` — hand-designed difference-of-
Gaussian convolution kernels computed in numpy (`origin="dog"`). That is a
hand-built retina; its output is already *signed* (so it assumes away the exact
problem rung 5 identified) and it breaks Dale's law rather than modelling it.
Rung 6 rejected it and so does this rung. **Centre-surround must FALL OUT of
lateral inhibition.**

The honest version — horizontal-cell feedback over the `neighbour` edges the
adapter already wires (declared in `vision_waves.json`'s productions and, until
now, consumed by exactly ONE rule, `wv_propagate`; **the topology exists and is
unused**):

    h1 = mean burst over the RetinaCell's radius-1 neighbours   (the near surround)
    h2 = mean burst over its radius-2 neighbours                (the far surround)
    resid = c - g1*h1 - g2*h2        <- PREDICT the centre from the surround,
                                        TRANSMIT the residual
    x_ON  = [ resid]+                <- two NON-NEGATIVE channels ...
    x_OFF = [-resid]+                <- ... whose DIFFERENCE is the signed residual

**Dale-consistency.** `g1, g2` are clipped to `[0, lat_gmax]`: NON-NEGATIVE.
The horizontal cell is an inhibitory interneuron — a **sign-constant pathway**
that always subtracts. What is learned is the *magnitude* of a fixed-sign
pathway, never the sign of a weight. This is the same discipline rung 6 used for
the ON/OFF split: the sign lives in the PATHWAY, not in the weight.

**THIS CLOSES THE ARC'S OLDEST LOOP.** Retinal centre-surround IS predictive
coding / redundancy reduction (Srinivasan, Laughlin & Dubs 1982: *the surround
is the optimal linear predictor of the centre, subtracted; the output is the
residual*). That is the substrate's own `prediction_minus_observation`
meta-shape, in the first synapse — and `seeds/vision_floor.json`'s
`vf_predictive_suppression` already encodes it. Whitening is the paradigm's
FIRST OUTPUT, not something we hand it.

WHY THE GAIN IS **LEARNED**, AND NOT HAND-SET (this is the load-bearing choice)
-------------------------------------------------------------------------------
A FIXED `g` would be a hand-set constant — VISION_PRIOR_ART.md is blunt about
that class: *"Everything else (sigma ratios, tau values) is a hand-set constant
with no derivation. Do not claim those emerge."* So `g` is learned by an
anti-Hebbian / decorrelating rule on the horizontal-cell feedback synapse:

    dg_k = eta * resid * h_k                (k = 1, 2)

Its fixed point is exactly the **normal equations** — i.e. the optimal linear
predictor of the centre from the surround:

    E[resid * h_k] = 0  <=>  E[(c - g.h) h_k] = 0  <=>  g* = Cov(h,h)^-1 Cov(h,c)

which is **Srinivasan's optimal predictor, derived rather than received**. The
surround is not *declared* to be a predictor; the rule makes it one.

**AND IT BUYS THE FALSIFIABLE PREDICTION.** Because `g*` is a regression
coefficient, it must SHRINK when the surround becomes a worse predictor — i.e.
when input noise rises (low light / low SNR), noise inflates `Var(h)` without
adding to `Cov(h,c)`. That is **Atick & Redlich's closed-form prediction**: the
surround **weakens in the dark and sharpens in the light**. VISION_PRIOR_ART.md
names this one of only two mechanisms in the whole survey that come with a
NOISE-FREE CONTROL — *"feed the same video at two luminances; if the fitted
surround does not change, it is null. A bare grid + drift cannot accidentally
pass this."* A hand-set `g` cannot pass it by construction. A learned `g` can
FAIL it. That asymmetry is the point.

The radius-2 pool exists so the surround has a WIDTH that can move, not only a
strength — Atick & Redlich predict the surround **broadens** as well as weakens.
With one radius only "broadens" is unmeasurable.

**AND IT IS HONEST ABOUT WHITENING.** VISION_PRIOR_ART.md's scepticism is
recorded and respected: *"be skeptical of 'centre-surround IS whitening' — the
direct test concludes it is NOT: whitening yields the |f| ramp, not a DoG. You
need THREE constraints: decorrelation + response equalisation + a
size/sparseness constraint."* This rung therefore claims **decorrelation only**
(one of the three), and does NOT claim the DoG shape is derived from whitening.

ANATOMY — what the adapter states, and why it is not the answer in disguise
---------------------------------------------------------------------------
The adapter wires `neighbour2` (the radius-2 ring) exactly as `WaveWorld`
already wires `neighbour` (the radius-1 ring): *"mechanical geometry (the grid's
own adjacency), the only spatial fact the adapter states. WHAT travels along it,
and whether anything does, is the rules' business."* The adapter states only
WHICH cells are adjacent — a fact about a grid. It does not state that the
surround inhibits, nor how strongly, nor with what profile: `g1` and `g2` are
**learned from zero** (`lat_g0 = 0.0` by default, i.e. the layer starts as a
PURE CENTRE with no surround at all). The centre-surround profile is grown.

ABLATIONS ARE GRAPH DATA (PROTOCOL §0) — never a Python code path
-----------------------------------------------------------------
  lateral    = 0  -> the whole layer is inert (DEFAULT; PROTOCOL §9)
  learn_gain = 0  -> `g` is pinned at `lat_g0` (the FIXED-gain control:
                     separates "learning the predictor" from "any subtraction")
  radius2    = 0  -> `g2` pinned at 0 (radius-1 surround only)
  frozen     = 1  -> a REAL freeze: gates EVERY learning rule in this seed.

THE FREEZE (rung 6's hardest-won lesson, inherited deliberately)
----------------------------------------------------------------
`oja=0` IS NOT A FREEZE — `bh_potentiate`/`bh_depress`/`bh_scale` are each gated
on `WaveParams.oja == 0.0`, so setting it to "switch learning off" switches the
OTHER rule ON (rung 5 measured 47.9 max |dw| per probe from this). This seed
carries ONE flag, `LatParams.frozen`, in the `where` of every learning rule, so
no rule can learn while it is set regardless of which other rule is selected.
The activation rules (`lat_pool`/`lat_residual`/`lat_bipolar`) deliberately do
NOT carry it — a frozen cell must still RESPOND, or the probe measures silence.

DISTINCT EDGE TYPES ON PURPOSE
-------------------------------
`Retina -has_hcell-> HCell` and `RetinaCell -pools_to-> HCell` are separate
types rather than two incoming edges of one type: the tree has a recorded engine
gotcha that *two same-type incoming edges on one node can break `run_rules`
matching for that edge type* (found during the ink work; the writer shortcut
edge uses a distinct type `wrote_transform` for exactly this reason).
"""
from __future__ import annotations

import json
import os


# --------------------------------------------------------------------------- #
#  The DSL micro-layer — identical to tools/build_vision_onoff_seed.py's.
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


LP = lambda k: PARAM("LatParams", k)      # noqa: E731
WV = lambda k: PARAM("WaveParams", k)     # noqa: E731


def IN(node, et):    return {"type": "InNeighbours", "node": node,
                             "edge_type": et, "any_type": False}
def OUT(node, et):   return {"type": "Neighbours", "node": node,
                             "edge_type": et, "any_type": False}
def PICK(src):       return {"type": "Pick", "source": src}
def ITE(c, a, b):    return {"type": "IfThenElse", "cond": c, "then": a, "other": b}
def GT(a, b):        return {"type": "Gt", "a": a, "b": b}
def LT(a, b):        return {"type": "Lt", "a": a, "b": b}
def LTE(a, b):       return {"type": "Lte", "a": a, "b": b}
def EQ(a, b):        return {"type": "Eq", "a": a, "b": b}
def AND(*xs):        return {"type": "And", "items": list(xs)}
def PLUS(*xs):       return {"type": "Plus", "items": list(xs)}
def TIMES(*xs):      return {"type": "Times", "items": list(xs)}
def MINUS(a, b):     return {"type": "Minus", "a": a, "b": b}
def DIV(a, b):       return {"type": "Div", "a": a, "b": b}
def MIN(*xs):        return {"type": "Min", "items": list(xs)}
def MAX(*xs):        return {"type": "Max", "items": list(xs)}


def FOLD(src, var, acc, init, body):
    return {"type": "Fold", "source": src, "var_name": var, "acc_name": acc,
            "init": init, "body": body}


# The layer is live only when `lateral` is selected. EVERY rule carries this.
LIVE = GT(LP("lateral"), L(0.5))
# A real freeze — gates every LEARNING rule (never the activation rules: a
# frozen cell must still RESPOND, or the probe would measure silence).
AWAKE = LT(LP("frozen"), L(0.5))


def BURST(var):
    """The burst-within-window indicator for a RetinaCell bound as `var`.

    IDENTICAL to the latency the rest of the ladder reads (rung 6's
    `oo_bipolar_burst` uses this exact expression): a cell counts as active if
    it burst within `WaveParams.window_steps` of the Retina's current step. The
    clock is the Retina's `step`, never the cell's own.
    """
    return ITE(LTE(MINUS(A(V("r"), "step"), A(V(var), "last_burst")),
                   WV("window_steps")), L(1.0), L(0.0))


def _mean_over(edge_type, count_attr):
    """Mean burst over a RetinaCell's neighbours along `edge_type`.

    `count_attr` is the neighbour COUNT the adapter wrote on the HCell — pure
    grid geometry (edge cells have fewer neighbours), the same class of
    mechanical fact as `n_on`/`n_off` in rung 6's `add_signed_units`. Reading a
    stored count rather than a second Fold keeps the pooled value a true MEAN at
    the boundary, where a fixed divisor would fabricate a dark surround.
    """
    total = FOLD(OUT(V("c"), edge_type), "n", "acc", L(0.0),
                 PLUS(V("acc"), BURST("n")))
    return DIV(total, MAX(A(V("h"), count_attr), L(1.0)))


# --------------------------------------------------------------------------- #
#  RULES
# --------------------------------------------------------------------------- #
def rule_pool():
    """THE SURROUND ITSELF — a horizontal cell pools its neighbourhood.

    `h1` = mean burst over the radius-1 ring, `h2` = over the radius-2 ring.
    This is the ONLY rule in the vision ladder other than `wv_propagate` that
    reads a `neighbour` edge — the topology has been declared and unused since
    rung 1.

    `radius2 = 0` pins `h2 = 0` (radius-1 surround only), so the far ring can be
    ablated as DATA with the anatomy left standing (rung 4's lesson: an ablation
    that also removes anatomy is not null).

    Phase-guarded by `pool_step` so it fires once per cell per step and
    `lat_residual` cannot race it.
    """
    return {
        "name": "lat_pool",
        "comment": (
            "THE SURROUND. h1/h2 = mean burst over the RetinaCell's radius-1 / "
            "radius-2 rings, along the `neighbour` / `neighbour2` edges the "
            "adapter wires as grid geometry. Divided by the adapter-recorded "
            "neighbour COUNT, so a cell at the retina's edge pools a true MEAN "
            "rather than a fabricated dark surround. radius2=0 pins h2=0 with "
            "the anatomy untouched. Phase-guarded by pool_step."),
        "match_type": "HCell",
        "match": [["r", "has_hcell", "h"], ["c", "pools_to", "h"]],
        "where": AND(LIVE, LT(A(V("h"), "pool_step"), A(V("r"), "step"))),
        "effects": [
            ["set_attr", "h", "h1", T(_mean_over("neighbour", "n_nb1"))],
            ["set_attr", "h", "h2",
             T(ITE(GT(LP("radius2"), L(0.5)),
                   _mean_over("neighbour2", "n_nb2"), L(0.0)))],
            ["set_attr", "h", "pool_step", T(A(V("r"), "step"))],
        ],
    }


def rule_residual():
    """PREDICT THE CENTRE FROM THE SURROUND; TRANSMIT THE RESIDUAL.

        resid = c - g1*h1 - g2*h2

    This one line IS `prediction_minus_observation` — Srinivasan, Laughlin &
    Dubs (1982) in the first synapse, and the substrate's own core motion.
    `g1, g2 >= 0` always (Dale: the horizontal cell is a sign-constant
    inhibitory pathway), so this is a SUBTRACTION by a non-negative gain, never
    a negative weight.

    Sequenced after `lat_pool` by DATA DEPENDENCY (`pool_step == r.step`), never
    by Python ordering.
    """
    pred = PLUS(TIMES(A(V("h"), "g1"), A(V("h"), "h1")),
                TIMES(A(V("h"), "g2"), A(V("h"), "h2")))
    return {
        "name": "lat_residual",
        "comment": (
            "PREDICTIVE CODING, one line: resid = centre - g1*h1 - g2*h2. The "
            "surround is the optimal linear predictor of the centre "
            "(Srinivasan/Laughlin/Dubs 1982) and the transmitted signal is the "
            "RESIDUAL. g1,g2 are non-negative gains on a sign-constant "
            "inhibitory pathway (Dale). Waits on lat_pool via pool_step == "
            "r.step -- data dependency, not Python sequencing."),
        "match_type": "HCell",
        "match": [["r", "has_hcell", "h"], ["c", "pools_to", "h"]],
        "where": AND(LIVE,
                     LT(A(V("h"), "resid_step"), A(V("r"), "step")),
                     EQ(A(V("h"), "pool_step"), A(V("r"), "step"))),
        "effects": [
            ["set_attr", "h", "resid", T(MINUS(BURST("c"), pred))],
            ["set_attr", "h", "resid_step", T(A(V("r"), "step"))],
        ],
    }


def rule_bipolar():
    """THE ON/OFF SPLIT AS THE TWO RECTIFIED HALVES OF ONE RESIDUAL.

        x_ON = [resid]+      x_OFF = [-resid]+

    Both channels are NON-NEGATIVE and their DIFFERENCE is the signed residual —
    rung 6's requirement, met without a signed weight anywhere (a DoG's signed
    output would break Dale and assume away rung 5's finding).

    **AND THIS IS WHY THE OFF CHANNEL IS ALIVE AT ALL.** With `g = 0`,
    `resid = c >= 0` and the OFF channel is SILENT — which is correct biology
    (an OFF cell does not respond to a light increment). The OFF channel has
    something to say only once the surround PREDICTS a non-zero baseline, so
    that a non-bursting cell is a *decrement relative to the prediction*.
    **The predictor is what CREATES the OFF channel** — which is precisely
    VISION_PRIOR_ART.md's "ON/OFF as a residual mint": a rectified channel
    leaves the negative residual permanently unexplained, and the quantum that
    explains it IS the OFF channel.
    """
    return {
        "name": "lat_bipolar",
        "comment": (
            "x_ON = [resid]+, x_OFF = [-resid]+ : two NON-NEGATIVE channels "
            "whose difference is the signed residual. No signed weight, no "
            "hand-built DoG, Dale intact. NOTE: with g=0 the OFF channel is "
            "SILENT (resid = c >= 0) -- correct biology, and the reason the "
            "learned predictor is what BRINGS THE OFF CHANNEL TO LIFE: only a "
            "non-zero prediction makes a non-bursting cell a decrement. Waits "
            "on lat_residual via resid_step == r.step."),
        "match_type": "LBipolar",
        "match": [["r", "has_lbipolar", "b"], ["h", "rectifies_to", "b"]],
        "where": AND(LIVE,
                     LT(A(V("b"), "bstep"), A(V("r"), "step")),
                     EQ(A(V("h"), "resid_step"), A(V("r"), "step"))),
        "effects": [
            ["set_attr", "b", "bursting",
             T(ITE(GT(A(V("b"), "polarity"), L(0.0)),
                   MAX(A(V("h"), "resid"), L(0.0)),
                   MAX(TIMES(L(-1.0), A(V("h"), "resid")), L(0.0))))],
            ["set_attr", "b", "bstep", T(A(V("r"), "step"))],
        ],
    }


def rule_learn_gain():
    """THE SURROUND GAIN IS LEARNED, NOT HAND-SET — anti-Hebbian decorrelation.

        dg_k = eta * resid * h_k          clipped to [0, lat_gmax]

    FIXED POINT: `E[resid * h_k] = 0` for every k — the NORMAL EQUATIONS. So
    `g*` is the optimal linear predictor of the centre from the surround
    (Srinivasan 1982), DERIVED by the rule rather than received as a constant.
    The residual is decorrelated from the surround at convergence: that is
    redundancy reduction, and it is the whole claim of this rung.

    WHY THIS IS THE FALSIFIABLE VERSION. `g*` is a regression coefficient, so it
    MUST shrink as the surround becomes a worse predictor — input noise inflates
    `Var(h)` without adding to `Cov(h, c)`. That is Atick & Redlich's prediction
    (surround weakens in the dark, sharpens in the light), and it is a
    prediction a HAND-SET gain cannot make and a learned gain can FAIL.

    `learn_gain = 0` pins `g` at its initial value: the FIXED-gain control,
    isolating "learning the predictor" from "any subtraction at all".

    Clipped to `[0, lat_gmax]`: NON-NEGATIVE (Dale — a sign-constant inhibitory
    pathway whose MAGNITUDE is learned, never a weight that may change sign).
    """
    def upd(gk, hk):
        dg = TIMES(LP("lat_eta"), A(V("h"), "resid"), A(V("h"), hk))
        return MIN(MAX(PLUS(A(V("h"), gk), dg), L(0.0)), LP("lat_gmax"))

    return {
        "name": "lat_learn_gain",
        "comment": (
            "ANTI-HEBBIAN DECORRELATION: dg_k = eta*resid*h_k, clipped to "
            "[0, lat_gmax]. Fixed point E[resid*h_k]=0 == the normal equations "
            "== Srinivasan's optimal linear predictor of centre from surround, "
            "DERIVED not hand-set. This is what makes Atick & Redlich's "
            "SNR-dependent surround a falsifiable PREDICTION of the mechanism "
            "rather than a fitted constant. learn_gain=0 pins g (fixed-gain "
            "control). Non-negative by clipping: Dale holds -- the pathway's "
            "SIGN is fixed, only its MAGNITUDE is learned. Gated by `frozen` "
            "(a REAL freeze: oja=0 is NOT a freeze -- rung 5 measured 47.9 "
            "max|dw| per probe from that trap)."),
        "match_type": "HCell",
        "match": [["r", "has_hcell", "h"], ["c", "pools_to", "h"]],
        "where": AND(LIVE, AWAKE,
                     GT(LP("learn_gain"), L(0.5)),
                     LT(A(V("h"), "gain_step"), A(V("r"), "step")),
                     EQ(A(V("h"), "resid_step"), A(V("r"), "step"))),
        "effects": [
            ["set_attr", "h", "g1", T(upd("g1", "h1"))],
            ["set_attr", "h", "g2",
             T(ITE(GT(LP("radius2"), L(0.5)), upd("g2", "h2"), L(0.0)))],
            ["set_attr", "h", "gain_step", T(A(V("r"), "step"))],
        ],
    }


# --------------------------------------------------------------------------- #
#  THE MANIFEST
# --------------------------------------------------------------------------- #
def build() -> dict:
    return {
        "id": "vision_lateral",
        "version": "1.0.0",
        "depends_on": ["vision_waves"],
        "description": (
            "RUNG 7 — RETINAL LATERAL INHIBITION, so CENTRE-SURROUND EMERGES. A "
            "horizontal cell pools the RetinaCell's radius-1/radius-2 rings over "
            "the `neighbour` edges rung 1 declared and never used; the bipolar "
            "transmits the RESIDUAL centre - g1*h1 - g2*h2, split into two "
            "non-negative rectified halves. The surround gain is LEARNED by "
            "anti-Hebbian decorrelation (fixed point = the normal equations = "
            "Srinivasan's optimal linear predictor), never hand-set -- so "
            "centre-surround FALLS OUT of predictive coding instead of being "
            "bolted on as a numpy DoG, and Atick & Redlich's SNR-dependent "
            "surround becomes a falsifiable prediction. Ships INERT "
            "(lateral=0)."),
        "microtheory": {
            "name": "retinal_lateral_inhibition",
            "description": (
                "Predict the centre from the surround; transmit the residual. "
                "Centre-surround is redundancy reduction (Atick & Redlich 1992; "
                "Srinivasan, Laughlin & Dubs 1982; Barlow), i.e. the substrate's "
                "own prediction_minus_observation shape in the first synapse. "
                "Rung 6 measured that the complementary split x_OFF = 1 - x_ON "
                "is degenerate (C_ON,OFF(d) = -C_ON,ON(d) identically), so the "
                "channels carry no independent correlation structure for waves "
                "to sculpt (Miller 1994 needs DIFFERENT spatial dependence). "
                "Lateral inhibition gives each channel its own spatial "
                "dependence -- grown from the grid's adjacency, not handed over "
                "as a kernel."),
        },
        "nodes": [{
            "local_id": 0,
            "type": "LatParams",
            "attrs": {
                # PROTOCOL §9 — ships OFF so every committed result reproduces.
                "lateral": 0.0,
                # The gain is LEARNED (the whole point). 0 => pinned at lat_g0.
                "learn_gain": 1.0,
                # The far ring. 0 => g2 pinned at 0, anatomy untouched.
                "radius2": 1.0,
                # A REAL freeze — gates every learning rule in this seed.
                "frozen": 0.0,
                "lat_eta": 0.002,
                "lat_gmax": 2.0,
                # STARTS AS A PURE CENTRE: no surround at all. The
                # centre-surround profile is GROWN, never initialised in.
                "lat_g0": 0.0,
            },
        }],
        "edges": [],
        "productions": [
            {"src": {"type": "Retina", "var": "a"}, "edge_type": "has_hcell",
             "tgt": {"type": "HCell", "var": "b"},
             "provenance": "seed:vision_lateral:has_hcell"},
            {"src": {"type": "RetinaCell", "var": "a"}, "edge_type": "pools_to",
             "tgt": {"type": "HCell", "var": "b"},
             "provenance": "seed:vision_lateral:pools_to"},
            {"src": {"type": "Retina", "var": "a"}, "edge_type": "has_lbipolar",
             "tgt": {"type": "LBipolar", "var": "b"},
             "provenance": "seed:vision_lateral:has_lbipolar"},
            {"src": {"type": "HCell", "var": "a"}, "edge_type": "rectifies_to",
             "tgt": {"type": "LBipolar", "var": "b"},
             "provenance": "seed:vision_lateral:rectifies_to"},
            {"src": {"type": "RetinaCell", "var": "a"}, "edge_type": "neighbour2",
             "tgt": {"type": "RetinaCell", "var": "b"},
             "provenance": "seed:vision_lateral:neighbour2"},
        ],
        "rules": [
            rule_pool(),
            rule_residual(),
            rule_bipolar(),
            rule_learn_gain(),
        ],
    }


if __name__ == "__main__":
    dst = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "seeds", "vision_lateral.json")
    with open(dst, "w") as fh:
        json.dump(build(), fh, indent=1)
        fh.write("\n")
    print(f"wrote {dst}")
