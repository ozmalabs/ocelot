# VISION — LIGHTING / APPEARANCE INVARIANCE (FRONTIER T3): the illuminant as a DISCOVERED, FACTORED cross-frame map — RESULTS

*Confirmatory run of `VISION_LIGHTING_PREREG.md`, authored and **committed BEFORE
the run** at **`feb65a57`** (§3). Runner `scripts/lighting_measure.py`; adapter
`domains/lighting_world.py`; seed `seeds/vision_lighting.json` (builder
`tools/build_vision_lighting.py`); gate `tests/test_lighting_migrated.py`; pinned raw
`results/lighting_measure.json`. Seeds **45000–45999** (noise floor 45000–45099,
out-of-class scenes 45200–45219). Base `main` HEAD **b1c736a0**
(`git merge-base --is-ancestor b1c736a0 HEAD` verified).*

## Engine / bench / provenance (§10)

- **Engine `7d5f50c18673`** @ `…/runners/dsl/python/substrate_rs/_native.abi3.so`
  — **shared build, Rust source byte-identical** to canonical (`provenance_line()`
  reads *"shared build from … — Rust source identical"*). **This rung adds NO
  Rust**, so the shared build is a legitimate build of this tree's source
  (§10.1 rule 4). **No new engine hash — there is truly no `.rs` change.**
- `data/` symlinked to canonical (§10.2), so the bench number is the **200/0**
  condition, not the vacuous 190/10.
- **NO new Rust, ONE new seed** (`vision_lighting`, NOT boot-loaded; ships
  `LightingParams{lighting:0.0}` **OFF by default**), so §9 byte-identity holds by
  construction and is verified below.

## VERDICT — **BOUNDED CROSSING**, with the bound NARROWER than pre-registered

**All 8 gated arms PASS. Every prediction in §5 of the pre-registration held.** But
the honest headline is the bound, not the pass: the crossing is over the
**EXACT-RENDERING (integer-ratio) diagonal illuminant sub-class**, not every diagonal
map — a real-valued gain is **REFUSED** (see L2). That narrowing was found by a
reported-only probe, is pinned by the gate, and is stated here rather than smoothed
over.

| arm | statistic | result |
|---|---|---|
| **A INVARIANCE** *(ENTAILED, §13.1 — consistency, NOT banked)* | same material under 3 diagonal illuminants → one identity | **36/36** correct id |
| **B DISCRIMINATION exact-0** *(RISKED — the §1.1 crux)* | cross-material false identities | **0** |
| **C ILLUMINANT-FACTORED vs RAW** *(magnitude informative)* | `(raw_correct, lit_correct)` / 36 | **(0, 36)** — raw confuses EVERY lit/unlit pair, discounted recovers all |
| **D OUT-OF-CLASS REFUSAL** *(RISKED)* | 20 spatially-varying scenes (45200–45219): in-class fired / false ids | **0 / 0** |
| **E DIFFERENT-OBJECT floor** *(RISKED)* | novel material force-matched | **0** |
| **F NOISE floor** *(RISKED, n=100, 45000–45099)* | fields minting or claiming anything | **0/100** |
| **G DOWNSTREAM / load-bearing** (§13.2) | `d_identities`, `max\|on−off\|` | **6**, **1.0**, `d_inclass` **1.0** |
| **X OFF-DAY** (§9) | flag at default 0 | fully inert (`n_identities=0`, `n_illuminants=0`, `stats_done=0`) |

## The headline — lighting-invariance IS the wall crossing, moved from geometry to appearance

**ONE seed, ZERO new Rust, ZERO magic numbers.** The illuminant is treated exactly
as the geometric rungs treated pose: a **low-D CROSS-FRAME map** that is
**DISCOVERED** and **FACTORED**, with identity defined as what it leaves fixed.

