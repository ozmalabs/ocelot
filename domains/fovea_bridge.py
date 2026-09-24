"""fovea_bridge — THE WORLD ADAPTER for the fovea/salience bridge (160000).

The MIGRATION rung: 159000 selected the fovea with a numpy ``argmax``/top-K in
Python (``scripts/salience_foveation_probe.py::select_fovea``'s
``scored.sort(key=-peak)[:top_k]``). That is an agent DECISION in Python, which
CLAUDE.md forbids. This module keeps ONLY the mechanical parts and hands the
DECISION to the graph:

  * ``extract_candidates`` — MECHANICAL world-adapter I/O. The residual-salience
    field -> ``flag_movers`` -> connected components -> per-component peak/box.
    This is byte-for-byte the extraction ``select_fovea`` runs BEFORE its sort;
    it makes the smallest graph token (one ``FoveaCandidate`` per salient region)
    out of an opaque numpy field. No conditional over graph state, no selection.

  * ``resolve_fovea`` — INGEST + tick + READ-BACK. Writes the candidates as
    ``FoveaCandidate`` graph nodes (``res -has_candidate-> c``), runs the Rust
    rule engine (``seeds/fovea_salience_bridge.json``'s ``fovea_resolve``), and
    READS BACK the candidate the GRAPH flagged ``is_fovea==1``. The SELECTION --
    the highest-log-weight Gamma-admissible candidate -- is computed by the
    engine's ``ArgminUnique`` over ``Neg(Log(salience)+goal_logweight)``, NOT by
    any Python argmax/max/sort/comparison. Python only translates and reads.

grammar.rs: Gamma is the WEIGHTED ADMISSIBILITY grammar; "selection over admitted
candidates is proportional to exp(w)". The MAP reading of that is
``argmax_w over admissible candidates`` = ``ArgminUnique(admissible, Neg(w))``.
"""
from __future__ import annotations

from typing import Optional, Sequence

import numpy as np

# Mechanical field ops reused from the 159000 probe stack (segmentation only --
# NOT the selection). These are pure numpy over the flow/salience fields.
from scripts.depth_from_motion_probe import flag_movers  # noqa: E402
from scripts.salience_foveation_probe import (  # noqa: E402
    _connected_components,
    FOVEA_MIN_HALF,
    FOVEA_PAD,
    MIN_REGION,
    SAL_FLOOR,
)


# ======================================================================
#  INGEST — mechanical extraction of candidate fovea targets (no decision).
#  This is select_fovea's body WITHOUT the `scored.sort(...)[:top_k]` line.
# ======================================================================
def extract_candidates(salience, valid, *, min_half=FOVEA_MIN_HALF, pad=FOVEA_PAD,
                       min_region=MIN_REGION, sal_floor=SAL_FLOOR):
    """MECHANICAL: the flagged (Otsu+floor) salience -> connected components ->
    per-component peak cell + bbox window + region size. Returns the candidate
    list in DISCOVERY order (NOT ranked -- ranking is the graph's job). Each
    candidate: {peak_rc, peak(=salience), box, region_cells, on_valid}. If nothing
    is flagged => [] (no candidate; the caller falls back to the coarse pass)."""
    salience = np.asarray(salience, np.float64)
    valid = np.asarray(valid, bool)
    gh, gw = salience.shape
    flagged, cut = flag_movers(salience, valid, floor=sal_floor)
    if not flagged.any():
        return [], cut
    comps = _connected_components(flagged)
    cands = []
    for rs, cs in comps:
        if len(rs) < min_region:                  # single-cell rounding spike
            continue
        vals = salience[rs, cs]
        k = int(np.argmax(vals))                  # peak LOCATION (mechanical), not
        pr, pc = int(rs[k]), int(cs[k])           # the fovea DECISION among regions
        rmin, rmax = int(rs.min()), int(rs.max())
        cmin, cmax = int(cs.min()), int(cs.max())
        rc = (rmin + rmax) / 2.0; cc = (cmin + cmax) / 2.0
        hh = max(min_half, (rmax - rmin) / 2.0 + pad)
        hw = max(min_half, (cmax - cmin) / 2.0 + pad)
        r0 = max(0, int(np.floor(rc - hh))); r1 = min(gh, int(np.ceil(rc + hh)) + 1)
        c0 = max(0, int(np.floor(cc - hw))); c1 = min(gw, int(np.ceil(cc + hw)) + 1)
        cands.append({"peak_rc": [pr, pc], "peak": float(vals[k]),
                      "box": [r0, r1, c0, c1], "region_cells": int(len(rs)),
                      "on_valid": 1})
    return cands, cut


