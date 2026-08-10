#!/usr/bin/env python3
"""Measure graph-directed event settlement on committed real-Doom photons.

This is a measure adapter, not cognition.  It feeds a committed luma stream to
GraphEye, mechanically projects the resulting salience field into the existing
attention/focus seeds, and copies their command into a second identical eye.
The two eyes then settle the same event history: whole sheet versus the
graph-commanded rectangle.  Labels/depth are never loaded.
"""
from __future__ import annotations

import argparse
import json
import os
import time

import numpy as np
import substrate_rs as srs

from domains import doom_photon_world as dpw
from domains import reflective_faculty as rf
from domains.photon_eye import GraphEye
from substrate.boot_core import boot_core
from substrate.seed_loader import manifest_for


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIXTURE_DIR = os.path.join(ROOT, "tests", "fixtures", "doom_carve_scale")


def _eye(n_az, n_el, *, focused):
    return GraphEye(
        n_az=n_az,
        n_el=n_el,
        adapt_rate=0.4,
        context={
            "retina_2d": True,
            "synchronous": True,
            "retina_accel": True,
            "event_native": True,
            "visual_motion": True,
            "visual_salience": True,
            "held_prediction": "decay",
            "retinal_focus": bool(focused),
            "onset_threshold_db": 6.0,
            "onset_refractory_epochs": 0.0,
            "carve_min_coherence": 0.5,
            "carve_min_events": 2.5,
        },
    ).build()


def _feed(eye, lumas, seed=202000):
    rng = np.random.default_rng(seed)
    for _ in range(6):
        eye.submit_photons_2d(dpw.photon_packets(lumas[0], rng))
        eye.substrate._inner.run_rules()
    for node in list(eye.substrate.nodes("RetinalOnsetEvent")):
        eye.substrate.remove_node(node)
    since = eye._epoch + 1
    for luma in lumas[1:]:
        eye.submit_photons_2d(dpw.photon_packets(luma, rng))
        eye.substrate._inner.run_rules()
    return since


def _attention_command(saliences, held_residuals, eye):
    substrate, agent = boot_core(seeds=())
    native = rf._native_eval2(substrate)
    for seed in (
        "fovea_salience_bridge",
        "retinal_attention_graph",
        "held_prediction_attention",
        "retinal_focus_control",
    ):
        native.load_seed_manifest(manifest_for(seed), agent)
    native.set_attr(agent, "vision_settled_epoch", eye._epoch)
    native.set_attr(agent, "my_angle", 0.0)
    for salience in saliences:
        attrs = dict(salience)
        attrs.update({
            "n_az": eye.n_az,
            "n_el": eye.n_el,
            "gaze_az": eye._column_az(int(attrs["column_index"])),
            "gaze_el": eye._row_el(int(attrs["row_index"])),
            "sensor_epoch": eye._epoch,
        })
        node = substrate.add_node("RetinalSalience", attrs)
        substrate.add_edge(agent, "perceives_salience", node)
    for residual in held_residuals:
        attrs = dict(residual)
        col = int(attrs["column_index"])
        row = int(attrs["row_index"])
        attrs.update({
            "n_az": eye.n_az,
            "n_el": eye.n_el,
            "gaze_az": eye._column_az(col),
            "gaze_el": eye._row_el(row),
            "sensor_epoch": eye._epoch,
            "residual_unit": "photon_count_quanta",
        })
        node = substrate.add_node("HeldPredictionResidual", attrs)
        substrate.add_edge(agent, "perceives_prediction_residual", node)
    native.run_rules()
    attrs = substrate.node(agent)["attrs"]
    return {
        "active": attrs.get("retinal_focus_active", 0.0),
        "center_col": attrs.get("retinal_focus_column", -1),
        "center_row": attrs.get("retinal_focus_row", -1),
        "half_width": attrs.get("retinal_focus_half_width", 2),
        "half_height": attrs.get("retinal_focus_half_height", 2),
        "source_epoch": attrs.get("retinal_focus_source_epoch", -1),
        "refused": attrs.get("attention_refused", 1.0),
    }


def _settle(eye, since):
    t0 = time.perf_counter()
    tasks = [
        eye.settle_carve_2d(since_epoch=since),
        eye.settle_motion_2d(since_epoch=since),
        eye.settle_salience_2d(since_epoch=since),
    ]
    t1 = time.perf_counter()
    eye.substrate._inner.run_cognitive_tasks(1)
    eye.substrate._inner.run_rules()
    t2 = time.perf_counter()
    task_attrs = [
        eye.substrate.node(srs.NodeID(task))["attrs"] for task in tasks
    ]
    return {
        "marshal_ms": (t1 - t0) * 1000.0,
        "execute_ms": (t2 - t1) * 1000.0,
        "total_ms": (t2 - t0) * 1000.0,
        "settlement_columns": (
            len(eye.substrate.neighbours(eye._retina, "settles_column"))
            if eye._focus_window is not None
            else eye.n_az * eye.n_el
        ),
        "event_counts": [
            int(a.get("focus_event_count", a["payload"][4] if i != 1 else a["payload"][0]))
            for i, a in enumerate(task_attrs)
        ],
        "total_event_counts": [
            int(a.get("focus_total_event_count", -1)) for a in task_attrs
        ],
        "polygons": len(eye.carve_polygons_2d()),
        "motion": len(eye.motion_percepts_2d()),
        "salience": len(eye.salience_percepts_2d()),
    }


def measure(n_az, n_el):
    path = os.path.join(FIXTURE_DIR, f"frames_{n_az}x{n_el}.npz")
    lumas = np.load(path)["lumas"]

    scout = _eye(n_az, n_el, focused=False)
    since = _feed(scout, lumas)
    scout.settle_salience_2d(since_epoch=since)
    scout.substrate._inner.run_cognitive_tasks(1)
    scout.substrate._inner.run_rules()
    command = _attention_command(
        scout.salience_percepts_2d(),
        scout.held_prediction_residuals_2d(),
        scout,
    )
    scout.stop()

    whole = _eye(n_az, n_el, focused=False)
    focused = _eye(n_az, n_el, focused=True)
    since_whole = _feed(whole, lumas)
    since_focused = _feed(focused, lumas)
    focused.update_focus_window_2d(**{
        key: command[key] for key in (
            "active", "center_col", "center_row", "half_width",
            "half_height", "source_epoch")
    })
    whole_result = _settle(whole, since_whole)
    focused_result = _settle(focused, since_focused)
    whole.stop()
    focused.stop()
    return {
        "grid": [n_az, n_el],
        "command": command,
        "whole": whole_result,
        "focused": focused_result,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--width", type=int, default=80)
    parser.add_argument("--height", type=int, default=60)
    args = parser.parse_args()
    print(json.dumps(measure(args.width, args.height), indent=2))


if __name__ == "__main__":
    main()
