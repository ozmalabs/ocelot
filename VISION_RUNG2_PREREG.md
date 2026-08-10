# Pre-registration — does foveated experience refine the wave-built scaffold?

*Written 2026-07-16, BEFORE the confirmatory run. Fixed in advance.*

## Background

Rung 1's `waves+video` arm **failed** biology: it came out significantly WORSE than
`waves` alone (−0.090, p=0.002), when dark-rearing vs normal-rearing says normal
rearing should **match or beat** dark rearing (waves continue in the dark; White,
Coppola & Fitzpatrick 2001). Diagnosis: `WaveWorld.drive` median-split the WHOLE
field, driving ~50% of the retina every step — a high-duty-cycle blast that swamped
the ~7% wave activity and behaved as a *degraded pattern*, landing between waves and
noise.

**The fix under test:** a FOVEAL APERTURE with saccadic relocation (radius 3 ⇒ ~11% of
the field; local median threshold inside the aperture). Measured duty cycle: waves
alone 6.2%, +video 9.3%, +noise 9.6% — experience now *modulates* the scaffold instead
of drowning it, and the two experience arms deliver near-identical drive QUANTITY so
they differ only in pattern STRUCTURE. No edge detection / whitening / contrast
normalisation is applied (that would hand-build the retina — the `preprocess_patches`
mistake). Saccade targets come from the adapter's RNG (positional entropy, like wave
ignition); curiosity-driven gaze would be a DECISION and therefore a rule, and is
deliberately not smuggled in.

## Hypothesis

**Primary, two-sided:** foveated real visual experience changes the anisotropy of the
learned receptive fields relative to waves alone.

Biology predicts **waves+video > waves** (experience refines/matures tuning on the
wave-built scaffold). Two-sided nonetheless: predicted directions in this arc have
been wrong three times, and the pilot point estimate is ≈ 0.

**H0:** d = 0.

## Design

- Arms (all with waves ON, `propagate=1`): `waves`, `waves+video`, `waves+noise`.
- `waves+video` = real Sesame Street frames (Jellyfin, 1080p HEVC → 16×16 grey).
- `waves+noise` = i.i.d. uniform frames through the IDENTICAL foveal aperture.
- **Paired within seed** (same seed drives the retina, the units, and the saccades).
- Fixed: 16×16 retina, 10 units, rf=7, 200 steps, fovea radius 3, saccade every 4,
  ignition every 5, latency window 2, unit_burst 3, homeostasis ON.
- **Unit of analysis = the SEED** (units within a run share a movie and compete under
  winner-take-all ⇒ not independent).

## Test statistic

Per seed *i*: `d_i = mean_anisotropy(waves+video)_i − mean_anisotropy(waves)_i`,
each arm's value being the mean anisotropy over that run's 10 units.

**Test:** one-sample, two-sided **sign-flip randomisation test** on `{d_i}`,
20,000 permutations, α = 0.05, with a bootstrap 95% CI.

## Sample size — FIXED IN ADVANCE

**n = 100 seeds.** Pilot on burned seeds 0–5 (variance only, no test): per-seed
SD = **0.107**. n=100 ⇒ ~80% power at α=0.05 for |δ| ≈ 0.030, ~99% for |δ| = 0.05.
The pilot point estimate was **−0.006** (i.e. ≈ null), so **a null result is the
likely outcome and is stated in advance as an acceptable finding**, not a failure to
be re-tested.

## Seeds

**Confirmatory seeds: 300–399.** Never used: rung-1 exploration used 0–13, the
rung-1 pre-reg used 100–179, this pilot used 0–5.

## Decision rule

- **PASS (fix works)** iff p < 0.05 **and** d > 0 ⇒ foveated experience refines the
  scaffold; the rung-1 failure was the blast, not the video.
