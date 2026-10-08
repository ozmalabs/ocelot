"""wave_world — RUNG 1 world adapter: the retina's substrate + entropy + clock.

ARCHITECTURE (CLAUDE.md). This is a WORLD ADAPTER and nothing else. It does
exactly three mechanical things:

  1. LAY OUT the retina — mint `RetinaCell` nodes on a grid and wire `neighbour`
     edges. Positional geometry, exactly like `VisionWorld.ingest` slicing an
     image into windows. No content decision.
  2. SUPPLY ENTROPY — inject random ignition seeds (`state="active"`). This is
     the stochastic-depolarisation analogue: biology's wave initiation IS
     random. It is UNSTRUCTURED by construction and carries no spatial or
     temporal correlation.
  3. ADVANCE A CLOCK — increment `Retina.step` and commit the recruited cells.

THE PARADIGM-FORCING SPLIT — the whole point of this rung:

    the adapter supplies UNSTRUCTURED entropy; the GRAPH makes the STRUCTURE.

All propagation, refractoriness and the resulting spatiotemporal correlation
are `seeds/vision_waves.json` rules. The `noise` control arm uses the SAME
entropy source with `WaveParams.propagate = 0` — so the two arms differ ONLY in
whether the agent's own rules ran. Any structure that shows up in the wave arm
and not the noise arm was manufactured by the graph, not handed to it by this
file. That is what makes rung 1 a test of the paradigm rather than a
demonstration of numpy.

Why the adapter may legitimately supply randomness: an RNG is not structure.
Biology's ignition is stochastic; what the retina contributes is the CIRCUIT
that turns stochastic ignition into travelling waves. Supplying the noise and
claiming the circuit would be the bolt-on error (that is exactly what
`vision_corpus.preprocess_patches` did by hand-building a retina); supplying
the noise and making the graph build the circuit is the honest split. The noise
arm is the control that proves it.
"""
from __future__ import annotations

import json
import os
from typing import Any, Optional

import numpy as np


def _add_edge(s, src, et, tgt):
    try:
        s.add_edge(src, et, tgt, None)
    except TypeError:
        s.add_edge(src, et, tgt)


_CHANGE_SEED = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            "domain_data", "vision_change.json")


def _install_change_rules(s) -> list:
    """Install `domain_data/vision_change.json` — the drive DECISION as graph data —
    and return its rule indices in file order. Mechanical seed I/O.

    FIND-OR-CREATE on the params node, and that is load-bearing, not tidiness:
    every config read in the seed is `PickUnique`, which PANICS on >1 candidate
    (§12.3, deliberately). If this adapter blindly added a second `ChangeParams`
    on top of a loader-installed one, every rule in the seed would abort. So the
    node is added ONLY if absent, and the same applies to the rules (a re-install
    would double-fire them). For the same reason `vision_change` is deliberately
    NOT registered in `seed_registry`: this adapter is its loader, because it is
    the only caller that needs the rule INDICES back in order to phase them.

    `_inner` is the native substrate — the accessor precedent is
    `domains/measurement_feedback.py` (`nat = substrate._inner if hasattr(...)`).
    `add_rule`/`apply_rule_once` live there and not on the Python wrapper.
    """
    with open(_CHANGE_SEED) as fh:
        seed = json.load(fh)
    nat = s._inner if hasattr(s, "_inner") else s
    if not s.nodes("ChangeParams"):
        for n in seed.get("nodes", []):
            attrs = {k: v for k, v in n["attrs"].items() if k != "comment"}
            s.add_node(n["type"], attrs)
    return [nat.add_rule({k: v for k, v in r.items() if k != "comment"})
            for r in seed.get("rules", [])]


