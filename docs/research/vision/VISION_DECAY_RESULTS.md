# VISION — THE EDGE-ANCHORED DECAYING GRADIENT: the conjunction PASSES 3/3, the decay length FELL OUT with a closed form of exactly 1/3 — and the same suppression that corrects Cornsweet provably BREAKS a real bounded ramp (RESULTS)

*Confirmatory run of `VISION_DECAY_PREREG.md`, authored and **committed BEFORE any
implementation or measurement** at **`d5260a6f`** (§3). Branch
`gamma-substrate/decaying-gradient`, worktree
`.claude/worktrees/agent-ad92e5a814bb8c342`. Base `main` HEAD **`51f5ecf9`**.
Mechanism commit **`88ac3f81`**. Builder `tools/build_vision_paint.py`; seed
`seeds/vision_paint.json` **v1.1.0**; adapter `domains/decay_world.py`; runner
`scripts/decay_measure.py`; gate `tests/test_decay_gradient_migrated.py`; pinned
raw `results/decay_measure.json`. Seeds **69000–69099** (F1) and **69100–69199**
(F2) and **69500** / **69600** consumed; **69200–69499, 69501–69599,
69601–69999 CLEAN**.*

## Engine / bench / provenance (§10)

- **Engine `25fa11652e83`** @ `runners/dsl/python/substrate_rs/_native.abi3.so` —
  **shared build, Rust source byte-identical** to canonical (`provenance_line()`
  reads *"shared build from … — Rust source identical"*). **This rung adds NO
  Rust**, gated by `test_this_rung_adds_NO_Rust` pinned to
  **`51f5ecf9..88ac3f81`** — **BOTH endpoints fixed**, neither is `HEAD` (§12.3),
  and `tests/test_provenance_endpoint_guard_migrated.py` passes (625 passed with
  the engine-provenance gate, run as its own step BEFORE any number was taken).
- `data/` **symlinked to canonical** (§10.2). **Baseline bench measured on this
  worktree BEFORE any file was added: `scripts/rung7_vision_bench.sh` → 222
  passed, exit 0. After: 222 passed, exit 0** (both verified against their own
  run's timestamps — see the instrument error recorded below, where I briefly
  quoted a stale 200 from a file a previous session had left at my redirect
  path).
- **NO new seed.** `vision_paint` goes 1.0.0 → 1.1.0, shipping a SECOND flag
  `PaintParams{pdecay: 0.0}` — **OFF by default**, so §9 holds by construction
  and is verified against the pinned artifact (below).
- **`domains/paint_world.py`, `scripts/paint_measure.py` and
  `tests/test_paint_migrated.py` are NOT EDITED AT ALL**, and the gate asserts
  it. No other rung's seed, adapter, test or default is touched; **no shared
  file at all is in this rung's diff** (not even the seed registry —
  `vision_paint` was already registered).

---

# THE VERDICT: **PASS**, on the rung's own pre-registered three-way conjunction

| arm | pre-registered requirement | measured | verdict |
|---|---|---|---|
| **ARM 1** — Cornsweet, correct sign at the ESCALATED order | `difference > 0` and both hubs `korder == 2` | **+0.727273**, korder **2.0 / 2.0** | **PASS** |
| **ARM 2** — induction DECLINES with distance from the edge | strictly decreasing `\|I\|` and no sign change, BOTH far fields | strictly decreasing on both, no sign change | **PASS** |
| **ARM 3** — the residual arm STILL passes | R1–R4 + F1 + F2, decay ON | all six | **PASS** |
| | | **CONJUNCTION** | **PASS** |

**And the headline is not the pass.** It is what the pass cost, which the
pre-registration predicted in advance and which is pinned here as a
first-class negative:

> **ARM 3b / R5 — a REAL linear ramp inside a BOUNDED compartment is fitted
> perfectly (slope recovered EXACTLY 3.0) and then RENDERED WRONG.** Residual
> 0.000 → **1.642857**; the region goes from not-refuted to **REFUTED**. The
> mechanism **cannot distinguish a genuine bounded ramp from a Cornsweet
> shoulder, because they are the same signal** — a gradient running up to an
> edge. The suppression that corrects one necessarily breaks the other.

