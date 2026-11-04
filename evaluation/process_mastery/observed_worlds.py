"""Independent finite observed-world dynamics for P18 experiments.

Hidden equations remain inside the simulator. Its observation and receipt API
exposes only visible features, legal actions, and the executed consequence.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import random
from typing import Any


@dataclass
class ObservedWorld:
    family: str
    seed: int
    world_id: str
    _mechanism: str
    _objects: dict[str, dict[str, str]]
    epoch: int = 0
    _latent_map: dict[str, str] | None = None

    @classmethod
    def create(cls, family: str, seed: int) -> "ObservedWorld":
        if family not in {"object_mechanism", "temporal_latent"}:
            raise ValueError("unsupported P18 world family")
        rng = random.Random(seed)
        mechanism = ("surface" if rng.randrange(2) == 0 else "material") if family == "object_mechanism" else "temporal_cue"
        latent_map = ({"low": "calm", "high": "surge"} if rng.randrange(2) == 0
                      else {"low": "surge", "high": "calm"}) if family == "temporal_latent" else None
        objects = {
            "object-0": {"surface": "rough", "material": "copper"},
            "object-1": {"surface": "smooth", "material": "wood"},
            "object-2": {"surface": "rough", "material": "copper"},
            "object-3": {"surface": "smooth", "material": "wood"},
            # This held combination distinguishes the two observation-built
            # models without revealing which feature the world uses.
            "object-4": {"surface": "rough", "material": "wood"},
            "object-5": {"surface": "smooth", "material": "copper"},
        }
        return cls(family, int(seed), f"p18:{family}:{seed}", mechanism, objects, 0, latent_map)

    def observe(self, object_id: str) -> dict[str, Any]:
        if self.family != "object_mechanism":
            raise ValueError("object observations are unavailable in temporal worlds")
        if object_id not in self._objects:
            raise KeyError("unknown object")
        return {"world_id": self.world_id, "world_epoch": self.epoch,
                "object_id": object_id, "object_type": "Object",
                "features": dict(self._objects[object_id]),
                "state": "cold", "legal_actions": ("heat", "tap")}

    def execute(self, observation: dict[str, Any], action: str) -> dict[str, Any]:
        if observation.get("world_id") != self.world_id:
            raise ValueError("observation belongs to another world")
        if observation.get("world_epoch") != self.epoch:
            raise ValueError("stale observation")
        if action not in observation.get("legal_actions", ()):
            raise ValueError("illegal action")
        if action == "heat":
            key = self._mechanism
            value = observation["features"][key]
            active = value == ("rough" if key == "surface" else "copper")
            after = "warm" if active else "cool"
        else:
            after = "cold"
        self.epoch += 1
        body = {"world_id": self.world_id, "world_epoch": self.epoch,
                "object_id": observation["object_id"], "action": action,
                "before_state": observation["state"], "observed_state": after,
                "source_epoch": observation["world_epoch"]}
        body["receipt_sha256"] = hashlib.sha256(json.dumps(
            body, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        return body

    def verify_receipt(self, receipt: dict[str, Any]) -> bool:
        if self.family != "object_mechanism":
            return False
        if receipt.get("world_id") != self.world_id or receipt.get("world_epoch") != self.epoch:
            return False
        obs = self.observe(receipt.get("object_id", ""))
        # Receipts are verified against hidden world state without revealing
        # the equation to the learner or scorer-facing input.
        if receipt.get("action") not in obs["legal_actions"]:
            return False
        key = self._mechanism
        value = self._objects[receipt["object_id"]][key]
        active = value == ("rough" if key == "surface" else "copper")
        expected = ("warm" if active else "cool") if receipt["action"] == "heat" else "cold"
        unsigned = {k: v for k, v in receipt.items() if k != "receipt_sha256"}
        digest = hashlib.sha256(json.dumps(unsigned, sort_keys=True,
            separators=(",", ":")).encode()).hexdigest()
        return (receipt.get("observed_state") == expected
                and receipt.get("receipt_sha256") == digest)

    def observe_temporal(self, sample_index: int) -> dict[str, Any]:
        if self.family != "temporal_latent":
            raise ValueError("temporal observations are unavailable in object worlds")
        return {"world_id": self.world_id, "world_epoch": self.epoch,
                "sample_id": f"sample-{int(sample_index)}",
                "cue": "low" if sample_index % 2 == 0 else "high",
                "sampling_interval": 1.0, "complete_window": True}

    def execute_temporal(self, observation: dict[str, Any]) -> dict[str, Any]:
        if self.family != "temporal_latent" or observation.get("world_id") != self.world_id:
            raise ValueError("temporal observation belongs to another world")
        if observation.get("world_epoch") != self.epoch:
            raise ValueError("stale temporal observation")
        cue = observation.get("cue")
        if cue not in {"low", "high"}:
            raise ValueError("unsupported temporal cue")
        self.epoch += 1
        body = {"world_id": self.world_id, "world_epoch": self.epoch,
                "sample_id": observation["sample_id"], "cue": cue,
                "observed_outcome": self._latent_map[cue],
                "sampling_interval": observation["sampling_interval"]}
        body["receipt_sha256"] = hashlib.sha256(json.dumps(
            body, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        return body

    def verify_temporal_receipt(self, receipt: dict[str, Any]) -> bool:
        if self.family != "temporal_latent" or receipt.get("world_id") != self.world_id:
            return False
        if receipt.get("world_epoch") != self.epoch:
            return False
        unsigned = {k: v for k, v in receipt.items() if k != "receipt_sha256"}
        digest = hashlib.sha256(json.dumps(unsigned, sort_keys=True,
            separators=(",", ":")).encode()).hexdigest()
        return (receipt.get("observed_outcome") == self._latent_map.get(receipt.get("cue"))
                and receipt.get("receipt_sha256") == digest)
