"""Gate: the default dual-process cycle settles UNLABELLED (legacy) rules.

Regression for docs/research/engine_substrate/dual-process-starves-unlabelled-rules.md.
`CyclePlan::Default` selects `DualProcess` whenever an enabled
`DualProcessPolicy` exists (every default `boot_core()`). Rules with neither
`latency_class` nor `area` used to match neither System 1 (hard_realtime) nor
any admitted System-2 area and never ran under `tick()`. The engine now
settles them with StructRulesOnly semantics in the leftover budget, while
labelled soft rules stay System-2 gated.

This file only builds frames and reads attrs; every decision is a seed rule.
"""
from __future__ import annotations

import pytest

from domains.engine_provenance import engine_preamble
engine_preamble()

import domains.seed_registry  # noqa: E402,F401
from substrate.boot_core import boot_core, load_seeds_into  # noqa: E402
from domains import lighting_world as lw  # noqa: E402

REFL = [{"name": "a", "rL": 10, "rM": 20, "rS": 30},
        {"name": "b", "rL": 40, "rM": 15, "rS": 25},
        {"name": "c", "rL": 12, "rM": 44, "rS": 8}]


def _scene(seeds):
    s, ag = boot_core() if seeds is None else boot_core(seeds=seeds)
    load_seeds_into(s, ag, ["vision_lighting"])
    ref = lw.add_frame(s, reflectances=[dict(r) for r in REFL], gain=(1, 1, 1),
                       is_reference=True, start_sidx=0)
    test = lw.add_frame(s, reflectances=[dict(r) for r in REFL], gain=(3, 2, 4),
                        start_sidx=1000)
    lw.link_reference(s, test, ref)
    lw.set_flag(s, lighting=1.0)
    return s


def _soft_probe(s):
    probe = s.add_node("UnlabelledGateProbe", {"ran": 0})
    root = s.add_node("UnlabelledGateRoot", {})
    try:
        s._inner.add_edge_unchecked(root, "has_unlabelled_gate_probe", probe, {})
    except TypeError:
        s._inner.add_edge_unchecked(root, "has_unlabelled_gate_probe", probe)
    s._inner.add_rule({
        "name": "test_unlabelled_gate_soft_probe",
        "area": "planning", "order": 0, "latency_class": "soft_realtime",
        "match": [["root", "has_unlabelled_gate_probe", "probe"]],
        "where": {"type": "Eq",
                  "a": {"type": "Attr", "node": {"type": "Var", "name": "probe"},
                        "key": "ran"},
                  "b": {"type": "Lit", "value": 0}},
        "effects": [["set_attr", "probe", "ran", 1]],
    })
    return probe


@pytest.mark.parametrize("seeds", [("dual_process_core",), None],
                         ids=["dual_process_core_only", "default_core"])
def test_tick_fires_unlabelled_lighting_rules_under_dual_process(seeds):
    s = _scene(seeds)
    steps = s.tick(200_000)
    assert steps > 0
    assert lw.n_illuminants(s) == 1


def test_tick_matches_run_rules_and_policy_free_boot_on_minimal_repro():
    """The unlabelled sheet reaches the same Illuminant count via tick under
    the policy, via run_rules, and via a policy-free boot."""
    a = _scene(("dual_process_core",)); a.tick(200_000)
    b = _scene(("dual_process_core",)); b._inner.run_rules(200_000)
    c = _scene(()); c.tick(200_000)
    assert lw.n_illuminants(a) == lw.n_illuminants(b) == lw.n_illuminants(c) == 1


def test_labelled_soft_rule_stays_system_two_gated_alongside_legacy_settle():
    s = _scene(("dual_process_core",))
    probe = _soft_probe(s)
    s.tick(200_000)
    assert lw.n_illuminants(s) == 1
    assert s.node(probe)["attrs"]["ran"] == 0


def test_trace_names_the_legacy_phase_after_system_one():
    s = _scene(("dual_process_core",))
    report = s._inner.run_cycle("default", trace=True)
    phases = [row[1] for row in report["trace"]]
    assert phases[0] == "system_one_settle"
    assert phases[-1] == "legacy_unlabelled_settle"
