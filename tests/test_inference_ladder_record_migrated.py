"""P3.D1.1 winner attribution for the existing inference rungs."""
from __future__ import annotations

import importlib.util
import json
import random
from pathlib import Path

import pytest

pytest.importorskip("substrate_rs")

from substrate.boot_core import boot_core
from substrate.seed_loader import manifest_for
from domains import reflective_faculty as rf
from tests.test_geninfer_grain_migrated import BLOCK, DT3, JIT, _rot
from tests.test_gen_infer_migrated import BASE, SHEAR_A, _lin

ROOT = Path(__file__).resolve().parents[1]


def _run(signature, *, dim_grains=None, gen=False, dt=None, base=BLOCK):
    s, agent = boot_core()
    native = rf._native_eval2(s)
    rf._ensure_shape_decode_loop(s, native, agent)
    native.load_seed_manifest(manifest_for("inference_ladder_record"), agent)
    if dim_grains is not None:
        s.set_attr(agent, "dim_grains", dim_grains)
    if gen:
        s.set_attr(agent, "gen_infer_enabled", 1.0)
    s.add_node("ShapeSignature", {"name": "held", "signature": json.dumps(base),
        "kind": "faculty", "faculty": "held", "dim_types": dt or DT3})
    s.set_attr(agent, "codebook_epoch", 0.0)
    obs = s.add_node("Observation", {"signature": signature, "key": ["ilr"],
        "status": "decoded", "residual": signature, "decoded_epoch": 0.0,
        "dim_types": dt or DT3})
    s.add_edge(agent, "observed", obs)
    native.run_rules()
    return s.node(obs)["attrs"]


def test_four_fixtures_report_dim_dim_grain_gen_linear_and_quantum():
    rotation = _rot(BLOCK)
    jittered = _rot(JIT)
    random.seed(811)
    coords = random.sample([(r, c) for r in range(8) for c in range(8)], len(JIT))
    scrambled = [["cell", r, c] for r, c in coords]
    dt4 = ["pred", "coord:r", "coord:c", "val"]
    base4 = [["cell", 0, 0, "red"], ["cell", 1, 0, "red"],
             ["cell", 2, 0, "red"], ["cell", 2, 1, "red"]]
    assert _run(rotation)["ladder_winner"] == "dim"
    assert _run(jittered, dim_grains=[0, 1])["ladder_winner"] == "dim_grain"
    assert _run(_lin(SHEAR_A, base4), gen=True, dt=dt4, base=base4)["ladder_winner"] == "gen_linear"
    assert _run(scrambled)["ladder_winner"] == "quantum"


def test_generator_reproduces_committed_seed_exactly():
    spec = importlib.util.spec_from_file_location("gen_inference_ladder_record_seed", ROOT / "scripts" / "gen_inference_ladder_record_seed.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    assert (ROOT / "seeds" / "inference_ladder_record.json").read_text() == json.dumps(module.build(), indent=1) + "\n"
