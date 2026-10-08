"""Bounded disagreement queries over a finite set of executable Term hypotheses.

This selects which input to ask an external oracle about; it does not produce
the oracle's expected output or invent hypotheses beyond the supplied set.
"""
from __future__ import annotations

import math
import copy
import hashlib
import json
from typing import Any, Callable

_PURE_TERM_TYPES = {
    "Var", "Lit", "IfThenElse", "And", "Or", "Not", "Abs", "Neg",
    "Plus", "Minus", "Times", "Div", "Mod", "Eq", "Ne", "Gt", "Ge",
    "Lt", "Le", "Min", "Max",
}

# A failed candidate evaluation is still a prediction outcome for query
# selection: after an oracle answer, that candidate is inconsistent. Keep the
# marker distinct from valid scalar outputs and serialize it explicitly.
_QUERY_EVALUATION_FAILED = object()


def _prediction_bucket(value: Any) -> tuple:
    if value is _QUERY_EVALUATION_FAILED:
        return ("substrate", "TermEvaluationFailure", "candidate_error")
    return _bucket(value)


def _prediction_record(hypothesis_id: str, value: Any) -> dict:
    if value is _QUERY_EVALUATION_FAILED:
        return {"hypothesis": hypothesis_id, "output": None, "evaluation_error": True}
    return {"hypothesis": hypothesis_id, "output": value}


def _same(a: Any, b: Any) -> bool:
    return type(a) is type(b) and a == b


def _bucket(value: Any) -> tuple:
    # Preserve type distinctions such as bool versus int in prediction groups.
    return (type(value).__module__, type(value).__qualname__, repr(value))


def _entropy(counts: list[int]) -> float:
    total = sum(counts)
    if not total:
        return 0.0
    return -sum((n / total) * math.log2(n / total) for n in counts if n)


def _closed_pure_term(term: Any) -> bool:
    """Conservatively allow memoization only for closed scalar Terms."""
    if isinstance(term, dict):
        op = term.get("type")
        if op is not None and op not in _PURE_TERM_TYPES:
            return False
        return all(_closed_pure_term(value) for value in term.values())
    if isinstance(term, (list, tuple)):
        return all(_closed_pure_term(value) for value in term)
    return True


class TermEvaluationCache:
    """Cache native values for immutable pure-Term/input object pairs.

    The cache retains Term and environment objects and computes their
    canonical JSON fingerprints once. Do not mutate either object, reuse the
    cache across changing evaluator/graph contexts, or pass graph-dependent
    Terms. `select_discriminating_input` additionally enforces its pure-Term
    allowlist before calling this cache.
    """

    def __init__(self) -> None:
        self._term_tokens: dict[int, tuple[dict, str]] = {}
        self._env_tokens: dict[int, tuple[dict, str]] = {}
        self._values: dict[tuple[str, str], Any] = {}

    def __len__(self) -> int:
        return len(self._values)

    @property
    def serialized_key_bytes(self) -> int:
        return sum(len(term_key.encode()) + len(env_key.encode())
                   for term_key, env_key in self._values)

    @staticmethod
    def _token(value: dict, index: dict[int, tuple[dict, str]]) -> str:
        identity = id(value)
        cached = index.get(identity)
        if cached is not None and cached[0] is value:
            return cached[1]
        token = json.dumps(value, sort_keys=True, separators=(",", ":"),
                           ensure_ascii=False, allow_nan=False)
        index[identity] = (value, token)
        return token

    def evaluate(self, term: dict, env: dict,
                 evaluator: Callable[[dict, dict], Any]) -> Any:
        try:
            key = (self._token(term, self._term_tokens),
                   self._token(env, self._env_tokens))
        except (TypeError, ValueError):
            return evaluator(term, env)
        if key in self._values:
            return copy.deepcopy(self._values[key])
        value = evaluator(term, env)
        self._values[key] = copy.deepcopy(value)
        return value


