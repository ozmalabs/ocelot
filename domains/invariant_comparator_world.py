"""INVARIANT COMPARATOR — the world adapter.

`VISION_INVARIANT_COMPARATOR_PREREG.md`. A world adapter and nothing else: it
turns pixels into relation tuples, writes them into the substrate, calls
`run_rules()`, and reads two attributes back. **It makes no comparison over
graph state and takes no branch on one.** The identification decision lives
entirely in `seeds/vision_invariant_comparator.json` (`ic_score` /
`ic_identify`), and the QUOTIENT BY THE TRANSLATION GROUP is that seed's
`MaxOver` / `Argmax` over an orbit held as graph data — not an adapter loop.

Pixel → symbol seam, exactly as `VISION_CROSSFRAME_IDENTITY_PREREG.md` fixed it
and unchanged here: a quantized cell becomes `["cell", r_local, c_local,
"v<q>"]`, region-LOCAL coordinates, ALL cells emitted.

THE FOUR COMPARATORS (§2 of the prereg). Every one of them uses the SAME two
rules and the SAME `covered_count`; they differ ONLY in what is held.

  Q(rho)  ORBIT QUOTIENT. The codebook holds one signature per region. Each
          PROBE is presented as an ObsGroup whose members are the same aperture
          sampled at every translation (dr, dc) with |dr|,|dc| <= rho --
          (2*rho+1)^2 members. The seed's `icg_score` / `icg_identify` take the
          max over the orbit and read the winning member's answer, so the graph
          performs the quotient. **Q(0) IS THE INCUMBENT**, exactly: a group of
          one member at zero shift. rho is the INDEPENDENT VARIABLE.

          (The equivalent construction with the orbit on the CODEBOOK side was
          built first and abandoned on cost, recorded here because the number is
          the useful part: per-candidate `codebook_scope` makes a probe cost
          O(N^2) in codebook size, measured 0.1 s for 16 probes at N=16 and
          10.2 s at N=144 -- an 81x jump for a 9x codebook, extrapolating to
          days at rho=3. Orbiting the PROBE is LINEAR in the orbit and scores
          the identical quantity, max over (region, shift) of covered_count.)
  R       CENTROID REGISTRATION. 16 members; both held and probe tiles are
          re-origined on their own rounded intensity centroid before encoding.
          The one-shot quotient: register, then compare -- no search.
  H       VALUE HISTOGRAM. 16 members, `["hist", "v<q>", count]`. Position-free,
          therefore translation-invariant BY CONSTRUCTION. The MAXIMAL-
          INVARIANCE / ZERO-DISCRIMINATION ANCHOR: the A3 floor preserves the
          value multiset exactly, so H's floor EQUALS H's arm by construction.
          It exists to prove the gate is a real conjunction.

The probe/floor variants (`shuffle_arrangement`, the codebook insertion-order
permutation, the noise tile) are INPUT CONSTRUCTION -- seeded, mechanical data
generation before anything reaches the graph, the same class of work as decoding
a frame. They are not ablations of the agent.
"""
from __future__ import annotations

import json
import math
import random

import numpy as np

DIM_TYPES = ["pred", "coord:r", "coord:c", "val"]

#: Held FIXED at the cross-frame rung's values so every number here is directly
#: comparable to `VISION_CROSSFRAME_IDENTITY_RESULTS.md`. Named as hand-set
#: (§13): neither falls out of anything. NOT swept by this rung -- the
#: cross-frame rung already sensitivity-checked k at {2,4,8} and found the
#: verdict stable, and this rung's independent variable is the orbit radius.
K_LEVELS = 4
REGION = 6
GRID = 24


def quantize(frame, k=K_LEVELS):
    """Uniform k-level quantization on a FIXED ABSOLUTE 0..255 scale.

    Byte-identical to `crossframe_world.quantize` (deliberately NOT per-frame
    min/max, which would normalise away the cross-frame appearance change)."""
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


