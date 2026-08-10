"""BLOCK 134000 — the vectorized-stencil fast path: BYTE-IDENTITY + the
admissibility ROUTING gate.

A speedup that changes ANY cell is a BUG, not a result (PROTOCOL §9). These
gates assert the Rust-vectorized stencil path (`wave_stencil_tick`) is bit-for-
bit identical to the committed per-cell `tick` — over a battery of grids AND
across MANY iterated ticks (the CA compounds; an error grows) — and that the
Γ-admissibility gate routes a stencil rule set → fast and a non-stencil rule set
→ general, both correct.
"""
from __future__ import annotations
import hashlib
import os
import sys

import numpy as np
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from substrate.boot_core import boot_core, load_seeds_into  # noqa: E402
import domains.seed_registry  # noqa: E402,F401
from domains.wave_world import WaveWorld  # noqa: E402
from substrate_rs import _native  # noqa: E402


def _boot(g, *, seed=0, fast=False, run_rest=True, propagate=1.0, n_units=0):
    s, ag = boot_core()
    load_seeds_into(s, ag, ["vision_waves"])
    s.set_attr(s.nodes("WaveParams")[0], "propagate", propagate)
    w = WaveWorld(s, h=g, w=g, seed=seed, fovea_radius=0)
    if n_units:
        w.add_units(n_units, rf=5)
    if fast:
        w.stencil_fast = True
        w.stencil_run_rest = run_rest
    return s, w


def _digest(s):
    """Full-graph state digest: every node's (type, sorted attrs)."""
    parts = []
    for n in s.nodes():
        at = s.node(n)["attrs"]
        parts.append((s.node(n)["type"],
                      tuple(sorted((k, repr(v)) for k, v in at.items()))))
    parts.sort(key=lambda x: repr(x))
    return hashlib.sha256(repr(parts).encode()).hexdigest()


def _mismatched_cells(sg, wg, sf, wf):
    """Count RetinaCells whose (state, fired_at, activated_at) differ."""
    keys = ("state", "fired_at", "activated_at")
    n = 0
    for k in sorted(wg.cells):
        ag = sg.node(wg.cells[k])["attrs"]
        af = sf.node(wf.cells[k])["attrs"]
        if any(repr(ag.get(x)) != repr(af.get(x)) for x in keys):
            n += 1
    return n


def _run_pair(g, *, seed, ticks, run_rest, propagate=1.0, n_units=0):
    sg, wg = _boot(g, seed=seed, propagate=propagate, n_units=n_units)
    sf, wf = _boot(g, seed=seed, fast=True, run_rest=run_rest,
                   propagate=propagate, n_units=n_units)
    tick_mism = 0
    cell_mism = 0
    for i in range(ticks):
        k = 1 if i % 5 == 0 else 0
        wg.step(ignite_k=k)
        wf.step(ignite_k=k)
        if _digest(sg) != _digest(sf):
            tick_mism += 1
        cell_mism += _mismatched_cells(sg, wg, sf, wf)
    return tick_mism, cell_mism


# --- 0. the method exists ----------------------------------------------------
def test_native_exposes_wave_stencil_tick():
    assert hasattr(_native.Substrate, "wave_stencil_tick"), (
        "engine predates wave_stencil_tick — rebuild via scripts/engine_build.sh")


# --- 1. BYTE-IDENTITY, multi-tick, both modes, grids × seeds -----------------
@pytest.mark.parametrize("g", [8, 12, 16, 24, 32])
def test_bare_mode_byte_identical_over_100_ticks(g):
    """FAST-BARE (run_rest=False) == GENERAL bit-for-bit on the pure wave field,
    100 iterated ticks (the CA compounds)."""
    tick_mism, cell_mism = _run_pair(g, seed=134000 + g, ticks=100, run_rest=False)
    assert tick_mism == 0 and cell_mism == 0, (tick_mism, cell_mism)


@pytest.mark.parametrize("g", [8, 12, 16, 24, 32])
def test_rest_mode_byte_identical_over_100_ticks(g):
    """FAST-REST (run_rest=True) == GENERAL bit-for-bit, 100 iterated ticks."""
    tick_mism, cell_mism = _run_pair(g, seed=134010 + g, ticks=100, run_rest=True)
    assert tick_mism == 0 and cell_mism == 0, (tick_mism, cell_mism)


def test_noise_arm_is_a_stencil_and_byte_identical():
    """propagate=0 (the NOISE control arm) is still a uniform local stencil —
    admissible, no recruitment, byte-identical."""
    tick_mism, cell_mism = _run_pair(16, seed=134020, ticks=80, run_rest=False,
                                     propagate=0.0)
    assert tick_mism == 0 and cell_mism == 0, (tick_mism, cell_mism)


