"""mccollough_world — a world adapter for the McCOLLOUGH CONTINGENT AFTEREFFECT
(VISION_MCCOLLOUGH_PREREG.md).

Mechanical I/O ONLY (CLAUDE.md / PROTOCOL §0). This file:
  * builds a Scene + a set of oriented colour patches (Region nodes with integer
    cone attrs cL,cM,cS and a `theta` orientation LABEL),
  * mints one orientation PRIOR node (Contingency) per distinct theta and wires
    each region to its prior via a single `tunes` edge (K -tunes-> R; grid-geometry
    scaffolding, exactly like colour_world wires `neighbour` and space_quantize
    wires portals),
  * blind-writes the OFF-by-default flags / phase / frame counter,
  * ticks the substrate to a fixpoint,
  * reads the computed percept (percept_rg / percept_by) and prior back.

It makes NO percept decision. The learned prior E[colour|orientation], the
render-from-prior + opponent-residual (predictive) and the direct read
(feedforward) are ALL seed rules (vision_mccollough). Orientation is supplied as a
stimulus feature (theta), exactly as cone values are supplied -- the adapter never
computes orientation or opponent colour. Supplying theta + cL,cM,cS per patch is
mechanical ingest.
"""
from __future__ import annotations


def add_field(s, *, patches: list[dict]) -> dict:
    """Create a Scene + one Region per patch, mint one Contingency prior per
    distinct `theta`, and wire K -tunes-> R.

    Each `patches` entry: `theta` (orientation label, float), `cL`,`cM`,`cS`
    (integer cone values), `is_adapt` (1.0 adapting stimulus / 0.0 test stimulus),
    optional `rrow`,`rcol` for readback keys. Returns
    {scene, region_ids, priors, index, meta}.
    """
    scene = s.add_node("Scene", {"budget": 0.0, "spent": 0.0})
    priors: dict = {}         # theta -> Contingency node id
    region_ids: list = []
    index: dict = {}
    meta: list = []
    for i, spec in enumerate(patches):
        theta = float(spec["theta"])
        if theta not in priors:
            priors[theta] = s.add_node("Contingency", {
                "theta": theta, "sum_rg": 0.0, "sum_by": 0.0, "n": 0.0,
            })
        n = s.add_node("Region", {
            "theta": theta,
            "rrow": float(spec.get("rrow", i)),
            "rcol": float(spec.get("rcol", 0)),
            "cL": float(spec["cL"]),
            "cM": float(spec["cM"]),
            "cS": float(spec["cS"]),
            "is_adapt": float(spec.get("is_adapt", 0.0)),
            "astep": -1.0,
            "pdone": 0.0,
            "percept_rg": 0.0,
            "percept_by": 0.0,
        })
        # add_edge_unchecked: EXTERNAL world scaffolding (which prior slot a patch
        # belongs to, by its orientation label) -- host-owned bookkeeping, not an
        # agent claim; bypasses Gamma exactly like colour_world's `neighbour` wiring.
        s.add_edge_unchecked(scene, "has_region", n)
        # K -tunes-> R : one OUTGOING edge per patch from its orientation prior, so
        # each Region has exactly ONE incoming `tunes` (avoids the two-incoming-edges
        # matcher gotcha noted in CLAUDE.md).
        s.add_edge_unchecked(priors[theta], "tunes", n)
        region_ids.append(n)
        index[(int(spec.get("rrow", i)), int(spec.get("rcol", 0)))] = n
        meta.append(spec)
    return {"scene": scene, "region_ids": region_ids, "priors": priors,
            "index": index, "meta": meta}


def set_flags(s, *, enabled: float, mode: float) -> None:
    """Blind-write mcc_enabled / mcc_mode on every MccoughParams. No read, no branch."""
    for p in s.nodes("MccoughParams"):
        s.set_attr(p, "mcc_enabled", float(enabled))
        s.set_attr(p, "mcc_mode", float(mode))


def set_phase(s, phase: float) -> None:
    """Blind-write mcc_phase (0=adapt, 1=test) on every MccoughParams."""
    for p in s.nodes("MccoughParams"):
        s.set_attr(p, "mcc_phase", float(phase))


def set_frame(s, frame: float) -> None:
    """Blind-write the adaptation-frame counter on every MccoughParams."""
    for p in s.nodes("MccoughParams"):
        s.set_attr(p, "frame", float(frame))


def tick(s, max_steps: int = 200_000) -> int:
    """run_rules to a fixpoint. Returns the sweep count."""
    return s.tick(max_steps)


def adapt(s, handle: dict, *, frames: int) -> None:
    """Present the adapting stimulus for `frames` frames. Each frame bumps the
    frame counter and ticks -> mcc_learn fires once per adapting region, so the
    prior accumulates the running mean E[colour|orientation]. Mechanical: it only
    advances the clock; the learning is the rule."""
    set_phase(s, 0.0)
    for f in range(1, frames + 1):
        set_frame(s, float(f))
        tick(s)


def test(s, handle: dict) -> None:
    """Switch to the test phase and tick -> a percept rule fires per test region."""
    set_phase(s, 1.0)
    tick(s)


def read_percept(s, handle: dict, key: str) -> list[float]:
    """Per-region percept value (percept_rg / percept_by), in region order."""
    return [float(s.node(n)["attrs"].get(key, 0.0)) for n in handle["region_ids"]]


def cell_percept(s, handle: dict, rrow: int, rcol: int, key: str) -> float:
    return float(s.node(handle["index"][(rrow, rcol)])["attrs"].get(key, 0.0))


def prior_of(s, handle: dict, theta: float) -> dict:
    """Read a learned orientation prior (measurement, no decision): the running
    mean colour sum/max(n,1) and the raw sums/count."""
    k = handle["priors"][float(theta)]
    a = s.node(k)["attrs"]
    n = float(a.get("n", 0.0))
    d = max(n, 1.0)
    return {"n": n, "sum_rg": float(a.get("sum_rg", 0.0)),
            "sum_by": float(a.get("sum_by", 0.0)),
            "mean_rg": float(a.get("sum_rg", 0.0)) / d,
            "mean_by": float(a.get("sum_by", 0.0)) / d}