class WaveWorld:
    """The retina world. Construct with a booted substrate (the `vision_waves`
    seed must be loaded) and a grid size."""

    def __init__(self, s, *, h: int = 16, w: int = 16, seed: int = 0,
                 fovea_radius: int = 0, saccade_every: int = 4,
                 track_prev_burst: bool = False):
        self.s = s
        self.h = h
        self.w = w
        self.rng = np.random.default_rng(seed)
        # THE DRIVE DECISION IS THE GRAPH'S (domain_data/vision_change.json). This
        # adapter installs that seed's rules and remembers their indices so it
        # can drive them AS A PHASE (`apply_rule_once`) between `drive()` (which
        # writes the luminance FACTS) and `_mark_bursts` (which reads `driven`).
        # A phase dispatch, not a decision: the precedent is `domains/language.py`
        # ("apply_rule_once, so only THIS phase's rules fire") and
        # `linear_algebra.py` ("run only this rule to a fixed point"). It is
        # REQUIRED here rather than stylistic: `_mark_bursts` consumes `driven`
        # BEFORE `s.tick()`, so a rule that only fired inside `tick()` would be
        # a step too late to reach `bursting`.
        self._drive_rules = _install_change_rules(s)
        # RUNG 3 (dorsal) bookkeeping, DEFAULT OFF so every committed rung-1 /
        # rung-2 result reproduces byte-identically. When on, `_mark_bursts`
        # also records `prev_burst` = what `last_burst` held BEFORE this step's
        # update. That is a FACT, not a decision: the DECISION of what counts as
        # a transient (burst onset) is the `dv_transient` RULE in
        # seeds/vision_dorsal.json, which reads it. It is written here for the
        # same reason `last_burst` is written here rather than by a rule — a
        # rule setting it would race the rules reading it inside one fixpoint.
        self.track_prev_burst = bool(track_prev_burst)
        # SPARSE VISUAL DRIVE: a foveal aperture on the `driven` channel only.
        # fovea_radius=0 => whole field (the committed behaviour; default, so
        # every existing result reproduces untouched).
        self.fovea_radius = fovea_radius
        self.saccade_every = saccade_every
        self._fovea = None
        # SEPARATE RNG for saccades. Load-bearing: the gaze must not consume
        # draws from the ignition RNG, or turning the fovea on would shift the
        # wave sequence and the scaffold would no longer be invariant across
        # arms (measured: shared RNG moved wave activity 0.071 -> 0.091, which
        # would have confounded the whole comparison).
        self.gaze_rng = np.random.default_rng(seed + 777_777)
        self.retina = s.add_node("Retina", {"h": float(h), "w": float(w),
                                            "step": 0.0,
                                            # The frame's own median, written as
                                            # a FACT by `drive()` so the median
                                            # SPLIT can be a rule instead of an
                                            # adapter decision.
                                            "frame_median": 0.0})
        self.cells: dict[tuple[int, int], Any] = {}
        for r in range(h):
            for c in range(w):
                n = s.add_node("RetinaCell", {
                    "row": float(r), "col": float(c),
                    "state": "rested", "fired_at": -999.0,
                    "activated_at": -999.0, "bursting": 0.0,
                    "last_burst": -999.0, "driven": 0.0,
                    "prev_burst": -999.0, "dlast_burst": -999.0,
                    # THE RECEPTOR'S FACTS — written by `drive()`, read by the
                    # `ch_*` rules, decided on by nobody here.
                    #   lum_raw   this step's luminance
                    #   lum_prev  last step's (the transient channels' reference)
                    #   lum_ref   the cell's OWN cumulative-mean reference (the
                    #             sustained channel's; `ch_adapt_ref` maintains it)
                    #   lum_seen  how many frames this cell has seen — gates the
                    #             first step, where `lum_prev` has no meaning yet
                    "lum_raw": 0.0, "lum_prev": 0.0, "lum_ref": 0.0,
                    "lum_seen": 0.0, "ref_n": 0.0, "ref_step": -999.0,
                    # One phase key PER drive rule (never a shared one, which
                    # would let whichever rule fired first block the others for
                    # this cell). Each says "I have already fired this step", so
                    # the adapter's fixed-point loop TERMINATES.
                    "dstep_med": -999.0, "dstep_on": -999.0,
                    "dstep_off": -999.0, "dstep_sus": -999.0})
                _add_edge(s, self.retina, "has_cell", n)
                self.cells[(r, c)] = n
        # 4-neighbourhood: mechanical geometry (the grid's own adjacency), the
        # only spatial fact the adapter states. WHAT travels along it, and
        # whether anything does, is the rules' business.
        for (r, c), n in self.cells.items():
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                m = self.cells.get((r + dr, c + dc))
                if m is not None:
                    _add_edge(s, n, "neighbour", m)
        # The cell id list in a FIXED order, cached once. The bulk accessors
        # are positional, so this list and `self.cells` must agree; it is built
        # here, from the same dict, and the grid never changes size after
        # construction. Purely an ordering handle — no state, no decision.
        self._cell_ids = list(self.cells.values())
        self._cell_rc = list(self.cells.keys())

    # ---- (2) ENTROPY: unstructured random ignition -----------------------
    def ignite(self, k: int = 1) -> list:
        """Inject `k` random ignition seeds. UNSTRUCTURED: uniform over the
        grid, independent across calls, no spatial or temporal correlation.
        The identical call feeds the noise arm."""
        out = []
        # ONE crossing for all N states instead of N full-dict materialisations.
        states = self.s.get_attr_many(self._cell_ids, "state")
        rested = [n for n, stt in zip(self._cell_ids, states) if stt == "rested"]
        if not rested:
            return out
        st = float(self.s.node(self.retina)["attrs"]["step"])
        for _ in range(k):
            n = rested[int(self.rng.integers(0, len(rested)))]
            self.s.set_attr(n, "state", "active")
            self.s.set_attr(n, "activated_at", st)   # FRESH: propagates this step
            out.append(n)
        return out

    # ---- EXPERIENCE: external drive (mechanical ingest) -------------------
    def drive(self, frame: Optional[np.ndarray]) -> None:
        """Drive the retina from an external (h, w) frame: a cell whose pixel
        exceeds the frame's own median is marked `driven`. Mechanical ingest —
        the same kind of translation `VisionWorld.ingest` does, no decision.

        VISUAL DRIVE IS NOT WAVE IGNITION. This is the mechanism fix, and it is
        the whole point of the rung. The first two cuts set `state="active"` —
        the SAME state a wave ignition uses — so every driven pixel became a
        travelling-wave SOURCE, and "experience" was really mass wave ignition
        that drowned the scaffold it was meant to refine. Measured
        (propagate ON vs OFF, identical drive): waves alone 0.071 vs 0.001
        (×91 — the waves ARE the propagation, as designed), but video 0.171 vs
        0.099 (×1.7) and noise 0.173 vs 0.151 (×1.1) — i.e. the drive was
        injecting 10–15% activity DIRECTLY, dwarfing the waves' 7%, and then
        propagating on top. That artifact explains every earlier arm ordering:
        noise scatters ignition maximally (−0.165), correlated video less so
        (−0.090), a small fovea barely at all (−0.013). None of it was
        experience refining anything.

        The biology is two PATHWAYS converging on one output: retinal waves are
        generated by the inner-retina amacrine network; visual input drives
        photoreceptors → bipolar → RGC. Both make the ganglion cell fire, but a
        visually-driven RGC does not launch a travelling wave. So `driven` is a
        separate channel: it contributes to `bursting` (the RGC output the
        learning rules read) and is invisible to `wv_propagate`, which matches
        only `state == "active"`.

        THE MEDIAN SPLIT IS NO LONGER DECIDED HERE — and that is this method's
        whole point now. It used to threshold the frame at its OWN median, which
        made `driven%` EXACTLY 50.00 at every size and in EVERY regime: a number
        that round is never nature, it is the adapter asserting a statistic
        rather than the world supplying one. It cost rung 1's `waves+video` arm
        (the median blasts ~50% of the retina every step = a degraded pattern,
        not normal rearing) and it made natural-image sparsity unmeasurable,
        which is what blocks the scale question.

        So this method now writes only FACTS — `lum_raw` (this frame's
        luminance), `lum_prev` (last frame's), `lum_seen`, and the frame's own
        `frame_median` — and the DECISION of what counts as `driven` is the
        `ch_*` rules in `domain_data/vision_change.json`: `ch_drive_median` reproduces
        the old split verbatim under the complementary `change < 0.5` guard
        (PROTOCOL §9 — the default reproduces byte-identically), and the
        transient/sustained channels replace it when `change = 1`. A cell's
        luminance is an observed datum; what counts as a CHANGE is the agent's
        call, and it is now graph data the agent can vary and repair.

        `lum_prev` is carried here, before any rule reads it, for exactly the
        reason `last_burst` and the recruit commit are: a rule maintaining it
        would race the rules reading it inside one fixpoint."""
        if frame is None:
            return
        st = float(self.s.node(self.retina)["attrs"]["step"])
        rad = self.fovea_radius
        if rad <= 0:                                    # whole field (default)
            # The frame's own median, as a FACT for `ch_drive_median` to read.
            # Written on the RAW frame and compared against the RAW `lum_raw`,
            # exactly as the old Python did, so the floats are bit-for-bit what
            # they were: a log-space median would NOT be byte-identical, because
            # numpy averages the two middle values on an even count (256 cells)
            # and log(mean) != mean(log).
            self.s.set_attr(self.retina, "frame_median", float(np.median(frame)))
            if getattr(self, "bulk_ingest", False):
                # PROTOCOL §9 OPT-IN (the `detect_cycles` precedent): DEFAULT
                # OFF, so the committed per-cell path below is UNCHANGED and
                # runs unless a caller sets `w.bulk_ingest = True`. This is the
                # scale rung's bulk PyO3 handoff: the ONE surviving per-cell
                # Python->Rust loop (4 crossings/cell; `node()` materialises the
                # WHOLE attr dict to read nothing) collapses to 5 bulk crossings.
                # BYTE-IDENTICAL BY CONSTRUCTION: the SAME float() conversions
                # produce the SAME f64 values in the SAME cell order; only the
                # number of crossings changes. `set_attr_many` cannot do this —
                # the values DIFFER per cell — which is why `set_attr_each`
                # (its per-node-value complement) exists. The reads gather the
                # INITIAL lum_raw/lum_seen (exactly the per-cell path's per-cell
                # snapshot, since no cell reads another cell) BEFORE any write.
                fh, fw = frame.shape[0], frame.shape[1]
                sub_ids, vals_raw = [], []
                for n, (r, c) in zip(self._cell_ids, self._cell_rc):
                    if r < fh and c < fw:
                        sub_ids.append(n)
                        vals_raw.append(float(frame[r, c]))
                prev = self.s.get_attr_many(sub_ids, "lum_raw")
                seen = self.s.get_attr_many(sub_ids, "lum_seen")
                self.s.set_attr_each(
                    sub_ids, "lum_prev",
                    [float(p if p is not None else 0.0) for p in prev])
                self.s.set_attr_each(sub_ids, "lum_raw", vals_raw)
                self.s.set_attr_each(
                    sub_ids, "lum_seen",
                    [float(s if s is not None else 0.0) + 1.0 for s in seen])
                self._drive_phase()
                return
            for (r, c), n in self.cells.items():
                if r < frame.shape[0] and c < frame.shape[1]:
                    at = self.s.node(n)["attrs"]
                    self.s.set_attr(n, "lum_prev", float(at.get("lum_raw", 0.0)))
                    self.s.set_attr(n, "lum_raw", float(frame[r, c]))
                    self.s.set_attr(n, "lum_seen",
                                    float(at.get("lum_seen", 0.0)) + 1.0)
            self._drive_phase()
            return
        # SPARSE: a foveal aperture that relocates saccade-like. Now that the
        # visual drive is a SEPARATE channel from wave ignition, shrinking the
        # aperture limits only what EXPERIENCE touches — the wave scaffold is
        # untouched either way (verified: activity identical across arms). That
        # is what makes this a different claim from the attempt-2 fovea, whose
        # aperture also throttled wave ignition and so destroyed the
        # deprivation asymmetry along with the harm.
        # Saccade targets come from the adapter's RNG: positional entropy, like
        # wave ignition. Curiosity-driven gaze would be a DECISION (a rule), and
        # is deliberately not smuggled in here.
        if self._fovea is None or (self.saccade_every and st % self.saccade_every == 0):
            self._fovea = (int(self.gaze_rng.integers(0, self.h)),
                           int(self.gaze_rng.integers(0, self.w)))
        fy, fx = self._fovea
        inside = [(r, c) for (r, c) in self.cells
                  if (r - fy) ** 2 + (c - fx) ** 2 <= rad * rad
                  and r < frame.shape[0] and c < frame.shape[1]]
        if not inside:
            return
        # Threshold LOCAL to the aperture, so a bright or dark scene delivers
        # the same duty cycle: the arms differ in pattern, never in quantity.
        thr = float(np.median([float(frame[r, c]) for (r, c) in inside]))
        for (r, c) in inside:
            if float(frame[r, c]) > thr:
                self.s.set_attr(self.cells[(r, c)], "driven", 1.0)

    def _drive_phase(self) -> None:
        """Drive the `ch_*` rules to a fixed point, and NOTHING else.

        Mechanical phase dispatch — the `domains/language.py` precedent verbatim
        ("apply_rule_once, so only THIS phase's rules fire (run_rules would also
        fire ...)"). `run_rules()` here would advance the WAVE rules an extra
        time per step and destroy every committed result; `tick()` is called once
        at the end of `step()` and is a step too late for `_mark_bursts`. So the
        drive rules, and only they, are run here.

        No conditional over graph state: the rules' own guards decide everything
        (`change < 0.5` selects the median split, `> 0.5` the change channels).
        At the default this loop still runs — and `ch_drive_median` reproduces
        the old behaviour exactly, which is what makes §9 hold.

        `apply_rule_batch`, NOT `apply_rule_once` (VISION_BATCH_APPLY_PREREG.md).
        `apply_rule_once` applies ONE binding per Python→Rust entry, so driving
        M bindings to a fixed point costs M full re-derivations of the binding
        set: the scale split measured 217,213 entries at 4096 cells against an
        irreducible floor of 100, i.e. 99.81% of ALL candidate enumeration on
        this path. `apply_rule_batch` hands off to the engine's existing
        `batch_apply_rule` for any rule whose graph data sets `batch`, and is
        `apply_rule_once` verbatim for any rule that does not — so this is still
        one mechanical line with no conditional over graph state. WHICH rules
        batch is decided by the seed, not here.

        THE `while` IS KEPT DELIBERATELY. A batch pass costs one extra, empty
        quiescence pass per firing rule, so the achievable floor is ~2× the
        one-pass floor rather than 1×. That residual is a property of "loop
        until no progress", not of batching, and it was registered as such
        BEFORE measurement. Dropping the `while` would assume no batch pass can
        ever enable a new binding — true for these five rules by their phase
        guards, but an assumption this adapter has no business making on behalf
        of rules it does not read."""
        nat = self.s._inner if hasattr(self.s, "_inner") else self.s
        for idx in self._drive_rules:
            while nat.apply_rule_batch(idx):
                pass

    # ---- (3) CLOCK -------------------------------------------------------
    def step(self, *, ignite_k: int = 0, frame: Optional[np.ndarray] = None) -> int:
        """Advance the world one step: optionally inject entropy, let the rules
        run to fixpoint, then COMMIT recruited cells to active. The commit is
        mechanical double-buffering (a recruited cell becomes active for the
        NEXT step) so a wave advances one hop per step instead of the fixpoint
        racing it across the whole grid in one go — the temporal structure is
        the point, and without this there would be none to learn from."""
        st = float(self.s.node(self.retina)["attrs"]["step"]) + 1.0
        self.s.set_attr(self.retina, "step", st)
        # COMMIT last step's recruits: they become FRESH actives for this step
        # (activated_at == st), so they propagate one hop now while the cells
        # that recruited them (activated_at == st-1) are stale and refract.
        # This double-buffering is what makes the wave advance ONE hop per
        # step instead of the fixpoint racing it across the grid instantly.
        # BULK: one read of all N states, then two uniform writes over the
        # recruited SUBSET. The per-node interleaving (state,activated_at per
        # cell) becomes (all states, then all activated_at) — the writes touch
        # DISTINCT (node, key) pairs and no rule runs between them (`tick` is
        # below), so the resulting graph is identical.
        states = self.s.get_attr_many(self._cell_ids, "state")
        recruited = [n for n, stt in zip(self._cell_ids, states) if stt == "recruited"]
        if recruited:
            self.s.set_attr_many(recruited, "state", "active")
            self.s.set_attr_many(recruited, "activated_at", st)
        # per-frame channel, not a state
        self.s.set_attr_many(self._cell_ids, "driven", 0.0)
        if ignite_k:
            self.ignite(ignite_k)
        self.drive(frame)
        self._mark_bursts(st)
        self.s.set_attr_many(self.s.nodes("Unit"), "bursting", 0.0)
        # PROTOCOL §11.4 opt-in: the §2/8D confirmatory run needs the settling
        # dither to TERMINATE (cycle detection). OFF by default — the attribute
        # is unset, so `getattr(self,"detect_cycles",False)` is False and this is
        # byte-identical to `tick(200_000)` (§9, verified: DEFAULT ≡ explicit-OFF,
        # max|Δact|=max|Δw|=0.0). A caller sets `w.detect_cycles = True` to opt in.
        # PROTOCOL §9 opt-in (block 134000, the `detect_cycles`/`bulk_ingest`
        # precedent): DEFAULT OFF. When `stencil_fast` is set, try the engine's
        # admissible vectorized stencil fast path INSTEAD of the per-cell wave
        # relaxation. `wave_stencil_tick` returns True iff the RetinaCell
        # dynamics ARE the recognised uniform local stencil (structural
        # admissibility read from the graph) and it applied them vectorized; if
        # it returns False (a non-stencil rule set — e.g. learners present), the
        # caller falls back to the committed `tick`. The routing DECISION lives
        # in Rust; this is one mechanical branch. Byte-identical (§9), gated by
        # `tests/test_stencil_simd_migrated.py`.
        if getattr(self, "stencil_fast", False) and self.s.wave_stencil_tick(
                200_000, getattr(self, "stencil_run_rest", True)):
            return int(st)
        self.s.tick(200_000, detect_cycles=getattr(self, "detect_cycles", False))
        return int(st)

    def _mark_bursts(self, st: float) -> None:
        """`bursting` mirrors `active` this step, and `last_burst` records WHEN
        it last did. Both mechanical: a cell that fires IS bursting, and the
        time it fired is an observed fact, not a decision — the DECISION (does
        this latency potentiate or depress?) is bh_potentiate/bh_depress
        reading Minus(step, last_burst) against WaveParams.window_steps.

        Written here rather than by a tracking RULE on purpose: a rule setting
        last_burst would race the rules reading it inside the same fixpoint (a
        coincident burst would potentiate or depress depending on firing
        order). Recording the fact in the adapter makes the latency
        unambiguous before any rule reads it — the same reason the recruit
        commit is double-buffered here."""
        # BULK: 2 reads (3 with rung 3's prev_burst) instead of N dict
        # materialisations, then uniform writes over the on/off SUBSETS. Same
        # (node, key) pairs, same values, distinct keys per pair, no rule
        # between — the graph lands identical.
        states = self.s.get_attr_many(self._cell_ids, "state")
        drivens = self.s.get_attr_many(self._cell_ids, "driven")
        on_cells, off_cells = [], []
        for n, stt, dr in zip(self._cell_ids, states, drivens):
            # TWO PATHWAYS, ONE OUTPUT: a cell bursts if the wave network made
            # it active OR visual input drove it. Only the wave path carries
            # `state == "active"`, so only the wave path propagates — a
            # visually-driven RGC fires without launching a travelling wave.
            (on_cells if (stt == "active") or (dr == 1.0) else off_cells).append(n)
        self.s.set_attr_many(on_cells, "bursting", 1.0)
        self.s.set_attr_many(off_cells, "bursting", 0.0)
        if self.track_prev_burst:
            # RUNG 3: carry the PREVIOUS last_burst forward before it is
            # overwritten. Pure bookkeeping of an observed fact — the
            # dv_transient RULE decides what an onset is from it.
            # NOTE: the VALUE differs per cell, so this stays a per-node write —
            # `set_attr_many` is uniform-value by construction. Default OFF, so
            # the hot path (rungs 1/2) does not pay it; rung 3 still does.
            lasts = self.s.get_attr_many(self._cell_ids, "last_burst")
            for n, lb in zip(self._cell_ids, lasts):
                self.s.set_attr(n, "prev_burst",
                                float(lb if lb is not None else -999.0))
        self.s.set_attr_many(on_cells, "last_burst", st)

    # ---- wiring the learners (mechanical geometry, no decisions) ---------
    def add_units(self, n_units: int, *, rf: int = 7, w0: float = 1.0,
                  jitter: float = 0.05, centres: Optional[list] = None,
                  init: str = "multiplicative") -> list:
        """Mint `n_units` Units, each fully connected to a centred `rf` x `rf`
        patch of the retina by `Synapse` nodes. Positional wiring only — which
        cells a unit can see is geometry (the same kind of fact as
        VisionWorld's window slicing).

        THE INITIAL WEIGHTS ARE NOT NEUTRAL, AND THIS PARAMETER IS THE ABLATION
        THAT SAYS SO (2026-07-17, `W0_ABLATION.md`). The committed default —
        `init="multiplicative"`, `w = max(w0*(1 + jitter*N(0,1)), 1e-3)` with
        `w0=1.0, jitter=0.05` — is a **494:1 DC prior**: every weight is
        strictly positive and the RF's power is 99.8% in its constant
        component. The old comment here said "NOT structure, just a tie-break".
        That was FALSE as written: a tie-break needs only the jitter, and the
        `w0` offset is a large structural prior on exactly the mode
        (`frac(w<0)=0`, DC-dominated response) that rung 5 named as its own
        root cause.

        `init="zero_mean"` is the ablation: `w = w0 + jitter*N(0,1)` with NO
        positivity clamp, so `w0=0.0` gives a genuinely zero-mean, signed,
        DC-free initial RF. The RNG draw sequence is IDENTICAL between the two
        modes (one `normal()` per synapse), so the arms differ in the initial
        weights and in nothing else.

        DEFAULT PRESERVES EVERY COMMITTED RESULT. `init="multiplicative"` is
        the committed expression, character for character; rungs 1/2/4/5/6 all
        ran through it and reproduce byte-identically (verified —
        `tests/test_w0_init_ablation_migrated.py`).

        `centres`: an OPTIONAL list of `n_units` (cy, cx) RF centres. Default
        None => centres are drawn from the adapter's RNG exactly as before, so
        every committed result reproduces byte-identically. RUNG 4 supplies
        RETINOTOPIC centres (see `domains/cortex_sheet.py`): where a unit looks
        is positional geometry, the same kind of mechanical fact as the retina's
        own grid — never a decision."""
        units = []
        half = rf // 2
        for i in range(n_units):
            if centres is None:
                cy = half + int(self.rng.integers(0, max(1, self.h - rf + 1)))
                cx = half + int(self.rng.integers(0, max(1, self.w - rf + 1)))
            else:
                cy, cx = int(centres[i][0]), int(centres[i][1])
            u = self.s.add_node("Unit", {"name": f"u{i}", "act": 0.0,
                                         "bursting": 0.0, "act_step": -1.0,
                                         "burst_step": -1.0,
                                         "wsum": 0.0, "wsum_step": -1.0, "last_burst": -999.0,
                                         "theta": 1.0, "theta_step": -1.0,
                                         "cy": float(cy), "cx": float(cx),
                                         "rf": float(rf)})
            _add_edge(self.s, self.retina, "has_unit", u)
            for dr in range(-half, half + 1):
                for dc in range(-half, half + 1):
                    cell = self.cells.get((cy + dr, cx + dc))
                    if cell is None:
                        continue
                    g = float(self.rng.normal())
                    if init == "zero_mean":
                        w = float(w0 + jitter * g)      # signed, NO clamp
                    else:
                        w = max(float(w0 * (1.0 + jitter * g)), 1e-3)
                    syn = self.s.add_node("Synapse", {
                        "weight": w, "touched": -1.0,
                        "scaled_step": -1.0,
                        "drow": float(dr), "dcol": float(dc)})
                    _add_edge(self.s, cell, "pre", syn)
                    _add_edge(self.s, syn, "post", u)
            units.append(u)
        return units

    def receptive_field(self, u) -> np.ndarray:
        """Read a Unit's receptive field back out of the graph: the synapse
        weights laid out by their (drow, dcol) offsets. Pure query."""
        rf = int(self.s.node(u)["attrs"]["rf"])
        half = rf // 2
        a = np.zeros((rf, rf), np.float32)
        for syn in self.s.in_neighbours(u, "post"):
            at = self.s.node(syn)["attrs"]
            a[int(at["drow"]) + half, int(at["dcol"]) + half] = float(at["weight"])
        return a

    # ---- REPLAY: drive learning from a recorded activity movie ------------
    def replay_step(self, frame: np.ndarray) -> int:
        """Advance one step with the retina's activity SET DIRECTLY from a
        recorded frame, bypassing the wave state machine. Mechanical.

        This exists for the temporal-shuffle control: replaying the SAME set of
        frames in a different ORDER holds the per-frame spatial statistics
        exactly constant and varies only time. Anything the learning rules do
        differently between the two orders is attributable to temporal
        structure and nothing else."""
        st = float(self.s.node(self.retina)["attrs"]["step"]) + 1.0
        self.s.set_attr(self.retina, "step", st)
        on_cells, off_cells = [], []
        for (r, c), n in zip(self._cell_rc, self._cell_ids):
            v = float(frame[r, c]) if (r < frame.shape[0] and c < frame.shape[1]) else 0.0
            (on_cells if v > 0.5 else off_cells).append(n)
        self.s.set_attr_many(on_cells, "bursting", 1.0)
        self.s.set_attr_many(off_cells, "bursting", 0.0)
        # the latency the rules read
        self.s.set_attr_many(on_cells, "last_burst", st)
        self.s.set_attr_many(self.s.nodes("Unit"), "bursting", 0.0)
        self.s.tick(200_000)
        return int(st)

    # ---- READ-OUT (pure query) -------------------------------------------
    def frame(self) -> np.ndarray:
        """The current activity frame — 1.0 where a cell is active."""
        a = np.zeros((self.h, self.w), np.float32)
        states = self.s.get_attr_many(self._cell_ids, "state")
        for (r, c), stt in zip(self._cell_rc, states):
            if stt == "active":
                a[r, c] = 1.0
        return a

    def set_bursting_from_frame(self) -> None:
        """Mark every active cell as bursting (mechanical: bursting IS being
        active this step). The learning rules read `bursting`."""
        states = self.s.get_attr_many(self._cell_ids, "state")
        on = [n for n, stt in zip(self._cell_ids, states) if stt == "active"]
        off = [n for n, stt in zip(self._cell_ids, states) if stt != "active"]
        self.s.set_attr_many(on, "bursting", 1.0)
        self.s.set_attr_many(off, "bursting", 0.0)


def record(world: WaveWorld, *, steps: int, ignite_k: int = 1,
           ignite_every: int = 6) -> np.ndarray:
    """Run the world and return the activity movie (steps, h, w). Mechanical."""
    out = []
    for i in range(steps):
        k = ignite_k if (ignite_every and i % ignite_every == 0) else 0
        world.step(ignite_k=k)
        out.append(world.frame())
    return np.stack(out)


__all__ = ["WaveWorld", "record"]