- **`li_frame_stats`** reads the frame's **own** per-channel `MaxOver` anchor and
  `Sum`, hub-scoped through `Neighbours(frame,"has_surface")` — the frame's own
  population, never a global `NodesOfType` grab (§12.1). The anchor is the frame's
  **measured dynamic-range ceiling**, which is §13's corollary in its exact form:
  dividing by it makes the appearance code **RELATIVE**, and ratios transfer where
  absolutes do not. **No constant is introduced.**
- **`li_inclass`** DISCOVERS whether the change is in-class **without needing surface
  correspondence** — so it is not circular with the recognition it gates. Under a
  diagonal map *every* order statistic scales by the same per-channel gain, so the
  anchor:sum ratio must agree between frames on all three channels. Measured: the
  discovered gain is recovered **exactly** — `(120/40, 88/44, 120/30) = (3,2,4)` —
  and is stored as an exact `(numer,denom)` **PAIR**, never divided into a float
  (the ratio is the cross-frame map, held intensionally, per the frame/continuum
  invariant).
- **`li_mint`** MDL-mints a `SurfaceIdentity` at **`m_min=2`, which FALLS OUT of
  `d=3`** (a prototype costs `d` integers and saves `d−1` per member ⇒ pays iff
  `m > d/(d−1) = 1.5`). Six materials × two patches mint exactly six; a
  single-patch material mints none.
- **`li_recognize`** matches by **anchor-relative reflectance**, as exact integer
  **cross-multiplication** — `c_ch · pa_ch == p_ch · a_ch`. The illuminant cancels
  identically. **No division, no rounding, no tolerance, no threshold.**
- **`li_raw_recognize`** is the untangling-style RAW baseline, and it is
  **ALIVE, not dead** (§1.1 clause 4): under the *identity* illuminant it scores
  **12/12**, and it drops to **0** under a gain because the gain moved the values —
  not because the rule is inert. That is what makes `(0, 36)` a measurement instead
  of a lookup.

## THE FAILURE THAT NEARLY BECAME A RESULT — a UNIVERSAL CONTAINER with a flawless invariance score (§1.1)

**This is the most important thing in this file.** The first working build scored
**perfect invariance** and looked like a clean crossing. It was a **universal
container**: every surface matched every identity, including a material that had
never been minted.

**Root cause:** `Times` takes an **`items` LIST** (`runners/dsl/src/jsonio.rs:1274`),
not `a`/`b`. Written as `{"type":"Times","a":…,"b":…}` it parses to an **EMPTY
PRODUCT — and an empty product is 1** — so the anchor-relative test became
`Eq(1, 1)`, universally true. This is the *same* empty-operand failure mode
`VISION_SIMILARITY_RESULTS.md` documented for its `det` guard, in a new costume.

**How it was caught, and how it was NOT:**

- The **invariance arm passed it perfectly.** A universal container always does.
- **`PickUnique` made it LOUD** (§12.3): the identity read panicked with
  *"AMBIGUOUS selection — 3 candidates where exactly one was required"*. A plain
  `Pick` would have written a **silent wrong answer** — every surface labelled with
  an arbitrary identity — and the rung would have shipped.
- The fix followed the panic message's own prescription: **bind the identity by the
  MATCH from the owning hub** (`["refframe","has_identity","sid"]`) instead of
  selecting it inside the effect. The filter predicate is **not applied in effect
  position**; a two-pattern match makes the pairing the matcher's decision.

**The lesson, in the arc's own terms: the floor caught what the headline could not.**
§1.1 exists precisely because "scores perfectly on the thing you want" is satisfied
by a mechanism that says yes to everything. **A perfect invariance number is
evidence of nothing until the discrimination floor is measured.**

**The gate is positive-controlled** (§12.3 — *a gate you have only ever seen pass is
not a gate you have tested*). Re-injecting the empty-product defect into the seed
turns **12 of 27 tests RED** — discrimination, the universal-container pin, the
novel-material refusal, the out-of-class refusal and the resolution bound all fire —
and reverting restores **27/27**. `test_the_universal_container_regression_is_pinned`
exists solely so this cannot recur silently.