class IdentityTermEvaluationCache:
    """Fast cache for stable pure Term and environment objects.

    Keys use object identity rather than content. Strong references prevent ID
    reuse; callers must keep each Term/environment immutable and the evaluator
    context unchanged for the cache lifetime. Structurally equal but distinct
    objects simply cause separate evaluations. The selector only routes its
    conservative pure-Term allowlist through this cache.
    """

    def __init__(self) -> None:
        self._terms: dict[int, dict] = {}
        self._environments: dict[int, dict] = {}
        self._values: dict[tuple[int, int], Any] = {}

    def __len__(self) -> int:
        return len(self._values)

    @property
    def serialized_key_bytes(self) -> int:
        return 0

    def evaluate(self, term: dict, env: dict,
                 evaluator: Callable[[dict, dict], Any]) -> Any:
        term_id, env_id = id(term), id(env)
        self._terms.setdefault(term_id, term)
        self._environments.setdefault(env_id, env)
        key = (term_id, env_id)
        if key in self._values:
            return copy.deepcopy(self._values[key])
        value = evaluator(term, env)
        self._values[key] = copy.deepcopy(value)
        return value


def select_discriminating_input(
    evaluate: Callable[[dict, dict], Any],
    hypotheses: list[dict],
    candidate_inputs: list[dict],
    observations: list[dict] | None = None,
    evaluation_cache: dict | TermEvaluationCache | IdentityTermEvaluationCache | None = None,
) -> dict:
    """Choose the first input with maximal predictive entropy.

    `hypotheses` rows contain unique `id` and native Term `term`. `observations`
    are prior `{inputs, expected}` rows used to remove inconsistent hypotheses.
    The function returns a query and each surviving hypothesis's predicted
    output, but never supplies an expected answer. Ties follow caller input
    order for reproducibility. When `evaluation_cache` is supplied, memoize
    exact canonical Term+environment pairs, but only for a conservative
    pure-Term allowlist. The caller must keep evaluator semantics stable for
    the cache lifetime. This is a finite candidate-set heuristic, not a
    general active-learning guarantee.
    """
    if not isinstance(hypotheses, list) or len(hypotheses) < 2:
        return {"ok": False, "reason": "at least two hypotheses are required"}
    ids = [h.get("id") for h in hypotheses if isinstance(h, dict)]
    if len(ids) != len(hypotheses) or any(not isinstance(i, str) or not i for i in ids) or len(set(ids)) != len(ids):
        return {"ok": False, "reason": "hypothesis ids must be unique non-empty strings"}
    if not isinstance(candidate_inputs, list) or not candidate_inputs:
        return {"ok": False, "reason": "candidate_inputs must be a non-empty list"}
    observations = observations or []

    def eval_hypothesis(hypothesis: dict, env: dict) -> Any:
        term = hypothesis["term"]
        if evaluation_cache is None or not _closed_pure_term(term):
            return evaluate(term, env)
        if isinstance(evaluation_cache, (TermEvaluationCache, IdentityTermEvaluationCache)):
            return evaluation_cache.evaluate(term, env, evaluate)
        try:
            key = json.dumps([term, env], sort_keys=True, separators=(",", ":"),
                             ensure_ascii=False, allow_nan=False)
        except (TypeError, ValueError):
            return evaluate(term, env)
        if key in evaluation_cache:
            return copy.deepcopy(evaluation_cache[key])
        value = evaluate(term, env)
        evaluation_cache[key] = copy.deepcopy(value)
        return value

    survivors = list(hypotheses)
    for row in observations:
        if not isinstance(row, dict) or set(row) != {"inputs", "expected"} or not isinstance(row["inputs"], dict):
            return {"ok": False, "reason": "invalid observation row"}
        kept = []
        for hypothesis in survivors:
            try:
                value = eval_hypothesis(hypothesis, row["inputs"])
            except Exception:  # candidate does not explain the observed case
                continue
            if _same(value, row["expected"]):
                kept.append(hypothesis)
        survivors = kept
    if len(survivors) < 2:
        return {"ok": False, "reason": "fewer than two hypotheses fit existing observations",
                "surviving_hypotheses": [h["id"] for h in survivors]}

    used = {_bucket(row["inputs"]) for row in observations}
    scored = []
    for input_index, env in enumerate(candidate_inputs):
        if not isinstance(env, dict) or not env or _bucket(env) in used:
            continue
        predictions = []
        for hypothesis in survivors:
            try:
                value = eval_hypothesis(hypothesis, env)
            except Exception:
                value = _QUERY_EVALUATION_FAILED
            predictions.append((hypothesis["id"], value))
        buckets: dict[tuple, int] = {}
        for _, value in predictions:
            key = _prediction_bucket(value)
            buckets[key] = buckets.get(key, 0) + 1
        score = _entropy(list(buckets.values()))
        scored.append((score, -input_index, env, predictions, len(buckets)))
    if not scored:
        return {"ok": False, "reason": "no valid unused candidate input"}
    score, _, env, predictions, partition_count = max(scored)
    if score <= 0.0:
        return {"ok": False, "reason": "candidate hypotheses agree on every available input",
                "surviving_hypotheses": [h["id"] for h in survivors]}
    return {"ok": True, "query": env, "entropy_bits": score,
            "partition_count": partition_count,
            "surviving_hypotheses": [h["id"] for h in survivors],
            "predictions": [_prediction_record(hid, value)
                            for hid, value in predictions]}