So the tension the paint rung discovered is **real but LOCALISED**: it is not
"perception vs honesty" everywhere, it is exactly the bounded-gradient case, and
the mechanism **says so** — it reports the render as refuted rather than
mis-rendering silently.

---

# THE DECAY LENGTH: it FELL OUT, and its closed form is itself a fallen-out number

**λ = `plam` = the region's own MEAN GEODESIC DEPTH from its own boundary**,
flooded across the same unblocked links `pt_flood` already uses, so the distance
never leaves the compartment.

**Nothing is imported.** No constant of Cohen-Duwek & Spitzer's (or anyone's)
appears anywhere in this rung. Their *mechanism* — weight the gradient before you
use it — is the idea being tested; their multi-scale Gabor dominance function and
its parameters are not used. λ is geometry: the same kind of first moment
`pt_fit1` already takes as a centroid, but in the distance-to-its-own-boundary
coordinate. The code depends only on the dimensionless `pdist/plam`, so it is
relative rather than absolute (§13: *ratios transfer, absolutes do not*).

**And the derivation has a closed form that was predicted before the code
existed and measured exactly.** For a region anchored on ONE side, `pdist` is
uniform on `0 … d_max`, so λ = d_max/2 **exactly**, and

> **w(d_max) = (d_max/2)/(d_max/2 + d_max) = 1/3, INDEPENDENT OF REGION WIDTH.**

Measured `far_weight` = **0.3333333333333333** at flat widths **3, 6 AND 12**,
with λ = **3.0 / 4.5 / 7.5** respectively. **The decay cuts the plane's far-field
excursion to exactly one third — so it buys exactly a factor of 3 of headroom
against inversion, derived rather than fitted.** That is what fixes the sign:

| code | far-field painted value | inverts iff | measured on the committed stimulus |
|---|---|---|---|
| order-1 flat | `m` | never | (+2.0, but the ladder does not stop here) |
| order-2 plane (v1.0.0) | `m − s·h` | `s·h > (m−100)` | 1.909 > 1.000 ⇒ **INVERTS (−1.818)** |
| order-2 decaying (v1.1.0) | `m − s·h/3` | `s·h > 3(m−100)` | 1.909 < 3.000 ⇒ **CORRECT (+0.727)** |

## WHAT DID **NOT** FALL OUT, DECLARED IN THE PRE-REGISTRATION AND NOT AFTER (§13.1)

**The FORM of the falloff is ARCHITECTURE, not a derivation.** `λ/(λ+d)` is the
simplest function meeting w(0)=1, strictly decreasing, w(∞)=0, one scale
parameter, expressible without new Rust (an exponential would need a new `Exp`
Term) — but it is a *choice*, and a different admissible form gives different
magnitudes.

**Therefore ARM 2's DIRECTION is FORCED by the construction**, and this is
§13.1's third category: *a mechanism whose architecture forces the signature you
are measuring is the same disease as an imported constant, wearing a mechanism's
clothes.* The pre-registration said so in advance, the seed's own `pt_paint`
comment says so, and the gate asserts that both declarations are present. **ARM 2
is NOT offered as evidence that a decaying code decays.**

What ARM 2 *does* risk, and what it therefore actually tests, is stated in §ARM 2
below: strictness/monotonicity of the **TOTAL** induction (a product whose
deviation factor changes sign inside the far field) and the absence of a sign
change — a predicate the committed plane **fails**.

---

# ARM 1 — Cornsweet, single-edge geometry (G1)

| statistic | `pdecay = 0` (committed v1.0.0) | `pdecay = 1` |
|---|---|---|
| painted left far cell (3,0) | 99.0909 | **100.3636** |
| painted right far cell (3,19) | 100.9091 | **99.6364** |
| **difference** | **−1.818182** (WRONG SIGN) | **+0.727273** (CORRECT) |
| `korder`, both hubs | 2.0 | **2.0** |
| region mean / slope | 101.0 / 0.424242 | **unchanged** (the FIT is untouched) |
| λ (`plam`) | — | **4.5** |

