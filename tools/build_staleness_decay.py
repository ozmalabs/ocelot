#!/usr/bin/env python3
"""EMIT seeds/staleness_decay.json (block 196000).

A seed BUILDER — it only assembles graph data (Rule/production JSON), no agent
decision, no runtime. The shared integer-half-life DECAY PRIMITIVE:
  freshness = Ashr(C0, IDiv(now_epoch - last_refresh_epoch, half_life))
of which the held surface is the FIRST consumer and a synthetic DecayTrace is a
SECOND consumer with byte-structurally-identical freshness machinery.

Terms used are ALL pre-existing (term.rs untouched): Abs, Minus, Plus, Times,
Div, IDiv, Ashr, Max, IfThenElse, Lt, Gt, Eq, And, Attr, Lit, Var.
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "seeds", "staleness_decay.json")


def A(var, key):
    return {"type": "Attr", "node": {"type": "Var", "name": var}, "key": key}


def L(v):
    return {"type": "Lit", "value": float(v)}


def T(t):
    return {"__term__": t}


# ------- shared guard (held-surface cells): enabled + fresh-guard -------
GUARD = {
    "type": "And",
    "items": [
        {"type": "Eq", "a": A("dparams", "enabled"), "b": L(1.0)},
        {"type": "Gt", "a": A("column", "input_epoch"), "b": A("hs", "epoch")},
        {"type": "Eq", "a": A("rod", "input_epoch"), "b": A("column", "input_epoch")},
    ],
}
MATCH = [
    ["retina", "has_held_decay_params", "dparams"],
    ["retina", "has_column", "column"],
    ["column", "rod_receptor", "rod"],
    ["column", "has_held_surface_cell", "hs"],
]


def rule(name, order, effects):
    return {"name": name, "area": "retina", "order": order,
            "latency_class": "hard_realtime", "match": MATCH,
            "where": GUARD, "effects": effects}


# --- sd_residual (order 0): the order-0 INTEGER surprise against the held
#     PREDICTION. Both operands are floored to i64 via IDiv(_, 1) so the surprise
#     is integer-native (decay bookkeeping) AND stays elevated until the held
#     value ADOPTS the observation (sustained innovation -> fast refresh, not a
#     one-tick transient). caught_quanta carries a fractional dark-current
#     offset; flooring both sides keeps the residual an exact integer. ---
FLOOR_CAUGHT = {"type": "IDiv", "a": A("rod", "caught_quanta"), "b": L(1.0)}
FLOOR_VALUE = {"type": "IDiv", "a": A("hs", "value"), "b": L(1.0)}
residual = rule("sd_residual", 0, [[
    "set_attr", "hs", "residual",
    T({"type": "Abs", "arg": {"type": "Minus",
       "a": FLOOR_CAUGHT, "b": FLOOR_VALUE}})]])

# --- sd_gate (order 1): surprise sets half_life inversely; gates the refresh
#     (innovation) clock. The FALSIFIER lives here as a graph PARAMETER
#     (dparams.uniform): when uniform==1 the surprise->half_life coupling is
#     ablated (half_life := uniform_hl, a FIXED decay) AND the clock is frozen at
#     its init (last_refresh_epoch untouched, so Delta = now - 0 grows) -> a pure
#     surprise-INDEPENDENT fixed exponential decay. The rule READS the param and
#     decides -- graph-native, no Python. ---
graded_hl = {"type": "Max", "items": [
    A("dparams", "hl_min"),
    {"type": "IDiv", "a": A("dparams", "hl_scale"),
     "b": {"type": "Plus", "items": [A("hs", "residual"), L(1.0)]}}]}
IS_UNIFORM = {"type": "Eq", "a": A("dparams", "uniform"), "b": L(1.0)}
half_life_term = {"type": "IfThenElse", "cond": IS_UNIFORM,
                  "then": A("dparams", "uniform_hl"), "other": graded_hl}
# surprise-gated clock: reset to now when CONFIRMED (residual < thresh); under
# uniform ablation, leave the clock at its init so decay is surprise-independent.
surprise_refresh = {"type": "IfThenElse",
                    "cond": {"type": "Lt", "a": A("hs", "residual"),
                             "b": A("dparams", "refresh_thresh")},
                    "then": A("column", "input_epoch"),
                    "other": A("hs", "last_refresh_epoch")}
refresh_term = {"type": "IfThenElse", "cond": IS_UNIFORM,
                "then": A("hs", "last_refresh_epoch"), "other": surprise_refresh}
gate = rule("sd_gate", 1, [
    ["set_attr", "hs", "half_life", T(half_life_term)],
    ["set_attr", "hs", "last_refresh_epoch", T(refresh_term)],
])

# --- sd_freshness (order 2): THE DECAY LAW (integer-exact ×2^-k) ---
FRESH_COMPUTED = {"type": "Ashr", "a": A("dparams", "c0"),
                  "b": {"type": "IDiv",
                        "a": {"type": "Minus", "a": A("column", "input_epoch"),
                              "b": A("hs", "last_refresh_epoch")},
                        "b": A("hs", "half_life")}}
# FIRST-CLASSNESS ablation as a graph param: pin_freshness==1 forces freshness to
# c0 (never stale) so the downstream consumer (sd_blend) can be shown to KEY OFF
# the exposed freshness attribute (gain collapses to lr_min -> smear).
FRESH = {"type": "IfThenElse",
         "cond": {"type": "Eq", "a": A("dparams", "pin_freshness"), "b": L(1.0)},
         "then": A("dparams", "c0"), "other": FRESH_COMPUTED}
freshness = rule("sd_freshness", 2, [["set_attr", "hs", "freshness", T(FRESH)]])

# --- sd_blend (order 3): precision-weighted Kalman update (FIRST consumer) ---
staleness = {"type": "Minus", "a": A("dparams", "c0"), "b": A("hs", "freshness")}
gain = {"type": "Plus", "items": [
    A("dparams", "lr_min"),
    {"type": "Times", "items": [
        {"type": "Minus", "a": L(1.0), "b": A("dparams", "lr_min")},
        {"type": "Div", "a": staleness, "b": A("dparams", "c0")}]}]}
value_term = {"type": "Plus", "items": [
    A("hs", "value"),
    {"type": "Times", "items": [
        gain, {"type": "Minus", "a": A("rod", "caught_quanta"),
               "b": A("hs", "value")}]}]}
blend = rule("sd_blend", 4, [
    ["set_attr", "hs", "value", T(value_term)],
    ["set_attr", "hs", "obs", T(A("rod", "caught_quanta"))],
    ["set_attr", "hs", "epoch", T(A("column", "input_epoch"))],
])

# --- sd_flag_stale (order 3): SECOND consumer (foveation keys off freshness).
#     A pure READER of the exposed freshness attribute, so it is guarded ONLY on
#     `enabled` (NOT the epoch fresh-guard the WRITERS share) — it recomputes the
#     flag idempotently from the current freshness, and therefore does not race
#     the epoch-advancing blend rule. ---
flag = {
    "name": "sd_flag_stale", "area": "retina", "order": 3,
    "latency_class": "hard_realtime",
    "match": [["retina", "has_held_decay_params", "dparams"],
              ["retina", "has_column", "column"],
              ["column", "has_held_surface_cell", "hs"]],
    "where": {"type": "Eq", "a": A("dparams", "enabled"), "b": L(1.0)},
    "effects": [[
        "set_attr", "hs", "needs_attention",
        T({"type": "IfThenElse",
           "cond": {"type": "Lt", "a": A("hs", "freshness"),
                    "b": A("dparams", "attn_thresh")},
           "then": L(1.0), "other": L(0.0)})]],
}

# --- sd_freshness_generic (order 2): GENERICITY — the SAME machinery, a
#     SECOND decaying quantity (DecayTrace). The freshness op tree is
#     STRUCTURALLY IDENTICAL to sd_freshness (only node/edge/key names differ). ---
FRESH_GENERIC = {"type": "Ashr", "a": A("dparams", "c0"),
                 "b": {"type": "IDiv",
                       "a": {"type": "Minus", "a": A("dt", "now_epoch"),
                             "b": A("dt", "last_refresh_epoch")},
                       "b": A("dt", "half_life")}}
freshness_generic = {
    "name": "sd_freshness_generic", "area": "retina", "order": 2,
    "latency_class": "hard_realtime",
    "match": [["retina", "has_held_decay_params", "dparams"],
              ["retina", "has_decay_trace", "dt"]],
    "where": {"type": "Eq", "a": A("dparams", "enabled"), "b": L(1.0)},
    "effects": [["set_attr", "dt", "freshness", T(FRESH_GENERIC)]],
}

seed = {
    "id": "staleness_decay",
    "version": "1.0.0",
    "self_load_only": True,
    "depends_on": [],
    "area": "retina",
    "description": (
        "SHARED integer-half-life DECAY PRIMITIVE (block 196000). One "
        "representation for any decaying quantity: last_refresh_epoch (integer "
        "innovation clock) + half_life (integer epochs, set INVERSELY by "
        "surprise) + freshness = Ashr(C0, IDiv(now_epoch - last_refresh_epoch, "
        "half_life)) -- the integer-EXACT x2^-k (scale2) atom read on the "
        "per-sensor epoch axis. The held surface is the FIRST consumer: the "
        "order-0 residual against the held prediction (sd_residual, an INTEGER "
        "temporal surprise |caught - obs_prev|) sets half_life (sd_gate) and "
        "gates the innovation clock; freshness (sd_freshness) precision-weights "
        "a Kalman blend of held-vs-new (sd_blend) so a STATIC cell keeps a long "
        "half-life and denoises (density accrues) while a MOVING cell's "
        "freshness collapses and it ADOPTS the new content (refreshed, not "
        "smeared) -- density and latency DECOUPLE over ONE held belief. A "
        "second consumer (sd_flag_stale) foveates by reading the exposed "
        "freshness attribute. A synthetic DecayTrace (sd_freshness_generic) is "
        "decayed by byte-structurally-identical machinery -- proving the "
        "primitive is shared, not perception-local. OFF by default: the rules "
        "need a HeldDecayParams node the measure adapter creates only on opt-in; "
        "absent it every existing path is byte-identical (held_surface.json "
        "untouched). NO Rust, NO new Term (Ashr/IDiv/Abs/IfThenElse/Max exist)."),
    "microtheory": {
        "name": "staleness_decay",
        "description": ("Integer-half-life freshness (scale2 on the epoch axis) "
                        "as a shared decay primitive; decay proportional to "
                        "surprise decouples accumulation density from adopt "
                        "latency in the held surface."),
    },
    "nodes": [],
    "edges": [],
    "productions": [
        {"provenance": "seed:staleness_decay:retina-decay-params",
         "src": {"type": "Retina", "var": "retina"},
         "edge_type": "has_held_decay_params",
         "tgt": {"type": "HeldDecayParams", "var": "dparams"}},
        {"provenance": "seed:staleness_decay:retina-decay-trace",
         "src": {"type": "Retina", "var": "retina"},
         "edge_type": "has_decay_trace",
         "tgt": {"type": "DecayTrace", "var": "dt"}},
    ],
    "rules": [residual, gate, freshness, blend, flag, freshness_generic],
}

with open(OUT, "w") as fh:
    json.dump(seed, fh, indent=1)
    fh.write("\n")
print("wrote", OUT, "-", len(seed["rules"]), "rules")
