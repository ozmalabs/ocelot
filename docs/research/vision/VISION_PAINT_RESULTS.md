# VISION — PAINT-FROM-SAMPLE: THE CONJUNCTION GATE FAILS. The residual ladder works and knows when it is wrong; the illusion account is HALF right, and the half that fails is killed BY THE LADDER ITSELF (RESULTS)

*Confirmatory run of `VISION_PAINT_PREREG.md`, authored and **committed BEFORE any
measurement or implementation** at **`e7f537d1`** (§3). Branch
`gamma-substrate/paint-from-sample`, worktree
`.claude/worktrees/agent-a21abdeb1c5fde2cc`. Base `main` HEAD **`a67afe4f`**. Mechanism
commits **`0324f9c3`** (build) and **`368d0528`** (pt_hub). Builder
`tools/build_vision_paint.py`; seed `seeds/vision_paint.json` v1.0.0; adapter
`domains/paint_world.py`; runner `scripts/paint_measure.py`; gate
`tests/test_paint_migrated.py`; pinned raw `results/paint_measure.json`. Seeds
**66000–66099** (F1) and **66100–66199** (F2); **66200–66999 UNBURNED**.*

## Engine / bench / provenance (§10)

- **Engine `b31b5911dcee`** @ `runners/dsl/python/substrate_rs/_native.abi3.so` —
  **shared build, Rust source byte-identical** to canonical (`provenance_line()` reads
  *"shared build from … — Rust source identical"*). **This rung adds NO Rust**, gated by
  `test_this_rung_adds_NO_Rust` pinned to `a67afe4f..368d0528` — **BOTH endpoints fixed**,
  neither is `HEAD` (§12.3), and `tests/test_provenance_endpoint_guard_migrated.py` passes.
- `data/` **symlinked to canonical** (§10.2). **Baseline bench measured on this worktree
  BEFORE any file was added: `scripts/rung7_vision_bench.sh` → 200 passed, exit 0.**
  **After: 200 passed, exit 0.** The **sd orbit law `{2:1,3:2,4:2,6:2,12:4}` is unmoved.**
- **ONE new seed** (`vision_paint`, NOT boot-loaded), shipping `PaintParams{paint: 0.0}`
  — **OFF by default**, so §9 byte-identity holds by construction and is verified.
- **No other rung's seed, adapter, test or default is touched.** The only shared file is
  `domains/seed_registry.py`, and the gate asserts that edit is **purely additive** (zero
  removed lines).

---

# THE VERDICT: **FAIL**, by the rung's own pre-registered conjunction

| | pre-registered | measured |
|---|---|---|
| **ARM I** — the illusions appear | requires **all four** | **FAIL — 2 of 4** |
| **ARM R** — the mechanism knows when it is wrong | requires R1–R4 | **PASS — all four, plus n=100** |

§5.3 fixed the meaning of this cell in advance: *"the residual ladder works; the illusion
predictions are **wrong**. The account, as a theory of these illusions, is refuted."*
**That is the verdict and it is recorded as such.** The honest refinement the data forces
is not that the account is uniformly wrong but that **it is right about the two illusions
that turn on WHICH cells enter the sample, and wrong about the two that turn on WHAT
HAPPENS AFTER — and the thing that breaks them is the escalation ARM R needs.** The two
halves of the conjunction are not independent; they are in tension, which nothing in the
pre-registration anticipated.

---

# ARM I — the illusion battery, baseline vs paint

**THE CRUX WAS APPLIED FIRST AND IT COST THE RUNG AN ARM.** Two items were declared
uninformative in advance from reading the code; a **third was declared uninformative by
the measurement**, against the rung's interest.