- **NULL** iff p ≥ 0.05 ⇒ the fovea *removes the harm* (rung 1's −0.090) but does not
  produce the predicted benefit. Reported as a null; **no re-runs, no sweeps of
  fovea_radius / saccade_every**. A further attempt requires a NEW pre-registration.
- **PASS (wrong direction)** iff p < 0.05 and d < 0 ⇒ the fix did not repair the arm;
  report as a second failure of the experience arm.

## Analyses permitted

**Exactly one hypothesis test: `d` above.**

Reported as **descriptive only, non-inferential**: the three arm means, and
`waves+noise − waves` (which rung 1 established at −0.165, p<0.0001; it should remain
negative — the deprivation asymmetry must survive the aperture change. If it does NOT,
that is a red flag about the new drive, and is reported as such rather than tested
post-hoc).

---

# OUTCOME (run 2026-07-16, exactly as specified)

```
d(waves+video − waves): −0.0195   95% CI [−0.0334, −0.0055]   p = 0.0083
n = 100 seeds (300–399), 20,000 sign-flips, two-sided
```

## **DECISION: PASS, WRONG DIRECTION — the experience arm is STILL BROKEN.**

Foveated experience makes the receptive fields *less* anisotropic than waves alone.
Biology says normal rearing should match or beat dark rearing. It does not.

**Descriptive (NOT tests), as pre-committed:**

| arm | mean anisotropy |
|---|---|
| waves | 0.320 |
| waves+video | 0.300 |
| waves+noise | 0.307 |

- **`waves+noise − waves` = −0.013** — the pre-registered **RED FLAG fired.**
  Rung 1 measured **−0.165 (p<0.0001)**.
- per-seed SD of d: 0.072 (pilot predicted 0.107 ⇒ more power than planned).

## What this means — the fix broke what was working

The foveal aperture (radius 3, ~11% of the field) reduced video's harm
(−0.090 → −0.020) but **also destroyed the deprivation asymmetry** (noise's harm
−0.165 → −0.013). Experience is now nearly **inert** in both arms: the aperture is
too small/sparse to matter either way. That is not a fix — it is a trade of a real,
biologically-correct signal (unstructured drive is *actively destructive*, the one
result in this line that reproduced a real experiment) for a null.

**Rung 1's whole-field drive was wrong about video but RIGHT about noise.** The fovea
is right about neither. Both drives are wrong in different directions, which says the
problem is not "how much retina to drive" but something about *what* experience is
doing to the scaffold.

**No sweep of `fovea_radius` / `saccade_every` was run, per this plan.** Tuning the
aperture until the asymmetry returns and video turns positive would be exactly the
forking-paths failure this arc already committed once. A further attempt requires a
NEW pre-registration with a mechanism-level hypothesis — not a parameter search.

## Honest status of the experience rung

**Not built, after two attempts** (whole-field blast; foveated aperture). The
wave scaffold (rung 1) stands and is unaffected — it does not depend on the
experience arm.

## The foveal drive was REVERTED (and why that is not tidying-up)

Keeping it would have silently invalidated a committed, passing result: rung 1's
deprivation gate (−0.165, p<0.0001) was measured with the whole-field drive, and under
the fovea the same comparison is −0.013. A change that **breaks a working result and
does not fix its target is not an improvement**, so `WaveWorld.drive` is back at the
committed version. Verified after reverting, on fresh seeds 400–411:

```
waves 0.347 | waves+noise 0.170 | noise − waves = −0.177   (committed: −0.165)
```

The asymmetry reproduces. The foveal implementation is preserved at
`scratchpad/wave_world_foveal.py` and this document is its record — the experiment
was run, pre-registered, and it failed; that is the result, and it does not need to
live in the tree to be true.

---

# ATTEMPT 3 — pre-registration (written 2026-07-16 BEFORE the run)

## The mechanism-level hypothesis (this is not a parameter search)

Attempts 1–2 both failed because of a **mechanism bug, not an aperture size**:
`drive()` set `state="active"` — the SAME state a wave ignition uses — so **every
driven pixel became a travelling-wave SOURCE**. "Experience" was mass wave ignition.
Measured (propagate ON vs OFF, identical drive): waves alone 0.071 vs 0.001 (×91 —
the waves ARE the propagation), but video 0.171 vs 0.099 (×1.7) and noise 0.173 vs
0.151 (×1.1) — the drive injected 10–15% activity directly, dwarfing the waves' 7%,
then propagated on top.

**That artifact explains every prior arm ordering** (noise scatters ignition maximally
−0.165; correlated video less so −0.090; a small fovea barely at all −0.013) — and it
means **rung 1's celebrated deprivation asymmetry may itself be an artifact**: noise
destroying the wave simulation, not tuning. That possibility is why this test matters.

**THE FIX:** two pathways, one output — as in biology (waves come from the inner-retina
amacrine network; vision drives photoreceptors→bipolar→RGC; both make the RGC fire, but
a visually-driven RGC does not launch a wave). `driven` is now a separate per-frame
channel that contributes to `bursting` (what the learning rules read) and is invisible
to `wv_propagate` (which matches `state == "active"`).

**Verified before this test:** wave activity is now IDENTICAL in all arms
(0.071 ON / 0.001 OFF for waves, video and noise alike) — the scaffold is invariant, so
any arm difference is experience acting on LEARNING, not on the waves.

Drive returns to WHOLE-FIELD (the fovea is reverted; it was treating the symptom).

## Hypothesis, design, statistic

**Primary, two-sided:** `d_i = mean_anis(waves+video)_i − mean_anis(waves)_i`.
Biology predicts **d > 0** (experience refines the wave-built scaffold). Two-sided:
predicted directions have been wrong three times.

Design/statistic **identical to Attempt 1** (paired within seed; SEED is the unit of
analysis; 16×16, 10 units, rf=7, 200 steps, ignite every 5, window 2, unit_burst 3,
homeostasis ON; one-sample two-sided sign-flip, 20,000 perms, α=0.05, bootstrap CI).

**n = 100 seeds, FIXED IN ADVANCE** (prior per-seed SD 0.107 ⇒ ~80% power for
|δ| ≈ 0.030). **Confirmatory seeds 500–599** — never used (0–13 exploration, 100–179
rung-1 pre-reg, 300–399 attempt 2, 400–411 revert check).

## Decision rule

- **PASS** iff p<0.05 ∧ d>0 ⇒ experience refines the scaffold; the rung is built.
- **NULL** iff p≥0.05 ⇒ removing the artifact removes the harm but yields no benefit.
- **PASS, WRONG DIRECTION** iff p<0.05 ∧ d<0 ⇒ third failure of the experience arm.

**Exactly one hypothesis test.** No sweeps, no re-runs, no post-hoc measures.

## Pre-committed descriptive check (NOT a test)

`waves+noise − waves`, which rung 1 reported at **−0.165, p<0.0001**. With the
wave-ignition artifact removed, **if that asymmetry now collapses toward 0, then rung
1's headline biological result was an artifact of the bug and must be retracted** —
reported as such, whatever this test says.

## ATTEMPT 3 — OUTCOME (run exactly as specified)

```
d(waves+video − waves): -0.0967   95% CI [-0.1085, -0.0847]   p < 0.0001
n = 100 seeds (500-599), 20,000 sign-flips, two-sided
```

### **DECISION: PASS, WRONG DIRECTION — the experience arm fails a THIRD time.**

| arm | mean anisotropy |
|---|---|
| waves | 0.330 |
| waves+video | 0.234 |
| waves+noise | 0.151 |

per-seed SD of d: 0.061 (prior estimate 0.107 ⇒ more power than planned).

### The pre-committed check VINDICATES rung 1

`waves+noise − waves` = **−0.179** (rung 1: −0.165). The deprivation asymmetry
**SURVIVES** removal of the wave-ignition artifact. This was the pre-registered
condition under which rung 1's headline would have had to be RETRACTED — it does not
apply. **Unstructured drive is actively destructive for its own reason, not because it
was wrecking the wave simulation.** The suspicion was correct to raise and is now
answered.

### What is now established, and the remaining defect

The arms order cleanly and monotonically in pattern quality:
**waves 0.330 > video 0.234 > noise 0.151.** Structured experience beats unstructured
experience — but *both* are worse than no experience at all, which is still wrong
(biology: normal ≥ dark > sutured).

**Diagnosis (mechanism, and it is a NEW one — the flood MOVED rather than went away):**
`drive()` still median-splits, so ~50% of cells now BURST every frame. The duty-cycle
blast has relocated out of the wave channel and into the **bursting** channel, where
bh_potentiate then strengthens huge blobby swaths of every unit's RF. The two-pathway
fix removed the drive's effect on the WAVES (verified: activity identical across arms)
but not its effect on LEARNING.

**Why this now points back at the fovea, and why that is not a re-run:** attempt 2's
fovea failed *because the deprivation asymmetry then depended on wave ignition*, so
shrinking the aperture destroyed the asymmetry along with the harm. That coupling is
now gone — the asymmetry is independent of the drive aperture (proved above). A sparse
visual drive on a provably-invariant wave scaffold is therefore a **different
mechanism claim** than attempt 2's, not a parameter retry of it. It requires its own
pre-registration and was NOT run here.

### Honest status

**Experience rung: NOT BUILT after three attempts** (whole-field blast → foveal
aperture → two-pathway whole-field). Each attempt fixed a real, measured defect and
each revealed the next one. The wave scaffold (rung 1) stands, is unaffected by any of
this, and is now known NOT to rest on the artifact.

---

# ATTEMPT 4 — pre-registration (written 2026-07-16 BEFORE the run)

## The claim (why this is not attempt 2 again)

Attempt 3 proved the flood MOVED rather than vanished: the two-pathway fix removed the
drive's effect on the waves (activity identical across arms) but ~50% of cells still
BURST every frame (measured: burst duty 0.572 vs the waves' 0.141), so bh_potentiate
strengthened blobby swaths of every RF.

**Sparse visual drive on a provably-invariant wave scaffold.** Attempt 2's fovea failed
*because* the asymmetry then depended on wave ignition, so throttling the aperture
destroyed the signal along with the harm. That coupling is now gone: the `driven`
channel is invisible to `wv_propagate`. This is therefore a different mechanism claim,
not a parameter retry.

**Verified before this test** (fovea r=3, saccade every 4):

| arm | burst duty (learning reads this) | wave activity (must be invariant) |
|---|---|---|
| waves | 0.141 | 0.071 |
| waves+video | 0.186 | **0.071** |
| waves+noise | 0.187 | **0.071** |

The scaffold is bit-invariant across arms; experience modulates (+4.5pp) instead of
flooding (was +43pp); video and noise deliver identical drive QUANTITY, differing only
in pattern STRUCTURE. A bug was caught and fixed en route: saccades shared the ignition
RNG, which shifted wave activity 0.071→0.091 and would have confounded everything —
gaze now uses a separate RNG.

## Hypothesis — CONJUNCTIVE, so it cannot pass by making experience inert

This is the discipline attempt 2 lacked (it "removed the harm" only by making
experience do nothing at all).

- **H1a (primary):** `d_video = mean_anis(waves+video) − mean_anis(waves)` — two-sided.
  Biology predicts **d_video > 0** (experience refines the scaffold).
- **H1b (co-primary):** `d_noise = mean_anis(waves+noise) − mean_anis(waves)` — two-sided.
  Biology predicts **d_noise < 0** (unstructured drive is actively destructive).

**The rung is BUILT only if BOTH hold** (d_video > 0 ∧ p<0.025) **and**
(d_noise < 0 ∧ p<0.025). Bonferroni α=0.025 each, fixed now.

## Design / statistic / n

Identical to attempts 1–3: paired within seed, **SEED is the unit of analysis**,
16×16, 10 units, rf=7, 200 steps, ignite every 5, window 2, unit_burst 3, homeostasis
ON; **fovea_radius=3, saccade_every=4**. One-sample two-sided sign-flip (20,000 perms)
on each of `{d_video_i}`, `{d_noise_i}`, bootstrap CIs.

**n = 100 seeds FIXED IN ADVANCE** (prior per-seed SD 0.061–0.107 ⇒ ≥80% power for
|δ|≈0.03 at α=0.025). **Confirmatory seeds 700–799** — never used (0–13, 100–179,
300–399, 400–411, 500–599 all burned).

## Decision rule

- **BUILT** iff d_video>0 ∧ p_video<0.025 **AND** d_noise<0 ∧ p_noise<0.025.
- **INERT** iff both p≥0.025 ⇒ sparse drive removed the harm by removing experience's
  effect — attempt 2's failure mode, reported as such.
- **PARTIAL / FAIL** otherwise ⇒ reported exactly as observed. In particular
  d_video<0 significant = a FOURTH failure of the experience arm.

**Exactly two hypothesis tests (the conjunction). No sweeps, no re-runs.** A further
attempt requires a new pre-registration with a new mechanism-level hypothesis.

## ATTEMPT 4 — OUTCOME (run exactly as specified)

```
d_video: -0.0565   95% CI [-0.0688, -0.0444]   p < 0.0001     (predicted > 0)
d_noise: -0.0663   95% CI [-0.0772, -0.0554]   p < 0.0001     (predicted < 0)  ✓
n = 100 seeds (700-799), two-sided sign-flip, Bonferroni a=0.025 each
arms: waves 0.325 | waves+video 0.269 | waves+noise 0.259
```

### **DECISION: PARTIAL / FAIL — fourth failure of the video arm.**

The conjunction fails on H1a. `d_noise < 0` held (the deprivation asymmetry is robust
across every drive implementation tried). `d_video < 0` again — and video/noise have
now nearly COLLAPSED TOGETHER (gap 0.083 → 0.010), i.e. sparsity flattened the
structured-vs-unstructured distinction without repairing the video arm.

### The replicated finding across four attempts

| attempt | drive | d_video | d_noise |
|---|---|---|---|
| 1 | whole-field, ignites waves | −0.090 | **−0.165** |
| 2 | foveal, ignites waves | −0.020 | −0.013 |
| 3 | whole-field, two-pathway | −0.097 | **−0.179** |
| 4 | sparse foveal, two-pathway | −0.057 | −0.066 |

**ANY visual drive degrades the wave-built scaffold. Structured degrades less than
unstructured (every attempt). Experience never refines.** Three genuine mechanism bugs
were found and fixed along the way (wave-ignition artifact, RNG contamination,
burst-channel flood) and the result did not move. It is not a bug at this point; it is
what this model does.

### THE DIAGNOSIS — a developmental-ORDERING error, and it is ours

**Biology's normal rearing is SEQUENTIAL: waves FIRST (prenatal, pre-eye-opening),
THEN vision (post-eye-opening) — and retinal waves largely CEASE at eye opening.**
Every attempt here ran waves and vision **CONCURRENTLY**. "waves+video" is therefore
not normal rearing at all — it is a chimera that exists in no animal: a retina
simultaneously running its prenatal wave program and receiving patterned vision, with
both converging on the same burst rule. Of course the vision corrupts the scaffold —
it is competing with a wave program that biology would have already switched off.

The correct arms are **sequential epochs**:
- dark-reared = waves(phase 1) → waves(phase 2)
- normal      = waves(phase 1) → **vision**(phase 2)
- lid-sutured = waves(phase 1) → **noise**(phase 2)

This is the same class of error the whole arc is about — mangling the developmental
sequence — committed one level down, inside the machinery built to respect it. That it
took four pre-registered failures to see is the honest cost of testing an arm's
PARAMETERS before questioning its SCHEDULE.

### Honest status

**Experience rung: NOT BUILT after four attempts.** Not attempted here: the sequential
schedule, which needs its own pre-registration. The wave scaffold (rung 1) stands and
is untouched by any of this; `fovea_radius` defaults to 0, so every committed result
reproduces.

---

# ATTEMPT 5 — pre-registration: SEQUENTIAL EPOCHS (written 2026-07-16 BEFORE the run)

## The claim

Attempts 1–4 all ran waves and vision CONCURRENTLY — a chimera that exists in no
animal. Biology is **sequential**: waves run prenatally, vision arrives at eye
opening, and **the waves largely cease when it does**. So "waves+video" was never
normal rearing, and vision was competing with a wave program biology would already
have switched off. This attempt fixes the SCHEDULE, not a parameter.

## Design — two epochs, phase 1 identical in every arm

**Phase 1 (200 steps, ALL arms identical): waves only** (`propagate=1`, ignite every
5, no drive). This builds the scaffold. Because it is bit-identical across arms
(same seed, same RNG draws), every arm enters phase 2 with the SAME receptive fields.

**Phase 2 (200 steps): eye opening — waves CEASE** (`propagate=0`, no ignition):

| arm | phase 2 drive | biology |
|---|---|---|
| `dark` | **nothing** | dark-reared: maps from waves persist, tuning never matures |
| `normal` | **real video** (Sesame Street) | normal rearing |
| `sutured` | **noise** | lid suture: degraded/decorrelated pattern |

Whole-field drive (`fovea_radius=0`, the committed default). Attempt 4's sparse
aperture is NOT used: it flattened the structured/unstructured distinction (gap
0.083→0.010), and its rationale — protecting the wave scaffold from the drive — is
moot once the waves have ceased in phase 2. Everything else as before: 16×16, 10
units, rf=7, window 2, unit_burst 3, homeostasis ON, two-pathway `driven` channel.

Note `dark` receives NO input in phase 2, so no rule fires and its RFs are FROZEN at
the phase-1 scaffold. That is the point: it is the "waves built it, nothing refined
it" baseline.

## Hypotheses — CONJUNCTIVE (cannot pass by making experience inert)

- **H1a (primary):** `d_normal = anis(normal) − anis(dark)`, two-sided.
  Biology predicts **d_normal > 0** — vision MATURES tuning beyond the frozen scaffold.
- **H1b (co-primary):** `d_sutured = anis(sutured) − anis(dark)`, two-sided.
  Biology predicts **d_sutured < 0** — unstructured drive is actively destructive.

**The rung is BUILT only if BOTH** (d_normal>0 ∧ p<0.025) **AND** (d_sutured<0 ∧
p<0.025). Bonferroni α=0.025 each, fixed now.

This is the exact ordering the research established (3-0): **normal ≥ dark > sutured**,
with lid-suture worse than darkness.

## n / seeds / statistic

Paired within seed; **SEED is the unit of analysis**; one-sample two-sided sign-flip
(20,000 perms) per hypothesis; bootstrap CIs. **n = 100 seeds FIXED IN ADVANCE**
(prior per-seed SD 0.06–0.11 ⇒ ≥80% power for |δ|≈0.03 at α=0.025).
**Confirmatory seeds 900–999** — never used (0–13, 100–179, 300–399, 400–411,
500–599, 700–799 all burned).

## Decision rule

- **BUILT** iff both hold ⇒ sequential experience refines the wave scaffold; the four
  prior failures were the concurrent schedule, not the drive.
- **INERT** iff both p≥0.025 ⇒ phase-2 experience does nothing.
- **FAIL** otherwise, reported exactly as observed. `d_normal<0` significant = a FIFTH
  failure, and would say the burst rule cannot use patterned vision at all — which
  would point at the RULE (raw Hebbian on RGC bursts), not the schedule.

**Exactly two hypothesis tests. No sweeps, no re-runs.** A fifth attempt requires a new
pre-registration with a new mechanism-level hypothesis.

## ATTEMPT 5 — OUTCOME (run exactly as specified)

```
d_normal  (normal - dark):  -0.0057   95% CI [-0.0092, -0.0022]   p = 0.0012   (predicted > 0)
d_sutured (sutured - dark): -0.0103   95% CI [-0.0136, -0.0070]   p < 0.0001   (predicted < 0) OK
n = 100 seeds (900-999), two-sided sign-flip, Bonferroni a=0.025 each
arms: dark 0.325 | normal 0.319 | sutured 0.315
```

### **DECISION: FAIL — fifth failure. The SCHEDULE was not the (only) problem.**

The sequential fix did exactly what it claimed (phase 1 bit-identical; waves cease at
phase 2; `dark` frozen) and **the result did not move**: the same monotonic ordering as
all four concurrent attempts, with magnitudes merely collapsed (−0.006 vs −0.057)
because phase 2 carries no wave activity.

### THE VERDICT ACROSS FIVE PRE-REGISTERED ATTEMPTS

| attempt | schedule | drive | d_video/normal | d_noise/sutured |
|---|---|---|---|---|
| 1 | concurrent | whole-field, ignites waves | −0.090 | −0.165 |
| 2 | concurrent | foveal, ignites waves | −0.020 | −0.013 |
| 3 | concurrent | whole-field, two-pathway | −0.097 | −0.179 |
| 4 | concurrent | sparse foveal, two-pathway | −0.057 | −0.066 |
| 5 | **sequential** | whole-field, two-pathway | **−0.006** | −0.010 |

**Patterned vision NEVER refines. Structured always degrades less than unstructured.
The direction is invariant across every drive implementation and both schedules.**
Four real mechanism bugs were found and fixed en route (wave-ignition artifact,
saccade/ignition RNG contamination, burst-channel flood, concurrent schedule). None
moved it. **This is not a bug — it is what the rule does.**

### The implication, PRE-COMMITTED before the run

This document stated in advance: *"`d_normal<0` significant = a FIFTH failure, and
would say the burst rule cannot use patterned vision at all — which would point at the
RULE (raw Hebbian on RGC bursts), not the schedule."* That is the outcome, and it is
therefore the conclusion — not a post-hoc reinterpretation.

**The burst rule cannot use patterned vision to refine.** Butts/Kanold/Shatz's rule is
the **retinogeniculate** rule: it was measured on *wave-driven* refinement before eye
opening, and the verified research explicitly **killed 0-3** the claim that it drives
the developmental outcome ("assert the measured rule, not the outcome"). We asserted
the outcome anyway, one stage further up the hierarchy, on input it was never measured
on. Experience-dependent V1 refinement is not raw Hebbian on RGC bursts — it involves
a sliding/activity-dependent threshold (BCM), cortical inhibition, and critical-period
gating, none of which exist here. With fixed +21.3%/−5.9% and no threshold, a unit
potentiates whatever co-bursts; a large bright blob teaches a blob. Nothing in the
mechanism can make vision SHARPEN rather than BLUR.

### Honest status — the rung is closed as NOT BUILT

**Experience rung: NOT BUILT after five pre-registered attempts.** The next hypothesis
is a RULE change (BCM sliding threshold / inhibition), not another drive or schedule —
and it must be pre-registered as such. Rung 1 stands untouched and vindicated: its
deprivation asymmetry survived every implementation, and `d_sutured<0` held in all five
attempts — **unstructured drive being destructive is the one biological fact this model
reproduces, robustly.**

---

# ATTEMPT 6 — pre-registration: BCM SLIDING THRESHOLD (written 2026-07-16 BEFORE the run)

## The claim — a RULE change, as the five failures demanded

Five pre-registered attempts established that patterned vision NEVER refines, across
every drive and both schedules. The pre-committed implication: **the RULE is the
defect.** Butts' constants are FIXED-SIGN (+21.3% if the pre burst in-window, −5.9%
otherwise), so a unit potentiates whatever co-bursts — a bright blob teaches a blob,
and nothing can make vision SHARPEN rather than BLUR.

**BCM (Bienenstock-Cooper-Munro)** makes the sign depend on the postsynaptic drive
relative to a threshold that SLIDES with the unit's own recent activity:
`theta ← theta + theta_rate·(act² − theta)`; potentiate iff `act² > theta`, depress
iff `act² < theta`. A unit that responds to everything raises its own threshold until
only the strongest patterns clear it. That is the selectivity the fixed-sign rule
lacks. **Butts' magnitudes are KEPT as the step sizes — only the SIGN rule changes**,
so the deviation from measured biology is exactly one thing, named.

`bcm=0` (default) keeps the fixed-sign rule exactly ⇒ every committed result
reproduces; `bcm=1` swaps it in. The ablation is DATA.

**Three bugs were found and fixed while building it, all measured, all recorded in the
seed:** (a) classic BCM compares `y` to `theta=E[y²]`, which only works for y~O(1) —
here act~8 drove theta→70 and NOTHING ever potentiated (RF std collapsed to 0.17); the
comparison is `act²` vs theta, scale-free. (b) homeostasis required `bursting==1`,
tying it to winner-take-all — but BCM learns on ALL units, so non-winners were never
scaled and ran away (theta→1.8e5, RF std 25). (c) BCM leaves silent synapses
unchanged, so they were never `touched` and the "all touched" ordering guard never
fired ⇒ no scaling at all (RF total 2000+ vs target 49); `bcm_mark_silent` marks them
without changing weights. **Verified before this test: RF total = 49.0 = target_sum
under both rules; RF std 0.68–0.94 (structure present, bounded).**

## Design — the SEQUENTIAL schedule (attempt 5's, which was correct)

Phase 1 (200 steps, ALL arms bit-identical): waves only. Phase 2 (200 steps): waves
CEASE (`propagate=0`, no ignition); `dark` = no input, `normal` = real video,
`sutured` = noise. Whole-field two-pathway drive. **`bcm=1` throughout.** Everything
else as attempt 5.

## Hypotheses — CONJUNCTIVE (cannot pass by making experience inert)

- **H1a:** `d_normal = anis(normal) − anis(dark)`, two-sided. Predicted **> 0**.
- **H1b:** `d_sutured = anis(sutured) − anis(dark)`, two-sided. Predicted **< 0**.

**BUILT** only if (d_normal>0 ∧ p<0.025) **AND** (d_sutured<0 ∧ p<0.025).
Bonferroni α=0.025 each. This is the research's 3-0 ordering: **normal ≥ dark >
sutured**.

## n / seeds / statistic

Paired within seed; **SEED is the unit of analysis**; one-sample two-sided sign-flip
(20,000 perms) per hypothesis; bootstrap CIs. **n = 100 FIXED IN ADVANCE.**
**Confirmatory seeds 1100–1199** — never used.

## Decision rule

- **BUILT** iff both hold ⇒ BCM lets experience refine the wave scaffold; the five
  prior failures were the fixed-sign rule.
- **INERT** iff both p≥0.025.
- **FAIL** otherwise, reported as observed. `d_normal<0` significant = a SIXTH failure
  ⇒ the defect is not the sign rule either, and the experience rung needs a
  fundamentally different account (cortical inhibition / critical-period gating / a
  different readout than anisotropy) — **not another parameter.**

**Exactly two hypothesis tests. No sweeps, no re-runs.**

## ATTEMPT 6 — OUTCOME (run exactly as specified)

```
d_normal:  -0.0557   95% CI [-0.0700, -0.0418]   p < 0.0001   (predicted > 0)
d_sutured: -0.0767   95% CI [-0.0901, -0.0636]   p < 0.0001   (predicted < 0) OK
n = 100 seeds (1100-1199).   arms: dark 0.245 | normal 0.189 | sutured 0.168
```

### **DECISION: FAIL — sixth failure. The sign rule was not the defect either.**

### SIX PRE-REGISTERED ATTEMPTS — the result is INVARIANT

| # | schedule | rule / drive | d_video/normal | d_noise/sutured |
|---|---|---|---|---|
| 1 | concurrent | fixed-sign, whole-field (ignites waves) | −0.090 | −0.165 |
| 2 | concurrent | fixed-sign, foveal (ignites waves) | −0.020 | −0.013 |
| 3 | concurrent | fixed-sign, two-pathway | −0.097 | −0.179 |
| 4 | concurrent | fixed-sign, sparse two-pathway | −0.057 | −0.066 |
| 5 | **sequential** | fixed-sign | −0.006 | −0.010 |
| 6 | **sequential** | **BCM sliding threshold** | −0.056 | −0.077 |

**dark > normal > sutured in every single one.** Seven real mechanism bugs were found
and fixed across these attempts (wave-ignition artifact, RNG contamination,
burst-channel flood, concurrent schedule, BCM scale, homeostasis scope, silent-synapse
marking). **Not one of them moved the direction.**

### The pre-committed implication

This document stated in advance: *"`d_normal<0` significant = a SIXTH failure ⇒ the
defect is not the sign rule either, and the experience rung needs a fundamentally
different account — not another parameter."* That is the outcome and therefore the
conclusion.

### THE SUSPICION THIS RAISES — and why it is NOT acted on here

Look at what `dark` actually is in attempts 5–6: **no phase-2 input at all**, i.e. RFs
FROZEN at the phase-1 wave scaffold. So "normal vs dark" is not "vision vs no vision" —
it is **"learned more" vs "stopped learning"**. And across all six attempts the arm
that learns LEAST scores HIGHEST. The pattern may not be about vision at all:
**anisotropy may simply DECREASE with continued learning of any kind**, in which case
the readout — not the rule, drive, or schedule — is what has been wrong for six
attempts, and every one of them was measuring "how much did this arm learn" while
believing it measured "how well is this arm tuned".

**This is not acted on now, deliberately.** Reaching for a new measure the moment a
gate fails is metric surgery — the exact move this arc has already recorded as
forbidden, and the anisotropy measure IS calibrated (ideal Gabor 0.87 / random 0.15 /
ideal DoG 0.00). What it was never checked against is *learning duration*. That is a
new, testable, mechanism-level hypothesis and it requires its own pre-registration,
whose FIRST test must be the boring one: **does anisotropy fall with phase-2 steps when
the input is waves themselves?** If it does, six failures collapse into one measurement
error, and rung 1's headline (which compares arms at equal learning duration) survives
regardless.

### Honest status — the rung is CLOSED as NOT BUILT

**Experience rung: NOT BUILT after six pre-registered attempts.** Rung 1 stands:
`d_sutured < 0` held in ALL SIX — unstructured drive being actively destructive is the
one biological fact this model reproduces, robustly, across every mechanism tried.

---

# INSTRUMENT CHECK (run 2026-07-16) — the readout IS duration-confounded, AND the `dark` arm was wrong

The boring test the previous section demanded: phase 1 = 200 steps of waves, then
phase 2 = N MORE steps of **waves themselves** — the same input that built the
scaffold. n=24 seeds (2000–2023).

| phase-2 steps | anisotropy | 95% CI |
|---|---|---|
| 0 (frozen) | 0.323 | [0.299, 0.347] |
| 50 | 0.326 | [0.303, 0.348] |
| 100 | 0.321 | [0.299, 0.344] |
| 200 | 0.304 | [0.282, 0.327] |
| 400 | 0.274 | [0.255, 0.293] |

**200 extra WAVE steps vs frozen: −0.0186, p=0.0060.**

## Finding 1 — the readout partly measures LEARNING DURATION, not tuning

More of the *identical* input that built the scaffold **lowers** the score, monotonically.
Anisotropy therefore conflates "how long did this arm learn" with "how well is it
tuned". Every arm in attempts 5–6 was scored against an arm that had **stopped
learning**, and the one that learned least won. The measure is calibrated against
structure (ideal Gabor 0.87 / random 0.15 / ideal DoG 0.00) but was never calibrated
against *duration* — that gap is now measured.

## Finding 2 (the bigger one) — `dark` was not dark-rearing

**Biology's dark-reared animals KEEP their retinal waves** — that is *why* they have
maps. `VISION_RUNG1_PLAN.md` states this explicitly: *"NOTE the correction that
matters: dark rearing does NOT remove waves — dark-reared ferrets have maps BECAUSE
waves continue."* **Attempts 5–6 made `dark` = no input at all.** So they never tested
normal-vs-dark; they tested **vision vs FROZEN**.

Against the correct baseline the sign may invert. Over the same 200 phase-2 steps:

| phase-2 input | cost vs frozen |
|---|---|
| **waves (= real dark-rearing)** | **−0.019** |
| vision (attempt 5) | −0.006 |
| noise (attempt 5) | −0.010 |
| vision (attempt 6, BCM) | −0.056 |
| noise (attempt 6, BCM) | −0.077 |

Under attempt 5's rule, vision (−0.006) costs LESS than continued waves (−0.019) ⇒
**normal > dark**, the predicted direction, against a control that was never run.
(Attempt 6's BCM numbers are larger than the confound and are not explained by it.)

**This arithmetic is ACROSS RUNS with different seeds and is NOT a result.** It is the
reason a re-run is warranted, nothing more.

## What this does and does not overturn

- **Attempts 5–6 are INVALIDATED as tests of normal-vs-dark** — wrong control arm.
  Their `d_sutured` figures are likewise vision-vs-frozen, not sutured-vs-dark.
- **Attempts 1–4 are NOT invalidated by Finding 2** (they were concurrent: every arm
  had waves throughout, at equal duration). They remain valid tests of
  waves+X vs waves, and they failed.
- **Rung 1 is untouched by both findings**: its arms run for identical durations and
  all carry waves, so neither the duration confound nor the dark-arm error applies.
  `d_sutured < 0` held in all six attempts.

## The next test (NOT run here — needs its own pre-registration)

Re-run the sequential design with **`dark` = waves continuing through phase 2** (real
dark-rearing), all arms at **identical learning duration**, so the duration confound
cancels by construction rather than being corrected for. Conjunctive gate as before.
Both the fixed-sign rule and BCM should be tested, since the confound explains
attempt 5's magnitudes but not attempt 6's.

**Not started now.** Six pre-registered attempts have already been spent on this rung;
the honest move is to hand over a diagnosed instrument rather than open a seventh on
the last of the context.

---

# ATTEMPT 7 — pre-registration: CORRECTED DARK ARM (written 2026-07-16 BEFORE the run)

## The two corrections

1. **`dark` = waves CONTINUING through phase 2** — real dark-rearing. Dark-reared
   animals keep their spontaneous activity and lack only patterned VISION; they have
   maps *because* the waves ran. Attempts 5–6 froze the dark arm (no input), so they
   tested vision-vs-frozen and are invalidated.
2. **All arms learn for the IDENTICAL duration** (200 phase-2 steps, every arm
   driven). The duration confound (−0.019 per 200 steps of any input, p=0.006) then
   **cancels by construction** instead of being corrected for.

The arms now differ in exactly one thing: **what the phase-2 input IS.**

## Design

Phase 1 (200 steps, ALL arms bit-identical): waves only, `propagate=1`.
Phase 2 (200 steps, ALL arms driven for the same duration):

| arm | phase 2 | biology |
|---|---|---|
| `dark` | **waves continue** (`propagate=1`, ignite every 5) | dark-reared: spontaneous activity, no vision |
| `normal` | **real video**, waves cease (`propagate=0`) | normal rearing: waves cease at eye opening |
| `sutured` | **noise**, waves cease | lid suture: degraded pattern |

Whole-field two-pathway drive; **`bcm=0`** — the MEASURED Butts rule is the primary
test (attempt 6's BCM figures exceed the confound and are not explained by it, so BCM
is a separate question and is NOT tested here). 16×16, 10 units, rf=7, window 2,
unit_burst 3, homeostasis ON.

## Hypotheses — CONJUNCTIVE

- **H1a:** `d_normal = anis(normal) − anis(dark)`, two-sided. Predicted **> 0**.
- **H1b:** `d_sutured = anis(sutured) − anis(dark)`, two-sided. Predicted **< 0**.

**BUILT** iff (d_normal>0 ∧ p<0.025) **AND** (d_sutured<0 ∧ p<0.025). Bonferroni
α=0.025 each. The research's 3-0 ordering: **normal ≥ dark > sutured**.

## n / seeds / statistic

Paired within seed; **SEED is the unit of analysis**; one-sample two-sided sign-flip
(20,000 perms); bootstrap CIs. **n = 100 FIXED IN ADVANCE.** **Seeds 1300–1399** —
never used.

## Decision rule

- **BUILT** iff both hold ⇒ the experience rung works, and the six prior failures were
  the wrong control arm + the duration confound.
- **INERT** iff both p≥0.025.
- **FAIL** otherwise, reported as observed. `d_normal<0` significant here — against the
  CORRECT control, at equal duration — would mean vision genuinely cannot refine in
  this model, and no control/confound/schedule story remains to explain it away.

## Stated honestly in advance

The cross-run arithmetic that motivates this (waves −0.019 vs vision −0.006 over the
same 200 steps ⇒ normal > dark) is **not evidence** — different seeds, different runs.
This is the first run in which normal and dark are measured against each other at
equal duration with the correct control. **A null or a failure here is the real
answer**, and after six attempts it would close the rung on the mechanism rather than
on my design errors.

**Exactly two hypothesis tests. No sweeps, no re-runs.**

## ATTEMPT 7 — OUTCOME (run exactly as specified)

```
d_normal  (normal - dark):  +0.0244   95% CI [+0.0166, +0.0323]   p < 0.0001   (predicted > 0) PASS
d_sutured (sutured - dark): +0.0194   95% CI [+0.0119, +0.0270]   p < 0.0001   (predicted < 0) INVERTED
n = 100 seeds (1300-1399).   arms: dark 0.309 | normal 0.333 | sutured 0.328
```

### **DECISION: FAIL (conjunction) — but H1a PASSES for the first time in seven attempts.**

- **H1a PASSES.** With the correct control at equal duration, **normal rearing beats
  dark rearing** (+0.024, p<0.0001) — the predicted direction, which six prior attempts
  never produced. **Patterned vision CAN refine the wave scaffold.** The six failures
  really were the wrong control arm + the duration confound.
- **H1b INVERTS.** `sutured` (0.328) also beats `dark` (0.309). Model ordering:
  **normal > sutured > dark.** Biology: **normal ≥ dark > sutured.** `dark` is in the
  wrong place — continued waves are the WORST input here, when biology has them
  beating degraded vision.

### THIS PARTIALLY RETRACTS RUNG 1'S HEADLINE

Rung 1's deprivation asymmetry (`waves+noise` −0.165, p<0.0001) held in all six prior
attempts and was this line's one reproduced biological fact. **Attempt 7 shows it was
confounded.** In attempts 1–4 noise was **ADDED to** running waves; here noise
**REPLACES** ceased waves. Both results are internally consistent:

- noise **+** waves < waves alone ⇒ noise **disrupts concurrent wave propagation**;
- noise **instead of** waves > waves alone ⇒ noise is no worse than more wave-learning.

So the asymmetry measured **"unstructured drive disrupts a running wave program"**, NOT
**"unstructured experience degrades tuning"** — which is what the lid-suture experiment
is about (in the animal, waves have already ceased at eye opening; suture degrades
*vision*, it does not interfere with waves). **Rung 1's headline was the right number
for the wrong claim.** It stands as a fact about wave disruption; it does not stand as
the White/Coppola/Fitzpatrick deprivation asymmetry. Recorded here rather than left
in place.

### Honest status after seven attempts

**The experience rung is HALF BUILT, and it is the half nobody had:** vision refines
(H1a, p<0.0001, correct control, equal duration), and normal > sutured is the right
order. What the model does not reproduce is **dark > sutured** — continued waves come
out worst, so degraded vision looks better than dark-rearing.

**Named next hypothesis (NOT run):** the `dark` arm's waves may be too strong/too
prolonged — in the animal the wave program **winds down** at eye opening rather than
running at full strength for the whole post-natal epoch, so "waves at phase-1 intensity
for all of phase 2" over-blurs. A dark arm with **decaying** wave drive is the obvious
test, and it is a mechanism claim (the wave program has a developmental offset), not a
parameter tweak. It needs its own pre-registration.

---

# ATTEMPT 8 — pre-registration: DECAYING DARK ARM (written 2026-07-16 BEFORE the run)

## The hypothesis

In the animal the wave program **winds down** at eye opening; it does not run at
prenatal intensity through the whole post-natal epoch. Attempt 7's `dark` ran waves at
full phase-1 strength for all of phase 2, which may over-blur and put `dark` (0.309)
below `sutured` (0.328). **`dark` = waves whose ignition rate DECAYS exponentially**
(τ = P2/3, so ~5% of base rate by the end) models the developmental offset.

## PREDICTION, STATED IN ADVANCE: this will NOT fix H1b

The frozen baseline (no phase-2 input) is **0.323** (instrument check, n=24). Attempt
7's arms read against it:

| arm | score | vs frozen | reading |
|---|---|---|---|
| dark (full waves) | 0.309 | **−0.014** | continued waves actively BLUR |
| sutured (noise) | 0.328 | **+0.005** | noise is **INERT** — ≈ no learning at all |
| normal (vision) | 0.333 | **+0.010** | vision genuinely refines |

Decaying `dark`'s waves can at best raise it toward the frozen ceiling (~0.323), which
is **still below** `sutured` (0.328). **So H1b should still fail**, and the arms are
not ordered by drive quantity (noise drives ~50% of cells vs waves' ~7% and still
scores higher).

**The real gap this exposes: unstructured input is INERT, not destructive.** Lid suture
degrades tuning in the animal; here noise ≈ frozen. With fixed-sign Butts + homeostasis,
random input's potentiation averages out and the phase-1 scaffold simply survives.

This test is run anyway because a pre-registered failure **settles** the decaying-dark
hypothesis instead of leaving it as a plausible untested story — and because the
prediction above is falsifiable: if `dark` rises ABOVE `sutured`, I am wrong about the
inertness reading.

## Design / hypotheses / n

Identical to attempt 7 except `dark` ignites with probability `exp(-i/τ)`, τ=P2/3.
All arms still learn for 200 phase-2 steps. `bcm=0`.

- **H1a:** `d_normal = anis(normal) − anis(dark)`, two-sided. Predicted **> 0**.
- **H1b:** `d_sutured = anis(sutured) − anis(dark)`, two-sided. Predicted **< 0** by
  biology; **predicted ≥ 0 by me** (see above).

**BUILT** iff both hold (Bonferroni α=0.025 each). Paired within seed, **SEED is the
unit of analysis**, sign-flip 20,000 perms, **n=100 FIXED**, **seeds 1500–1599** (never
used).

## Pre-committed descriptive

`dark` vs the frozen ceiling 0.323 — does decay actually lift it, and how far?

**Exactly two hypothesis tests. No sweeps, no re-runs.**

## ATTEMPT 8 — OUTCOME (run exactly as specified)

```
d_normal  (normal - dark):  +0.0107   95% CI [+0.0019, +0.0196]   p = 0.0204   PASS
d_sutured (sutured - dark): +0.0025   95% CI [-0.0060, +0.0108]   p = 0.5709   NULL
n = 100 seeds (1500-1599).   arms: dark 0.314 | normal 0.325 | sutured 0.316
```

### **DECISION: FAIL (conjunction) — and the in-advance prediction was CORRECT.**

The pre-registration predicted decay would NOT fix H1b, because noise reads as INERT
(≈ frozen) rather than destructive. Confirmed: decay lifted `dark` 0.309 → 0.314
(toward the frozen ceiling 0.323, as forecast, not past it), and `sutured` (0.316) is
now statistically **indistinguishable** from `dark` (p=0.57). The decaying-dark
hypothesis is **settled and rejected** rather than left plausible-but-untested.

## THE RUNG AFTER EIGHT ATTEMPTS — what is established

**H1a — VISION REFINES — PASSES, and it REPLICATES across two independent
pre-registrations:**

| attempt | dark arm | d_normal | p | seeds |
|---|---|---|---|---|
| 7 | waves continue (full) | **+0.0244** | <0.0001 | 1300–1399 |
| 8 | waves decay | **+0.0107** | 0.0204 | 1500–1599 |

Patterned real visual experience **measurably refines the self-generated wave
scaffold**, against the correct control, at equal learning duration, replicated on
fresh seeds under two different dark-arm models. **This is the experience rung's core
claim and it is earned.**

**H1b — UNSTRUCTURED DRIVE DESTROYS — NEVER passes** with the correct control. Read
against the frozen baseline (0.323): noise ≈ frozen (**inert**), vision ≈ +0.010
(**refines**), full waves ≈ −0.014 (**blur**). The model reproduces **normal > dark**
but not **dark > sutured**.

**The mechanism, measured:** with the fixed-sign Butts rule + multiplicative
homeostasis, random input's potentiation **averages out** — the phase-1 scaffold simply
survives it. Nothing in the rule lets unstructured input actively *degrade* tuning; it
can only fail to improve it. Lid-suture deprivation is therefore **out of reach of this
rule**, which is a statement about the rule, not about the biology.

**Rung 1's headline remains partially retracted** (attempt 7): its −0.165 asymmetry
measured *noise disrupting a running wave program*, not *unstructured experience
degrading tuning*. Attempt 8 confirms the corrected reading — once noise REPLACES waves
rather than competing with them, it is inert.

### Honest status

**Experience rung: HALF BUILT, and the built half is the substantive one.** Vision
refines (replicated, p<0.0001 and p=0.02). Not reproduced: the deprivation asymmetry
proper, which needs a rule in which unstructured input can actively degrade — BCM was
the obvious candidate and failed on its own terms (attempt 6, though against the wrong
control; **BCM against the CORRECTED dark arm is untested and is the one clean open
question left**). That needs its own pre-registration.

---

# ATTEMPT 9 — pre-registration: BCM against the CORRECTED dark arm (written BEFORE the run)

## The one clean open question

Attempt 6 tested BCM but against the **frozen** dark arm — the same design error that
invalidated attempt 5. BCM has never been tested against the correct control. It is the
obvious candidate for the missing half, because **BCM's sign flips below threshold**:
unstructured input can *actively degrade*, which is exactly what the fixed-sign rule
cannot do (attempts 7–8: noise is INERT, ≈ frozen).

## Design

Attempt 7's design EXACTLY — sequential, phase 1 = 200 steps waves (bit-identical),
phase 2 = 200 steps, all arms driven for equal duration; `dark` = **waves continue**,
`normal` = video (waves cease), `sutured` = noise (waves cease) — with **`bcm=1`
throughout** (phase 1 and 2).

## PREDICTION, STATED IN ADVANCE

From attempt 6 (BCM vs frozen): vision **−0.056**, noise **−0.077** ⇒ under BCM, noise
IS more destructive than vision — the mechanism fixed-sign lacks.

- **H1b (sutured < dark): I predict it PASSES**, provided `dark`'s continued waves are
  no more destructive than noise. This is BCM's whole point.
- **H1a (normal > dark): genuinely uncertain.** Waves and vision are *both* structured,
  so `dark` may not separate from `normal` — and under fixed-sign, continued waves were
  the MOST blurring input of all (attempt 7), which would help H1a but is not
  guaranteed to carry over to BCM.

**If BOTH pass, the experience rung is BUILT** — normal > dark > sutured, the research's
3-0 ordering, with the correct control at equal duration.

## Hypotheses / n / seeds

- **H1a:** `d_normal = anis(normal) − anis(dark)`, two-sided, predicted **> 0**.
- **H1b:** `d_sutured = anis(sutured) − anis(dark)`, two-sided, predicted **< 0**.

**BUILT** iff both (Bonferroni α=0.025 each). Paired within seed; **SEED is the unit of
analysis**; sign-flip 20,000 perms; bootstrap CIs. **n=100 FIXED IN ADVANCE.**
**Seeds 1700–1799** — never used.

**Exactly two hypothesis tests. No sweeps, no re-runs.** If this fails, the experience
rung closes as half-built (vision refines; deprivation not reproduced) and the next move
is a different account entirely — not another rule variant.

## ATTEMPT 9 — OUTCOME (run exactly as specified)

```
d_normal  (normal - dark):  +0.1433   95% CI [+0.1342, +0.1523]   p < 0.0001   PASS (huge)
d_sutured (sutured - dark): +0.1169   95% CI [+0.1072, +0.1270]   p < 0.0001   INVERTED
n = 100 seeds (1700-1799).   arms: dark 0.050 | normal 0.193 | sutured 0.167
```

### **DECISION: FAIL — and the proviso in my own prediction is what broke.**

The prediction said H1b would pass *"provided `dark`'s continued waves are no more
destructive than noise"*. They are **far** more destructive: under BCM, sustained waves
drive `dark` to **0.050 — BELOW the random floor (0.148)**. The scaffold is annihilated.
The BCM-specific half of the prediction was right (normal 0.193 > sutured 0.167 ⇒ BCM
*does* make noise more destructive than vision, which fixed-sign cannot); it is simply
irrelevant once `dark` is on the floor.

## THE REAL DEFECT, NAMED AFTER NINE ATTEMPTS

Across attempts 7, 8 and 9, under **every** rule and **every** dark-arm model:

| dark arm | rule | dark score |
|---|---|---|
| waves continue (full) | fixed-sign | 0.309 |
| waves decay | fixed-sign | 0.314 |
| waves continue (full) | BCM | **0.050** |

**Continued waves are always the most destructive input.** `sutured` therefore always
beats `dark`, and `dark > sutured` is unreachable — not because of the drive, the
schedule, the aperture, the sign rule or the control, all of which have now been fixed
and tested.

**THE LEARNING RULE DOES NOT CONVERGE ON ITS OWN INPUT DISTRIBUTION.** The instrument
check already showed it and I read it as a mere confound: 200→400 steps of waves takes
anisotropy 0.323 → 0.274. **More of the exact input that BUILT the scaffold DEGRADES
it.** BCM makes this catastrophic (0.050). A developmental learning rule must be
*self-consistent*: prolonged exposure to the statistics that formed a representation
should **stabilise** it, not dissolve it. Ours dissolves it.

That is why `dark` — the arm defined by *continued exposure to its own formative
input* — is always worst, and why every deprivation comparison inverted. It is also
why rung 1's asymmetry only ever appeared when noise **disrupted running waves**: the
waves were degrading themselves, and noise merely interfered with that.

**This is a single defect that explains all nine attempts**, and it is upstream of
every mechanism tried. No drive, schedule, aperture, threshold or control fixes a rule
that destroys its own fixed point.

### Honest final status

**Experience rung: HALF BUILT.** Established and replicated across three independent
pre-registrations (7: +0.024 p<0.0001; 8: +0.011 p=0.020; 9: +0.143 p<0.0001):
**patterned visual experience refines the wave scaffold, against the correct control,
at equal duration.** That result is robust to the rule (fixed-sign AND BCM) and to the
dark-arm model.

**Not reproduced and now EXPLAINED rather than merely failed:** `dark > sutured`
requires a rule with a stable fixed point under its own training distribution. The next
work is **convergence** (does the rule settle? BCM's theta should provide it and
demonstrably does not at these settings), not another mechanism. That is a
pre-registration about the rule's *dynamics*, and it must start by measuring the
obvious: **anisotropy vs wave-exposure duration out to convergence or collapse.**

---

# CONVERGENCE MEASUREMENT (run 2026-07-16) — the scaffold is a TRANSIENT; neither rule has a useful fixed point

Waves only, far past the previous 400-step horizon. n=12 seeds (3000–3011).

| steps | FIXED-SIGN anisotropy | drift | BCM anisotropy | drift |
|---|---|---|---|---|
| 0 | 0.150 (random floor) | — | 0.150 | — |
| 50 | 0.298 | 0.335 | 0.336 | 0.500 |
| 100 | 0.329 | 0.308 | **0.361 (PEAK)** | 0.606 |
| 200 | **0.345 (PEAK)** | 0.493 | 0.256 | 1.283 |
| 400 | 0.293 | 0.726 | 0.059 | 1.671 |
| 800 | 0.236 | 0.749 | 0.007 | 0.273 |
| 1600 | 0.181 | 0.660 | 0.004 | 0.019 |
| 3200 | **0.123** (below random!) | 0.494 | **0.004** | **0.000** |

**Neither rule has a useful fixed point.** Fixed-sign **never converges** (drift stays
0.49–0.75) and decays *through* the random floor. BCM **converges** (drift → 0.000) — to
**annihilation** (0.004, zero structure). One never settles; the other settles on
nothing.

## THE SCAFFOLD IS A TRANSIENT — and phase 1 = 200 steps was its PEAK, by luck

Every result in this arc was measured at the top of a transient. That is the complete
explanation of all nine attempts:

- `dark` = **continued** wave exposure ⇒ pushed past the peak ⇒ degrades ⇒ **always
  worst**, under every rule and every dark-arm model. Not a drive/schedule/threshold
  problem at all.
- `normal` / `sutured` = waves CEASE ⇒ wave-driven decay HALTS ⇒ both stay near the
  peak ⇒ both beat `dark`. Hence H1b inverting in attempts 7 and 9, and going null in 8.

## THIS RETRACTS THE INTERPRETATION OF "VISION REFINES"

The replicated result (7: +0.024 p<0.0001; 8: +0.011; 9: +0.143) is a real
*comparison*, but its **reading was wrong**. `normal` beats `dark` mostly because it
**stops the wave-driven decay**, not because vision refines anything. The evidence is
already in the arms:

| attempt 7 arm | score | vs frozen (0.323) |
|---|---|---|
| sutured (waves cease, noise) | 0.328 | +0.005 ≈ frozen ⇒ **halting decay is the whole effect** |
| normal (waves cease, vision) | 0.333 | +0.010 |

**Stopping the waves buys ≈ +0.019** (dark 0.309 → frozen 0.323 → sutured 0.328). The
genuine vision-over-noise refinement is only **normal − sutured ≈ +0.005** — an order of
magnitude smaller than the headline, and never tested on its own. **"Vision refines the
wave scaffold" is retracted as an interpretation.** What is established is narrower and
duller: *ceasing waves halts a decay, and vision may add a little on top of that.*

## Honest final status of the experience rung

**NOT BUILT.** Nine pre-registered attempts, one root cause, now measured rather than
inferred: **the learning rule has no stable fixed point on its own input
distribution.** Everything downstream — the deprivation arms, the inverted asymmetry,
rung 1's confounded headline, the "vision refines" reading — follows from that.

**The next work is a rule with a stable fixed point** (does anisotropy plateau and drift
→ 0 at NON-zero structure?), measured on waves alone before ANY experience arm is run
again. Candidate directions: weight decay/normalisation that does not collapse (BCM's
theta converges but to zero), a lower learning rate with a longer horizon, or a rule
whose fixed point is the input's principal structure (Oja converges by construction —
and Oja is already in the tree, in `vision_growth`). **No experience comparison is
meaningful until the scaffold is a stable state rather than a transient.**

---

# OJA CONVERGENCE (run 2026-07-16) — **THE SCAFFOLD IS NOW A STABLE STATE**

`oja_learn` added to the wave scaffold's Synapse population (the Oja already in the
tree, `vision_growth`'s `vg_learn_kernel_oja`, operates on Kernel weight-vectors via
ConvFaculty — a different architecture). `w <- w(1 - eta*y^2) + eta*y*x`, y = the post
unit's own drive, x = 1 iff the pre burst in-window. Local; winner-take-all retained so
the population differentiates. Homeostasis is gated OFF under `oja=1` (Oja
self-normalises; `bh_scale` would fight the decay term). `oja=0` default ⇒ every
committed result reproduces.

