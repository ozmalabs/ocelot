"""jabberwock_grounding_reach — the GATE for domains/grounding_reach.py.

Builds a small hand-constructed graph exercising every scenario the
grounding-reachability substrate has to get right, then prints the anchors
reached per node and the discriminative flag_ungrounded_confident results —
especially the RECONSTRUCTED residual-salience failure mode (see
seeds/residual_salience.json's description: a SATURATED axis flat-tied
salience to zero and got re-picked 24x; that was exactly a confident, low-
residual collapse with no live grounding — this substrate is what would have
caught it).

No CuriousAgent, no seed boot needed — a bare `substrate_rs.Substrate()`
IS a valid `agent` argument to every domains.grounding_reach function (its
`_resolve` duck-types `getattr(agent, "s", agent)` then falls back to
`agent._inner`, which a raw native Substrate already carries).

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_grounding_reach.py
"""
from __future__ import annotations
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

import substrate_rs as srs
from domains import grounding_reach as gr


def _mk(s):
    """Build the gate graph. Returns a dict of the interesting NodeIDs."""
    N = {}

    # --- Agent root + a real vision-cortex-shaped percept (world_adapter.
    #     update_vision's own perceives edge). ---
    N["agent"] = s.add_node("Agent", {})
    N["percept"] = s.add_node("VisionPercept", {})
    s.add_edge_unchecked(N["agent"], "perceives", N["percept"])

    # (a) a node grounded via a CHAIN to a SensorAnchor (hops > 0): a
    #     downstream collapse `perception_result` grounded in the percept,
    #     not directly in the anchor — ensure_grounding_edges grounds the
    #     PERCEPT to SensorAnchor; the chain to it must show hops == 2.
    N["perception_result"] = s.add_node("Collapse", {"label": "a_chained"})
    s.add_edge_unchecked(N["perception_result"], "grounded_in", N["percept"])

    # (b) a self-referential loop with NO anchor anywhere in it.
    N["loop_a"] = s.add_node("Collapse", {"label": "b_loop_a"})
    N["loop_b"] = s.add_node("Collapse", {"label": "b_loop_b"})
    s.add_edge_unchecked(N["loop_a"], "grounded_in", N["loop_b"])
    s.add_edge_unchecked(N["loop_b"], "grounded_in", N["loop_a"])

    # (c) confident + low-residual + NO grounding at all -> must be flagged.
    N["confident_ungrounded"] = s.add_node("Collapse", {
        "label": "c_confident_ungrounded", "residual": 0.01, "confidence": 0.97})

    # (d) confident + low-residual + WITH a real anchor -> must NOT be
    #     flagged (discriminative: grounding, not confidence, is what saves it).
    N["confident_grounded"] = s.add_node("Collapse", {
        "label": "d_confident_grounded", "residual": 0.01, "confidence": 0.97})
    s.add_edge_unchecked(N["confident_grounded"], "grounded_in", N["percept"])

    # (e) RECONSTRUCT the residual-salience failure mode:
    #   a SATURATED axis (residual ~ 0) with NO live grounding -> flagged.
    N["axis_saturated_ungrounded"] = s.add_node("CapabilityAxis", {
        "label": "e_saturated_axis_no_grounding",
        "residual": 0.0, "confidence": 0.99, "saturation": 1.0})
    #   a genuinely-solved axis grounded in a REAL judged Experiment outcome
    #   (a ConsequenceAnchor source) -> NOT flagged.
    N["run"] = s.add_node("Run", {"status": "done", "score": 12.0, "frames": 12.0})
    N["experiment"] = s.add_node("Experiment", {
        "status": "requested", "outcome": "supported"})
    s.add_edge_unchecked(N["experiment"], "produced", N["run"])
    N["axis_saturated_grounded"] = s.add_node("CapabilityAxis", {
        "label": "e_saturated_axis_grounded",
        "residual": 0.0, "confidence": 0.99, "saturation": 1.0})
    s.add_edge_unchecked(N["axis_saturated_grounded"], "grounded_in", N["experiment"])

    return N