| id | baseline | paint | verdict |
|---|---|---|---|
| **I1 neon spreading** | `ppaint_app = 0.0` at the far cell (and `gr_fill` leaves belief ≡ observation on a fully-sensed field, `max|bel−obs| = 0.0` **exactly**) | **6.667** at a cell whose observed appearance is **0.0** | **PRESENT** |
| **I2 watercolour** | `0.0` | **+38.4**, and it takes the **INNER** contour's sign (+60), not the OUTER's (−60) | **PRESENT — the risked prediction HELD** |
| **I3 Cornsweet** | `0.0` exactly (the two flats are physically equal) | **−1.818** — non-zero, **WRONG SIGN** | **FAIL** |
| **I4 blind-spot texture** | **NOT absent: `gr_fill` fill variance is 7.30% of the true surround variance** | 0.21% of true variance | **FAIL, twice over** |
| **U1 crowding** | already present (`cr_pool`) | — | **UNINFORMATIVE, declared in advance** |
| **U2 blind-spot flat fill** | already present (`gr_fill`) | — | **UNINFORMATIVE, declared in advance** |

## I1 — neon spreading falls out, and its magnitude is right for the wrong-ish reason

Appearance appears at a cell whose observed appearance is exactly zero, inside a
contour-bounded region, at **60 × 4/36 = 6.667** — the inducer's value diluted by the
region's area. A **weak tint**, which is the correct magnitude for neon spreading and was
predicted in advance as such.

**But its evidential value is LIMITED and I am not going to overstate it (§13.1).** *Could
this model have produced the opposite result?* Barely. The sample is a mean over the
region's cells, and the inducer is in the region, so a non-zero tint is close to **entailed
by the sampling rule**. The one way it could have failed is if the inducer had been
segmented out — it was not. **I1 is consistent with the account rather than a test of it.**

## I2 — watercolour falls out, takes the INNER contour, and this is the rung's one real result

This is the only prediction in the rung that **could cleanly have gone the other way**, and
it was registered before the code existed:

> the strong dark **outer** contour IS a strict-|Δ| maximum, so it is a **boundary** and is
> EXCLUDED from the region; the weak **inner** contour is iso-luminant with the interior,
> so it is **NOT** a maximum, so it is **INSIDE** the region and its chroma enters the
> sample. The tint therefore takes the **inner** contour's colour.

The stimulus was built so the two contours carry **opposite** appearance signs (+60 inner,
−60 outer). Measured: the interior is painted **+38.4** — the inner contour's sign.
`takes_INNER_sign = True`, `takes_OUTER_sign = False`.

**The asymmetry that defines the watercolour illusion falls out of which contour is strong
enough to be a boundary, from a mechanism with nothing about watercolour written anywhere
in it, using a boundary criterion with no threshold in it.** That is the result this rung
actually earned.

## I3 — Cornsweet appears, with the WRONG SIGN, and the ladder is why

Two physically identical flat far-fields (both 100.0) are painted **differently** — so the
mechanism does *something* — but the difference is **−1.818**: the side with the **bright**
cusp shoulder is painted **darker**. The illusion is inverted.

**The diagnosis is exact, and it is the most interesting thing in the rung.** The
pre-registration predicted the illusion would fall out **at k=1**, and *at k=1 it does*:
the cusp is the only strict-|Δ| maximum, so each flat region KEEPS its ramp shoulder, and
the region means are **101.0** and **99.0** — a **+2.0** difference in exactly the right
direction. But the flat code is **refuted** by the ramp cells, so `pt_escalate` fires; the
order-2 plane is fitted to *flat-plus-ramp* and **extrapolated across the far field**,
where it tilts the other way (slopes **+0.424** on both sides), landing the far cells at
**99.09** and **100.91**.

> **The escalation ARM R requires is the same escalation that destroys this illusion.**
> A mechanism that stopped at k=1 would predict Cornsweet and would not know when it was
> wrong. This one knows when it is wrong and predicts Cornsweet backwards. **The two arms
> of the conjunction gate are in tension, and the pre-registration treated them as
> independent.** That is the rung's structural finding.