Waves only, n=8 seeds, same protocol as the fixed-sign/BCM convergence run:

| steps | OJA η=5e-4 | drift | OJA η=1e-4 | drift | OJA η=2e-5 | drift |
|---|---|---|---|---|---|---|
| 0 | 0.148 | — | 0.148 | — | 0.148 | — |
| 400 | 0.326 | 0.370 | 0.164 | 0.405 | 0.148 | 0.279 |
| 1600 | 0.365 | 0.225 | 0.278 | 0.402 | 0.150 | 0.401 |
| 3200 | **0.368** | **0.107** | 0.328 | 0.172 | 0.168 | 0.241 |

**0/80 NaN units at every η.** (η=2e-3 DIVERGED to NaN — the L0 failure exactly: Oja is
stable only while `eta*y^2 < 1`, and with up to 49 bursting inputs y is large. The
stable regime is η ≈ 5e-4.)

## The three rules side by side, on identical input

| rule | peak | @3200 | drift@3200 | verdict |
|---|---|---|---|---|
| fixed-sign (Butts) | 0.345 @200 | **0.123** (below random) | 0.494 | never converges; decays through the floor |
| BCM | 0.361 @100 | **0.004** | 0.000 | converges — **to annihilation** |
| **Oja η=5e-4** | — | **0.368** (still plateauing) | **0.107 ↓** | **converges to NON-ZERO structure** |

