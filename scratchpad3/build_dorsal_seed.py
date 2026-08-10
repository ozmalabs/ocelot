"""Emit seeds/vision_dorsal.json — RUNG 3's dorsal/motion seed.

Authoring script (tools/-class: it EMITS graph data and is not agent runtime).
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ---- term helpers (pure JSON construction) --------------------------------
def V(n): return {"type": "Var", "name": n}
def L(v): return {"type": "Lit", "value": v}
def A(node, key): return {"type": "Attr", "node": node, "key": key}
def P(dp, key): return A({"type": "Pick", "source": {"type": "NodesOfType", "node_type": dp}}, key)
def T(term): return {"__term__": term}

def DP(key): return P("DorsalParams", key)

STEP = A(V("r"), "step")

# latency of THIS synapse's pre cell's TRANSIENT, as the rule sees it
def lat(pre_node):
    return {"type": "Minus", "a": STEP, "b": A(pre_node, "dlast_burst")}

SY_PRE = {"type": "Pick", "source": {"type": "InNeighbours", "node": V("sy"),
                                     "edge_type": "dpre", "any_type": False}}

def delay_match(pre_node, syn_var):
    """1.0 iff the pre TRANSIENT's latency lands in this synapse's arrival
    window [delay, delay+delay_tol]. THE DIRECTION MECHANISM: a synapse
    contributes only when its pre cell's transient fired exactly `delay` steps
    ago, so a DUnit sums inputs that are COINCIDENT AT THE UNIT rather than
    coincident at the retina. delay_tol=0 is exact coincidence."""
    la = lat(pre_node)
    d = A(syn_var, "delay")
    return {"type": "IfThenElse",
            "cond": {"type": "And", "items": [
                {"type": "Gte", "a": la, "b": d},
                {"type": "Lte", "a": la, "b": {"type": "Plus", "items": [d, DP("delay_tol")]}},
            ]},
            "then": L(1.0), "other": L(0.0)}


DORSAL_ON = {"type": "Gt", "a": DP("dorsal"), "b": L(0.5)}

# ---- rules ---------------------------------------------------------------

dv_transient = {
    "name": "dv_transient",
    "comment": (
        "THE TRANSIENT (MAGNOCELLULAR) CHANNEL — a cell's dorsal output fires on "
        "the ONSET of its burst, not on its level: dlast_burst records the step "
        "at which the cell STARTED bursting after not bursting on the previous "
        "step. This is asserted biology, not convenience: the dorsal stream is "
        "fed by transient M/Y-type retinal ganglion cells, which respond to "
        "CHANGE and adapt away static input, while the ventral stream's "
        "sustained P/X cells carry level. The rules therefore read DIFFERENT "
        "retinal channels off the same cells, which is exactly the parallel "
        "anatomy the research established.\n\n"
        "IT IS ALSO FORCED BY A MEASURED PATHOLOGY, and finding it before the "
        "run is why the rung is testable at all. The committed drive() "
        "median-splits each frame, so on real video a bright pixel stays bright: "
        "measured duty cycle 0.500, of which 0.481 is SUSTAINED and only 0.019 "
        "is onset. `last_burst` is overwritten on every step a cell is on, so a "
        "sustained cell's latency is PERMANENTLY 0 and only delay=0 synapses can "
        "ever match. On the sustained channel the delay line is STRUCTURALLY "
        "BLIND to video — the `normal` arm could not have produced direction "
        "selectivity for an instrumental reason, and the null would have been "
        "read as 'direction needs more than experience' when it actually meant "
        "'the instrument had no temporal edges to read'. That is the wrong-arm "
        "failure PROTOCOL section 6 is about, caught by measuring the drive "
        "before running the arms rather than after.\n\n"
        "THE SPLIT IS PRESERVED: the ADAPTER records only FACTS (last_burst = "
        "when this cell burst; prev_burst = what last_burst was before this "
        "step's update — bookkeeping, for the same reason wave_world already "
        "writes last_burst in the adapter: a rule writing it would race the "
        "rules reading it inside one fixpoint). This RULE makes the DECISION of "
        "what counts as a transient. Waves are unaffected by the change — a wave "
        "cell is active for exactly one step before refracting, so every wave "
        "burst already IS an onset and the dark arm reads the same events either "
        "way."),
    "match_type": "RetinaCell",
    "match": [["r", "has_cell", "c"]],
    "where": {"type": "And", "items": [
        DORSAL_ON,
        {"type": "Eq", "a": A(V("c"), "last_burst"), "b": STEP},
        {"type": "Lt", "a": A(V("c"), "prev_burst"),
         "b": {"type": "Minus", "a": STEP, "b": L(1.0)}},
    ]},
    "effects": [["set_attr", "c", "dlast_burst", T(STEP)]],
}

dv_unit_activate = {
    "name": "dv_unit_activate",
    "comment": (
        "THE DIRECTION MECHANISM — a DELAY-LINE COINCIDENCE DETECTOR. A DUnit's "
        "drive = sum over its DSynapses of weight x [the pre cell burst EXACTLY "
        "`delay` steps ago]. This is the one structural difference from the "
        "ventral wv_unit_activate, which counts ANY pre-burst inside a shared "
        "[0, window_steps] box and is therefore blind to ORDER by construction: "
        "a->b and b->a deliver the identical set of in-window bursts, so no "
        "weight assignment on that rule can ever prefer one. Here each synapse "
        "carries its OWN conduction delay, so inputs that were SEQUENTIAL at the "
        "retina arrive SIMULTANEOUSLY at the unit iff the sequence matches the "
        "delay gradient (delay + position-along-motion = const). That is the "
        "classical asymmetric-conduction-delay account of direction "
        "selectivity, and it makes ORDER a first-class thing the rule can read. "
        "CRITICALLY, the delays are NOT a hand-built direction gradient: the "
        "adapter draws them UNIFORMLY AT RANDOM (unstructured entropy, exactly "
        "like the weight jitter and the wave ignition), and WHICH delay/position "
        "combinations cohere is what dv_oja_learn has to discover from the "
        "input's own motion statistics. Handing the agent a tuned delay gradient "
        "would be the `preprocess_patches` bolt-on error at the motion grain. "
        "PARALLEL, NOT LATER: DUnit/DSynapse/has_dunit are a separate population "
        "reading the SAME retina, because the verified research established 3-0 "
        "that the dorsal stream is EARLY and parallel (marmoset layer-4 CB+ "
        "dense in V1 AND MT/MST/FST at E130, prenatal; PV peaks PD14 dorsal vs "
        "PD28 ventral; a retina->inferior-pulvinar->MT route BYPASSES V1) — not "
        "a rung stacked on top of V1. It also keeps vision_waves.json byte-"
        "untouched, so every committed rung-1/rung-2 result reproduces."),
    "match_type": "DUnit",
    "match": [["r", "has_dunit", "u"]],
    "where": {"type": "And", "items": [
        DORSAL_ON,
        {"type": "Lt", "a": A(V("u"), "dact_step"), "b": STEP},
    ]},
    "effects": [
        ["set_attr", "u", "dact", T({
            "type": "Fold",
            "source": {"type": "InNeighbours", "node": V("u"), "edge_type": "dpost",
                       "any_type": False},
            "var_name": "sy", "acc_name": "acc", "init": L(0.0),
            "body": {"type": "Plus", "items": [
                V("acc"),
                {"type": "Times", "items": [
                    A(V("sy"), "weight"),
                    delay_match(SY_PRE, V("sy")),
                ]},
            ]},
        })],
        ["set_attr", "u", "dact_step", T(STEP)],
    ],
}

dv_burst_winner = {
    "name": "dv_burst_winner",
    "comment": (
        "WINNER-TAKE-ALL among the DUnits, by the same Argmax idiom "
        "wv_unit_burst_winner uses (Eq compares Value::Node by id, so exactly "
        "one unit survives per pass). Competition is what makes the dorsal "
        "population DIFFERENTIATE — without it every DUnit chases the same "
        "leading component and the population learns one direction. Scoped to "
        "the retina's has_dunit neighbours, so it never races the ventral "
        "population's has_unit Argmax: the two streams compete only within "
        "themselves, which is what `parallel` means."),
    "match_type": "DUnit",
    "match": [["r", "has_dunit", "u"]],
    "where": {"type": "And", "items": [
        DORSAL_ON,
        {"type": "Lt", "a": A(V("u"), "burst_step"), "b": STEP},
        {"type": "Eq", "a": A(V("u"), "dact_step"), "b": STEP},
        {"type": "Gt", "a": A(V("u"), "dact"), "b": L(0.0)},
        {"type": "Eq", "a": V("u"), "b": {
            "type": "Argmax",
            "source": {"type": "Neighbours", "node": V("r"), "edge_type": "has_dunit",
                       "any_type": False},
            "var_name": "u2", "value": A(V("u2"), "dact"), "default": None}},
    ]},
    "effects": [
        ["set_attr", "u", "bursting", 1.0],
        ["set_attr", "u", "burst_step", T(STEP)],
        ["set_attr", "u", "last_burst", T(STEP)],
    ],
}

dv_oja_learn = {
    "name": "dv_oja_learn",
    "comment": (
        "OJA'S RULE on the dorsal population: w <- w*(1 - eta*y^2) + eta*y*x, "
        "with y = the DUnit's own delay-line drive (dact) and x = 1 iff this "
        "synapse's pre-burst ARRIVED this step (the same delay window "
        "dv_unit_activate reads). Oja because the convergence measurement "
        "(VISION_RUNG2_PREREG.md) established it is the only rule in this tree "
        "with a stable non-zero fixed point on its own input distribution — "
        "fixed-sign Butts never converges and decays through the random floor, "
        "BCM converges to annihilation — and nine experience attempts failed "
        "purely because they were measured on a transient. A rung-3 arm "
        "comparison is meaningless on a scaffold that is not a STATE, so the "
        "convergence check is run before any arm. eta=5e-4 is the MEASURED "
        "stable regime (eta=2e-3 diverges to NaN: Oja is stable only while "
        "eta*y^2 < 1). Purely local: the rule reads only the synapse, its own "
        "pre cell and its own post unit. Winner-take-all is retained "
        "(u.bursting==1) so the population differentiates. WHAT MAKES THIS "
        "LEARN DIRECTION: x is now delay-gated, so the correlation Oja "
        "accumulates is between the unit's drive and ARRIVAL, not between the "
        "drive and mere presence-in-a-box. The leading principal component of a "
        "delay-line input under consistently-moving stimuli IS a direction; "
        "under direction-isotropic input it is not. That is the whole "
        "differential prediction, and it is the rule that has to deliver it."),
    "match_type": "DSynapse",
    "match": [["c", "dpre", "s"], ["s", "dpost", "u"], ["r", "has_cell", "c"]],
    "where": {"type": "And", "items": [
        DORSAL_ON,
        {"type": "Lt", "a": A(V("s"), "touched"), "b": STEP},
        {"type": "Eq", "a": A(V("u"), "dact_step"), "b": STEP},
        {"type": "Eq", "a": A(V("u"), "bursting"), "b": L(1.0)},
    ]},
    "effects": [
        ["set_attr", "s", "weight", T({"type": "Plus", "items": [
            {"type": "Times", "items": [
                A(V("s"), "weight"),
                {"type": "Minus", "a": L(1.0), "b": {"type": "Times", "items": [
                    DP("oja_eta"), A(V("u"), "dact"), A(V("u"), "dact")]}},
            ]},
            {"type": "Times", "items": [
                DP("oja_eta"), A(V("u"), "dact"),
                delay_match(V("c"), V("s")),
            ]},
        ]})],
        ["set_attr", "s", "touched", T(STEP)],
    ],
}

PARAMS_COMMENT = (
    "RUNG 3 knobs as GRAPH DATA. dorsal: 0.0 = OFF (the DEFAULT — every rule in "
    "this seed is gated on it, so a booted agent that does not ask for the "
    "dorsal stream runs byte-identically to the committed rung-1/rung-2 "
    "substrate, and every committed result reproduces). 1.0 = the dorsal/motion "
    "population runs. delay_tol: the width of a DSynapse's ARRIVAL WINDOW "
    "[delay, delay+delay_tol]; 0.0 = exact coincidence. This is the dorsal "
    "counterpart of WaveParams.window_steps, and the reason it must be a "
    "SEPARATE knob is the whole point of the rung: the ventral window is "
    "SHARED across a unit's synapses (order-blind by construction), while the "
    "dorsal window is PER-SYNAPSE and offset by that synapse's own conduction "
    "delay (order-sensitive by construction). oja_eta: Oja's learning rate; "
    "5e-4 is the MEASURED stable regime from the convergence work (2e-3 "
    "diverges to NaN — Oja is stable only while eta*y^2 < 1), NOT a tuned "
    "optimum. WHY OJA AND NOT THE BUTTS BURST RULE: the convergence measurement "
    "established that fixed-sign Butts has no fixed point at all (drift "
    "0.49-0.75, decays THROUGH the random floor) and BCM converges to zero "
    "structure — nine pre-registered experience attempts failed because they "
    "compared arms on a transient. Oja's decay term is a contraction toward the "
    "input's leading principal component: a stable, non-zero fixed point by "
    "construction. WHAT THIS SEED DELIBERATELY DOES NOT CONTAIN: any direction "
    "gradient, any preferred direction, any motion-energy filter, any "
    "hand-built delay structure. The delays are uniform random entropy from the "
    "adapter; every direction is symmetric a priori. If direction selectivity "
    "appears it was grown by dv_oja_learn from the input's motion statistics, "
    "and if it does not appear that is the result."
)

seed = {
    "id": "vision_dorsal",
    "version": "1.0.0",
    "depends_on": ["vision_waves"],
    "description": (
        "RUNG 3 — THE DORSAL/MOTION STREAM: DIRECTION SELECTIVITY. A population "
        "of DUnits reads the SAME retina as rung 1's ventral Units, in PARALLEL "
        "(the verified 105-agent research established 3-0 that the dorsal stream "
        "is EARLY and parallel — V1 and MT co-earliest, marmoset layer-4 CB+ "
        "dense in both at E130 prenatal, a retina->inferior-pulvinar->MT route "
        "BYPASSING V1, and neonatal MT ablation permanently degrading "
        "reach-to-grasp for MOVING targets, Atapour & Bourne 2021 — NOT a rung "
        "stacked above V1). The mechanism is a DELAY-LINE COINCIDENCE DETECTOR: "
        "each DSynapse carries its own conduction delay and contributes only "
        "when its pre cell fired exactly that many steps ago, so inputs that "
        "were SEQUENTIAL at the retina arrive SIMULTANEOUSLY at the unit iff the "
        "sequence matches the delay gradient. The ventral rule cannot do this: "
        "its window is SHARED across a unit's synapses, so a->b and b->a deliver "
        "the identical in-window burst set and no weight assignment can prefer "
        "one. THE DIFFERENTIAL PREDICTION THIS SEED EXISTS TO TEST: the research "
        "explicitly warns 'do NOT generalise from orientation to DIRECTION "
        "selectivity — direction is absent at eye opening and DOES require "
        "experience (Li 2006) — the opposite case'. Orientation (rung 1/2) "
        "emerges from waves alone and is refined by experience; direction should "
        "be ~ABSENT after waves alone and should REQUIRE moving visual "
        "experience. The delays are UNIFORM RANDOM entropy from the adapter, "
        "never a tuned gradient, so any direction preference is grown by "
        "dv_oja_learn, not planted. Gated OFF by DorsalParams.dorsal=0."),
    "microtheory": {
        "name": "vision_dorsal",
        "description": (
            "direction selectivity as a delay-line coincidence detector learned "
            "by Oja's rule: random per-synapse conduction delays + winner-take-all "
            "competition; the leading principal component of a delay-line input "
            "under consistently-moving stimuli IS a direction, and under "
            "direction-isotropic input it is not. Parallel to, not downstream of, "
            "the ventral wave scaffold."),
    },
    "nodes": [{
        "local_id": 0,
        "type": "DorsalParams",
        "attrs": {
            "name": "default",
            "dorsal": 0.0,
            "delay_tol": 0.0,
            "oja_eta": 0.0005,
            "comment": PARAMS_COMMENT,
        },
    }],
    "edges": [],
    "productions": [
        {"src": {"type": "RetinaCell", "var": "a"}, "edge_type": "dpre",
         "tgt": {"type": "DSynapse", "var": "b"},
         "provenance": "seed:vision_dorsal:dpre"},
        {"src": {"type": "DSynapse", "var": "a"}, "edge_type": "dpost",
         "tgt": {"type": "DUnit", "var": "b"},
         "provenance": "seed:vision_dorsal:dpost"},
        {"src": {"type": "Retina", "var": "a"}, "edge_type": "has_dunit",
         "tgt": {"type": "DUnit", "var": "b"},
         "provenance": "seed:vision_dorsal:has_dunit"},
    ],
    "rules": [dv_transient, dv_unit_activate, dv_burst_winner, dv_oja_learn],
}

out = os.path.join(ROOT, "seeds", "vision_dorsal.json")
with open(out, "w") as f:
    json.dump(seed, f, indent=1)
    f.write("\n")
print("wrote", out, len(json.dumps(seed)), "bytes")
