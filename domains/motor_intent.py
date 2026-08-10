"""motor_intent — generic motor-intent layer (NOT handwriting-specific).

Separates WHAT the actor was TRYING to do (MotorIntent / MotorPlan / goal_kind) from the
noisy EXECUTION outcome (ExecutionTrace in world coordinates). Intent carries ALL the signal,
but is only extractable AFTER systemic jitter/noise (per-stroke pose equipment error,
inter-stroke pen-lift displacement) has been REALIZED — then the inverse model reads the
actual MotorPlan. Recognition compares extracted intents, not canvas outcomes.

ARCHITECTURE (CLAUDE.md): MECHANICAL I/O ONLY.
  • `realize_execution_noise` — held `TransformDecode` per stroke (pose noise) + mechanical
    inter-stroke lift delta read-off; stamps graph datums for rules to mint `MotorNoise`.
  • `extract_motor_plan` — inverse model AFTER noise realization: undo lift, read plan segs.
  • `intent_match_term` / `intent_arrangement_term` — AbS render-compare on extracted plans.
  • `classify_abs_intent` / `classify_per_stroke_program` — held-Argmin verdict arms.
  • `classify_sctps_diag` — diagnostic only (holistic blob warp, demoted).
  • `fused_motor_verdict` — unified entry; SC+TPS not a primary arm.

Every classify/match/rank decision lives in seed Rules or held Term evaluation.
"""
from __future__ import annotations

import json
import re
from typing import Any, Optional

from domains.abs_read import _argmin_pairs_term
from domains.stroke_codebook import (
    DEFAULT_LEN_BINS,
    DEFAULT_SCALE_BINS,
    DEFAULT_SEGMENTS,
    DEFAULT_TURN_BINS,
    PROTOTYPE_LEN,
    _native,
    _quantize,
    _stroke_quantize_live,
    _sub,
)

DEFAULT_GRID = 8
DEFAULT_RENDER_N = PROTOTYPE_LEN


def _seg_only(signature: list) -> list:
    """Mechanical filter: keep invariant `seg` relations only (intent topology)."""
    return [r for r in signature if r and r[0] == "seg"]


def _pose_rels(signature: list) -> list:
    return [list(r) for r in signature if r and r[0] != "seg"]


def full_signature(native, points: list, *, segments: int = DEFAULT_SEGMENTS,
                   turn_bins: int = DEFAULT_TURN_BINS, len_bins: int = DEFAULT_LEN_BINS,
                   grid: int = DEFAULT_GRID, scale_bins: int = DEFAULT_SCALE_BINS) -> list:
    """Mechanical read-off: full observed signature (seg + pose) from canvas points."""
    q = _quantize(native, points, segments=segments, turn_bins=turn_bins, len_bins=len_bins,
                  grid=grid, scale_bins=scale_bins, invariant_only=False)
    sig = q.get("signature") or []
    return [list(r) if isinstance(r, tuple) else r for r in sig]


def invariant_seg(native, points: list, *, segments: int = DEFAULT_SEGMENTS,
                  turn_bins: int = DEFAULT_TURN_BINS, len_bins: int = DEFAULT_LEN_BINS,
                  grid: int = DEFAULT_GRID, scale_bins: int = DEFAULT_SCALE_BINS) -> list:
    """Read off a stroke's seg topology via held `StrokeQuantize(invariant_only=True)`."""
    q = _quantize(native, points, segments=segments, turn_bins=turn_bins, len_bins=len_bins,
                  grid=grid, scale_bins=scale_bins, invariant_only=True)
    return _seg_only(q.get("signature") or [])


def extract_plan_segments(native, strokes: list[list], **kw) -> list[list]:
    """Per-stroke invariant segs from plan-frame strokes — mechanical batch read."""
    return [invariant_seg(native, s, **kw) for s in strokes]