def partition_hypotheses_by_behavior(
    evaluate: Callable[[dict, dict], Any],
    hypotheses: list[dict],
    probe_inputs: list[dict],
) -> dict:
    """Group Terms by their typed predictions on a caller-supplied finite set.

    This describes observational equivalence only on `probe_inputs`. It is not
    a semantic-equivalence proof outside that finite domain. Evaluation errors
    form their own stable prediction bucket, matching the query selector.
    """
    if not isinstance(hypotheses, list) or not hypotheses:
        return {"ok": False, "reason": "at least one hypothesis is required"}
    ids = [h.get("id") for h in hypotheses if isinstance(h, dict)]
    if len(ids) != len(hypotheses) or any(not isinstance(i, str) or not i for i in ids) or len(set(ids)) != len(ids):
        return {"ok": False, "reason": "hypothesis ids must be unique non-empty strings"}
    if not isinstance(probe_inputs, list) or not probe_inputs:
        return {"ok": False, "reason": "probe_inputs must be a non-empty list"}
    if any(not isinstance(env, dict) or not env for env in probe_inputs):
        return {"ok": False, "reason": "every probe input must be a non-empty mapping"}
    try:
        probe_digest = hashlib.sha256(json.dumps(
            probe_inputs, sort_keys=True, separators=(",", ":"),
            ensure_ascii=False, allow_nan=False).encode("utf-8")).hexdigest()
    except (TypeError, ValueError):
        return {"ok": False, "reason": "probe inputs must be finite JSON values"}

    classes: dict[tuple, list[str]] = {}
    for hypothesis in hypotheses:
        signature = []
        for env in probe_inputs:
            try:
                value = evaluate(hypothesis.get("term"), env)
            except Exception:
                value = _QUERY_EVALUATION_FAILED
            signature.append(_prediction_bucket(value))
        classes.setdefault(tuple(signature), []).append(hypothesis["id"])

    return {
        "ok": True,
        "probe_count": len(probe_inputs),
        "probe_sha256": probe_digest,
        "hypothesis_count": len(hypotheses),
        "class_count": len(classes),
        "all_agree_on_probes": len(classes) == 1,
        "classes": [
            {"hypothesis_ids": sorted(class_ids),
             "signature": [list(bucket) for bucket in signature]}
            for signature, class_ids in classes.items()
        ],
    }


