"""test_troxler_migrated — the gates for the TROXLER rung.

PROTOCOL §12.3: a provenance claim is pinned to **this rung's own DIFF**, never to
a mutable tree — both of rung 8B's self-restraint gates rotted the same day they
were written, by falsely accusing an innocent rung.

PROTOCOL §12.3 also: **every gate here was POSITIVE-CONTROLLED** — a violation was
injected, the gate went RED, the violation was reverted, the gate went GREEN. A
gate you have only ever seen pass is not a gate you have tested. The injections
are recorded in `VISION_TROXLER_RESULTS.md`.

These run at a SHORT calibration (the mirror and the coincidence are properties of
the wiring, not of the setpoint's convergence), so the file is fast enough to be a
gate rather than an experiment.
"""
import os
import subprocess
import sys

import numpy as np
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "scripts"))

pytest.importorskip("substrate_rs")

import troxler_lib as T  # noqa: E402

CAL = 100     # short: these gates are about the WIRING, not the setpoint
VIS = 40

# THIS RUNG'S OWN COMMITS, identified BY IDENTITY rather than by a base sha.
#
# The first cut of this gate pinned `80e706f5..HEAD`. That was ROT-PRONE and the rot
# was demonstrated within the hour: main advanced by one commit (`f7c1e104`, the scale
# rung) while this rung's runs were in flight, and after the mandatory rebase onto the
# new tip the range `80e706f5..HEAD` SPANNED THAT OTHER RUNG'S COMMIT. It still passed
# — the scale rung added no Rust — but it was by then testing someone else's diff as
# though it were this rung's, which is EXACTLY §12.3's disease: rung 8B's two
# self-restraint gates rotted the same day they were written and rotted by ACCUSING AN
# INNOCENT RUNG. A base sha is not a pin; a rebase moves what sits above it.
#
# The claim is "the TROXLER rung adds no Rust and edits no seed", so the gate resolves
# the Troxler rung's OWN commits by subject and diffs EACH against ITS OWN parent.
# Invariant under rebase, and under any amount of other agents' concurrent work.
RUNG_SUBJECT_PREFIX = "vision TROXLER"


def _run(arm, **kw):
    return T.run_arm(0, arm, vis_steps=VIS, calib_steps=CAL, **kw)


def test_the_mirror_stabilises_EXACTLY_while_the_eye_still_moves():
    """§6 — arm B must be DITCHBURN (image follows a MOVING eye), not PARALYSIS.

    A stabilisation that silently failed would look exactly like 'the drift does
    not matter', which is the result the rung is trying to earn. So the arm
    asserts its own success: lum == W_img at EVERY step, while the gaze MOVES.
    """
    b = _run(T.ARM_STABILISED)
    assert b["max_stab_err"] == 0.0, "the mirror did not stabilise the image"
    assert b["gaze_distinct"] > 1, "the eye did NOT move — that is paralysis, not Ditchburn"

    a = _run(T.ARM_DRIFT)
    assert a["max_stab_err"] > 0.0, "the drift arm's image did not move at all"
    assert a["gaze_distinct"] > 1


def test_frozen_gaze_does_not_move_and_stabilised_gaze_does():
    """The manipulation is LIVE — FM-0's own positive control, at this rung's scale."""
    c = _run(T.ARM_FROZEN)
    b = _run(T.ARM_STABILISED)
    assert c["gaze_distinct"] == 1, "saw=0 did not freeze the gaze"
    assert b["gaze_distinct"] > 1, "saw=1 did not move the gaze"


def test_all_three_arms_see_an_IDENTICAL_retinal_image_at_t0():
    """The arms may diverge only as the gaze moves. If they differed at t=0 the
    comparison would be confounded from the first step."""
    vals = [_run(arm)["contrast_t0"] for arm in
            (T.ARM_DRIFT, T.ARM_STABILISED, T.ARM_FROZEN)]
    assert max(vals) - min(vals) == 0.0, f"arms differ at t=0: {vals}"


