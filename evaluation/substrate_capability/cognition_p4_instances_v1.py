"""Deterministic P4 D5 transfer instances; oracle labels are evaluation-only."""
from __future__ import annotations

import random
import hashlib
import re
from copy import deepcopy
import json


FAMILY_SALTS = {"graph_role": 0x47524150, "numeric_sequence": 0x4E554D53}
ARM_SALTS = {"recall_on": 0x11, "recall_off": 0x22, "mismatched_source": 0x33}


def _graph_roles(rng, compatible: bool):
    source_ids = [f"src-{i}-{rng.randrange(1_000_000)}" for i in range(3)]
    target_ids = [f"tgt-{i}-{rng.randrange(1_000_000)}" for i in range(4)]
    while set(source_ids) & set(target_ids):
        target_ids = [f"tgt-{i}-{rng.randrange(1_000_000)}" for i in range(4)]
    source = {"frame_id": "source-frame",
              "nodes": list(zip(("source", "relation", "target"), source_ids)),
              "edges": [(source_ids[0], "arg", source_ids[1]),
                        (source_ids[1], "supports", source_ids[2])]}
    target = {"frame_id": "target-frame",
              "nodes": [("source", target_ids[0]), ("relation", target_ids[1]),
                        ("candidate", target_ids[2]), ("candidate", target_ids[3])],
              "edges": [(target_ids[0], "arg", target_ids[1]),
                        (target_ids[1], "supports" if compatible else "contradicts",
                         target_ids[2]),
                        (target_ids[1], "contradicts" if compatible else "enables",
                         target_ids[3])]}
    return source, target, {"target": target_ids[2] if compatible else None,
                            "relation": "supports"}


def _numeric_sequence(rng, compatible: bool):
    a = rng.randint(2, 9)
    b = rng.randint(-5, 5)
    source_x = list(range(5))
    source_y = [a * x + b for x in source_x]
    offset = rng.randint(20, 50)
    target_x = list(range(offset, offset + 4))
    target_y = [(a if compatible else a + 10) * x + b for x in target_x]
    candidate_values = [target_y[-1], target_y[-1] + 2]
    candidate_ids = [f"candidate-{rng.randrange(1_000_000)}" for _ in range(2)]
    while candidate_ids[0] == candidate_ids[1]:
        candidate_ids[1] = f"candidate-{rng.randrange(1_000_000)}"
    source = {"x": source_x, "y": source_y, "frame_id": "source-frame"}
    target = {"x": target_x[:-1], "y": target_y[:-1], "frame_id": "target-frame",
              "candidates": [{"id": candidate_ids[i], "x": target_x[-1],
                              "y": candidate_values[i]} for i in range(2)]}
    oracle = {"next_x": target_x[-1] if compatible else None,
              "next_y": target_y[-1] if compatible else None,
              "target_candidate_id": candidate_ids[0] if compatible else None,
              "compatible": compatible}
    return source, target, oracle


def draw_transfer(direction: str, seed: int, compatible: bool = True) -> dict:
    """Return agent-visible source/target plus a strictly external scoring oracle."""
    rng = random.Random(int(seed))
    if direction == "graph_role":
        source, target, oracle = _graph_roles(rng, compatible)
    elif direction == "numeric_sequence":
        source, target, oracle = _numeric_sequence(rng, compatible)
    else:
        raise ValueError(f"unknown P4 transfer direction: {direction}")
    return {
        "family": direction, "seed": int(seed), "compatible": bool(compatible),
        "source_exposure": source, "target_problem": target,
        "source_id": f"source-{direction}-{seed}",
        "target_id": f"target-{direction}-{seed}",
        "frame_map": {"source-frame": "target-frame"},
        "scoring_oracle": {**oracle, "compatible": bool(compatible)},
    }


