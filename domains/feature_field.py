"""FEATURE FIELD — the I/O boundary for GRAPH-NATIVE feature discrimination + cue selection.

The world TRANSDUCES a sense into feature vectors (the cue extractors: cochleagram, FFT, …) —
that transduction is the affordance. This adapter lays those features into the graph as
labelled `Exemplar` nodes (and per-cue `CueResp` nodes) and lets the GRAPH decide: the seeded
`feature_discrimination` Term scores label separation, and the `keep_discriminative_cue` Rule
selects which cues earn their place. No Python measurement and no Python selection — the world
lays the features, the graph judges them.
"""
from __future__ import annotations

import json

import numpy as np


def _l2(v):
    v = np.asarray(v, dtype=np.float64).ravel()
    n = np.linalg.norm(v)
    return (v / n).tolist() if n > 1e-9 else v.tolist()


def _disc_faculty(substrate):
    return next((n for n in substrate.nodes("FeatureDisc")), None)


def _ensure(substrate):
    if _disc_faculty(substrate) is None:
        from substrate.seed_loader import manifest_for
        ag = next((n for n in substrate.nodes("Agent")), None) or substrate.add_node("Agent", {})
        try:
            substrate._inner.load_seed_manifest(manifest_for("feature_discrimination"), ag)
        except Exception:
            pass


def discrimination(substrate, features_by_label):
    """GRAPH-NATIVE discrimination of laid features. Lay each label's L2-normalised feature
    vectors as Exemplar nodes (the world's transduced affordance) on a Sense, then evaluate the
    seed's discrimination_term (a Rust DSL fold over Dot-distances). Returns the scalar."""
    _ensure(substrate)
    fac = _disc_faculty(substrate)
    if fac is None:
        return 0.0
    sense = substrate.add_node("Sense", {})
    for label, feats in features_by_label.items():
        for f in feats:
            e = substrate.add_node("Exemplar", {"feat": _l2(f), "label": str(label)})
            substrate.add_edge(sense, "has_exemplar", e)
    term = substrate.node(fac)["attrs"].get("discrimination_term")
    if not term:
        return 0.0
    return float(substrate._inner.evaluate(json.loads(term), {"sense": sense}))


def select_cues(substrate, cue_feats_by_label):
    """GRAPH-NATIVE cue selection (the effect-gate as a Rule, not a Python loop).
    `cue_feats_by_label` = {label: [ {cue_id: feat_vec} per exemplar ]}. Lays a CueGate that
    `probes` one CueProbe per cue, each CueProbe `has_exemplar` that cue's labelled responses
    (the world's transduced affordance). Fires the seeded `keep_discriminative_cue` Rule — which
    KEEPS a cue whose per-cue label-discrimination exceeds the mean across cues — and reads back
    the kept cue ids. The KEEP decision is the Rule; the world only lays the responses."""
    _ensure(substrate)
    if _disc_faculty(substrate) is None:
        return []
    cue_ids = list({c for exs in cue_feats_by_label.values() for d in exs for c in d})
    gate = substrate.add_node("CueGate", {})
    probe_of = {}
    for cue in cue_ids:
        probe = substrate.add_node("CueProbe", {"cue_id": str(cue)})
        substrate.add_edge(gate, "probes", probe)
        probe_of[cue] = probe
        for label, exs in cue_feats_by_label.items():
            for d in exs:
                if cue in d:
                    e = substrate.add_node("Exemplar", {"feat": _l2(d[cue]), "label": str(label)})
                    substrate.add_edge(probe, "has_exemplar", e)
    substrate.add_node("NativeFeatureFieldReceipt", {
        "schema": "native_feature_field_receipt_v1",
        "cluster": "feature_field.cue_selection",
        "provenance": "native_rule_readback:feature_cue_selection",
        "native_rule": "keep_discriminative_cue",
        "native_steps": ["lay_cue_exemplars", "run_rules", "readback"],
        "outcome_source": "native_rule_readback",
        "python_outcome_selection": False,
    })
    substrate._inner.run_rules(100000)               # keep_discriminative_cue fires
    kept_probes = set(substrate.neighbours(gate, "kept_cue"))
    return [cue for cue, pr in probe_of.items() if pr in kept_probes]


__all__ = ["discrimination", "select_cues"]
