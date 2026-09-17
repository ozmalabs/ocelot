from __future__ import annotations

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from evaluation.p0a.canonical import canonical_bytes
from evaluation.p2.study import STUDY_SIZE, materialize_held_out_study, score_held_out


def _proposal(envelope):
    predictions = []
    for binding in envelope["training_bundle"]["action_bindings"]:
        advance = binding["effect"] == "advance"
        predictions.append({"action_id": binding["action_id"],
                            "outcome_basis_points": {"o0": 9000 if advance else 0, "o1": 1000 if advance else 10000}})
    advances = [item["action_id"] for item, binding in zip(predictions, envelope["training_bundle"]["action_bindings"], strict=True) if binding["effect"] == "advance"]
    return {"schema": "P2NativePlanProposalV1", "predictions": predictions,
            "selection": {"selected_action_id": sorted(advances)[0] if advances else None}}


def test_held_out_generator_is_finite_deterministic_and_signed():
    key = Ed25519PrivateKey.from_private_bytes(b"\x17" * 32)
    first = materialize_held_out_study(secret_seed=b"\x42" * 32, signing_key=key, run_id="local")
    second = materialize_held_out_study(secret_seed=b"\x42" * 32, signing_key=key, run_id="local")
    manifest, envelopes, truth = first
    assert manifest["episode_count"] == STUDY_SIZE == len(envelopes) == len(truth)
    assert canonical_bytes(manifest) == canonical_bytes(second[0])
    assert all("secret_seed" not in envelope and "hidden_state" not in envelope for envelope in envelopes)
    assert len({entry["episode_id"] for entry in manifest["entries"]}) == STUDY_SIZE
    by_stratum = {entry["stratum"]: envelopes[entry["ordinal"]]["training_bundle"]["action_bindings"] for entry in manifest["entries"] if entry["family"] == "compose-advance-hold" and entry["bijection"] == 0 and entry["action_order"] == 0}
    assert len({canonical_bytes(value) for value in by_stratum.values()}) == 8


def test_independent_held_out_scoring_requires_all_receipts_and_episodes():
    key = Ed25519PrivateKey.from_private_bytes(b"\x19" * 32)
    manifest, envelopes, truth = materialize_held_out_study(secret_seed=b"\x23" * 32, signing_key=key, run_id="local")
    proposals = {envelope["episode_id"]: _proposal(envelope) for envelope in envelopes}
    receipts = {episode_id: "sha256:" + f"{number:064x}" for number, episode_id in enumerate(truth, start=1)}
    evidence = score_held_out(manifest=manifest, truth=truth, proposals=proposals, receipt_hashes=receipts, signer=key)
    assert evidence["episode_count"] == STUDY_SIZE
    assert evidence["metrics"]["validity"]["count"] == STUDY_SIZE
    assert evidence["signature"]