**Oja's plateau (0.368) EXCEEDS fixed-sign's transient PEAK (0.345)** — and it is a
STATE, not a moment. Anisotropy rises monotonically and flattens while drift falls
monotonically toward 0. This is exactly the property the convergence measurement said
was missing, and it is the direct consequence of Oja's decay term being a contraction
toward the input's leading principal component.

## What this unblocks

The nine failed experience attempts are now fully explained AND the blocker is removed:
they compared arms on a **transient** whose peak my phase-1 (200 steps) happened to sit
on, so any arm that kept learning was pushed past it and `dark` could never win. On an
Oja scaffold there is no peak to fall off — continued exposure to the formative input
**stabilises** the representation, as development requires.

**The experience arms are now worth re-running, and only now.** That is a fresh
pre-registration (normal/dark/sutured on an Oja scaffold, `dark` = waves continuing,
equal duration) and is NOT run here.

**Honest scope:** this is a diagnostic measurement of dynamics (n=8), not a
pre-registered hypothesis test, and drift at 3200 is 0.107 — falling, not yet 0. The
claim is "converges toward non-zero structure", not "has converged". η=5e-4 is a
measured stable regime, not a tuned optimum.

---

# ATTEMPT 10 — pre-registration: EXPERIENCE ARMS ON THE OJA SCAFFOLD (written BEFORE the run)

