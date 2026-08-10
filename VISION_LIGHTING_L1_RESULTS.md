# ADVANCED LIGHTING — RUNG L1: REAL-VALUED ILLUMINANT GAINS — RESULTS

*Confirmatory run of `VISION_LIGHTING_L1_PREREG.md`, authored and **committed BEFORE
the run** at **`0cec9c38`** (§3). Runner `scripts/lighting_l1_measure.py`; seed
`seeds/vision_lighting_l1.json` (builder `tools/build_vision_lighting_l1.py`); adapter
`domains/lighting_world.py`; gate `tests/test_lighting_l1_migrated.py`; pinned raw
`results/lighting_l1_measure.json`. Seeds **45220–45319** (noise floor) +
**45320–45339** (out-of-class). Base `main` HEAD **7cbf1962**
(`git merge-base --is-ancestor 7cbf1962 HEAD` verified). Branch
`gamma-substrate/vision-lighting-l1`.*

## Engine / bench / provenance (§10)

- **Engine `7d5f50c18673`** @ `…/runners/dsl/python/substrate_rs/_native.abi3.so`
  — **shared build, Rust source byte-identical** to canonical (`provenance_line()`
  reads *"shared build from … — Rust source identical"*). **This rung adds NO Rust**,
  so the shared build is a legitimate build of this tree's source (§10.1 rule 4).
  **No new engine hash — there is truly no `.rs` change.**
- `data/` symlinked to canonical (§10.2), so the bench number is the **200/0**
  condition. **Baseline measured on this worktree BEFORE any file was added: 200/0.**
- **NO new Rust, ONE new seed** (`vision_lighting_l1`, NOT boot-loaded; ships
  `LightingL1Params{lighting_l1:0.0}` **OFF by default**). **T3's
  `seeds/vision_lighting.json` and `tools/build_vision_lighting.py` are byte-identical
  — `git status` clean on both.**

---

## VERDICT — **CROSSING, with a MEASURED NEGATIVE at the resolution floor**

**T3's refusal is lifted: real-valued gains are recognized 60/60 with exact-0
discrimination, by a continuous verdict over T3's own discrete codebook, with the
admission bound falling out of the lattice.** But the honest headline is *two*
findings, and the second is a negative that this rung found in its own mechanism:

> **Below the resolution floor the mechanism returns a CONFIDENT WRONG IDENTITY
> instead of refusing — and the ambiguity is DETECTABLE from inside the graph
> (two or more candidates within the bound) but is never checked.** `Argmin`
> resolves the tie silently. This is T3's `PickUnique` lesson in a new costume.

**And the arm that was supposed to find this could not have found it.** The
pre-registered identifiability sweep bottomed out at `g=0.2`; the true floor is
`g≈0.06`. Arm D passed while sitting **entirely above** the region where it could
fail. That is reported first-class below rather than quietly rescoped.

