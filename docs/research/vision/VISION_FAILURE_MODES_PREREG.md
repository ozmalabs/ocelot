# Replicating KNOWN FAILURE MODES — pre-registration

*Written and committed BEFORE any run (PROTOCOL §3). Engine, commit and seed block
recorded below. The creator's framing: "Can we replicate known failure modes? **That is
the real tell.**" Normal function is cheap to fake; pathology is specific.*

**Engine:** `6fcc99edfa4a` @
`.claude/worktrees/agent-failure-modes/.../runners/dsl/python/substrate_rs/_native.abi3.so`
— **own** build of this tree's Rust source (`scripts/engine_build.sh`).
**Why a fresh build:** the canonical engine `95167c01b7b3` **fails the provenance gate as
STALE** (12 `.rs` newer than the binary; canonical also carries an untracked
`py.rs.selfmod.bak`, i.e. something wrote `py.rs`). Tracked `.rs` content is clean vs git
and byte-identical to this tree's, so this is an mtime/rebuild hazard, not a divergence —
but §10 forbids attributing numbers to a binary that may not be a build of the source
they are attributed to. **Baseline reproduces on the fresh engine:**
`tests/test_vision_eye_migrated.py tests/test_vision_calibration_migrated.py` → **27
passed**.

**Commit at pre-registration:** `c20816fd32` (branch `vision/failure-modes`).

**Seed block: 14000–14999** — taken from the ledger's FREE list, declared here in
advance. Calibration/audit uses already-burned 0–2.

---

## FM-0. THE VACUITY GATE — can `saw` reach the receptor sheet at all?

**This gate runs FIRST and it can stop the whole line of work.** Precedent:
`VISION_PREVISUAL_PREREG.md` §3, where H3's double dissociation was found vacuous in both
halves (0 rules read both paths; all four cells equalled their null arm exactly). Rung 8's
§1 gate is the other precedent: a blind probe makes every arm uninterpretable.

The proposed Troxler test is: **freeze the drift (`saw=0`) ⇒ the response decays; with
drift (`saw=1`) it does not.** That test presupposes that the drift MOVES THE IMAGE ON THE
RECEPTORS. Before burning a single confirmatory seed, prove that it can.

### What I already know from reading the source (stated in advance, to be measured)

Structural, and enumerated positively rather than by a soft accessor (§12):

1. **Zero of the 23 rules in `seeds/vision_eye.json` read both a `GazeCell` and an
   `EyeCell`.** The rules partition by `match_type`: `EyeCell` (`ey_receptor_*`, `ey_xbar`,
   `ey_adapt_theta`, `ey_response`), `GazeCell` (`ey_saw_*`), `EyeUnit`, `WUnit`,
   `EySynapse`, `WSynapse`.
2. **No production admits ANY edge between the Gaze subsystem and the Eye subsystem.**
   The 11 productions give `Gaze -has_gazecell-> GazeCell`, `Gaze -gaze_at-> GazeCell`,
   `GazeCell -gaze_neighbour-> GazeCell`, and separately `Eye -has_eyecell-> EyeCell`.
   There is no `Gaze`↔`EyeCell` production, so such an edge is **inadmissible** — Γ would
   reject it.
3. **`eye_world.present()` writes `frame[r, c]` onto cell `(r, c)` and never calls
   `gaze_pos()`.**
4. **`gaze_pos()`'s only consumers in the entire tree are `eye_world.walk()`** (the
   trajectory recorder, lines 427/430) **and one assertion in
   `tests/test_vision_eye_migrated.py`.** The walk's sole consumer is the ruler that
   measures the walk.

Point 4 is the same shape as rung 7's finding that `wv_propagate` was the `neighbour`
edges' sole consumer in the whole tree — stated here so it is on record as a prediction,
not a post-hoc reading.

### Hypothesis (two-sided)

**H0-vac:** the value of `saw` has NO effect on any `EyeCell` attribute (`lum`, `x`,
`theta`, `resp`, `xbar`) at any step.

### The statistic

Run the eye with `eye=1` on a fixed static frame for 400 steps, twice: `saw=1` and
`saw=0`, **identical seed, identical frame**. Record per step:

- `D_resp(t) = max_cells |resp_saw1(t) − resp_saw0(t)|`
- `D_theta(t)`, `D_x(t)`, `D_lum(t)` likewise.

