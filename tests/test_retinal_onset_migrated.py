"""ASYNC VISUAL ONSET EVENTS — the gate (`VISION_RETINAL_ONSET_PREREG.md`).

The visual one-to-one analog of the cochlear-nucleus onset stage
(`runners/dsl/src/cochlear_nucleus.rs::detect_onsets`): a discrete
`RetinalOnsetEvent` is MINTED for a column when its rod receptor's transduced
drive (`caught`) departs its OWN adapting floor (`adaptation`) by a dB threshold,
refractory-gated. The DECISION primitive is Rust (the `photon_transduce_onset`
task kind appends output[3] = 20·log10((caught+eps)/(adaptation+eps))); the
graph rule `retinal_mint_onset` thresholds it and mints the events. Python here
only drives the world clock and reads counts back.

What this guards:
  1. THE PRIMITIVE, called directly (CognitiveTask round-trip): the onset kernel
     is a byte-identical peer of `photon_transduce` in its first three outputs
     (so the shared apply rule folds it unchanged) and appends the dB departure,
     which is large off a fresh floor and ~0 off an adapted one.
  2. COMPUTE-∝-SURPRISE (the headline, able-to-fail): a moving bar fires events
     that LOCALISE to where change happens; a held bright scene falls SILENT
     once the floor adapts; and — the load-bearing control — with adaptation
     turned OFF the SAME held scene stays NOISY (so the silence is the floor's
     doing, not an artefact).
  3. THE PRE-REGISTERED INTERVAL R = moving/(static_adapted+1) ∈ [6, 40].
  4. DEFAULT OFF: with the flag off, no onset events, plain `photon_transduce`
     kind, no params node — the retina is byte-unchanged (the oracle proves the
     rest).
  5. §10 PROVENANCE: the engine is a build of this tree's Rust.
"""
from __future__ import annotations

import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

pytest.importorskip("substrate_rs")
np = pytest.importorskip("numpy")

import substrate_rs as srs  # noqa: E402
from domains.photon_eye import GraphEye  # noqa: E402
from domains.engine_provenance import engine_provenance  # noqa: E402

SEED = 135000
BRIGHT = 2000
WARMUP = 8  # dark frames so each column's floor adapts before measurement


# --- 1. the Rust DECISION primitive, called directly ----------------------

def _run_kernel(s, kind, payload):
    t = s.add_node("CognitiveTask", {
        "status": "requested", "kind": kind, "payload": [float(v) for v in payload],
        "input_epoch": 1, "logical_time": 0, "area": "global"})
    s._inner.run_cognitive_tasks(1)
    return list(s.node(t)["attrs"]["output"])


def test_onset_kernel_peers_transduce_and_appends_db():
    s = srs.Substrate()
    # center, bandwidth, adaptation(floor), adapt_rate, half, dark, wl, count
    fresh = [498.0, 42.0, 0.0, 0.12, 1024.0, 0.15, 500.0, float(BRIGHT)]
    base = _run_kernel(s, "photon_transduce", fresh)
    onset = _run_kernel(s, "photon_transduce_onset", fresh)
    assert len(base) == 3, "photon_transduce is byte-unchanged (3 outputs)"
    assert len(onset) == 4, "onset kernel appends the dB departure"
    assert onset[:3] == base, "the first three outputs must be byte-identical"
    assert onset[3] > 6.0, f"a bright step off a zero floor is an onset (db={onset[3]})"

    # An adapted floor (adaptation == drive) → ~0 dB → silence.
    adapted = [498.0, 42.0, float(BRIGHT), 0.12, 1024.0, 0.0, 498.0, float(BRIGHT)]
    o2 = _run_kernel(s, "photon_transduce_onset", adapted)
    assert abs(o2[3]) < 1.0, f"an adapted floor silences the onset (db={o2[3]})"


# --- the synchronous world harness ----------------------------------------

def _eye(adapt_rate=0.12, n_az=16, onset=True, threshold_db=6.0, refractory=0.0):
    ctx = {"synchronous": True, "worker_capacity": 1}
    if onset:
        ctx.update(visual_onset=True, onset_threshold_db=threshold_db,
                   onset_refractory_epochs=refractory)
    return GraphEye(n_az=n_az, adapt_rate=adapt_rate, context=ctx).build()


def _frame(eye, packets):
    eye.submit_photons(packets)
    eye.substrate._inner.run_cognitive_tasks(1)
    eye.substrate._inner.run_rules()