| arm | statistic | result | vs prereg |
|---|---|---|---|
| **A REAL-GAIN INVARIANCE** *(headline; ADMISSION half ENTAILED, CORRECTNESS half RISKED)* | correct id / 60 at the 4 real gains T3 refused + 1 per-channel real gain | **60/60**, 0 false | ≥58/60 ✓ |
| **B DISCRIMINATION exact-0** *(RISKED — the §1.1 crux)* | cross-material false identities | **0** | ==0 ✓ |
| **C CONTINUOUS-DECIDES** *(the rung's reason to exist)* | discrete vs continuous on the SAME graph | **discrete 0/60, continuous 60/60** | ✓ |
| **C-alive** *(§1.1 cl. 4 — DEAD-ARM FLOOR)* | T3's discrete arm at integer gains 2/3/4 | **36/36 — ALIVE** | ==36 ✓ |
| **D IDENTIFIABILITY** *(declared RISKED — **was not**)* | correct/12 over the pre-registered sweep 0.2…20.0 | **12/12 everywhere, 0 false** | ✓ **but UNDER-POWERED — see below** |
| **E NOISE floor** *(RISKED, n=100, 45220–45319)* | fields minting or claiming | **0/100** | 0 ✓ |
| **F OUT-OF-CLASS floor** *(RISKED, n=20, 45320–45339)* | false identities / in-class admitted | **0 false, 0/20 admitted** | 0 ✓ (in-class refusal **better** than predicted) |
| **G NOVEL-material floor** *(RISKED)* | never-minted material force-matched | **0**, all `l1_refused` | 0 ✓ |
| **H DOWNSTREAM** (§13.2) | `D = \|on − off\|` at a real gain | **12** (on 12, off 0); T3 on same graph **0** | ✓ |
| **X OFF-DAY** (§9) | flag at default 0 | L1 fully inert; **T3 unchanged (6 identities, 12/12)** | ✓ |
| **P₁ residual margins** *(reported)* | max true residual vs bound 1.0 | **0.500–0.568** | bound is load-bearing, not decorative |
| **P₂ TRUE RESOLUTION FLOOR** *(reported, BEYOND prereg)* | first gain with a false identity | **g = 0.06** | **the real measurement** |
| **P₃ AMBIGUITY DETECTABLE** *(reported, BEYOND prereg)* | candidates within bound at the floor | **≥2 (up to 6)** | **the negative's diagnosis** |

---

## THE CROSSING — what T3 refused, L1 recognizes

T3's bound L2 measured **0/12** at gains 1.5 / 2.5 / 3.3 / 7.5 and **12/12** at
2.0 / 3.0 / 4.0, and refused to add a tolerance. L1 recognizes all of them, and the
two arms are read **from the same graph in the same run**:

| gain | T3 `illum_inclass` | T3 correct | L1 `l1_inclass` | L1 correct | L1's discovered REAL gain |
|---|---|---|---|---|---|
| (1.5,1.5,1.5) | 0 | **0/12** | 1 | **12/12** | (1.5000, 1.5000, 1.5122) |
| (2.5,2.5,2.5) | 0 | **0/12** | 1 | **12/12** | (2.5000, 2.5000, 2.4878) |
| (3.3,3.3,3.3) | 0 | **0/12** | 1 | **12/12** | (3.3000, 3.2955, 3.2927) |
| (7.5,7.5,7.5) | 0 | **0/12** | 1 | **12/12** | (7.5000, 7.5000, 7.5122) |
| (1.5,2.5,3.3) | 0 | **0/12** | 1 | **12/12** | (1.5000, 2.5000, 3.2927) |

The mechanism is T1's, transposed from rotation to gain:

- **The gain is a CONTINUOUS parameter in the CROSS-FRAME MAP.** `Div(l1_a, pa)`
  returns a **real** number — correct, and *not* a violation of the frame/continuum
  invariant, because it lives in `Hom(frame, frame)`. The surfaces' own coordinates
  stay integers (gated by `test_the_discovered_gain_is_REAL_and_pinned_to_resolution`).
  T3 held the gain as an exact `(numer,denom)` integer pair; L1 holds it as a real.
- **The candidate is RENDERED at that continuous gain** onto the stepped lattice
  (`Times([p_ch, ĝ_ch])`) — the analogue of T1's `MapList(Rotate(p, θ))`.
- **BINS PROPOSE, CONTINUOUS DECIDES.** The proposal set is exactly the
  `SurfaceIdentity` codebook T3's **integer** `li_mint` produced, unmodified; the
  decision is the continuous L∞ residual, `Lte(MinOver(...), 1.0)` guarded and
  `Argmin`-named — `cp_recognize`'s shape exactly.
- **The gain is pinned ONLY to observational resolution.** `3.3 → 3.2927` on the S
  channel is not an error; it is the anchor's rounding, and encoding more precision
  than the steps support would be the MDL violation §13 forbids.

### The bound FALLS OUT (§13) — the derivation, and the evidence it is not tuned

Per channel, reference at unit gain (T3's own protocol), `p=r`, `pa=M:=max_i r_i`,
`c=round(r·g)=r·g+ε_c`, `a=round(M·g)=M·g+ε_a`, `|ε_c|,|ε_a| ≤ ½`:

```
residual = | c − p·(a/pa) | = | ε_c − ε_a·(r/M) | ≤ ½ + ½·(r/M) ≤ ½ + ½ = 1
```

**ONE LATTICE STEP — the sum of exactly TWO half-step roundings**: the observation's
own, and the anchor estimate's **attenuated by `r/a ≤ 1`, which holds because the
anchor IS the frame's maximum**. Exact analogue of T1's `√2/2` (there: one rounding,
2-D Euclidean half-diagonal; here: two roundings, per-channel L∞). Aggregation is
`Max` (L∞) because each channel rounds independently.

**Measured evidence the bound is load-bearing and not decorative (§13.2):** the true
match's residual runs **0.500–0.568** against a bound of **1.0** — a substantial
fraction, neither ~0 (which would make the bound irrelevant) nor hugging the bound
(which would make it the only thing preventing a universal container). Gated by
`test_the_bound_is_actually_adjudicating_something`.

The in-class envelope likewise falls out (`½·(ref_s + n·ref_a)` on the sum statistic,
`n` **counted from the data**; plus a tighter `½·(ref_m + ref_a)` min clause declared
in advance because the sum accumulates `n` roundings). **F came out better than
predicted:** the looser envelope was the arm most at risk, and it still refused
**20/20** spatially-varying scenes — T3's 0/20 is not regressed.

---

## THE NEGATIVE — and the arm that could not have found it

### D was UNDER-POWERED. Reported, not rescoped.

The pre-registration declared arm D **RISKED** and predicted degradation at low gain.
**It measured 12/12 at every gain including 0.2, and its gate passed.** That is not a
result — it is an arm whose declared range sat **entirely above** the region where it
could fail. The six materials stay on **distinct lattice points all the way down to
g=0.08**; the floor is at **g≈0.06**. §13.1's test — *could this model have produced
the opposite result?* — is answered **NO for arm D as written**.

This is the same disease §13.1 names, in my own instrument: I declared an arm risked
that architecture had already decided. It is recorded in the results JSON under
`D_identifiability.UNDERPOWERED` and here, rather than being quietly redefined.

### Extended to the true floor: it does NOT refuse — it returns a WRONG ID

| gain | correct | **FALSE IDs** | refused | distinct lattice points | collisions |
|---|---|---|---|---|---|
| 0.2 | 12 | 0 | 0 | 6 | — |
| 0.1 | 12 | 0 | 0 | 6 | — |
| 0.08 | 12 | 0 | 0 | 6 | — |
| **0.06** | 10 | **2** | **0** | 5 | `b`≡`d` at (2,1,2) |
| **0.05** | 10 | **2** | **0** | 5 | `a`≡`f` at (0,1,2) |
| **0.04** | 8 | **4** | **0** | 5 | `a`≡`f` at (0,1,1) |
| **0.03** | 8 | **4** | **0** | 4 | `a`≡`f`, `b`≡`d` |
| **0.02** | 10 | **2** | **0** | 5 | `c`≡`e` at (0,1,0) |

**`refused = 0` in every failing row.** The mechanism does not say *"I cannot tell"*;
it says *"this is material `f`"*, confidently, about a patch of `a`.

### Why that is a real gap and not intrinsic ill-posedness

If only **one** candidate were within the bound, a wrong identity would be
unavoidable — the observation genuinely would not carry the distinction, and this
would be the same intrinsic ill-posedness as T3's global-scale ambiguity. **It is
not.** At the floor, **two or more candidates lie within the bound**:

| gain | material | observation | reported | expected | candidates within bound (residual) |
|---|---|---|---|---|---|
| 0.05 | `a` | (0,1,2) | id 10 (`f`) | id 0 (`a`) | **f 0.300**, a 0.537 |
| 0.06 | `b` | (2,1,2) | id 6 (`d`) | id 2 (`b`) | **d 0.386**, b 0.780 |
| 0.04 | `e` | (1,1,1) | id 0 (`a`) | id 8 (`e`) | **a 0.500**, e 0.682, f 0.756, b 1.000, c 1.000, d 1.000 — **6 of 6** |

**The ambiguity is present in the graph and the `Argmin` resolves it silently.** A
refusal was available and was not taken. T3's own results file says of its
`Pick`/`PickUnique` episode: *"a plain `Pick` would have written a SILENT WRONG
ANSWER … and the rung would have shipped."* **`Argmin` does exactly that here, at the
resolution floor** — the same failure mode, one level up, in the continuous verdict.

### NAMED, NOT BUILT (§5)

The fix is nameable in one line — **refuse when the runner-up is also within the
bound; make the verdict's UNIQUENESS a gate** (the continuous analogue of the
`PickUnique` lesson). **It is deliberately NOT bolted on here.** Adding a mechanism
after seeing the failure and reporting the improved number is precisely what §5
forbids; T3 named L1's bound rather than building it, and that naming is what
licensed this rung. So this names **L1b**, which needs its own pre-registration.

Both findings are **GATED** so they cannot drift into an unexamined pass:
`test_BOUND_below_the_resolution_floor_it_returns_a_WRONG_ID_not_a_refusal` and
`test_BOUND_the_ambiguity_at_the_floor_IS_detectable_from_the_graph`.

---

## §13.1 — ENTAILED vs RISKED, declared BEFORE the run, honoured here

**ENTAILED — reported as consistency, NOT banked:**

- **Arm A's ADMISSION half.** Given the §2.1 algebra, a correct build *must* admit the
  true identity. Reported because a broken build fails it — it did, in the positive
  control — not because it is a result.
- **Arm C's DIRECTION.** T3 already measured that exact cross-multiplication refuses a
  rounded real gain. Only the magnitude (0/60 → 60/60) is informative.
- **Arm D, as it turned out.** Declared RISKED in advance; **measured to have been
  ENTAILED.** The correction is recorded above.

**RISKED — this is the result:** arm A's **correctness** half (the argmin picking the
*right* candidate), **B** exact-0, **E**, **F** (doubly risked — a deliberately looser
envelope, which still refused 20/20), **G**. The measured conjunction — invariance
**with** exact-0 discrimination **and** refusal outside the class — is what
distinguishes an invariance from a universal container, and is the only part claimed
as a crossing.

