#!/usr/bin/env python
"""AUTHORING SCRIPT (one-off, not runtime): JOB 2 — kill the constant.

`mu = 0.024` is GCAL's target average activity, imported into an unnormalised
frame. It killed cells in two independent layers (rung 8B: theta wound to 26.9,
rbar exactly 0; the eye: min aliveness 10.5%, a 16.6x compression of a measured
drive of 0.398910). PROTOCOL §13: the fix is NEVER to tune it.

WHERE THE SETPOINT NOW FALLS OUT OF — one sentence, as §13 demands:

  **The setpoint is the mean output the cell measured IN ITSELF during the
  pre-visual phase, when its only input was its own spontaneous retinal waves.**

No free parameter. No fraction, no `/2` (FM-1b's arm B used `natural/2 = 0.1995`
-- the `/2` is a fudge factor inside something labelled "falls out", and it was
measured by the HOST off the VISUAL input, which is exactly the frame the
setpoint is supposed to precede).

WHY THIS IS COMMENSURATE, and it is the crux: GCAL's `mu` is a target MEAN
ACTIVITY -- "the fraction of its dynamic range the cell should use". The mean
endogenous burst rate is THE SAME QUANTITY, in the same [0,1] units (`resp` is
bounded by `rmax`), measured rather than imported. The pathology was never that
0.024 was the wrong number; it was that an ABSOLUTE setpoint asserts a scale the
system has no way to know (§13's "an absolute constant IS a view from nowhere").

THE MECHANISM, all graph data:
  * `RetinaCell -endo_drives-> EyeCell` -- co-located 1:1. The two populations
    are both h*w on the same grid, and a receptor and the wave at its own
    location are the SAME PLACE in the sheet. `wave_world.drive`'s docstring is
    explicit that these are TWO PATHWAYS CONVERGING ON ONE OUTPUT: waves come
    from the inner-retina amacrine network, light comes through the
    photoreceptors, and both make the ganglion cell fire.
  * `ey_endo_resp` -- during the calibration phase the cell's OUTPUT IS its
    spontaneous burst. Not routed through `lum`: a wave is not light and must
    not be laundered through phototransduction.
  * `ey_endo_latch` -- `mu_endo := xbar`. NO NEW MACHINERY: `xbar` is the EMA of
    `resp` the cell ALREADY keeps (ey_xbar), so during the pre-visual phase it
    IS the mean endogenous rate, by the cell's own existing controller.
  * `ey_adapt_theta_endo` -- the homeostat, reading the cell's OWN `mu_endo`.

COULD THIS PRODUCE THE OPPOSITE RESULT? YES, and that is the point (§13.1).
Nothing here forces the cell to live. The wave statistics were fixed by RUNG 1,
long before this question existed, and they are not consulted about the answer:
if the endogenous burst rate is ~0.02, `mu_endo` lands on GCAL's value and the
eye dies EXACTLY as it does now -- which would be evidence AGAINST the creator's
pre-visual thesis, and would be reported as such (§7). The mechanism measures a
number it does not control.

Every arm is DATA (PROTOCOL §0) and OFF by default (§9): `calib=0`, `mu_mode=0`.

Run:  python tools/patch_vision_eye_setpoint.py
"""
import json
import os

SEED = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    "seeds", "vision_eye.json")


def attr(node, key):
    return {"type": "Attr", "node": node, "key": key}


def var(n):
    return {"type": "Var", "name": n}


def lit(v):
    return {"type": "Lit", "value": v}


def param(key):
    """A config read on the EyeParams SINGLETON.

    `PickUnique`, never `Pick` (main's 185-read rebind, `PickUnique` in
    `runners/dsl/src/term.rs`): `Pick` returns `iter().next()` -- ONE of N
    candidates, silently, so a second params node would be ignored without a
    word. `PickUnique` is identical for 0 or 1 and PANICS on >1, so an ambiguous
    config read SCREAMS instead of quietly reading someone else's default. Same
    disease as `.get('Name','')` and a guarded division returning 0.0 (§1.1,
    §12) -- a silent wrong answer where there should be an error.
    """
    return attr({"type": "PickUnique", "source": {"type": "NodesOfType",
                                                  "node_type": "EyeParams"}}, key)


def gt(a, b):
    return {"type": "Gt", "a": a, "b": b}


def lt(a, b):
    return {"type": "Lt", "a": a, "b": b}


def eq(a, b):
    return {"type": "Eq", "a": a, "b": b}


