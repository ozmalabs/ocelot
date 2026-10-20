"""Tests for P2.C3 (`tolerance_registry` and inline-literal tolerance migrations).

Covers:
1. P2.C3.2: `tolerance_registry` loads beside its target seeds and every `Tolerance`
   node resolves via `governs_policy` to exactly one policy node carrying `governs_attr`
   with its declared `default` value.
2. P2.C3.3: `valence_salience` in `seeds/residual_salience.json` reads
   `SaliencePolicy.shape_match_tolerance` (default 2.0) instead of an inline literal;
   changing `shape_match_tolerance` on `SaliencePolicy` changes whether a nearby
   `Shape` matches.
3. P2.C3.4: `sd_infer_dimension` in `seeds/shape_decode_loop.json` reads the fallback
   `dim_grains` from `DimInferPolicy` when `agent.dim_grains` is `None`.
"""
from __future__ import annotations

import json
from pathlib import Path
import pytest

pytest.importorskip("substrate_rs")

from domains import reflective_faculty as rf
from substrate.boot_core import boot_core, load_seeds_into
from substrate.seed_loader import manifest_for


def _load_manifests(s, ag, seed_ids):
    for sid in seed_ids:
        s._inner.load_seed_manifest(manifest_for(sid), ag)


def test_tolerance_registry_resolves_all_target_policies():
    s, ag = boot_core()
    _load_manifests(
        s,
        ag,
        [
            "capability_collapse",
            "motor_decision_collapse",
            "affective_state_core",
            "dual_process_core",
            "autonomy",
            "residual_salience",
            "math_capability_shapes",
            "self_design_axis",
            "shape_decode_loop",
            "tolerance_registry",
        ],
    )

    tols = s.neighbours(ag, "has_tolerance")
    assert len(tols) == 5

    seen_names = set()
    for tid in tols:
        t_attrs = s.node(tid)["attrs"]
        seen_names.add(t_attrs["name"])
        governs_attr = t_attrs["governs_attr"]
        assert t_attrs["direction"] in ("widen_up", "widen_down")

        targets = s.neighbours(tid, "governs_policy")
        assert len(targets) == 1, f"{t_attrs['name']} resolved to {len(targets)} policies"
        p_attrs = s.node(targets[0])["attrs"]
        assert governs_attr in p_attrs, f"{governs_attr} missing on {p_attrs}"
        assert p_attrs[governs_attr] == t_attrs["default"]

    assert seen_names == {
        "motor_settle_tolerance",
        "dual_process_conflict_margin_tolerance",
        "dual_process_minimum_confidence_tolerance",
        "salience_shape_match_tolerance",
        "dim_infer_grain_tolerance",
    }


