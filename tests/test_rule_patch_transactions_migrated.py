"""Native self-modification transaction surface.

The Python calls here are mechanical conformance probes over the Rust
implementation. Patch selection and adoption remain graph-native.
"""

import pytest

import substrate_rs as srs


def _rule(name: str) -> dict:
    return {
        "name": name,
        "match": [],
        "where": {"type": "Lit", "value": True},
        "effects": [],
    }


def _native_substrate():
    # These APIs intentionally live on the native extension surface alongside
    # the existing add_rule/export_rules checkpoint mechanics.
    return srs._native.Substrate()


def test_uid_revision_hash_cas_and_inverse_round_trip():
    substrate = _native_substrate()
    idx = substrate.add_rule(_rule("patch_me"))
    before = substrate.rule_metadata(idx)

    assert before["rule_uid"] > 0
    assert before["revision"] == 0
    assert before["content_hash"] > 0

    changed = substrate.apply_rule_patch(
        before["rule_uid"],
        before["revision"],
        before["content_hash"],
        "where",
        {"type": "Lit", "value": False},
    )
    assert changed["revision"] == 1
    assert changed["content_hash"] != before["content_hash"]

    with pytest.raises(ValueError, match="stale_revision"):
        substrate.apply_rule_patch(
            before["rule_uid"],
            before["revision"],
            before["content_hash"],
            "where",
            {"type": "Lit", "value": True},
        )

    reverted = substrate.apply_rule_patch(
        before["rule_uid"],
        changed["revision"],
        changed["content_hash"],
        "where",
        changed["inverse_clause"],
    )
    assert reverted["revision"] == 2
    assert reverted["content_hash"] == before["content_hash"]


def test_checkpoint_preserves_stable_rule_identity_metadata():
    original = _native_substrate()
    original.add_rule(_rule("duplicate_name"))
    original.add_rule(_rule("duplicate_name"))
    exported = original.export_rules()

    assert exported[0]["rule_uid"] != exported[1]["rule_uid"]
    assert all(rule["content_hash"] > 0 for rule in exported)

    restored = _native_substrate()
    restored.import_rules(exported)
    assert restored.export_rules() == exported


def test_apply_rule_patch_effect_round_trips_in_rule_codec():
    substrate = _native_substrate()
    substrate.add_rule(
        {
            "name": "graph_patch_dispatch",
            "match": [["agent", "has_patch", "patch"]],
            "where": None,
            "effects": [["apply_rule_patch", "patch"]],
        }
    )
    assert substrate.export_rules()[0]["effects"] == [
        ["apply_rule_patch", "patch"]
    ]


def test_seed_installed_rules_are_protected_but_live_authored_rules_are_patchable():
    substrate = _native_substrate()
    substrate.load_seed_manifest(
        {
            "id": "protected_prior_probe",
            "nodes": [],
            "edges": [],
            "productions": [],
            "rules": [_rule("seed_prior")],
        }
    )
    seed_meta = substrate.rule_metadata(0)
    assert seed_meta["mutation_protected"] is True
    with pytest.raises(ValueError, match="protected_target"):
        substrate.apply_rule_patch(
            seed_meta["rule_uid"],
            seed_meta["revision"],
            seed_meta["content_hash"],
            "where",
            {"type": "Lit", "value": False},
        )
    restored = _native_substrate()
    restored.import_rules(substrate.export_rules())
    assert restored.rule_metadata(0)["mutation_protected"] is True

    live_idx = substrate.add_rule(_rule("authored_live"))
    live_meta = substrate.rule_metadata(live_idx)
    assert live_meta["mutation_protected"] is False
    substrate.apply_rule_patch(
        live_meta["rule_uid"],
        live_meta["revision"],
        live_meta["content_hash"],
        "where",
        {"type": "Lit", "value": False},
    )