def term(t):
    return {"__term__": t}


PRODUCTION = {
    "src": {"type": "RetinaCell", "var": "a"}, "edge_type": "endo_drives",
    "tgt": {"type": "EyeCell", "var": "b"},
    "provenance": "seed:vision_eye",
}

ENDO_RESP = {
    "name": "ey_endo_resp",
    "comment": (
        "THE PRE-VISUAL PHASE: the cell's output IS its own spontaneous burst. "
        "Before eye-opening there is no light, and the retina is not silent -- "
        "it generates waves. `resp := bursting` of the RetinaCell at this "
        "receptor's OWN location. DELIBERATELY NOT ROUTED THROUGH `lum`: a wave "
        "is not light, and laundering it through the log receptor would model "
        "the amacrine network as a photon source. `wave_world.drive` states the "
        "biology this follows -- two pathways (waves via the inner retina, light "
        "via the photoreceptors) converging on one RGC output. Gated `calib`, "
        "default 0 (PROTOCOL §9)."
    ),
    "match_type": "EyeCell",
    "match": [["e", "has_eyecell", "c"], ["rc", "endo_drives", "c"]],
    "where": {"type": "And", "items": [
        gt(param("eye"), lit(0.5)),
        gt(param("calib"), lit(0.5)),
        lt(attr(var("c"), "resp_step"), attr(var("e"), "step")),
    ]},
    "effects": [
        ["set_attr", "c", "resp", term(attr(var("rc"), "bursting"))],
        ["set_attr", "c", "resp_step", term(attr(var("e"), "step"))],
    ],
}

ENDO_LATCH = {
    "name": "ey_endo_latch",
    "comment": (
        "THE SETPOINT FALLS OUT, AND IT IS A CUMULATIVE MEAN, NOT AN EMA: "
        "mu_endo_n = mu_endo_{n-1} + (resp - mu_endo_{n-1})/n, i.e. the running "
        "average of every endogenous output the cell has ever produced. "
        "MEASURED FIRST, THEN FIXED (PROTOCOL §2). The first cut latched `xbar` "
        "-- the cell's existing EMA (beta=0.991) -- and §2 caught it: an EMA is "
        "a TRACKING FILTER, not an estimator. Its variance does not decay "
        "(steady-state SD ~ sqrt(p(1-p)(1-beta)/(1+beta)) ~ 0.024 at p=0.146), "
        "so it fluctuates forever and HAS NO STABLE FIXED POINT -- exactly the "
        "condition §2 says cannot model development, where prolonged exposure to "
        "formative statistics STABILISES a representation. Measured: the EMA "
        "tracked the input's mean correctly (0.1437 vs 0.1462) but its L2 drift "
        "sat at ~0.078 and never approached 0. A cumulative mean's variance "
        "falls as 1/n, so it CONVERGES to E[resp] -- the endogenous rate -- and "
        "the drift genuinely goes to zero. "
        "IT ALSO REMOVES THE LAST IMPORTED CONSTANT FROM THE SETPOINT PATH: "
        "beta=0.991 is GCAL's too, and the setpoint no longer touches it. What "
        "`mu_endo` falls out of is now ONLY the cell's own spontaneous output "
        "and the number of steps it has lived -- no constant of anyone's. "
        "When `calib` goes to 0 the rule stops firing and `mu_endo` HOLDS: the "
        "setpoint the system established for itself before it ever saw anything. "
        "Both effects read the PRE-state `mu_n`, so the update is correct under "
        "either simultaneous or sequential effect semantics."
    ),
    "match_type": "EyeCell",
    "match": [["e", "has_eyecell", "c"]],
    "where": {"type": "And", "items": [
        gt(param("eye"), lit(0.5)),
        gt(param("calib"), lit(0.5)),
        lt(attr(var("c"), "mu_endo_step"), attr(var("e"), "step")),
        eq(attr(var("c"), "resp_step"), attr(var("e"), "step")),
    ]},
    "effects": [
        # mu_endo <- (mu_endo*n + resp) / (n+1)
        ["set_attr", "c", "mu_endo", term({
            "type": "Div",
            "a": {"type": "Plus", "items": [
                {"type": "Times", "items": [attr(var("c"), "mu_endo"),
                                            attr(var("c"), "mu_n")]},
                attr(var("c"), "resp"),
            ]},
            "b": {"type": "Plus", "items": [attr(var("c"), "mu_n"), lit(1.0)]},
        })],
        ["set_attr", "c", "mu_n", term({"type": "Plus", "items": [
            attr(var("c"), "mu_n"), lit(1.0)]})],
        ["set_attr", "c", "mu_endo_step", term(attr(var("e"), "step"))],
    ],
}