def _read_pose_transform(native, seg: list, full_sig: list) -> dict:
    """ONE held `TransformDecode` evaluate — realize per-stroke pose/equipment noise."""
    goal = [list(r) for r in seg] + _pose_rels(full_sig)
    return native.evaluate({
        "type": "TransformDecode",
        "goal": {"type": "Lit", "value": goal},
        "max_dims": 4,
    }, {}) or {}


def _inter_stroke_lift_deltas(strokes: list[list]) -> list[Optional[tuple[float, float]]]:
    """Mechanical read-off: canvas displacement at each pen lift (noise, not intent)."""
    if not strokes:
        return []
    out: list[Optional[tuple[float, float]]] = [None]
    for i in range(1, len(strokes)):
        prev_end = strokes[i - 1][-1]
        actual_start = strokes[i][0]
        out.append((float(actual_start[0]) - float(prev_end[0]),
                    float(actual_start[1]) - float(prev_end[1])))
    return out


def _undo_lift_noise(strokes: list[list]) -> list[list]:
    """Inverse model step: cancel realized inter-stroke lift → plan arrangement frame."""
    if not strokes:
        return []
    corrected = [[list(p) for p in strokes[0]]]
    for i in range(1, len(strokes)):
        prev_end = corrected[i - 1][-1]
        actual_start = strokes[i][0]
        lift_dx = float(actual_start[0]) - float(prev_end[0])
        lift_dy = float(actual_start[1]) - float(prev_end[1])
        corrected.append([[float(p[0]) - lift_dx, float(p[1]) - lift_dy] for p in strokes[i]])
    return corrected


def realize_execution_noise(native, strokes: list[list], **kw) -> dict[str, Any]:
    """Realize systemic jitter/noise BEFORE intent extraction.

    Per-stroke: `TransformDecode` against seg + observed pose (equipment/slant noise).
    Inter-stroke: lift delta at each pen-up (placement noise, not shape).
    Returns realized noise + plan-frame strokes ready for inverse-model seg read-off.
    """
    pose_noise = []
    lift_noise = _inter_stroke_lift_deltas(strokes)
    for stroke in strokes:
        full = full_signature(native, stroke, **kw)
        seg = invariant_seg(native, stroke, **kw)
        pose_noise.append(_read_pose_transform(native, seg, full))
    plan_strokes = _undo_lift_noise(strokes)
    return {
        "pose_noise": pose_noise,
        "lift_noise": lift_noise,
        "plan_strokes": plan_strokes,
        "noise_realized": True,
    }


def extract_motor_plan(native, strokes: list[list], **kw) -> dict[str, Any]:
    """Inverse model: realize noise first, then read the ACTUAL intent (plan segs)."""
    realized = realize_execution_noise(native, strokes, **kw)
    plan_segs = extract_plan_segments(native, realized["plan_strokes"], **kw)
    return {
        "plan_segments": plan_segs,
        "plan_strokes": realized["plan_strokes"],
        "pose_noise": realized["pose_noise"],
        "lift_noise": realized["lift_noise"],
        "noise_realized": True,
    }


def _render_intent_term(seg: list, *, n_points: int = DEFAULT_RENDER_N,
                        turn_bins: int = DEFAULT_TURN_BINS,
                        len_bins: int = DEFAULT_LEN_BINS,
                        grid: int = DEFAULT_GRID,
                        scale_bins: int = DEFAULT_SCALE_BINS) -> dict:
    """Synthesize INTENT at canonical pose — `apply_pose=False`."""
    return {
        "type": "StrokeRender",
        "signature": {"type": "Lit", "value": list(seg)},
        "n_points": n_points,
        "apply_pose": False,
        "turn_bins": turn_bins,
        "len_bins": len_bins,
        "grid": grid,
        "scale_bins": scale_bins,
        "field": "points",
    }