def region_origins(shape=(GRID, GRID), region=REGION):
    """The (r0, c0) top-left of each tile, in the SAME row-major order as
    `regions_of`. The orbit needs the origins, not just the tiles."""
    h, w = shape
    return [(r0, c0)
            for r0 in range(0, h - h % region, region)
            for c0 in range(0, w - w % region, region)]


def sig_of(tile):
    """A tile as its COMPLETE relation system, in region-local coordinates."""
    return [["cell", int(r), int(c), f"v{int(v)}"]
            for r, row in enumerate(np.asarray(tile))
            for c, v in enumerate(row)]


def centroid_of(tile):
    """The tile's own intensity centroid, ROUNDED TO THE INTEGER LATTICE.

    In-frame coordinates are integer (the frame/continuum invariant): the
    centroid is a continuous quantity computed in the map and immediately
    stepped back onto the lattice, never stored as a float coordinate.
    Returns `(r, c, degenerate)`. `degenerate` is True when the weight sum is
    zero (an all-`v0` tile has no intensity centroid) and the geometric centre
    is used instead -- reported, never silently absorbed (§1.1: an absence off
    a guarded division is evidence of a lookup, not a measurement)."""
    a = np.asarray(tile, float)
    tot = float(a.sum())
    if tot <= 0.0:
        c = (a.shape[0] - 1) / 2.0
        return int(math.floor(c + 0.5)), int(math.floor(c + 0.5)), True
    rs = np.arange(a.shape[0], dtype=float)[:, None]
    cs = np.arange(a.shape[1], dtype=float)[None, :]
    rbar = float((a * rs).sum()) / tot
    cbar = float((a * cs).sum()) / tot
    return (int(math.floor(rbar + 0.5)), int(math.floor(cbar + 0.5)), False)


def sig_registered(tile):
    """R's encoding: `sig_of` with the origin moved to the tile's own centroid.

    A whole-tile translation moves the centroid by the same amount, so these
    coordinates are translation-invariant up to the lattice rounding and up to
    the content the aperture actually retains."""
    r0, c0, _ = centroid_of(tile)
    return [["cell", int(r) - r0, int(c) - c0, f"v{int(v)}"]
            for r, row in enumerate(np.asarray(tile))
            for c, v in enumerate(row)]


def sig_histogram(tile, k=K_LEVELS):
    """H's encoding: the value histogram, position-free. Every level is emitted
    (including zero counts) so the signature length is constant at k."""
    a = np.asarray(tile, int)
    return [["hist", f"v{q}", int((a == q).sum())] for q in range(k)]


ENCODERS = {"cell": sig_of, "registered": sig_registered, "hist": sig_histogram}


def pad_edge(frame, rho):
    """Edge-replicate a frame by `rho` so every orbit member is defined even for
    regions on the frame border. Mechanical; declared in the prereg."""
    if rho <= 0:
        return np.asarray(frame)
    return np.pad(np.asarray(frame), rho, mode="edge")


def orbit_offsets(rho):
    """The translation group elements this codebook quotients by: the Chebyshev
    ball of radius `rho` in Z^2, in a fixed deterministic order."""
    return [(dr, dc)
            for dr in range(-rho, rho + 1)
            for dc in range(-rho, rho + 1)]