**A universal container was a live outcome, not a hypothetical:** the six materials'
cone triples come within 2 in individual channels against a bound of 1.0, and at the
floor the merge duly happened.

---

## THE POSITIVE CONTROL (§12.3) — measured, not asserted

`Times` takes an `items` **LIST** (`jsonio.rs:1274`); the a/b form parses to an
**EMPTY PRODUCT = 1**. L1 uses `Times` in the render **and** in both in-class clauses,
so it is exposed to the identical defect that made T3's first build a universal
container.

**Injected it, rebuilt the seed, ran the gate: exactly 5 of 19 tests go RED** —
`test_real_valued_gains_are_recognized`,
`test_continuous_decides_what_the_discrete_codebook_refuses`,
`test_the_bound_is_actually_adjudicating_something`,
`test_out_of_class_spatially_varying_light_is_refused`,
`test_the_universal_container_regression_is_pinned`.
Reverting restores **19/19** with the seed **byte-equal** to the committed one
(verified by JSON diff).

**And §1.1 repeated itself in the control.** `test_discrimination_is_exact_zero`
**does NOT go red** under the defect: the empty product makes the residual `|c−1|`,
which exceeds the bound almost everywhere, so the broken mechanism **refuses
everything** — and a mechanism that refuses everything has a **perfect discrimination
score**. The defect was caught by the **invariance** and **out-of-class** arms, not by
the discrimination floor. **Neither floor alone is sufficient; the conjunction is the
gate.** This is recorded in the test's own docstring.