**I did not read the k=1 state as the verdict**, and say so explicitly: the mechanism's
output is its converged state, and reading an intermediate one to rescue a failed arm is
precisely §5's metric surgery. The +2.0 is reported as a **diagnosis of the failure**, not
as a result.

## I4 — the blind-spot texture arm fails TWICE, and the first failure is the crux rule firing against me

**(a) The pre-registered baseline was wrong, and measuring it is what found that.** The
prereg asserted `gr_fill`'s fill would be *"flat BY CONSTRUCTION"* because it is a mean of
filled neighbours. **It is not flat.** Applied iteratively over a hole, each cell's mean is
taken over a different neighbourhood, so the fill already carries **7.30%** of the true
surround variance. By the rung's own crux rule — *an illusion present at baseline is
uninformative* — **I4's absent-vs-present comparison is void.** This is the third
uninformative item, and unlike the two declared in advance it was found by measurement,
against the rung's interest.

**(b) On the only comparable statistic, the paint LOSES to the baseline it was built to
beat.** Fill variance as a fraction of true surround variance: **baseline 7.30%, paint
0.21%** — a factor of **36 worse**. The hole joins the surround's region and is painted by
a smooth order-2 **plane**, so the fill is a gradient, not a texture. **The order-k
extension's one strictly-stronger prediction over the flat version is not merely unproven;
it is measured in the wrong direction.**

---

# ARM R — the residual contrast arm: PASS on all four, and it refutes MY OWN prediction

| arm | regions | `korder` | `prefuted` | mean residual | verdict |
|---|---|---|---|---|---|
| **R1 uniform** | **1** | **1** | **0** | **0.000** | PASS |
| **R2 linear gradient** | **1** | **2** | **0** | **0.000** | PASS |
| **R3 texture** | **5** | **2** | **1** | **29.463** | PASS |
| **R4 contrast** | texture − uniform = **+29.463**; refuted **1 vs 0** | | | | PASS |

- **R3's refuted AREA fraction is 0.965** — it is not one stray region flagging itself; the
  mechanism reports the paint as wrong across **96.5%** of the field.
- **F2 at power (n=100, seeds 66100–66199): 100/100 fields refuted**, mean refuted area
  **0.965**, mean residual **27.75**. Pre-registered bar was **>0.9**.
- **F1 noise floor (n=100, seeds 66000–66099): 0/100 fields invent appearance from none**,
  `max|ppaint_app| = 0.0` exactly. A mechanism that painted chroma where there is no chroma
  would be a confabulator; this one does not.

## §3.7 / §7 — the pre-registration named the arm most likely to kill the rung, and it was WRONG

The prereg registered, before the code existed:

> **R3 / F2 texture — THE ARM MOST LIKELY TO KILL THE RUNG.** … a texture is strict-|Δ|
> maxima everywhere, so a textured region should **FRAGMENT into micro-regions**. Each
> micro-region is then painted perfectly by its own k=1 mean and **`presid` collapses to ~0
> with `prefuted=0`.**

**It does not fragment.** Measured: **5 regions over 144 cells**, largest region **130
cells**; at power, **mean 5.63 regions**. The reasoning that produced the prediction was
wrong in a way worth recording: a random field's forward differences are **rarely STRICT
local maxima** — a strict maximum requires beating *both* flanking links, which is
uncommon in noise — so the flood merges nearly everything and the paint is refuted almost
everywhere. **Threshold-free non-maximum suppression is far more conservative about minting
boundaries than I expected, and that conservatism is exactly what makes ARM R work.**

---

# ARM K — k FALLS OUT, and `pquant` is a RESOLUTION, not a magic number

## K1 — all three ladder outcomes are REACHED, by the residual alone

| stimulus | outcome | meaning |
|---|---|---|
| uniform | `korder=1`, `prefuted=0` | flat surface |
| linear ramp | `korder=2`, `prefuted=0` | vague pattern — and the recovered slope is **3.0 exactly**, the true slope |
| texture | `korder=2`, `prefuted=1` | the ladder EXHAUSTED and the paint is still wrong |

