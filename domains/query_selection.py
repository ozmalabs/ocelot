"""Finite-pool, label-blind query ranking over an explicit hypothesis set."""
from __future__ import annotations
import math
from collections import Counter
from typing import Any, Callable, Iterable, Sequence

Describe = Callable[[Any], dict]


def _prediction_key(value: Any) -> tuple[str, Any]:
    """Keep booleans distinct from numeric 0/1 while grouping equal numbers."""
    if isinstance(value, bool):
        return ("bool", value)
    if isinstance(value, (int, float)):
        number = float(value)
        if math.isnan(number):
            return ("number", "nan")
        return ("number", number)
    return (type(value).__name__, repr(value))


def _entropy(counts: Counter) -> float:
    total = sum(counts.values())
    if not total:
        return 0.0
    return -sum((n / total) * math.log2(n / total) for n in counts.values())


def rank_queries_by_disagreement(
    substrate,
    hypotheses: Sequence,
    describe: Describe,
    candidates: Iterable[tuple[str, Any]],
) -> list[dict]:
    """Rank finite query candidates by predictive entropy under equal weights.

    The function has no oracle/label argument: it sees only the supplied current
    hypotheses, their native Term evaluations, and candidate inputs. Higher
    entropy means predictions divide the explicit hypothesis set more evenly.
    Ties use more distinct predictions, then original candidate order. This is
    a finite-pool selector, not a hypothesis generator or a calibrated posterior.
    """
    if not hypotheses:
        raise ValueError("at least one hypothesis is required")
    ranked = []
    for ordinal, (name, input_value) in enumerate(candidates):
        env = describe(input_value)
        predictions = [hyp.evaluate(env, substrate) for hyp in hypotheses]
        counts = Counter(_prediction_key(value) for value in predictions)
        ranked.append({
            "name": name,
            "input": input_value,
            "predictions": predictions,
            "prediction_counts": [
                {"key": list(key), "count": count}
                for key, count in sorted(counts.items(), key=lambda item: repr(item[0]))
            ],
            "distinct_predictions": len(counts),
            "entropy_bits": _entropy(counts),
            "_ordinal": ordinal,
        })
    ranked.sort(key=lambda row: (-row["entropy_bits"],
                                 -row["distinct_predictions"],
                                 row["_ordinal"]))
    for row in ranked:
        row.pop("_ordinal")
    return ranked


class QueryRankingIndex:
    """Cached hypothesis-by-query predictions for repeated active selection.

    Building the index evaluates each pair once and retains both values and
    comparison keys. Repeated ranking reads this matrix rather than re-running
    the substrate evaluator; callers should include matrix construction time
    and O(hypotheses × candidates) retained memory in their cost accounting.
    The index is immutable: changing hypotheses, descriptors, or candidates
    requires rebuilding it.
    """

    def __init__(self, substrate, hypotheses: Sequence, describe: Describe,
                 candidates: Iterable[tuple[str, Any]]):
        if not hypotheses:
            raise ValueError("at least one hypothesis is required")
        self.hypotheses = list(hypotheses)
        self.candidates = list(candidates)
        if not self.candidates:
            raise ValueError("at least one query candidate is required")
        self._values: list[list[Any]] = []
        self._keys: list[list[tuple[str, Any]]] = []
        envs = [describe(value) for _, value in self.candidates]
        for hypothesis in self.hypotheses:
            values = [hypothesis.evaluate(env, substrate) for env in envs]
            self._values.append(values)
            self._keys.append([_prediction_key(value) for value in values])
        self.prediction_evaluations = len(self.hypotheses) * len(self.candidates)

    def rank(self, active_hypothesis_indices: Iterable[int] | None = None,
             candidate_indices: Iterable[int] | None = None) -> list[dict]:
        """Rank selected candidates over active hypotheses with equal weights."""
        active = list(range(len(self.hypotheses))) if active_hypothesis_indices is None \
            else list(active_hypothesis_indices)
        queries = list(range(len(self.candidates))) if candidate_indices is None \
            else list(candidate_indices)
        if not active:
            raise ValueError("at least one active hypothesis is required")
        ranked = []
        for ordinal, query_index in enumerate(queries):
            name, input_value = self.candidates[query_index]
            values = [self._values[hypothesis_index][query_index] for hypothesis_index in active]
            counts = Counter(self._keys[hypothesis_index][query_index]
                             for hypothesis_index in active)
            ranked.append({
                "name": name,
                "input": input_value,
                "predictions": values,
                "prediction_counts": [
                    {"key": list(key), "count": count}
                    for key, count in sorted(counts.items(), key=lambda item: repr(item[0]))
                ],
                "distinct_predictions": len(counts),
                "entropy_bits": _entropy(counts),
                "_ordinal": ordinal,
                "candidate_index": query_index,
            })
        ranked.sort(key=lambda row: (-row["entropy_bits"],
                                     -row["distinct_predictions"],
                                     row["_ordinal"]))
        for row in ranked:
            row.pop("_ordinal")
        return ranked

    def filter(self, active_hypothesis_indices: Iterable[int],
               candidate_index: int, response: Any,
               tolerance: float = 1e-9) -> list[int]:
        """Retain cached hypotheses consistent with one observed response.

        Numeric predictions use the same absolute tolerance as the CEGIS
        target matcher; booleans remain distinct from numeric zero and one.
        """
        response_key = _prediction_key(response)
        kept = []
        for index in active_hypothesis_indices:
            prediction = self._values[index][candidate_index]
            if (isinstance(prediction, (int, float)) and not isinstance(prediction, bool)
                    and isinstance(response, (int, float)) and not isinstance(response, bool)):
                matches = abs(float(prediction) - float(response)) <= tolerance
            else:
                matches = self._keys[index][candidate_index] == response_key
            if matches:
                kept.append(index)
        return kept
