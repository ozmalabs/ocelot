"""Evaluator-owned signed P5-R0 DomainCards and independent authority checks."""
from __future__ import annotations
from typing import Any
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from evaluation.p0a.canonical import b64decode, b64encode, sign, verify_signature
from .protocol import AXES, DOMAINS, P5R0Error, digest, is_digest

_CARD_FIELDS = {"schema", "card_id", "card_digest", "domain_token", "private_domain_family", "modality", "observation_schema_digest", "state_schema_digest", "action_schema_digest", "effect_algebra_digest", "latent_mechanics_digest", "reward_constraint_digest", "tool_vocabulary_digest", "transition_oracle_digest", "reset_policy_digest", "safety_policy_digest", "resource_envelope", "generator_digest", "closure_digest", "case_commitments", "signature", "authority_id", "key_id", "authority_public_key"}


def authority_from_private(key: Ed25519PrivateKey, authority_id: str = "p5-r0-evaluator", key_id: str = "p5-r0-domain-card") -> dict[str, Any]:
    public = b64encode(key.public_key().public_bytes_raw())
    return {"schema": "P5R0AuthorityV2", "authority_id": authority_id, "key_id": key_id, "public_key": public, "public_key_digest": digest(public)}


def _card(card_id: str, token: str, family: str, modality: str, signer: Ed25519PrivateKey, authority_id: str, key_id: str) -> dict[str, Any]:
    semantics = {"modality": modality, "observation": {"schema": "opaque-observation-v2", "bounded_fields": ["x", "y", "signal"] if modality == "grid_discrete" else ["position", "velocity", "contact"]}, "state": {"schema": "evaluator-state-v2", "hidden": True}, "action": {"schema": "opaque-action-v2", "legal_action_count": 4 if modality == "grid_discrete" else 3}, "effects": {"composition": "bounded-canonical-effect", "distinct": True}, "latent": {"memory": "factor-bound", "causal": "factor-bound"}, "reward": {"success": "private-oracle", "safety": "strict"}, "tools": {"tokens": "opaque", "arguments": "bounded"}, "transition": {"oracle": "P5R0MechanicsSpecV2"}, "reset": {"policy": "arm-bound-exact-snapshot"}, "safety": {"policy": "deny-out-of-envelope"}}
    card = {"schema": "P5R0DomainCardV2", "card_id": card_id, "card_digest": "", "domain_token": token, "private_domain_family": family, "modality": modality, "observation_schema_digest": digest(semantics["observation"]), "state_schema_digest": digest(semantics["state"]), "action_schema_digest": digest(semantics["action"]), "effect_algebra_digest": digest(semantics["effects"]), "latent_mechanics_digest": digest(semantics["latent"]), "reward_constraint_digest": digest(semantics["reward"]), "tool_vocabulary_digest": digest(semantics["tools"]), "transition_oracle_digest": digest(semantics["transition"]), "reset_policy_digest": digest(semantics["reset"]), "safety_policy_digest": digest(semantics["safety"]), "resource_envelope": {"max_steps": 8, "frame_bytes": 65536, "wall_seconds": 3, "memory_mb": 512, "cpu": 1, "pids": 32}, "generator_digest": digest({"generator": "P5R0PrivateCSPRNGGeneratorV2", "card": card_id}), "closure_digest": digest({"closure": "local-crun-podman", "card": card_id}), "case_commitments": {split: digest({"card": card_id, "split": split, "seed": "p5-r0-v2"}) for split in ("train", "development", "held_out")}, "signature": "", "authority_id": authority_id, "key_id": key_id, "authority_public_key": b64encode(signer.public_key().public_bytes_raw())}
    card["card_digest"] = digest({k: v for k, v in card.items() if k not in {"card_digest", "signature"}})
    card["signature"] = sign(card, signer, "card_digest")
    return card


def validate_domain_card(card: dict[str, Any], public_key: Ed25519PublicKey | dict[str, Any] | None = None, *, trusted_authority: dict[str, Any] | None = None, expected_lock_digest: str | None = None) -> dict[str, Any]:
    if not isinstance(card, dict) or set(card) != _CARD_FIELDS or card.get("schema") not in {"P5R0DomainCardV1", "P5R0DomainCardV2"}: raise P5R0Error("domain card schema")
    if card["card_id"] not in {"card-01", "card-02"} or card["domain_token"] not in DOMAINS or card["modality"] not in AXES["modality"]: raise P5R0Error("domain card identity")
    for key in ("card_digest", "generator_digest", "closure_digest", *[f for f in _CARD_FIELDS if f.endswith("_digest") and f != "card_digest"]):
        if not is_digest(card[key]): raise P5R0Error(f"domain card {key}")
    if card["card_digest"] != digest({k: v for k, v in card.items() if k not in {"card_digest", "signature"}}): raise P5R0Error("domain card digest")
    if trusted_authority is not None:
        if trusted_authority.get("authority_id") != card["authority_id"] or trusted_authority.get("key_id") != card["key_id"] or trusted_authority.get("public_key_digest") != digest(trusted_authority.get("public_key")): raise P5R0Error("domain card authority")
        if card["authority_public_key"] != trusted_authority["public_key"]: raise P5R0Error("domain card trusted key")
        public_key = Ed25519PublicKey.from_public_bytes(b64decode(trusted_authority["public_key"]))
    elif isinstance(public_key, dict):
        public_key = Ed25519PublicKey.from_public_bytes(b64decode(public_key["public_key"]))
    elif public_key is None:
        public_key = Ed25519PublicKey.from_public_bytes(b64decode(card["authority_public_key"]))
    try: verify_signature(card, public_key, "card_digest")
    except Exception as exc: raise P5R0Error("domain card signature") from exc
    return card


def create_domain_cards(signer: Ed25519PrivateKey | None = None, *, authority_id: str = "p5-r0-evaluator", key_id: str = "p5-r0-domain-card") -> list[dict[str, Any]]:
    signer = signer or Ed25519PrivateKey.generate()
    cards = [_card("card-01", DOMAINS[0], "arc_like_grid_transformation_navigation", "grid_discrete", signer, authority_id, key_id), _card("card-02", DOMAINS[1], "embodied_sensorimotor_control", "embodied_sensorimotor", signer, authority_id, key_id)]
    return [validate_domain_card(card) for card in cards]


def public_card(card: dict[str, Any]) -> dict[str, Any]:
    validate_domain_card(card)
    return {"schema": "P5R0PublicDomainCardV2", "card_id": card["card_id"], "domain_token": card["domain_token"], "modality": card["modality"], "card_digest": card["card_digest"], "resource_envelope": card["resource_envelope"], "authority_id": card["authority_id"], "key_id": card["key_id"]}