---

## AUDIT (§12.4) — composition, with file:line

**VERDICT: COMPOSE. NO new Rust. ONE new seed. NO new magic number.**

| reused | where |
|---|---|
| the continuous cross-frame gain | `Div` (`runners/dsl/src/jsonio.rs:1275`) |
| the render at a continuous parameter | `Times` (`:1274`) — T1's `Rotate` (`term.rs:709`) analogue |
| the continuous verdict | `Abs` (`:1267`) / `Minus` (`:1270`) / `Max` (`:1403`) — T1 used `PointSetDist` (`term.rs:545`) |
| bins-propose-continuous-decides | `Lte`(`:1094`) + `MinOver`(`:1174`) + `Argmin`(`:1194`), the shape of `cp_recognize` (`seeds/continuous_pose.json`) |
| the discrete codebook that proposes | T3's `li_mint` (`tools/build_vision_lighting.py:232`) — **reused unmodified** |
| hub-scoped population statistics | `Neighbours` (`jsonio.rs:437`), per `li_frame_stats` (`build_vision_lighting.py:113`) |
| the exact arm measured against | `li_inclass`/`li_recognize` (`:171`, `:295`) — **read from the same graph** |
| absence-tolerant config read | `MaxOver(..., default)` (`:1174`) — **never `PickUnique`**, gated by `test_the_flag_is_absence_tolerant_never_PickUnique` |

