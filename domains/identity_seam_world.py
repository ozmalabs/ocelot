"""THE PERCEPT->IDENTITY SEAM — the world adapter.

`VISION_IDENTITY_SEAM_PREREG.md`. A world adapter and nothing else: it turns
pixels into relation tuples and unit-centred vectors, writes them into the
substrate, calls `run_rules()`, and reads attributes back. **It makes no
comparison over graph state and takes no branch on one.** Which held identity an
observation is, and whether it is novel enough to mint, are decided entirely by
`seeds/vision_identity_seam.json` (arm B) or by the STOCK `shape_decode_loop` +
`vision_sdloop` (arm A).

The probe construction below (noise draws, value shuffles, the shuffled-frame
floor, the codebook insertion order) is INPUT CONSTRUCTION -- seeded, mechanical
data generation before anything reaches the graph, the same class of work as
decoding a frame. It is not an ablation of the agent.

Encoding is shared with `crossframe_world` (the `["cell", r, c, "v<q>"]`
signature) and `verdict_comparator_world` (the `nvals` unit-centred vector), so
both arms see byte-identical pixels and the numbers are comparable to both
rungs.
"""
from __future__ import annotations

import math

import numpy as np

from domains.crossframe_world import (  # noqa: F401  (re-exported)
    DIM_TYPES, GRID, K_LEVELS, REGION, quantize, regions_of, sig_of,
    shuffle_arrangement,
)


def unit_centered(vals):
    """Mean-centre and scale to unit L2 norm.

    A `Dot` of two such vectors IS normalized cross-correlation, which is why
    the seed's verdict is one `Dot` and contains no Sqrt and no guarded
    division. A flat (zero-variance) tile returns the ZERO vector, so its Dot is
    exactly 0.0 -- "no evidence" rather than a divide-by-zero. Verbatim from
    `verdict_comparator_world`, deliberately unmodified."""
    n = len(vals)
    m = sum(vals) / n
    c = [v - m for v in vals]
    mag = math.sqrt(sum(x * x for x in c))
    if mag <= 0.0:
        return [0.0] * n, True
    return [x / mag for x in c], False


def encode(qtile, gtile):
    """One tile in BOTH arms' encodings at once, so the arms provably cannot
    differ in their input (the verdict rung's construction)."""
    nv, flat = unit_centered([float(v) for v in np.asarray(gtile).ravel()])
    return {"signature": sig_of(qtile), "dim_types": DIM_TYPES,
            "nvals": nv, "nflat": 1.0 if flat else 0.0}


def grey_regions_of(gframe, region=REGION):
    """Tile a RAW GREY frame, in the same row-major order as `regions_of`."""
    h, w = np.asarray(gframe).shape
    return [np.asarray(gframe)[r0:r0 + region, c0:c0 + region]
            for r0 in range(0, h - h % region, region)
            for c0 in range(0, w - w % region, region)]


def mean_abs_diff(a, b):
    """CLAUSE 2's "genuinely different" statistic, computed OUTSIDE the graph in
    raw grey. Deliberately NOT NCC: NCC is the comparator under test, and using
    it to decide which pairs are genuinely different would be the self-check
    this arc has been bitten by three times."""
    return float(np.mean(np.abs(np.asarray(a, float) - np.asarray(b, float))))


def otsu(vals):
    """The cut split (protocol section 13: NO free parameter). Verbatim
    Otsu on the corpus's own per-step motion distribution."""
    v = np.asarray(vals, float)
    lo, hi = float(v.min()), float(v.max())
    if hi <= lo:
        return hi + 1.0
    best_t, best_var = hi + 1.0, -1.0
    for t in np.linspace(lo, hi, 256):
        a, b = v[v <= t], v[v > t]
        if a.size == 0 or b.size == 0:
            continue
        w0, w1 = a.size / v.size, b.size / v.size
        between = w0 * w1 * (a.mean() - b.mean()) ** 2
        if between > best_var:
            best_var, best_t = between, float(t)
    return best_t