def select_candidate_from_graph_evidence(
    sub: Any,
    experiment_id: str,
    proposals: list[dict],
    evidence: list[dict],
) -> dict:
    """Choose the unique proposal matching the most recorded labels in a Term.

    Proposal/evidence rows are copied into the supplied isolated substrate as
    `CandidateProposal` and `CandidateEvidence` nodes. A native Term counts
    matching evidence rows for each proposal and returns a winner only when
    the maximum is positive and unique. The caller still supplies candidates,
    probe predictions, and expected labels; this function does not authenticate
    those labels or establish that the probes cover the task domain.
    """
    if not isinstance(experiment_id, str) or not experiment_id:
        return {"ok": False, "reason": "experiment_id must be non-empty"}
    if not isinstance(proposals, list) or len(proposals) < 2:
        return {"ok": False, "reason": "at least two proposals are required"}
    if not isinstance(evidence, list) or not evidence:
        return {"ok": False, "reason": "non-empty evidence is required"}
    for node_type in ("CandidateProposal", "CandidateEvidence"):
        for node in sub.nodes(node_type):
            if sub.node(node)["attrs"].get("experiment_id") == experiment_id:
                return {"ok": False, "reason": "experiment_id is already present in this substrate"}
    proposal_ids = [row.get("proposal_id") for row in proposals if isinstance(row, dict)]
    if (len(proposal_ids) != len(proposals)
            or any(not isinstance(x, str) or not x for x in proposal_ids)
            or len(set(proposal_ids)) != len(proposal_ids)):
        return {"ok": False, "reason": "proposal ids must be unique non-empty strings"}
    normalized = []
    for row in evidence:
        if not isinstance(row, dict):
            return {"ok": False, "reason": "evidence rows must be objects"}
        pid, probe = row.get("proposal_id"), row.get("probe_id")
        predicted, expected = row.get("predicted"), row.get("expected")
        if pid not in proposal_ids or not isinstance(probe, str) or not probe:
            return {"ok": False, "reason": "evidence references an unknown proposal or empty probe"}
        if not isinstance(predicted, (str, int, float, bool, type(None))) or not isinstance(expected, (str, int, float, bool, type(None))):
            return {"ok": False, "reason": "labels must be scalar JSON values"}
        if ((isinstance(predicted, float) and not math.isfinite(predicted))
                or (isinstance(expected, float) and not math.isfinite(expected))):
            return {"ok": False, "reason": "labels must contain only finite numbers"}
        normalized.append((pid, probe, predicted, expected))
    probe_ids = {probe for _, probe, _, _ in normalized}
    seen = {(pid, probe) for pid, probe, _, _ in normalized}
    if len(seen) != len(normalized):
        return {"ok": False, "reason": "duplicate proposal/probe evidence"}
    if len(seen) != len(proposal_ids) * len(probe_ids):
        return {"ok": False, "reason": "every proposal must have evidence for every supplied probe"}

    for row in proposals:
        sub.add_node("CandidateProposal", {
            "experiment_id": experiment_id,
            "proposal_id": row["proposal_id"],
            "proposal_label": str(row.get("proposal_label", row["proposal_id"])),
        })
    for pid, probe, predicted, expected in normalized:
        sub.add_node("CandidateEvidence", {
            "experiment_id": experiment_id, "proposal_id": pid,
            "probe_id": probe, "predicted": predicted, "expected": expected,
        })

    V = lambda name: {"type": "Var", "name": name}
    L = lambda value: {"type": "Lit", "value": value}
    A = lambda node, key: {"type": "Attr", "node": node, "key": key}
    Eq = lambda a, b: {"type": "Eq", "a": a, "b": b}
    And = lambda *items: {"type": "And", "items": list(items)}
    Ite = lambda cond, yes, no: {"type": "IfThenElse", "cond": cond, "then": yes, "other": no}
    Filter = lambda source, var, pred: {"type": "Filter", "source": source, "var_name": var, "predicate": pred}
    Nodes = lambda kind: {"type": "NodesOfType", "node_type": kind}
    Sum = lambda source, var, value: {"type": "Sum", "source": source, "var_name": var, "value": value}
    Count = lambda source: {"type": "Count", "source": source}
    Argmax = lambda source, var, value, default: {"type": "Argmax", "source": source, "var_name": var, "value": value, "default": default}
    scoped_proposals = Filter(Nodes("CandidateProposal"), "p0",
        Eq(A(V("p0"), "experiment_id"), L(experiment_id)))
    scoped_evidence = Filter(Nodes("CandidateEvidence"), "e0",
        Eq(A(V("e0"), "experiment_id"), L(experiment_id)))

    def matched_count(proposal_var: str) -> dict:
        return Sum(scoped_evidence, "e", Ite(
            And(Eq(A(V("e"), "proposal_id"), A(V(proposal_var), "proposal_id")),
                Eq(A(V("e"), "predicted"), A(V("e"), "expected"))), L(1.0), L(0.0)))

    best = Argmax(scoped_proposals, "p", matched_count("p"), L(None))
    tied = Count(Filter(scoped_proposals, "q",
        Eq(matched_count("q"), matched_count("winner"))))
    expression = {"type": "Let", "name": "winner", "value": best,
        "body": Ite(Eq(V("winner"), L(None)), L(None),
            Ite(And({"type": "Gt", "a": matched_count("winner"), "b": L(0.0)},
                    Eq(tied, L(1.0))), V("winner"), L(None)))}
    try:
        winner = sub._inner.evaluate(expression, {})
    except Exception as exc:
        return {"ok": False, "reason": f"candidate scoring Term failed: {type(exc).__name__}: {exc}"}
    if winner is None or not sub.has_node(winner):
        return {"ok": False, "reason": "no unique proposal has positive matching evidence",
                "proposal_count": len(proposal_ids), "probe_count": len(probe_ids)}
    attrs = sub.node(winner)["attrs"]
    independently_counted = sum(1 for pid, _probe, predicted, expected in normalized
                                if pid == attrs["proposal_id"] and predicted == expected)
    return {"ok": True, "proposal_id": attrs["proposal_id"],
            "proposal_label": attrs["proposal_label"],
            "matching_evidence_count": independently_counted,
            "proposal_count": len(proposal_ids), "probe_count": len(probe_ids),
            "proposal_node": winner}


