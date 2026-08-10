"""Falsifiable temporal and integration gates for graph-native PSI affect."""
import json
import os

import scripts.modulator_emergence_measure as M
from substrate.seed_loader import manifest_for

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_drive_decay_occurs_exactly_once_per_epoch():
    eye, inner = M._eye()
    _hub, ms = M._hub_ms(eye, inner)
    d = M._drive(
        eye, inner, ms, v_d=0, v_0=0, c_d=1024, c_d_prev=1024,
        half_life=1, last_tend=0, now_epoch=1,
    )
    inner.run_rules()
    first = int(eye.substrate.node(d)["attrs"]["c_d"])
    latched = int(eye.substrate.node(d)["attrs"]["last_tend"])
    inner.run_rules()
    second = int(eye.substrate.node(d)["attrs"]["c_d"])
    eye.stop()
    assert (first, second, latched) == (512, 512, 1)


def test_competence_accumulates_in_graph_once_per_epoch():
    result = M.competence_accumulator()
    assert result["trace"] == [20, 40, 60, 80, 100]
    assert result["rises_monotonically"]


def test_emotion_readout_resets_by_graph_epoch_without_host_clears():
    eye, inner = M._eye()
    _hub, ms = M._hub_ms(eye, inner)
    d = M._drive(
        eye, inner, ms, appraised=1, explore=1, learning_progress=20,
        v_d=1000, c_d=600, c_d_prev=100, v_0=0,
    )
    inner.run_rules()
    assert int(eye.substrate.node(ms)["attrs"]["hit_curiosity"]) == 1

    # Change only appraisal inputs. The graph epoch rule owns all hit/read-off
    # clearing; this test deliberately never writes any such cell.
    for key, value in {
        "appraised": 1, "explore": 0, "learning_progress": 0,
        "value_progress": 0, "v_d": 0, "c_d": 0, "c_d_prev": 0,
    }.items():
        eye.substrate.set_attr(d, key, float(value))
    inner.run_rules()  # converge the new appraisal while prior read-off is held
    eye.substrate.set_attr(ms, "epoch", 1.0)
    inner.run_rules()  # emx_epoch_reset + classification of the stable state
    attrs = eye.substrate.node(ms)["attrs"]
    eye.stop()
    assert all(int(attrs["hit_" + name]) == 0 for name in M.ALL_NAMES)
    assert int(attrs["emotion"]) == 0
    assert int(attrs["action_tendency"]) == 0
    assert int(attrs["emotion_epoch"]) == 1


def _load_affect(eye, inner):
    inner.load_seed_manifest(manifest_for("affective_state_core"), eye._agent)
    return next(iter(inner.neighbours(eye._agent, "has_affective_state")))


def test_weighted_urgency_leader_persists_until_switch_margin_is_crossed():
    eye, inner = M._eye()
    _load_affect(eye, inner)
    _hub, ms = M._hub_ms(eye, inner, drive_switch_threshold=100)
    incumbent = M._drive(
        eye, inner, ms, leading=True, weight=1, v_d=1000, v_0=0,
        c_d=500, c_d_prev=500,
    )
    challenger = M._drive(
        eye, inner, ms, leading=False, weight=1, v_d=1000, v_0=0,
        c_d=450, c_d_prev=450,
    )
    inner.run_rules()
    assert list(inner.neighbours(ms, "leading_drive")) == [incumbent]

    eye.substrate.set_attr(challenger, "c_d", 300.0)
    eye.substrate.set_attr(challenger, "c_d_prev", 300.0)
    inner.run_rules()
    leaders = list(inner.neighbours(ms, "leading_drive"))
    eye.stop()
    assert leaders == [challenger]


def test_weighted_urgency_selects_initial_leading_drive_in_graph():
    eye, inner = M._eye()
    _load_affect(eye, inner)
    _hub, ms = M._hub_ms(eye, inner, drive_switch_threshold=100)
    M._drive(
        eye, inner, ms, leading=False, weight=1, v_d=1000, v_0=0,
        c_d=600, c_d_prev=600,
    )
    winner = M._drive(
        eye, inner, ms, leading=False, weight=2, v_d=1000, v_0=0,
        c_d=600, c_d_prev=600,
    )
    inner.run_rules()
    leaders = list(inner.neighbours(ms, "leading_drive"))
    eye.stop()
    assert leaders == [winner]


def test_psi_projects_complete_canonical_affective_state():
    eye, inner = M._eye()
    affect = _load_affect(eye, inner)
    hub, ms = M._hub_ms(eye, inner)
    inner.add_edge_unchecked(hub, "has_affective_state", affect)
    inner.add_edge_unchecked(ms, "projects_affect_to", affect)
    M._drive(
        eye, inner, ms, appraised=1, explore=1, learning_progress=20,
        v_d=1000, c_d=600, c_d_prev=100, v_0=0,
    )
    inner.run_rules()
    source = eye.substrate.node(ms)["attrs"]
    projected = eye.substrate.node(affect)["attrs"]
    eye.stop()
    assert projected["baseline"] == 0.0
    assert projected["valence"] == source["valence"]
    assert projected["arousal"] == source["arousal"]
    assert projected["resolution"] == source["resolution"]
    assert projected["selection_threshold"] == source["sel_threshold"]
    assert projected["securing"] == source["securing"]
    assert projected["competence"] == source["competence"]
    assert projected["epoch"] == source["epoch"]


def test_affective_state_contract_and_adapter_have_no_host_readout_clear():
    seed = json.load(open(os.path.join(ROOT, "seeds", "affective_state_core.json")))
    productions = {
        (p["src"]["type"], p["edge_type"], p["tgt"]["type"])
        for p in seed["productions"]
    }
    assert ("Agent", "has_affective_state", "AffectiveState") in productions
    assert ("EmotionHub", "has_affective_state", "AffectiveState") in productions
    assert ("ModulatorState", "projects_affect_to", "AffectiveState") in productions
    assert ("DualProcessContext", "uses_affective_state", "AffectiveState") in productions

    adapter = open(
        os.path.join(ROOT, "domains", "doom_emotion_narration_ingest.py")
    ).read()
    assert "for k in _READOFF" not in adapter
    assert 'set_attr(ms, "competence_base"' not in adapter