Report `max_t` of each. Also record the gaze trajectory in both arms (positive control on
the manipulation: `saw=1` must MOVE and `saw=0` must NOT — if the gaze doesn't move in the
`saw=1` arm, the manipulation is inert and the audit says nothing).

### Decision rule

- **All `D_* == 0.0` exactly, AND the `saw=1` gaze demonstrably moves while `saw=0`'s does
  not** ⇒ **the manipulation is live but cannot reach the measure** ⇒ the Troxler test as
  specified is **VACUOUS**. **STOP. Burn no confirmatory seed.** Report the drift as
  DECORATIVE with respect to the receptor sheet, and name the wiring as the next rung's
  work with its own pre-registration.
- **Any `D_* > 0`** ⇒ there is a coupling I did not find by reading ⇒ the audit is
  informative and FM-1/FM-2 proceed.
- **The gaze does not move in the `saw=1` arm** ⇒ inert manipulation ⇒ the audit is
  uninterpretable; fix the arm before concluding anything (the inert-instrument rule).

**What a null means here:** a null (`D=0`) is NOT "no effect of drift on vision". It is
"**this architecture cannot express an effect of drift on vision**" — a structural fact
about the model, which is a stronger and more useful statement than any p-value, and it is
knowable without burning seeds.

### Prediction, with provisos

**I predict `D_* == 0.0` exactly for every attribute at every step, and that the gaze
moves in `saw=1` and not in `saw=0`.** Confidence: high (points 1–4 are structural).

Provisos — each, if it breaks, tells me what I did not understand:

1. *If the `saw=1` gaze does NOT move* — then `ey_saw_move` is gated off by something
   beyond `eye`/`saw` and my reading of the gating is wrong.
2. *If `D_resp > 0` while `D_lum == 0`* — then some rule reads gaze state into the EyeCell
   path without an edge (e.g. a `Pick`/`NodesOfType` global read, which needs no
   production and which my edge-based enumeration would MISS). This is the most likely way
   I am wrong, because `NodesOfType` bypasses the admissibility argument entirely.
3. *If `D_lum > 0`* — then the adapter couples them somewhere I did not grep.

Proviso 2 is the real risk to my reasoning and is why this audit is empirical rather than
a code-reading assertion.

---

## FM-1. THE FADE PRECONDITION — does a static image fade AT ALL?

**Independent of drift, and therefore measurable today regardless of FM-0's outcome.**
Note the consequence of FM-0's structure: **this eye is ALWAYS stabilized** — the image
never moves on the receptors, whatever the gaze does. So the model is permanently in the
condition Ditchburn & Ginsborg 1952 / Riggs & Ratliff 1952 created artificially.

### Hypothesis (two-sided)

**H1:** with a static frame and `eye=1`, the spatial structure of the response either
decays toward uniformity (FADE) or it does not.

### The statistic

- **`contrast(t) = SD` across cells of `resp(t)`** — the response's spatial structure.
- **`fidelity(t) = Pearson r(resp(t), x(t))`** across cells — "can the image still be read
  out of the response?"

Fit a decay time constant τ to `contrast(t)` if it decays. Report `contrast(0)`,
`contrast(400)`, and the ratio.

### §1 calibration triple — floors MEASURED IN-RUN, never inherited

The arc's own instrument defect (`W0_ABLATION.md`): the OSI floor is init-dependent,
0.0044 vs 0.3899, 89× on the identical probe. **No floor is inherited here.**

1. **Floor on random input:** present i.i.d. uniform noise ⇒ `fidelity` must be at the
   floor for a *structured-image* readout, and I measure that floor rather than assuming
   it is 0.
2. **Ideal exemplar:** at `t=0`, before any adaptation, `fidelity` must be HIGH
   (`resp = max(x − theta, 0)` with `theta` at init ⇒ `r ≈ 1`). **This is the positive
   control on the READER: it proves the probe can SEE the image when it IS there.** A fade
   is an ABSENCE claim, and an absence measured off a probe that never saw anything is the
   trap that has caught this arc six times.
3. **Duration:** report the full `contrast(t)` curve, not an endpoint, so the reader can
   see whether it settles (§2) or is measured mid-transient.

### Decision rule

- **`contrast` decays ≥10× toward 0 with a finite τ, AND the t=0 positive control shows
  `fidelity ≈ 1`** ⇒ the model FADES under stabilization — half of the Troxler result,
  present today, in a system where nothing was designed toward it.
