"""dorsal_world — RUNG 3 world adapter: the dorsal/motion population's wiring,
its entropy, and the drifting-stimulus PROBE that measures direction
selectivity.

ARCHITECTURE (CLAUDE.md). This is a WORLD ADAPTER + a MEASURE. It does exactly
four mechanical things, and makes no decisions over graph state:

  1. LAY OUT the dorsal population — mint `DUnit` nodes and wire them to a
     centred patch of the retina by `DSynapse` nodes. Positional geometry, the
     same kind of fact as `WaveWorld.add_units`' window slicing.
  2. SUPPLY ENTROPY — draw each DSynapse's conduction `delay` UNIFORMLY AT
     RANDOM from {0..max_delay}. THIS IS THE PARADIGM-CRITICAL LINE OF THE
     WHOLE RUNG. A delay-line direction detector is trivial to BUILD: set
     delay = k - (position along the preferred axis) and you have a
     direction-selective unit with no learning at all. That would be the
     `preprocess_patches` bolt-on error at the motion grain — handing the agent
     the structure it was supposed to grow. Random delays are UNSTRUCTURED by
     construction: every direction is symmetric a priori, the expected delay
     gradient is zero along every axis, and any direction preference that
     appears was manufactured by `dv_oja_learn` out of the input's own motion
     statistics. Random delays are to direction what random ignition is to
     waves.
  3. SUPPLY STIMULI — generate drifting-bar frames (pure geometry) and hand
     them to the retina through the existing, unmodified `WaveWorld.drive`.
  4. READ BACK — query each DUnit's `dact` and compute the Direction
     Selectivity Index. Pure arithmetic on numbers read out of the graph, the
     same class of thing as `anisotropy`: an experimenter's readout, not the
     agent's cognition.

WHAT IS NOT HERE, ON PURPOSE: any preferred direction, any delay gradient, any
motion-energy filter, any temporal-difference front end. The drive path is the
committed `WaveWorld.drive` untouched; the transient channel that makes motion
readable is the `dv_transient` RULE in seeds/vision_dorsal.json, not a numpy
diff in this file.
"""
from __future__ import annotations

from typing import Any, Optional

import numpy as np

from domains.wave_world import WaveWorld, _add_edge

# The probe's directions: 8 evenly spaced, so every direction has an exact
# opposite (k and k+4) for the null. Fixed here rather than swept — the DSI's
# null direction MUST be the anti-preferred one, and a sweep over direction
# counts would be a forking path.
N_DIR = 8
DIRECTIONS = tuple(2.0 * np.pi * k / N_DIR for k in range(N_DIR))


