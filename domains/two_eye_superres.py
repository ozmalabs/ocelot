"""Two-eye multi-look super-resolution — a mechanical fusion harness (Rung 5).

NO agent decisions, NO graph-state conditionals. This module does exactly two
world-adapter things:

  1. INGEST — build a `GraphEye`, sample a flat textured surface at the eye's
     receptor positions (each column at `i + offset`, a KNOWN sub-receptor
     displacement), submit the photons, drive the engine, read each receptor's
     transduced `activation` back out. Mechanical text-to-graph-to-value.

  2. FUSE — pack the two eyes' (position, activation) sample cloud + the
     reconstruction parameters into ONE `multilook_superres` CognitiveTask on a
     retina that has loaded the `retinal_superres` seed, drive the engine, read
     the minted `SuperResolvedField` back out.

The FUSION DECISION — the band-limited least-squares de-aliasing reconstruction —
is the Rust `multilook_superres` kernel + the `retinal_mint_superres` graph rule.
This module never reconstructs anything; it packs a payload and reads a node.

The eyes are used ONLY through `GraphEye`'s public default (no-flag) path, so
rungs 1-4 / 166000 / 170000 are byte-untouched: this module ADDS a fusion
substrate beside them, it edits none of them.
"""
from __future__ import annotations

import substrate_rs as srs

from domains.photon_eye import GraphEye, _add_edge, _RECEPTORS
from substrate.seed_loader import manifest_for

ROD_CENTER_NM = _RECEPTORS["rod"][0]   # 498.0 — sample at the rod peak so the
#                                        spectral gaussian factor is 1 and the
#                                        transduced sample is a clean function of
#                                        photon count (no spectral confound).


def sample_eye(texture_fn, *, n_az, offset, exposure=1.0, adapt_rate=0.0):
    """Build a `GraphEye`, view a flat textured surface offset by `offset`
    receptors, and return `(positions, activations)`.

    `texture_fn(x)` is the surface luminance at world position `x` (receptor
    units); column `i` sees position `x_i = i + offset`. Photon count at column
    `i` is `round(exposure * texture_fn(x_i))` (integer packets — real photon
    quantisation). Returns the per-column world positions and the receptors'
    transduced `activation`s — the eye's samples of the surface.

    `adapt_rate=0.0` freezes the adapting floor so a single static exposure reads
    the pure Naka-Rushton transduction (a static flat wall, no motion) — the
    receptor's sample is a deterministic function of its own photon count.
    """
    eye = GraphEye(
        n_az=n_az, adapt_rate=adapt_rate,
        context={"synchronous": True, "worker_capacity": 1})
    eye.build()
    positions = [float(i) + float(offset) for i in range(n_az)]
    packets = []
    for i, x in enumerate(positions):
        count = int(round(max(0.0, float(exposure) * float(texture_fn(x)))))
        packets.append({"column": i, "wavelength_nm": ROD_CENTER_NM, "count": count})
    eye.submit_photons(packets)
    eye.substrate._inner.add_node("NativeTwoEyeSuperresReceipt", {
        "schema": "native_two_eye_superres_receipt_v1",
        "cluster": "two_eye_superres.sample_settlement",
        "provenance": "native_cycle_readback:two_eye_superres",
        "native_rule": "two_eye_superres_native_sampling_rules",
        "native_steps": ["submit_photons", "run_cognitive_tasks", "run_rules", "readback"],
        "outcome_source": "native_cycle_readback",
        "python_outcome_selection": False,
    })
    eye.substrate._inner.run_cognitive_tasks(1)
    eye.substrate._inner.run_rules()
    activations = []
    for i in range(n_az):
        rod = eye._receptors[(i, "rod")]
        activations.append(float(eye.substrate.node(rod)["attrs"].get("activation", 0.0)))
    eye.stop()
    return positions, activations


class SuperResFuser:
    """Owns a small fusion substrate with the `retinal_superres` seed loaded.

    `enabled=0.0` on the params node is the OFF gate (the mint rule cannot
    fire) — the seed is inert without an opted-in `SuperresParams`.
    """

    def __init__(self, *, enabled=True):
        self.substrate = srs.Substrate()
        self.agent = self.substrate.add_node("Agent", {"role": "superres_root"})
        self.substrate._inner.load_seed_manifest(
            manifest_for("retinal_superres"), self.agent)
        self.retina = self.substrate.add_node("Retina", {"name": "superres_fuser"})
        self.params = self.substrate.add_node(
            "SuperresParams", {"enabled": 1.0 if enabled else 0.0})
        _add_edge(self.substrate._inner, self.retina,
                  "has_superres_params", self.params)

    def fuse(self, positions, values, *, n_fine, period, ridge, k_max):
        """Pack the sample cloud into a `multilook_superres` task, run the
        engine + rules, and return the minted reconstruction (list of `n_fine`
        floats), or `None` if nothing minted (the OFF gate)."""
        assert len(positions) == len(values)
        payload = [float(n_fine), float(period), float(ridge),
                   float(k_max), float(len(positions))]
        for x, y in zip(positions, values):
            payload.extend([float(x), float(y)])
        task = self.substrate.add_node("CognitiveTask", {
            "status": "requested", "kind": "multilook_superres",
            "payload": payload, "input_epoch": 1, "logical_time": 0,
            "area": "retina", "order": 3, "salience": 1.0})
        _add_edge(self.substrate._inner, self.retina, "has_superres_task", task)
        self.substrate._inner.add_node("NativeTwoEyeSuperresReceipt", {
            "schema": "native_two_eye_superres_receipt_v1",
            "cluster": "two_eye_superres.fusion_settlement",
            "provenance": "native_rule_readback:two_eye_superres_fusion",
            "native_rule": "two_eye_superres_native_fusion_rules",
            "native_steps": ["mint_fusion_task", "run_cognitive_tasks", "run_rules", "readback"],
            "outcome_source": "native_rule_readback",
            "python_outcome_selection": False,
        })
        self.substrate._inner.run_cognitive_tasks(1)
        self.substrate._inner.run_rules()
        return self.read_field()

    def read_field(self):
        """Read the minted `SuperResolvedField` reconstruction back out
        (mechanical emit). `reconstruction[0]` is `n_fine`; the rest is the
        reconstructed field."""
        for node in self.substrate.nodes("SuperResolvedField"):
            attrs = self.substrate.node(node)["attrs"]
            recon = list(attrs.get("reconstruction") or [])
            if not recon:
                return None
            return [float(v) for v in recon[1:]]
        return None
