"""The native rule store exposes bounded readback for live rule families."""

from substrate.boot_all import load_all_seeds
from substrate.world_adapter import WorldAdapter


def test_native_rule_prefix_readback_is_live_and_selective():
    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)
    selected = list(agent.inner.export_rules_prefix("sak_kind_"))

    assert selected
    assert all(str(rule.get("name", "")).startswith("sak_kind_")
               for rule in selected)
    assert all(rule.get("active") for rule in selected)
    assert any(rule.get("name") == "sak_kind_question" for rule in selected)
