"""SENSORY FIELD — the I/O boundary for the GRAPH-NATIVE convolution faculty.

This is the ONLY Python in the convolution path, and it is pure adapter work (CLAUDE.md):
it lays an external 2-D sensory field into the graph as Patch nodes (mechanical translation,
no decision) and reads back convolution RESPONSES by EVALUATING the seed's DSL Term — the
convolution itself runs in Rust (MaxOver + Dot), the kernels are seed data. There is no
convolution math here.

A sense (ear / eye / …) produces a 2-D field (a cochleagram window, an image, any projection);
`lay_field` ingests it; `conv_response` / `field_signature` read the graph-native responses.
"""
from __future__ import annotations

import json

import numpy as np


def lay_field(substrate, field2d, kh=3, kw=3):
    """INGEST: lay a 2-D field as a Field node + flattened kh×kw Patch nodes. Mechanical
    translation of an external array into graph data (substrate.add_node/add_edge). Returns
    the Field node id."""
    M = np.asarray(field2d, dtype=np.float64)
    if M.ndim != 2 or M.shape[0] < kh or M.shape[1] < kw:
        return substrate.add_node("Field", {"rows": 0, "cols": 0})
    field = substrate.add_node("Field", {"rows": int(M.shape[0]), "cols": int(M.shape[1])})
    H, W = M.shape
    for i in range(H - kh + 1):
        for j in range(W - kw + 1):
            p = substrate.add_node("Patch", {"vals": [float(v) for v in M[i:i + kh, j:j + kw].ravel()]})
            substrate.add_edge(field, "has_patch", p)
    return field


def _faculty(substrate):
    return next((n for n in substrate.nodes("ConvFaculty")), None)


def kernels(substrate):
    """The seed's designed convolution kernels (graph data)."""
    fac = _faculty(substrate)
    return list(substrate.neighbours(fac, "has_kernel")) if fac is not None else []


def _response_term(substrate):
    fac = _faculty(substrate)
    return json.loads(substrate.node(fac)["attrs"]["response_term"]) if fac is not None else None


def conv_response(substrate, field, kernel):
    """The convolution response of `field` to `kernel` — computed by the GRAPH-NATIVE DSL Term
    (Rust: MaxOver patches of Dot(kernel.weights, patch.vals)), NOT Python. A pure read-out."""
    term = _response_term(substrate)
    if term is None:
        return 0.0
    return float(substrate._inner.evaluate(term, {"field": field, "k": kernel}))


def field_signature(substrate, field, kernel_ids=None):
    """A field's signature = its graph-native convolution responses to each seed kernel — a
    feature vector assembled from the Term read-outs (the convolution is the graph's)."""
    ks = kernel_ids if kernel_ids is not None else kernels(substrate)
    return [conv_response(substrate, field, k) for k in ks]


def select_kernels(substrate, fields):
    """GRAPH-NATIVE effect-gate. Lay a Sense that `considers` the conv faculty and `has_field`
    each field (the world's affordance), run the seeded `keep_discriminative_kernel` Rule, and
    read back the kernels the Rule KEPT (those whose response spread across the fields is a
    meaningful fraction of the most-varying kernel's). The KEEP decision is the Rule (Rust); this
    only lays the fields and reads the result. `fields` = list of 2-D arrays. Returns Kernel ids."""
    fac = _faculty(substrate)
    if fac is None:
        return []
    sense = substrate.add_node("Sense", {})
    substrate.add_edge(sense, "considers", fac)
    for fld in fields:
        substrate.add_edge(sense, "has_field", lay_field(substrate, fld))
    substrate.add_node("NativeSensoryFieldReceipt", {
        "schema": "native_sensory_field_receipt_v1",
        "cluster": "sensory_field.kernel_selection",
        "provenance": "native_rule_readback:sensory_kernel_selection",
        "native_rule": "keep_discriminative_kernel",
        "native_steps": ["lay_fields", "run_rules", "readback"],
        "outcome_source": "native_rule_readback",
        "python_outcome_selection": False,
    })
    substrate._inner.run_rules(100000)
    return list(substrate.neighbours(sense, "kept_kernel"))


def sense_discrimination(substrate, fields_by_label):
    """GRAPH-NATIVE discrimination. Lay a Sense with LABELLED fields (the world's affordance),
    fire the keep_discriminative_kernel Rule, then evaluate the seed's `discrimination_term`
    (mean between-label minus within-label squared-distance over kept kernels, normalised) — a
    Rust DSL fold. No Python math: the world lays the fields, the GRAPH computes the score.
    `fields_by_label` = {label: [2-D field arrays]}. Returns the scalar + the Sense id."""
    fac = _faculty(substrate)
    if fac is None:
        return 0.0, None
    sense = substrate.add_node("Sense", {})
    substrate.add_edge(sense, "considers", fac)
    for label, arrays in fields_by_label.items():
        for a in arrays:
            f = lay_field(substrate, a)
            substrate.set_attr(f, "label", str(label))
            substrate.add_edge(sense, "has_field", f)
    substrate.add_node("NativeSensoryFieldReceipt", {
        "schema": "native_sensory_field_receipt_v1",
        "cluster": "sensory_field.discrimination",
        "provenance": "native_rule_readback:sensory_discrimination",
        "native_rule": "keep_discriminative_kernel",
        "native_steps": ["lay_labelled_fields", "run_rules", "readback"],
        "outcome_source": "native_rule_readback",
        "python_outcome_selection": False,
    })
    substrate._inner.run_rules(100000)                # the selection Rule fires
    term = substrate.node(fac)["attrs"].get("discrimination_term")
    if not term:
        return 0.0, sense
    return float(substrate._inner.evaluate(json.loads(term), {"sense": sense})), sense


__all__ = ["lay_field", "kernels", "conv_response", "field_signature",
           "select_kernels", "sense_discrimination"]
