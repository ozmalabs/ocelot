"""Mechanical Whisper evidence ingress for the graph-native grounding guard.

Whisper supplies a free-decoder proposal and a final-encoder feature. This
adapter computes external cosine evidence and lays every closed-vocabulary
candidate into the substrate. The loaded graph rules choose the nearest
candidate, apply its support-derived admission radius, and decide
accept/correct/abstain. Python never selects a label or action.
"""
from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Mapping, Sequence

import numpy as np

from domains.whisper_teacher_adapter import embed
from substrate.seed_loader import manifest_for


DIGIT_WORDS = (
    "zero", "one", "two", "three", "four",
    "five", "six", "seven", "eight", "nine",
)
_DIGIT_MAP = {str(i): word for i, word in enumerate(DIGIT_WORDS)}


def normalize_digit_transcript(text: str) -> str:
    """Mechanical exact-match normalization; never fuzzy-matches a label."""
    tokens = re.findall(r"[a-z]+|[0-9]+", str(text).lower())
    normalized = [_DIGIT_MAP.get(token, token) for token in tokens]
    return " ".join(normalized)


def _add_edge(inner, src, edge_type, tgt):
    try:
        inner.add_edge_unchecked(src, edge_type, tgt)
    except TypeError:
        inner.add_edge_unchecked(src, edge_type, tgt, {})


@dataclass(frozen=True)
class PrototypeBank:
    """Support-fold geometry. These values are evidence, not decisions."""

    prototypes: Mapping[str, np.ndarray]
    radii: Mapping[str, float]
    support_counts: Mapping[str, int]
    fold: str
    model: str = "faster-whisper/base.en"

    @classmethod
    def from_support(
        cls,
        support: Mapping[str, Sequence[np.ndarray]],
        *,
        fold: str,
        model: str = "faster-whisper/base.en",
    ) -> "PrototypeBank":
        prototypes = {}
        radii = {}
        counts = {}
        for label in sorted(support):
            vectors = np.asarray(support[label], dtype=np.float64)
            if vectors.ndim != 2 or len(vectors) == 0:
                raise ValueError(f"{label!r}: expected one or more vectors")
            vectors = vectors / (
                np.linalg.norm(vectors, axis=1, keepdims=True) + 1e-12
            )
            centroid = vectors.mean(axis=0)
            centroid /= np.linalg.norm(centroid) + 1e-12
            distances = 1.0 - vectors @ centroid
            # Keep the same precision used to derive the radius: down-casting
            # the prototype after measuring support can place a boundary
            # exemplar infinitesimally outside its own radius.
            prototypes[label] = centroid
            radii[label] = float(np.max(distances))
            counts[label] = int(len(vectors))
        return cls(prototypes, radii, counts, str(fold), str(model))


class GraphWhisperGroundingGuard:
    """Lay complete evidence; let the Rust graph choose and admit the result."""

    def __init__(self, substrate, agent, bank: PrototypeBank):
        self.s = substrate
        self.inner = substrate._inner
        self.agent = agent
        self.bank = bank
        loaded = self.inner.load_seed_manifest(
            manifest_for("whisper_grounding_guard"), agent
        )
        skipped = list(loaded.get("rules_skipped", []))
        if skipped:
            raise RuntimeError(f"grounding guard rules skipped: {skipped}")
        self.prototype_nodes = {}
        for label in sorted(bank.prototypes):
            prototype = self.s.add_node("WhisperGroundingPrototype", {
                "label": label,
                "support_radius": float(bank.radii[label]),
                "support_count": float(bank.support_counts[label]),
                "fold": bank.fold,
                "model": bank.model,
                "provenance_kind": "learned_from_support_fold",
            })
            _add_edge(
                self.inner, self.agent,
                "holds_whisper_grounding_prototype", prototype,
            )
            self.prototype_nodes[label] = prototype

    def infer_embedding(self, vector, baseline_text: str) -> dict:
        """Run one graph decision over an already extracted encoder vector."""
        vector = np.asarray(vector, dtype=np.float64)
        vector /= np.linalg.norm(vector) + 1e-12
        normalized = normalize_digit_transcript(baseline_text)
        inquiry = self.s.add_node("WhisperGroundingInquiry", {
            "status": "raw",
            "baseline_text": str(baseline_text),
            "baseline_normalized": normalized,
            "baseline_nonempty": float(bool(normalized)),
            "fold": self.bank.fold,
            "model": self.bank.model,
            "provenance_kind": "observed_external_proposal",
        })
        _add_edge(
            self.inner, self.agent, "has_whisper_grounding_inquiry", inquiry
        )
        for label in sorted(self.bank.prototypes):
            candidate = self.s.add_node("WhisperGroundingCandidate", {
                "distance": float(
                    1.0 - vector @ self.bank.prototypes[label]
                ),
                "fold": self.bank.fold,
                "provenance_kind": "observed_encoder_evidence",
            })
            _add_edge(
                self.inner, inquiry, "has_grounding_candidate", candidate
            )
            _add_edge(
                self.inner, candidate, "derived_from_grounding_prototype",
                self.prototype_nodes[label],
            )
        self.inner.run_rules()
        result = dict(self.s.node(inquiry)["attrs"])
        if result.get("status") != "decided":
            raise RuntimeError(f"graph guard did not decide inquiry: {result}")
        return result

    def infer_audio(self, audio, baseline_text: str) -> dict:
        """Extract borrowed encoder evidence, then perform the graph decision."""
        return self.infer_embedding(embed(audio), baseline_text)


def audit_no_python_inference_decision() -> list[str]:
    """Conservative source audit for label/action selection in inference."""
    import ast
    import inspect

    tree = ast.parse(inspect.getsource(GraphWhisperGroundingGuard))
    violations = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            name = getattr(node.func, "id", None)
            if name in {"min", "max"}:
                violations.append(
                    f"line {getattr(node, 'lineno', '?')}: Python {name}()"
                )
        if isinstance(node, ast.Attribute) and node.attr in {
            "argmin", "argmax", "argsort"
        }:
            violations.append(
                f"line {getattr(node, 'lineno', '?')}: Python {node.attr}"
            )
    return violations