## Why this is the first meaningful experience test

All nine prior attempts compared arms on a **transient** whose peak my 200-step phase-1
sat on, so any arm that kept learning fell off it and `dark` could never win. On an Oja
scaffold there is no peak to fall off: anisotropy plateaus at 0.368 and drift falls
toward 0 (measured). **The scaffold is now a STATE.**

**Phase 1 = 1600 steps** (measured: 0.365, ≈99% of the 3200-step plateau) so every arm
enters phase 2 at the fixed point, not mid-transient. `oja=1`, η=5e-4 (the measured
stable regime; η=2e-3 diverges).

## Design

Phase 1 (1600 steps, ALL arms bit-identical): waves only, Oja.
Phase 2 (400 steps, ALL arms driven, equal duration):

| arm | phase 2 | biology |
|---|---|---|
| `dark` | waves continue | dark-reared |
| `normal` | real video, waves cease | normal rearing |
| `sutured` | noise, waves cease | lid suture |

## PREDICTION, STATED IN ADVANCE

**H1b (sutured < dark): I predict PASS — and for the first time there is a MECHANISM.**
Oja converges to the leading principal component *of whatever it is shown*. Noise has no
structure, so its fixed point is unstructured: the noise arm should be **pulled off** the
wave-learned structure and degrade. This is exactly the active degradation the
fixed-sign rule could not produce (attempts 7–8: noise INERT, ≈ frozen) — there, random
potentiation averaged out and the scaffold survived; under Oja the input's statistics
*define* the attractor, so unstructured input actively dissolves structure.