**Not reused, because it does not exist:** any uniqueness/ambiguity gate on a
continuous verdict. Named above as L1b.

**§0 / CLAUDE.md compliance:** every decision — the statistics, the in-class envelope,
the render, the verdict, the refusal — is a seed **RULE**. The adapter renders
`round(r·g)` (world physics; `round()` of an integer product is that product, so
**integer gains render byte-identically to the pre-L1 path** and T3's numbers are
unmoved) and reads attrs. Source-audited by `test_no_python_decision_in_the_adapter`;
`test_L1_never_writes_a_T3_attribute` enforces the namespace split that makes the
two-arm comparison one measurement.

---

## §9 — defaults preserve committed results

- **Vision bench `scripts/rung7_vision_bench.sh`: 200 passed / 0 failed** with `data/`
  — identical to the baseline measured on this worktree **before any file was added**.
  Its no-Python-thresholds scan reports *"(none — every knob is graph data)"*.
- **sd orbit law `{2:1,3:2,4:2,6:2,12:4}` UNMOVED.**
- **Sibling gates: 92 passed in one process** — category · colour-identity ·
  similarity · sdloop-vision · continuous-pose · engine-provenance · **T3 lighting
  27/27 unchanged** · the new L1 gate.
- **New gate `tests/test_lighting_l1_migrated.py`: 19 passed**, and **verified to fail
  (5 red) on an injected defect**.
- The seed is **not boot-loaded** and ships its flag at **0**; with L1 off and T3 on,
  T3 mints its 6 identities and scores 12/12 exactly as committed.

---

## BOUNDS (§8) — what this rung does NOT do

L1 widens the **GLOBAL diagonal illuminant** class from integer ratios to **real
values**, at the abstract cone-triple grain. **Still the named frontier and NOT this
rung:**

- **L1b — the uniqueness gate** on the continuous verdict (found and named here).
- **L2 — spatially-varying illuminant / Retinex.** Refused 20/20, not solved.
- **L3 — global illuminant inference** (no reference frame).
- **L4 — shadow-vs-reflectance edge attribution.**
- **Multi-illuminant scenes** — unsolved even computationally.
- **The abstract cone-triple grain**: integer `(cL,cM,cS)` per surface, **reflectance
  GIVEN**; not pixels, not images, not spectra; axes not learned.
- **The white-patch (anchor) assumption**, inherited from T3 and still load-bearing —
  the two frames must share the surface SET. Land's assumption, as a mechanism.
- **The intrinsic global-scale ambiguity** (T3's bound L1) is untouched and remains
  correct behaviour.
- Inherited: deformation, style, the learned axis-codebook at natural-image scale.

The claim is over **six hand-chosen materials × two patches** at one reference
resolution; the resolution floor (`g≈0.06`) is a property of **these** materials'
separation, not a universal constant.

## Why this is believed

For the reason the category, lighting-T3 and blind-spot rungs were: **it fails where
it must, and it found a failure the pre-registration missed.** Noise mints nothing
100/100; a spatially-varying illuminant is refused 20/20; a never-minted material is
refused at every gain; the flag off makes it inert; and the discrete arm it beats is
demonstrably **alive** at 36/36. The one arm that passed *without being able to fail*
is reported as such, and the negative it should have found is measured, diagnosed, and
gated rather than smoothed over.