def _render_outcome_term(seg: list, pose_bins: tuple, *, bounds: list,
                          n_points: int = DEFAULT_RENDER_N,
                          turn_bins: int = DEFAULT_TURN_BINS,
                          len_bins: int = DEFAULT_LEN_BINS,
                          grid: int = DEFAULT_GRID,
                          scale_bins: int = DEFAULT_SCALE_BINS) -> dict:
    """Synthesize OUTCOME at observed canvas pose."""
    x_q, y_q, o_q, s_q = pose_bins
    sig = list(seg) + [["pose_x", x_q], ["pose_y", y_q], ["pose_o", o_q], ["pose_s", s_q]]
    return {
        "type": "StrokeRender",
        "signature": {"type": "Lit", "value": sig},
        "n_points": n_points,
        "apply_pose": True,
        "turn_bins": turn_bins,
        "len_bins": len_bins,
        "grid": grid,
        "scale_bins": scale_bins,
        "bounds": {"type": "Lit", "value": [float(v) for v in bounds]},
        "field": "points",
    }


def _dtw_term(a_term: dict, observed: list) -> dict:
    return {"type": "DtwTo", "a": a_term, "b": {"type": "Lit", "value": observed}}


def _mean_dtw_term(dtw_terms: list) -> Optional[dict]:
    if not dtw_terms:
        return None
    return {"type": "Div", "a": {"type": "Plus", "items": dtw_terms},
            "b": {"type": "Lit", "value": float(len(dtw_terms))}}


def _pose_bins_from_stroke(native, points: list, bounds: list, **kw) -> Optional[tuple]:
    """Mechanical read-off of full-signature pose quanta for outcome rendering."""
    q = _quantize(native, points, invariant_only=False, **kw)
    sig = q.get("signature") or []
    bins = {}
    for rel in sig:
        if not rel:
            continue
        pred = rel[0]
        if pred in ("pose_x", "pose_y", "pose_o", "pose_s") and len(rel) >= 2:
            bins[pred] = rel[1]
    if not all(k in bins for k in ("pose_x", "pose_y", "pose_o", "pose_s")):
        return None
    return (bins["pose_x"], bins["pose_y"], bins["pose_o"], bins["pose_s"])


def _stroke_bbox(strokes: list[list]) -> list:
    xs, ys = [], []
    for stroke in strokes:
        for p in stroke:
            xs.append(float(p[0]))
            ys.append(float(p[1]))
    if not xs:
        return [0.0, 0.0, 1.0, 1.0]
    return [min(xs), min(ys), max(xs), max(ys)]


def intent_match_term(query_plan_segs: list, candidate_segs: list, *, native,
                      n_points: int = DEFAULT_RENDER_N,
                      turn_bins: int = DEFAULT_TURN_BINS,
                      len_bins: int = DEFAULT_LEN_BINS,
                      grid: int = DEFAULT_GRID,
                      scale_bins: int = DEFAULT_SCALE_BINS) -> Optional[dict]:
    """ONE held Term: mean per-stroke DtwTo between TWO EXTRACTED intents (plan segs).

    Both sides are inverse-model outputs — noise was realized and undone BEFORE this runs.
    No raw canvas strokes; no comparison-time canonicalization shortcut.
    """
    if len(query_plan_segs) != len(candidate_segs) or not query_plan_segs:
        return None
    dtw_terms = []
    kw = dict(n_points=n_points, turn_bins=turn_bins, len_bins=len_bins,
              grid=grid, scale_bins=scale_bins)
    for q_seg, c_seg in zip(query_plan_segs, candidate_segs):
        if not q_seg or not c_seg:
            return None
        render_q = _render_intent_term(q_seg, **kw)
        render_c = _render_intent_term(c_seg, **kw)
        q_pts = native.evaluate(render_q, {})
        if not q_pts:
            return None
        dtw_terms.append(_dtw_term(render_c, q_pts))
    return _mean_dtw_term(dtw_terms)