_EVAL_FAILED = object()


class TermPredictionMatrix:
    """Sequence-local predictions for an immutable pure-Term hypothesis set."""

    def __init__(self, evaluate: Callable[[dict, dict], Any],
                 hypotheses: list[dict], candidate_inputs: list[dict]) -> None:
        self._evaluate = evaluate
        self._terms = tuple(h["term"] for h in hypotheses)
        self._candidate_buckets = tuple(_bucket(env) for env in candidate_inputs)
        self._values: dict[tuple, tuple[dict, dict[int, Any]]] = {}

    @property
    def cells(self) -> int:
        return sum(len(values) for _, values in self._values.values())

    @property
    def approximate_bytes(self) -> int:
        return sum(len(repr((key, env, values)).encode("utf-8"))
                   for key, (env, values) in self._values.items())

    def compatible(self, evaluate: Callable[[dict, dict], Any],
                   hypotheses: list[dict], candidate_inputs: list[dict]) -> bool:
        return (self._evaluate is evaluate
                and len(self._terms) == len(hypotheses)
                and all(term is hypothesis.get("term")
                        for term, hypothesis in zip(self._terms, hypotheses))
                and self._candidate_buckets == tuple(_bucket(env)
                                                      for env in candidate_inputs))

    def values_for(self, env: dict, hypothesis_indices: list[int]) -> dict[int, Any]:
        key = _bucket(env)
        cached = self._values.get(key)
        if cached is None:
            cached = (env, {})
            self._values[key] = cached
        values = cached[1]
        for index in hypothesis_indices:
            if index in values:
                continue
            try:
                values[index] = self._evaluate(self._terms[index], env)
            except Exception:
                values[index] = _EVAL_FAILED
        return values


