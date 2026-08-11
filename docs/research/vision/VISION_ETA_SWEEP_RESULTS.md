# ETA-SWEEP — RESULTS: **THE 2×2 IS EMPTY.** 8D's tension SURVIVES the settling loop.

*The predicted NEGATIVE, and it is the valuable one (§7): with GCAL's own
orientation mechanism — a settling loop, now terminating via cycle detection —
running under the developmental learning rule, there is STILL no η at which the
rule is both convergent and load-bearing, and whatever OSI appears carries a
coin-flip angle. The cortex line through this mechanism is exhausted with a
diagnosed reason: the input-covariance eigenspectrum, not a tuning failure.*

**Engine `559d7f380c17`** @ `<this worktree>/runners/dsl/python/substrate_rs/_native.abi3.so`
— **shared build from the canonical tree, Rust source byte-identical** (this
rung adds NO Rust; provenance gate `own`/`shared` verdict = shared). Base commit
`69beada4` (the fixpoint-predicate tip). **NO Rust, NO seed edited, NO new
constant.**

**PRE-REGISTRATION `VISION_ETA_SWEEP_PREREG.md` COMMITTED AT `e1523d6c`,
2026-07-17T23:12:55Z. RUN STARTED 23:13:04Z — 9 seconds later, checkable in
git.** **CONFIRMATORY SEEDS 24000–24023 (n=24), DECLARED IN ADVANCE.**
24024–24999 remain clean; 12000–23999 untouched.

---

## 0. THE ONE-LINE OPT-IN, AND ITS INERTNESS (§9, §11.4)

`domains/wave_world.step` now threads
`detect_cycles=getattr(self,"detect_cycles",False)` into its single
`s.tick(200_000)` — one functional line, OFF by default. Proven inert **two
ways**, on a dithering settling sheet:

- **DEFAULT (attribute unset) ≡ explicit `detect_cycles=False`:**
  `max|Δact| = max|Δw| = 0.000e+00`.
- **OFF ≡ ON (SAME sheet, not an approximation):** `max|Δact| = max|Δw| =
  0.000e+00` — **the learning trajectory is UNAFFECTED by termination
  semantics**; detection only makes the settling terminate (6 steps: 8.0s →
  0.05s, ~160×; per developmental step ~10-40 applications vs the 200 000 cap).

No default changed. The opt-in is what makes the sweep tractable at 24 seeds ×
5 η × (3000 develop + 3200 train) steps — without it every step burns the cap.

## 1. THE η SWEEP — THE 8D 2×2 (n=24; unit = SEED)