ADAPT_ENDO = {
    "name": "ey_adapt_theta_endo",
    "comment": (
        "GCAL Eq. 8 with the imported constant REMOVED: theta drifts to hold the "
        "cell's mean output at the setpoint THE CELL MEASURED IN ITSELF "
        "(`mu_endo`), not at a number from someone else's frame. Structurally "
        "identical to `ey_adapt_theta` in every other respect -- same lam, same "
        "placement outside the learning rule, same step gates -- so the ONLY "
        "difference between the arms is where the setpoint came from. That is "
        "what makes this a controlled comparison rather than two models. Gated "
        "`mu_mode>0.5`, default 0 (PROTOCOL §9); the imported-constant rule "
        "carries the complementary `mu_mode<0.5` guard, which is TRUE at the "
        "default, so every committed result reproduces byte-identically."
    ),
    "match_type": "EyeCell",
    "match": [["e", "has_eyecell", "c"]],
    "where": {"type": "And", "items": [
        gt(param("eye"), lit(0.5)),
        lt(param("frozen"), lit(0.5)),
        gt(param("homeo"), lit(0.5)),
        lt(param("calib"), lit(0.5)),
        gt(param("mu_mode"), lit(0.5)),
        lt(param("theta_mode"), lit(0.5)),
        lt(attr(var("c"), "theta_step"), attr(var("e"), "step")),
        eq(attr(var("c"), "xbar_step"), attr(var("e"), "step")),
    ]},
    "effects": [
        ["set_attr", "c", "theta", term({"type": "Plus", "items": [
            attr(var("c"), "theta"),
            {"type": "Times", "items": [
                param("lam"),
                {"type": "Minus", "a": attr(var("c"), "xbar"),
                 "b": attr(var("c"), "mu_endo")},
            ]},
        ]})],
        ["set_attr", "c", "theta_step", term(attr(var("e"), "step"))],
    ],
}


def main():
    with open(SEED) as f:
        d = json.load(f)

    p = d["nodes"][0]
    assert p["type"] == "EyeParams", p["type"]
    p["attrs"]["calib"] = 0.0
    p["attrs"]["mu_mode"] = 0.0

    have = {(pr["src"]["type"], pr["edge_type"], pr["tgt"]["type"])
            for pr in d["productions"]}
    key = (PRODUCTION["src"]["type"], PRODUCTION["edge_type"],
           PRODUCTION["tgt"]["type"])
    if key not in have:
        d["productions"].append(PRODUCTION)

    by_name = {r["name"]: r for r in d["rules"]}

    # --- guards on the EXISTING rules. Each is TRUE at the defaults, so the
    #     committed behaviour is byte-identical (PROTOCOL §9). ---
    # `ey_response` must not fight `ey_endo_resp` during the pre-visual phase:
    # in the dark the cell's output is its burst, not max(x-theta,0).
    resp = by_name["ey_response"]
    resp["where"]["items"].append(lt(param("calib"), lit(0.5)))
    # theta must not adapt during calibration: the phase MEASURES the cell's
    # endogenous rate, and a homeostat running during the measurement would be
    # regulating the very quantity being measured.
    ad = by_name["ey_adapt_theta"]
    ad["where"]["items"].append(lt(param("calib"), lit(0.5)))
    ad["where"]["items"].append(lt(param("mu_mode"), lit(0.5)))

    names = [r["name"] for r in d["rules"]]
    if "ey_endo_resp" not in names:
        i = names.index("ey_xbar")
        d["rules"][i:i] = [ENDO_RESP]
        names = [r["name"] for r in d["rules"]]
    if "ey_endo_latch" not in names:
        i = names.index("ey_adapt_theta")
        d["rules"][i:i] = [ENDO_LATCH]
        names = [r["name"] for r in d["rules"]]
    if "ey_adapt_theta_endo" not in names:
        i = names.index("ey_adapt_theta") + 1
        d["rules"][i:i] = [ADAPT_ENDO]

    d["version"] = "1.2.0"

    with open(SEED, "w") as f:
        json.dump(d, f, indent=1)
        f.write("\n")
    print(f"patched {SEED}")
    print(f"  productions: {len(d['productions'])}")
    print(f"  rules:       {len(d['rules'])}")


if __name__ == "__main__":
    main()
