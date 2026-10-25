"""Source split, anchor isolation, and missing lexical-bridge controls."""
from dataclasses import replace
import hashlib
import json

import pytest

from evaluation.ousiometrics.lexical_validation import (
    fit_anchor_alignment, lexical_readiness, pds_target_coordinates,
    read_gpads_labels, score_locked_test,
)
import evaluation.ousiometrics.lexical_validation as lexical_module
from evaluation.ousiometrics.source_manifest import split_lexical_ids
from evaluation.ousiometrics.lexical_validation import split_clustered_ids


def _split_manifest():
    assignment = {"a": "anchor", "b": "anchor", "c": "anchor",
                  "test": "heldout", "missing-1": "heldout", "missing-2": "heldout"}
    digest = hashlib.sha256(json.dumps(sorted(assignment.items()), separators=(",", ":"),
                                       ensure_ascii=False).encode()).hexdigest()
    return {"split_by_id": assignment, "split_digest": digest}


def _sha(value):
    return hashlib.sha256(value.encode()).hexdigest()


def _align(vectors, labels):
    return fit_anchor_alignment(vectors, labels, anchor_ids=("a", "b", "c"),
                                checkpoint_sha256=_sha("frozen-checkpoint"),
                                split_manifest=_split_manifest())


def test_external_scores_not_training_input():
    first = split_lexical_ids(("kind", "harm", "safe"), namespace="p28-test",
                              synsets_by_id={"kind": (), "harm": (), "safe": ()})
    # Target score values are deliberately changed; the ID-only splitter has no
    # score parameter and therefore produces the same assignment.
    target_scores_a = {"kind": (0.1, 0.2, 0.3), "harm": (0.9, 0.8, 0.7)}
    target_scores_b = {"kind": (0.9, 0.8, 0.7), "harm": (0.1, 0.2, 0.3)}
    second = split_lexical_ids(("kind", "harm", "safe"), namespace="p28-test",
                               synsets_by_id={"kind": (), "harm": (), "safe": ()})
    assert target_scores_a != target_scores_b
    assert first == second
    assert set(first) == {"kind", "harm", "safe"}


def test_related_concepts_share_split():
    splits = split_lexical_ids(("safe", "secure", "harm"), namespace="p28-test",
                               synsets_by_id={"safe": ("syn:1",), "secure": ("syn:1",),
                                              "harm": ("syn:2",)})
    assert splits["safe"] == splits["secure"]


def test_oversized_connected_component_is_kept_out_of_anchor_and_test():
    ids = tuple(f"word-{index}" for index in range(10))
    synsets = {token: (("giant-family",) if index < 3 else ())
               for index, token in enumerate(ids)}
    allocation = split_clustered_ids(ids, namespace="p28-mass-guard",
                                     synsets_by_id=synsets)
    giant = {f"word-{index}" for index in range(3)}
    assert len(allocation["oversized_clusters"]) == 1
    assert {allocation["split_by_id"][token] for token in giant} == {"train"}


def test_anchor_labels_not_in_test():
    vectors = {"a": (1, 0, 0), "b": (0, 1, 0), "c": (0, 0, 1), "test": (1, 1, 0)}
    labels = {token: (vec[0], 91.0 + i, 92.0 + i, vec[1], vec[2])
              for i, (token, vec) in enumerate(vectors.items())}
    alignment = _align(vectors, labels)
    score = score_locked_test(vectors, labels, test_ids=("test",), alignment=alignment,
                              split_manifest=_split_manifest())
    assert score["scored_ids"] == ["test"]
    with pytest.raises(ValueError, match="heldout"):
        score_locked_test(vectors, labels, test_ids=("a", "test"), alignment=alignment,
                          split_manifest=_split_manifest())


