"""Generator for seeds/self_id_stability.json — measure the discriminator's self-id stability from LIVE
perception and bank it onto a repairable axis, so the autonomous self-repair loop fires on a REAL regression
(not an injected demo measure). The jabberwock's design (extension b), realised.

Three graph-resident rules:
  · mark_self        — latch is_self=1 on a region the moment it is classified controllable, so the measure
                       follows the SELF even after a broken discriminator lets it flip to autonomous.
  · measure_self_id  — per frame, track the window's own prev_action (classify overwrites the region's
                       classified_under every frame, so "committed" must use the WINDOW's prev, not the
                       region's); on a committed self frame, fold committed_n += 1 and held_n += (axis_kind
                       == controllable). Folded => once per frame.
  · window_close     — at W committed frames, bank stability = held_n/committed_n onto the axis (target 1.0,
                       a healthy discriminator holds EVERY committed frame), bump epoch, reset. post_repair
                       is set iff a fault is already open (the gate's re-measure); otherwise it is a normal
                       measure that lets fault_detect_regression fire on its own.

Run: python3 scripts/gen_self_id_stability_seed.py
"""
from __future__ import annotations

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W = 6.0


def V(n): return {"type": "Var", "name": n}
def Lit(v): return {"type": "Lit", "value": v}
def Attr(node, k): return {"type": "Attr", "node": node, "key": k}
def P0(var, k): return {"type": "Plus", "items": [Attr(V(var), k), Lit(0.0)]}
def And(items): return {"type": "And", "items": items}
def Eq(a, b): return {"type": "Eq", "a": a, "b": b}
def Lt(a, b): return {"type": "Lt", "a": a, "b": b}
def Gt(a, b): return {"type": "Gt", "a": a, "b": b}
def Plus(items): return {"type": "Plus", "items": items}
def Div(a, b): return {"type": "Div", "a": a, "b": b}
def Ite(c, t, o): return {"type": "IfThenElse", "cond": c, "then": t, "other": o}


def mark_self():
    return {
        "name": "mark_self",
        "comment": "Latch is_self=1 the first time a region is classified controllable, so the stability "
                   "measure keeps following the SELF even after a broken discriminator flips it to autonomous.",
        "match": [["g", "has_region", "r"]],
        "where": And([Eq(Attr(V("r"), "axis_kind"), Lit("controllable")), Lt(P0("r", "is_self"), Lit(0.5))]),
        "effects": [["set_attr", "r", "is_self", 1.0]],
    }


def measure_self_id():
    is_ctrl = Eq(Attr(V("r"), "axis_kind"), Lit("controllable"))
    committed = Eq(Attr(V("g"), "last_action"), Attr(V("w"), "prev_action"))
    active = And([committed, Lt(P0("w", "committed_n"), Lit(W))])     # count up to W, then window_close handles it
    return {
        "name": "measure_self_id_hold",
        "comment": "Per frame, for the self region + the window: always track the window's own prev_action "
                   "(classify overwrites the region's classified_under every frame, so committed must use the "
                   "WINDOW's prev). On a committed self frame (under the cap) fold committed_n+=1 and "
                   "held_n+=(axis_kind==controllable). Folded so it counts once per frame, not per fixpoint pass.",
        "match": [["g", "has_region", "r"], ["g", "has_window", "w"]],
        "where": Gt(P0("r", "is_self"), Lit(0.5)),
        "effects": [
            ["set_attr", "w", "clocked", 1.0],
            ["set_attr", "w", "next_prev_action", {"__term__": Attr(V("g"), "last_action")}],
            ["set_attr", "w", "next_committed_n",
                {"__term__": Ite(active, Plus([P0("w", "committed_n"), Lit(1.0)]), P0("w", "committed_n"))}],
            ["set_attr", "w", "next_held_n",
                {"__term__": Ite(active, Plus([P0("w", "held_n"), Ite(is_ctrl, Lit(1.0), Lit(0.0))]),
                             P0("w", "held_n"))}],
        ],
    }


def window_close():
    return {
        "name": "window_close_self_id",
        "comment": "At W committed frames, bank stability = held_n/committed_n onto the repairable axis "
                   "(target 1.0); post_repair iff a fault is already open (the gate's re-measure). Bump epoch "
                   "and reset the counters IMMEDIATELY (single-fire; the folded increment paused at the cap).",
        "match": [["g", "has_window", "w"], ["w", "for_axis", "ax"]],
        "where": Gt(P0("w", "committed_n"), Lit(W - 0.5)),
        "effects": [
            ["add_node", "mc", "MeasuredCapability", {
                "measured": {"__term__": Div(P0("w", "held_n"), P0("w", "committed_n"))},
                "target": 1.0, "metric": "self_id_stability",
                "post_repair": {"__term__": Ite(Gt(P0("ax", "fault_open"), Lit(0.5)), Lit(1.0), Lit(0.0))},
                "measure_epoch": {"__term__": Plus([P0("w", "epoch"), Lit(1.0)])}}],
            ["add_edge", "mc", "measures_axis", "ax"],
            ["set_attr", "w", "committed_n", 0.0],
            ["set_attr", "w", "held_n", 0.0],
            ["set_attr", "w", "epoch", {"__term__": Plus([P0("w", "epoch"), Lit(1.0)])}],
        ],
    }


def main():
    seed = {
        "id": "self_id_stability",
        "version": "1.0.0",
        "area": "self_monitoring",
        "latency_class": "hard_realtime",
        "depends_on": ["self_repair"],
        "description": "Measure the self/world discriminator's self-id stability from live perception and bank "
                       "it onto a repairable axis, so fault_detect_regression fires on a REAL regression. "
                       "Generated by scripts/gen_self_id_stability_seed.py.",
        "microtheory": {"name": "self_id_stability",
                        "description": "self-id holds under committed action -> high stability; a flip -> low -> autonomous repair"},
        "nodes": [], "edges": [],
        "productions": [
            {"provenance": "seed:self_id_stability:has_window",
             "src": {"type": "WorldInstance", "var": "x"}, "edge_type": "has_window",
             "tgt": {"type": "SelfIdWindow", "var": "y"}, "where": None, "weight": {"type": "Lit", "value": 1.0}},
            {"provenance": "seed:self_id_stability:for_axis",
             "src": {"type": "SelfIdWindow", "var": "x"}, "edge_type": "for_axis",
             "tgt": {"type": "CapabilityAxis", "var": "y"}, "where": None, "weight": {"type": "Lit", "value": 1.0}},
        ],
        "rules": [mark_self(), measure_self_id(), window_close()],
    }
    out = os.path.join(ROOT, "seeds", "self_id_stability.json")
    tmp = out + ".tmp"
    with open(tmp, "w") as fh:
        json.dump(seed, fh, indent=1)
    json.load(open(tmp))
    os.replace(tmp, out)
    print(f"wrote + validated {os.path.relpath(out, ROOT)} ({len(seed['rules'])} rules, {len(seed['productions'])} productions)")


if __name__ == "__main__":
    main()