def orbit_windows(qsrc_padded, origin, rho, region=REGION, pad=None):
    """ONE probe's translation orbit: the `region x region` window at `origin`
    sampled at every shift in the Chebyshev ball of radius `rho`. `qsrc_padded`
    is already quantized and edge-padded by `pad`, so an unpadded origin
    (r0, c0) sits at (r0+pad, c0+pad). Returns `[(shift_index, tile)]`.

    `pad` is how much the SOURCE was edge-padded and defaults to `rho` -- which
    was this function's original IMPLICIT assumption, and is FALSE whenever the
    probe origin is itself displaced. At the default the index arithmetic below
    is character-for-character the original `r0 + rho + dr`, so every
    zero-displacement call is byte-unchanged.

    THE DEFECT THE GUARD EXISTS TO KILL (found by `verdict_comparator_world`'s
    per-trial reference check, `VISION_VERDICT_RESULTS.md`, and latent here):
    `pad_edge(src, rho)` widens a 24-wide frame to 24+2*rho. A probe presented
    at displacement `d` takes its window at `c0 + d + pad + dc`, which for the
    trailing-edge regions runs off the end once `d + dc > pad - rho`, and
    **numpy CLIPS AN OUT-OF-RANGE SLICE SILENTLY** -- returning 4 columns where
    6 were expected. The tile is then encoded with 24 cells instead of 36.

    Under `covered_count` (a SET OVERLAP) that is invisible: a short window
    merely contributes fewer tuples, and the outside reference, computed over
    the SAME short window, agrees with the graph on a WRONG number. Under a
    NORM it is immediately visible, which is why the verdict rung found it and
    this one never did. It is also a SELECTION bias, not only a score error: a
    window with 24 cells has a lower ceiling than one with 36 and cannot win an
    argmax against it.

    The correct pad is `rho + max|displacement|`. The guard below makes any
    insufficient pad LOUD instead of silent."""
    if pad is None:
        pad = rho
    r0, c0 = origin
    out = []
    for j, (dr, dc) in enumerate(orbit_offsets(rho)):
        rr, cc = r0 + pad + dr, c0 + pad + dc
        tile = qsrc_padded[rr:rr + region, cc:cc + region]
        if tile.shape != (region, region):
            raise ValueError(
                f"TRUNCATED APERTURE at origin {origin} shift {(dr, dc)}: got "
                f"{tile.shape} from a {qsrc_padded.shape} source padded by "
                f"{pad}. Pad by rho + max|displacement|, not by rho.")
        out.append((j, tile))
    return out


def shuffle_arrangement(tile, rng):
    """A3's floor: permute the cell VALUES over the cell POSITIONS. The value
    multiset is preserved EXACTLY; only the arrangement is destroyed."""
    a = np.asarray(tile)
    flat = a.flatten().tolist()
    rng.shuffle(flat)
    return np.asarray(flat, int).reshape(a.shape)


def uniform_noise_tile(rng, k=K_LEVELS, region=REGION):
    """G2's floor stimulus: cell values drawn uniformly, no image behind them."""
    return np.asarray([[rng.randrange(k) for _ in range(region)]
                       for _ in range(region)], int)


def _relset(sig):
    """A signature as a set of hashable relation tuples."""
    return {tuple(r) for r in sig}


def reference_score(probe_sig, cand_sig):
    """REFERENCE R2's kernel, computed OUTSIDE the graph: the number of GOAL
    relations present in the candidate's relation system. This is exactly what
    `ShapeDecode`'s `covered_count` computes for wildcard-free tuples
    (`covered_count = n_goal - |residual|`, and `covers_relation` reduces to
    equality when neither side carries a wildcard), so it is the honest
    reference for EVERY encoder here -- not just the cell one."""
    cs = _relset(cand_sig)
    return sum(1 for r in probe_sig if tuple(r) in cs)


def reference_choice(orbit, codebook_tiles, encoder):
    """REFERENCE R2 (not an arm, not the agent): the same 16-way choice made
    OUTSIDE the graph, as `max over (region, shift) of reference_score`. Exists
    so this rung cannot claim substrate structure that is really a shift-
    tolerant overlap -- the cross-frame rung's prediction 5, carried forward.

    `orbit` is `[(shift_index, tile)]`. Returns
    `(region_index, best_score, n_regions_tied_at_best)`."""
    enc = ENCODERS[encoder]
    csigs = [_relset(enc(t)) for t in codebook_tiles]
    best_per_region = [-1] * len(codebook_tiles)
    for _j, tile in orbit:
        psig = enc(tile)
        for i, cs in enumerate(csigs):
            s = sum(1 for r in psig if tuple(r) in cs)
            if s > best_per_region[i]:
                best_per_region[i] = s
    best = max(best_per_region)
    winners = [i for i, s in enumerate(best_per_region) if s == best]
    return winners[0], best, len(winners)