**The verdict is read at the order the residual REACHES**, not at an intermediate
k=1 state — reading k=1 to rescue the arm is exactly the §5 surgery the paint
rung refused, and this rung refuses it too. The illusion is now correct **at
k=2**, which is the state the mechanism actually converges to.

**The pre-registration's named proviso was measured, not assumed.** If the field
border anchored, or the far side of the cusp did, every number above would be
wrong. Measured `panchor` on row 3 is `[0]×9, 1, 1, [0]×9` — **exactly the two
columns flanking the cusp, and nothing else** — and `pdist` runs
`9,8,7,6,5,4,3,2,1,0 | 0,1,2,3,4,5,6,7,8,9`. The field's outer border does not
anchor, and cannot: a border link does not exist, so `pt_block` can never call it
a strict maximum.

---

# ARM 2 — the Blakeslee & McCourt decline, AND ITS POSITIVE CONTROL

Measured only on the **physically uniform** far fields (both exactly 100.0), and
against **the STIMULUS's own distance from the cusp — never `pdist`** (the
instrument-discipline rule: *a diagnostic must not be computed by the component
it checks*).

| distance from cusp | 4 | 5 | 6 | 7 | 8 | 9 | monotone? | sign change? |
|---|---|---|---|---|---|---|---|---|
| **`pdecay = 1`** (both sides, identical) | 1.112299 | 0.899522 | 0.727273 | 0.584980 | 0.465455 | 0.363636 | **strictly declining** | **none** |
| **`pdecay = 0`** (committed plane) | 1.212121 | 0.787879 | 0.363636 | 0.060606 | 0.484848 | 0.909091 | **NO** | **YES** |

**THE ARM IS POSITIVE-CONTROLLED, which is why it means anything** (§12.3: *a gate
you have only ever seen pass is not a gate you have tested*). The same predicate,
the same cells, against the committed order-2 plane: it **fails both clauses**.
The plane's induction declines, **overshoots through the null, and comes back up
inverted** — the failure mode the rung exists to fix, visible in the profile
itself. A flat fill would give a *constant* |I|, failing "declining". **The arm
discriminates all three codes**, which is what the brief asked of it.

The honest reading, restated: the *direction* was forced (§13.1); the
*strictness* was not. The total induction is `(m−100) + s·dev(c)·w(d(c))` and
`dev(c)` **changes sign inside the left far field** (columns 0–5 run from −4.5 to
+0.5 about the centroid), so a non-monotone result was live. It came out
monotone.

---

# ARM 3 — the residual arm STILL passes, and R1/R2 are unchanged BY THE INVARIANT

| arm | regions | `korder` | refuted | mean residual | `panch_n` | verdict |
|---|---|---|---|---|---|---|
| **R1 uniform** | **1** | **1** | **0** | **0.000** | **0** | PASS |
| **R2 linear ramp** | **1** | **2** | **0** | **0.000**, slope **3.0 exactly** | **0** | PASS |
| **R3 texture** (seed 69600) | 6 | **2** | **1** | **29.622**, refuted area **0.986** | 118 | PASS |
| **R4 contrast** | texture − uniform = **+29.622**; refuted 1 vs 0 | | | | | PASS |
| **F1 noise floor** (n=100, 69000–69099) | **0/100** invent appearance; `max\|ppaint_app\|` **0.0 exactly** | | | | | PASS |
| **F2 texture floor** (n=100, 69100–69199) | **100/100** refuted; mean area **0.993**; mean regions **5.41**; mean residual **28.118** | | | | | PASS |

**R1 and R2 are byte-unchanged, and that is the INVARIANT rather than luck.** A
uniform field and a linear ramp have **no strict-|Δ| maximum anywhere**, so they
have no boundary, so `panch_n = 0`, so the weight takes the literal `1.0` and the
render is v1.0.0's. **No edge ⇒ no anchor ⇒ no decay.** This is precisely why the
ramp's exact slope recovery survives under a code that is, by construction, not
a faithful gradient code — and it is the pre-registered reason, not a
post-hoc one.