Sheet: n_side=3 (9 cortical cells), connectivity=8 (the non-bipartite sheet that
settles, ρ<1); settling ON during development (settle=1.0 + detect_cycles), OFF
(feedforward, 8D's CALIBRATED probe) at readout.

| η | Δ_OSI | 95% CI | rel ‖w‖ move | drift first→last | converged? | load-bearing? | n_dead |
|---|---|---|---|---|---|---|---|
| 1e-4 | +0.0037 | [−0.0185, +0.0259] | 0.009 | 0.0009→0.0008 | no (flat) | **no** | 0 |
| 5e-4 | +0.0147 | [−0.0032, +0.0326] | 0.047 | 0.0042→0.0042 | no (flat) | **no** | 0 |
| 1e-3 | +0.0084 | [−0.0112, +0.0280] | 0.098 | 0.0084→0.0087 | no (flat) | **no** | 0 |
| 2e-3 | **−0.0369** | [−0.0628, −0.0109] | 0.213 | 0.0171→0.0194 | no (rises) | **no** | 0 |
| 5e-3 | **−0.0668** | [−0.0885, −0.0450] | 0.575 | 0.0445→0.0474 | no (high) | **no** | 0 |

**NO η is BOTH convergent AND load-bearing.** The two failure modes 8D named are
both present, now WITH settling:

- **Low η (1e-4 / 5e-4 / 1e-3) — VACUOUS.** The weights barely move (‖w‖ moves
  0.9–9.8%), drift is flat and tiny (~1e-3, does not decay because there is
  nothing to decay — the rule is near-frozen), and Δ_OSI's CI includes 0, far
  below SESOI = 0.0595. Converged-to-init, not load-bearing.
- **High η (2e-3 / 5e-3) — RUNS ON AND HARMS.** The weights move a lot (21–58%),
  but drift does NOT fall (it plateaus at ~0.019 / ~0.047 or rises — the rule
  never settles in 3200 steps), AND **Δ_OSI is NEGATIVE with a CI excluding 0**:
  training makes cells LESS orientation-selective (D_OSI<0 in 17/24 seeds at
  2e-3, 20/24 at 5e-3). This is the eigenspectrum realised: E[xxᵀ]'s leading
  eigenvector is a **DC BLOB** (wave-isotropy rung, OI 0.0855), and Oja converges
  toward the leading PC — so more learning drives the RF toward a blob and
  DESTROYS selectivity.

**`n_dead = 0` on ALL 144 arms** (24 floor + 24×5 trained) — every arm ALIVE, so
the floor is not death (§1 clause 4; §1.1's silent-arm trap avoided and measured).
Floor OSI mean 0.302, range [0.248, 0.391], measured IN-RUN per seed.

## 2. MAP STRUCTURE vs PER-CELL OSI — COIN FLIP AT EVERY η

The control is the **UNTRAINED FLOOR**, not a pool-shuffle null (the pilot found
the pool-null is FOOLED — see §2 of the prereg). Floor: across-seed R **0.582**,
neighbour-similarity −0.058, global-bias 0.345.

| η | neighbour-sim (trained − floor), 95% CI | across-seed R: trained vs floor | verdict |
|---|---|---|---|
| 1e-4 | +0.032 [−0.100, +0.165] | 0.531 vs 0.582 | coin-flip |
| 5e-4 | +0.018 [−0.097, +0.134] | 0.497 vs 0.582 | coin-flip |
| 1e-3 | +0.107 [−0.039, +0.253] | 0.523 vs 0.582 | coin-flip |
| 2e-3 | +0.059 [−0.051, +0.170] | 0.467 vs 0.582 | coin-flip |
| 5e-3 | +0.011 [−0.087, +0.108] | 0.571 vs 0.582 | coin-flip |

**Training adds NO structure over the untrained floor at any η.** Neighbour-
similarity gain CI includes 0 everywhere (no spatial organisation); trained
across-seed R never exceeds the floor's 0.582 (learning does not make preferred
orientation more position-reproducible than the probe already does *without any
learning*). The apparent across-seed reproducibility is the probe's argmax-tie
aliasing (8D §4 — F0 over K=16 phases ties EXACTLY at 30/150°, 60/120° on the
integer grid, so preferred angle is a function of cell POSITION), present in the
untrained arm at the same magnitude (R 0.582) and NOT a learned orientation map.
A field of high-OSI cells with random angles and a pinwheel map both give high
mean OSI; this is the former.

## 3. VERDICT — ENGINEERING, NOT PARADIGM

**Plainly: this line is ENGINEERING, not a paradigm claim** — building a V1 from
a settling loop + a Hebbian/Oja rule is matching an existing model (GCAL, which
already works). And in this substrate the engineering DOES NOT SUCCEED: the 2×2
is empty and the map is a coin flip. **The settling loop — GCAL's own orientation
mechanism — does NOT rescue this rule class here.** The cortex line through this
mechanism is exhausted with a **diagnosed** reason: the formative input's
covariance has a DC-blob leading eigenvector and a NEAR-DEGENERATE oriented
eigenpair (λ2/λ3 = 1.0907, wave-isotropy rung), so Oja drives the RF toward a
blob (killing OSI at high η) or barely moves (vacuous at low η), and the angle it
lands on is a lottery. **The settling loop composes what the input statistics
hold; it does not conjure a leading oriented PC they lack** — the sd-loop rung's
independent bound, arrived at from the linear-algebra side.

**The paradigm claim (dynamic quantization / the sd loop) is UNTOUCHED** by this
negative, exactly as the sd-loop rung's own negative ("the loop composes what it
holds; it does not discover what it lacks") stands untouched by it.

### What the winning η would have fallen out of — there is no winner, so nothing

No η is a committed default here: η was a SWEPT IV (§4/§13), and the sweep
returns NO value that is both convergent and load-bearing, so there is no
constant to justify and none is committed. Had a single η won, §13 would demand
it fall out of something (a noise floor, a dynamic range) or be named a knob;
the question does not arise.

## 4. THE ρ→1 CEILING, RESTATED (§8)

Ran at **n_side = 3 (9 cells) BY NECESSITY**: ρ(M)→1 as the sheet grows
(0.45→0.87 over n_side 3→6, re-verified by the cycle-detect gate's
`test_rho_ceiling_is_not_fixed_by_this`), so a GCAL-scale sheet settles
arbitrarily slowly regardless of termination semantics. **This negative at small
n does NOT clear that ceiling** — it licenses only: "at n_side=3, with the
settling loop terminating, no η in {1e-4…5e-3} is both convergent and
load-bearing, and the learned map is a coin flip." It does NOT license a claim
about a GCAL-scale sheet, where the settling itself does not terminate tractably.
GCAL asserts convergence but shows "(data not shown)".

## 5. SCOPE / WHAT IS NOT SHOWN (§8)

- **OSI probed feedforward** (settle=0) with 8D's CALIBRATED instrument (IDEAL
  0.9989, FLOOR 0.2691). A settled-probe OSI (uncalibrated here) is NOT measured;
  if lateral settling sharpens tuning, feedforward OSI is a conservative lower
  bound on selectivity MAGNITUDE — but the STRUCTURE (angle) verdict is robust to
  magnitude: sharpening a tuning curve does not fix a random preferred angle, and
  the negative on load-bearing is corroborated by the ‖w‖-and-drift trajectory,
  which is probe-independent.
