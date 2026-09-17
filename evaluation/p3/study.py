"""Evaluator-owned P3-E1 task release, accounting, statistics, and decision rules."""
from __future__ import annotations

import hashlib
import math
import random
import time
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from evaluation.p0a.canonical import canonical_bytes, object_hash, sign, verify_signature
from .lock import THRESHOLDS
from .protocol import P3ProtocolError, is_digest

DISTRIBUTIONS = tuple(f"shift-{family}-{shift}" for family in ("toy-a", "toy-b", "toy-c") for shift in ("struct-1", "struct-2", "struct-3", "struct-4"))
ARMS = ("governed", "frozen", "reset_memory", "no_consolidation")
FAILURE_SCORE = 0
ALPHA_MICRO = THRESHOLDS["familywise_alpha_milli"] * 1000


def _seed(seed: bytes, *parts: str) -> int:
    if not isinstance(seed, bytes) or len(seed) < 32: raise P3ProtocolError("evaluator seed")
    return int.from_bytes(hashlib.sha256(seed + b"\0" + "\0".join(parts).encode()).digest()[:8], "big")
def _integer(value: Any, name: str, low: int = 0, high: int = 100000) -> int:
    if type(value) is not int or not low <= value <= high: raise P3ProtocolError(name)
    return value

_TASK_FIELDS = {"schema", "key_id", "lock_digest", "run_id", "distribution_id", "pair_id", "sequence", "ordinal", "nonce", "expires_at", "budget", "task_digest", "signature"}
_TASK_BUDGET = {key: THRESHOLDS[key] for key in ("cpu_count", "memory_bytes", "wall_seconds", "graph_transactions", "network_bytes")}


def _pair_id(distribution: str, ordinal: int) -> str:
    return "p3-" + hashlib.sha256(canonical_bytes({"distribution": distribution, "ordinal": ordinal})).hexdigest()[:24]


def validate_task_envelope(value: Mapping[str, Any], *, trusted_keys: Mapping[str, Any], lock_digest: str,
                           run_id: str, expected_sequence: int | None = None, now: int | None = None) -> dict[str, Any]:
    """Authenticate one canonical evaluator release before either side parses it.

    Sequence is global (0..359), while ordinal is the position in its distribution.
    A nonce binds a particular evaluator issuance and expiry prevents re-use later.
    """
    if not isinstance(value, Mapping) or set(value) != _TASK_FIELDS or value.get("schema") != "P3TaskEnvelopeV1":
        raise P3ProtocolError("task envelope schema")
    if value.get("lock_digest") != lock_digest or value.get("run_id") != run_id:
        raise P3ProtocolError("task envelope lock/run binding")
    key_id = value.get("key_id")
    if not isinstance(key_id, str) or key_id not in trusted_keys:
        raise P3ProtocolError("task envelope authority")
    sequence, ordinal = value.get("sequence"), value.get("ordinal")
    distribution = value.get("distribution_id")
    if (type(sequence) is not int or not 0 <= sequence < THRESHOLDS["distribution_count"] * THRESHOLDS["pairs_per_distribution"]
            or type(ordinal) is not int or not 0 <= ordinal < THRESHOLDS["pairs_per_distribution"]
            or distribution not in DISTRIBUTIONS or sequence != DISTRIBUTIONS.index(distribution) * THRESHOLDS["pairs_per_distribution"] + ordinal
            or (expected_sequence is not None and sequence != expected_sequence)):
        raise P3ProtocolError("task envelope sequence")
    if value.get("pair_id") != _pair_id(distribution, ordinal) or not is_digest(value.get("nonce")):
        raise P3ProtocolError("task envelope identity")
    if type(value.get("expires_at")) is not int or value["expires_at"] <= (int(time.time()) if now is None else now):
        raise P3ProtocolError("task envelope expiry")
    if value.get("budget") != _TASK_BUDGET:
        raise P3ProtocolError("task envelope budget")
    unsigned = {key: item for key, item in value.items() if key not in {"task_digest", "signature"}}
    if value.get("task_digest") != object_hash(unsigned):
        raise P3ProtocolError("task envelope digest")
    try:
        verify_signature(dict(value), trusted_keys[key_id])
    except Exception as exc:
        raise P3ProtocolError("task envelope signature") from exc
    return dict(value)


