"""Public case commitments and evaluator-private held-out material."""
from __future__ import annotations
from copy import deepcopy
from typing import Any
from .mechanics import private_observation, private_truth, spec_for
from .protocol import P5R0Error, digest, is_digest


_PRIVATE_FIELDS = {"generator_seed", "secret_seed", "truth", "private_parameters", "private_domain_family"}


def _reject_nested_private(value: Any, path: str = "task") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if key in {"truth", "target_action", "secret_seed", "private_domain_family", "split"}:
                raise P5R0Error(f"private field: {path}.{key}")
            _reject_nested_private(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _reject_nested_private(child, f"{path}[{index}]")


def validate_manifest_integrity(bundle: dict[str, Any]) -> dict[str, Any]:
    """Validate the public manifest and its evaluator-owned private commitment.

    This deliberately recomputes every commitment and compares the supplied row
    sequence with the committed private-store sequence.  Dict construction is
    never used as an ordering or uniqueness check.
    """
    required = {"schema", "case_index", "index_digest", "truth_digest", "store_digest", "split_digest", "manifest_digest"}
    if not isinstance(bundle, dict) or set(bundle) != required or bundle.get("schema") != "P5R0ManifestV2":
        raise P5R0Error("manifest schema")
    rows = bundle.get("case_index")
    if not isinstance(rows, list) or not rows or len(rows) != 48:
        raise P5R0Error("manifest cardinality")
    if len({row.get("case_id") for row in rows}) != len(rows):
        raise P5R0Error("duplicate case id")
    if bundle["index_digest"] != digest(rows) or not is_digest(bundle["index_digest"]):
        raise P5R0Error("manifest index commitment")
    if bundle["manifest_digest"] != digest({k: v for k, v in bundle.items() if k != "manifest_digest"}) or not is_digest(bundle["manifest_digest"]):
        raise P5R0Error("manifest commitment")
    store = _PRIVATE_STORES.get(bundle["manifest_digest"])
    if not isinstance(store, dict):
        raise P5R0Error("evaluator private case store unavailable")
    private_rows = store.get("cases")
    if not isinstance(private_rows, list) or len(private_rows) != len(rows):
        raise P5R0Error("private store cardinality")
    public_keys = ("case_id", "domain_token", "combination_id", "split", "ordinal", "factors", "modality", "mechanics_digest", "case_digest")
    seen_keys: set[tuple[Any, ...]] = set()
    for index, (public, private) in enumerate(zip(rows, private_rows)):
        if not isinstance(public, dict) or not isinstance(private, dict):
            raise P5R0Error("manifest row")
        if public.get("case_id") in {row.get("case_id") for row in rows[:index]}:
            raise P5R0Error("duplicate case id")
        key = (public.get("domain_token"), public.get("combination_id"), public.get("ordinal"))
        if key in seen_keys:
            raise P5R0Error("duplicate case ordinal")
        seen_keys.add(key)
        if public.get("case_digest") != digest({k: v for k, v in public.items() if k != "case_digest"}):
            raise P5R0Error("case commitment")
        if any(public.get(key) != private.get(key) for key in public_keys):
            raise P5R0Error("manifest/private order commitment")
        if index and public.get("ordinal") == rows[index - 1].get("ordinal") and public.get("case_id") == rows[index - 1].get("case_id"):
            raise P5R0Error("duplicate case")
        spec = spec_for(private)
        expected_truth = private_truth(private, spec)
        if private.get("mechanics_digest") != spec.get("mechanics_digest") or private.get("truth") != expected_truth:
            raise P5R0Error("private truth commitment")
    truth = {row["case_id"]: row["truth"] for row in private_rows}
    expected_store = {"case_index_digest": bundle["index_digest"], "truth_digest": digest(truth), "cases": private_rows}
    if bundle["truth_digest"] != digest(truth) or store.get("truth_digest") != bundle["truth_digest"]:
        raise P5R0Error("truth commitment")
    if store.get("case_index_digest") != bundle["index_digest"] or store.get("store_digest") != digest(expected_store) or bundle["store_digest"] != store.get("store_digest"):
        raise P5R0Error("store commitment")
    if not all(is_digest(bundle.get(key)) for key in ("truth_digest", "store_digest", "split_digest")):
        raise P5R0Error("manifest digest format")
    return bundle

_PRIVATE_STORES: dict[str, dict[str, Any]] = {}


def _legacy_truth(case: dict[str, Any]) -> dict[str, Any]:
    spec = spec_for(case)
    private = dict(case)
    private.setdefault("secret_seed", case.get("generator_seed", digest(case)))
    return private_truth(private, spec)


def _truth(case: dict[str, Any]) -> dict[str, Any]:
    return _legacy_truth(case)


def _private_case(case: dict[str, Any], card: dict[str, Any], combo: dict[str, Any]) -> dict[str, Any]:
    row = dict(case)
    row["modality"] = card["modality"]
    row["factors"] = dict(combo["factors"])
    row["secret_seed"] = case["generator_seed"]
    spec = spec_for(row)
    row["mechanics_digest"] = spec["mechanics_digest"]
    row["truth"] = private_truth(row, spec)
    row["private_parameters"] = {"observation_digest": digest(private_observation(row, spec)), "oracle_version": "P5R0MechanicsSpecV2"}
    return row


def generate_fixtures(split: dict[str, Any], cards: list[dict[str, Any]]) -> dict[str, Any]:
    from .split import build_case_index, validate_split_commitment
    validate_split_commitment(split)
    cases = build_case_index(split, cards)
    # Legacy helper remains available to tests; preregister() never returns this object.
    truth = {case["case_id"]: _truth(case) for case in cases}
    return {"schema": "P5R0FixtureBundleV1", "case_index": cases, "truth": truth, "truth_digest": digest(truth), "index_digest": digest(cases), "bundle_digest": digest({"case_index": cases, "truth_digest": digest(truth)})}


def build_private_manifest(split: dict[str, Any], cards: list[dict[str, Any]]) -> tuple[dict[str, Any], dict[str, Any]]:
    from .split import build_case_index, validate_split_commitment
    validate_split_commitment(split)
    cases = build_case_index(split, cards)
    combos = {row["combination_id"]: row for row in split["combinations"]}
    private_cases = []
    public_cases = []
    for case in cases:
        card = next(c for c in cards if c["domain_token"] == case["domain_token"])
        private = _private_case(case, card, combos[case["combination_id"]])
        private_cases.append(private)
        public = {k: v for k, v in case.items() if k not in {"generator_seed"}}
        public["schema"] = "P5R0CaseManifestV2"
        public["factors"] = dict(combos[case["combination_id"]]["factors"])
        public["modality"] = card["modality"]
        public["mechanics_digest"] = private["mechanics_digest"]
        public["case_digest"] = digest({k: v for k, v in public.items() if k not in {"case_digest"}})
        # The evaluator stores the same opaque commitment that the worker-facing
        # manifest exposes; the removed seed remains private.
        private["case_digest"] = public["case_digest"]
        # The truth token commits the final public case digest, not the
        # provisional commitment used while constructing the private row.
        private["truth"] = private_truth(private, spec_for(private))
        private_cases[-1] = private
        public_cases.append(public)
    truth_digest = digest({row["case_id"]: row["truth"] for row in private_cases})
    index_digest = digest(public_cases)
    store = {"schema": "P5R0CaseStoreV2", "case_index_digest": index_digest, "truth_digest": truth_digest, "cases": private_cases, "store_digest": digest({"case_index_digest": index_digest, "truth_digest": truth_digest, "cases": private_cases})}
    manifest = {"schema": "P5R0ManifestV2", "case_index": public_cases, "index_digest": index_digest, "truth_digest": truth_digest, "store_digest": store["store_digest"], "split_digest": split["split_digest"], "manifest_digest": ""}
    manifest["manifest_digest"] = digest({k: v for k, v in manifest.items() if k != "manifest_digest"})
    _PRIVATE_STORES[manifest["manifest_digest"]] = store
    return manifest, store


def private_store_for(bundle: dict[str, Any]) -> dict[str, Any]:
    validate_manifest_integrity(bundle)
    return _PRIVATE_STORES[bundle["manifest_digest"]]


def make_task(private_case: dict[str, Any], *, task_nonce: str, arm_context: dict[str, Any] | None = None, state: dict[str, Any] | None = None, step_index: int = 0) -> dict[str, Any]:
    spec = spec_for(private_case)
    task = {"schema": "P5R0WorkerTaskV2", "case_token": digest({"case": private_case["case_digest"], "nonce": task_nonce}), "task_nonce": task_nonce, "observation": private_observation(private_case, spec, state), "legal_actions": list(spec["legal_actions"]), "protocol_budget": {"max_steps": spec["max_steps"], "frame_bytes": 65536, "wall_seconds": 3}, "step_index": step_index, "arm": arm_context["arm"] if arm_context else "cold_reset"}
    if set(task) != {"schema", "case_token", "task_nonce", "observation", "legal_actions", "protocol_budget", "step_index", "arm"}: raise P5R0Error("worker task")
    return task


def worker_view(case: dict[str, Any], *, task_nonce: str) -> dict[str, Any]:
    # Compatibility projection for legacy callers; it still derives only from a
    # case object and never contains truth or family information.
    private = dict(case); private.setdefault("secret_seed", case.get("generator_seed", digest(case))); private.setdefault("modality", "grid_discrete")
    task = make_task(private, task_nonce=task_nonce)
    return {"schema": "P5R0WorkerTaskV1", "case_token": task["case_token"], "task_nonce": task["task_nonce"], "observation": task["observation"], "legal_actions": task["legal_actions"], "protocol_budget": task["protocol_budget"]}



def make_task_v3(private_case: dict[str, Any], *, task_nonce: str, arm_context: dict[str, Any] | None = None, episode_state: dict[str, Any] | None = None, persistent_projection: dict[str, Any] | None = None, control_metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    """Create the V3 worker envelope without evaluator-private truth.

    Control metadata is deliberately public and commitment-only; it never carries
    a target action, truth, seed, split, or private domain family.
    """
    spec = spec_for(private_case); episode = dict(episode_state or {"step": 0})
    observation = private_observation(private_case, spec, episode)
    if spec["memory"] == "persistent":
        projection = dict(persistent_projection or {})
        observation["persistent"] = {"adoption_count": int(projection.get("adoption_count", 0)), "namespace_digest": projection.get("namespace_digest")}
    task = {"schema": "P5R0WorkerTaskV3", "case_token": digest({"case": private_case["case_digest"], "nonce": task_nonce}), "task_nonce": task_nonce, "observation": observation, "legal_actions": list(spec["legal_actions"]), "protocol_budget": {"max_steps": spec["max_steps"], "frame_bytes": 65536, "wall_seconds": 3}, "episode_step": int(episode.get("step", 0)), "reset_policy": "fresh_case", "arm": arm_context["arm"] if arm_context else "cold_reset", "persistent_projection": dict(persistent_projection or {}), "control": dict(control_metadata) if control_metadata is not None else None}
    if set(task) != {"schema", "case_token", "task_nonce", "observation", "legal_actions", "protocol_budget", "episode_step", "reset_policy", "arm", "persistent_projection", "control"}: raise P5R0Error("worker task v3")
    return task