class SeamWorld:
    """One substrate holding ONE GROWING codebook.

    `arm="stock"` installs nothing beyond `shape_decode_loop` + `vision_sdloop`
    and presents observations in the form those rules already read. `arm="ncc"`
    additionally installs `vision_identity_seam` and arms it. Nothing between
    ingest and read-back inspects graph state."""

    def __init__(self, arm: str):
        from substrate.boot_core import boot_core
        from substrate.seed_loader import manifest_for
        from domains import reflective_faculty as rf

        assert arm in ("stock", "ncc")
        self.arm = arm
        self.s, self.ag = boot_core()
        self.native = rf._native_eval2(self.s)
        rf._ensure_shape_decode_loop(self.s, self.native, self.ag)
        self.native.load_seed_manifest(manifest_for("vision_sdloop"), self.ag)
        if arm == "ncc":
            self.native.load_seed_manifest(
                manifest_for("vision_identity_seam"), self.ag)
            # Section 9: the seed ships seam=0.0. Arming it is a blind write of
            # a declared measurement flag -- no read, no branch.
            for p in self.s.nodes("IdentitySeamParams"):
                self.s.set_attr(p, "seam", 1.0)
        self._obs = []

    # ------------------------------------------------------------- ingest
    def _pending_status(self):
        return "is_pending" if self.arm == "ncc" else "pending"

    def present(self, qtile, gtile, *, tag: str, probe_kind: str = ""):
        e = encode(qtile, gtile)
        attrs = {"signature": e["signature"], "dim_types": e["dim_types"],
                 "nvals": e["nvals"], "nflat": e["nflat"],
                 "key": [tag], "status": self._pending_status(), "vq": 1}
        if probe_kind:
            attrs["probe_kind"] = probe_kind
            attrs["calib_epoch"] = -1.0
        node = self.s.add_node("Observation", attrs)
        self.s.add_edge(self.ag, "observed", node)
        self._obs.append((node, tag))
        return node

    def calibrate(self, rng, n_probes: int):
        """Install the G2c calibration-noise probes that MEASURE the floor.

        Arm B only: the stock loop has no floor to measure, and that absence is
        this rung's clause-3 finding rather than something to paper over."""
        if self.arm != "ncc":
            return 0
        for j in range(n_probes):
            q = rng.randint(0, K_LEVELS, (REGION, REGION))
            g = rng.randint(0, 256, (REGION, REGION)).astype(float)
            self.present(q, g, tag=f"G2c_{j}", probe_kind="G2c")
        return n_probes

    def run(self):
        self.native.run_rules()

    # ------------------------------------------------------------ readback
    def codebook_size(self):
        """Held identities GROWN FROM PIXELS. Counted the same way in both arms
        (`vq_grown` for the stock loop, `seam_grown` for arm B) so the mint
        trajectories are directly comparable and neither counts boot residue."""
        n = 0
        for sid in self.s.nodes("ShapeSignature"):
            at = self.s.node(sid)["attrs"]
            if at.get("vq_grown") == 1.0 or at.get("seam_grown") == 1.0:
                n += 1
        return n

    def read_last(self):
        node, tag = self._obs[-1]
        at = self.s.node(node)["attrs"]
        # ARM A's identity is `covered_by` (sd_recognize's Argmax); a minting
        # observation takes its own new name, which the stock loop writes as
        # the grown signature's name = the observation's own key.
        if self.arm == "stock":
            ident = at.get("covered_by")
            if ident is None and at.get("status") == "minted":
                ident = tag
        else:
            ident = at.get("identified_as")
        return {"tag": tag, "status": at.get("status"), "identity": ident,
                "is_max": at.get("is_max"), "is_floor": at.get("is_floor"),
                "covered_count": at.get("covered_count"),
                "residual_len": len(at.get("residual") or [])}