def outcome_arrangement_term(query_strokes: list, candidate_segs: list, *,
                             native, n_points: int = DEFAULT_RENDER_N,
                             turn_bins: int = DEFAULT_TURN_BINS,
                             len_bins: int = DEFAULT_LEN_BINS,
                             grid: int = DEFAULT_GRID,
                             scale_bins: int = DEFAULT_SCALE_BINS) -> Optional[dict]:
    """Whole-trace OUTCOME compare: candidate at canonical arrangement vs raw query canvas."""
    if len(query_strokes) != len(candidate_segs) or not query_strokes:
        return None
    q_pts = [p for stroke in query_strokes for p in stroke]
    c_pts = []
    ox, oy = 0.0, 0.0
    for seg in candidate_segs:
        if not seg:
            return None
        render = _render_intent_term(seg, n_points=n_points, turn_bins=turn_bins,
                                     len_bins=len_bins, grid=grid, scale_bins=scale_bins)
        pts = native.evaluate(render, {})
        if not pts:
            return None
        for p in pts:
            c_pts.append([float(p[0]) + ox, float(p[1]) + oy])
        if pts:
            ox, oy = c_pts[-1][0], c_pts[-1][1]
    return {"type": "PointSetDist",
            "a": {"type": "Lit", "value": q_pts},
            "b": {"type": "Lit", "value": c_pts}}


def outcome_match_term(native, query_strokes: list, candidate_segs: list, *,
                       n_points: int = DEFAULT_RENDER_N,
                       turn_bins: int = DEFAULT_TURN_BINS,
                       len_bins: int = DEFAULT_LEN_BINS,
                       grid: int = DEFAULT_GRID,
                       scale_bins: int = DEFAULT_SCALE_BINS,
                       segments: int = DEFAULT_SEGMENTS) -> Optional[dict]:
    """Per-stroke OUTCOME compare at observed canvas poses (legacy AbS slice)."""
    if len(query_strokes) != len(candidate_segs) or not query_strokes:
        return None
    bounds = _stroke_bbox(query_strokes)
    kw = dict(segments=segments, turn_bins=turn_bins, len_bins=len_bins,
              grid=grid, scale_bins=scale_bins)
    dtw_terms = []
    for q_stroke, seg in zip(query_strokes, candidate_segs):
        if not seg:
            return None
        pose = _pose_bins_from_stroke(native, q_stroke, bounds, **kw)
        if pose is None:
            return None
        render = _render_outcome_term(seg, pose, bounds=bounds, n_points=n_points, **kw)
        dtw_terms.append(_dtw_term(render, q_stroke))
    return _mean_dtw_term(dtw_terms)


def motor_intent_verdict(native, query_strokes: list, candidate_segs_list: list[list],
                          *, mode: str = "intent", query_plan_segs: Optional[list] = None,
                          **kw) -> dict[str, Any]:
    """Held-Argmin verdict. Intent mode requires `query_plan_segs` from inverse model."""
    if mode == "intent":
        if query_plan_segs is None:
            query_plan_segs = extract_motor_plan(native, query_strokes, **kw)["plan_segments"]
    pairs = []
    for ci, segs in enumerate(candidate_segs_list):
        if mode == "arrangement":
            term = outcome_arrangement_term(query_strokes, segs, native=native, **kw)
        elif mode == "outcome":
            term = outcome_match_term(native, query_strokes, segs, **kw)
        else:
            term = intent_match_term(query_plan_segs, segs, native=native, **kw)
        if term is None:
            continue
        score = float(native.evaluate(term, {}) or 0.0)
        pairs.append((score, ci))
    winner = None
    if pairs:
        w = native.evaluate(_argmin_pairs_term(pairs), {})
        if w is not None:
            winner = int(w[1])
    return {"winner": winner, "mode": mode, "scores": pairs,
            "query_plan_segs": query_plan_segs if mode == "intent" else None}