- A "coin flip" is consistent with BOTH the wave-isotropy eigenspectrum
  degeneracy (λ2/λ3=1.09) AND the probe's argmax-tie lottery (8D §4); this design
  does not separate them, but a genuinely STRUCTURED map would produce real
  tuning-curve gaps (no ties) and clear the floor control regardless — it did not.
- This licenses nothing about which biological mechanism is correct; it is a
  statement about THIS learning-rule-on-settled-sheet in THIS substrate at THIS
  scale.

## 6. §9 BYTE-IDENTITY / GATES / SEED BLOCK

- **§9 opt-in inertness:** DEFAULT ≡ OFF ≡ ON, `max|Δact| = max|Δw| = 0.0` (§0).
- **Cycle-detect gate** `tests/test_cycle_detect_migrated.py`: **10/10**
  (byte-identity, off-by-default, the dither terminates, degree-ε refuted, ρ
  ceiling not fixed) — run with the provenance gate, combined **17 passed / 0
  failed** (exit 0).
- **Provenance gate** `tests/test_engine_provenance_migrated.py`: **7/7**
  (engine `own`/`shared`, source-identical).
- **§9 named vision bench** `scripts/rung7_vision_bench.sh` (WITH `data/`
  symlinked, §10.2): **200 passed / 0 failed** (131.7s) — the committed baseline,
  unchanged. (Without `data/` it would be 190/10, the 10 BSDS300-gated skips
  §10.2 documents.)
- **Seed block:** confirmatory 24000–24023 (n=24) declared in the prereg BEFORE
  the run; pilot on burned 0–7; every deciding byte-identity/timing check on
  already-burned seed 0. 12000–23999 untouched.
- Engine `559d7f380c17`, shared build, Rust source identical to canonical.
