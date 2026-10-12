"""Target-blind selection of one fresh adequacy probe from challenger Terms.

The selector chooses only an input descriptor. Label acquisition and receipt
adjudication remain separate operations in ``independent_adequacy``.
"""
from __future__ import annotations

import hashlib
import json
import math
from typing import Any, Callable


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _entropy(values: list[Any]) -> float:
    counts: dict[str, int] = {}
    for value in values:
        key = _canonical(value)
        counts[key] = counts.get(key, 0) + 1
    total = len(values)
    return -sum((count / total) * math.log2(count / total) for count in counts.values())


def select_disagreement_probe(
    candidate_id: str,
    candidate_term: dict,
    challenger_terms: list[dict],
    acquisition_rows: list[dict],
    admissible_inputs: list[dict],
    evaluate: Callable[[dict, dict], Any],
    *,
    seed: str = "adequacy-disagreement-v1",
) -> dict:
    """Select one fresh input maximizing prediction entropy across held Terms.

    The result is target blind: labels are not accepted by this function. The
    caller supplies the finite domain and alternatives, and must obtain labels
    independently before calling the receipt adjudicator. Domain adequacy is
    not guaranteed when all supplied inputs alias or the target is absent from
    the candidate/challenger set.
    """
    if not isinstance(candidate_id, str) or not candidate_id.strip():
        raise ValueError("candidate_id must be non-empty")
    if not isinstance(candidate_term, dict) or not isinstance(challenger_terms, list) or not challenger_terms:
        raise ValueError("candidate Term and at least one challenger Term are required")
    if any(not isinstance(term, dict) for term in challenger_terms):
        raise TypeError("challenger_terms must contain Term mappings")
    if not isinstance(acquisition_rows, list) or not isinstance(admissible_inputs, list):
        raise TypeError("acquisition_rows and admissible_inputs must be lists")
    if not isinstance(seed, str) or not seed.strip():
        raise ValueError("seed must be non-empty")

    acquired = set()
    for row in acquisition_rows:
        if not isinstance(row, dict) or not isinstance(row.get("inputs"), dict):
            raise ValueError("each acquisition row must contain an inputs mapping")
        acquired.add(_digest(row["inputs"]))
    fresh: dict[str, dict] = {}
    for inputs in admissible_inputs:
        if not isinstance(inputs, dict) or not inputs:
            raise ValueError("admissible inputs must be non-empty mappings")
        key = _digest(inputs)
        if key in fresh:
            raise ValueError("admissible input descriptors must be unique")
        if key not in acquired:
            fresh[key] = inputs
    if not fresh:
        raise ValueError("admissible domain contains no fresh inputs")

    scored = []
    models = [candidate_term, *challenger_terms]
    for input_hash, inputs in fresh.items():
        predictions = [evaluate(term, inputs) for term in models]
        encoded = [_canonical(value) for value in predictions]
        entropy = _entropy(predictions)
        tie = hashlib.sha256(f"{seed}:{input_hash}".encode()).hexdigest()
        scored.append((entropy, tie, input_hash, inputs, predictions, encoded))
    entropy, _, input_hash, inputs, predictions, encoded = sorted(
        scored, key=lambda item: (-item[0], item[1]))[0]
    identity = {"candidate_id": candidate_id,
                "candidate_term_sha256": _digest(candidate_term),
                "challenger_terms_sha256": [_digest(term) for term in challenger_terms],
                "acquisition_sha256": _digest(acquisition_rows),
                "domain_sha256": _digest(admissible_inputs),
                "selected_input_sha256": input_hash,
                "predictions_sha256": _digest(encoded), "seed": seed}
    return {"schema": "AdequacyDisagreementProbeSelectionV1", "selection_id": _digest(identity),
            **identity, "input": inputs, "predictions": predictions,
            "prediction_entropy_bits": entropy, "candidate_challengers": len(models),
            "fresh_domain_size": len(fresh)}
