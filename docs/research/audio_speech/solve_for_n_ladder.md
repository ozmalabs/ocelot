# solve-for-n diagnostic ladder — three harder rungs

The general solve-for-n engine (`scripts/solve_for_n.py`, domain-agnostic
analysis-by-synthesis: matching-pursuit-to-order-N + joint back-fitting +
weighted-admissibility collapse) passed rung one (sinusoids — super-resolved
the FFT 3.3x, commit 6af64af7). This skips several rungs and probes it on
THREE qualitatively-harder WELL-UNDERSTOOD domains at once, by swapping **only
the forward-model plug-in**. The engine is reused **unchanged**; the only new
code is `scripts/solve_for_n_ladder.py` (three plug-ins + ground-truth
harnesses).

The breaks, with their exact ground-truth diagnosis, are the deliverable.

## Run

```
python -m scripts.solve_for_n_ladder        # full
python -m scripts.solve_for_n_ladder --quick
```

Captured to `/tmp/ladder_full.log`, end marker `SOLVE_FOR_N_LADDER_COMPLETED`,
elapsed 62s, pgrep-verified completed (exit 0). All numbers below are real.

## Donkey audit

- **Forward models = owned EXACT generative numpy.** Kepler orbit (Kepler's
  equation solved by Newton on the eccentric anomaly); elementary CA rule table;
  gated-sinusoid (raised-cosine burst) synthesis. Ground truth constructed, so
  every recovery error is exact.
- **Engine = the existing general one, imported unchanged**
  (`from scripts.solve_for_n import solve_for_n`).
- NO net, NO `.fit()`, NO gradient-descent training. Refinement is bounded local
  coordinate polish against the exact forward model (golden-section / closed-form
  LSQ). For the discrete rung, an explicit small **discrete** search — flagged as
  the interface gap, not the engine's continuous calculus.
- CortexLoop untouched.

---

## RUNG 1 — NON-LINEAR PHYSICS (2-body Kepler orbit) → CLEARS w/ a diagnosable local-minimum

**System.** A test particle on a bound Kepler ellipse. The "signal" is the
flattened trajectory `[x(t); y(t)]`. One non-linear component (n=1); the param
is the 5 orbital elements `(a, e, omega, M0, n_mean)`. The forward model is
exact (Newton on `M = E − e sin E`). Tests the continuous golden-section/LSQ
search on a non-linear, local-minima landscape.

**Result (30 trials).**

| metric | value |
|---|---|
| recovery rate (a, e, n all < 2%) | **70.0%** |
| median \|a\| rel err | 2.8e-05 |
| median \|e\| abs err | 1.2e-05 |
| median \|n\| (period) rel err | 5.6e-05 |
| median trajectory RMSE | 3.6e-04 |
| p95 trajectory RMSE | 4.0e-01 |

**Break diagnosis (exact, from ground truth).** The 30% that fail are **not
random** — every single failure is a **low-eccentricity** orbit (failing
e ∈ [0.04, 0.25], median ≈0.13; succeeding median e=0.36). In every failure
`a` and the period `n_mean` are recovered to ~0.1–1.5%, but `e` collapses
toward 0 (the engine fits a near-circle). The mechanism, confirmed directly:

- `propose` reads the orbit orientation from the **PCA principal axis** of the
  point cloud. For a near-circular orbit the cloud is nearly isotropic, so the
  principal axis is dominated by the time-sampling sweep, not the (barely
  elliptical) shape → `omega` and `M0` start in the **wrong basin**
  (measured: proposed omega=1.73 vs true 0.50; M0=−1.09 vs 0.30).
- The elements `e`, `omega`, `M0` are **coupled** through the orbit rotation.
  Holding the wrong `omega/M0` and pushing `e` toward truth makes the fit
  *worse* (err 6.18 → 7.14), so one-axis-at-a-time golden-section is trapped:
  it is a **genuine joint local minimum**, not a flat dimension (the `e`-axis
  alone is well-curved and convex when the others are at truth: err 12.7 → 0 →
  12.8). The coordinate search cannot make the correlated multi-element jump
  needed to reach the global basin.

