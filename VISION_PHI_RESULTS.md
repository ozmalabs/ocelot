# DOES THE SUBSTRATE SEE PHI? — RESULTS

Pre-registration `VISION_PHI_PREREG.md`, committed **`8edacf62`** before any phi
number. Branch **`worktree-agent-af6f51636362ac138`** — reporting the name I
actually see; no `gamma-substrate/phi` name exists.

Engine **`68860d0b0f78`** (`own` build, `scripts/engine_build.sh`), **no Rust
change**. Provenance gate run as its **own step before any number**:
`tests/test_engine_provenance_migrated.py` **7 passed**. Oracle
`scripts/rung7_vision_bench.sh`: **212 passed, 10 skipped, exit 0** — this tree
has no `data/`, the documented no-corpus case (222 is the *collected* count).

Seeds **86000–86999**, measured. Corpora pinned and asserted at run time:
**C1** `08630d4b…`, **C2** `119eca43…`. Four other rungs ran concurrently;
**every quantity below is COUNTED or EXACT — no wall-clock number is reported
or claimed.**

---

## THE HEADLINE, IN SIX LINES

**The substrate does NOT see phi. It sees pixel overlap.** At every one of the
three correspondence mechanisms in this tree, "one thing moved" is returned iff
the thing's two positions **overlap within a fixed aperture**, and the aperture
is a length in pixels.

**Registered outcome 3: a motion response with the WRONG PARAMETER
DEPENDENCE** — a different mechanism wearing phi's clothes.

**The ISI dependence is not merely different; it is INVERTED.** Human phi
*requires* a temporal gap and is worst at simultaneity. Every level here is
**maximal at ISI = 0 and identically dead at every ISI ≥ 1** — 30 of 30
conditions.

**And the C1 re-reading REFUTES the hypothesis that prompted this rung, while
also refuting the claim it was aimed at.** The 0.8% is **not** explained by the
sensor missing phi (widening the aperture 8× converts **0.06%** of the discarded
change). But the motion rung's stated reason — *"consecutive frames are very
often identical"* — is **false as measured: 0 of 40 C1 pairs are identical.**

**All five registered predictions were confirmed, three of them exactly**, and
**one proviso broke informatively** (a saturation band the registration missed).

**The §13 finding is the one the pre-registration expected: the substrate's
correspondence range is a SUPPLIED NUMBER, not one that falls out.**

---

## 1 — M1: WHAT THE SENSOR REPORTS ON PHI, RAW

`S = 8` px, ISI = 0, one 4×4 dot. **Raw output, not an interpretation of it.**

| background | v at SOURCE cell | v at TARGET cell | non-zero cells (of 324) | distinct vectors | verdict |
|---|---|---|---|---|---|
| **uniform** | **(0.0, 0.0)** | (−4.0, 0.0) | **1** | `{(-4,0): 1}` | **TWO EVENTS** |
| **textured** | (−3.0, −1.0) | (−1.0, −3.0) | **2** | `{(-3,-1): 1, (-1,-3): 1}` | **OTHER** |

**On a uniform field the sensor's answer to "a dot was here, now it is there" is
`(0, 0)` — literally no motion.** The whole 324-cell field carries **one**
non-zero vector, and it points the wrong way `(−4, 0)`: a spurious vertical
displacement at the cell where the dot *appeared*, which is the block matcher
finding a partial edge match, not a correspondence.

**On a textured field it is worse and quieter**: two non-zero vectors, neither
related to the true displacement, both artefacts of background competition. This
is the ~11% per-block error floor (`VISION_MOTION_OBJECTS_RESULTS.md` §0.2)
showing up as a *confident wrong answer* rather than an abstention.

---

## 2 — M2: SEPARATION DEPENDENCE, AND THE PROVISO THAT BROKE

### L1 — the motion sensor (the layer the motion rung consumed)

| S (px) | 1 | 2 | 3 | **4** | 5 | 6 | 7 | **8** | 9 … 20 |
|---|---|---|---|---|---|---|---|---|---|
| **uniform** verdict | PHI | PHI | PHI | **PHI** | OTHER | OTHER | OTHER | **TWO EVENTS** | TWO EVENTS |
| `v_src` | (0,1) | (0,2) | (0,3) | **(0,4)** | (0,4) | (0,4) | (0,4) | **(0,0)** | (0,0) |
| **textured** verdict | PHI | PHI | PHI | **PHI** | OTHER | OTHER … | | | OTHER (all) |
| `v_src` | (0,1) | (0,2) | (0,3) | **(0,4)** | (0,4) | **(−3,−1)** frozen from S=6 to S=20 | | | |