- **`contrast` flat** ⇒ NO fading mechanism ⇒ Troxler is unreachable in this model
  regardless of any wiring, and that is a clean negative that kills the line.
- **`fidelity(0)` NOT high** ⇒ the probe is blind ⇒ report nothing else; fix the probe
  (rung 8's failure mode).

### Prediction, with provisos

**I predict a FADE:** `ey_adapt_theta` drives each cell's mean output to `mu = 0.024`
**independently per cell**, so every cell's `resp` converges to the same 0.024 regardless
of its `lum` ⇒ the spatial pattern collapses to uniform ⇒ `contrast → ~0`,
`fidelity → undefined/0`. Predicted τ on the order of the EMA timescale,
`1/(1−beta) = 1/0.009 ≈ 111` steps, with `lam = 0.01` (θ's rate) a comparable ~100 steps —
so **τ ≈ 100–200 steps**, and I predict `contrast(400)/contrast(0) < 0.1`.

Provisos:

1. *If contrast plateaus well above 0* — then θ's homeostasis is weaker than mu-targeting
   implies (e.g. `lam` too small to converge in 400 steps, or a rectification floor at
   `resp=0` pinning cells). **This would make τ the finding, not the fade.**
2. *If cells pin at `resp = 0` rather than at `mu`* — then the fade is rectification, not
   homeostasis, and the mechanism I am claiming is wrong even though the direction is
   right. **I must check WHERE the cells land (at `mu`? at 0?), not just that contrast
   fell.** Distinguishing these is the difference between understanding and pattern-
   matching.
3. *If `fidelity` stays high while `contrast` falls* — the image is being scaled down, not
   erased; that is a gain change, NOT fading, and I must not report it as fading.

Proviso 3 is why BOTH statistics are pre-registered: a fade must lose the *pattern*, not
merely the *amplitude*.

---

## FM-2. MACH BANDS / SIMULTANEOUS CONTRAST on rung 7's EMERGED centre-surround

**Deferred pending the literature review and FM-0/FM-1 outcomes.** Rung 7 earned a
centre-surround from a zero init (`CS = 1.0839`, `lat_g0 = 0.0`), which is the right
substrate for a lateral-inhibition epiphenomenon. Any test here will be pre-registered in
its own section BEFORE running, with its own §1 triple and its own floor measured in-run.

**Recorded in advance on the Hermann grid:** the classic lateral-inhibition account is
**contested** — it fails for wavy grids (Geier et al.) and Schiller & Carvey 2005
re-attributes it. If the grid is tested at all, it will be tested against what the
research actually licenses, and the contested status reported (§8). **A model reproducing
the Hermann grid via lateral inhibition would be reproducing a FOLK explanation, and that
is worth less, not more.**

---

## STRUCTURALLY OUT OF SCOPE — stated, not faked

- **Amblyopia / ocular dominance shift / strabismus / Hubel & Wiesel monocular
  deprivation.** These need **TWO EYES**. This model has one (`Eye`, one receptor sheet).
  Ocular dominance is a competition BETWEEN eyes for cortical territory; with one eye
  there is no competition and no dominance to shift. **Not attemptable. Not attempted.**
  Whether a second eye is worth building is reported as a finding, not bodged.
- **Blakemore & Cooper stripe-rearing.** Needs working cortical orientation selectivity.
  Rungs 5/6/8 establish there is none (rung 8: an IDEAL split-Gabor scores 0.1290 on the
  composed pathway — the probe is blind). **A failure mode measured on a blind probe is
  not a result.** Not attempted.

---

## The pattern to be tested as a CLAIM, not assumed

The supervisor's hypothesis: *the failure modes we CAN test map onto the parts that work;
the ones we cannot map onto the parts that do not.* If that holds it is independent
evidence the working/broken boundary is real rather than an artifact of our measures.

**FM-0 is the first test of that claim and it may well FALSIFY it** — the eye's drift is
one of the parts that "works" (α_short 1.1553 > 1 > α_long 0.7590, matching Engbert's
0.79±0.11), yet if FM-0 returns `D = 0` then **a failure mode of a WORKING part is
structurally untestable**. That would mean "works" and "is load-bearing" are different
properties, and the pattern as stated is false. I record this before running.