def test_alignment_frozen_before_test():
    assert lexical_readiness(checkpoint_sha256=None, vectors_available=False)["status"] == "UNSUPPORTED"
    vectors = {"a": (1, 0, 0), "b": (0, 1, 0), "c": (0, 0, 1)}
    labels = {token: (vec[0], 98.0, 97.0, vec[1], vec[2]) for token, vec in vectors.items()}
    alignment = _align(vectors, labels)
    assert alignment.frozen is True
    with pytest.raises(ValueError, match="frozen"):
        score_locked_test(vectors, labels, test_ids=("test",),
                          alignment=replace(alignment, checkpoint_sha256="", frozen=False),
                          split_manifest=_split_manifest())


def test_missing_concepts_not_dropped_silently():
    vectors = {"a": (1, 0, 0), "b": (0, 1, 0), "c": (0, 0, 1)}
    labels = {token: (vec[0], 98.0, 97.0, vec[1], vec[2]) for token, vec in vectors.items()}
    alignment = _align(vectors, labels)
    score = score_locked_test(vectors, labels, test_ids=("missing-1", "missing-2"),
                              alignment=alignment, split_manifest=_split_manifest())
    assert score["status"] == "unsupported"
    assert score["missing_ids"] == ["missing-1", "missing-2"]
    assert score["coverage"] == 0.0


def test_token_bridge_and_split_are_frozen():
    vectors = {"a": (1, 0, 0), "b": (0, 1, 0), "c": (0, 0, 1), "test": (1, 1, 0)}
    labels = {token: (vec[0], 91.0, 92.0, vec[1], vec[2])
              for token, vec in vectors.items()}
    alignment = _align(vectors, labels)
    changed = dict(vectors, test=(0, 1, 1))
    with pytest.raises(ValueError, match="bridge changed"):
        score_locked_test(changed, labels, test_ids=("test",), alignment=alignment,
                          split_manifest=_split_manifest())
    altered_manifest = _split_manifest()
    altered_manifest["split_by_id"] = dict(altered_manifest["split_by_id"], test="anchor")
    with pytest.raises(ValueError, match="split"):
        score_locked_test(vectors, labels, test_ids=("test",), alignment=alignment,
                          split_manifest=altered_manifest)


def test_anchor_fit_requires_exact_registered_anchor_set():
    vectors = {"a": (1, 0, 0), "b": (0, 1, 0), "c": (0, 0, 1), "test": (1, 1, 0)}
    labels = {token: (0, 1, 0, 1, 0) for token in vectors}
    with pytest.raises(ValueError, match="complete registered anchor"):
        fit_anchor_alignment(vectors, labels, anchor_ids=("a", "b", "test"),
                             checkpoint_sha256=_sha("checkpoint"),
                             split_manifest=_split_manifest())


def test_target_scores_require_previously_frozen_checkpoint_and_bridge(tmp_path, monkeypatch):
    path = tmp_path / "gpads.tsv"
    path.write_text("word\tgoodness\tpower\taggression\tdanger\tstructure\n"
                    "a\t0\t1\t0\t2\t3\n"
                    "b\t0\t4\t0\t5\t6\n"
                    "c\t0\t7\t0\t8\t9\n"
                    "test\t0\t10\t0\t11\t12\n", encoding="utf-8")
    monkeypatch.setattr(lexical_module, "verify_source_bytes", lambda *_: {})
    with pytest.raises(ValueError, match="freeze checkpoint"):
        read_gpads_labels(path, split_manifest=_split_manifest(), split="anchor",
                          checkpoint_sha256="", bridge_sha256="")
    labels = read_gpads_labels(path, split_manifest=_split_manifest(), split="anchor",
                               checkpoint_sha256=_sha("checkpoint"),
                               bridge_sha256=_sha("bridge"))
    assert set(labels) == {"a", "b", "c"}
    assert "test" not in labels


def test_gpads_five_columns_map_only_declared_pds():
    # goodness, power, aggression, danger, structure: every distractor differs.
    assert pds_target_coordinates((10.0, 91.0, 92.0, 20.0, 30.0)) == (91.0, 20.0, 30.0)
    with pytest.raises(ValueError, match="five"):
        pds_target_coordinates((10.0, 20.0, 30.0))