def intent_arrangement_term(query_plan_strokes: list[list], candidate_plan_segs: list, *,
                           native, n_points: int = DEFAULT_RENDER_N,
                           turn_bins: int = DEFAULT_TURN_BINS,
                           len_bins: int = DEFAULT_LEN_BINS,
                           grid: int = DEFAULT_GRID,
                           scale_bins: int = DEFAULT_SCALE_BINS) -> Optional[dict]:
    """AbS generative verdict: render candidate extracted intent in query plan arrangement.

    Candidate plan segs are synthesized at canonical pose, then placed at each query
    plan-stroke origin (mechanical coordinate translate). Verdict is mean per-stroke DtwTo
    against the query's own plan-frame observed ink — not holistic blob warp.
    """
    if len(query_plan_strokes) != len(candidate_plan_segs) or not query_plan_strokes:
        return None
    kw = dict(n_points=n_points, turn_bins=turn_bins, len_bins=len_bins,
              grid=grid, scale_bins=scale_bins)
    dtw_terms = []
    for q_stroke, c_seg in zip(query_plan_strokes, candidate_plan_segs):
        if not c_seg or not q_stroke:
            return None
        render = _render_intent_term(c_seg, **kw)
        pts = native.evaluate(render, {})
        if not pts:
            return None
        q0 = q_stroke[0]
        r0 = pts[0]
        dx = float(q0[0]) - float(r0[0])
        dy = float(q0[1]) - float(r0[1])
        placed = [[float(p[0]) + dx, float(p[1]) + dy] for p in pts]
        dtw_terms.append(_dtw_term({"type": "Lit", "value": placed}, q_stroke))
    return _mean_dtw_term(dtw_terms)


def _held_argmin_winner(native, pairs: list) -> Optional[int]:
    if not pairs:
        return None
    w = native.evaluate(_argmin_pairs_term(pairs), {})
    return int(w[1]) if w is not None else None


def classify_abs_intent(native, query_strokes: list, exemplar_strokes: list[list], *,
                         mode: str = "topology", **kw) -> int:
    """AbS render-compare on extracted motor plans (noise realized first).

    `topology` — canonical-pose render, per-stroke DtwTo between plan segs.
    `arrangement` — render candidate intent placed in query plan arrangement frame.
    """
    extracted = extract_motor_plan(native, query_strokes, **kw)
    q_segs = extracted["plan_segments"]
    q_plan = extracted["plan_strokes"]
    pairs = []
    for ci, ex in enumerate(exemplar_strokes):
        ex_plan = extract_motor_plan(native, ex, **kw)
        if mode == "arrangement":
            term = intent_arrangement_term(q_plan, ex_plan["plan_segments"], native=native, **kw)
        else:
            term = intent_match_term(q_segs, ex_plan["plan_segments"], native=native, **kw)
        if term is None:
            continue
        pairs.append((float(native.evaluate(term, {}) or 1e9), ci))
    w = _held_argmin_winner(native, pairs)
    return int(w) if w is not None else -1


# --------------------------------------------------------------------------- #
#  PROGRAM VERDICT — per-stroke correspondence + warp (BPL path), plan-frame.
#  SC+TPS demoted to diagnostic baseline only (holistic blob warp — false confidence).
# --------------------------------------------------------------------------- #
def _stroke_points_for_whole_figure(strokes: list[list]) -> list:
    out = []
    for stroke in strokes:
        pts = [[float(p[0]), float(p[1])] for p in stroke]
        out.append((pts, None))
    return out


def raw_whole_figure_point_set(strokes: list[list], **kw) -> Optional[list]:
    """Mechanical adapter: canvas strokes → Family-A whole-figure point set."""
    from domains import abs_read as ar
    return ar.whole_figure_point_set(_stroke_points_for_whole_figure(strokes), **kw)