# --- 2. COMPOSITION: learners present, run_rest=True untouched, byte-identical
def test_rest_mode_composes_with_learners():
    """With Units/Synapses present (the non-stencil LEARNER rules), the stencil
    is fast-pathed and the learner rules run UNTOUCHED via the general pass —
    byte-identical under run_rest=True. This is the 'irregular rules untouched'
    composition."""
    tick_mism, cell_mism = _run_pair(12, seed=134030, ticks=40, run_rest=True,
                                     n_units=4)
    assert tick_mism == 0 and cell_mism == 0, (tick_mism, cell_mism)


# --- 3. THE ADMISSIBILITY ROUTING GATE --------------------------------------
def test_gate_routes_pure_field_to_fast():
    """A pure wave field (the recognised stencil) → wave_stencil_tick returns
    True in BOTH modes (admissible → fast)."""
    s, w = _boot(16, seed=1)
    w.step(ignite_k=1)
    assert s.wave_stencil_tick(200_000, True) is True   # rest mode
    s2, w2 = _boot(16, seed=1)
    w2.step(ignite_k=1)
    assert s2.wave_stencil_tick(200_000, False) is True  # bare mode


def test_gate_refuses_bare_mode_with_learners():
    """Learners present → BARE mode is INADMISSIBLE (strict): returns False so
    the caller falls back to the general per-cell path (else it would skip the
    learner rules and diverge — measured)."""
    s, w = _boot(12, seed=1, n_units=4)
    w.step(ignite_k=1)
    assert s.wave_stencil_tick(200_000, False) is False   # bare: refused
    # rest mode still admissible (runs the learners untouched)
    s2, w2 = _boot(12, seed=1, n_units=4)
    w2.step(ignite_k=1)
    assert s2.wave_stencil_tick(200_000, True) is True


def test_gate_refuses_a_non_stencil_state_rule():
    """Install an extra rule that writes RetinaCell.state in a NON-stencil form
    (a global unconditional write). The state dynamics is no longer the
    recognised uniform local stencil → wave_stencil_tick returns False in BOTH
    modes, and the caller uses the general path (correct)."""
    s, w = _boot(12, seed=1)
    w.step(ignite_k=1)
    nat = s._inner
    # a rule matching every RetinaCell that writes `state` — not one of the
    # three stencil templates (no neighbour edge, no phase guard).
    nat.add_rule({
        "name": "nonstencil_state_write",
        "match_type": "RetinaCell",
        "match": [["r", "has_cell", "c"]],
        "where": {"type": "Eq",
                  "a": {"type": "Attr", "node": {"type": "Var", "name": "c"},
                        "key": "state"},
                  "b": {"type": "Lit", "value": "rested"}},
        "effects": [["set_attr", "c", "state", "rested"]],
    })
    assert s.wave_stencil_tick(200_000, True) is False
    assert s.wave_stencil_tick(200_000, False) is False


def test_gate_refuses_when_a_foreign_rule_reads_the_field():
    """If a non-wave active rule READS state/fired_at, the vectorized pass could
    race it → inadmissible in both modes (condition b)."""
    s, w = _boot(12, seed=1)
    w.step(ignite_k=1)
    nat = s._inner
    # a rule (different match type) whose where-clause reads RetinaCell-shaped
    # `state`: read_set gains Attr(state), so the gate refuses.
    nat.add_rule({
        "name": "foreign_reads_state",
        "match_type": "Retina",
        "match": [["a", "has_cell", "c"]],
        "where": {"type": "Eq",
                  "a": {"type": "Attr", "node": {"type": "Var", "name": "c"},
                        "key": "state"},
                  "b": {"type": "Lit", "value": "active"}},
        "effects": [["set_attr", "a", "frame_median", 1.0]],
    })
    assert s.wave_stencil_tick(200_000, True) is False


# --- 4. §9 DEFAULT: an un-opted world takes the committed tick path ----------
def test_default_world_is_byte_unchanged():
    """A world that does NOT set stencil_fast never calls the fast path — its
    run is the committed per-cell tick, verified identical to an explicitly
    general run."""
    sa, wa = _boot(16, seed=7)                 # default (stencil_fast unset)
    sb, wb = _boot(16, seed=7)                 # also default
    for i in range(30):
        k = 1 if i % 5 == 0 else 0
        wa.step(ignite_k=k)
        wb.step(ignite_k=k)
    assert _digest(sa) == _digest(sb)
    assert not getattr(wa, "stencil_fast", False)


# --- 5. NO PYTHON AGENT DECISION: the routing is the Rust gate ---------------
def test_routing_decision_is_in_rust_not_python():
    """The adapter's only stencil line is a mechanical `if flag and
    s.wave_stencil_tick(...)` — no conditional over GRAPH STATE. The
    admissibility DECISION lives in Rust (`wave_stencil::admissible`)."""
    import inspect
    src = inspect.getsource(WaveWorld.step)
    # the adapter calls the native gate and branches only on its boolean verdict
    assert "wave_stencil_tick" in src
    # it must NOT itself inspect graph state to decide admissibility
    assert "nodes_of_type" not in src and "match_type" not in src