**H1a (normal > dark): genuinely uncertain.** It requires natural video's leading
principal component to be MORE anisotropic than the waves' — plausible (real scenes carry
oriented structure) but untested, and 16×16 cartoon frames are mostly flat.

**If both pass, the experience rung is BUILT: normal > dark > sutured**, the research's
3-0 ordering, on a stable scaffold with the correct control at equal duration.

## Hypotheses / n / seeds / statistic

- **H1a:** `d_normal = anis(normal) − anis(dark)`, two-sided, predicted **> 0**.
- **H1b:** `d_sutured = anis(sutured) − anis(dark)`, two-sided, predicted **< 0**.

**BUILT** iff both (Bonferroni α=0.025 each). Paired within seed; **SEED is the unit of
analysis**; sign-flip 20,000 perms; bootstrap CIs. **n = 100 FIXED IN ADVANCE**
(prior per-seed SD 0.06–0.11 ⇒ ≥80% power for |δ|≈0.03). **Seeds 1900–1999** — never used.

**Exactly two hypothesis tests. No sweeps, no re-runs.**

## ATTEMPT 10 — OUTCOME (run exactly as specified)

```
d_normal  (normal - dark):  +0.0385   95% CI [+0.0320, +0.0451]   p < 0.0001   PASS
d_sutured (sutured - dark): -0.1474   95% CI [-0.1546, -0.1400]   p < 0.0001   PASS
n = 100 seeds (1900-1999).   arms: dark 0.363 | normal 0.402 | sutured 0.216
```