def _events(eye):
    """(epoch, column_index) for every RetinalOnsetEvent held."""
    out = []
    for n in eye.substrate.nodes("RetinalOnsetEvent"):
        a = eye.substrate.node(n)["attrs"]
        out.append((int(a["epoch"]), int(a["column_index"])))
    return out


def _bright(cols, rng):
    return [{"column": int(c), "wavelength_nm": 500.0, "count": int(rng.poisson(BRIGHT))}
            for c in cols]


# --- 2/3. the compute-∝-surprise gate + the pre-registered interval -------

def test_moving_fires_static_silent_off_noisy():
    n_az = 16
    rng = np.random.default_rng(SEED)

    # MOVING: warm up on dark, then sweep a single bright column across.
    eye = _eye(adapt_rate=0.12, n_az=n_az)
    for _ in range(WARMUP):
        _frame(eye, [])                       # dark
    sweep_lo = eye._epoch + 1                  # first sweep epoch
    bright_at = {}
    for t in range(n_az):
        _frame(eye, _bright([t], rng))
        bright_at[eye._epoch] = t
    moving = [(ep, ci) for (ep, ci) in _events(eye) if ep >= sweep_lo]
    moving_count = len(moving)
    # LOCALISATION: every event sits on the column that was bright at its epoch.
    for ep, ci in moving:
        assert ci == bright_at[ep], (
            f"onset at epoch {ep} localised to column {ci}, bar was at "
            f"{bright_at[ep]}")
    eye.stop()

    # STATIC, adaptation ON: hold the whole retina bright; measure the LAST 8.
    eye = _eye(adapt_rate=0.12, n_az=n_az)
    for _ in range(WARMUP):
        _frame(eye, [])
    for _ in range(8):                         # adaptation window (uncounted)
        _frame(eye, _bright(range(n_az), rng))
    measure_lo = eye._epoch + 1
    for _ in range(8):                         # measured window
        _frame(eye, _bright(range(n_az), rng))
    static_adapted_count = sum(1 for (ep, _c) in _events(eye) if ep >= measure_lo)
    eye.stop()

    # OFF CONTROL: identical scene, adaptation frozen (adapt_rate = 0).
    eye = _eye(adapt_rate=0.0, n_az=n_az)
    for _ in range(WARMUP):
        _frame(eye, [])
    for _ in range(8):
        _frame(eye, _bright(range(n_az), rng))
    off_lo = eye._epoch + 1
    for _ in range(8):
        _frame(eye, _bright(range(n_az), rng))
    off_count = sum(1 for (ep, _c) in _events(eye) if ep >= off_lo)
    eye.stop()

    print(f"\nRETINAL ONSET: moving={moving_count} static_adapted="
          f"{static_adapted_count} off={off_count}")

    # (1) MOVING fires and localises.
    assert moving_count >= 12, (
        f"the sweeping bar should fire ~{n_az} onsets, got {moving_count}")
    # (2) STATIC-adapted falls silent.
    assert static_adapted_count <= 2, (
        f"a held, adapted scene must go silent, got {static_adapted_count}")
    # (3) ADAPTATION-OFF stays noisy — the silence in (2) IS the floor's doing.
    assert off_count >= n_az, (
        f"with adaptation OFF the SAME held scene must stay noisy, got "
        f"{off_count}; if it also went silent the gate is meaningless")
    assert off_count > 5 * (static_adapted_count + 1), (
        "OFF must be dramatically noisier than the adapted case")

    # (4) THE PRE-REGISTERED HEADLINE: R = moving/(static_adapted+1) ∈ [6, 40].
    R = moving_count / (static_adapted_count + 1)
    assert 6.0 <= R <= 40.0, f"contrast R={R} outside pre-registered [6, 40]"


# --- 4. default OFF / byte-identity ----------------------------------------

def test_onset_path_is_off_by_default():
    eye = _eye(onset=False, n_az=8)
    assert eye._onset_kind == "photon_transduce", "flag off ⇒ plain kind"
    assert eye.substrate.nodes("RetinaOnsetParams") == [], "no params node when off"
    rng = np.random.default_rng(SEED)
    for c in range(8):
        _frame(eye, _bright([c], rng))
    assert eye.substrate.nodes("RetinalOnsetEvent") == [], (
        "no onset events may be minted with the onset path off")
    eye.stop()


# --- 5. provenance ---------------------------------------------------------

def test_engine_is_a_build_of_this_tree():
    p = engine_provenance()
    assert p["source_match"] in ("own", "shared"), (
        f"engine source verdict {p['source_match']!r} — see "
        "test_engine_provenance_migrated.py")