# --------------------------------------------------------------------------- #
#  (1)+(2) WIRING + ENTROPY
# --------------------------------------------------------------------------- #
def add_dunits(world: WaveWorld, n_units: int, *, rf: int = 7,
               max_delay: int = 3, w0: float = 1.0, jitter: float = 0.05,
               rng: Optional[np.random.Generator] = None) -> list:
    """Mint `n_units` DUnits, each fully connected to a centred `rf` x `rf`
    patch of the retina by DSynapse nodes carrying a RANDOM conduction delay.

    Positional wiring + entropy only. Initial weights are uniform `w0` with a
    small symmetry-breaking jitter (a tie-break, not structure — a perfectly
    uniform population would have no winner to take all), exactly as
    `WaveWorld.add_units` does. Delays are uniform over {0..max_delay}: see the
    module docstring for why that line is the paradigm-critical one.

    REFUSES to build on a world that is not tracking `prev_burst`, because the
    failure is SILENT and produces wrong science. `dv_transient` fires iff
    `last_burst == step AND prev_burst < step - 1`; with tracking off,
    `prev_burst` stays at its -999 sentinel forever, so the second clause is
    ALWAYS true and the transient fires on EVERY burst step. The dorsal stream
    then reads the SUSTAINED channel — measured on a static half-field with
    tracking off: 128 "transients" per step, every step, instead of 128 once —
    which is exactly the structural blindness to motion that the transient
    channel exists to fix, with no error raised. A wrong-channel run looks
    entirely normal and just quietly answers a different question.
    """
    if not getattr(world, "track_prev_burst", False):
        raise ValueError(
            "add_dunits requires WaveWorld(..., track_prev_burst=True): the "
            "dv_transient rule reads prev_burst, and with tracking off it "
            "silently fires on every burst step, so the dorsal stream reads "
            "the SUSTAINED channel and is blind to motion. This is a wrong-"
            "science failure, so it is raised rather than defaulted.")
    s = world.s
    rng = rng if rng is not None else world.rng
    units = []
    half = rf // 2
    for i in range(n_units):
        cy = half + int(rng.integers(0, max(1, world.h - rf + 1)))
        cx = half + int(rng.integers(0, max(1, world.w - rf + 1)))
        u = s.add_node("DUnit", {"name": f"d{i}", "dact": 0.0,
                                 "bursting": 0.0, "dact_step": -1.0,
                                 "burst_step": -1.0, "last_burst": -999.0,
                                 "cy": float(cy), "cx": float(cx),
                                 "rf": float(rf)})
        _add_edge(s, world.retina, "has_dunit", u)
        for dr in range(-half, half + 1):
            for dc in range(-half, half + 1):
                cell = world.cells.get((cy + dr, cx + dc))
                if cell is None:
                    continue
                w = float(w0 * (1.0 + jitter * rng.normal()))
                syn = s.add_node("DSynapse", {
                    "weight": max(w, 1e-3), "touched": -1.0,
                    "delay": float(int(rng.integers(0, max_delay + 1))),
                    "drow": float(dr), "dcol": float(dc)})
                _add_edge(s, cell, "dpre", syn)
                _add_edge(s, syn, "dpost", u)
        units.append(u)
    return units


def dunit_synapses(world: WaveWorld, u) -> list:
    """Every DSynapse on a DUnit, in a STABLE order (by drow, dcol, delay), so
    two read-backs of the same unit are directly comparable. Pure query."""
    out = []
    for syn in world.s.in_neighbours(u, "dpost"):
        at = world.s.node(syn)["attrs"]
        out.append((float(at["drow"]), float(at["dcol"]), float(at["delay"]),
                    float(at["weight"])))
    out.sort(key=lambda t: (t[0], t[1], t[2]))
    return out


def dunit_weights(world: WaveWorld, u) -> np.ndarray:
    """A DUnit's weight VECTOR in stable order — what the drift measure
    (||w(t) - w(t-D)|| / ||w||) is computed on. Pure query."""
    return np.array([t[3] for t in dunit_synapses(world, u)], np.float64)


def set_dunit_ideal(world: WaveWorld, u, theta: float, *,
                    max_delay: int = 3) -> None:
    """CALIBRATION ONLY — hand-construct an IDEAL direction-selective unit
    preferring `theta`: set each synapse's conduction delay to exactly cancel
    its position along the motion axis (delay = max_delay - proj, so
    delay + proj = const and EVERY input arrives at the unit on the same step
    for motion along `theta`), weight 1 where that delay is realisable and ~0
    elsewhere.

    This is the ideal exemplar PROTOCOL section 1 demands ('run it on an ideal
    exemplar of the structure — it must score high'). It sets the DELAYS as
    well as the weights, because a delay-line direction detector IS its delay
    gradient; an exemplar built only by re-weighting the adapter's RANDOM
    delays is a weak one (only the ~1-in-4 synapses whose random delay happens
    to land on the line can be kept), and a measure must be calibrated against
    the real thing rather than against a diluted version of it.

    This is EXACTLY the hand-built structure the agent must never be handed —
    it is the `preprocess_patches` error made deliberately, as a ruler. It is
    never called on an experimental arm: the arms get uniform random delays
    from `add_dunits` and have to grow any preference themselves. Its only job
    is to prove the DSI can see direction selectivity when it is present, so
    that a null on an arm means 'the agent did not grow it' rather than 'the
    instrument cannot see it'.
    """
    s = world.s
    for syn in s.in_neighbours(u, "dpost"):
        at = s.node(syn)["attrs"]
        proj = float(at["dcol"]) * np.cos(theta) + float(at["drow"]) * np.sin(theta)
        d = round(max_delay - proj)
        if 0 <= d <= max_delay:
            s.set_attr(syn, "delay", float(d))
            s.set_attr(syn, "weight", 1.0)
        else:
            s.set_attr(syn, "weight", 1e-6)


