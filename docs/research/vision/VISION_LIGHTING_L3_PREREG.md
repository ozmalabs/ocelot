# ADVANCED LIGHTING — RUNG L3: GLOBAL ILLUMINANT INFERENCE — PRE-REGISTRATION

*Written and COMMITTED BEFORE the confirmatory run (§3). Runner
`scripts/lighting_l3_measure.py`; seed `seeds/vision_lighting_l3.json` (builder
`tools/build_vision_lighting_l3.py`); adapter `domains/lighting_l3_world.py`; gate
`tests/test_lighting_l3_migrated.py`; pinned raw `results/lighting_l3_measure.json`.
Base `main` HEAD **3fbfe2a8** (`git merge-base --is-ancestor 3fbfe2a8 HEAD` verified).
Branch `gamma-substrate/vision-lighting-l3-global`.*

**SEEDS TAKEN: 45560–45659** (noise floor, 100 seeds × 13 surfaces = 1300 — the
SAME size as L2's E2 so the leak rates are directly comparable) **and 45660–45679**
(out-of-class fast-varying, 20). The ledger records 45560–45999 and 45100–45199 as
CLEAN; **45680–45999 and 45100–45199 remain CLEAN after this rung.**

---

## 1. THE PROBLEM THIS RUNG INHERITS

L2 crossed the spatially-varying illuminant (60/60, exact-0 discrimination) and its
noise floor **FAILED its own pre-registered rule: 13/1300 (1.0%)**. The diagnosis is
architectural, not statistical:

> If a surface IS its locale's maximum then `c = a_loc`, so the prototype that is the
> **reference** locale's maximum renders to `p·(a_loc/ra_loc) = a_loc = c` — **exactly**.
> A local maximum is therefore *always* recognized as whatever material is the
> reference locale's maximum, whether or not it is that material.

12 of the 13 are exactly that, at residual **exactly 0.0**. This is the **WHITE-PATCH
(ANCHOR) ASSUMPTION, localized**: the local anchor's IDENTITY is assumed and never
checked. L2 named the fix and refused to bolt it on (§5) — **corroborate the anchor,
which is necessarily a GLOBAL statement.** That is this rung.

## 2. AUDIT (§12.4) — VERDICT: **COMPOSE. NO new Rust. NO new constant.**

| needed | held Term, with file:line |
|---|---|
| the per-locale illuminant estimate | `Div` (`runners/dsl/src/jsonio.rs:1275`) over L2's **already-stored** `l2_a*` / `l2_ra*` (`tools/build_vision_lighting_l2.py:293`, `:344`) |
| **pooling local → scene** | `Argmin` (`jsonio.rs:1194`) over `Neighbours(frame,"has_locale")` (`:1121`) of `MaxOver` (`:1180`) — a nested fold, both held |
| the disagreement metric | `Abs`/`Minus`/`Max` (`:1267`/`:1270`/`:1403`) — the **same L∞** `l2_recognize`'s verdict uses |
| the scene's locale count | `Count` (`:1148`) — **N read from the DATA**, exactly as L1's envelope counted `n` |
| the "every locale has an estimate" quantifier | `Not` + `Exists` (`:1159`) — T3's `li_mint` guard construction |
| the verdict, render, codebook, bound | **extracted VERBATIM from `l2_recognize`** (`build_vision_lighting_l2.py:430`–`:521`) |
| the candidate counter (process rule 7) | `Count` + `Filter` (`:1148`/`:1149`) — L1b's `uq_admit` construction, as a REPORTER |
| absence-tolerant flag | `MaxOver(…, default 0.0)` — **never `PickUnique`** (process rule 3) |

**Nothing the substrate lacks is required.** A scene-level estimate plus anchor
corroboration is expressible entirely in held Terms. **`Sum`/`Prod` folds also exist
(`:1164`/`:1170`) and are deliberately NOT used** — a mean would be dragged by the very
outlier the corroboration must catch.

## 3. THE MECHANISM

1. **`l3_ghat`** — writes each paired locale's estimate `ĝ_loc = a_loc / ra_loc` as an
   explicit float. A real value is **correct** here: `ĝ` is a CROSS-FRAME map, and the
   frame/continuum invariant permits reals between frames (the cones stay integers).
   Guarded on `ra > 0` per channel, so a degenerate locale REFUSES rather than dividing
   by zero.
2. **`l3_pool`** — **ONE scene-level estimate**, the **CHEBYSHEV CENTER** of every
   locale's estimate:
   `L* = Argmin_i Max_j Max_ch |ĝ_i,ch − ĝ_j,ch|`, `Ĝ_ch = ĝ_{L*,ch}` — *the local
   estimate MOST CORROBORATED BY THE WHOLE SCENE*. Robust (a mean is not); global (every
   locale scores every candidate); no new constant. **This is the V4/PIT step over L2's
   V1/V2 local contrast.** Fires once per frame, only after EVERY locale has an estimate.
3. **`l3_corroborate`** — the anchor is CHECKED, not assumed:
   `ra_i,ch · |ĝ_i,ch − Ĝ_ch| ≤ N·LS + HS + HS` on every channel.
4. **`l3_recognize`** — L2's verdict **AND** corroboration.
5. **`l3_refuse_uncorroborated` / `l3_refuse_bound`** — refusal as a POSITIVE datum,
   **split by reason**, so the leak-closing mechanism is auditable from the results file.
6. **`l3_recognize_lesioned`** — **THE V4 LESION**, always computed on the same graph:
   the constancy stage removed entirely (`ĝ ≡ 1`), same codebook, same L∞, same bound.

### THE ENVELOPE FALLS OUT (§13) — no new constant

L2's `l2_slowvar` derives the **per-adjacency** budget: one lattice step of rendered
displacement (`p ≤ ra_i`) plus the two anchors' half-step roundings. The pooled center
is at most `N−1` adjacencies away, so the same budget accumulates along that path, and
`N ≥ N−1` is the safe over-estimate. **`N` is `Count`ed from the data.** The seed's
entire numeric literal set is `{0.0, 0.5, 1.0, 1.0e9}` — **identical to L2's**.

The envelope therefore **grows with scene extent**, which is the same property L2 derived
for the field itself. **An envelope that did NOT scale with `N` would refuse L2's own
headline** — that is a statement about the algebra, not a fitted choice.

### WHY THIS IS NOT `l2_slowvar` AGAIN

`l2_slowvar` is PAIRWISE and ADJACENT, and L2 measured it STRICTLY MORE CONSERVATIVE than
the exact verdict (hence it gates nothing). `l3_corroborate` is **looser locally** (the
`N`-scaled envelope) and yet catches what no adjacency check can: **a wrong anchor
IDENTITY is a REFLECTANCE-ratio error, not a field slope.** Only a global estimate sees it.

### THE ABLATION IS L2'S OWN ARM (§13.2)

`l3_recognize` is `l2_recognize`'s where-clause **plus exactly one conjunct**. So **L2's
`l2_*` arm, read off the SAME graph in the SAME tick, IS the pooling ablation** — this
rule with the corroboration removed and nothing else changed. No duplicate rule ships,
and **L3 can only ever SUBTRACT claims from L2, never add** (an admitted L3 row is
byte-identical to L2's answer on that row).

## 4. BUILD-PHASE DISCLOSURE (§3, honesty about what was seen before pre-registering)

The mechanism was built and smoke-checked before this document was committed. **What was
observed:** the seed loads, `run_rules` converges in 15 sweeps, the pooled scene estimate
is sensible (`Ĝ ≈ 2.06–2.19` against a true field `2.0 → 2.16`), 13/13 locales corroborate,
and L3 = L2 = 12/12 at ρ=1.006 / 1.012 / per-channel and at uniform gains 1.5 / 3.0 / 7.5.
**What was NOT observed and is genuinely unknown at the time of writing: the noise-floor
leak rate under L3, every floor arm, the V4 dissociation, and the candidate counts.** The
headline prediction below is therefore a real prediction.

## 5. PREDICTION

**The leak shrinks but I do NOT predict it closes to exactly zero.** A perfect floor is
suspicious (§1.1, and process rule 5 — a refuse-everything build scores perfect floors),
and a chance-level prediction that lands is stronger evidence than a suspiciously clean
one. Reasoning: noise `ĝ_loc = a_loc/ra_loc` has a large spread (noise cones reach ~264
against reference anchors ~20–44), so most noise locales sit far from any Chebyshev center
and fail corroboration; but with 1300 draws, a locale whose estimate happens to land near
the center can still leak. **Predicted: 0–3 of 1300 (≤0.23%).**

## 6. ARMS, STATISTICS, DECISION RULES (§4) — fixed before the run

| arm | statistic | decision rule | §13.1 |
|---|---|---|---|
| **A LEAK CLOSED** *(headline)* | noise surfaces claiming a held identity, L3 on, LIVE codebook, seeds 45560–45659 | **≤3/1300 AND strictly < L2's count on the SAME graph** | **RISKED** |
| **B NO REGRESSION — THE CONJUNCTION** | L3 correct id / 60 under L2's five headline fields; / 96 at the eight uniform gains | **≥57/60 and ≥91/96, 0 false**; T3 12/12 and L1 12/12 unmoved; sibling gates T3 **27/27**, L1 **19/19**, L2 **46/46** unchanged | **RISKED** |
| **B′ DISAGREEMENT** *(process rule 5)* | rows where L2 admits and L3 refuses | **NON-EMPTY on the noise floor, EMPTY on the headline** | **RISKED** |
| **C DISCRIMINATION** | cross-material false identities | **exactly 0** — declared IN ADVANCE to be **NOT a gate on its own** (a refuse-everything build passes it; three times demonstrated in this arc) | RISKED but WEAK |
| **D POOLING IS LOAD-BEARING** (§13.2) | leak with pooling ABLATED (= L2's arm, same graph) | **the leak RETURNS: ≥10/1300**, and `max|on−off| > 0` | **RISKED** |
| **E THE V4 DISSOCIATION** | lesioned arm, both halves | **CONSTANCY ABOLISHED: ≤6/60 correct under the fields where intact ≥57/60. DISCRIMINATION INTACT: ≥11/12 correct and 0 false at the REFERENCE illuminant.** Both required | **RISKED** |
| **F FLOOR** | fast-varying out-of-class (45660–45679); novel material | **≤25% recognized, 0 false; novel claimed = 0** | RISKED |
| **G CANDIDATES IN BOUND** (process rule 7) | `l3_ncand` over admitted rows | **reported** min/median/max | reported |
| **H THE COST** | correct rows corroboration ALSO refuses | **reported, not gated** — declared in advance as this rung's honest price | reported |
| **X OFF-DAY** (§9) | flag at default 0 | **no `l3_*`/`l3l_*` attribute written anywhere**; bench 200/0; sd orbit law `{2:1,3:2,4:2,6:2,12:4}` unmoved; siblings green | ENTAILED |

### §13.1 — ENTAILED vs RISKED, and THE FAILING INPUT (process rule 6)

**ENTAILED (reported as consistency, NOT banked):** **X** (the seed is not boot-loaded and
every rule is flag-gated at 0). **The `L3 ⊆ L2` containment** (structural — one added
conjunct). **The fact that a corroborated locale's admitted row equals L2's** (same terms).

**RISKED, with the input that would falsify each — all in the tested range:**

- **A** fails if >3 of the 1300 noise surfaces at seeds 45560–45659 still claim.
- **B** fails at ρ ∈ {1.006, 1.008, 1.010, 1.012, (1.006,1.008,1.010)} or at any of the
  eight uniform gains {1.5, 2.5, 3.3, 7.5, (1.5,2.5,3.3), 2.0, 3.0, 4.0} — **this is the
  arm a refuse-everything build must redden**, and it is the arm the positive control
  targets.
- **B′** fails if the disagreement set is EMPTY on noise (the mechanism does nothing —
  §13.2 decorative) or NON-EMPTY on the headline (it costs the crossing).
- **D** fails if the ablated leak is <10/1300, i.e. the leak was not the pooling's doing.
- **E** fails if the lesioned arm still recognizes under the fields (constancy not
  abolished ⇒ the lesion is not a lesion) **or** if it also fails at the reference
  illuminant (⇒ the arm is merely DEAD, §1.1 clause 4, and the dissociation is worthless).
- **F** fails at the alternating field amp 1.10 over seeds 45660–45679.

### THE PROVISOS, stated in advance (§3.7)

1. **The leak may not close completely, and I have predicted it will not.** A residual
   non-zero rate is the expected outcome and will be reported as the headline number
   whatever it is.
2. **Corroboration will refuse some CORRECT rows** (arm H). It buys honesty with recall,
   exactly as L1b's uniqueness gate did. That is why this seed ships **OFF**.
3. **The V4 lesion is partly entailed** — `ĝ ≡ 1` obviously fails under a large gain. The
   genuinely risked half is **DISCRIMINATION SURVIVING**, which is what separates a lesion
   from a dead arm; it is measured, not assumed.
4. **This rung does NOT solve L4.** L2 already recovers identities on both sides of a
   shadow edge without knowing an edge exists; attribution is untouched here.

## 7. POSITIVE CONTROLS (§12.3, process rules 4 and 5) — to be run and reported

1. **The `Times` EMPTY-PRODUCT trap** — inject the `a`/`b` form (empty product = 1) and
   confirm the gate goes RED, then revert and confirm the seed is **byte-equal**.
2. **A REFUSE-EVERYTHING build** — and **confirm the arms that redden are B (NO
   REGRESSION) and B′ (DISAGREEMENT)**, NOT the floors. **Arm A (LEAK CLOSED) will SCORE
   PERFECTLY under a refuse-everything build — it is a floor, and floors are not gates.**
   This is stated in advance precisely because it has caught three previous rungs.

## 8. BOUNDS (§8) — what this rung will NOT do, whatever it measures

- **ONE scene-level illuminant estimate with anchor corroboration**, and nothing more.
- **L4 — shadow-vs-reflectance EDGE ATTRIBUTION: NOT solved.**
- **MULTI-ILLUMINANT scenes: NOT solved** (unsolved even computationally).
- **The abstract cone-triple grain with reflectance GIVEN** — inherited from T3/L1/L2.
- **Locale-grain spatial registration is GIVEN; adjacency is GIVEN, not grown.**
- **A 1-D chain of 13 surfaces, radius-1 locales, six hand-chosen materials.** Every
  boundary measured is a property of THESE materials and THIS dynamic range.
- **Corroboration is a NECESSARY condition, not a sufficient one.** A scene in which the
  majority of anchors are wrong in the SAME way would corroborate a wrong pool — that is
  the mechanism's declared failure mode and it is NOT tested here.