**Nothing chooses k.** `pt_escalate` is the **only** rule in the seed whose effects assign
`korder` (asserted by the gate against the manifest); the adapter assigns it **once**, at
cell creation, to the **bottom** of the ladder; neither the runner nor the gate ever writes
a graph attribute (asserted). **k was not chosen — it was reached.**

**And the boundary criterion carries no threshold, which is load-bearing rather than
decorative:** a linear ramp's |Δ| are all **equal**, so none is a strict local maximum, so
the ramp is **ONE region** with `max(pblk_e) = max(pblk_s) = 0.0` everywhere. *Any*
magnitude threshold would have cut it into pieces and R2 would have been meaningless.

## K3 — the ×4 alphabet reproduces every verdict, and every magnitude scales EXACTLY ×4

| statistic | ×1, `pquant=1` | ×4, `pquant=4` |
|---|---|---|
| I1 painted appearance at the far cell | 6.6667 | **26.6667** |
| I2 painted appearance at the interior | 38.4 | **153.6**, still INNER sign |
| I3 far-field difference | −1.8182 | **−7.2727** |
| R1 / R2 / R3 `korder` | 1 / 2 / 2 | **1 / 2 / 2** |
| R1 / R2 / R3 `prefuted` | 0 / 0 / 1 | **0 / 0 / 1** |
| R1 / R2 / R3 region count | 1 / 1 / 5 | **1 / 1 / 5** |

**`pquant` is the field's own alphabet step and behaves as one.** A number tuned against
the answer would not survive a distribution shift of its own scale (§13). This is the
strongest §13 result in the rung, and it is the one thing here that would transfer.

## K2 — §13.2 vacuity, run FIRST: the mechanism is LOAD-BEARING

Toggling `paint` 0→1 moves `pregion` by 85, `ppaint_lum` by 100.0, `ppaint_app` by 6.67,
`presid_app` by 53.3, `prefuted_cell` by 1.0, `prefuted` by 1.0, `korder` by 1.0.
`D == 0.0` on none of the attributes the rung claims to affect. *(`presid_lum` moves 0.0 on
this stimulus, correctly: the neon field's luminance is piecewise constant and is painted
exactly. It moves 29.5 on R3.)*

## §9 — OFF by default and inert

`PaintParams.paint` ships **0.0**; a fresh boot reads 0.0; with the flag off **every** paint
attribute reads exactly **0.0** — including `pdelta_done` / `pblock_done` / `pseed_done`,
so no rule fires at all. Vision bench **200 passed, exit 0** with `data/` symlinked, before
and after. sd orbit law unmoved.

---

# Things I got wrong, and two bugs that would have produced clean false answers

**Predictions: 2 right, 1 half, 2 wrong.**

| prediction (from prereg §5) | outcome |
|---|---|
| I1 neon falls out, **weakly** | **RIGHT** (6.667 = 60×4/36) — but nearly entailed, discounted above |
| I2 watercolour falls out and takes the **INNER** contour | **RIGHT**, and it is the rung's only genuinely risked prediction |
| I3 Cornsweet falls out **at k=1**, weakly; *"the brief's guess that it needs k=2 is one I expect to be WRONG"* | **HALF** — right that k=1 produces it (+2.0) and that the brief's k=2 guess was wrong, but **wrong about the verdict**: the ladder escalates past k=1 and **inverts** it |
| ARM R texture will **FRAGMENT** and kill the rung | **WRONG** — 5 regions, not 144; the arm passes |
| I4 blind-spot texture, lowest confidence | **WRONG in the direction I did not consider**: not that the fill would be poor, but that **the BASELINE was not flat**, voiding the comparison |

**Two implementation bugs, both caught before any verdict, both recorded because each
produced a plausible wrong answer rather than an error:**