def select_discriminating_input_batched(
    evaluate: Callable[[dict, dict], Any],
    hypotheses: list[dict],
    candidate_inputs: list[dict],
    observations: list[dict] | None = None,
    prediction_matrix: TermPredictionMatrix | None = None,
) -> dict:
    """Select by building one exact pure-Term prediction matrix per sequence.

    This trades memory for fewer evaluator crossings when a caller reuses the
    returned matrix across oracle labels. Only closed allowlisted Terms are
    accepted; graph-dependent or callback-backed terms must use the general
    selector. Inputs and Terms must remain stable for the sequence.
    """
    if not isinstance(hypotheses, list) or len(hypotheses) < 2:
        return {"ok": False, "reason": "at least two hypotheses are required"}
    ids = [h.get("id") for h in hypotheses if isinstance(h, dict)]
    if len(ids) != len(hypotheses) or any(not isinstance(i, str) or not i for i in ids) or len(set(ids)) != len(ids):
        return {"ok": False, "reason": "hypothesis ids must be unique non-empty strings"}
    if any(not _closed_pure_term(h.get("term")) for h in hypotheses):
        return {"ok": False, "reason": "batched selection requires pure Term hypotheses"}
    if not isinstance(candidate_inputs, list) or not candidate_inputs:
        return {"ok": False, "reason": "candidate_inputs must be a non-empty list"}
    observations = observations or []
    for row in observations:
        if not isinstance(row, dict) or set(row) != {"inputs", "expected"} or not isinstance(row["inputs"], dict):
            return {"ok": False, "reason": "invalid observation row"}

    if prediction_matrix is None:
        prediction_matrix = TermPredictionMatrix(evaluate, hypotheses, candidate_inputs)
    elif not prediction_matrix.compatible(evaluate, hypotheses, candidate_inputs):
        return {"ok": False, "reason": "prediction matrix does not match evaluator, hypotheses, or inputs"}

    survivors = list(range(len(hypotheses)))
    for row in observations:
        values = prediction_matrix.values_for(row["inputs"], survivors)
        survivors = [i for i in survivors
                     if values[i] is not _EVAL_FAILED and _same(values[i], row["expected"])]
    if len(survivors) < 2:
        return {"ok": False, "reason": "fewer than two hypotheses fit existing observations",
                "surviving_hypotheses": [ids[i] for i in survivors]}

    used = {_bucket(row["inputs"]) for row in observations}
    scored = []
    for input_index, env in enumerate(candidate_inputs):
        if not isinstance(env, dict) or not env or _bucket(env) in used:
            continue
        values = prediction_matrix.values_for(env, survivors)
        buckets: dict[tuple, int] = {}
        for i in survivors:
            value = (_QUERY_EVALUATION_FAILED if values[i] is _EVAL_FAILED else values[i])
            key = _prediction_bucket(value)
            buckets[key] = buckets.get(key, 0) + 1
        score = _entropy(list(buckets.values()))
        predictions = [(ids[i], (_QUERY_EVALUATION_FAILED if values[i] is _EVAL_FAILED else values[i]))
                       for i in survivors]
        scored.append((score, -input_index, env, predictions, len(buckets)))
    if not scored:
        return {"ok": False, "reason": "no valid unused candidate input"}
    score, _, env, predictions, partition_count = max(scored)
    if score <= 0.0:
        return {"ok": False, "reason": "candidate hypotheses agree on every available input",
                "surviving_hypotheses": [ids[i] for i in survivors]}
    return {"ok": True, "query": env, "entropy_bits": score,
            "partition_count": partition_count,
            "surviving_hypotheses": [ids[i] for i in survivors],
            "predictions": [_prediction_record(hid, value)
                            for hid, value in predictions]}
