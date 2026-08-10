"""Modality-reflex — the self-training primal layer for ANY sense.

The primal layer is modality-agnostic: every modality in this substrate
quantizes to a SIGNATURE (the "dynamic quantization is the core loop"
thesis — ink → StrokeQuantize seg relations, vision → space/percept
quanta, language → sentence relations, speech → acoustic signs). So a
reflex net + basin gate + self-training-by-collapse is ONE mechanism over
signatures; a modality plugs in by supplying, per example:

  * a FEATURE vector  (the net's numeric input),
  * a SIGNATURE       (relation tuples — the basin gate decodes these),
  * a VERDICT class   (what its cognition decided — the training target).

This adapter is mechanical host I/O only: it mints the net, ingests
observations, ticks (the ENGINE's run_rules does the collapse via the
net_collapse effect — Python never calls net_collapse_step in the loop),
and reads predictions back. Every DECISION is a seed rule
(reflex_net_self_train_step / reflex_self_train_converged / the basin
gate). One class per modality; the same class serves all four senses.
"""
from __future__ import annotations

import json

import numpy as np


def _nid(x):
    return x.value if hasattr(x, "value") else int(x)


class ModalityReflex:
    """A self-training reflex net for one modality, driven at the engine
    level. `substrate` is a native Substrate with the reflex_net seed rules
    installed (reflex_net_self_train_step) and the modality's node/edge
    types admissible."""

    def __init__(self, substrate, name, in_dim, n_classes, *,
                 hidden=200, seed=1, w1_scale=1.2):
        self.s = substrate
        self.name = name
        self.n_classes = n_classes
        self._seen = set()          # basin codebook (part names)
        rng = np.random.default_rng(seed)

        # Fixed random ReLU feature layer + ZERO readout — untrained.
        asm = substrate.add_node("NetworkAssemblage",
                                 {"input_dim": in_dim, "output_dim": n_classes})
        sid = substrate.add_node("AssemblageStep",
                                 {"order": 0, "dim_behavior": "transform"})
        substrate.add_edge(asm, "has_step", sid, {})
        w = {"W1": (rng.standard_normal((hidden, in_dim)) * w1_scale).tolist(),
             "b1": (rng.standard_normal(hidden) * 0.3).tolist(),
             "W2": [[0.0] * hidden for _ in range(n_classes)],
             "b2": [0.0] * n_classes}
        for role, dat in w.items():
            wt = substrate.add_node("WeightTensor", {"role": role, "data": dat})
            substrate.add_edge(sid, "has_weight", wt, {})
        self.asm = asm
        self.nid = _nid(asm)

        # The self-training reflex net wrapping the assemblage.
        rn = substrate.add_node("ReflexNet", {
            "name": name, "status": "self_training", "enabled": 0.0,
            "eta": 0.5, "converge_tol": 0.01, "basin_codebook": f"SeenQuantum_{name}",
        })
        substrate.add_edge(rn, "net_assemblage", asm, {})
        self.rn = rn
        self._obs = []

    # -- ingest (mechanical) --------------------------------------------
    def _onehot(self, c):
        y = [0.0] * self.n_classes
        y[int(c)] = 1.0
        return y

    def observe(self, feature, cls, signature=None):
        """Ingest one (feature, verdict) observation as a graph node the
        ENGINE trains on; optionally grow the basin from its signature."""
        o = self.s.add_node("ReflexObservation", {
            "status": "pending",
            "input_vec": [float(v) for v in feature],
            "target": self._onehot(cls)})
        self.s.add_edge(o, "observes", self.rn, {})
        self._obs.append(o)
        if signature is not None:
            self.grow_basin(signature)
        return o

    def grow_basin(self, signature):
        """Add each novel quantum of a signature to the modality's basin
        codebook (cognition teaches the cache what it knows)."""
        cb_type = self.s.node(self.rn)["attrs"]["basin_codebook"]
        for rel in signature:
            key = "|".join(str(x) for x in rel)
            if key not in self._seen:
                self.s.add_node(cb_type, {"name": key,
                                          "signature": json.dumps([list(rel)])})
                self._seen.add(key)

    # -- train: the ENGINE collapses (no Python net_collapse_step) -------
    def train(self, epochs=150, eta0=0.5):
        """Self-train via the engine: each epoch resets observations to
        pending and ticks; run_rules fires the net_collapse effect per
        observation and collapses the weights toward reducing surprise."""
        for epoch in range(epochs):
            self.s.set_attr(self.rn, "eta", eta0 / (1.0 + 0.03 * epoch))
            for o in self._obs:
                self.s.set_attr(o, "status", "pending")
            self.s.run_rules()
        return float(self.s.node(self.rn)["attrs"].get("surprise", 0.0))

    # -- serve + gate (fast) --------------------------------------------
    def predict(self, feature):
        """The fast serve: native forward + argmax = the reflex verdict."""
        out = self.s.net_forward(self.nid, [float(v) for v in feature])
        return int(np.argmax(out))

    def basin_residual(self, signature):
        """The grounded basin gate: how many of this input's quanta are NOT
        in the modality's codebook (0 = in the known basin, defer if > 0)."""
        cb_type = self.s.node(self.rn)["attrs"]["basin_codebook"]
        g = self.s.add_node("_ProbeObs", {"signature": [list(r) for r in signature]})
        # max_steps must be >= signature length: each single-quantum part
        # covers one relation per step, so a short cap would floor the
        # residual at (len - cap) even for a fully-seen input.
        steps = max(8, len(signature) + 4)
        term = {"type": "Count", "source": {
            "type": "ShapeDecode",
            "goal": {"type": "Attr", "node": {"type": "Var", "name": "g"}, "key": "signature"},
            "codebook_type": cb_type, "beam": 3, "max_steps": steps, "cand_k": 3,
            "field": "residual", "wild": "·?·", "wild_objects": False}}
        return int(self.s.evaluate(term, {"g": g}))

    def serve_or_defer(self, feature, signature, *, basin_frac=0.4):
        """In-basin → the reflex verdict (fast); otherwise DEFER to
        cognition (return None). Basin membership is RELATIVE: serve iff the
        fraction of the input's quanta the codebook does not cover is below
        `basin_frac` (a familiar input shares most quanta with what the net
        was trained on; a novel one does not). This is the grounded gate —
        the net's confidence is never consulted."""
        if not signature:
            return None
        residual = self.basin_residual(signature)
        if residual / len(signature) < basin_frac:
            return self.predict(feature)
        return None