@dataclass
class TaskReleaseLedger:
    """Separate worker/evaluator single-use release state; no caller-controlled set."""
    trusted_keys: Mapping[str, Any]
    lock_digest: str
    run_id: str
    next_sequence: int = 0
    consumed: set[str] = field(default_factory=set)

    def consume(self, envelope: Mapping[str, Any]) -> dict[str, Any]:
        parsed = validate_task_envelope(envelope, trusted_keys=self.trusted_keys, lock_digest=self.lock_digest,
                                        run_id=self.run_id, expected_sequence=self.next_sequence)
        task_digest = parsed["task_digest"]
        if task_digest in self.consumed:
            raise P3ProtocolError("task envelope replay")
        self.consumed.add(task_digest)
        self.next_sequence += 1
        return parsed


def materialize_study(*, seed: bytes, signing_key: Any, run_id: str, lock_digest: str,
                      expires_at: int | None = None, key_id: str = "evaluator-task") -> tuple[dict[str, Any], dict[str, list[dict[str, Any]]], dict[str, dict[str, Any]]]:
    if not isinstance(run_id, str) or not run_id or not is_digest(lock_digest) or not isinstance(key_id, str) or not key_id:
        raise P3ProtocolError("study binding")
    expiry = int(time.time()) + 3600 if expires_at is None else expires_at
    if type(expiry) is not int or expiry <= int(time.time()): raise P3ProtocolError("study expiry")
    public: dict[str, list[dict[str, Any]]] = {}; private: dict[str, dict[str, Any]] = {}; index=[]
    for distribution_index, distribution in enumerate(DISTRIBUTIONS):
        entries=[]
        for ordinal in range(THRESHOLDS["pairs_per_distribution"]):
            sequence = distribution_index * THRESHOLDS["pairs_per_distribution"] + ordinal
            pair_id = _pair_id(distribution, ordinal)
            envelope={"schema":"P3TaskEnvelopeV1", "key_id":key_id, "lock_digest":lock_digest, "run_id":run_id,
                      "distribution_id":distribution, "pair_id":pair_id, "sequence":sequence, "ordinal":ordinal,
                      "nonce":"sha256:" + hashlib.sha256(seed + run_id.encode() + sequence.to_bytes(4, "big")).hexdigest(),
                      "expires_at":expiry, "budget":dict(_TASK_BUDGET)}
            envelope["task_digest"] = object_hash(envelope); envelope["signature"] = sign(envelope, signing_key)
            entries.append(envelope); index.append({"distribution_id":distribution,"pair_id":pair_id,"sequence":sequence,"task_digest":envelope["task_digest"]})
            private[pair_id]={"truth_commitment":"sha256:" + hashlib.sha256(seed + pair_id.encode()).hexdigest(), "release_index":sequence}
        public[distribution]=entries
    manifest={"schema":"P3StudyManifestV1","lock_digest":lock_digest,"run_id":run_id,"distribution_count":12,"pairs_per_distribution":30,"entries":index,"seed_commitment":"sha256:"+hashlib.sha256(seed).hexdigest()}
    manifest["manifest_digest"] = object_hash(manifest)
    return manifest, public, private


def release_next(released: set[str], package: Mapping[str, Sequence[Mapping[str, Any]]], distribution: str) -> dict[str, Any]:
    # Compatibility helper for coordinator selection.  Authentication and replay
    # prevention occur in the two independent TaskReleaseLedger instances.
    if distribution not in package: raise P3ProtocolError("unknown distribution")
    for envelope in package[distribution]:
        if envelope["task_digest"] not in released:
            released.add(envelope["task_digest"]); return dict(envelope)
    raise P3ProtocolError("release exhausted")