*Comparability caveat, stated rather than glossed:* R3/F2 run on **69600 /
69100–69199**, DIFFERENT seeds from the paint rung's 66600 / 66100–66199, so
their numbers are **not** a paired comparison with 0.965 / 29.463 / 5.63. What is
comparable is the **verdict**, and it is identical on every clause.

**A declared wart:** `plam` in an *unanchored* region saturates at the cap (the
field's own cell count, 144 for a 12×12) — the flood has nothing to measure from,
so it climbs until the terminator stops it. It is `panch_n` that is load-bearing,
not `plam`: with no anchor the weight is the literal 1.0 and `plam` is never
read. Pinned in the gate so it is a declared fact rather than a surprise.

---

# ARM 3b / R5 — **THE COST**, predicted in advance and pinned as a regression (§7)

A genuine linear ramp inside a **bounded** compartment (`[20]×4 + [50,53,…,71] +
[120]×4`; both steps ARE strict-|Δ| maxima, so the ramp region is anchored on
BOTH sides, λ = **1.5**, `panch_n` = 16).

| | `pdecay = 0` | `pdecay = 1` |
|---|---|---|
| `pslope_c_plum` (the FIT) | **3.0 exactly** | **3.0 exactly — UNCHANGED** |
| `presid_mean` (the RENDER) | **0.000** | **1.642857** |
| `prefuted` | **0** | **1** |
| painted, row 3, ramp cells | 50, 53, 56, 59, 62, 65, 68, 71 (**exact**) | 50, **56, 58.571, 60.0, 61.0, 62.429, 65**, 71 |
| true | 50, 53, 56, 59, 62, 65, 68, 71 | — |

**The shape of the damage is the diagnosis.** The ramp is rendered **exactly
right at both ends** (w = 1 at the anchors) and **flattened toward the region
mean in the middle** — which is the mechanism doing precisely what it was built
to do: be the fitted plane at the edge and the order-1 constant far from it.
Applied to a Cornsweet shoulder that is correct; applied to a real ramp it is
wrong; **and the mechanism has no way to tell them apart, because there is no
difference to see.** A gradient running up to an edge is a gradient running up to
an edge.

**This was pre-registered as prediction P6 and it is reported as the headline
rather than traded away.** It is the same trade as G2 below, seen at the
compartment scale. Note what the mechanism does NOT do: it does not mis-render
silently. `prefuted` goes to 1 — **the paint says it is wrong**, which is exactly
the property ARM 3 exists to protect, still working on the case that hurts.

---

# THE TWO GEOMETRIES, SEPARATED — G2 is an ABSENCE, not an inversion

Cavanagh & Anstis (2018) report a human percept **opposing** the local gradients
under cumulative geometry, so inversion there would not be proof of a bug
(`VISION_PRIOR_ART_MAP.md` §1.5c). **G1 and G2 were measured separately and are
not pooled**, and G2 was declared non-gated in advance.

**Measured on a 1-D Cornsweet sawtooth** (the unit `[100,100,100,100,
101,102,103,104, 96,97,98,99]` tiled 4×, so every plateau is physically 100.0 and
every cusp has the same polarity), reading the physically-100 plateau of each
**interior** unit (columns 13 / 25 / 37; unit 0 is skipped because its region is
truncated by the field border and is therefore not a translate of the others):

| | plateau 1 | plateau 2 | plateau 3 | staircase? |
|---|---|---|---|---|
| `pdecay = 0` | 99.685315 | 99.685315 | 99.685315 | **none** |
| `pdecay = 1` | 99.895105 | 99.895105 | 99.895105 | **none** |

**Our mechanism produces NO cumulative Cornsweet effect at all — not an
inversion, an ABSENCE.** Every interior unit is a translate of every other, and
every cusp is a region boundary, so the steps **cannot accumulate: regions do not
communicate.** The five region means are `[97.5, 100.0, 100.0, 100.0, 101.25]` —
the three interior regions are identical.

**And the absence is NOT this rung's doing.** It is already v1.0.0's behaviour
(the `pdecay = 0` row), because it follows from the **region segmentation**,
which this rung did not change. The decay only shifts the common value.

**THE FINDING: the very field segmentation that FIXES single-edge Cornsweet
FORBIDS cumulative Cornsweet.** Arend & Goldstein's curl result says cross-region
integration is ill-posed and that humans resolve it by field segmentation; we
took the segmentation, and the price is that the one phenomenon which *requires*
integration across boundaries is unreachable. **Same trade as R5, one scale up.**

---

# ARM B — BOUNDS, three fixed widths (§8; does not move the verdict)

| flat width | 3 | 6 (committed) | 12 |
|---|---|---|---|
| difference, `pdecay = 0` | **−1.428571** | **−1.818182** | **−1.617647** |
| difference, `pdecay = 1` | **+1.428571** | **+0.727273** | **+0.294118** |
| λ (`plam`) | 3.0 | 4.5 | 7.5 |
| far weight | **1/3** | **1/3** | **1/3** |
| slope / mean | 0.714286 / 101.4286 | 0.424242 / 101.0 | 0.191176 / 100.625 |
| **`s·h / (m−100)`** (the headroom consumed, of 3) | **1.500** | **1.909** | **2.294** |

**The correction holds at all three widths and the baseline inverts at all
three.** But the last row is the honest one: **the share of the decay's factor-3
headroom that the stimulus consumes RISES with the far field's width** — 1.50,
1.91, 2.29 — while the illusion's magnitude falls (+1.43 → +0.73 → +0.29).
**Whether that ratio crosses 3 at a still wider far field — which would
re-invert the percept — WAS NOT MEASURED.** Three fixed widths were
pre-registered; extending them is a sweep and would need its own
pre-registration (§3.6). **So ARM 1's correction is demonstrated, not proven
unconditional**, and a successor should treat the width dependence as open.

---

# ARM V / ARM V2 — the mechanism is LOAD-BEARING, and §9 holds EXACTLY

**ARM V ran FIRST (§13.2).** Toggling `pdecay` 0 → 1 moves `ppaint_lum` by
**1.2727**, `presid_lum` by **0.5455**, `prefuted_cell` by **1.0**, `pdist` by
**9.0**, `panchor` by **1.0**, and λ from **0.0 → 4.5**. `D == 0.0` on none of
the attributes the rung claims to affect.

**And it moves NOTHING it must not:** `pregion` moves **0.0** and `korder` moves
**0.0**. This is the rung's structural invariant, measured rather than asserted —
**the decay RENDERS the order-2 code, it never DECIDES the order.** `korder`
steps 1→2 on the residual of the *flat* code, in which no plane term appears, so
"k falls out" is untouched and `pt_escalate` remains the only writer of `korder`
anywhere in the seed (asserted against the manifest, and the three new rules are
asserted to write it never).

**ARM V2 — §9 byte-identity, and it is EXACT.** With `pdecay` at its shipped
default of 0.0, **all eleven arms of `results/paint_measure.json` reproduce
identically, key for key**: `mismatched_arms == []`. This includes the paint
rung's pinned NEGATIVES — I3's `−1.818182` wrong sign and I4's failure are still
there on the default path, so nothing was quietly rescued. The `wgt` factor is
folded into each slope term rather than around their sum specifically so this
holds down to the last ULP rather than by luck: floating-point re-association
would otherwise have put §9 at the mercy of the arithmetic's association order.

**ARM P — the paint rung's two positives survive**, and neither is a new result:
I1 neon **6.666667 → 6.666667** (unchanged: the stimulus's own symmetry makes
both slopes zero, so the weight multiplies a zero) and I2 watercolour **38.4 →
38.4**, still taking the INNER contour (the read cell sits at the region
centroid, where the plane IS the mean). Checked only so a successor cannot lose
them silently.

---

# THINGS I GOT WRONG, AND ONE GATE THAT FIRED ON ME

**Predictions: 9 registered, 9 correct** (and one instrument error, recorded
below, that briefly had me chasing a regression that did not exist) — including the two provisos named as
most likely to break (the anchor set is the cusp and only the cusp; R2 produces
no blocked link). Every hand-computed number matched to the digits quoted:
+0.727273, λ=4.5, the six-point induction profile, the three ARM B differences
and their three baselines, and G2's 99.895105. **P6's magnitude was the one loose
estimate** — I predicted the R5 residual "≈1.9"; it measured **1.642857**. The
direction and the refutation flip were right; the magnitude was a rough hand
figure and is corrected here.

**Being right nine times is weaker evidence than it looks, and I will not
oversell it.** The mechanism is deterministic arithmetic over a synthetic field,
so hand-computing it in advance demonstrates that I understood the code I was
about to write — not that the *hypothesis* was risky. The genuinely risked
quantities were three: the SIGN (ARM 1), the STRICTNESS of the total induction
(ARM 2), and whether R3/F2 survived. The rest is arithmetic.

**THE GATE FIRED ON ME, AND THE FIX WAS NOT TO WIDEN IT.** The first version of
`domains/decay_world.py` had an `anchor_cells()` read-back that selected cells
with a Python comprehension guard over `panchor` — a conditional over graph
state. My own AST no-decision gate caught it. **The `panchor` entry was NOT
removed from the gate's attribute list** (that is the allowlist-widening §12.3
forbids); the guard was **deleted**, and the anchor set is now reported as the
raw `panchor` FIELD — no conditional at all, and strictly *more* informative than
the filtered list it replaced. The gate was then **positive-controlled**: a
deliberate violation was injected, it went **RED**, the violation was reverted,
it went **GREEN**.