def main() -> int:
    print("=" * 92)
    print("GROUNDING-REACHABILITY gate — domains/grounding_reach.py")
    print("=" * 92)
    s = srs.Substrate()
    N = _mk(s)

    rep = gr.ensure_grounding_edges(s)
    print(f"\n  ensure_grounding_edges (pass 1): {rep}")
    ok_mint = rep["sensor"] >= 1 and rep["consequence"] >= 1 and rep["total"] >= 2
    print(f"    sensor>=1 and consequence>=1: {'PASS' if ok_mint else 'FAIL'}")

    rep2 = gr.ensure_grounding_edges(s)
    print(f"  ensure_grounding_edges (pass 2, re-run): {rep2}")
    ok_idem = rep2["total"] == 0
    print(f"    idempotent (0 new edges on re-run): {'PASS' if ok_idem else 'FAIL'}")

    print("\n  --- grounding_reach per scenario node (anchors reached) ---")

    def show(label, nid):
        r = gr.grounding_reach(s, nid)
        print(f"    {label:32s} reached={r['reached']!s:5s} "
              f"anchors={r['anchors']}  hops={r['hops']}")
        return r

    r_a = show("(a) chained -> SensorAnchor", N["perception_result"])
    r_b = show("(b) self-loop, no anchor", N["loop_a"])
    r_c = show("(c) confident, ungrounded", N["confident_ungrounded"])
    r_d = show("(d) confident, grounded", N["confident_grounded"])
    r_e1 = show("(e) saturated, ungrounded", N["axis_saturated_ungrounded"])
    r_e2 = show("(e) saturated, grounded (Consequence)", N["axis_saturated_grounded"])

    ok_a = r_a["reached"] and r_a["anchors"] == ["SensorAnchor"] and (r_a["hops"] or 0) > 0
    ok_b = (not r_b["reached"]) and r_b["anchors"] == [] and r_b["hops"] is None
    ok_e1_reach = not r_e1["reached"]
    ok_e2_reach = r_e2["reached"] and r_e2["anchors"] == ["ConsequenceAnchor"]

    print(f"\n  (a) reaches SensorAnchor, hops>0     : {'PASS' if ok_a else 'FAIL'}")
    print(f"  (b) self-loop does NOT reach an anchor: {'PASS' if ok_b else 'FAIL'}")
    print(f"  (e) saturated+ungrounded NOT reached  : {'PASS' if ok_e1_reach else 'FAIL'}")
    print(f"  (e) saturated+grounded REACHES Consequence: {'PASS' if ok_e2_reach else 'FAIL'}")

    # --- cross-check grounding_reach against a DIRECT native evaluate() call
    #     of the same installed ReachableFrom Term — proves grounding_reach
    #     is a thin caller of the real primitive, not a Python re-walk.
    term = {"type": "ReachableFrom", "node": {"type": "Var", "name": "n"},
            "edge_type": "grounded_in"}
    direct = set(s._inner.evaluate(term, {"n": N["perception_result"]}))
    direct_types = {s.node(x)["type"] for x in direct if s.has_node(x)}
    ok_native = ("SensorAnchor" in direct_types) and (direct_types & set(gr.ANCHOR_KINDS)
                                                        == set(r_a["anchors"]))
    print(f"\n  grounding_reach agrees with a DIRECT native evaluate(ReachableFrom) call: "
          f"{'PASS' if ok_native else 'FAIL'}  (direct types reached: {sorted(direct_types)})")

    print("\n  --- flag_ungrounded_confident (discriminative) ---")
    flagged = gr.flag_ungrounded_confident(
        s, node_types=["Collapse", "CapabilityAxis"],
        residual_max=0.05, conf_min=0.9)
    flagged_labels = sorted(s.node(n)["attrs"].get("label", "?") for n in flagged)
    print(f"    flagged: {flagged_labels}")

    ok_c_flagged = N["confident_ungrounded"] in flagged
    ok_d_not_flagged = N["confident_grounded"] not in flagged
    ok_e1_flagged = N["axis_saturated_ungrounded"] in flagged
    ok_e2_not_flagged = N["axis_saturated_grounded"] not in flagged

    print(f"    (c) confident+ungrounded IS flagged        : "
          f"{'PASS' if ok_c_flagged else 'FAIL'}")
    print(f"    (d) confident+grounded is NOT flagged      : "
          f"{'PASS' if ok_d_not_flagged else 'FAIL'}")
    print(f"    (e) saturated+ungrounded IS flagged        : "
          f"{'PASS' if ok_e1_flagged else 'FAIL'}")
    print(f"    (e) saturated+grounded(Consequence) NOT flagged: "
          f"{'PASS' if ok_e2_not_flagged else 'FAIL'}")

    gaps = list(s.nodes("GroundingGap"))
    ok_gap_shape = len(gaps) == len(flagged) and all(
        s.node(g)["attrs"].get("why") == "confident but ungrounded" for g in gaps)
    print(f"    GroundingGap nodes minted ({len(gaps)}) match flagged count & shape: "
          f"{'PASS' if ok_gap_shape else 'FAIL'}")

    # idempotent re-run of the flag pass shouldn't duplicate GroundingGap nodes.
    flagged2 = gr.flag_ungrounded_confident(
        s, node_types=["Collapse", "CapabilityAxis"],
        residual_max=0.05, conf_min=0.9)
    ok_flag_idem = len(list(s.nodes("GroundingGap"))) == len(gaps) and set(flagged2) == set(flagged)
    print(f"    flag pass is idempotent (no duplicate GroundingGap): "
          f"{'PASS' if ok_flag_idem else 'FAIL'}")

    all_ok = all([ok_mint, ok_idem, ok_a, ok_b, ok_e1_reach, ok_e2_reach, ok_native,
                  ok_c_flagged, ok_d_not_flagged, ok_e1_flagged, ok_e2_not_flagged,
                  ok_gap_shape, ok_flag_idem])
    print("\n" + "=" * 92)
    print(f"  {'PASS' if all_ok else 'FAIL'} — grounding-reachability substrate: "
          f"groundedness is a queryable graph property via the real installed "
          f"ReachableFrom Term; residual+confidence alone is NOT enough to clear a "
          f"node, grounding is.")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