def validate_pair_execution(value: Mapping[str, Any], envelope: Mapping[str, Any]) -> dict[str, Any]:
    """Validate retained four-arm evidence against the exact released task."""
    needed={"schema","pair_id","sequence","task_digest","arms","receipt_digest","safety_ok","resources","retention_delta","transfer_delta"}
    if not isinstance(value, Mapping) or set(value) != needed or value.get("schema") != "P3PairExecutionV1": raise P3ProtocolError("pair execution schema")
    if (value["pair_id"] != envelope.get("pair_id") or value["sequence"] != envelope.get("sequence")
            or value["task_digest"] != envelope.get("task_digest") or not is_digest(value["receipt_digest"])):
        raise P3ProtocolError("pair execution binding")
    arms=value["arms"]
    if not isinstance(arms, Mapping) or set(arms) != set(ARMS): raise P3ProtocolError("four arm accounting")
    for arm in ARMS:
        record=arms[arm]
        if not isinstance(record, Mapping) or set(record) != {"score","status"}: raise P3ProtocolError("arm record")
        _integer(record["score"], "arm score")
        if record["status"] not in {"ok","failure"}: raise P3ProtocolError("arm status")
    if type(value["safety_ok"]) is not bool: raise P3ProtocolError("pair safety")
    resources=value["resources"]
    budget=envelope.get("budget")
    if not isinstance(resources, Mapping) or set(resources) != set(ARMS) or not isinstance(budget, Mapping): raise P3ProtocolError("resource ledger")
    resource_fields={"cpu_count","memory_bytes","wall_seconds","graph_transactions","network_bytes"}
    resources_ok=True
    for arm in ARMS:
        ledger=resources[arm]
        if not isinstance(ledger, Mapping) or set(ledger) != resource_fields or any(type(ledger[key]) is not int or ledger[key] < 0 for key in resource_fields): raise P3ProtocolError("resource ledger")
        resources_ok &= all(ledger[key] <= budget.get(key, -1) for key in resource_fields)
    _integer(value["retention_delta"], "retention delta", -100000, 100000)
    _integer(value["transfer_delta"], "transfer delta", -100000, 100000)
    return {key: value[key] for key in needed}, resources_ok