def intent_whole_figure_point_set(strokes: list[list], **kw) -> Optional[list]:
    """After noise realization: plan-frame strokes → whole-figure point set for SC+TPS."""
    from domains import abs_read as ar
    plan = _undo_lift_noise(strokes)
    return ar.whole_figure_point_set(_stroke_points_for_whole_figure(plan), **kw)


def plan_frame_stroke_point_sets(strokes: list[list], *, n: int = 24,
                                  max_strokes: int = 6) -> list:
    """Per-stroke point-sets in plan arrangement frame (after lift noise undone)."""
    return _stroke_sets_from_path_strokes(_undo_lift_noise(strokes), n=n, max_strokes=max_strokes)


def classify_per_stroke_program(query_strokes: list, exemplar_strokes: list[list], *,
                                 intent_corrected: bool = False) -> int:
    """Per-stroke correspondence + warp — plan-frame when intent_corrected."""
    from domains import per_stroke_abs as ps
    if intent_corrected:
        q_sets = plan_frame_stroke_point_sets(query_strokes)
        s_sets = [plan_frame_stroke_point_sets(ex) for ex in exemplar_strokes]
    else:
        q_sets = _stroke_sets_from_path_strokes(query_strokes)
        s_sets = [_stroke_sets_from_path_strokes(ex) for ex in exemplar_strokes]
    pred, _ = ps.classify(q_sets, s_sets)
    return int(pred)


def classify_sctps_diag(native, query_strokes: list, exemplar_strokes: list[list], **kw) -> int:
    """DIAGNOSTIC ONLY — whole-figure SC+TPS blob warp (borrowed Family-A geometry).

    Moderately high accuracy with false confidence; not the proper verdict layer.
    """
    from domains import abs_read as ar
    qps = raw_whole_figure_point_set(query_strokes, **kw)
    cps_list = [raw_whole_figure_point_set(ex, **kw) for ex in exemplar_strokes]
    res = ar.sctps_rerank(native, qps, cps_list, list(range(len(exemplar_strokes))), **kw)
    w = res.get("winner")
    return int(w) if w is not None else -1


def fused_motor_verdict(native, query_strokes: list, exemplar_strokes: list[list], *,
                         mode: str = "intent", **kw) -> dict[str, Any]:
    """Unified classifier — proper stack first, SC+TPS diagnostic last.

    Primary:
      intent          — AbS topology (extracted plan segs, canonical render + DtwTo)
      intent_abs      — AbS arrangement (render candidate in query plan frame)
      program_intent  — per-stroke program inference on plan-frame strokes
    Baselines:
      arrangement     — raw canvas outcome compare (failure mode)
      program_raw     — per-stroke program on raw canvas (diagnostic)
      sctps_diag      — whole-figure SC+TPS blob warp (diagnostic, demoted)
    """
    modes = {
        "intent": lambda: {"winner": classify_abs_intent(
            native, query_strokes, exemplar_strokes, mode="topology", **kw)},
        "intent_abs": lambda: {"winner": classify_abs_intent(
            native, query_strokes, exemplar_strokes, mode="arrangement", **kw)},
        "program_intent": lambda: {"winner": classify_per_stroke_program(
            query_strokes, exemplar_strokes, intent_corrected=True)},
        "arrangement": lambda: motor_intent_verdict(
            native, query_strokes,
            [extract_plan_segments(native, ex, **kw) for ex in exemplar_strokes],
            mode="arrangement", **kw),
        "program_raw": lambda: {"winner": classify_per_stroke_program(
            query_strokes, exemplar_strokes, intent_corrected=False)},
        "sctps_diag": lambda: {"winner": classify_sctps_diag(
            native, query_strokes, exemplar_strokes, **kw)},
        # legacy aliases — route to diagnostic or proper arms
        "topology": lambda: {"winner": classify_abs_intent(
            native, query_strokes, exemplar_strokes, mode="topology", **kw)},
        "sctps_raw": lambda: {"winner": classify_sctps_diag(
            native, query_strokes, exemplar_strokes, **kw)},
    }
    fn = modes.get(mode)
    if fn is None:
        return {"winner": None, "mode": mode}
    out = fn()
    out["mode"] = mode
    return out


