"""Two-eye super-resolution on the REAL 2-D az×el retina (block 177000).

A mechanical world-adapter — NO agent decisions, NO graph-state conditionals.
It closes Rung 5's largest caveat (`VISION_TWO_EYES_REGISTRATION_RESULTS.md` §6:
*"a 2-D flat wall is the same estimator per elevation row (separable), noted not
run"*) by running the PROVEN 1-D pieces per elevation row of the 2-D retina:

  1. INGEST — build a 2-D `GraphEye` (`retina_2d=True`), sample a flat 2-D
     textured wall at each cell `(col, row)` at azimuth `col + offset` (a KNOWN
     rigid sub-receptor azimuth displacement), submit the photon packets, drive
     the SAME `photon_transduce_onset` graph kernel Rungs 1-4 use, and read each
     cell's transduced `activation`. Mechanical text-to-graph-to-value; the 2-D
     twin of `two_eye_superres.sample_eye`, and byte-identical to it per cell
     (the 2-D rod runs the identical transduction — verified in the gate).

  2. REGISTER + FUSE — for EACH elevation row independently: estimate the row's
     azimuth offset with the UNCHANGED Rung-5b cross-frame-phase estimator
     (`two_eye_register.estimate_offset_phase`), then fuse that row with the
     UNCHANGED Rung-5 `multilook_superres` kernel (`two_eye_superres.
     SuperResFuser`). Assemble the 2-D fused field row by row.

NO new Rust, NO new DSL Term, NO new CognitiveTask kind. This module is a loop
over the proven 1-D estimator + fuser; the DECISIONS (de-aliasing reconstruction,
the phase read) live entirely in the existing kernels/sensor. SEPARABILITY — that
the per-row estimates AGREE — is the claim this harness exists to measure.

DEFAULT OFF / additive: it imports the existing eyes/fuser through their public
paths and ADDS a 2-D loop beside them; it edits none of them (§9).
"""
from __future__ import annotations

from domains.photon_eye import GraphEye
from domains.two_eye_superres import ROD_CENTER_NM


def sample_eye_2d(texture_fn, *, n_az, n_el, offset, exposure=1.0,
                  adapt_rate=0.0):
    """Build a 2-D `GraphEye` and view a flat 2-D textured wall offset in AZIMUTH
    by `offset` receptors; return `(positions_az, activations)`.

    `texture_fn(x, row)` is the surface luminance at azimuth world position `x`
    (receptor units) and elevation index `row`. Cell `(col, row)` sees azimuth
    position `x_col = col + offset`, identical every row (one rigid azimuth
    displacement of the eye). Photon count at a cell is `round(exposure *
    texture_fn(x_col, row))` (integer packets — real photon quantisation).

    Returns `positions_az` (length `n_az`, shared by all rows) and `activations`
    (a list of `n_el` rows, each a list of `n_az` transduced `activation`s — the
    eye's samples of the wall). `adapt_rate=0.0` freezes the adapting floor so a
    single static exposure reads the pure Naka-Rushton transduction (the same
    frozen-floor convention as the 1-D `sample_eye`).
    """
    eye = GraphEye(
        n_az=n_az, n_el=n_el, adapt_rate=adapt_rate,
        context={"retina_2d": True, "synchronous": True, "worker_capacity": 1})
    eye.build()
    positions_az = [float(col) + float(offset) for col in range(n_az)]
    packets = []
    for row in range(n_el):
        for col in range(n_az):
            x = positions_az[col]
            count = int(round(max(0.0, float(exposure) * float(texture_fn(x, row)))))
            packets.append({"col": col, "row": row,
                            "wavelength_nm": ROD_CENTER_NM, "count": count})
    eye.submit_photons_2d(packets)
    eye.substrate._inner.run_cognitive_tasks(1)
    eye.substrate._inner.run_rules()
    activations = []
    for row in range(n_el):
        line = []
        for col in range(n_az):
            flat = row * n_az + col
            rod = eye._receptors[(flat, "rod")]
            line.append(
                float(eye.substrate.node(rod)["attrs"].get("activation", 0.0)))
        activations.append(line)
    eye.stop()
    return positions_az, activations