# --------------------------------------------------------------------------- #
#  (3) STIMULI — pure geometry
# --------------------------------------------------------------------------- #
def drifting_bar(h: int, w: int, theta: float, pos: float,
                 halfwidth: float = 0.7) -> np.ndarray:
    """One frame of a bar perpendicular to `theta`, centred at `pos` along the
    motion axis. Pure geometry — no filtering, no normalisation."""
    yy, xx = np.mgrid[:h, :w]
    proj = xx * np.cos(theta) + yy * np.sin(theta)
    return (np.abs(proj - pos) <= halfwidth).astype(np.float32)


def gaze_walk(video: np.ndarray, n: int, h: int, w: int, *,
              rng: np.random.Generator, speed: float = 1.0,
              hold: int = 20) -> np.ndarray:
    """THE RETINAL IMAGE OF A NORMALLY-REARED ANIMAL: `n` (h, w) crops of a
    larger video, taken through an eye that DRIFTS. Returns the retinal frame
    sequence; mechanical translation of where the eye is pointed, which is world
    I/O in exactly the sense `WaveWorld.ignite` is.

    WHY THIS EXISTS, MEASURED BEFORE ANY ARM WAS RUN. Real video at 16x16 is
    very nearly STATIC: at native frame rate, consecutive frames differ by 0.005
    (grey levels in [0,1]) and the median-split drive yields a burst ONSET rate
    of 0.6% against a 50% duty cycle — i.e. 99% of the drive is a standing
    pattern. A `normal` arm built on it would deliver almost no motion at all,
    so a null on 'moving experience produces direction selectivity' would mean
    'there was no motion in the moving-experience arm', not anything about
    development. That is the wrong-arm error PROTOCOL section 6 exists to
    prevent, and it is checked here rather than discovered afterwards.

    IT IS ALSO THE BIOLOGY, not a convenience. No animal has a stabilised
    retina: fixational ocular drift and microsaccades are continuous, and a
    retinal image that IS stabilised FADES FROM PERCEPTION ENTIRELY (Ditchburn &
    Ginsborg 1952; Riggs & Ratliff 1952; Troxler fading). A normally-reared
    animal's retina is in near-constant motion even in front of a static scene,
    so the perfectly-stabilised retina — not the drifting one — is the
    unphysical model. Supplying the eye's motion is the adapter's job; what the
    graph must grow is the ability to READ it.

    The drift is a piecewise-constant velocity: a direction is drawn at random,
    held for `hold` steps, then redrawn (drift epochs punctuated by
    microsaccades). It is DIRECTION-ISOTROPIC by construction — the adapter has
    no preferred direction and hands the agent no direction gradient, exactly as
    wave ignition hands it no spatial structure. `speed` is 1 px/step, matching
    the probe's, because that is the velocity range a 0-3 step delay line can
    resolve at all; it is a stated design choice, not a swept parameter.
    """
    H, W = video.shape[1], video.shape[2]
    y = float(rng.integers(0, max(1, H - h)))
    x = float(rng.integers(0, max(1, W - w)))
    vy = vx = 0.0
    out = []
    for i in range(n):
        if i % hold == 0:
            th = float(rng.random()) * 2.0 * np.pi
            vy, vx = speed * np.sin(th), speed * np.cos(th)
        y += vy
        x += vx
        y = float(np.clip(y, 0, max(0, H - h)))
        x = float(np.clip(x, 0, max(0, W - w)))
        iy, ix = int(round(y)), int(round(x))
        out.append(video[i % len(video)][iy:iy + h, ix:ix + w].copy())
    return np.stack(out)


