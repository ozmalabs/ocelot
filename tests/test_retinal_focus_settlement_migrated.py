"""Graph-directed retinal event focus and its default-off oracle."""
from __future__ import annotations

import json

import pytest
import substrate_rs as srs

pytest.importorskip("substrate_rs")

from domains.photon_eye import GraphEye
from domains import reflective_faculty as rf
from substrate.boot_core import boot_core
from substrate.seed_loader import manifest_for


def _load_attention_focus(epoch=7):
    substrate, agent = boot_core(seeds=())
    native = rf._native_eval2(substrate)
    for seed in (
        "fovea_salience_bridge",
        "retinal_attention_graph",
        "held_prediction_attention",
        "retinal_focus_control",
    ):
        native.load_seed_manifest(manifest_for(seed), agent)
    native.set_attr(agent, "vision_settled_epoch", epoch)
    native.set_attr(agent, "my_angle", 0.0)
    return substrate, agent, native


def _salience(substrate, agent, *, epoch, col, row, residual):
    node = substrate.add_node(
        "RetinalSalience",
        {
            "column_index": col,
            "row_index": row,
            "n_az": 8,
            "n_el": 6,
            "gaze_az": 0.0,
            "gaze_el": 0.0,
            "sensor_epoch": epoch,
            "raw_salience": residual,
            "residual_salience": residual,
        },
    )
    substrate.add_edge(agent, "perceives_salience", node)
    return node


def test_focus_command_is_the_graph_attention_verdict_and_refuses_ties():
    substrate, agent, native = _load_attention_focus(epoch=7)
    _salience(substrate, agent, epoch=7, col=2, row=4, residual=3.0)
    _salience(substrate, agent, epoch=7, col=6, row=1, residual=9.0)
    native.run_rules()

    attrs = substrate.node(agent)["attrs"]
    assert attrs["attention_column_index"] == 6
    assert attrs["attention_row_index"] == 1
    assert attrs["retinal_focus_active"] == 1.0
    assert attrs["retinal_focus_column"] == 6
    assert attrs["retinal_focus_row"] == 1
    assert attrs["retinal_focus_half_width"] == 4
    assert attrs["retinal_focus_half_height"] == 4
    assert attrs["retinal_focus_source_epoch"] == 7

    # A late exact top tie makes the unchanged attention resolver refuse.  The
    # focus control must publish that refusal instead of retaining the old box.
    _salience(substrate, agent, epoch=7, col=0, row=5, residual=9.0)
    native.run_rules()
    attrs = substrate.node(agent)["attrs"]
    assert attrs["attention_refused"] == 1.0
    assert attrs["retinal_focus_active"] == 0.0
    assert attrs["retinal_focus_column"] == -1
    assert attrs["retinal_focus_row"] == -1


def _eye(*, focused):
    context = {
        "retina_2d": True,
        "synchronous": True,
        "visual_motion": True,
        "visual_salience": True,
        "event_native": True,
    }
    if focused:
        context["retinal_focus"] = True
    return GraphEye(n_az=8, n_el=6, context=context).build()


def _mint_event_sheet(eye, epoch=7):
    for row in range(eye.n_el):
        for col in range(eye.n_az):
            eye.substrate.add_node(
                "RetinalOnsetEvent",
                {
                    "column_index": col,
                    "row_index": row,
                    "epoch": epoch,
                    "magnitude_db": 9.0,
                },
            )
    eye._epoch = epoch


def _payload_count(attrs):
    # carve-2d header: n_az,n_el,max_gap,vel_tol,count,...
    return int(attrs["payload"][4])


def test_rust_event_focus_reads_graph_window_and_filters_all_three_stages():
    eye = _eye(focused=True)
    _mint_event_sheet(eye)
    eye.update_focus_window_2d(
        active=1,
        center_col=3,
        center_row=2,
        half_width=1,
        half_height=1,
        source_epoch=6,
    )

    tasks = [
        eye.settle_carve_2d(since_epoch=1),
        eye.settle_motion_2d(since_epoch=1),
        eye.settle_salience_2d(since_epoch=1),
    ]
    for task in tasks:
        attrs = eye.substrate.node(srs.NodeID(task))["attrs"]
        assert attrs["focus_event_count"] == 9
        assert attrs["focus_total_event_count"] == 48
        assert attrs["focus_source_epoch"] == 6

    carve = eye.substrate.node(srs.NodeID(tasks[0]))["attrs"]
    assert _payload_count(carve) == 9
    # Every serialized event lies inside cols 2..4, rows 1..3.
    events = carve["payload"][5:]
    triples = list(zip(events[0::3], events[1::3], events[2::3]))
    assert len(triples) == 9
    assert all(2 <= col <= 4 and 1 <= row <= 3 for col, row, _ in triples)
    assert len(eye.substrate.neighbours(eye._retina, "settles_column")) == 9

    eye.substrate._inner.run_cognitive_tasks(1)
    eye.substrate._inner.run_rules()
    saliences = eye.salience_percepts_2d()
    assert len(saliences) == 9
    assert all(
        2 <= salience["column_index"] <= 4
        and 1 <= salience["row_index"] <= 3
        for salience in saliences
    )


def test_no_focus_node_and_explicit_refusal_are_exact_whole_sheet_fallbacks():
    default = _eye(focused=False)
    refused = _eye(focused=True)
    _mint_event_sheet(default)
    _mint_event_sheet(refused)
    refused.update_focus_window_2d(
        active=0,
        center_col=3,
        center_row=2,
        half_width=1,
        half_height=1,
        source_epoch=6,
    )

    default_task = default.settle_carve_2d(since_epoch=1)
    refused_task = refused.settle_carve_2d(since_epoch=1)
    default_attrs = default.substrate.node(srs.NodeID(default_task))["attrs"]
    refused_attrs = refused.substrate.node(srs.NodeID(refused_task))["attrs"]

    assert _payload_count(default_attrs) == 48
    assert _payload_count(refused_attrs) == 48
    assert default_attrs["payload"] == refused_attrs["payload"]
    assert "focus_event_count" not in default_attrs
    assert "focus_event_count" not in refused_attrs
    assert len(
        refused.substrate.neighbours(refused._retina, "settles_column")
    ) == 48


def test_focus_faculty_is_generic_and_default_off_at_eye_boundary():
    manifest = manifest_for("retinal_focus_control")
    text = json.dumps(manifest).lower()
    assert manifest["depends_on"] == ["held_prediction_attention"]
    assert "doom" not in text
    assert "depth" not in text and "label" not in text
    assert '"argmin"' not in text and '"argmax"' not in text

    eye = _eye(focused=False)
    assert eye._focus_window is None
    assert not list(eye.substrate.nodes("RetinalFocusWindow"))
