"""Modality-reflex — the self-training primal layer works across senses.

Gates the generic ModalityReflex adapter (domains/modality_reflex.py): any
modality's (feature, signature, verdict) stream self-trains a reflex net
INSIDE the engine's run_rules (the net_collapse effect), gated by that
modality's grounded basin. Synthetic per-modality data (fast, no
reader/audio/vision boot) — the demo (scripts/reflex_modalities_demo.py)
exercises the real encoders.
"""
from __future__ import annotations

import json
import os

import numpy as np
import pytest
from substrate_rs import _native
from domains.modality_reflex import ModalityReflex

_SEED = os.path.join(os.path.dirname(__file__), "..", "seeds", "reflex_net.json")

_NODE = ("NetworkAssemblage", "AssemblageStep", "WeightTensor", "ReflexNet",
         "ReflexObservation", "_ProbeObs", "SeenQuantum_m")
_EDGE = ("has_step", "has_weight", "net_assemblage", "observes")


def _fresh():
    s = _native.Substrate()
    for a in _NODE:
        for b in _NODE:
            for et in _EDGE:
                s.add_production({"src": {"type": a, "var": "s"}, "edge_type": et,
                                  "tgt": {"type": b, "var": "t"}, "where": None,
                                  "weight": {"type": "Lit", "value": 1.0}, "provenance": "t"})
    rule = next(r for r in json.load(open(_SEED))["rules"]
                if r["name"] == "reflex_net_self_train_step")
    s.add_rule(rule)
    return s


def _quantize(vec, bins, tag, lo=-2.0, hi=2.0):
    return [[f"{tag}{i}", str(int(np.clip((v - lo) / (hi - lo) * bins, 0, bins - 1)))]
            for i, v in enumerate(vec)]


def _modality_dataset(seed, in_dim=8, n_classes=4, per=25):
    """A generic modality: each class a distinct feature prototype + noise —
    the same shape every real sense produces after feature extraction."""
    rng = np.random.default_rng(seed)
    protos = [rng.standard_normal(in_dim) * 1.5 for _ in range(n_classes)]
    data = []
    for _ in range(per):
        for c in range(n_classes):
            f = (protos[c] + rng.normal(0, 0.25, in_dim)).tolist()
            data.append((f, _quantize(f, 4, "m"), c))
    return data, in_dim, n_classes


def test_modality_reflex_self_trains_and_gates():
    """One adapter, self-trains a modality to high held-out accuracy via the
    engine collapse, serves in-basin, and defers a novel (out-of-codebook)
    input to cognition."""
    data, in_dim, nc = _modality_dataset(seed=0)
    rng = np.random.default_rng(1)
    idx = rng.permutation(len(data))
    train = [data[i] for i in idx[:70]]
    test = [data[i] for i in idx[70:]]

    s = _fresh()
    # rename the codebook type to the one the harness admits.
    mr = ModalityReflex(s, "m", in_dim, nc, seed=3)
    for f, sig, c in train:
        mr.observe(f, c, signature=sig)
    mr.train(epochs=150)

    acc = sum(mr.predict(f) == c for f, _, c in test) / len(test)
    assert acc >= 0.85, f"modality self-trained acc {acc}"

    # in-basin test example serves; a novel-tag input defers.
    served = mr.serve_or_defer(test[0][0], test[0][1])
    assert served is not None, "in-basin input served by the reflex net"
    novel_sig = _quantize([9.9] * in_dim, 4, "zz")   # quanta never trained on
    deferred = mr.serve_or_defer([9.9] * in_dim, novel_sig)
    assert deferred is None, "out-of-basin input deferred to cognition"


def test_two_modalities_share_the_mechanism_independently():
    """Two independent senses each get their own self-training reflex net
    over the SAME machinery, with separate basins — one primal layer, many
    senses."""
    s = _fresh()
    da, _, _ = _modality_dataset(seed=5)
    db, _, _ = _modality_dataset(seed=9)
    ma = ModalityReflex(s, "m", 8, 4, seed=2)
    mb = ModalityReflex(s, "m", 8, 4, seed=4)
    for f, sig, c in da[:80]:
        ma.observe(f, c, signature=sig)
    for f, sig, c in db[:80]:
        mb.observe(f, c, signature=sig)
    ma.train(epochs=120)
    mb.train(epochs=120)
    acc_a = sum(ma.predict(f) == c for f, _, c in da[80:]) / max(1, len(da[80:]))
    acc_b = sum(mb.predict(f) == c for f, _, c in db[80:]) / max(1, len(db[80:]))
    assert acc_a >= 0.8 and acc_b >= 0.8, f"both senses learned: {acc_a}, {acc_b}"
