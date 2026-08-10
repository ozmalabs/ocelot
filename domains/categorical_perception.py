"""Categorical perception seed — Phoneme categories emerge from A1
response clustering.

Biology: in STG (superior temporal gyrus, the part of auditory
cortex above A1), neurons show categorical perception — /b/ vs /p/
becomes a discrete distinction despite the continuous VOT
variable. By 6–12 months, infants' perceptual boundaries sharpen
to whatever language they hear. The categories are LEARNED from
the statistical distribution of inputs, not built-in.

The substrate's analogue:

  Phoneme           emergent cluster centroid in patch-response
                    space. Persistent across runs; accumulates
                    samples and tightens its centroid as more
                    audio is processed.
  PhonemeInstance   one per sampled moment of audio. Carries
                    time_s + confidence + is_a edge to the
                    Phoneme it was assigned to.

Each "moment" is sampled from the A1 patch_evaluate responses at
a fixed interval (default 25 ms ≈ phoneme timescale). The feature
vector has one dimension per A1 patch.

Clustering: online leader-follower. For each new feature vector,
find the nearest existing Phoneme; if distance < threshold,
assign + update centroid via incremental mean. Else mint a new
Phoneme at this vector. No k-specified-upfront, no batch passes,
no NN — same biological story as how infant categories sharpen.

Op type: ``categorical_perception``. Takes feeds_into from every
patch_evaluate op (multi-input) so the runtime can walk all their
buffers + assemble feature vectors.
"""
from __future__ import annotations


_CP_PRODUCTIONS = [
    ("AudioStream", "has_phoneme_instance", "PhonemeInstance",
     "categorical_perception:stream_instance"),
    ("PhonemeInstance", "is_a", "Phoneme",
     "categorical_perception:instance_is_a"),
    ("PhonemeInstance", "from_stream", "AudioStream",
     "categorical_perception:instance_from_stream"),
]


def install_categorical_perception(substrate) -> None:
    """Productions only — Phoneme nodes are minted by the
    categorical_perception op at runtime; the pipeline op itself
    is wired per-stream by attach_categorical_perception."""
    for src_t, et, tgt_t, prov in _CP_PRODUCTIONS:
        try:
            substrate.add_production({
                "src": {"type": src_t, "var": "src"},
                "edge_type": et,
                "tgt": {"type": tgt_t, "var": "tgt"},
                "provenance": prov,
            })
        except Exception:
            pass


def attach_categorical_perception(
    substrate, audio_stream_nid,
    *,
    sample_interval_ms: float = 25.0,
    distance_threshold: float = 0.3,
    min_confidence_to_mint: float = 0.0,
) -> dict:
    """Wire one categorical_perception op consuming every
    patch_evaluate op's output. The op walks the patch responses,
    samples them at fixed intervals, builds feature vectors, and
    clusters against existing Phoneme nodes.

    distance_threshold: cosine-distance gate (0 = identical,
    1 = orthogonal). Below threshold = same category; above =
    mint a new Phoneme.
    """
    patch_eval_ops = [
        op for op in substrate.nodes("Operation")
        if substrate.node(op)["attrs"].get("kind") == "patch_evaluate"
    ]
    if not patch_eval_ops:
        return {"op": None, "patch_count": 0}

    cp_nid = substrate.add_node("Operation", {
        "kind": "categorical_perception",
        "sample_interval_ms": float(sample_interval_ms),
        "distance_threshold": float(distance_threshold),
        "min_confidence_to_mint": float(min_confidence_to_mint),
    })
    for pe in patch_eval_ops:
        substrate.add_edge(pe, "feeds_into", cp_nid)
    return {"op": cp_nid, "patch_count": len(patch_eval_ops)}


__all__ = [
    "install_categorical_perception",
    "attach_categorical_perception",
    "_CP_PRODUCTIONS",
]