def test_valence_salience_reads_shape_match_tolerance_from_salience_policy():
    s, ag = boot_core()
    _load_manifests(s, ag, ["autonomy", "residual_salience"])

    pols = list(s.nodes("SaliencePolicy"))
    assert len(pols) == 1
    pol = pols[0]
    assert s.node(pol)["attrs"]["shape_match_tolerance"] == 2.0

    # Extract the valence_salience Concept definition from residual_salience
    raw = json.loads((Path(__file__).resolve().parents[1] / "seeds" / "residual_salience.json").read_text())
    val_term = next(c["definition"] for c in raw["concepts"] if c["name"] == "valence_salience")

    # Create two axes: axis A has slightly higher shortfall (0.8) than axis B (0.6),
    # but axis A is at L1 distance 4 from an anti-shape (valence = -1.0).
    ax_a = s.add_node(
        "CapabilityAxis",
        {
            "is_axis": 1.0,
            "shortfall": 0.8,
            "saturation": 0.0,
            "cost": 0.0,
            "aperture": 1.0,
            "csig_0": 4.0,
            "csig_1": 0.0,
            "csig_2": 0.0,
            "csig_3": 0.0,
            "csig_4": 0.0,
            "csig_5": 0.0,
            "csig_6": 0.0,
            "csig_7": 0.0,
        },
    )
    ax_b = s.add_node(
        "CapabilityAxis",
        {
            "is_axis": 1.0,
            "shortfall": 0.6,
            "saturation": 0.0,
            "cost": 0.0,
            "aperture": 1.0,
            "csig_0": 20.0,
            "csig_1": 0.0,
            "csig_2": 0.0,
            "csig_3": 0.0,
            "csig_4": 0.0,
            "csig_5": 0.0,
            "csig_6": 0.0,
            "csig_7": 0.0,
        },
    )
    s._inner.add_edge_unchecked(ax_a, "investigated_by", ag)
    s._inner.add_edge_unchecked(ax_b, "investigated_by", ag)

    s.add_node(
        "Shape",
        {
            "aperture": 1.0,
            "valence": -1.0,
            "sig_0": 0.0,
            "sig_1": 0.0,
            "sig_2": 0.0,
            "sig_3": 0.0,
            "sig_4": 0.0,
            "sig_5": 0.0,
            "sig_6": 0.0,
            "sig_7": 0.0,
        },
    )

    # At default shape_match_tolerance = 2.0, L1=4 > 2.0 so the anti-shape does not match ax_a; ax_a wins.
    assert s._inner.evaluate(val_term, {}) == ax_a

    # Widen shape_match_tolerance on SaliencePolicy to 4.0 -> anti-shape repels ax_a, so ax_b wins.
    s.set_attr(pol, "shape_match_tolerance", 4.0)
    assert s._inner.evaluate(val_term, {}) == ax_b


def test_dim_infer_fallback_reads_dim_grains_from_policy_node():
    s, ag = boot_core()
    native = rf._native_eval2(s)
    rf._ensure_shape_decode_loop(s, native, ag)

    pols = s.neighbours(ag, "has_dim_infer_policy")
    assert len(pols) == 1
    assert list(s.node(pols[0])["attrs"]["dim_grains"]) == [0]

    # Observation that is NOT explained at grain 0 (jittered by 1 pixel), but IS explained at grain 2:
    dim_types = ["pred", "coord:r", "coord:c", "val"]
    tromino = [["cell", 0, 0, "red"], ["cell", 0, 4, "red"], ["cell", 4, 0, "red"]]
    # Rotated k=1 of tromino is (0,0), (0,4), (4,4); jitter one cell to (4,5) so grain 0 fails but grain 2 succeeds
    jittered_rot = [["cell", 0, 0, "red"], ["cell", 0, 4, "red"], ["cell", 4, 5, "red"]]

    s.add_node(
        "ShapeSignature",
        {
            "name": "part_tromino",
            "signature": json.dumps(tromino),
            "kind": "faculty",
            "faculty": "part_tromino",
            "dim_types": dim_types,
        },
    )

    obs1 = s.add_node(
        "Observation",
        {
            "signature": jittered_rot,
            "key": ["k1"],
            "status": "decoded",
            "residual": jittered_rot,
            "decoded_epoch": 0.0,
            "dim_types": dim_types,
        },
    )
    s.add_edge(ag, "observed", obs1)
    s.tick(100_000)
    # At default DimInferPolicy.dim_grains = [0], jittered_rot is not explained by DimInfer
    assert s.node(obs1)["attrs"].get("dim_explained") is False

    # Widen DimInferPolicy.dim_grains to [0, 2] without setting agent.dim_grains
    assert s.node(ag)["attrs"].get("dim_grains") is None
    s.set_attr(pols[0], "dim_grains", [0, 2])

    obs2 = s.add_node(
        "Observation",
        {
            "signature": jittered_rot,
            "key": ["k2"],
            "status": "decoded",
            "residual": jittered_rot,
            "decoded_epoch": 0.0,
            "dim_types": dim_types,
        },
    )
    s.add_edge(ag, "observed", obs2)
    s.tick(100_000)
    assert s.node(obs2)["attrs"].get("dim_explained") is True
    assert s.node(obs2)["attrs"].get("dim_grain") == 2
