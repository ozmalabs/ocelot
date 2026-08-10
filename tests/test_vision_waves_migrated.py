"""RUNG 1 — SELF-GENERATED SPONTANEOUS ACTIVITY (retinal waves) + the measured
burst-based Hebbian rule.

These gates exist because the developmental research (105-agent verified pass,
see VISION_DEVELOPMENT_ARC.md) showed the previous L0 experiment was the WRONG
EXPERIMENT: orientation selectivity is not created by learning on natural images
(ferret maps emerge P31-36 with NO correlation to eye opening; dark-reared
ferrets have maps; cat orientation emerges BEFORE eye opening), and before eye
opening V1's training data is WAVE statistics. Tabula rasa is not
blank + external data — it is blank + SELF-GENERATED structured activity.

THE PARADIGM-FORCING CLAIM these gates protect:

    the adapter supplies UNSTRUCTURED entropy; the GRAPH makes the STRUCTURE.

`test_the_graph_makes_structure_from_unstructured_entropy` is the one that
matters: the same RNG feeds both arms, and only the arm where the agent's own
rules run produces spatial correlation. If that ever fails, the rung is a
numpy demo wearing a graph costume.
"""
from __future__ import annotations

import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if p not in sys.path:
        sys.path.insert(0, p)

pytest.importorskip("substrate_rs")
np = pytest.importorskip("numpy")

import domains.seed_registry  # noqa: E402,F401
from substrate.boot_core import boot_core, load_seeds_into  # noqa: E402
from domains.wave_world import WaveWorld, record  # noqa: E402

WAVES_SEED = os.path.join(ROOT, "seeds", "vision_waves.json")


def _boot(propagate=1.0, *, h=16, w=16, seed=1):
    s, ag = boot_core()
    load_seeds_into(s, ag, ["vision_waves"])
    wp = s.nodes("WaveParams")[0]
    s.set_attr(wp, "propagate", float(propagate))
    return s, WaveWorld(s, h=h, w=w, seed=seed)


def _spatial_corr_at_distance(mv, d=1):
    T, H, W = mv.shape
    X = mv.reshape(T, -1)
    X = X - X.mean(0, keepdims=True)
    sd = X.std(0)
    sd[sd == 0] = 1e-9
    Xn = X / sd
    C = (Xn.T @ Xn) / T
    ys, xs = np.mgrid[:H, :W]
    pos = np.stack([ys.ravel(), xs.ravel()], 1)
    D = np.rint(np.hypot(pos[:, None, 0] - pos[None, :, 0],
                         pos[:, None, 1] - pos[None, :, 1])).astype(int)
    m = (D == d)
    return float(C[m].mean()) if m.sum() else 0.0


# --------------------------------------------------------------------------- #
#  1. THE HEADLINE: structure is made by the graph, not handed to it.
# --------------------------------------------------------------------------- #
def test_the_graph_makes_structure_from_unstructured_entropy():
    """THE PARADIGM GATE. Both arms get the SAME unstructured entropy from the
    SAME adapter (uniform random ignition, identical seed). They differ ONLY in
    whether the agent's own propagation rule is allowed to run
    (WaveParams.propagate, graph data — the ablation is DATA, not a code path).

    The wave arm must show local spatial correlation; the noise arm must show
    none. Any structure is therefore manufactured by the rules — this is what
    makes rung 1 a test of the paradigm rather than a demonstration of numpy."""
    _s1, w_wave = _boot(1.0, seed=1)
    mv_wave = record(w_wave, steps=60, ignite_k=1, ignite_every=5)
    _s2, w_noise = _boot(0.0, seed=1)          # SAME seed => same entropy
    mv_noise = record(w_noise, steps=60, ignite_k=1, ignite_every=5)

    c_wave = _spatial_corr_at_distance(mv_wave, 1)
    c_noise = _spatial_corr_at_distance(mv_noise, 1)

    assert mv_wave.mean() > 10 * mv_noise.mean(), (
        "propagation produced no more activity than bare ignition — the "
        f"rules did not fire (wave {mv_wave.mean():.4f} vs noise {mv_noise.mean():.4f})")
    assert c_wave > 0.05, f"wave activity is not spatially correlated ({c_wave:.3f})"
    assert abs(c_noise) < 0.02, (
        f"the NOISE arm is spatially correlated ({c_noise:.3f}) — the entropy "
        "source is not unstructured, so the comparison proves nothing")
    assert c_wave > 5 * abs(c_noise) + 0.02