def agent_payload(instance: dict) -> dict:
    """Return agent-visible task data with every scoring label/seed removed."""
    hidden = {"scoring_oracle", "compatible", "seed"}
    payload = {key: deepcopy(value) for key, value in instance.items()
               if key not in hidden}
    # Top-level IDs are bookkeeping only. They must not encode the deterministic
    # draw index, which would let a participant reproduce the scoring oracle.
    for key in ("source_id", "target_id"):
        value = str(payload.get(key, ""))
        payload[key] = hashlib.sha256(value.encode("utf-8")).hexdigest()[:20]
    if payload.get("family") == "graph_role":
        remap = {}
        for side in ("source_exposure", "target_problem"):
            nodes = payload[side]["nodes"]
            for _role, node_id in nodes:
                remap[str(node_id)] = hashlib.sha256(
                    f"{side}:{node_id}".encode("utf-8")).hexdigest()[:20]
            payload[side]["nodes"] = [(role, remap[str(node_id)])
                                        for role, node_id in nodes]
            payload[side]["edges"] = [
                (remap.get(str(src), str(src)), edge,
                 remap.get(str(tgt), str(tgt)))
                for src, edge, tgt in payload[side]["edges"]]
    else:
        for candidate in payload.get("target_problem", {}).get("candidates", []):
            candidate["id"] = hashlib.sha256(
                str(candidate["id"]).encode("utf-8")).hexdigest()[:20]
    return payload


def draw_panel(prereg_hash: str, first: int = 0, end: int = 200, *,
               development: bool = False) -> list[dict]:
    """Build the registered paired D5 target/decoy panel.

    Each direction has `end-first` compatible targets and, for registered
    indices below 100, one incompatible decoy. Three arms receive byte-identical target data;
    only their registered source/frame condition differs. Oracle labels remain
    in the evaluation-only sibling field and never enter `agent_payload`.
    Development checks must pass `development=True` and use indices 1000-1199,
    disjoint from the registered 0-199 draw.
    """
    if not re.fullmatch(r"[0-9a-fA-F]{40,64}", str(prereg_hash)):
        raise ValueError("prereg_hash must be a full 40-64 digit hexadecimal hash")
    first, end = int(first), int(end)
    limit_low, limit_high = (1000, 1200) if development else (0, 200)
    if first < limit_low or end < first or end > limit_high:
        label = "development range must satisfy 1000 <= first <= end <= 1200" if development else \
            "registered range must satisfy 0 <= first <= end <= 200"
        raise ValueError(label)
    base = int(prereg_hash[:8], 16)
    panel = []
    for direction, family_salt in FAMILY_SALTS.items():
        for index in range(first, end):
            seed = base + 7919 * index + family_salt
            instances = [("target", draw_transfer(direction, seed, True))]
            if (index - first < 100 if development else index < 100):
                instances.append(("incompatible_decoy", draw_transfer(
                    direction, seed + 0xDEC0, False)))
            for kind, case in instances:
                mismatch_case = draw_transfer(direction, seed + 0xBAD5, False)
                if direction == "graph_role":
                    edges = mismatch_case["source_exposure"]["edges"]
                    mismatch_case["source_exposure"]["edges"] = [
                        (src, "expresses" if edge == "supports" else edge, tgt)
                        for src, edge, tgt in edges]
                else:
                    source = mismatch_case["source_exposure"]
                    source["y"] = [value + 100 * x
                                    for x, value in zip(source["x"], source["y"])]
                paired_id = hashlib.sha256(
                    f"{prereg_hash}:{direction}:{index}:{kind}".encode()).hexdigest()[:24]
                target_payload = agent_payload(case)
                target_digest = hashlib.sha256(json.dumps(
                    target_payload["target_problem"], sort_keys=True,
                    separators=(",", ":")).encode("utf-8")).hexdigest()
                arms = {}
                for arm, arm_salt in ARM_SALTS.items():
                    visible = dict(target_payload)
                    visible["target_digest"] = target_digest
                    visible["arm_key"] = hashlib.sha256(
                        f"{paired_id}:{arm_salt}".encode()).hexdigest()[:16]
                    if arm == "mismatched_source":
                        mismatched = agent_payload(mismatch_case)
                        visible["source_exposure"] = mismatched["source_exposure"]
                        visible["source_id"] = mismatched["source_id"]
                    arms[arm] = visible
                panel.append({
                    "paired_id": paired_id, "family": direction,
                    "draw_index": index, "case_kind": kind,
                    "arms": arms,
                    "scoring_oracle": {
                        **case["scoring_oracle"],
                        "target_candidate_key": (
                            hashlib.sha256(
                                f"target_problem:{case['scoring_oracle']['target']}".encode()
                            ).hexdigest()[:20] if direction == "graph_role"
                            and case["scoring_oracle"].get("target") else
                            hashlib.sha256(str(case["scoring_oracle"]["target_candidate_id"])
                                           .encode()).hexdigest()[:20]
                            if direction == "numeric_sequence"
                            and case["scoring_oracle"].get("target_candidate_id") else None),
                    },
                })
    return panel