class InvComparatorWorld:
    """One substrate holding ONE codebook. Ingest: `hold` writes the held
    `XfSignature`s; `present` writes one Observation. `run()` ticks. `read()`
    walks the graph for `identified_as`. Nothing between ingest and read-back
    inspects graph state."""

    def __init__(self, *, arm: bool = True, manifest=None):
        """`manifest` overrides the seed that is loaded. Its ONLY use is the
        gate's dead-instrument control, which loads a deliberately INVERTED copy
        of the seed and requires the mechanism tests to go red (§12.3: a gate
        that has only ever been seen to pass has not been tested). No
        measurement path passes it."""
        from substrate.boot_core import boot_core
        from substrate.seed_loader import manifest_for
        from domains import reflective_faculty as rf

        self.s, self.ag = boot_core()
        self.native = rf._native_eval2(self.s)
        # `shape_decode_loop` supplies the `observed` edge type this seed's
        # rules match on; declared as a depends_on in the manifest.
        rf._ensure_vision_grain_policy(self.s, self.native, self.ag)
        self.native.load_seed_manifest(
            manifest_for("vision_invariant_comparator") if manifest is None
            else manifest, self.ag)
        # §9: the seed ships invcomp=0.0. Arming it is a blind write of a
        # declared measurement flag -- no read, no branch.
        for p in self.s.nodes("InvComparatorParams"):
            self.s.set_attr(p, "invcomp", 1.0 if arm else 0.0)
        self._groups = []
        self.codebook = []
        self.encoder = "cell"

    def hold(self, tiles, order, *, encoder="cell"):
        """Write the held codebook: ONE `XfSignature` per region. `order` is a
        seeded permutation of INSERTION order, so Argmax's tie-breaking cannot
        systematically favour index 0."""
        self.codebook = list(tiles)
        self.encoder = encoder
        enc = ENCODERS[encoder]
        for i in order:
            self.s.add_node("XfSignature", {
                "name": f"r{i:02d}",
                "signature": json.dumps(enc(self.codebook[i])),
                "kind": "faculty", "faculty": f"r{i:02d}",
                "dim_types": DIM_TYPES})

    def present(self, orbit, *, truth: int, tag: str):
        """Present ONE probe as its translation orbit. `orbit` is
        `[(shift_index, tile)]` (a single-element list at rho=0). The group node
        is what the graph answers; the members are what it scores."""
        grp = self.s.add_node("ObsGroup", {"key": [tag], "status": "icg_pending"})
        self.s.add_edge(self.ag, "has_group", grp)
        for j, tile in orbit:
            node = self.s.add_node("Observation", {
                "signature": ENCODERS[self.encoder](tile), "key": [f"{tag}#{j}"],
                "status": "ic_pending", "dim_types": DIM_TYPES})
            self.s.add_edge(self.ag, "observed", node)
            self.s.add_edge(grp, "has_member", node)
        self._groups.append((grp, truth, tag, list(orbit)))
        return grp

    def run(self):
        self.native.run_rules()

    def read(self):
        """Mechanical read-back. The group's `identified_as` is the graph's
        answer; the region index is the `r<NN>` name of the winning codebook
        entry. The reference columns are computed here, OUTSIDE the graph."""
        rows = []
        for grp, truth, tag, orbit in self._groups:
            at = self.s.node(grp)["attrs"]
            said = at.get("identified_as")
            said_idx = None
            if isinstance(said, str) and said.startswith("r"):
                said_idx = int(said[1:3])
            enc = ENCODERS[self.encoder]
            nn_i, nn_score, nn_ties = reference_choice(orbit, self.codebook,
                                                       self.encoder)
            tsig = _relset(enc(self.codebook[truth]))
            true_score = max(
                sum(1 for r in enc(t) if tuple(r) in tsig) for _j, t in orbit)
            rows.append({
                "tag": tag, "truth": truth, "said": said, "said_idx": said_idx,
                "n_orbit": len(orbit),
                "true_score": true_score,
                "true_is_max": bool(true_score == nn_score),
                "icg_max": at.get("icg_max"), "icg_ntied": at.get("icg_ntied"),
                "status": at.get("status"),
                "nn_idx": nn_i, "nn_score": nn_score, "nn_ties": nn_ties})
        return rows