def _stroke_sets_from_path_strokes(strokes: list[list], n: int = 24, max_strokes: int = 6) -> list:
    """Inline per_stroke_abs normalization when only raw stroke lists are available."""
    import numpy as np
    arrays = [np.asarray(s, dtype=float) for s in strokes if len(s) >= 1]
    if not arrays:
        return []
    allp = np.concatenate(arrays, 0)
    if len(allp) < 3:
        return []
    mn = allp.mean(0)
    sc = float(np.abs(allp - mn).max()) + 1e-9
    out = []
    for s in arrays[:max_strokes]:
        a = (s - mn) / sc
        if len(a) < 2:
            continue
        d = np.sqrt((np.diff(a, axis=0) ** 2).sum(1))
        cum = np.concatenate([[0.0], np.cumsum(d)])
        if cum[-1] == 0:
            continue
        u = np.linspace(0.0, cum[-1], n)
        out.append(np.stack([np.interp(u, cum, a[:, 0]), np.interp(u, cum, a[:, 1])], 1).tolist())
    return out


def stroke_render_live(native=None) -> bool:
    """Probe: is held `StrokeRender` callable (required for AbS intent verdict)."""
    from domains.abs_read import _stroke_render_live
    import substrate_rs as srs
    n = native or srs.Substrate()._inner
    return _stroke_render_live(n)


def _ensure_motor_intent_seed(agent) -> None:
    from substrate.seed_loader import manifest_for
    native = _native(agent)
    ag = getattr(agent, "agent", agent)
    if native is not None and hasattr(native, "load_seed_manifest"):
        native.load_seed_manifest(manifest_for("motor_intent_core"), ag)


def _trace_stroke_nodes(sub, trace_id) -> list:
    import substrate_rs as srs
    inner = sub._inner
    nid = trace_id if hasattr(trace_id, "value") else srs.NodeID(int(trace_id))
    out = []
    for ts in sub.nodes("TraceStroke"):
        if nid in inner.in_neighbours(ts, "has_trace_stroke"):
            out.append(ts)
    out.sort(key=lambda n: float(sub.node(n)["attrs"].get("index", 0)))
    return out


def realize_and_stamp_noise(agent, trace_id, strokes: list[list], **kw) -> dict[str, Any]:
    """Stamp realized noise datums on graph nodes; rules mint `MotorNoise` from these."""
    import substrate_rs as srs
    sub = _sub(agent)
    inner = sub._inner
    nid = trace_id if hasattr(trace_id, "value") else srs.NodeID(int(trace_id))
    native = _native(agent)
    extracted = extract_motor_plan(native, strokes, **kw)

    stroke_nodes = _trace_stroke_nodes(sub, nid)
    for k, (stroke, ts_nid) in enumerate(zip(strokes, stroke_nodes)):
        inner.set_attr(ts_nid, "points_json", json.dumps(stroke))
        pose = extracted["pose_noise"][k]
        inner.set_attr(ts_nid, "pose_transform", json.dumps(pose))
        inner.set_attr(ts_nid, "pose_realized", 1.0)
        lift = extracted["lift_noise"][k]
        if lift is not None:
            inner.set_attr(ts_nid, "lift_dx", float(lift[0]))
            inner.set_attr(ts_nid, "lift_dy", float(lift[1]))
            inner.set_attr(ts_nid, "lift_realized", 1.0)

    inner.set_attr(nid, "noise_realized", 1.0)
    inner.set_attr(nid, "plan_segments", json.dumps(extracted["plan_segments"]))
    inner.set_attr(nid, "plan_extracted", 1.0)
    sub.tick()
    return extracted