## §13.1 — what was ENTAILED and what was RISKED (declared BEFORE the run, honoured here)

**ENTAILED — reported as consistency, NOT banked as discovery:**

- **Arm A.** Dividing by an anchor that scales with the illuminant is *exactly*
  invariant; the mechanism cannot fail here on a correct build. It is reported
  because a broken build *does* fail it (it did, in the positive control), not
  because it is a result.
- **Arm C's DIRECTION.** Raw cone values necessarily move under a gain. The
  **magnitude** — `(0, 36)`, a total wipeout of the raw baseline — is the
  informative part; the sign is not.

**RISKED — this is the result:**

- **B (exact-0), D (out-of-class refusal), E, F** are all tests the opposite
  mechanism fails. **A blind normaliser passes A and C and FAILS D**; a
  nearest-assignment mechanism force-assigns and fails B/E/F. The measured
  conjunction — invariance **with** exact-0 discrimination **and** refusal outside
  the class — is what distinguishes an invariance from a universal container, and it
  is the only part claimed as a crossing.

## THE BOUNDS — measured, reported, and pinned (§7 / §8)

### L1 — the intrinsic ill-posedness (predicted, CORRECT behaviour)

Scaling **every** reflectance in the scene by a constant is **indistinguishable**
from a dimmer illuminant: the anchor scales with it, so the anchor-relative code is
unchanged. Measured: identical identities and identical recognitions
(`indistinguishable: true`). **This is correct, not a defect** — a grey surface in
bright light and a white surface in dim light *are* the same observation. It is the
ill-posedness `VISION_VENTRAL_GROUNDING.md` names, and no mechanism in this class
can or should resolve it. Pinned by `test_BOUND_global_scale_is_intrinsically_ambiguous`.

### L2 — THE NARROWING BOUND: a REAL-valued gain is REFUSED, not mis-matched

The pre-registration scoped the rung to "a uniform gain / low-D multiplicative map".
**The delivered crossing is narrower than that**, and the probe says so plainly:

| gain | integer? | in-class discovered | recognized / 12 |
|---|---|---|---|
| 1.5 | no | **0** | **0** |
| 2.0 | yes | 1 | **12** |
| 2.5 | no | **0** | **0** |
| 3.0 | yes | 1 | **12** |
| 3.3 | no | **0** | **0** |
| 4.0 | yes | 1 | **12** |
| 7.5 | no | **0** | **0** |

Because the comparison is **exact integer cross-multiplication**, a real gain
rendered through `round()` breaks the order-statistic equality and `li_inclass`
**refuses the frame outright**. So:

- **The crossing is over the EXACT-RENDERING (integer-ratio) diagonal sub-class**,
  not over every diagonal map. Stated as the claim's scope, not buried.
- **The failure mode is CONSERVATIVE** — a refusal, never a false identity. The
  mechanism does not hallucinate an invariance it cannot support, which is the
  behaviour the floors were built to demand.
