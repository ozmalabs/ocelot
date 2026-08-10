#!/usr/bin/env python3
"""Emit seeds/vision_mccollough.json — the McCOLLOUGH CONTINGENT AFTEREFFECT,
the DECISIVE predictive-coding gate (VISION_MCCOLLOUGH_PREREG.md, seeds 41000-41999).

The McCollough effect: after adapting to colour-ORIENTATION pairings (red-vertical
+ green-horizontal), an ACHROMATIC vertical grating is perceived greenish and a
horizontal one pinkish -- an ORIENTATION-CONTINGENT colour aftereffect, opposite the
adapted colour, extremely persistent, error-driven.

THE MECHANISM (VISION_VENTRAL_GROUNDING.md): the aftereffect is the NEGATIVE RESIDUAL
of an over-fit contingency prior. The system learns the joint (colour x orientation)
statistic E[colour | orientation]; at test the prior RENDERS the expected colour for
the test orientation and the percept is the OPPONENT RESIDUAL observed - predicted.
Achromatic observed (0) minus a rendered red prior (+rg) = -rg = GREEN.

THE CRUX (PROTOCOL §1.1): a genuine PREDICTIVE / opponent code (render-from-prior +
subtract) PRODUCES the contingent aftereffect; a FEEDFORWARD classifier control
(direct read of the input colour, NO render-from-prior) does NOT -- achromatic in,
achromatic out. That discrimination is the whole test. Both readouts are seeded; a
flag (mcc_mode) selects which fires -- the ablation is GRAPH DATA, not a Python path
(PROTOCOL §0 / CLAUDE.md).

COMPOSITION, NO NEW RUST. Reuses the opponent coordinates rg=L-M, by=S-(L+M) of
vision_colour's cc_contrast and the "predict, transmit the residual" shape of
vision_lateral's lat_residual -- here the predictor is the ORIENTATION prior, not the
spatial surround. The prior is the running MEAN colour given orientation
(Div(sum, Max(n,1))) -- ZERO learning rate, ZERO magic number (PROTOCOL §13); the
percept SIGN is fixed by the sign of the adapting colour, invariant to any scale.

This is a seed BUILDER (emits graph data) -- admissible under CLAUDE.md.
Run from the gamma-substrate dir:  python tools/build_vision_mccollough.py
"""
from __future__ import annotations
import json
import os


# --- term constructors (the DSL JSON forms, same as build_vision_colour.py) ----
def V(name):            return {"type": "Var", "name": name}
def Lit(v):             return {"type": "Lit", "value": v}
def A(node, key):       return {"type": "Attr", "node": node, "key": key}
def Gt(a, b):           return {"type": "Gt", "a": a, "b": b}
def Lt(a, b):           return {"type": "Lt", "a": a, "b": b}
def And(items):         return {"type": "And", "items": items}
def Plus(items):        return {"type": "Plus", "items": items}
def Minus(a, b):        return {"type": "Minus", "a": a, "b": b}
def Times(items):       return {"type": "Times", "items": items}
def Div(a, b):          return {"type": "Div", "a": a, "b": b}
def Max(items):         return {"type": "Max", "items": items}
def NodesWhere(nt, key, value):
    return {"type": "NodesWhere", "node_type": nt, "attr_key": key, "value": value}
def PickUnique(src):    return {"type": "PickUnique", "source": src}
def term(x):            return {"__term__": x}


def PickMP():
    return PickUnique({"type": "NodesOfType", "node_type": "MccoughParams"})


def mp(key):
    """An MccoughParams flag/counter (singleton)."""
    return A(PickMP(), key)


# --- per-node opponent coordinates (integer, in-frame), from raw cone attrs ----
def RG(node):   return Minus(A(node, "cL"), A(node, "cM"))                          # L-M
def BY(node):   return Minus(A(node, "cS"), Plus([A(node, "cL"), A(node, "cM")]))   # S-(L+M)


# --- the learned prior for orientation theta = MEAN colour given orientation ---
# w = Div(sum, Max(n,1)): when n==0 (never adapted) this is 0/1 = 0 -> NO prior ->
# NO aftereffect (the floor arm). No learning rate, no magic number (§13).
def prior(K, axis):     return Div(A(K, "sum_" + axis), Max([A(K, "n"), Lit(1.0)]))