def test_waves_travel_rather_than_saturate():
    """Refractoriness must make the wave TRAVEL: activity spreads from the
    ignition point over successive steps instead of igniting in place. Without
    travel there is no temporal structure to learn from."""
    _s, w = _boot(1.0, seed=2)
    mv = record(w, steps=12, ignite_k=1, ignite_every=99)   # ONE ignition
    n = mv.sum(axis=(1, 2))
    assert n[0] >= 1
    assert n[4] > n[0], f"activity did not spread from the ignition point: {n[:6]}"
    assert n.max() < mv[0].size, "the grid saturated — refractoriness is not working"


def test_phase_guards_are_disjoint_so_a_cell_is_not_refracted_before_it_fires():
    """REGRESSION on a real bug: the first cut let wv_refract fire on a cell in
    the same tick it ignited, refracting it before it could propagate or be
    observed — the grid stayed empty (measured 0/40 frames active). The fix is
    disjoint clock phases: wv_propagate requires activated_at == step,
    wv_refract requires activated_at < step."""
    import json
    with open(WAVES_SEED) as f:
        seed = json.load(f)
    prop = [r for r in seed["rules"] if r["name"] == "wv_propagate"][0]
    refr = [r for r in seed["rules"] if r["name"] == "wv_refract"][0]
    assert '"Eq"' in json.dumps(prop["where"]) and "activated_at" in json.dumps(prop["where"])
    assert '"Lt"' in json.dumps(refr["where"]) and "activated_at" in json.dumps(refr["where"])
    _s, w = _boot(1.0, seed=3)
    mv = record(w, steps=10, ignite_k=1, ignite_every=3)
    assert (mv.sum(axis=(1, 2)) > 0).sum() >= 8, "cells are being refracted before they fire"


# --------------------------------------------------------------------------- #
#  2. THE MEASURED RULE.
# --------------------------------------------------------------------------- #
def test_burst_rule_uses_the_measured_constants_as_graph_data():
    """The burst rule's constants are the MEASURED ones from Butts, Kanold &
    Shatz 2007 (coincident bursts +21.3 +/- 5.1%, non-overlapping -5.9 +/- 1.4%),
    and they live in graph data, not in a Python literal.

    SCOPE (learned the hard way): this gates the CONSTANTS ONLY. It does NOT
    gate the ~1s WINDOW, and must not be read as doing so — see
    `test_the_latency_axis_is_currently_missing` below. A gate that checks the
    numbers but not the axis they parameterise is not a gate for the
    mechanism."""
    import json
    with open(WAVES_SEED) as f:
        seed = json.load(f)
    wp = [n for n in seed["nodes"] if n["type"] == "WaveParams"][0]["attrs"]
    assert abs(wp["enhance_rate"] - 0.213) < 1e-9
    assert abs(wp["depress_rate"] - 0.059) < 1e-9
    names = {r["name"] for r in seed["rules"]}
    assert {"bh_potentiate", "bh_depress", "wv_propagate",
            "wv_refract", "wv_recover"} <= names


