"""Generate a Seldon-manifold visualisation scene.

Builds several candidate future trajectories (wait / refine / commit, the
same three projections named in CLAUDE.md's engine-wide decision boundary)
against a target/acceptable continuation, and audits every one of them
through the REAL modality-independent Rust future-manifold projector
(`FutureManifoldProjection`, runners/dsl/src/future_manifold.rs) — the same
Term the speech future-manifold path uses (domains/projection.py,
substrate_rs/speech.py:project_sign_future_manifold). This script does not
reimplement the audit: it builds graph nodes carrying the
`future_manifold_*` contract and calls the native evaluator for every field.

Python's only job here is graph construction + native evaluate calls
(mechanical), matching the project's Python-is-a-world-adapter rule. The
candidate trajectories themselves are hand-authored demo data (no live
agent run backs this), by explicit user choice — this is a viewer for the
Seldon-manifold contract, not a claim about any particular episode.

Output: a JSON scene consumed by the 3D visualiser artifact.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "runners" / "dsl" / "python"))

from substrate_rs import Substrate

FIELDS = (
    "support", "resolved", "termination_code", "horizon", "budget",
    "loss", "information_loss", "retained_width", "anchor_count",
    "certified_interval_count", "ambiguous_interval_count",
    "max_enclosure_width", "earliest_decisive_tick",
    "retained_0", "retained_1",
)

DIM_LABELS = ["lateral deviation", "risk margin"]
TICKS = 12


def _native(s):
    return s._inner if hasattr(s, "_inner") else s


def project(inner, values, widths, target, bounds, budget, horizon):
    episode = inner.add_node("SeldonDemoEpisode", {
        "future_manifold_target": target,
        "future_manifold_bounds": bounds,
    })
    policy = inner.add_node("SeldonDemoPolicy", {
        "future_manifold_projection_budget": float(budget),
        "future_manifold_physical_horizon": float(horizon),
    })
    source = inner.add_node("SeldonDemoCandidate", {
        "future_manifold_values": values,
        "future_manifold_widths": widths,
    })
    out = {}
    for field in FIELDS:
        term = {
            "type": "FutureManifoldProjection",
            "episode": {"type": "Var", "name": "episode"},
            "policy": {"type": "Var", "name": "policy"},
            "source": {"type": "Var", "name": "source"},
            "field": field,
        }
        out[field] = float(inner.evaluate(
            term, {"episode": episode, "policy": policy, "source": source}))
    return out


def wait_trajectory(ticks, wait_lateral, wait_risk):
    """No correction: momentum carries the state along its existing
    direction (Law of Narrative Momentum) — drifts out of tolerance late."""
    values, widths = [], []
    for t in range(1, ticks + 1):
        values.append([round(wait_lateral * t, 4), round(wait_risk * t, 4)])
        widths.append([0.15, 0.10])  # tight — the drift itself is the failure, not uncertainty
    return values, widths


def refine_trajectory(ticks, refine_gain):
    """Partial, foveated correction: coarse early, resolution increases as
    the decision-relevant region approaches, converges inside tolerance."""
    values, widths = [], []
    for t in range(1, ticks + 1):
        frac = t / ticks
        lateral = 3.0 * (1 - math.exp(-refine_gain * frac))
        risk = 1.6 * (1 - math.exp(-refine_gain * 0.91 * frac))
        values.append([round(lateral, 4), round(risk, 4)])
        # width shrinks as foveation sharpens near the decision point
        widths.append([round(0.9 * (1 - frac) + 0.12, 4), round(0.6 * (1 - frac) + 0.08, 4)])
    return values, widths


def commit_trajectory(ticks, commit_gain):
    """Decisive early correction: narrativium spent up front, tight tube
    throughout, minimum sufficient intervention to stay inside the goal."""
    values, widths = [], []
    for t in range(1, ticks + 1):
        frac = t / ticks
        lateral = 3.1 * (1 - math.exp(-commit_gain * frac))
        risk = 1.55 * (1 - math.exp(-commit_gain * frac))
        values.append([round(lateral, 4), round(risk, 4)])
        widths.append([0.10, 0.07])
    return values, widths


def target_and_bounds(ticks, tol_lateral, tol_risk):
    """The acceptable manifold: goal continuation the frame is willing to
    treat as inside Goal_{h,rho} subset Seldon_{h,rho}."""
    target, bounds = [], []
    for t in range(1, ticks + 1):
        frac = t / ticks
        lateral = 3.0 * (1 - math.exp(-4.0 * frac))
        risk = 1.5 * (1 - math.exp(-4.0 * frac))
        target.append([round(lateral, 4), round(risk, 4)])
        bounds.append([round(tol_lateral, 4), round(tol_risk, 4)])
    return target, bounds


# ---------------------------------------------------------------------------
# Derived presentation metrics.
#
# These are NOT native-audited fields — the Rust FutureManifoldProjection
# Term certifies retention/loss for exactly one candidate against exactly
# one target. Muchness, reachable muchness, narrativium cost, and basins are
# plain arithmetic aggregates computed here, in Python, OVER those already-
# audited per-candidate numbers (tube widths, and the identical per-cell
# `residual <= bound + width` retained test the Rust engine applies). This
# is display aggregation for the instrument, not a new decision — nothing
# here decides what the agent does; it only sums/labels what the engine
# already certified. See CLAUDE.md's Python-is-a-world-adapter rule.
# ---------------------------------------------------------------------------

def _cell_retained(value_row, width_row, target_row, bound_row):
    return all(
        abs(value_row[d] - target_row[d]) <= bound_row[d] + width_row[d]
        for d in range(len(value_row))
    )


def _tube_area(width_row):
    area = 1.0
    for w in width_row:
        area *= 2.0 * w
    return area


def compute_muchness(candidates, target, bounds, ticks):
    """Per tick: total retained future possibility (sum of every admissible
    candidate's tube cross-section — Muchness), and the portion of it that
    also lands inside the acceptable manifold (Reachable muchness)."""
    much = [0.0] * ticks
    reach = [0.0] * ticks
    for c in candidates:
        for t in range(ticks):
            area = _tube_area(c["widths"][t])
            much[t] += area
            if _cell_retained(c["values"][t], c["widths"][t], target[t], bounds[t]):
                reach[t] += area
    return [round(v, 5) for v in much], [round(v, 5) for v in reach]


def compute_narrativium_cost(candidate_values, narrative_values):
    """Cumulative deviation in PER-TICK MOTION from the narrative's own
    momentum — a proxy for N_Frame(R): the force spent bending the
    trajectory away from where momentum alone would have carried it. This
    is a velocity-space comparison, not a position-space one: raw distance
    from the (unboundedly drifting) narrative would grow forever regardless
    of correction effort, since the narrative itself never stops moving.
    Zero for the narrative candidate itself (matching momentum costs
    nothing). previous_* start at the shared t=0 "now" anchor (0, 0)."""
    cum, total = [], 0.0
    prev_c, prev_n = (0.0, 0.0), (0.0, 0.0)
    for v, n in zip(candidate_values, narrative_values):
        dc = (v[0] - prev_c[0], v[1] - prev_c[1])
        dn = (n[0] - prev_n[0], n[1] - prev_n[1])
        total += math.hypot(dc[0] - dn[0], dc[1] - dn[1])
        cum.append(round(total, 4))
        prev_c, prev_n = tuple(v), tuple(n)
    return cum, round(total, 4)


def compute_basins(candidates, target, bounds):
    """Two attractor basins the manifold's tubes settle into by the final
    tick: the acceptable basin (the goal continuation's own terminal
    tolerance) and the momentum basin (where the uncorrected narrative
    lands if nothing redirects it). Depth is purely geometric — inverse of
    terminal cross-section area, i.e. a narrower/more certain settling
    region reads as a deeper well."""
    final_target, final_bounds = target[-1], bounds[-1]
    narrative = next(c for c in candidates if c.get("is_narrative"))
    final_narr_value = narrative["values"][-1]
    final_narr_width = narrative["widths"][-1]
    basins = [
        {
            "id": "acceptable",
            "label": "Acceptable basin",
            "kind": "acceptable",
            "center": final_target,
            "radius": final_bounds,
            "depth": round(1.0 / max(_tube_area(final_bounds), 1e-6), 4),
        },
        {
            "id": "momentum",
            "label": "Momentum basin (unmanaged)",
            "kind": "unmanaged",
            "center": final_narr_value,
            "radius": final_narr_width,
            "depth": round(1.0 / max(_tube_area(final_narr_width), 1e-6), 4),
        },
    ]
    return basins


def build_scene(
    ticks=TICKS,
    commit_gain=5.0,
    refine_gain=2.2,
    wait_lateral=0.55,
    wait_risk=0.35,
    tol_lateral=0.35,
    tol_risk=0.22,
):
    s = Substrate()
    inner = _native(s)
    target, bounds = target_and_bounds(ticks, tol_lateral, tol_risk)

    candidates_src = {
        "wait": ("Wait", lambda: wait_trajectory(ticks, wait_lateral, wait_risk),
                 "the frame's uncorrected momentum — the narrative default"),
        "refine": ("Refine", lambda: refine_trajectory(ticks, refine_gain),
                   "foveated partial correction"),
        "commit": ("Commit", lambda: commit_trajectory(ticks, commit_gain),
                   "decisive minimum-sufficient correction"),
    }

    candidates = []
    for key, (label, builder, note) in candidates_src.items():
        values, widths = builder()
        report = project(
            inner, values, widths, target, bounds,
            budget=ticks, horizon=ticks,
        )
        candidates.append({
            "id": key,
            "label": label,
            "note": note,
            "is_narrative": key == "wait",
            "values": values,
            "widths": widths,
            "report": report,
        })

    narrative = next(c for c in candidates if c["is_narrative"])
    for c in candidates:
        cost_cum, cost_total = compute_narrativium_cost(c["values"], narrative["values"])
        c["narrativium_cost"] = cost_cum
        c["narrativium_total"] = cost_total

    muchness, reachable_muchness = compute_muchness(candidates, target, bounds, ticks)
    basins = compute_basins(candidates, target, bounds)

    scene = {
        "ticks": ticks,
        "dim_labels": DIM_LABELS,
        "target": target,
        "bounds": bounds,
        "candidates": candidates,
        "muchness": muchness,
        "reachable_muchness": reachable_muchness,
        "basins": basins,
    }
    return scene


def main():
    scene = build_scene()
    out_path = Path("/tmp/claude-1000/-home-matt-ozmadev-ocelot/a237a39d-7159-4291-b14a-dcec02c5fb44/scratchpad/seldon_manifold_scene.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(scene, indent=2))
    print(f"wrote {out_path}")
    for c in scene["candidates"]:
        r = c["report"]
        tag = " [narrative default]" if c["is_narrative"] else ""
        print(f"{c['label']:8s} resolved={r['resolved']:.0f} loss={r['loss']:.2f} "
              f"retained_width={r['retained_width']:.0f}/2 "
              f"earliest_decisive_tick={r['earliest_decisive_tick']:.0f} "
              f"narrativium_cost={c['narrativium_total']:.2f}{tag}")
    print(f"muchness (final tick):           {scene['muchness'][-1]:.4f}")
    print(f"reachable muchness (final tick):  {scene['reachable_muchness'][-1]:.4f}")
    for b in scene["basins"]:
        print(f"basin {b['label']:28s} kind={b['kind']:10s} depth={b['depth']:.3f} "
              f"center={b['center']}")


if __name__ == "__main__":
    main()