def _proj_range(h: int, w: int, theta: float) -> tuple[float, float]:
    yy, xx = np.mgrid[:h, :w]
    proj = xx * np.cos(theta) + yy * np.sin(theta)
    return float(proj.min()), float(proj.max())


def reset_retina(world: WaveWorld) -> None:
    """Clear every cell's activity history so a probe sweep starts from a blank
    retina and cannot read a stale burst from the previous sweep. Mechanical."""
    for n in world.cells.values():
        world.s.set_attr(n, "state", "rested")
        world.s.set_attr(n, "driven", 0.0)
        world.s.set_attr(n, "bursting", 0.0)
        world.s.set_attr(n, "last_burst", -999.0)
        world.s.set_attr(n, "prev_burst", -999.0)
        world.s.set_attr(n, "dlast_burst", -999.0)
        world.s.set_attr(n, "fired_at", -999.0)
        world.s.set_attr(n, "activated_at", -999.0)


# --------------------------------------------------------------------------- #
#  (4) THE MEASURE — Direction Selectivity Index
# --------------------------------------------------------------------------- #
def sweep_frames(h: int, w: int, k: int, phase: float = 0.0,
                 speed: float = 1.0) -> list:
    """The frame sequence for direction `k` of `N_DIR`.

    THE MIRRORED-PAIR CONSTRUCTION, and it is the core of the measure. Direction
    `k` and its opposite `k + N_DIR/2` share one AXIS (a bar is a line; the line
    perpendicular to theta is the same line as the one perpendicular to
    theta+180). This builds ONE position sequence per axis and hands it to the
    opposite direction REVERSED. Directions k and k+4 therefore present the
    EXACT SAME SET OF FRAMES, pixel for pixel, in the opposite ORDER.

    WHY THIS AND NOT INDEPENDENT SWEEPS: measured on the first cut, which swept
    each direction independently. The tuning curves came out IDENTICAL for
    45/135/225/315 and for 90/180/270, and every one of 10 units reported the
    same DSI of 0.026 — the "direction" signal was a pixel-quantisation artifact
    of the bar geometry (an irrational projection lands on the sampling grid
    differently per angle), common to every unit and every arm, and it would
    have been read as a non-zero floor that a trained unit could inherit. Under
    the mirrored construction the spatial statistics of a direction and its
    opposite are IDENTICAL BY CONSTRUCTION, so the ONLY thing that can separate
    them is the ORDER of activation — which is precisely what direction
    selectivity is. The probe is thereby a per-direction temporal-shuffle
    control, and the DSI's floor is an exact zero rather than an empirical
    hope.
    """
    axis = k % (N_DIR // 2)
    theta = np.pi * axis / (N_DIR // 2)
    lo, hi = _proj_range(h, w, theta)
    n_steps = int(np.ceil((hi - lo) / speed)) + 4
    pos = [lo - 2.0 + phase + i * speed for i in range(n_steps)]
    frames = [drifting_bar(h, w, theta, p) for p in pos]
    return frames if k < (N_DIR // 2) else frames[::-1]


def sweep_response(world: WaveWorld, dunits: list, k: int,
                   phase: float = 0.0, speed: float = 1.0) -> np.ndarray:
    """Drift a bar across the retina in direction `k` and return each DUnit's
    PEAK `dact` over the sweep. Drive goes through the committed, unmodified
    `WaveWorld.drive`; the response is read straight off the graph.

    PEAK, NOT MEAN — and the reason is a PROVEN property of the model, found by
    calibrating the measure before using it (PROTOCOL section 1) rather than
    after. A DUnit's drive is LINEAR in its arriving inputs, and over one bar
    sweep every cell in the RF fires exactly one transient and therefore
    contributes to exactly one step (the step `delay` after it fired). So the
    SUM of dact over a sweep is the sum of the unit's weights — IDENTICAL for
    every direction, by construction. Measured on the mirrored pair: sum(dact)
    = 48.75 forward vs 48.76 reversed, while the PEAK was 11.07 vs 8.95. A
    time-averaged readout of a linear unit is MATHEMATICALLY INCAPABLE of
    measuring direction selectivity in this model, and it duly scored the
    hand-built IDEAL direction-selective unit at 0.004 — i.e. at the floor.

    What direction changes is not how much drive arrives but WHEN: in the
    preferred direction the delay line makes every input arrive on the SAME
    step (a tall, narrow peak); in the null direction the same inputs are
    smeared across the sweep. Direction lives in the TEMPORAL CONCENTRATION of
    the drive, so the readout must be a concentration statistic. That is also
    the biologically correct reading: a neuron has a spiking threshold, and a
    coincident volley crosses it where the same charge dribbled out over a
    second does not. The peak is what the unit's own winner-take-all burst rule
    is reading when it fires.

    This is a fix to the MEASURE, made BEFORE any hypothesis test was run and
    recorded here and in VISION_RUNG3_PREREG.md. It is not metric surgery
    (PROTOCOL section 5): nothing had failed a gate — the calibration exemplar
    is exactly the instrument designed to catch this, and it did.
    """
    reset_retina(world)
    frames = sweep_frames(world.h, world.w, k, phase=phase, speed=speed)
    peak = np.zeros(len(dunits), np.float64)
    for fr in frames:
        world.step(ignite_k=0, frame=fr)
        for j, u in enumerate(dunits):
            peak[j] = max(peak[j], float(world.s.node(u)["attrs"]["dact"]))
    return peak


def probe_dsi(world: WaveWorld, dunits: list, *, seed: int = 0,
              n_rep: int = 4, speed: float = 1.0) -> np.ndarray:
    """THE MEASURE. Returns a per-DUnit, CROSS-VALIDATED Direction Selectivity
    Index in [-1, 1].

    Each of the 8 directions is swept `n_rep` times with an independent random
    sub-pixel start PHASE. The reps are split in half: the preferred direction
    is chosen on half A, and the DSI

        (R_pref - R_null) / (R_pref + R_null),   null = pref + 180 degrees

    is evaluated on the held-out half B.

    WHY CROSS-VALIDATED: the textbook DSI picks the preferred direction by
    argmax over the SAME responses it then scores. Argmax over noise is biased
    upward, and the bias GROWS with the response variance across directions,
    which itself differs between arms — so the floor would be neither constant
    nor interpretable, and every arm difference would be partly a difference in
    noise. Splitting pref-selection from evaluation removes that selection bias
    by construction.

    THE FLOOR IS NOT ZERO, AND THAT IS A FACT ABOUT THE MODEL, NOT A DEFECT OF
    THE MEASURE. Measured on untrained units: DSI = 0.111 (n=8 burned seeds, SD
    0.021 across seeds), against a hand-built ideal's 0.44. Cross-validation
    does not remove it because it is NOT noise — it is real, reproducible
    structure: a unit whose conduction delays are drawn at random has, by
    chance, a slightly better delay gradient along some direction than along
    its opposite, and that preference replicates across reps because the delays
    are fixed. Random wiring confers weak direction bias for free.

    THE CONSEQUENCE FOR EVERY CLAIM MADE WITH THIS MEASURE: an arm's absolute
    DSI is meaningless on its own, and 'DSI > 0' is NOT evidence of learned
    direction selectivity. Only a PAIRED comparison is interpretable — the arms
    share a seed and therefore share their delays, so the innate bias is
    identical in each and cancels in the difference. The floor is measured
    per-seed by an `untrained` arm (no training at all, same delays) so that
    'waves produce no direction selectivity' is tested against what the wiring
    already gives rather than against zero.

    NO LEARNING HAPPENS DURING A PROBE. `oja_eta` AND `bi_eta` are BOTH set to 0
    for the duration (dv_oja_learn's update is a SUM of an Oja part scaled by
    oja_eta and a rung-3B bistable part scaled by bi_eta; zeroing both degenerates
    the whole rule to w <- w*1 + 0 + 0 = w, exactly the identity) and `propagate`
    to 0 so no wave contaminates the response. All three are restored afterwards.
    Configuration writes, not decisions.

    ZEROING bi_eta TOO IS A MEASURED INSTRUMENT FIX, found by the rung-3B positive
    control BEFORE any arm was run. The freeze originally zeroed only `oja_eta`, on
    the reasoning that Oja then degenerates to the identity. That reasoning was
    correct for rung 3 and FALSE the moment the bistable term was added: the term
    is scaled by `bi_eta`, NOT by `oja_eta`, so the probe went on training the unit
    ON THE PROBE STIMULUS -- the measure was manufacturing the thing it measured.

    It shows up in the one place it cannot hide: the positive control's step-0
    column is taken BEFORE ANY TRAINING STEP and must therefore equal the 0.111
    floor in every row. It did not. It rose monotonically with bi_eta -- 0.112,
    0.118, 0.136, and 0.339 at bi_eta=1e-1, a 3x floor jump produced entirely by
    measuring. Every armed number in that table was training on the test set, and
    the apparent bi_eta=1e-1 "win" was almost all of it.

    The gate that should have caught this (test_the_probe_does_not_let_the_agent_learn)
    PASSED throughout, because it booted with bistable=0: it checked the freeze's
    CONSTANTS while being blind to the AXIS they parameterise, which is exactly the
    defect PROTOCOL section 1 names ("a gate that checks a rule's CONSTANTS but not
    the AXIS they parameterise is not a gate"). It is now run with the term ARMED,
    which is the only version of it that could have failed.
    """
    s = world.s
    dp = s.nodes("DorsalParams")[0]
    wp = s.nodes("WaveParams")[0]
    eta0 = float(s.node(dp)["attrs"]["oja_eta"])
    bi0 = float(s.node(dp)["attrs"].get("bi_eta", 0.0))
    prop0 = float(s.node(wp)["attrs"]["propagate"])
    s.set_attr(dp, "oja_eta", 0.0)
    s.set_attr(dp, "bi_eta", 0.0)
    s.set_attr(wp, "propagate", 0.0)
    try:
        rng = np.random.default_rng(seed + 5_150_000)
        # One phase per (axis, rep), SHARED by a direction and its opposite, so
        # the mirrored pair stays exactly mirrored.
        phases = rng.random((N_DIR // 2, n_rep))
        R = np.zeros((N_DIR, n_rep, len(dunits)), np.float64)
        for k in range(N_DIR):
            for rep in range(n_rep):
                R[k, rep] = sweep_response(world, dunits, k,
                                           phase=float(phases[k % (N_DIR // 2), rep]),
                                           speed=speed)
    finally:
        s.set_attr(dp, "oja_eta", eta0)
        s.set_attr(dp, "bi_eta", bi0)
        s.set_attr(wp, "propagate", prop0)

    half = n_rep // 2
    A = R[:, :half].mean(axis=1)          # (dir, unit) — choose pref here
    B = R[:, half:].mean(axis=1)          # (dir, unit) — score here
    pref = A.argmax(axis=0)               # (unit,)
    null = (pref + N_DIR // 2) % N_DIR
    idx = np.arange(len(dunits))
    rp, rn = B[pref, idx], B[null, idx]
    den = rp + rn
    return np.where(den > 0, (rp - rn) / np.where(den > 0, den, 1.0), 0.0)


def mean_dsi(world: WaveWorld, dunits: list, **kw) -> float:
    """The per-run scalar: the mean cross-validated DSI over the run's DUnits.
    The SEED is the unit of analysis (PROTOCOL section 4) — units in a run share
    input and compete under winner-take-all, so they are not independent."""
    return float(np.mean(probe_dsi(world, dunits, **kw)))


__all__ = ["add_dunits", "dunit_synapses", "dunit_weights", "set_dunit_ideal",
           "gaze_walk",
           "drifting_bar", "reset_retina", "sweep_frames", "sweep_response",
           "probe_dsi", "mean_dsi", "DIRECTIONS", "N_DIR"]