def test_the_latency_axis_exists_and_homeostasis_bounds_it():
    """The latency axis IS now implemented (this test replaces
    `test_the_latency_axis_is_currently_missing`, which was written to fail
    exactly when the axis landed — it did).

    bh_potentiate/bh_depress compare Minus(step, pre.last_burst) against
    WaveParams.window_steps, so the ~1s window is a real axis rather than its
    Dt=0 point; window_steps=0 recovers the old rule exactly, keeping the
    ablation as DATA. bh_sum_weights/bh_scale add Turrigiano multiplicative
    synaptic scaling, forced by a MEASURED runaway (norm 6.9 -> 93.0 in 200
    steps, ~half the RF energy in 3 of 49 synapses).

    WHAT THIS TEST DOES **NOT** CLAIM: that the temporal axis WORKS. The
    temporal-shuffle control is still NULL at every window width tested
    (0/1/2/4: p=0.48/0.63/0.32/0.40, n=40/arm) — an earlier n=60 run gave
    p=0.013 and did NOT replicate. Time still does no measurable work. The
    honest gate for that is the shuffle control itself, not this structural
    check. See VISION_DEVELOPMENT_ARC.md."""
    import json
    with open(WAVES_SEED) as f:
        seed = json.load(f)
    blob = json.dumps([{"where": r.get("where"), "effects": r.get("effects")}
                       for r in seed["rules"]
                       if r["name"] in ("bh_potentiate", "bh_depress")])
    assert "last_burst" in blob and "window_steps" in blob, (
        "the burst rules no longer read a pre-burst latency — the temporal "
        "axis regressed to the Dt=0-only rule")
    names = {r["name"] for r in seed["rules"]}
    assert {"bh_sum_weights", "bh_scale"} <= names, "homeostasis rules missing"
    wp = [n for n in seed["nodes"] if n["type"] == "WaveParams"][0]["attrs"]
    assert "window_steps" in wp and "target_sum" in wp, "knobs are not graph data"


def test_homeostasis_bounds_the_runaway():
    """REGRESSION on a measured pathology: with the latency window and no
    synaptic scaling, +21.3% compounding explodes the weights (norm 6.9 -> 93.0
    over 200 steps). Multiplicative scaling must hold the unit's total near
    target_sum, which is what makes competition zero-sum."""
    s, w = _boot(1.0, seed=7)
    units = w.add_units(4, rf=7)
    for i in range(120):
        w.step(ignite_k=1 if i % 5 == 0 else 0)
    for u in units:
        tot = float(np.abs(w.receptive_field(u)).sum())
        assert tot < 400.0, f"weights ran away despite scaling (total {tot:.1f})"


def test_burst_hebbian_learns_from_self_generated_waves():
    """The winner's receptive field must MOVE under the burst rule, driven only
    by the agent's own waves — no external input at all. Weight structure
    (std) must grow: a unit that never differentiates has not learned."""
    s, w = _boot(1.0, seed=4)
    units = w.add_units(4, rf=7)
    before = {u: w.receptive_field(u).copy() for u in units}
    wins = {u: 0 for u in units}
    for i in range(80):
        w.step(ignite_k=1 if i % 5 == 0 else 0)
        for u in units:
            if float(s.node(u)["attrs"]["bursting"]) == 1.0:
                wins[u] += 1
    winner = max(units, key=lambda u: wins[u])
    assert wins[winner] > 0, "no unit ever burst — winner-take-all never fired"
    a, b = before[winner], w.receptive_field(winner)
    assert np.abs(b - a).mean() > 1e-3, "the winner's RF did not move"
    assert b.std() > a.std(), "no weight structure developed"


def test_winner_take_all_is_a_rule_not_python():
    """Competition (which unit learns) is the graph's decision — an Argmax in
    the rule's where-clause — not a Python max()."""
    import json
    with open(WAVES_SEED) as f:
        seed = json.load(f)
    r = [x for x in seed["rules"] if x["name"] == "wv_unit_burst_winner"][0]
    assert '"Argmax"' in json.dumps(r["where"])
    # The adapter must not pick the winner, rank units, or set `bursting` on a
    # Unit to anything but 0 (it clears; the RULE crowns). Scoped to real
    # decisions over graph state — a bounds clamp like max(1, h-rf+1) is
    # arithmetic, not a decision, and must not trip this.
    src = open(os.path.join(ROOT, "domains", "wave_world.py")).read()
    for banned in ("argmax", "np.argmax", "sorted(", ".sort("):
        assert banned not in src, f"adapter ranks/selects: {banned}"
    for ln in src.splitlines():
        if 'set_attr' in ln and '"bursting"' in ln and 'Unit' in ln:
            assert '0.0' in ln, f"adapter decides a Unit burst: {ln.strip()}"