- **NO tolerance was added to widen it (§5).** A tolerance here would be a tuned
  constant with nothing to fall out of, and §13 says the fix for a failed constant is
  never to tune it. The honest form of the missing mechanism is an
  **identifiability bound derived from the observation resolution** (the
  continuous-pose precedent, `VISION_PROTOCOL` "the identifiability bound falls out
  of resolution") — **named, NOT built here**, because deriving it properly is its
  own rung with its own pre-registration.
- Pinned by `test_BOUND_a_real_valued_gain_is_REFUSED_not_mis_matched`.

### The named frontier — what this rung does NOT do

**Genuine colour constancy is NOT achieved and was not attempted.** Specifically:

- **Multi-illuminant scenes, shadows, penumbrae, interreflections, specularity and
  spatially-varying light are UNSOLVED.** The mechanism can only **REFUSE** them
  (arm D, 20/20 refused). It performs **no surface-reflectance inference** — the
  capability `VISION_VENTRAL_GROUNDING.md` identifies as needed to complete constancy
  downstream of the local double-opponent first step. **That is the honest named
  bound, and reporting it cleanly is the point, not a shortfall.**
- **The white-patch (anchor) assumption is real and declared** (prereg §5 proviso 3):
  inferring the illuminant from the frame's maximum is exact only while the two
  frames share the surface SET. It is Land's assumption, imported as a *mechanism*
  and not as a constant, and it is where the method breaks first.
- **Abstract cone-triple grain** — integer `(cL,cM,cS)` per surface, NOT pixels, NOT
  images, NOT spectra. **Reflectance is GIVEN** as the in-frame integer coordinate;
  the axes are not learned from pixels (the category rung's bound, inherited).
- Also named frontier, inherited: **deformation, style, and the learned axis-codebook
  at natural-image scale.**

## §9 — defaults preserve committed results

- **Vision bench `scripts/rung7_vision_bench.sh`: 200 passed / 0 failed** WITH
  `data/` — identical to the pre-build baseline measured on this worktree before any
  file was added. *(Re-run cleanly after the positive-control experiment, so the
  number is attributable to the committed tree and not to a transiently patched one,
  §11 rule 5.)*
- **sd orbit law `{2:1,3:2,4:2,6:2,12:4}` UNMOVED**
  (`test_orbit_law_arithmetic_matches_the_measured_mint_counts` green).
- **Sibling gates green — 67 passed in one process**: category · colour-identity ·
  similarity · sdloop-vision · engine-provenance + the new lighting gate.
- **New gate `tests/test_lighting_migrated.py`: 27 passed**, and **verified to fail
  (12 red) on an injected defect**.
- The seed is **not boot-loaded** and ships its flag at **0**, so the default graph
  is byte-identical.

## AUDIT (§12.4) — composition, with file:line

**VERDICT: IN-CLASS BY COMPOSITION. NO new Rust. ONE new seed. NO new magic number.**

| reused | where |
|---|---|
| MDL-gated mint with `m_min` falling out of dimensionality | `tools/build_vision_category.py:110` (`cat_mint`) → here at `d=3` ⇒ `m_min=2` |
| exact-match baseline as the untangling-style control | `tools/build_vision_category.py:196` (`cat_memorize`) → `li_raw_recognize` |
| cone triple → integer appearance coordinate | `tools/build_vision_colour_identity.py:266` (`ci_opponent`) |
| hub-scoped population statistics | `Neighbours` (`runners/dsl/src/jsonio.rs:437`), pattern per `seeds/affordance_basis.json:36` |
| exact integer cross-multiplication as a cross-frame guard | `Times`/`Eq` (`runners/dsl/src/jsonio.rs:1274`), the construction `sd_gen_check_sim_*` used for its orthogonality/`det` test |
| multiplicative map as a first-class discovered cross-frame dimension | `runners/dsl/src/shape_decode.rs:621` (`scale2`) — precedent that a ×-map is legitimate here |
| ambiguous-config read made LOUD | `PickUnique` (§12.3) — **fired, and caught this rung's central defect** |

**Not reused, because it does not exist:** any surface-reflectance inference. Named
above as the frontier.

**§0 / CLAUDE.md compliance:** every decision — the anchor, the in-class discovery,
the mint, the invariant, the baseline — is a seed RULE. The adapter
(`domains/lighting_world.py`) only builds frames and reads attrs; the rendering
(reflectance × gain) is world physics the agent never sees behind. Source-audited by
`test_no_python_decision_in_the_adapter`.

## Why this is believed

For the reason the category and blind-spot rungs were: **it fails where it must.**
A different material is refused; a spatially-varying illuminant is refused 20/20;
noise mints nothing 100/100; a real-valued gain is refused rather than
force-matched; and the flag OFF makes it inert. Each of those is a **RISKED** test
that the opposite mechanism — a blind normaliser, or a nearest-assignment matcher —
**fails**. And the one thing that scored perfectly while being completely wrong (the
universal container) was caught by exactly those floors, which is the strongest
available evidence that the floors are doing real work.