# **DECISION: *** BUILT *** — normal > dark > sutured.**

**The experience rung is built.** Both co-primary hypotheses pass the conjunctive gate
(Bonferroni α=0.025 each), giving the verified research's **3-0 biological ordering**
(normal ≥ dark > sutured) on a **stable scaffold**, with the **correct control**, at
**equal learning duration**, on **fresh seeds**, from a **pre-registration written
before the run**.

| arm | anisotropy | reading |
|---|---|---|
| `normal` (video) | **0.402** | experience REFINES beyond the wave fixed point |
| `dark` (waves continue) | **0.363** | the stable scaffold — holds, does not decay |
| `sutured` (noise) | **0.216** | unstructured drive ACTIVELY DISSOLVES structure |

## The mechanism — predicted in advance, and it is what delivered

The pre-registration predicted H1b would pass *"and for the first time there is a
MECHANISM: Oja converges to the leading principal component OF WHATEVER IT IS SHOWN.
Noise has no structure, so its fixed point is unstructured: the noise arm should be
PULLED OFF the wave-learned structure and degrade."* Measured: **−0.147** — by far the
largest deprivation effect in the whole arc, and the first that is *active destruction*
rather than an artifact. Under fixed-sign, noise was INERT (≈ frozen) because random
potentiation averages out; under Oja the input's statistics **define the attractor**, so
unstructured input dissolves structure. **That is the White/Coppola/Fitzpatrick
lid-suture asymmetry, earned on the right mechanism** — not rung 1's confounded version
(which measured noise disrupting a *running wave program*).

H1a was flagged "genuinely uncertain" — it required natural video's leading PC to be
more anisotropic than the waves'. It is: **+0.039, p<0.0001.**

## What made the difference — a stable fixed point, nothing else

Nine attempts failed on a transient. `dark` here is **0.363**: it holds at the Oja fixed
point instead of decaying (fixed-sign's dark fell to 0.309; BCM's to 0.050). Once the
scaffold is a STATE, every arm measures what experience *does to it* rather than where
it happens to sit on a decay curve — and the biology appears immediately, with no
further tuning.

## Honest scope

- **Not** orientation *maps*: 0.402 vs an ideal Gabor's 0.867 — refined structure, not
  Gabors, and no map topography is measured.
- The verified research **refuted 0-3** the Hebbian-vs-sparsity question; this shows
  *this* rule on *this* scaffold reproduces the deprivation ordering, and licenses
  nothing about which biological mechanism is correct.
- η=5e-4 is a measured stable regime (η=2e-3 diverges), not a tuned optimum.
- Rung 1's confounded headline stays retracted; this result **replaces** it on a sound
  mechanism rather than rehabilitating it.

---

# RE-RUN ON THE REAL SOURCE — pre-registration (written 2026-07-17 BEFORE the run)

## Why this exists

Attempt 10 (the BUILT result) **has no committed runner**, and its `normal` arm's
stimulus was never cached. A reconstruction (`scripts/w0_part5_rung2.py`) substituted
**BSDS300 crops** because the Sesame Street corpus was reported *"absent from this
machine's Jellyfin catalogue (137 items)"*.

**That absence claim is FALSE and is retracted.** Verified live today, and the dead
instrument reproduced on purpose:

- `catalog()` returns **137 items** — the RIGHT catalogue, the count was correct;
- `Sesame Street` **IS in it**: Series `a6152b4a3b12f70779d1cb6364fa97e6`, **78 episodes**;
- **root cause:** `catalog()` returns dicts keyed lowercase `name`/`type`/`id`; the
  absence check read **`Name`** (capital). `.get('Name','')` returns `''` and **cannot
  raise**, so all 137 items silently missed. Reproduced here side-by-side: the lowercase
  key finds 2 Sesame hits, the capital key finds **0**.
- frames decode today: (8,16,16) float32, range 0.089–0.830, **adjacent-frame
  correlation 0.9904**.

**Why the substitution mattered (and is not repeated):** `bsds_crops` draws each frame as
an *independent random crop from a randomly chosen photograph* — spatially natural but
**temporally DECORRELATED**. Rung 2 is about spatioTEMPORAL structure. That arm landed at
**0.288**, between video (0.402) and noise (0.216) — exactly where a temporally shuffled
stream predicts. The previous agent **correctly refused** to score it as a refutation of
H1a and named it as its own confound. That judgement stands; only its premise was wrong.

## The measure, horizon, statistic — UNCHANGED from attempt 10

Phase 1 = **1600** steps (waves only, `oja=1`, `oja_eta=5e-4`, `propagate=1`, ignite every
5th step), all arms bit-identical. Phase 2 = **400** steps, all arms driven, equal
duration:

| arm | phase 2 |
|---|---|
| `dark` | waves continue |
| `normal` | real Sesame Street video, waves cease |
| `sutured` | uniform noise, waves cease |

Statistic: mean `orientation_selectivity` over the run's **10 units** (`rf=7`, DC init —
the committed default). **SEED is the unit of analysis.** Sign-flip 20,000 perms;
bootstrap CIs; paired within seed. `d_normal = anis(normal) − anis(dark)`;
`d_sutured = anis(sutured) − anis(dark)`. Two-sided, Bonferroni α=0.025 each.
**BUILT** iff both pass with the predicted signs (`d_normal > 0`, `d_sutured < 0`).

## Seeds — DECLARED BEFORE THE RUN

- **Block A — EXACT REPRODUCTION: seeds 1900–1999** (attempt 10's OWN confirmatory
  block, n=100). This is the *only* legitimate use of a burned block: reproducing the
  numbers it produced. Burns nothing new. This is the arm compared against 0.402 / 0.363
  / 0.216 and `d_sutured` −0.1474.
