"""Re-wire test for shape_generation_programs — the GENERATE/RECOVER Term builders.

shape_generation_programs builds the reified GENERATE and RECOVER Programs as
graph-resident Term-trees (a shape = the fed-forward iterate of the held
difference operator). At runtime the agent reaches them via reflective_faculty
(_run_generate / _run_recover) reading the PERSISTED Term-trees in
seeds/programs.json — so the Python BUILDER read as an orphan (its output lives in
the seed). This restores it by (a) pinning the builder as the source of truth for
the persisted Programs, and (b) running the builder's own Term-trees through the
proven runner to exercise the generate->recover cycle.

  · builder == seed: generate_program()/recover_program() reproduce exactly the
    Term-trees persisted in seeds/programs.json (so the seed can be regenerated and
    cannot silently drift from its source).
  · capability: the GENERATE Program makes a CIRCLE from a constant residual (it
    closes) and a LINE from the identity residual (it does not); the RECOVER Program
    differences the circle's trail back into a ~constant turning residual.
"""
import json
import math
import os

import pytest
from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds
from domains.shape_generation_programs import generate_program, recover_program
from domains.reflective_faculty import run_program_on_fresh

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _persisted(name):
    d = json.load(open(os.path.join(ROOT, "seeds", "programs.json")))
    for n in d["nodes"]:
        if n.get("type") == "Program" and n["attrs"].get("name") == name:
            return json.loads(n["attrs"]["program"])
    raise AssertionError(f"Program {name!r} not in seeds/programs.json")


def test_builder_matches_persisted_generate():
    assert generate_program() == _persisted("generate_shape"), \
        "generate_program() must reproduce the persisted generate_shape Term-tree (source of truth)"


def test_builder_matches_persisted_recover():
    assert recover_program() == _persisted("recover_shape_law"), \
        "recover_program() must reproduce the persisted recover_shape_law Term-tree (source of truth)"


def _generate(turn0_deg, dturn_deg, steps):
    env = {"turn0": math.radians(turn0_deg), "dturn": math.radians(dturn_deg),
           "steps": list(range(steps))}
    out = run_program_on_fresh(generate_program(), env)
    assert out.get("ran"), f"generate did not run: {out}"
    state = out["value"]
    return [[float(p[0]), float(p[1])] for p in state[5]]      # the trail (slot 5)


def test_generate_circle_closes():
    trail = _generate(30.0, 0.0, 12)                            # constant 30° residual, 12 steps -> closes
    assert len(trail) == 12
    assert math.hypot(trail[-1][0], trail[-1][1]) < 1e-6, "a constant residual must close into a circle"


def test_generate_line_does_not_close():
    trail = _generate(0.0, 0.0, 6)                              # identity residual -> straight line
    assert math.hypot(trail[-1][0], trail[-1][1]) > 1.0, "the identity residual must run straight (not close)"


def test_recover_circle_residual_is_constant():
    trail = _generate(30.0, 0.0, 12)
    out = run_program_on_fresh(recover_program(),
                               {"trail": trail, "idx": list(range(2, len(trail)))})
    assert out.get("ran"), f"recover did not run: {out}"
    turns = [float(t) for t in out["value"]]
    assert turns, "recover produced no residual"
    target = math.radians(30.0)
    assert max(abs(t - target) for t in turns) < 1e-6, \
        "RECOVER must difference the circle's trail back into a ~constant turning residual"