def build():
    params = {
        "local_id": 0,
        "type": "MccoughParams",
        "attrs": {
            "name": "default",
            "mcc_enabled": 0.0,   # 0 (DEFAULT) = seed INERT; committed results reproduce (§9)
            "mcc_mode": 0.0,      # 0 = PREDICTIVE (render-from-prior + residual); 1 = FEEDFORWARD control (the crux)
            "mcc_phase": 0.0,     # 0 = ADAPT (learn E[colour|orientation]); 1 = TEST (read percept)
            "frame": 0.0,         # adaptation-frame counter (adapter increments); per-frame once-guard
            "comment": (
                "ALL knobs are GRAPH DATA (PROTOCOL §0). mcc_enabled: 0 DEFAULT = "
                "seed INERT, every committed result reproduces byte-identically (§9); "
                ">0.5 arms it. mcc_mode: 0 = PREDICTIVE readout (percept = observed - "
                "render-from-prior, the opponent residual that IS the contingent "
                "aftereffect); 1 = FEEDFORWARD control (percept = observed colour "
                "directly, NO render-from-prior) which by construction produces NO "
                "aftereffect on achromatic input -- THE CRUX, §1.1. mcc_phase: 0 = "
                "adapt (mcc_learn accumulates the joint statistic); 1 = test (a "
                "percept rule fires). frame: the adapter increments it per adapting "
                "frame so mcc_learn fires exactly once per frame (astep<frame guard, "
                "vision_theta's rbar_step<step idiom). The prior is the running MEAN "
                "colour given orientation (Div(sum,Max(n,1))) -- NO learning rate, NO "
                "magic number (§13); the aftereffect SIGN is fixed by the sign of the "
                "adapting colour and is invariant to any scale."
            ),
        },
    }

    # -- mcc_learn: LEARN the joint statistic E[colour | orientation] ------------
    # For each ADAPTING region R wired to its orientation prior K, once per frame,
    # accumulate the opponent colour onto K (sum += colour, n += 1). The running
    # mean sum/n IS the render-from-prior at test. Error-driven, persistent (stored
    # on the graph, survives arbitrary intervening ticks -- NOT momentary fatigue).
    learn = {
        "name": "mcc_learn",
        "comment": (
            "ADAPTATION -- learn E[colour|orientation]. Match an adapting Region R "
            "(is_adapt>0.5) and, via its single incoming `tunes` edge, its "
            "orientation prior K (vision_onoff's oo_bipolar_burst incoming-edge "
            "join; each R has exactly ONE incoming `tunes`, avoiding the "
            "two-incoming-edges matcher gotcha). Once per frame (astep<frame): "
            "accumulate the opponent colour rg=L-M, by=S-(L+M) onto K's running sum "
            "and increment n. The prior sum/n is the joint colour-orientation "
            "statistic; it is STORED (persists across ticks -> not fatigue) and "
            "ERROR-DRIVEN (its magnitude is the learned adapting-colour mean). "
            "Gated on mcc_enabled>0.5 AND mcc_phase<0.5 (adapt). NO learning rate "
            "(§13)."
        ),
        "match": [["scene", "has_region", "R"], ["K", "tunes", "R"]],
        "where": And([
            Gt(mp("mcc_enabled"), Lit(0.5)),
            Lt(mp("mcc_phase"), Lit(0.5)),              # ADAPT phase
            Gt(A(V("R"), "is_adapt"), Lit(0.5)),        # only adapting stimuli
            Lt(A(V("R"), "astep"), mp("frame")),        # once per frame
        ]),
        "effects": [
            ["set_attr", "K", "sum_rg", term(Plus([A(V("K"), "sum_rg"), RG(V("R"))]))],
            ["set_attr", "K", "sum_by", term(Plus([A(V("K"), "sum_by"), BY(V("R"))]))],
            ["set_attr", "K", "n",      term(Plus([A(V("K"), "n"), Lit(1.0)]))],
            ["set_attr", "R", "astep",  term(mp("frame"))],
        ],
    }

    # -- mcc_percept_pred: PREDICTIVE readout (render-from-prior + residual) ------
    # percept = observed opponent colour - prior(orientation). Achromatic test
    # (observed 0) minus a rendered +red prior = -red = GREEN: the contingent,
    # opponent, orientation-specific aftereffect. THE predictive-coding percept.
    pred = {
        "name": "mcc_percept_pred",
        "comment": (
            "PREDICTIVE-CODING percept (mcc_mode<0.5). percept = OBSERVED opponent "
            "colour MINUS the render-from-prior for this region's orientation "
            "(prior = K.sum/Max(K.n,1), the learned mean). This is vision_lateral's "
            "lat_residual shape -- predict, transmit the residual -- with the "
            "ORIENTATION prior as the predictor instead of the spatial surround. On "
            "an ACHROMATIC test (observed rg=by=0) the percept is -prior: opposite "
            "the adapted colour, contingent on orientation (swap orientation -> "
            "different K -> flipped aftereffect). With no adaptation K.n=0 -> "
            "prior=0/1=0 -> percept=observed (NO aftereffect). Test regions only "
            "(is_adapt<0.5), once (pdone guard), gated on mcc_enabled>0.5 AND "
            "mcc_phase>0.5 (test)."
        ),
        "match": [["scene", "has_region", "R"], ["K", "tunes", "R"]],
        "where": And([
            Gt(mp("mcc_enabled"), Lit(0.5)),
            Gt(mp("mcc_phase"), Lit(0.5)),              # TEST phase
            Lt(mp("mcc_mode"), Lit(0.5)),               # PREDICTIVE
            Lt(A(V("R"), "is_adapt"), Lit(0.5)),        # test stimuli only
            Lt(A(V("R"), "pdone"), Lit(0.5)),           # once
        ]),
        "effects": [
            ["set_attr", "R", "percept_rg", term(Minus(RG(V("R")), prior(V("K"), "rg")))],
            ["set_attr", "R", "percept_by", term(Minus(BY(V("R")), prior(V("K"), "by")))],
            ["set_attr", "R", "pdone", term(Lit(1.0))],
        ],
    }

    # -- mcc_percept_ff: FEEDFORWARD control (the CRUX) --------------------------
    # percept = observed opponent colour, DIRECTLY. The prior K is matched (same
    # information available) but NOT rendered/subtracted -- no predictive loop. On
    # an achromatic test the percept is 0: NO aftereffect. This is the dead-arm
    # discriminator (§1.1): a mechanism that "explains" McCollough without the
    # predictive loop MUST fail to reproduce it. Positive-controlled: on a COLOURED
    # test this arm reports the real colour (percept = observed != 0), so its null
    # on achromatic input is a real null, not a dead arm.
    ff = {
        "name": "mcc_percept_ff",
        "comment": (
            "FEEDFORWARD control (mcc_mode>0.5) -- THE CRUX, §1.1. percept = the "
            "OBSERVED opponent colour, read directly. The orientation prior K is "
            "matched (identical information is available) but is NOT rendered or "
            "subtracted -- there is no predictive loop. On an achromatic test the "
            "percept is exactly 0: NO contingent aftereffect, for EITHER orientation "
            "-- a feedforward classifier cannot fake McCollough. ALIVE / "
            "positive-controlled: on a genuinely coloured test this same arm reports "
            "the real colour (percept = observed != 0), so its achromatic null is a "
            "real null, not a dead arm scoring a perfect floor. Test regions only, "
            "once, gated on mcc_enabled>0.5 AND mcc_phase>0.5."
        ),
        "match": [["scene", "has_region", "R"], ["K", "tunes", "R"]],
        "where": And([
            Gt(mp("mcc_enabled"), Lit(0.5)),
            Gt(mp("mcc_phase"), Lit(0.5)),              # TEST phase
            Gt(mp("mcc_mode"), Lit(0.5)),               # FEEDFORWARD
            Lt(A(V("R"), "is_adapt"), Lit(0.5)),
            Lt(A(V("R"), "pdone"), Lit(0.5)),
        ]),
        "effects": [
            ["set_attr", "R", "percept_rg", term(RG(V("R")))],
            ["set_attr", "R", "percept_by", term(BY(V("R")))],
            ["set_attr", "R", "pdone", term(Lit(1.0))],
        ],
    }

    seed = {
        "id": "vision_mccollough",
        "version": "1.0.0",
        "depends_on": [],
        "description": (
            "McCOLLOUGH CONTINGENT AFTEREFFECT -- the DECISIVE predictive-coding "
            "gate. After adapting to colour-orientation pairings (red-vertical, "
            "green-horizontal), an ACHROMATIC vertical grating is perceived greenish "
            "and a horizontal one pinkish: an orientation-CONTINGENT, OPPONENT, "
            "persistent, error-driven colour aftereffect. Mechanism "
            "(VISION_VENTRAL_GROUNDING.md): the aftereffect is the negative residual "
            "of an over-fit contingency prior -- the system learns the joint "
            "E[colour|orientation] and the percept is the render-from-prior + "
            "opponent-residual (observed - predicted). THE CRUX (§1.1): the "
            "PREDICTIVE readout produces the aftereffect; a FEEDFORWARD control "
            "(direct colour read, no render-from-prior) does NOT -- both are seeded, "
            "a flag selects (ablation = graph data, §0). COMPOSITION, NO NEW RUST: "
            "reuses vision_colour's opponent coordinates (rg=L-M, by=S-(L+M)) and "
            "vision_lateral's predict-then-residual shape, with the ORIENTATION "
            "prior as predictor. The prior is the running MEAN colour given "
            "orientation (Div(sum,Max(n,1))) -- ZERO magic number (§13); the "
            "aftereffect SIGN is fixed by the adapting-colour sign, scale-invariant. "
            "Flag-gated on MccoughParams.mcc_enabled, OFF by default (§9). VALIDATION "
            "gate for predictive/opponent joint colour-orientation coding, NOT a "
            "recognition capability; orientation is supplied as a stimulus feature, "
            "not grown (grown orientation maps are the diagnosed Hebbian dead-end). "
            "See VISION_MCCOLLOUGH_PREREG.md."
        ),
        "microtheory": "vision",
        "nodes": [params],
        "edges": [],
        "productions": [],
        "rules": [learn, pred, ff],
    }
    return seed


def main():
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out = os.path.join(here, "seeds", "vision_mccollough.json")
    seed = build()
    with open(out, "w") as f:
        json.dump(seed, f, indent=2)
        f.write("\n")
    print("wrote", out, "-", len(seed["rules"]), "rules")


if __name__ == "__main__":
    main()
