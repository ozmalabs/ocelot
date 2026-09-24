"""CROSS-FRAME IDENTITY — the world adapter.

`VISION_CROSSFRAME_IDENTITY_PREREG.md`. A world adapter and nothing else: it
turns pixels into relation tuples, writes them into the substrate, calls
`run_rules()`, and reads one attribute back. **It makes no comparison over graph
state and takes no branch on one.** The 16-way identification decision lives
entirely in `seeds/vision_crossframe_identity.json` (`xf_score` / `xf_identify`).

The probe/floor variants below (`shuffle_arrangement`, the codebook order
permutation) are INPUT CONSTRUCTION — seeded, mechanical data generation before
anything reaches the graph, the same class of work as decoding a frame. They are
not ablations of the agent and they are not conditionals over what the agent
believes.

Pixel → symbol seam, exactly as `VISION_VIDEO_PROBE_RESULTS.md` §2.4b forced it:
a quantized cell becomes `["cell", r_local, c_local, "v<q>"]`. Region-LOCAL
coordinates (absolute ones would let a probe match by POSITION alone) and ALL
cells emitted (no background threshold, so signature length is constant and
`covered_count` is a clean 0..N overlap).
"""
from __future__ import annotations

import json
import random

import numpy as np

DIM_TYPES = ["pred", "coord:r", "coord:c", "val"]

#: The two hand-set numbers of this rung, named as such (§13 — neither falls out
#: of anything). Swept / sensitivity-checked, never tuned.
K_LEVELS = 4
REGION = 6
GRID = 24


def quantize(frame, k=K_LEVELS):
    """Uniform k-level quantization on a FIXED ABSOLUTE 0..255 scale.

    Deliberately NOT per-frame min/max (which `video_probe_measure._quantize`
    uses): a per-frame adaptive scale would silently normalise away exactly the
    cross-frame appearance change under test."""
    f = np.clip(np.asarray(frame, float), 0.0, 255.0)
    return np.clip((f / 256.0 * k).astype(int), 0, k - 1)


def regions_of(qframe, region=REGION):
    """Tile a quantized frame into row-major (region x region) tiles."""
    h, w = qframe.shape
    out = []
    for r0 in range(0, h - h % region, region):
        for c0 in range(0, w - w % region, region):
            out.append(qframe[r0:r0 + region, c0:c0 + region])
    return out


def sig_of(tile):
    """A tile as its COMPLETE relation system, in region-local coordinates."""
    return [["cell", int(r), int(c), f"v{int(v)}"]
            for r, row in enumerate(np.asarray(tile))
            for c, v in enumerate(row)]


def shuffle_arrangement(tile, rng):
    """A3's floor: permute the cell VALUES over the cell POSITIONS. The value
    multiset is preserved EXACTLY; only the arrangement is destroyed."""
    a = np.asarray(tile)
    flat = a.flatten().tolist()
    rng.shuffle(flat)
    return np.asarray(flat, int).reshape(a.shape)


def hamming_nn(probe_tile, codebook_tiles):
    """REFERENCE R1 (not an arm, not the agent): the same 16-way choice made
    OUTSIDE the graph by maximum exact-cell overlap. Exists so this rung cannot
    claim substrate structure that is really Hamming distance."""
    p = np.asarray(probe_tile)
    scores = [int((p == np.asarray(t)).sum()) for t in codebook_tiles]
    best = max(scores)
    return scores.index(best), best, scores.count(best)


class CrossFrameWorld:
    """One substrate holding ONE codebook (the 16 regions of one base frame).

    Ingest: `hold_codebook` writes the held ShapeSignatures; `present` writes one
    Observation. `run()` ticks. `read()` walks the graph for `identified_as`.
    Nothing between ingest and read-back inspects graph state."""

    def __init__(self, *, arm: bool = True):
        from substrate.boot_core import boot_core
        from substrate.seed_loader import manifest_for
        from domains import reflective_faculty as rf

        self.s, self.ag = boot_core()
        self.native = rf._native_eval2(self.s)
        # `shape_decode_loop` supplies the `observed` edge type this seed's
        # rules match on; declared as a depends_on in the manifest.
        rf._ensure_shape_decode_loop(self.s, self.native, self.ag)
        self.native.load_seed_manifest(
            manifest_for("vision_crossframe_identity"), self.ag)
        # §9: the seed ships crossframe=0.0. Arming it is a blind write of a
        # declared measurement flag -- no read, no branch.
        for p in self.s.nodes("CrossFrameParams"):
            self.s.set_attr(p, "crossframe", 1.0 if arm else 0.0)
        self._probes = []

    def hold_codebook(self, tiles, order):
        """Write the held regions. `order` is a seeded permutation of insertion
        order, so Argmax's tie-breaking cannot systematically favour index 0."""
        self.tiles = list(tiles)
        for i in order:
            self.s.add_node("ShapeSignature", {
                "name": f"r{i:02d}", "signature": json.dumps(sig_of(tiles[i])),
                "kind": "faculty", "faculty": f"r{i:02d}", "dim_types": DIM_TYPES})

    def present(self, tile, *, truth: int, tag: str):
        node = self.s.add_node("Observation", {
            "signature": sig_of(tile), "key": [tag], "status": "xf_pending",
            "dim_types": DIM_TYPES})
        self.s.add_edge(self.ag, "observed", node)
        self._probes.append((node, truth, tag, np.asarray(tile)))
        return node

    def run(self):
        self.s.add_node("NativeCrossFrameReceipt", {
            "schema": "native_crossframe_receipt_v1",
            "cluster": "crossframe_world.identity_settlement",
            "provenance": "native_rule_readback:crossframe_identity",
            "native_rule": "crossframe_identity_native_rules",
            "native_steps": ["present_observations", "run_rules", "readback"],
            "outcome_source": "native_rule_readback",
            "python_outcome_selection": False,
        })
        self.native.run_rules()

    def read(self):
        """Mechanical read-back. `identified_as` is the graph's answer; the
        Hamming-NN column is computed here, outside the graph, as REFERENCE R1."""
        rows = []
        for node, truth, tag, tile in self._probes:
            at = self.s.node(node)["attrs"]
            said = at.get("identified_as")
            nn_i, nn_score, nn_ties = hamming_nn(tile, self.tiles)
            # The TRUE region's own overlap. With it, "did the true region even
            # ACHIEVE the maximum score" is separable from "did the arbitrary
            # tie-break land on it" -- so a top-1 number deflated by ties is
            # visible as a bound rather than read as a discrimination.
            true_score = int((tile == np.asarray(self.tiles[truth])).sum())
            rows.append({
                "tag": tag, "truth": truth, "said": said,
                "true_score": true_score, "true_is_max": bool(true_score == nn_score),
                "said_idx": (int(said[1:]) if isinstance(said, str)
                             and said.startswith("r") else None),
                "xf_max": at.get("xf_max"), "xf_ntied": at.get("xf_ntied"),
                "status": at.get("status"),
                "nn_idx": nn_i, "nn_score": nn_score, "nn_ties": nn_ties})
        return rows


def uniform_noise_tile(rng, k=K_LEVELS, region=REGION):
    """G2's floor stimulus: cell values drawn uniformly, no image behind them."""
    return np.asarray([[rng.randrange(k) for _ in range(region)]
                       for _ in range(region)], int)