def _percentile(values: list[int], numerator: int, denominator: int) -> int:
    values=sorted(values); return values[(len(values)-1)*numerator//denominator]
def bootstrap_ci(deltas: Sequence[int], *, seed: int, resamples: int = THRESHOLDS["bootstrap_resamples"]) -> tuple[int,int]:
    if len(deltas) != 30 or not all(type(v) is int for v in deltas) or resamples <= 0: raise P3ProtocolError("paired scores")
    rng=random.Random(seed); means=[]
    for _ in range(resamples): means.append(sum(deltas[rng.randrange(30)] for _ in range(30))//30)
    return _percentile(means, 25, 1000), _percentile(means, 975, 1000)
def sign_permutation_pvalues(deltas: Sequence[int], *, seed: int, permutations: int = THRESHOLDS["sign_permutations"]) -> tuple[int,int]:
    if len(deltas) != 30 or permutations <= 0: raise P3ProtocolError("paired scores")
    observed=sum(deltas); rng=random.Random(seed); improve=harm=0
    for _ in range(permutations):
        shuffled=sum(value if rng.getrandbits(1) else -value for value in deltas)
        improve += shuffled >= observed; harm += shuffled <= observed
    return ((1+improve)*1_000_000//(permutations+1), (1+harm)*1_000_000//(permutations+1))
def holm(pvalues: Sequence[int]) -> list[int]:
    if len(pvalues) != 12 or any(type(p) is not int or not 0 <= p <= 1_000_000 for p in pvalues): raise P3ProtocolError("Holm p values")
    adjusted=[0]*12; maximum=0
    for rank,index in enumerate(sorted(range(12),key=lambda i:pvalues[i])):
        maximum=max(maximum, min(1_000_000, pvalues[index]*(12-rank))); adjusted[index]=maximum
    return adjusted
def classify(delta: int, ci: tuple[int,int], improve_p: int, harm_p: int, *, complete: bool) -> str:
    if not complete: return "inconclusive"
    if delta >= THRESHOLDS["improve_delta_min"] and ci[0] > 0 and improve_p <= ALPHA_MICRO: return "improve"
    if delta <= THRESHOLDS["harm_delta_max"] and ci[1] < 0 and harm_p <= ALPHA_MICRO: return "harm"
    return "inconclusive"
def score_distribution(scores: Sequence[Mapping[str, Any]], *, seed: bytes, distribution: str,
                       bootstrap_resamples: int = THRESHOLDS["bootstrap_resamples"],
                       permutations: int = THRESHOLDS["sign_permutations"]) -> dict[str, Any]:
    if len(scores)!=30: raise P3ProtocolError("all pairs required")
    deltas=[]; complete=True
    for item in scores:
        if set(item)!={"pre","adopt","status"} or not all(type(item[k]) is int and 0<=item[k]<=100000 for k in ("pre","adopt")): raise P3ProtocolError("score record")
        valid=item["status"]=="ok"; complete &= valid; deltas.append(item["adopt"]-item["pre"] if valid else FAILURE_SCORE-item["pre"])
    delta=sum(deltas)//30; sd=math.isqrt(sum((x-delta)**2 for x in deltas)//29)
    ci=bootstrap_ci(deltas,seed=_seed(seed,"bootstrap",distribution),resamples=bootstrap_resamples)
    improve,harm=sign_permutation_pvalues(deltas,seed=_seed(seed,"sign",distribution),permutations=permutations)
    return {"deltas":deltas,"delta":delta,"sample_sd":sd,"ci":ci,"improvement_p":improve,"harm_p":harm,"complete":complete}

def score_four_arm_distribution(records: Sequence[Mapping[str, Any]], *, package: Mapping[str, Sequence[Mapping[str, Any]]],
                                distribution: str, seed: bytes) -> tuple[dict[str, Any], list[int], list[int], bool, bool]:
    """Bind all 30 results to their evaluator-issued sequential envelopes."""
    if len(records) != 30: raise P3ProtocolError("four arm pair coverage")
    released:set[str]=set(); scores=[]; retention=[]; transfer=[]; safety=True; resources=True
    for record in records:
        envelope=release_next(released, package, distribution)
        parsed, within_budget=validate_pair_execution(record,envelope)
        arms=parsed["arms"]
        status="ok" if all(arms[arm]["status"] == "ok" for arm in ARMS) else "failure"
        scores.append({"pre":arms["frozen"]["score"],"adopt":arms["governed"]["score"],"status":status})
        retention.append(parsed["retention_delta"]); transfer.append(parsed["transfer_delta"])
        safety &= parsed["safety_ok"]; resources &= within_budget
    return score_distribution(scores, seed=seed, distribution=distribution), retention, transfer, safety, resources

def _hierarchical_ci(outcomes: Mapping[str, Mapping[str, Any]], *, seed: bytes,
                     resamples: int = THRESHOLDS["bootstrap_resamples"]) -> tuple[int, int]:
    if set(outcomes) != set(DISTRIBUTIONS) or resamples <= 0: raise P3ProtocolError("aggregate outcomes")
    source=[list(outcomes[d]["deltas"]) for d in DISTRIBUTIONS]
    if any(len(row) != 30 or not all(type(v) is int for v in row) for row in source): raise P3ProtocolError("aggregate deltas")
    rng=random.Random(_seed(seed,"hierarchical-bootstrap")); means=[]
    for _ in range(resamples):
        means.append(sum(source[rng.randrange(12)][rng.randrange(30)] for _ in range(12) for _ in range(30))//360)
    return _percentile(means,25,1000),_percentile(means,975,1000)
def _transfer_ci(deltas: Sequence[int], *, seed: bytes,
                 resamples: int = THRESHOLDS["bootstrap_resamples"]) -> tuple[int,int]:
    if len(deltas) != 12 or not all(type(v) is int for v in deltas): raise P3ProtocolError("transfer deltas")
    rng=random.Random(_seed(seed,"transfer-bootstrap")); values=[]
    for _ in range(resamples): values.append(sum(deltas[rng.randrange(12)] for _ in range(12))//12)
    return _percentile(values,25,1000),_percentile(values,975,1000)

def e1_decision(*, outcomes: Mapping[str, Mapping[str, Any]], retention_deltas: Sequence[int],
                transfer_deltas: Sequence[int], safety_ok: bool, resources_ok: bool, custody_ok: bool,
                seed: bytes) -> dict[str, Any]:
    """Apply the locked aggregate 8/12/no-harm and secondary gates."""
    if len(retention_deltas) != 360 or not all(type(v) is int for v in retention_deltas): raise P3ProtocolError("retention coverage")
    if type(safety_ok) is not bool or type(resources_ok) is not bool or type(custody_ok) is not bool: raise P3ProtocolError("aggregate controls")
    aggregate=sum(outcomes[d]["delta"] for d in DISTRIBUTIONS)//12
    aggregate_ci=_hierarchical_ci(outcomes,seed=seed)
    transfer=sum(transfer_deltas)//12 if len(transfer_deltas) == 12 else (_ for _ in ()).throw(P3ProtocolError("transfer coverage"))
    transfer_ci=_transfer_ci(transfer_deltas,seed=seed)
    classifications=[outcomes[d]["classification"] for d in DISTRIBUTIONS]
    checks={"aggregate_delta":aggregate >= THRESHOLDS["improve_delta_min"], "aggregate_ci":aggregate_ci[0] > 0,
            "eight_improve":classifications.count("improve") >= 8, "no_harm":"harm" not in classifications,
            "retention":all(value >= -5000 for value in retention_deltas), "transfer":transfer >= 5000 and transfer_ci[0] > 0,
            "safety":safety_ok, "resources":resources_ok, "custody":custody_ok}
    return {"schema":"P3E1DecisionV1","aggregate_delta":aggregate,"aggregate_ci":aggregate_ci,
            "transfer_delta":transfer,"transfer_ci":transfer_ci,"improve_count":classifications.count("improve"),
            "harm_count":classifications.count("harm"),"checks":checks,
            "decision":"adopt" if all(checks.values()) else "reject", "rollback_required":not all(checks.values())}

def seal_results(*, run_id:str, lock_digest:str, outcomes:Mapping[str,Mapping[str,Any]], signer:Any,
                 release_bindings:Mapping[str,str]) -> dict[str,Any]:
    required={"p0_go_digest","p1_go_digest","p2_go_digest","native_export_digest","candidate_digest","pre_snapshot_digest"}
    if set(release_bindings)!=required or any(not is_digest(value) for value in release_bindings.values()): raise P3ProtocolError("result release bindings")
    if set(outcomes)!=set(DISTRIBUTIONS): raise P3ProtocolError("all distributions required")
    improvement=holm([outcomes[d]["improvement_p"] for d in DISTRIBUTIONS]); harm=holm([outcomes[d]["harm_p"] for d in DISTRIBUTIONS]); records=[]
    for i,d in enumerate(DISTRIBUTIONS):
        record=dict(outcomes[d]); record["ci"]=list(record["ci"]); record["distribution_id"]=d; record["adjusted_improvement_p"]=improvement[i]; record["adjusted_harm_p"]=harm[i]; record["classification"]=classify(record["delta"],record["ci"],improvement[i],harm[i],complete=record["complete"]); records.append(record)
    seal={"schema":"P3ResultSealV1","run_id":run_id,"lock_digest":lock_digest,"release_bindings":dict(release_bindings),"outcomes":records}; seal["seal_digest"]=object_hash(seal); seal["signature"]=sign(seal,signer,"seal_digest"); return seal
