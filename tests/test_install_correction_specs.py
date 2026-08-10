"""Tests for ActionSpec migration of corrections."""
from __future__ import annotations

import pytest
from substrate_rs import _native

from domains.correction_raise_plasticity import (
    PLASTICITY_OVERRIDE_INITIAL,
    get_plasticity_override,
)
from domains.install_correction_specs import (
    install_action_spec,
    install_correction_specs,
    install_prune_actionspec,
    install_raise_plasticity_actionspec,
    list_action_specs,
    run_action_specs_for_events,
)


_NODE_TYPES = ("Microtheory", "Concept", "ActionSpec",
               "FrozenShouldAdaptEvent", "SparseMtEvent")
_EDGE_TYPES = ("has_concept", "causal_influence")


def _fresh_substrate():
    s = _native.Substrate()
    for src_t in _NODE_TYPES:
        for tgt_t in _NODE_TYPES:
            for et in _EDGE_TYPES:
                s.add_production({
                    "src": {"type": src_t, "var": "src"},
                    "edge_type": et,
                    "tgt": {"type": tgt_t, "var": "tgt"},
                    "where": None,
                    "weight": {"type": "Lit", "value": 1.0},
                    "provenance": "test:open",
                })
    return s


# --- Installation creates the right specs --------------------------------

def test_install_correction_specs_creates_action_specs():
    s = _fresh_substrate()
    install_correction_specs(s)
    specs = list_action_specs(s)
    assert len(specs) == 2
    names = {s["name"] for s in specs}
    assert names == {"raise_plasticity_for_frozen", "prune_for_sparse"}


def test_installed_specs_have_correct_triggers():
    s = _fresh_substrate()
    install_correction_specs(s)
    specs = {s["name"]: s for s in list_action_specs(s)}
    assert specs["raise_plasticity_for_frozen"]["trigger_event_type"] \
        == "FrozenShouldAdaptEvent"
    assert specs["prune_for_sparse"]["trigger_event_type"] \
        == "SparseMtEvent"


# --- Action dispatch executes correctly ---------------------------------

def test_raise_plasticity_spec_writes_plasticity_override():
    s = _fresh_substrate()
    mt = s.add_node("Microtheory", {})
    install_raise_plasticity_actionspec(s)
    events = [{
        "event_type": "FrozenShouldAdaptEvent",
        "mt": mt,
        "mt_id": mt.value,
    }]
    actions = run_action_specs_for_events(s, events)
    assert len(actions) == 1
    assert get_plasticity_override(s, mt) == \
        pytest.approx(PLASTICITY_OVERRIDE_INITIAL)


def test_prune_spec_writes_low_beta():
    s = _fresh_substrate()
    mt = s.add_node("Microtheory", {"temperature": 2.0})
    install_prune_actionspec(s)
    events = [{
        "event_type": "SparseMtEvent",
        "mt": mt,
        "mt_id": mt.value,
    }]
    actions = run_action_specs_for_events(s, events)
    assert len(actions) == 1
    assert s.node(mt)["attrs"]["temperature"] == pytest.approx(0.05)


def test_action_spec_only_fires_for_matching_event_type():
    """raise_plasticity ActionSpec shouldn't fire for SparseMtEvent."""
    s = _fresh_substrate()
    mt = s.add_node("Microtheory", {})
    install_raise_plasticity_actionspec(s)
    events = [{
        "event_type": "SparseMtEvent",  # wrong type
        "mt": mt,
        "mt_id": mt.value,
    }]
    actions = run_action_specs_for_events(s, events)
    assert actions == []
    # plasticity_override should NOT be set
    assert get_plasticity_override(s, mt) == 0.0


def test_no_events_no_actions():
    s = _fresh_substrate()
    mt = s.add_node("Microtheory", {})
    install_correction_specs(s)
    actions = run_action_specs_for_events(s, [])
    assert actions == []