This is exactly the predicted non-linear local minimum. **The next fix** is a
better proposal for the degenerate regime (e.g. read periapsis from the
trajectory's max-speed point / closest approach instead of PCA) and/or a joint
multi-element step (Levenberg–Marquardt over all 5 elements) replacing pure
coordinate descent — both are engine-level, not plug-in.

---

## RUNG 2 — DISCRETE / SYMBOLIC (elementary cellular automaton) → BREAKS (as predicted); minimal discrete extension CLEARS

**System.** A width-21 elementary CA, 24 rows. The "signal" is the flattened
space-time pattern; the param is `(rule ∈ 0..255, init bits)`. The forward model
is exact (the 8-entry rule table). NO smooth gradient — the continuous
`refine_component` is meaningless on an integer rule index.

**Result (40 trials).**

| plug-in | rule recovery | pattern recovery |
|---|---|---|
| **continuous engine, as-is** (`ECAModelContinuous`) | **0.0%** | 0.0% |
| **discrete extension** (`ECAModelDiscrete`) | **97.5%** | **100.0%** |

**Break diagnosis (exact).** The continuous engine **cannot search the discrete
space at all** — the failure is total and clean, exactly as the ground truth
predicts:

- `refine_component` is the continuous calculus (golden-section / LSQ). On an
  integer rule index it is a **no-op** — there is no gradient and no neighbourhood
  to polish. So the engine keeps whatever `propose` returned.
- `propose` can read the init off the first row (it is directly visible) but the
  **rule is latent** — it is not a peak in any spectrum, so there is nothing to
  read off. The proposal returns rule 0; the no-op refine leaves it there →
  0% rule recovery. The matching-pursuit menu over a continuous read-off proposes
  garbage in a discrete space.

This is the predicted break: *"discrete — continuous refinement is a no-op,
matching-pursuit proposes garbage."*

**The minimal interface extension the lack demands** (cheap, so included as the
fix-demonstration): `ECAModelDiscrete.refine_component` does an explicit
**discrete search** — exhaustively pick the rule (256 options) at the observed
init, then greedy bit-flips on the init. Same `synthesise/merge/propose`
contract; only the calculus is discrete. It recovers 97.5% of rules and 100% of
patterns exactly (err 0). (The ~2.5% rule miss is the genuine ambiguity where a
small init never exercises some neighbourhood, so two rules produce the
identical observed pattern — a ground-truth identifiability limit, not an engine
failure.)

**Diagnosis for the engine:** the engine's `refine_component` contract assumes a
**continuous local polish**. A domain with no gradient needs a **discrete-search
refinement** primitive in the interface (the engine's collapse/matching-pursuit
scaffold is fine — it is the polish step that must branch on domain type). The
next fix is to make the refinement strategy a property the plug-in declares
(continuous vs discrete-search), not a hardcoded golden-section.

---

## RUNG 3 — COMPOSITIONAL (notes-in-a-melody) → peels components but does NOT compose (the crux break)

**System.** A melody of 2–4 notes. Each note is a **sinusoid burst**: one pitch,
gated by a raised-cosine window of some duration at some onset. The "signal" is
the waveform. The param is the **nested** structure
`note → (A, pitch, onset, dur)`. The forward model is exact. One component =
one note. This is the speech-relevant rung: recover not just partials but the
GROUPING into notes.

**Result (24 trials, engine free to choose n up to 8).**

| metric | value |
|---|---|
| note recovery rate (a matching component per true note) | **100.0%** |
| median pitch rel err | 1.7e-02 |
| median onset rel err | 4.9e-03 |
| **mean components used** | **8.00** |
| mean true notes | 3.04 |
| **mean spurious components** | **4.96** |
| median fit RMSE | 2.2e-01 |

**Break diagnosis (exact, the crux).** The engine **peels every note** (100%
recovery — for each true note there is a component near its pitch+onset) **but
does NOT recover the nested structure** — it returns a **flat over-complete bag**,
not the note hierarchy:

- It uses **8 components for ~3 notes** (hits the `max_n` ceiling every time) with
  **~5 spurious components** per melody. The reason is structural and exact: a
  **gated** tone is NOT a single global damped sinusoid — a finite raised-cosine
  burst has spectral side-lobes and the matching-pursuit residual after peeling
  one note still carries energy at the same pitch (the gate edges), so the engine
  peels **multiple components per note** plus side-lobe artefacts. The residual
  never falls below the auto-stop, so it peels to the ceiling.
- There is **no grouping / compose operator** in the engine. Matching pursuit +
  back-fitting produce a flat list ordered by energy; nothing collapses "these
  three components at the same onset and pitch are ONE note", and nothing
  represents the rhythm grid (the composition). The fit RMSE stays at 0.22
  (not driven to 0) precisely because the bag is an approximation of a structure
  the model can represent exactly but the engine can't assemble.

This is the predicted crux: *"compositional — peels low-level components but
can't group them into the hierarchy."* The components ARE there (recovery is
100%); what's missing is the **nesting**.

**The next fix (the speech-relevant one).** The engine needs a second,
**compositional** level: after peeling the flat component bag, a GROUP/COMPOSE
step that (a) clusters components sharing onset+pitch into one note, (b) fits the
note's gate as a unit, and (c) represents the rhythm grid as the parent
structure. I.e. solve-for-n must become **recursive/hierarchical** — solve-for-n
over notes, where each note is itself a (gated) solve-for-n over partials. That
recursion is exactly the structure continuous speech needs (utterance → words →
phones → source-filter), and this rung isolates that it is the **missing
mechanism**, not a tuning problem.

---

## VERDICT

| rung | result | exact failure mode = the next fix |
|---|---|---|
| **1 — non-linear physics** | **CLEARS** (70%; perfect when e≳0.3) | Local minimum on the non-linear landscape **only for near-circular orbits**: PCA proposal mis-orients `omega/M0` and coupled coordinate-descent is trapped. Fix = degenerate-regime proposal + joint multi-element (LM) step. Engine-level. |
| **2 — discrete / symbolic** | **BREAKS** (0% as-is) | Continuous `refine_component` is a **no-op** on a rule index; `propose` reads garbage for the latent rule. Fix = a **discrete-search** refinement strategy in the interface (demonstrated: `ECAModelDiscrete` → 97.5% / 100%). |
| **3 — compositional** | **PEELS, doesn't COMPOSE** (100% note recovery, 8 comps for 3 notes, ~5 spurious) | No **grouping/compose** operator: returns a flat over-complete bag, shatters each gated note into several components + side-lobes. Fix = make solve-for-n **recursive/hierarchical** (notes-of-partials). This is the speech rung. |

**Honest summary.** Physics is the only clean pass, and even it has a precise,
ground-truth-diagnosed local-minimum failure on the degenerate (circular) regime.
Discrete and compositional **break as predicted**, and the breaks are exactly
located:

- discrete needs a **discrete-search refinement primitive** (the continuous
  polish is a no-op) — cheaply demonstrated to fix it;
- compositional needs a **recursive compose/group level** (matching pursuit peels
  components but the engine has no operator to nest them into the hierarchy) —
  the single missing mechanism the continuous-speech kill was really about.

The two engine-level gaps (a refinement-strategy abstraction; a recursive
compose level) are the next fixes; the physics local-minimum is a
proposal/step-direction fix. None were forced into a fake pass.
