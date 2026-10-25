"""Locked, read-only lexical comparison helpers; labels never enter agent state."""
from __future__ import annotations

from dataclasses import dataclass
import csv
from collections import Counter
import hashlib
import json
from pathlib import Path
from typing import Mapping, Sequence

import numpy as np

from evaluation.ousiometrics.source_manifest import (
    GPADS_V2, NRC_VAD_V1, iter_lexical_ids, lexical_clusters,
    split_lexical_ids, verify_source_bytes,
)

GPADS_PDS_INDICES = (1, 3, 4)  # power, danger, structure; structure high=unstructured.


def pds_target_coordinates(values: Sequence[float]) -> tuple[float, float, float]:
    """Select registered P/D/S coordinates from GPADS' five columns."""
    if len(values) != 5:
        raise ValueError("GPADS row must contain five rated columns")
    return tuple(float(values[index]) for index in GPADS_PDS_INDICES)


@dataclass(frozen=True)
class LexicalAlignment:
    matrix: tuple[tuple[float, ...], ...]
    anchor_ids: tuple[str, ...]
    anchor_digest: str
    split_digest: str
    checkpoint_sha256: str
    bridge_sha256: str
    frozen: bool = True


def _bridge_digest(vectors: Mapping[str, Sequence[float]]) -> str:
    payload = [(str(token), [float(value) for value in vectors[token]])
               for token in sorted(vectors)]
    return hashlib.sha256(json.dumps(payload, separators=(",", ":"),
                                     ensure_ascii=False).encode("utf-8")).hexdigest()


def _valid_sha256(value: str) -> bool:
    return len(value) == 64 and all(char in "0123456789abcdef" for char in value.lower())


def _split_digest(split_by_id: Mapping[str, str]) -> str:
    return hashlib.sha256(json.dumps(sorted((str(token), str(split))
                                            for token, split in split_by_id.items()),
                                     separators=(",", ":"), ensure_ascii=False)
                          .encode("utf-8")).hexdigest()


def split_clustered_ids(ids: Sequence[str], *, namespace: str,
                        synsets_by_id: Mapping[str, Sequence[str]] | None = None) -> dict:
    """Split whole synonym components; route any >10% vocabulary component to train.

    A single giant polysemy-connected component must not dominate anchors or
    held-out lexical coverage. The size guard is identifier-only and fixed
    before score columns are opened.
    """
    clusters = lexical_clusters(ids, synsets_by_id=synsets_by_id)
    assignment = split_lexical_ids(ids, namespace=namespace, synsets_by_id=synsets_by_id)
    sizes = Counter(clusters.values())
    max_component_size = len(clusters) * 0.10
    oversized = sorted(cluster for cluster, count in sizes.items()
                       if count > max_component_size)
    oversized_set = set(oversized)
    for token, cluster in clusters.items():
        if cluster in oversized_set:
            assignment[token] = "train"
    return {"cluster_by_id": clusters, "split_by_id": assignment,
            "oversized_clusters": oversized,
            "max_component_size": max_component_size}


def label_blind_splits(gpads_path: str | Path, vad_path: str | Path, *, namespace: str) -> dict:
    """Verify both payloads and assign whole synonym clusters using IDs only."""
    gpads = verify_source_bytes(gpads_path, GPADS_V2)
    vad = verify_source_bytes(vad_path, NRC_VAD_V1)
    ids = sorted(set(iter_lexical_ids(gpads_path)) & set(iter_lexical_ids(vad_path)))
    allocation = split_clustered_ids(ids, namespace=namespace)
    assignment = allocation["split_by_id"]
    clusters = allocation["cluster_by_id"]
    split_digest = _split_digest(assignment)
    return {"gpads_source": gpads, "vad_source": vad, "namespace": namespace,
            "ids": ids, "cluster_by_id": clusters, "split_by_id": assignment,
            "split_digest": split_digest,
            "oversized_clusters": allocation["oversized_clusters"],
            "oversized_component_size_limit": allocation["max_component_size"],
            "split_ids": {name: sorted(token for token, split in assignment.items() if split == name)
                          for name in ("train", "development", "anchor", "heldout")},
            "scores_loaded": False}


def read_gpads_labels(path: str | Path, *, split_manifest: Mapping, split: str,
                      checkpoint_sha256: str,
                      bridge_sha256: str) -> dict[str, tuple[float, ...]]:
    """Read only one already-frozen split; this module never writes labels to agent state."""
    if not _valid_sha256(checkpoint_sha256) or not _valid_sha256(bridge_sha256):
        raise ValueError("freeze checkpoint and token bridge before opening target scores")
    assignment = split_manifest.get("split_by_id", {})
    if split not in {"train", "development", "anchor", "heldout"}:
        raise ValueError("unknown lexical score split")
    if split_manifest.get("split_digest") != _split_digest(assignment):
        raise ValueError("label-blind split manifest digest mismatch")
    verify_source_bytes(path, GPADS_V2)
    allowed = {token for token, assigned in assignment.items() if assigned == split}
    result = {}
    with Path(path).open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream, delimiter="\t")
        for row in reader:
            word = (row.get("word") or "").strip().casefold()
            if word in allowed:
                result[word] = tuple(float(row[key]) for key in
                                     ("goodness", "power", "aggression", "danger", "structure"))
    return result