# ======================================================================
#  RESOLUTION — ingest to graph, tick, read back. THE DECISION IS THE GRAPH'S.
# ======================================================================
def _boot():
    """Fresh seed-booted substrate with the fovea bridge rule loaded."""
    from substrate.boot_core import boot_core
    from domains import reflective_faculty as rf
    from substrate.seed_loader import manifest_for
    s, ag = boot_core()
    native = rf._native_eval2(s)
    native.load_seed_manifest(manifest_for("fovea_salience_bridge"), ag)
    return s, ag, native


def ingest_candidates(s, res, cands: Sequence[dict],
                      goal_logweights: Optional[Sequence[float]] = None,
                      admissible: Optional[Sequence[int]] = None):
    """MECHANICAL: write each candidate as a FoveaCandidate node edged
    `res -has_candidate-> c`. `goal_logweights[i]` is a CO-PRESENT top-down
    log-weight on candidate i (default 0); `admissible[i]` overrides the Gamma
    admissibility datum on_valid (default: the candidate's own on_valid). No
    decision -- pure translation."""
    ids = []
    for i, cand in enumerate(cands):
        g = float(goal_logweights[i]) if goal_logweights is not None else 0.0
        ov = int(admissible[i]) if admissible is not None else int(cand.get("on_valid", 1))
        cid = s.add_node("FoveaCandidate", {
            "cand_id": i,
            "peak_row": int(cand["peak_rc"][0]),
            "peak_col": int(cand["peak_rc"][1]),
            "salience": float(cand["peak"]),
            "region_cells": int(cand.get("region_cells", 1)),
            "on_valid": float(ov),
            "goal_logweight": g,
        })
        s.add_edge(res, "has_candidate", cid)
        ids.append(cid)
    return ids


def read_fovea(s, cand_ids: Sequence[int]) -> Optional[dict]:
    """MECHANICAL read-back: the candidate the GRAPH flagged is_fovea==1. Returns
    its attrs (or None if the graph resolved no fovea -- empty source or a
    log-weight TIE that ArgminUnique refused). NO Python selection here: this only
    reads which node the engine already marked."""
    for cid in cand_ids:
        a = s.node(cid)["attrs"]
        if float(a.get("is_fovea", 0.0)) == 1.0:
            return a
    return None


def resolve_fovea(cands: Sequence[dict],
                  goal_logweights: Optional[Sequence[float]] = None,
                  admissible: Optional[Sequence[int]] = None) -> Optional[dict]:
    """Full loop: ingest candidates -> run_rules -> read the graph's fovea.
    The SELECTION is the engine's ArgminUnique over the log-weighted admissible
    candidates (seeds/fovea_salience_bridge.json). Returns the winning candidate's
    attrs dict (with peak_row/peak_col), or None if the graph resolved no fovea."""
    if not cands:
        return None
    s, ag, native = _boot()
    res = s.add_node("FoveaResolver", {})
    ids = ingest_candidates(s, res, cands, goal_logweights, admissible)
    native.run_rules()
    s.add_node("NativeFoveaResolutionReceipt", {
        "schema": "native_fovea_resolution_receipt_v1",
        "cluster": "fovea_bridge.salience_selection",
        "provenance": "native_rule_readback:fovea_salience",
        "native_rule": "fovea_salience_argmin_unique",
        "native_steps": ["ingest_candidates", "run_rules", "read_fovea"],
        "outcome_source": "native_rule_readback",
        "python_outcome_selection": False,
    })
    return read_fovea(s, ids)
