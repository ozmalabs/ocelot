"""ASYNC MOTION FROM THE EVENT STREAM — the gate (`VISION_ASYNC_MOTION_PREREG.md`).

Rung 2 of the photon-eye migration. Motion (direction + speed) is recovered from
the ASYNCHRONOUS onset-event stream (`RetinalOnsetEvent` nodes minted by Rung 1),
NOT from a two-frame `vector_field` / `retinal_flow_depth` difference and NOT from
the coarse `retinal_field` raster.

A moving edge fires onset events in ADJACENT columns at SUCCESSIVE per-receptor
epochs; each event carries its OWN epoch. The velocity is the least-squares SLOPE
of column position on per-event epoch — the space-time STRUCTURE of the event
cloud, settled from the accumulated events available this tick (leaving a
residual), never a snapshot difference. The DECISION primitive is Rust
(`retinal_event_motion`); the graph rule `retinal_mint_motion` mints the percept;
Python only packs the event stream into the task payload and reads the percept
back.

What this guards:
  1. THE PRIMITIVE, called directly (CognitiveTask round-trip): a positive
     space-time diagonal recovers +1 / |slope|, a negative diagonal −1, and a
     SCRAMBLED-epoch set of the SAME columns decorrelates to coherence≈0.
  2. MOVING → correct motion off the EVENT STREAM (end-to-end through the eye):
     L→R gives direction +1, R→L gives −1, speed tracks the true sweep step.
  3. THE PRE-REGISTERED HEADLINE: ρ = Pearson(recovered speed, true speed) over a
     speed sweep ∈ [0.90, 1.00].
  4. STATIC → no motion: a dark scene mints no events → no `RetinalMotionPercept`.
  5. SCRAMBLED → no coherent motion through the REAL mint rule (coherence below
     `min_coherence` → the rule declines to mint).
  6. DEFAULT OFF: flag off ⇒ no motion params, no motion percept, plain kind.
  7. MERGE-BLOCK SOURCE AUDIT: the adapter's motion path reads ONLY the event
     stream (`RetinalOnsetEvent` attrs), never the raster / a frame diff.
  8. §10 PROVENANCE: the engine is a build of this tree's Rust.
"""
from __future__ import annotations

import inspect
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

pytest.importorskip("substrate_rs")
np = pytest.importorskip("numpy")

import substrate_rs as srs  # noqa: E402
from domains.photon_eye import GraphEye, _add_edge  # noqa: E402
from domains.engine_provenance import engine_provenance  # noqa: E402

SEED = 136000
BRIGHT = 2000
WARMUP = 8  # dark frames so each column's floor adapts before the sweep
MIN_COHERENCE = 0.5  # the adapter's default RetinaMotionParams.min_coherence


# --- 1. the Rust DECISION primitive, called directly ----------------------

def _run_kernel(s, payload):
    t = s.add_node("CognitiveTask", {
        "status": "requested", "kind": "retinal_event_motion",
        "payload": [float(v) for v in payload],
        "input_epoch": 1, "logical_time": 0, "area": "global"})
    s._inner.run_cognitive_tasks(1)
    return list(s.node(t)["attrs"]["output"])


def _pack(pairs):
    """Serialise (column, epoch) pairs into the kernel payload."""
    payload = [float(len(pairs))]
    for c, e in pairs:
        payload.extend([float(c), float(e)])
    return payload


def test_kernel_recovers_direction_speed_and_decorrelates_when_scrambled():
    s = srs.Substrate()
    # A clean L→R diagonal: column advances with epoch, slope +2.
    lr = [(2 * k, k) for k in range(6)]
    out = _run_kernel(s, _pack(lr))
    direction, speed, residual, coherence, n = out
    assert direction == 1.0, f"L→R must be positive, got {direction}"
    assert abs(speed - 2.0) < 1e-9, f"slope must equal the step (2), got {speed}"
    assert abs(coherence - 1.0) < 1e-9, f"a clean diagonal is coherent, got {coherence}"
    assert residual < 1e-9 and n == 6.0

    # R→L: same magnitude, opposite sign.
    rl = [(20 - 2 * k, k) for k in range(6)]
    d2, s2, _r2, c2, _n2 = _run_kernel(s, _pack(rl))
    assert d2 == -1.0 and abs(s2 - 2.0) < 1e-9 and abs(c2 - 1.0) < 1e-9

    # SCRAMBLED CONTROL: the SAME column multiset, epochs shuffled — the
    # space-time structure is destroyed. Read the MEASURED coherence.
    rng = np.random.default_rng(SEED)
    cols = [c for c, _e in lr]
    epochs = [e for _c, e in lr]
    rng.shuffle(epochs)
    scrambled = list(zip(cols, epochs))
    _d3, _s3, _r3, c3, _n3 = _run_kernel(s, _pack(scrambled))
    print(f"\nMOTION KERNEL: coherence clean={coherence:.3f} scrambled={c3:.3f}")
    assert c3 < coherence, "scrambling must reduce coherence below the clean fit"
    assert c3 < MIN_COHERENCE, (
        f"scrambled coherence {c3:.3f} must fall below the mint threshold "
        f"{MIN_COHERENCE} — it is the space-time STRUCTURE that carries motion")