Note also that the paint rung's own adapter has the identical pattern in
`hubs()` (a comprehension guard over `phub`) and passes only because `phub` is
not in *its* gate's attribute list. **That is a real gap in the older gate**, not
a licence for this one; it is recorded here rather than fixed, because fixing
another rung's gate is not this rung's to do.

## AND I BRIEFLY REPORTED A BENCH REGRESSION THAT NEVER HAPPENED — §10's disease, self-inflicted

**I read "200 passed" as this rung's after-bench and started diagnosing a
22-test regression. There was no regression. I had read a STALE FILE.**

The mechanism, which is worth recording because it fails silently in both
halves:

1. I launched the after-bench behind a wait-loop, `until ! pgrep -f
   "decay_measure.py"; do sleep 15; done`. **That guard matches its own shell's
   command line** — the string `decay_measure.py` is *in* the very command
   `pgrep` is scanning for — so the loop could never exit and **the bench never
   ran**. A guard that matches itself is the `-k vision` substring-selector
   defect (§12) in a new costume.
2. The redirect target `bench_after.txt` **already existed in the scratchpad
   from a session nine hours earlier** (mtime 13:19 vs my before-bench's 22:22).
   So the command that never ran left behind a file that looked exactly like its
   output.
3. And the stale number was **200 — the vision oracle's value BEFORE commit
   `581a88e6` added the paint gate to the named list.** A plausible wrong
   answer, off by exactly the 22 tests of the file I then went looking at.

**Nothing was wrong with the code.** A clean run gives **222 passed, exit 0**
(`bench3.txt`, 22:47), matching my own before-run of **222 passed, exit 0**
(22:22), and `tests/test_paint_migrated.py` collects and passes 22/22 both
standalone and in the list.

**The rule this earns: a redirect target is not evidence that the command ran.**
Check the artifact's mtime against the run, or write to a path the run creates.
§10 says *a number without an engine is not a result*; the corollary is that **a
number without a verified producing run is not a result either** — and I had
already quoted this one before checking.

---

# BOUNDS — what is NOT shown (§8)

- **Synthetic battery only. No real frames.** Nothing here licenses any claim
  about natural images; the paint rung's proto-object blocker is untouched.
- **The width dependence is OPEN.** ARM B's headroom ratio rises with far-field
  width (1.50 → 1.91 → 2.29 of a maximum 3). Whether it crosses 3 — re-inverting
  the percept on a sufficiently wide field — was **not measured**, by design.
- **ARM 2's direction is FORCED by the falloff's form (§13.1).** Only its
  strictness and sign-constancy were at risk. It is not evidence of emergence.
- **The falloff FORM is unjustified beyond its five constraints.** A different
  admissible form gives different magnitudes; only `λ/(λ+d)` was tried, and a
  second form would be a NEW pre-registration, not a sweep on this one.
- **G2 is a 1-D sawtooth, NOT Cavanagh & Anstis's 2-D diamond stimulus**, and
  our "no cumulative effect" is a statement about our mechanism, not a
  psychophysical comparison. No human data was matched anywhere in this rung.
- **ONE stimulus per illusion** except F1/F2 (n=100) and ARM B (3 widths). No
  parametric family swept over cusp height, ramp length or region shape.
- **λ's closed form 1/3 is exact only for a ONE-SIDED anchor.** R5's two-sided
  region gives λ = 1.5 on an 8-cell span, not d_max/2, and R3's dense-anchor
  texture gives λ = 0.113. The "1/3" is a property of the Cornsweet geometry,
  not of the mechanism in general — stated because the table above could be
  misread as universal.
- **No claim about biology.** That this mechanism reproduces the
  decline-with-distance profile does not license "this is how the brain does
  it", and the direction was architecturally forced anyway.
- **I4 blind-spot texture gets WORSE, not better** (seed 69500): fill variance as
  a fraction of true surround variance **3.57e-5 → 1.24e-6**. The decay smooths
  the hole's fill further, deepening the paint rung's I4 negative. Reported, not
  hidden.
- **The greedy-stagewise seam (Barnes & Frost) is UNTOUCHED and this rung
  slightly worsens it.** Stage 1's constant is still the region mean, which is
  not the constant leaving the most *decay*-explainable residual — and because
  the order-2 code is now damped, the stage-1 constant matters MORE than it did
  under the extrapolating plane (the far field relaxes onto it). The
  stage-1/stage-2 relationship therefore DID change, in the direction of making
  the greedy stage-1 choice more load-bearing. Not fixed here; named.

---

# What a successor should take, and what it should not

**Take:** (a) the decay length's derivation — a region's own mean geodesic depth
from its own boundary is a scale that costs nothing, needs no threshold, and
rescales with the lattice; (b) the **"no edge ⇒ no anchor ⇒ no decay"**
invariant, which is what let a non-faithful gradient code keep a faithful one's
exact ramp recovery; (c) the ARM 2 positive control, which is the cheapest way to
show an induction-profile measure can fail; (d) **the R5 cost**, which is not a
bug to be fixed but a statement about what the representation can and cannot
distinguish.

**Do not take:** "the decaying gradient solves Cornsweet." It corrects the sign
**on a single-edge stimulus at three measured widths**, with a headroom that is
being consumed as the field widens and was not measured to its limit; the
decline-with-distance signature it displays **went in with the architecture**;
and it **breaks a real bounded ramp** and **cannot produce the cumulative effect
at all**.

**The open question this rung ends on, which it did not start with:** the paint
rung asked which of two hypotheses saves Cornsweet, and this one — *do not
extrapolate the order-2 code* — works. But it works by making the order-2 code
**local to its edge**, and both of this rung's negatives (R5, G2) are the same
consequence: **a code that is local to its edge cannot represent structure that
spans a compartment, nor structure that accumulates across compartments.** The
next question is therefore not "which falloff" but **whether the residual can
distinguish a bounded ramp from a shoulder at all** — and if it cannot at order
2, that is an argument for a *third* rung of the ladder rather than a better
weight. Which is a mechanism-level hypothesis, and needs its own
pre-registration (§3.6).