- **Block B — FRESH CONFIRMATION: seeds 9200–9299** (n=100), **claimed here, previously
  FREE and clean** (`VISION_PROTOCOL.md` ledger: *"2100+, 4300+, 6100+, 9200+, 13000+ —
  FREE"*). 12000–12999 was NOT taken (pre-visual holds it); 13000–13999 was NOT taken
  (rung 8 holds it). Block B tests whether the ordering survives seeds attempt 10 never
  touched.

**Exactly the two hypothesis tests, on each block. No sweeps, no re-runs.**

## DEVIATIONS, declared in advance (the runner is gone; these are unavoidable)

1. **Per-seed video window.** The prereg's prose does not say how frames were assigned
   across seeds, and the runner is gone. Each seed draws a **contiguous 400-frame window**
   from a per-seed episode (`seed % 10`) at a per-seed start offset. Contiguity preserves
   the temporal correlation that IS the arm's content; per-seed variation preserves the
   independence that "SEED is the unit of analysis" requires. (The reconstruction varied
   its crops per seed the same way, via `bsds_crops(seed=seed)`.)
2. **Cached stimulus, pinned.** Frames come from a committed cache built at
   `start_s=300`, `every=6`, `size=16` from **10 pinned episode ids**, content-hashed, so
   a third party re-runs without a live server.
3. **Unit count / RF** are read from the prereg's prose ("that run's 10 units"), as the
   reconstruction did.

**Because of (1) the `normal` arm is a REPRODUCTION OF THE DESIGN, not necessarily
bit-identical to attempt 10.** `dark` and `sutured` use no video and are therefore
bit-exact reproductions — they are the **harness fidelity check**: if they land on 0.363
and 0.216, the harness is faithful and `normal` is being read on a sound instrument.

## PREDICTION, STATED IN ADVANCE

**I predict H1b (sutured < dark) reproduces**, at ≈ −0.147: it uses no video, and its
mechanism (Oja's attractor is the leading PC of whatever it is shown; noise has no
structure) is untouched by the source question.

**I predict H1a (normal > dark) reproduces, direction PASS, magnitude uncertain.** The
reconstruction's 0.288 is evidence *for* this: temporally decorrelated natural images
scored BELOW `dark`, and the one property the substitution destroyed is the one real
video restores. But attempt 10's own prereg called H1a *"genuinely uncertain"* and noted
*"16×16 cartoon frames are mostly flat"* — so I hold this loosely.

**Provisos that would break my prediction:** (a) if the per-seed window (deviation 1)
differs from attempt 10's assignment, `normal`'s variance — and so its CI, not its sign —
moves; (b) if attempt 10 drew from a different episode range or `start_s`, the mean can
move without the ordering moving; (c) Sesame Street is high-contrast, low-detail
animation — if 0.402 depended on a specific segment's oriented structure, a different
window reproduces the ordering but not the magnitude.

**A `normal` that does NOT reproduce is a genuine negative and will be reported as one,
with the confound analysis — not tuned toward 0.402.** No parameter is free: η, phase
lengths, unit count, RF, and the measure are all frozen by attempt 10.

## RE-RUN — OUTCOME (run exactly as specified, 2026-07-17)

```
engine 95167c01b7b3 [shared build — Rust source identical]   commit d168e0be83
stimulus (10,600,16,16) sha256[:16]=4bc2c256fb55bc3d  Sesame Street, 10 pinned episodes

BLOCK A — seeds 1900-1999 (EXACT REPRODUCTION, attempt 10's own block)
  arms: dark 0.363 | normal 0.317 | sutured 0.217
  d_normal  (normal - dark)   -0.0463  95% CI [-0.0560, -0.0366]  p < 0.0001   FAIL (sign REVERSED)
  d_sutured (sutured - dark)  -0.1458  95% CI [-0.1523, -0.1394]  p < 0.0001   PASS

BLOCK B — seeds 9200-9299 (FRESH CONFIRMATION)
  arms: dark 0.361 | normal 0.316 | sutured 0.220
  d_normal  (normal - dark)   -0.0455  95% CI [-0.0542, -0.0369]  p < 0.0001   FAIL (sign REVERSED)
  d_sutured (sutured - dark)  -0.1413  95% CI [-0.1482, -0.1345]  p < 0.0001   PASS
```

# **DECISION: FAIL (conjunction) — H1a does NOT reproduce on the REAL source.**

| arm | pre-registered | re-run (block A) | verdict |
|---|---|---|---|
| `dark` (waves continue) | 0.363 | **0.363** | **EXACT** |
| `sutured` (noise) | 0.216 (d −0.1474) | **0.217** (d −0.1458) | **REPRODUCES** |
| `normal` (real video) | **0.402** (d +0.0385) | **0.317** (d −0.0463) | **DOES NOT REPRODUCE — sign REVERSED** |

**The harness is validated and the negative is real.** The two arms that use no video
reproduce attempt 10 to three decimals — `dark` **exactly**, `sutured` within 0.001 —
so the instrument reading `normal` is sound. On the real Sesame Street source `normal`
lands at **0.317, BELOW `dark`**: not merely short of +0.039 but **reversed**, p<0.0001,
CI excluding 0 in the wrong direction, **replicated on 100 fresh seeds** (block B,
−0.0455). Rung 2's verdict is **conjunctive**, so **rung 2 does not currently reproduce
as BUILT.**

**H1b survives untouched** (−0.146/−0.141): noise actively dissolves structure, the
largest deprivation effect in the arc. That mechanism never depended on the video source.

## THE CAUSE IS MEASURED, AND IT IS THE STIMULUS CONSTRUCTION — not the corpus

The `normal` arm's input was built with `episode_frames(size=16)` — a **whole-frame
downsample** of a 1080p frame to 16×16, so each pixel averages ~120×67 source pixels.
The prereg's own words ("**16×16 cartoon frames** are mostly flat") point at exactly
this, and it is what the supervisor's verification used. **Descriptive measurement of
the STIMULUS ONLY (no arm re-run), binarized at its own median as `drive()` does:**

| stimulus | anisotropy |
|---|---|
| whole-frame 16×16 downsample (**what this run used**) | **0.2136** |
| uniform noise (the `sutured` arm) | 0.0775 |
| native-resolution 16×16 crops (`episode_crops`) | **0.5769** |

**Oja converges to the leading PC of whatever it is shown.** An input whose own
anisotropy is **0.21** cannot pull the weights above a wave scaffold sitting at
**0.363** — it pulls them *down*, to 0.317, which is precisely what was measured. An
input at **0.58** would pull them *up*. **The two constructions differ by 2.7× in the
exact quantity the rule converges to**, and that is a sufficient mechanism for both this
negative and attempt 10's 0.402.

**The tree already said so, in three places, before this run:**

- `vision_corpus.episode_crops`'s own docstring: crops *"(never a whole-frame
  downsample) so the high-spatial-frequency statistics kernel learning depends on
  survive"*;
- `VISION_DEVELOPMENT_ARC.md`: the vision curriculum feeds on Sesame Street **crops**
  (*"~10% of sampled Sesame Street crops (29/288) carry enough structure to learn
  from"*) — the arc's own vision work uses the crop path, not the downsample path;
- attempt 10's prereg flagged *"16×16 cartoon frames are mostly flat"* as H1a's stated
  risk — and on the downsample construction that risk is simply **realised**.

**This is NOT scored as a refutation of attempt 10, and the difference matters.**
Attempt 10's runner was **never committed to git** (verified: `git log --all -S"sutured"`
returns only the research-grounding script, the w0 reconstruction, and this re-run's
files). **So which construction attempt 10 used is UNRECOVERABLE from the tree.** Its
prose supports the downsample reading; its corpus module and its own curriculum support
the crop reading. **The honest verdict: rung 2's headline cannot be attributed, because
the artifact that would attribute it does not exist.** That is the finding — and it is
exactly why an uncommitted runner is a defect rather than a formality.

**The crop construction is NOT tested here.** Running it would be a second test of H1a
to rescue a failed gate — PROTOCOL §5 (never rescue a failed gate by changing the
instrument) and §3.6 (exactly the listed tests; no sweeps, no re-runs). It is named as
the leading candidate and needs its **own prospective pre-registration**, whose result
would be interpretable *because this one was run and reported first*.

## What the BSDS reconstruction got right, and what it got wrong

The reconstruction reported `normal` **0.288** and refused to score it as a refutation of
H1a, naming temporal decorrelation as its own confound. **That refusal was correct.** But
the diagnosis was incomplete: real, temporally-correlated video (adjacent-frame corr
0.906) moves the arm only **0.288 → 0.317**, still **far below `dark`**. Temporal
correlation was worth ~+0.03 and was **never** what separated 0.402 from 0.363.
**Restoring the real corpus did not restore the result** — so the missing source was a
smaller part of the hazard than it looked, and the stimulus *construction* was the
larger part all along. The corpus claim was false; the confound claim was true but not
load-bearing.

## MY PREDICTION WAS WRONG, and the proviso that broke is not one I wrote

I predicted **H1a reproduces, direction PASS**. It **failed, with the sign reversed** —
and I cited the reconstruction's 0.288 as evidence *for* my prediction, which was the
error: I read 0.288 as "temporally decorrelated, therefore low" when 0.288 was mostly
telling me *the downsampled stimulus is flat*, the same fact my own run then measured.
**H1b I predicted correctly, at ≈−0.147 (measured −0.1458).**

My provisos named the window, the episode, and `start_s` — every one of them a
*sampling* choice **within** a construction. **The fork that mattered was the
construction itself** (whole-frame downsample vs native-resolution crop), and I did not
name it because I took the prereg's "16×16 cartoon frames" as unambiguous. It is not:
the same tree documents a crop path whose stimulus scores 2.7× higher on the one axis
that decides this rung. **A proviso that breaks tells you what you didn't understand
(§3.7): I did not understand that "16×16 frames" names a RESOLUTION, not a
CONSTRUCTION** — and the arc's headline turns on the difference.