# --- the synchronous world harness ----------------------------------------

def _eye(n_az=32, adapt_rate=0.12, motion=True):
    ctx = {"synchronous": True, "worker_capacity": 1}
    if motion:
        ctx["visual_motion"] = True
    return GraphEye(n_az=n_az, adapt_rate=adapt_rate, context=ctx).build()


def _frame(eye, packets):
    eye.submit_photons(packets)
    eye.substrate._inner.run_cognitive_tasks(1)
    eye.substrate._inner.run_rules()


def _bright(cols, rng):
    return [{"column": int(c), "wavelength_nm": 500.0,
             "count": int(rng.poisson(BRIGHT))} for c in cols]


def _sweep(eye, columns, rng):
    """Present a single bright column per frame along `columns` (in order)."""
    for c in columns:
        _frame(eye, _bright([c], rng))


def _settle_and_mint(eye, since_epoch):
    """Drive the motion op: settle the event stream, run the kernel + rule.

    `since_epoch` is the observation window (excludes the cold-start warm-up
    events — the floor-priming phase carries no scene motion; Rung 1's onset
    gate filters the same warm-up epochs test-side).
    """
    eye.settle_motion(since_epoch=since_epoch)
    eye.substrate._inner.run_cognitive_tasks(1)
    eye.substrate._inner.run_rules()
    return eye.motion_percepts()


# --- 2/3. moving recovers motion; the pre-registered speed-tracking headline

def test_moving_recovers_direction_and_speed_static_is_silent():
    rng = np.random.default_rng(SEED)
    n_az = 32

    # L→R sweep at step 1.
    eye = _eye(n_az=n_az)
    for _ in range(WARMUP):
        _frame(eye, [])                      # dark warm-up
    lo = eye._epoch + 1
    _sweep(eye, list(range(0, n_az, 1)), rng)
    lr = _settle_and_mint(eye, since_epoch=lo)
    assert len(lr) == 1, f"one settled motion percept expected, got {len(lr)}"
    assert lr[0]["direction"] == 1.0, f"L→R direction must be +1, got {lr[0]}"
    assert lr[0]["coherence"] > MIN_COHERENCE
    eye.stop()

    # R→L sweep at step 1.
    eye = _eye(n_az=n_az)
    for _ in range(WARMUP):
        _frame(eye, [])
    lo = eye._epoch + 1
    _sweep(eye, list(range(n_az - 1, -1, -1)), rng)
    rl = _settle_and_mint(eye, since_epoch=lo)
    assert len(rl) == 1 and rl[0]["direction"] == -1.0, (
        f"R→L direction must be −1, got {rl}")
    eye.stop()

    # STATIC (dark): no events in the window ⇒ no motion percept.
    eye = _eye(n_az=n_az)
    for _ in range(WARMUP):
        _frame(eye, [])
    lo = eye._epoch + 1
    for _ in range(8):
        _frame(eye, [])
    static = _settle_and_mint(eye, since_epoch=lo)
    print(f"\nMOTION EYE: L→R dir={lr[0]['direction']} R→L dir={rl[0]['direction']} "
          f"static_percepts={len(static)}")
    assert static == [], f"a dark scene must mint no motion, got {static}"
    eye.stop()


