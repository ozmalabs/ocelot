"""sdloop_vision — the WORLD ADAPTER for the sd-loop vision rung (seeds 18000-18999).

PROTOCOL §3 / VISION_SDLOOP_PREREG.md. CLAUDE.md's architecture rule is the whole
point of this rung, so this file is held to it strictly: **every function here is
mechanical I/O.** It presents a stimulus, reads the retina's channels, translates the
support into an Observation, ticks, and reads the codebook back. **There is not one
conditional over graph state in this module** — the sd loop (`seeds/shape_decode_loop.json`
+ this rung's one rule in `seeds/vision_sdloop.json`) decides everything: whether an
observation is recognized, transformed, dimension-inferred, or minted.

THE ENCODING, and why it carries no magic number (PROTOCOL §13)
--------------------------------------------------------------
`support()` selects cells where the channel is **`!= 0`**. That is NOT a threshold I
chose — it is the bipolar's own rectification. Measured on burned pilot seed 18000
(VISION_SDLOOP_PREREG.md §3): an inactive bipolar reads **EXACTLY 0.0** (224/256 ON,
192/256 OFF), and every active one is bounded away from zero (ON min **0.891363**, OFF
min **0.008981**). There is no continuum near zero in which to place a cut. So the
**integer lattice `coord_ints` requires FALLS OUT of the retina** rather than going in —
which is what CLAUDE.md's frame/continuum invariant demands ("in-frame is INTEGER";
`coord_ints` returning None on a Float slot is CORRECT and load-bearing).

The signature is `[["on", r, c], ...] + [["off", r, c], ...]` with
`dim_types = ["pred", "coord:r", "coord:c"]`. Orientation is therefore left as a
**rotation of the coordinate lattice** — the form the retina actually delivers it in.
It is deliberately NOT encoded as a slot (`["edge", r, c, orientation_index]`), which
would hand `cycle4` the very structure the loop was supposed to grow (PROTOCOL §0/§13.1).

THE KEY (PREREG §3.2) — the one place a fake positive could enter
----------------------------------------------------------------
`sd_dedup_existing` marks an Observation `recognized_duplicate` when an axis with the
same `capability_keys` exists. A key SHARED across orientations would collapse
mint-count to 1 for free — a fake positive passing every §1 check. So every stimulus
gets a **UNIQUE** key and dedup can never manufacture the headline.
"""
from __future__ import annotations

import numpy as np

# Per-slot typing for a ["on"/"off", r, c] relation. Only the "coord:" prefix is
# interpreted by DimInfer (`dims_are_coord`); the axis label is free text.
DIM_TYPES = ["pred", "coord:r", "coord:c"]


def bar_frame(theta_deg: float, h: int = 16, w: int = 16, thick: float = 1.2) -> np.ndarray:
    """A rasterised oriented bar through the grid centre — the STIMULUS, pure numpy.

    Unstructured-ish external input the adapter is licensed to supply (PROTOCOL §0: the
    adapter supplies the world; the GRAPH makes the structure). `thick` is a rasterisation
    width, not a model parameter: it is the smallest value that yields a connected
    single-cell-wide line on a 16x16 lattice at every angle, and no result reads it.
    """
    th = np.deg2rad(theta_deg)
    cy, cx = (h - 1) / 2.0, (w - 1) / 2.0
    f = np.zeros((h, w), np.float32)
    for r in range(h):
        for c in range(w):
            if abs(-(r - cy) * np.cos(th) + (c - cx) * np.sin(th)) < thick:
                f[r, c] = 1.0
    return f


def support(on: np.ndarray, off: np.ndarray) -> list[list]:
    """The retina's ON/OFF channels -> a relation-system. Mechanical translation.

    `!= 0` is the rectifier's own output, not a threshold (see module docstring).
    """
    sig: list[list] = []
    for r, c in zip(*np.nonzero(on)):
        sig.append(["on", int(r), int(c)])
    for r, c in zip(*np.nonzero(off)):
        sig.append(["off", int(r), int(c)])
    return sig


def ingest(s, ag, signature: list[list], key: str):
    """Write one Observation into the graph and hand off to the loop. No decisions."""
    obs = s.add_node("Observation", {
        "signature": [list(x) for x in signature],
        "key": [key],
        "dim_types": list(DIM_TYPES),
        "status": "pending",
        "vq": 1,                       # this rung's inertness guard (PROTOCOL §9)
    })
    s.add_edge(ag, "observed", obs)
    return obs


def read_outcome(s, obs) -> dict:
    """Read one Observation's verdict back out. Pure query."""
    at = s.node(obs)["attrs"]
    out = {
        "status": at.get("status"),
        "covered_by": at.get("covered_by"),
        "transform_checked": at.get("transform_checked"),
        "transform_explained": at.get("transform_explained"),
        "dim_checked": at.get("dim_checked"),
        "dim_explained": at.get("dim_explained"),
        "n_residual": len(at.get("residual") or ()),
        "generator": None,
        "k": None,
        "transform_kinds": [],
        "plan_len": None,
    }
    dec = at.get("decode")
    if isinstance(dec, dict):
        plan = dec.get("plan")
        out["plan_len"] = len(plan) if plan is not None else None
    for t in s.neighbours(obs, "has_transform"):
        t_at = s.node(t)["attrs"]
        out["generator"] = t_at.get("generator")
        out["k"] = t_at.get("k")
        tr = t_at.get("transforms") or ()
        out["transform_kinds"] = [
            (x.get("kind") if isinstance(x, dict) else None) for x in tr
        ]
    return out


def codebook_state(s) -> dict:
    """Counts the whole rung reads. Pure query."""
    axes = [n for n in s.nodes("CapabilityAxis")
            if (s.node(n)["attrs"].get("induced") == 1.0)]
    lds = list(s.nodes("LatentDimension"))
    return {
        "mints": len(axes),
        "latent_dims": len(lds),
        "latent_names": sorted({str(s.node(n)["attrs"].get("name")) for n in lds}),
        "shape_signatures": len(list(s.nodes("ShapeSignature"))),
    }


__all__ = ["DIM_TYPES", "bar_frame", "support", "ingest", "read_outcome", "codebook_state"]