**Maximum separation with a correct correspondence: S = 4 px = `BLOCK` =
`radius`, on BOTH backgrounds. P1's cutoff is the aperture, exactly.**

### The proviso that broke, and it is informative

**P1 predicted `(0,0)` for every `S > 4`. It is wrong for S = 5, 6, 7:** the
sensor reports **`(0, 4)`** — the correct *direction*, **saturated at the
aperture**, with a magnitude that is simply wrong. It only reaches `(0,0)` at
`S ≥ 8`, where the dot (4 px wide, displaced 8 px) shares **no pixels at all**
with the ±4 search window.

So the sensor has **three regimes, not two**: correct (S ≤ 4), **confidently
wrong** (5–7), and silent (S ≥ 8). The middle band is the dangerous one — it
emits a plausible motion vector of the wrong magnitude, and nothing downstream
can tell it from a real one.

**On the textured field there is a fourth pathology: from S = 6 to S = 20 the
source cell reports a CONSTANT `(−3, −1)`** — the background's match, frozen,
completely independent of the stimulus. **The sensor stops being a function of
the displacement it is supposed to measure.**

### L2 and L3 — the other two mechanisms

| level | mechanism | max S with correspondence | matches its aperture? |
|---|---|---|---|
| **L1** | SAD block match | **4** | `radius = BLOCK = 4` — **exactly** |
| **L2** | `segment_and_track` | **6** | `span + 2 = 4 + 2 = 6` — **exactly** |
| **L3** | `track_identity` | **whatever you ask for** | `radius`, verbatim |