def fit_anchor_alignment(vectors: Mapping[str, Sequence[float]],
                         labels: Mapping[str, Sequence[float]], *,
                         anchor_ids: Sequence[str], checkpoint_sha256: str,
                         split_manifest: Mapping) -> LexicalAlignment:
    """Fit orthogonal orientation on the complete preregistered anchor split."""
    assignment = split_manifest.get("split_by_id", {})
    split_digest = split_manifest.get("split_digest")
    if split_digest != _split_digest(assignment):
        raise ValueError("label-blind split manifest digest mismatch")
    registered_anchors = {token for token, split in assignment.items() if split == "anchor"}
    if set(anchor_ids) != registered_anchors:
        raise ValueError("alignment may use only the complete registered anchor split")
    if not _valid_sha256(checkpoint_sha256):
        raise ValueError("frozen checkpoint SHA-256 is required")
    bridge_sha256 = _bridge_digest(vectors)
    common = sorted(registered_anchors & set(vectors) & set(labels))
    missing_anchors = sorted(registered_anchors - set(common))
    if missing_anchors:
        raise ValueError(f"registered anchor concepts missing vectors or scores: {missing_anchors}")
    if len(common) < 3:
        raise ValueError("at least three aligned anchor concepts are required")
    x = np.asarray([vectors[token] for token in common], dtype=np.float64)
    y = np.asarray([pds_target_coordinates(labels[token]) for token in common], dtype=np.float64)
    if x.shape != y.shape or x.ndim != 2 or x.shape[1] != 3:
        raise ValueError("anchor vectors and target coordinates must be three-dimensional")
    if not np.isfinite(x).all() or not np.isfinite(y).all():
        raise ValueError("anchor values must be finite")
    u, _, vt = np.linalg.svd(x.T @ y, full_matrices=False)
    matrix = u @ vt
    digest = hashlib.sha256("\n".join(common).encode("utf-8")).hexdigest()
    return LexicalAlignment(tuple(tuple(float(v) for v in row) for row in matrix),
                            tuple(common), digest, split_digest, checkpoint_sha256,
                            bridge_sha256)


def score_locked_test(vectors: Mapping[str, Sequence[float]],
                      labels: Mapping[str, Sequence[float]], *,
                      test_ids: Sequence[str], alignment: LexicalAlignment,
                      split_manifest: Mapping) -> dict:
    """Score test IDs without refitting and report every absent concept."""
    if (not alignment.frozen or not _valid_sha256(alignment.checkpoint_sha256)
            or not _valid_sha256(alignment.bridge_sha256)):
        raise ValueError("lexical alignment and checkpoint must be frozen")
    assignment = split_manifest.get("split_by_id", {})
    if (split_manifest.get("split_digest") != alignment.split_digest
            or alignment.split_digest != _split_digest(assignment)):
        raise ValueError("score split differs from frozen alignment")
    if _bridge_digest(vectors) != alignment.bridge_sha256:
        raise ValueError("token-to-concept bridge changed after alignment freeze")
    if any(assignment.get(token) != "heldout" for token in test_ids):
        raise ValueError("only preregistered heldout concepts can be scored")
    if set(test_ids) & set(alignment.anchor_ids):
        raise ValueError("anchor and test concepts must be disjoint")
    matrix = np.asarray(alignment.matrix, dtype=np.float64)
    scored, missing, errors = [], [], []
    for token in test_ids:
        if token not in vectors or token not in labels:
            missing.append(token)
            continue
        predicted = np.asarray(vectors[token], dtype=np.float64) @ matrix
        target = np.asarray(pds_target_coordinates(labels[token]), dtype=np.float64)
        if predicted.shape != (3,) or target.shape != (3,) or not np.isfinite(predicted).all() or not np.isfinite(target).all():
            missing.append(token)
            continue
        errors.append(float(np.mean(np.abs(predicted - target))))
        scored.append(token)
    return {"status": "scored" if scored else "unsupported",
            "scored_ids": scored, "missing_ids": list(test_ids) if not scored else missing,
            "requested_count": len(test_ids), "scored_count": len(scored),
            "coverage": len(scored) / max(1, len(test_ids)),
            "mean_absolute_error": float(np.mean(errors)) if errors else None,
            "anchor_digest": alignment.anchor_digest,
            "checkpoint_sha256": alignment.checkpoint_sha256,
            "heldout_labels_entered_training": False}


def lexical_readiness(*, checkpoint_sha256: str | None, vectors_available: bool,
                      bridge_sha256: str | None = None) -> dict:
    if (not checkpoint_sha256 or not _valid_sha256(checkpoint_sha256)
            or not vectors_available or not bridge_sha256 or not _valid_sha256(bridge_sha256)):
        return {"status": "UNSUPPORTED", "reason": "no frozen lexical feature checkpoint/bridge",
                "source_calibration_status": "unresolved", "heldout_opened": False}
    return {"status": "READY_FOR_ANCHOR_ALIGNMENT", "reason": None,
            "checkpoint_sha256": checkpoint_sha256,
            "bridge_sha256": bridge_sha256,
            "source_calibration_status": "published-source-only-unless-reproduced",
            "heldout_opened": False}


__all__ = ["LexicalAlignment", "fit_anchor_alignment", "label_blind_splits",
           "lexical_readiness", "pds_target_coordinates", "read_gpads_labels",
           "score_locked_test", "split_clustered_ids"]