def annotate_execution_trace(agent, strokes: list[list], *,
                              goal_kind: str = "replicate_template") -> int:
    """Stamp ExecutionTrace → realize noise → extract plan → tick rules for MotorPlan/Intent."""
    _ensure_motor_intent_seed(agent)
    sub = _sub(agent)
    inner = sub._inner
    ag = getattr(agent, "agent", agent)
    native = _native(agent)

    tr = sub.add_node("ExecutionTrace", {
        "stroke_count": float(len(strokes)),
        "goal_kind_hint": goal_kind,
        "noise_realized": 0.0,
        "plan_extracted": 0.0,
        "plan_inferred": 0.0,
        "outcome_match_failed": 0.0,
        "gap_noted": 0.0,
    })
    inner.add_edge_unchecked(ag, "has_execution_trace", tr)
    for k, stroke in enumerate(strokes):
        ts = sub.add_node("TraceStroke", {"index": float(k)})
        inner.add_edge_unchecked(tr, "has_trace_stroke", ts)

    realize_and_stamp_noise(agent, tr, strokes)
    return int(tr.value)


def read_extracted_plan(agent, trace_id) -> Optional[list]:
    """Mechanical read-off: inverse-model plan segments stored on ExecutionTrace."""
    import substrate_rs as srs
    sub = _sub(agent)
    nid = trace_id if hasattr(trace_id, "value") else srs.NodeID(int(trace_id))
    raw = sub.node(nid)["attrs"].get("plan_segments")
    if not raw:
        return None
    try:
        return json.loads(raw)
    except (TypeError, ValueError):
        return None


def held_motor_noise(agent) -> list[dict]:
    """Query MotorNoise nodes the rules minted after noise realization."""
    sub = _sub(agent)
    out = []
    for nid in sub.nodes("MotorNoise"):
        attrs = sub.node(nid)["attrs"]
        out.append({"id": int(nid.value), "kind": attrs.get("kind"),
                    "dx": attrs.get("dx"), "dy": attrs.get("dy"),
                    "explained": attrs.get("explained")})
    return out


def record_outcome_match_failure(agent, trace_id) -> None:
    """Mechanical datum for `note_outcome_intent_recognition_gap` — not a decision."""
    import substrate_rs as srs
    _ensure_motor_intent_seed(agent)
    sub = _sub(agent)
    inner = sub._inner
    nid = trace_id if hasattr(trace_id, "value") else srs.NodeID(int(trace_id))
    inner.set_attr(nid, "outcome_match_failed", 1.0)
    sub.tick()


def held_motor_intents(agent) -> list[dict]:
    """Query MotorIntent nodes the rules minted — mechanical read-off."""
    sub = _sub(agent)
    out = []
    for nid in sub.nodes("MotorIntent"):
        attrs = sub.node(nid)["attrs"]
        out.append({"id": int(nid.value), "goal_kind": attrs.get("goal_kind"),
                    "status": attrs.get("status")})
    return out


def stroke_quantize_live() -> bool:
    import substrate_rs as srs
    return _stroke_quantize_live(srs.Substrate()._inner)


_NO_PYTHON_DECISION_PATTERNS = [
    re.compile(r"\bmin\s*\("),
    re.compile(r"\bmax\s*\("),
    re.compile(r"\bsorted\s*\("),
    re.compile(r"\bargmin\b"),
    re.compile(r"\bargmax\b"),
]


def audit_no_python_decisions() -> list[str]:
    """Source audit: this module must not rank/score-decide in Python."""
    import inspect
    import domains.motor_intent as mod
    violations = []
    for name, obj in inspect.getmembers(mod, inspect.isfunction):
        if name.startswith("_") and name not in ("_argmin_pairs_term",):
            continue
        try:
            src = inspect.getsource(obj)
        except OSError:
            continue
        for pat in _NO_PYTHON_DECISION_PATTERNS:
            if pat.search(src) and name != "audit_no_python_decisions":
                violations.append(f"{name}: {pat.pattern}")
    return violations