def test_recovered_speed_tracks_true_speed_headline():
    """PRE-REGISTERED: ρ = Pearson(recovered, true) speed ∈ [0.90, 1.00]."""
    rng = np.random.default_rng(SEED)
    n_az = 32
    true_speeds = [1, 2, 3, 4]
    recovered = []
    for step in true_speeds:
        eye = _eye(n_az=n_az)
        for _ in range(WARMUP):
            _frame(eye, [])
        lo = eye._epoch + 1
        _sweep(eye, list(range(0, n_az, step)), rng)   # slope == step
        percepts = _settle_and_mint(eye, since_epoch=lo)
        assert len(percepts) == 1, f"step {step}: expected one percept"
        assert percepts[0]["direction"] == 1.0
        recovered.append(percepts[0]["speed"])
        eye.stop()

    rho = float(np.corrcoef(true_speeds, recovered)[0, 1])
    print(f"\nMOTION SPEED TRACKING: true={true_speeds} recovered={recovered} "
          f"rho={rho:.4f}")
    assert 0.90 <= rho <= 1.00, (
        f"speed-tracking ρ={rho:.4f} outside pre-registered [0.90, 1.00]")


# --- 5. scrambled control through the REAL mint rule ----------------------

def test_scrambled_event_times_mint_no_coherent_motion():
    """The mint RULE (not just the kernel) declines a scrambled event set."""
    rng = np.random.default_rng(SEED + 1)
    n_az = 32
    eye = _eye(n_az=n_az)
    for _ in range(WARMUP):
        _frame(eye, [])
    lo = eye._epoch + 1
    _sweep(eye, list(range(0, n_az, 1)), rng)

    # Read the SWEEP event stream, SHUFFLE the epochs, and inject that scrambled
    # payload as a motion task on the retina (same path settle_motion uses).
    events = []
    for node in eye.substrate.nodes("RetinalOnsetEvent"):
        a = eye.substrate.node(node)["attrs"]
        if float(a["epoch"]) >= lo:
            events.append((float(a["column_index"]), float(a["epoch"])))
    assert len(events) >= 3
    cols = [c for c, _e in events]
    epochs = [e for _c, e in events]
    rng.shuffle(epochs)
    payload = _pack(list(zip(cols, epochs)))

    task = eye.substrate.add_node("CognitiveTask", {
        "status": "requested", "kind": "retinal_event_motion",
        "payload": payload, "input_epoch": eye._epoch, "logical_time": 999,
        "area": "retina", "order": 2, "salience": 1.0})
    _add_edge(eye.substrate._inner, eye._retina, "has_motion_task", task)
    eye.substrate._inner.run_cognitive_tasks(1)
    coherence = float(eye.substrate.node(task)["attrs"]["output"][3])
    eye.substrate._inner.run_rules()

    minted_from_scrambled = [
        p for p in eye.motion_percepts()
        if abs(p["coherence"] - coherence) < 1e-9]
    print(f"\nMOTION SCRAMBLED (rule): coherence={coherence:.3f} "
          f"minted={len(minted_from_scrambled)}")
    assert coherence < MIN_COHERENCE, (
        f"scrambled coherence {coherence:.3f} must be below {MIN_COHERENCE}")
    assert minted_from_scrambled == [], (
        "the mint rule must decline a scrambled (incoherent) event set")
    eye.stop()


# --- 6. default OFF / byte-identity ---------------------------------------

def test_motion_path_is_off_by_default():
    eye = _eye(n_az=8, motion=False)
    assert eye._motion_enabled is False
    assert eye._onset_kind == "photon_transduce", "flag off ⇒ plain kind"
    assert eye.substrate.nodes("RetinaMotionParams") == [], "no params node when off"
    assert eye.settle_motion() is None, "settle_motion is a no-op when off"
    rng = np.random.default_rng(SEED)
    for c in range(8):
        _frame(eye, _bright([c], rng))
    assert eye.substrate.nodes("RetinalMotionPercept") == [], (
        "no motion percept may be minted with the motion path off")
    eye.stop()


# --- 7. merge-block source audit: motion reads ONLY the event stream ------

def test_motion_is_derived_from_the_event_stream_not_a_raster_or_frame_diff():
    src = inspect.getsource(GraphEye.settle_motion)
    assert "RetinalOnsetEvent" in src, "motion must read the onset EVENT STREAM"
    assert "column_index" in src and "epoch" in src, (
        "motion reads each event's column + own epoch")
    for forbidden in ("retinal_field", "vector_field", "retinal_flow_depth",
                      "_previous_field", "PhotonExposure"):
        assert forbidden not in src, (
            f"MERGE-BLOCK: settle_motion must not touch {forbidden!r} — motion "
            "is off the async event stream, never a raster / frame diff")


# --- 8. provenance ---------------------------------------------------------

def test_engine_is_a_build_of_this_tree():
    p = engine_provenance()
    assert p["source_match"] in ("own", "shared"), (
        f"engine source verdict {p['source_match']!r} — see "
        "test_engine_provenance_migrated.py")