**L3, measured (`min radius that returns `matched`, by separation):**

| S | 2 | 4 | 8 | 16 |
|---|---|---|---|---|
| min matching `radius` | **2.0** | **4.0** | **8.0** | **16.0** |

**`track_identity` flips at exactly `radius ≥ S`, at every separation tested.
P4 confirmed exactly. It has no intrinsic aperture: it returns the answer it
was told to return.** Registered in advance as a **§13 NEGATIVE, not a phi
positive** — and it is being reported as one.

---

## 3 — M3: THE ISI DEPENDENCE — THE HUMAN CURVE, INVERTED

`R(S, k) = 1` iff **any** consecutive pair in the sequence links the source to
the full displacement. **This definition was fixed in advance and is
deliberately generous** — a system that bridged the gap would be credited.

**L1, uniform background:**

| ISI (blank frames) | **0** | 1 | 2 | 3 | 4 |
|---|---|---|---|---|---|
| S = 2 | **1** | 0 | 0 | 0 | 0 |
| S = 4 | **1** | 0 | 0 | 0 | 0 |
| S = 8 | 0 | 0 | 0 | 0 | 0 |

**L2, uniform background:** `MATCHED` at `S ∈ {2,4}, k = 0` only. **TWO_EVENTS
in all 13 other conditions.**

**Across L1 and L2, 30 ISI conditions were run. Not one produced a
correspondence at any ISI ≥ 1. P3 confirmed exactly.**

### Why this is the decisive result

**Human phi is an interior optimum in ISI.** Wertheimer's optimal apparent
motion needs a real temporal gap; at ISI = 0 the two stimuli are *simultaneous*
and observers see two things at once, not one thing moving.

**The substrate's curve is the exact opposite: maximal at ISI = 0, dead
everywhere else.** The brief asked whether a response that does not vary with
ISI is phi. This one **does** vary with ISI — **in the wrong direction**, which
is a stronger negative than invariance would have been.

**The mechanism is legible in the raw output.** At `S = 4, k = 1` the first
consecutive pair (dot → blank) carries **`n_nonzero = 0`**: the dot's
disappearance produces **literally no motion signal at all**. The second pair
(blank → dot) carries one. **That is "one vanished, another appeared", reported
as two independent events with nothing linking them — the null hypothesis of
this rung, realised exactly.**

---

## 4 — M5: THE CONTROLS, AND C-RIGID IS WHY THIS NULL IS DIAGNOSABLE

| control | result | |
|---|---|---|
| **C-POS** dot translating one block | **PHI, `v_src = (0.0, 4.0)`** | dead-instrument arm **FIRED** |
| **C-NULL** unchanged frame pair | **0 non-zero cells** | clean |
| **C-RIGID** same total displacement, delivered continuously | **40 of 40 conditions tracked EVERY hop**, including S = 20 (5 hops), both backgrounds | **the interpretive control** |
| **NOISE** independent random dot positions | mean **1.05** non-zero cells of 324 (max 2) | no spurious motion |
| **L2 wiring self-test** stationary dot | 2 regions, same node id | wiring **live** |

### C-RIGID is the whole interpretation

**At S = 20 px the sensor fails phi completely (TWO_EVENTS / frozen `(−3,−1)`)
— and tracks the SAME 20 px perfectly when it is delivered as five 4-px hops.**
Every hop, every separation, both backgrounds: **40/40.**

**So the failure is not blindness, not resolution, not contrast, and not the
displacement magnitude. It is specifically CORRESPONDENCE ACROSS A GAP.** The
sensor can follow a thing that never leaves its aperture and cannot infer a
thing that does. **Human vision sees both as motion; this system sees only the
first.** Without this arm the null would have been uninterpretable, which is
why it was registered.

---

## 5 — M6: THE C1 RE-READING — BOTH READINGS WERE WRONG

n = 40 consecutive pairs per corpus, 18×18 lattice, split at **exactly zero**
(constant-free, §13): `Δ = max|a − b|` over each block's own pixels.

| | **C1** cartoon | **C2** live-action |
|---|---|---|
| frame pairs **literally pixel-identical** | **0 / 40 (0.000)** | 0 / 40 |
| cells still (`Δ=0, v=0`) | 0.1915 | 0.0004 |
| cells **motion reported** (`Δ>0, v≠0`) | **0.0080** | **0.3343** |
| cells **CHANGE WITHOUT MOTION** (`Δ>0, v=0`) | **0.8005** | **0.6653** |
| cells spurious (`Δ=0, v≠0`) | 0.0000 | 0.0000 |

**The 0.8% reproduces exactly** (0.0080 vs the motion rung's 0.8%), so this is
the same measurement on the same corpus, not a different one.

### Finding 1 — the motion rung's stated MECHANISM is false

`VISION_MOTION_OBJECTS_RESULTS.md` §0.1 attributes the 0.8% to *"a cartoon is
animated on twos and threes and then downsampled to 72×72, so consecutive
frames are very often identical."*

**Zero of 40 C1 pairs are identical.** Mean max-abs-frame-difference is **25.7**
(min 0.47, max 132.7). **Every C1 frame pair differs, several of them
enormously.** The de-facto-stills claim was right about the *number* and wrong
about *why*.

### Finding 2 — but the phi hypothesis does not explain it either

**The registered aperture diagnostic.** Of the change-without-motion cells, the
share that acquire a vector when the block match is re-run at a wider radius:

| radius | 4 (native) | 8 | 16 | **32** |
|---|---|---|---|---|
| **C1** | 0.0000 | 0.0000 | 0.0001 | **0.0006** |
| **C2** | 0.0000 | 0.0290 | 0.0505 | **0.0609** |

**At radius 32 — nearly half the frame, an 8× aperture — 0.06% of C1's
discarded change becomes motion.** The change is **not** a correspondence the
aperture could not reach. **P6 confirmed: cartoon change is REDRAW, and a
redraw has no correspondence to find at any radius.**

**So the answer to the brief's question is NO: the 0.8% is not explained by the
sensor missing phi.** *This measurement licenses no motion-grouping re-run at a
wider radius (§3.6, §5); it is an instrument, and it was registered as one.*

### Finding 3 — what C1's "change" actually is (DESCRIPTIVE, post-hoc, labelled)

`scripts/phi_change_magnitude_diagnostic.py`. The exactly-zero split is
constant-free and therefore **maximally liberal** — a block that moved by 0.001
counts as changed. The reference level below **falls out of the 8-bit source
encoding** (1.0 = one quantization step); it is the only level reported.

| | C1 | C2 |
|---|---|---|
| change-without-motion cells | 10 374 | 8 622 |
| **share below ONE 8-bit step** | **0.968** | **0.160** |
| median Δ of those cells | **0.087** | 3.063 |
| max Δ of those cells | 124.09 | 52.09 |

**96.8% of C1's "change without motion" is below one 8-bit level** — it is
area-downsample arithmetic, not visible change. **So the de-facto-stills
CONCLUSION survives**, on a mechanism the motion rung did not state: C1's
consecutive frames are **near-identical but never exactly identical**.

**The honest residue: 3.2% of them (≈8 cells/frame) carry genuine
above-quantum change, up to Δ = 124, and the sensor emits no vector for any of
it at any radius.** That is real drawn change the motion layer discards — small,
but not nothing, and not phi.

**On C2 the same statistic inverts: only 16% is sub-quantum, so 84% of
change-without-motion on live action is REAL visible change with no vector**,
and widening the aperture 8× recovers 6% of it. **The sensor discards a great
deal of real change on video too** — a finding about the sensor, on the corpus
that does test the hypothesis.

---

## 6 — WHICH REGISTERED OUTCOME OCCURRED

§5 registered four. **Outcome 3, with outcome 4 realised at L3.**

3. **A MOTION RESPONSE WITH THE WRONG PARAMETER DEPENDENCE.** ✅ Non-zero
   response; cut off geometrically at the aperture on both backgrounds; a
   confidently-wrong saturation band; **destroyed rather than helped by ISI**.
   *A different mechanism wearing phi's clothes.*
4. **CORRESPONDENCE-IF-TOLD.** ✅ at L3 — `matched` at exactly `radius ≥ S`.
   **Reported as the §13 negative it was registered as.**
1. **The substrate sees phi** — ❌ refuted at all three levels.
2. **It does not, full stop** — partially: correspondence *does* exist, bounded
   by a pixel aperture, so the layer is at the wrong level of description
   without being wholly absent.

### Predictions: 5 confirmed, 1 proviso broken

| | prediction | outcome |
|---|---|---|
| **P1** | cutoff at the aperture exactly | ✅ S = 4 both backgrounds — **but the `(0,0)` clause is WRONG for S = 5–7 (saturation band)** |
| **P2** | hard geometric cutoff, not human's graded function | ✅ |
| **P3** | zero at every ISI ≥ 1, every level | ✅ **30/30** |
| **P4** | L3 flips at exactly `radius ≥ S` | ✅ exactly, 4/4 |
| **P5** | L2 corresponds to `span + 2 = 6` | ✅ exactly |
| **P6** | C1 partly-but-not-wholly sensor; widening won't rescue it | ✅ 0.06% conversion |

**The textured-background proviso also fired as written** (spurious vectors →
the OTHER bucket), which is why M1 reports the raw field.

---

## 7 — WHAT THIS IMPLIES FOR THE MOTION-GROUPING RUNG

**Registered in §5 of the pre-registration BEFORE the measurement, and it now
applies.** `VISION_MOTION_OBJECTS_RESULTS.md` grouped vectors from a sensor
that answers *"which pixels overlap within 4 px"*, not *"what moved"*.

**Grouping a bad signal well is indistinguishable from grouping a good signal
badly.** Therefore:

- **Its FLOOR-B failure (persist 0.187 vs arbitrary partition 0.803) can no
  longer be attributed to the grouping RULE.** On C2, 66.5% of cells carry
  change the sensor issued no vector for, and 84% of that is real visible
  change. The criterion was fed a signal with most of the motion missing and a
  saturation band of confidently-wrong vectors in what remained. **That is a
  SCOPE REDUCTION on a committed result, not a rescue of it**, and it was
  written down before the number existed.
- **Its §5 global-pan failure is re-confirmed as the sensor's**, now with an
  independent mechanism: the same aperture that fails phi produces the wrong
  vectors that minted 5 false objects.
- **Its positives are UNTOUCHED.** Cohesion (within 0.404 vs between 3.950,
  paired lower bound +2.863) and the tolerance's 3.8× fragmentation cut are
  statements about *whatever the vectors are*, and hold regardless of what they
  mean.
- **§0.1's "de-facto stills corpus" CONCLUSION stands; its stated MECHANISM
  ("consecutive frames are very often identical") is corrected here** — 0 of 40
  pairs are identical; the correct statement is *near-identical, 96.8% of
  changed blocks below one 8-bit level*.

---

## 8 — TWO ENGINE FACTS FOUND EN ROUTE, BOTH RECORDED

### 8.1 L2 WOULD HAVE PRODUCED A PERFECT FAKE NULL

`segment_and_track` writes `game -has_region-> Region` and
`cell -within-> Region` through the **admissibility-checked** `add_edge`. On a
bare `Substrate()` those productions do not exist, **the edges are silently
refused**, and every frame then sees **zero priors** — so every component is a
birth, nothing is ever matched, and **L2 reports TWO_EVENTS at every
separation.**

**That is a clean, publishable, entirely fake phi null**, and it is what the
first working version of this runner produced (0 regions at every frame). It was
caught by a control that fires on the **wiring** rather than the hypothesis: a
**stationary** dot must be MATCHED to its own prior. `seeds/region_grouping.json`
declares the productions (they are read off the seed file, not hand-written);
with them installed, L2 corresponds up to S = 6 exactly as predicted.

**The general form — and it is §1.1's guarded division in a new costume: a
mechanism whose output is "no correspondence" is indistinguishable from a
mechanism that cannot express correspondence. Positive-control the WIRING, not
only the hypothesis.**

### 8.2 `segment_and_track`'s Region NODE IDS ARE NON-DETERMINISTIC

It iterates a `std::collections::HashMap` of connected components, whose
iteration order is randomised per process. Measured across **3 independent
processes**: the id of the dot's Region shuffles between 5185 and 5186, while
**every verdict is identical (`MMMMMM......`, matched 1–6, two-events 7–12).**

**Verdicts are stable; ids are not.** Anything keying on a Region id across
processes is reading a random number. No result here depends on an id — the
verdict reads `first_id == last_id` **within** one process, which is exactly the
comparison that remains valid.

---

## 9 — §13: NO THRESHOLD ENTERED, AND THE GATE WAS PROVEN TO BITE

`tests/test_phi_ast_migrated.py` — **7 passed**. A **Python AST walk**, never a
substring selector.

Every verdict is **exact equality**: `v == (0, S)`, `v == (0, 0)`,
`matched` vs `births + deaths`, `Δ == 0`. Asserted structurally:
- **no non-zero constant** is compared against a measured quantity anywhere;
- the verdict functions decide by **equality only** — an ordering comparison
  there would be partial credit, which the registration forbids;
- the M6 split is structurally a `Gt` against the constant `0.0`;
- the declared residuals (`BLOCK`, `GRID`, `DOT`, `K_LUM`) never appear inside
  a verdict comparison, and are bound exactly once;
- the swept axes are module-level sequences that are **iterated**, never
  compared against — i.e. independent variables;
- the dead-instrument arms **raise**, not warn.

**POSITIVE-CONTROLLED (§12.3).** Injecting `abs(v[1] - sep) < 2.5` into the
verdict turns **two** assertions RED (the constant walk and the
equality-not-ordering walk); the unmodified source is asserted green in the same
test, so the walker is discriminating rather than permissive. **Non-vacuity is
asserted too** — the scan must match the verdict functions *by name*, so a
rename cannot make the gate pass by scanning nothing.

### THE GATE'S OWN DEFECT, FOUND AND RECORDED RATHER THAN QUIETLY FIXED

**The first walker flagged six sites, and three were its own false positives:
it counted ARRAY INDICES as thresholds** (`vf[r, c, 1] != 0.0`, `hist[-1]`). An
index is addressing, not a threshold. **Every one of the six was audited by hand
BEFORE the gate was touched** (§12.3 — verify the fact, then fix the gate):

| site | what it is |
|---|---|
| `vf[r,c,1]`, `hist[-1]`, `vfr[r,c,1]` ×3 | **walker defect** — subscript indices |
| `n < 2` (`ci95`) | structural: a t-interval is undefined below two observations |
| `len(hist) < 2` (`l2_verdict`) | structural: a correspondence needs two frames |
| `c < COL + sep` (`rigid_sequence`) | a loop bound **building a stimulus**, not a verdict |

**None was a threshold on a measured quantity.** The fix prunes subscript
indices and admits a non-zero constant **only** against a cardinality (`len(…)`
or the sample size `n`), enumerated narrowly. The first attempt at the prune was
*also* wrong — `ast.walk` cannot prune, so it still saw the indices — and that
is recorded here rather than presented as having worked first time.

**What §13 does NOT cover, stated rather than hidden:** `BLOCK`, `GRID`, `DOT`
and `K_LUM` are **declared magic-number residuals INHERITED** from the motion
rung; the gate asserts they are *configuration* (bound once, never a verdict
threshold), which is **weaker than "they fell out" and is the only claim made.**

**And the rung's actual §13 finding is about the mechanisms, not the runner:**
**L2's `+ 2.0` and L3's `radius` are aperture constants that were PUT IN.**
`span` falls out of the object's own extent — the most nearly-emergent aperture
in the tree — but the `+ 2.0` bolted onto it does not, and L3 has no derivation
at all. **The substrate's correspondence range is a supplied number.**

---

## 10 — SEED ACCOUNTING: MEASURED, NOT ASSERTED

Declared **86000–86999**. Measured with `scripts/seed_audit.py` on this rung's
own runner:

```
scripts/phi_measure.py   resolved: [86000, 86100, 86200]   unknown_sinks: 0
scripts/phi_change_magnitude_diagnostic.py   (no seed sinks)
parse_errors: 0
```

**3 resolved seeds, ZERO unknown sinks, none outside the block.** *A `--check`
that passes while leaving sinks UNKNOWN has verified nothing.*

An earlier revision resolved a **seed `0`** — the uniform-background branch,
where the RNG is never constructed but a static walk cannot see the early
return. Rather than explain it away, `uniform_bg()` was split into its own
seedless function so **the audit reports the truth instead of a defensible
falsehood.**

---

## 11 — WHAT IS NOT SHOWN (§8), AND THE NAMED NEXT LEVERS

**Not shown:**

- **Nothing about biological mechanism.** Human phi enters only as the parameter
  dependence to compare against; no human data was measured here.
- **The ~11% per-block sensor error is INHERITED, not re-derived**, and bounds
  every claim. No claim here exceeds it.
- **`TimeInfer` was NOT run**, and the reason was registered in advance:
  translation is group-closed, so on two frames "is this pair a translation" is
  **vacuously yes**. Its unbounded offset makes it the only globally-apertured
  mechanism in the tree, and **whether it does phi on ≥3 frames is genuinely
  open** — it needs its own pre-registration, not a footnote here.
- **One dot, one shape, one size.** `DOT = BLOCK`. Phi in humans depends on
  stimulus size and luminance too; neither was varied. **L2's aperture scales
  with `span`, so a larger dot would correspond further** — that is a
  prediction, not a measurement.
- **Horizontal displacement only.**
- **No timing claim of any kind.** Four rungs ran concurrently; every quantity
  reported is exact or counted.
- **`data/` and BSDS300 are absent**, so the oracle is the 212/10 case.
- **C1 supports no conclusion about video**, inherited from the motion rung and
  now independently confirmed (96.8% sub-quantum change).

**Named next levers, each needing its own pre-registration:**

1. **`TimeInfer` on ≥3 frames** — the only mechanism whose aperture is not a
   pixel length. The group-closure vacuity that rules it out on two frames is
   broken by a third, and the constant-velocity discriminator
   `VISION_TIME_RESULTS.md` names is exactly a correspondence criterion.
2. **A correspondence aperture that FALLS OUT.** The §13 finding is that all
   three are supplied. `span + 2` shows the shape of the answer — an aperture
   read off the object's own extent — but the `+ 2` is put in. **A range derived
   from the observation's own distribution (as the motion rung's Otsu tolerance
   is) is the obvious candidate and is not built.**
3. **The saturation band is a sensor defect worth its own gate.** S = 5–7
   returns a confidently-wrong magnitude that nothing downstream can distinguish
   from a true one. An abstention there would be strictly better than a wrong
   answer, and would cost nothing.
4. **A better sensor before a better criterion**, unchanged from the motion
   rung's lever 2 — and now with a second independent reason.