1. **The flood omitted SELF** — `MinOver(neighbours)` instead of `min(self, neighbours)`,
   so every region floored at its **second**-smallest `pidx`. A uniform field still reported
   **exactly one region**, so the arm meant to check segmentation could not see the defect.
   Caught by offsetting `pidx` by 1000 and watching the floor land on **1001**.
2. **Unsensed cells were never painted** — an optic-disc cell never reached `pdelta_done`,
   so never `pblock_done`, so `pt_paint` skipped it and I4 read a fill of **exactly 0.0**.
   That would have been reported as a clean negative. Fixed by firing `pt_delta` on every
   cell with the |Δ| term itself returning 0 when either endpoint carries no observation.
   The adapter also now **zeroes both channels in the hole** — passing the scene value
   through leaks the observation the hole is *defined* by not having.
3. **A third, found by the gate rather than by me:** the read-back computed `pidx ==
   pregion` in Python to find a region's hub. Moving it into `pt_hub` did not merely
   satisfy §0 — it **corrected a phantom**: with paint OFF, the Python comparison had been
   calling pre-seeded cell 0 a "hub" in a graph where no rule had fired. `n_regions` in the
   inert arm goes **1 → 0**. The Python conditional was not just inelegant; it was wrong.

---

# BOUNDS — what is NOT shown (§8)

- **Synthetic battery only. Real frames were OUT OF SCOPE and were not attempted** —
  proto-objects produce nothing on real frames, so real-frame painting is blocked on a seam
  this rung did not touch. Nothing here licenses any claim about natural images.
- **A 1-cell-thick contour is invisible to this boundary criterion.** Two adjacent equal
  deltas cannot break a strict-maximum tie, so **every battery contour is 2 cells thick**.
  Classic neon-spreading stimuli use thin lines. This is a real limitation of
  threshold-free NMS, declared, not worked around.
- **The ladder stops at k=2.** No periodic or texture-statistic order was built, so "the
  ladder exhausts" is a property of a **two-rung** ladder. A k=3 order might rescue I4 and
  would change what R3 means.
- **The order-2 fit is SEPARABLE**, not an optimal joint plane: for a region whose row and
  column coordinates are correlated it is the marginal slope. Declared in the seed comment.
- **One stimulus per illusion.** I1/I2/I3 are single deterministic fields; only F1/F2 carry
  n=100. No parametric family (cusp width, ring thickness, inducer area) was swept — and
  I3's magnitude in particular should be expected to depend on all three.
- **No claim about biology.** An illusion falling out of this mechanism does not license
  "this is how the brain does it", and I2's agreement with the border-ownership account of
  watercolour is a structural coincidence until something tests it.
- **`presid_lum` is 0.0 on the neon stimulus**, so the vacuity evidence for that one
  attribute comes from R3, not from K2's stimulus.

# What a successor should take, and what it should not

**Take:** the residual ladder (ARM R, F1, F2) and `pquant`'s scale-invariance. Those are
CI-free deterministic facts with a positive-controlled gate, and the k-falls-out machinery
is reusable wherever a surface code is wanted.

**Do not take:** "paint-from-sample predicts the illusions." It predicts **two** of four;
one of the two is nearly entailed by the sampling rule; and the pre-registered gate is
**FAIL**. The single result worth building on is **I2** — that the watercolour asymmetry
falls out of which contour is strong enough to be a boundary.

**The open question the rung ends on, which it did not start with:** *the escalation that
makes the mechanism honest is the escalation that breaks Cornsweet.* Either the percept is
read at a **lower** order than the one the residual reaches — which needs a principled
account of *which* order is the percept, and this rung has none — or the order-2 code must
not be **extrapolated** beyond the cells it was fitted to. **Both are mechanism-level
hypotheses and neither may be tried as a parameter search on this pre-registration (§3.6);
each needs its own.**