def test_the_fade_measures_FLOOR_is_reached_by_UNIFORMITY_not_by_DEATH():
    """§1.1 — 'a dead probe fades beautifully'. SD(resp) reads 0 for a SILENT sheet
    and a UNIFORM one alike, which is how FM-1's fade window was disqualified.

    A FLAT world has no contrast to represent, so the measure must floor — AND the
    sheet must still be 100% alive. That is the distinction the measure cannot make
    on its own, and it is why aliveness is reported beside it at every timepoint.
    """
    r = T.run_arm(0, T.ARM_FROZEN, vis_steps=VIS, calib_steps=CAL,
                  scene=T.uniform_scene(0.5), frozen=1.0)
    assert r["contrast_t0"] < 0.01, "the measure does not floor on a flat world"
    assert r["alive_t0"] > 0.99, "the floor was reached by DEATH, not by uniformity"


def test_the_reader_can_SEE_a_non_faded_response():
    """A fade is an ABSENCE CLAIM: positive-control the READER. With the mechanism
    OFF (a REAL freeze — every adaptation rule gated), a structured image must be
    read as high contrast and must NOT fade on its own."""
    r = T.run_arm(0, T.ARM_STABILISED, vis_steps=VIS, calib_steps=CAL, frozen=1.0)
    assert r["contrast_final"] > 0.1, "the reader cannot see a response that IS there"
    drift = abs(r["contrast_final"] - r["contrast_t0"]) / r["contrast_t0"]
    assert drift < 0.01, f"the measure fades on its own with the mechanism OFF ({drift:.4f})"


def test_defaults_preserve_committed_results():
    """§9 — this rung ships nothing new that is ON by default. It changes NO seed
    and NO default: `world_sample` and `mu_mode` remain 0, so FM-0 still reports
    VACUOUS and every committed result reproduces byte-identically."""
    import json
    seed = json.load(open(os.path.join(ROOT, "seeds", "vision_eye.json")))
    p = [n for n in seed["nodes"] if n["type"] == "EyeParams"][0]["attrs"]
    assert p["world_sample"] == 0.0, "world_sample must default OFF"
    assert p["mu_mode"] == 0.0, "mu_mode must default OFF"
    assert p["mu"] == 0.024, "the committed default setpoint changed"


def test_this_rung_adds_NO_rust_and_edits_NO_seed():
    """§12.3 — pinned to THIS RUNG'S OWN DIFF, never to a mutable tree.

    The claim is about what the Troxler rung's commits did: it adds no Rust Term and
    edits no other rung's seed. Each of THIS rung's commits is diffed against ITS OWN
    parent, so later work by anyone else cannot make this gate falsely accuse this
    rung (rung 8B's two gates rotted the same day by doing exactly that), and a
    rebase cannot silently widen the range (which is how the first cut of THIS gate
    was caught — see the note on RUNG_SUBJECT_PREFIX).
    """
    try:
        log = subprocess.run(
            ["git", "log", "--format=%H", f"--grep=^{RUNG_SUBJECT_PREFIX}"],
            cwd=ROOT, capture_output=True, text=True, timeout=60)
    except Exception as e:  # pragma: no cover
        pytest.skip(f"git unavailable: {e}")
    if log.returncode != 0:
        pytest.skip("git log not resolvable in this checkout")
    shas = [s for s in log.stdout.split() if s.strip()]
    if not shas:
        pytest.skip("this rung's commits are not in this checkout")
    files = []
    for sha in shas:
        d = subprocess.run(["git", "diff", "--name-only", f"{sha}^", sha],
                           cwd=ROOT, capture_output=True, text=True, timeout=60)
        if d.returncode == 0:
            files.extend(f for f in d.stdout.split() if f.strip())
    offenders = [f for f in files
                 if f.startswith("research/experiments/gamma-substrate/runners/")
                 or f.startswith("runners/")]
    assert not offenders, f"this rung added Rust: {offenders}"
    seeds_touched = [f for f in files if "/seeds/" in f or f.startswith("seeds/")]
    assert not seeds_touched, f"this rung edited a seed: {seeds_touched}"
