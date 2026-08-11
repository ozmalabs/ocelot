# LIGHTING / APPEARANCE INVARIANCE (FRONTIER T3) — PRE-REGISTRATION

*Written and COMMITTED BEFORE the confirmatory run (`VISION_PROTOCOL.md` §3).
Seeds **45000–45999** (noise floor 45000–45099). Base `main` HEAD **b1c736a0**
(`git merge-base --is-ancestor b1c736a0 HEAD` verified). Flag OFF by default (§9).*

---

## 0. The rung, in one sentence

**The illuminant is a low-D CROSS-FRAME map; lighting-invariant recognition is
therefore DISCOVER-THE-ILLUMINANT-AND-TAKE-WHAT-IT-LEAVES-FIXED** — the same shape
as the geometric-nuisance crossings (similarity / generator discovery), moved from
geometry to appearance. Scope is the **TRACTABLE illuminant class**: a uniform /
low-D **diagonal (von Kries) multiplicative map** on the cone coordinates. Full
colour constancy (multi-illuminant, shadows, spatially-varying light) is **NOT**
attempted and is the named frontier.

---

## 1. AUDIT (§12.4) — is lighting-invariance expressible by COMPOSITION? — file:line

**VERDICT: IN-CLASS BY COMPOSITION. NO new Rust. ONE new seed.**

What already exists, verified in source before designing:

| piece | where | what it gives |
|---|---|---|
| cone triple → integer opponent/appearance coordinate | `tools/build_vision_colour_identity.py:266` (`ci_opponent`: `crg=cL−cM`, `cby=cS−(cL+cM)`), seed `seeds/vision_colour_identity.json` | the in-frame INTEGER appearance coordinate this rung factors an illuminant out of |
| MDL-gated **mint** of an identity quantum from a recurring coordinate, `m_min` FALLING OUT of the coordinate dimensionality | `tools/build_vision_category.py:110` (`cat_mint`, `Gte(Count(same-signature), Lit(3))`, `m>d/(d−1)`) | the mint discipline, reused verbatim at `d=3` ⇒ `m_min=2` |
| **region / containment** recognition + an exact-match **memorization control** as the untangling-style baseline | `tools/build_vision_category.py:158` (`cat_recognize`), `:196` (`cat_memorize`) | the RAW baseline pattern (`li_raw_recognize`) — a control that must CONFUSE where the discounted code must not |
| per-frame order statistics over a hub-scoped population | `MinOver`/`MaxOver`/`Sum`/`Count`/`Filter` over `Neighbours{node,edge_type,any_type}` (`runners/dsl/src/jsonio.rs:437`; used e.g. `seeds/affordance_basis.json:36`) | the frame's **own** anchor and sum — no global grab, frame-scoped |
| exact integer cross-frame comparison without division | `Times`/`Plus`/`Minus`/`Eq` (term table, `runners/dsl/src/jsonio.rs`) — the same construction the similarity rung used for its orthogonality/`det` guard (`VISION_SIMILARITY_RESULTS.md`, `sd_gen_check_sim_*`) | the ratio comparison as **cross-multiplication** — cross-frame, exact, NO float, NO tolerance |
| a **multiplicative** (log-scale) cross-frame generator already exists as a first-class dimension | `runners/dsl/src/shape_decode.rs:621` (`scale2`, `scale_pow2_once`), `:822` dispatch | precedent that a MULTIPLICATIVE map is a legitimate discovered cross-frame dimension in this substrate — this rung's illuminant is the appearance-space analogue |

**What does NOT exist and is NOT built here:** any surface-reflectance inference
(multi-illuminant decomposition, shadow/penumbra reasoning, spatially-varying
light). **That is the honest named bound, stated in advance** — §4 arm D tests only
that the mechanism **REFUSES** out-of-class lighting, never that it solves it.

**Composition, therefore:** the illuminant is inferred as the frame's **own
per-channel maximum** (the frame's measured dynamic-range ceiling — §13's
"a fraction of a dynamic range the system measures for itself", NOT a constant),
its in-class validity is DISCOVERED by an order-statistic consistency test across
the two frames, and recognition compares the **anchor-relative** reflectance by
exact integer cross-multiplication. Every decision is a seed rule; Python builds
scenes and reads attrs (§0 / CLAUDE.md).

---

## 2. The mechanism — seed `vision_lighting`, flag `LightingParams.lighting` OFF by default

An `ObjSurface` carries integer cones `(cL,cM,cS) = (rL·gL, rM·gM, rS·gS)` — the
reflectance `r` (the stable IN-FRAME property, integer lattice) rendered under the
illuminant `g` (the CROSS-FRAME map). Rendering is EXACT-integer, so the frame
invariant holds with **no tolerance and no magic number anywhere**.

| rule | what it decides |
|---|---|
| `li_frame_stats` | the frame's **own** per-channel `MaxOver` anchor `(aL,aM,aS)` and `Sum` `(sL,sM,sS)` over `Neighbours(frame,"has_surface")`. Frame-scoped, no global grab. |
| `li_inclass` | **DISCOVERS whether the lighting change is in-class**, WITHOUT surface correspondence: under a diagonal map EVERY order statistic scales by the same per-channel `g`, so `a_ch·ref.s_ch == s_ch·ref.a_ch` must hold for all three channels (exact integer cross-multiplication). Holds ⇒ mint an `Illuminant` node carrying the discovered gain as an exact `(numer,denom)` PAIR (the ratio is the cross-frame map, stored intensionally — never a float) and set `illum_inclass=1`. Fails ⇒ nothing minted, `illum_inclass` stays 0. |
| `li_mint` | MDL-gated mint of a `SurfaceIdentity` in the REFERENCE frame: `Count(same exact (cL,cM,cS)) >= m_min` with **`m_min=2` FALLING OUT of `d=3`** (a prototype costs `d` integers and saves `d−1` per member ⇒ pays iff `m>d/(d−1)=1.5` ⇒ `m>=2`; §13). Canonical-representative + `Not(Exists)` guards, exactly `cat_mint`'s. Stores the prototype `(pL,pM,pS)` **and its own frame's anchor** `(paL,paM,paS)`. UNSUPERVISED — no label read. |
| `li_recognize` | **THE INVARIANT.** A surface in a TEST frame matches a `SurfaceIdentity` iff `illum_inclass=1` AND, for every channel, `c_ch · pa_ch == p_ch · a_ch` — i.e. the reflectance **relative to the frame's own anchor** agrees. The illuminant cancels identically; what it leaves fixed is the invariant. Sets `lit_recognized`, `lit_id`. |
| `li_raw_recognize` | **THE RAW BASELINE / untangling-style control.** Matches iff `cL==pL AND cM==pM AND cS==pS` — no discounting at all. Sets `raw_recognized`, `raw_id`. |

**Magic-number audit (§13): NONE.** `m_min=2` falls out of `d=3`; the anchor is the
frame's own measured maximum; every comparison is exact integer cross-multiplication
(no threshold, no tolerance, no learning rate, no radius).

---

## 3. §13.1 DECLARATION — what is ENTAILED and what is RISKED (stated BEFORE the run)

**ENTAILED by the algebra, reported as CONSISTENCY and NOT banked as discovery:**

- **Arm A (invariance under an exact diagonal map with a shared surface set).**
  Dividing by an anchor that scales with the illuminant is exactly invariant — the
  mechanism *cannot* fail here, so reproducing it is not evidence. It is reported
  because a broken implementation would fail it, not because it is a result.
- **Arm C's DIRECTION (the raw baseline confuses).** Raw cone values necessarily
  change under a gain. The **MAGNITUDE** (how many identities raw loses) is
  informative; the sign is not.

**RISKED — these are the result, and the opposite mechanism fails them:**

- **Arm B DISCRIMINATION exact-0.** Nothing in the algebra guarantees that distinct
  reflectances stay distinct after anchor-relative discounting. A code that merged
  them would be a **universal container** (§1.1) and would DISQUALIFY the rung. A
  nearest-assignment mechanism fails this.
- **Arm D OUT-OF-CLASS REFUSAL.** A spatially-varying (per-surface) illuminant is
  outside the class. The mechanism must **REFUSE**, not force-match. A mechanism
  that normalises anything would force-match here and pass A while failing D — this
  is the arm that separates "invariant" from "blind".
- **Arm E DIFFERENT-OBJECT floor** and **Arm F NOISE floor** (0/100).
- **Arm G load-bearing** (§13.2) — the flag must move something downstream.

---

## 4. ARMS, statistics, and decision rules — EXACTLY these tests, no sweeps (§3.6)

Confirmatory arms A–E, G, X are **DETERMINISTIC** (fixed constructed scenes; `n`
fixed by construction, no sampling ⇒ no power analysis applicable, per the
category/crowding precedent). Only arm F samples: **n = 100 seeds, 45000–45099,
fixed in advance, never previously used.**

Scenes: **6 materials × 2 patches = 12 surfaces** per frame (2 patches gives
`m_min=2`). Reference illuminant `g_ref=(1,1,1)`; test illuminants
`g ∈ {(2,2,2), (3,2,4), (5,7,3)}` (integer diagonal maps — exact rendering).

| arm | statistic | PASS |
|---|---|---|
| **A INVARIANCE** *(entailed)* | over the 3 test illuminants × 6 materials: `lit_recognized==1` AND `lit_id==own id` | **18/18** |
| **B DISCRIMINATION exact-0** *(RISKED, §1.1 crux)* | count of (surface, identity) pairs with `lit_recognized==1` and `lit_id != own id`, over all 3 test illuminants | **exactly 0** |
| **C ILLUMINANT-FACTORED vs RAW** *(magnitude informative)* | `(raw_correct, lit_correct)` over the 18 test-frame surface presentations | `raw_correct < lit_correct` AND `lit_correct==18`; the headline is the PAIR |
| **D OUT-OF-CLASS REFUSAL** *(RISKED)* | a frame lit by a PER-SURFACE random gain (spatially-varying): (i) `illum_inclass`; (ii) false identities claimed | **`illum_inclass==0`** AND **0 false identities** |
| **E DIFFERENT-OBJECT floor** *(RISKED)* | a novel material (reflectance never minted) presented under an in-class illuminant | `lit_recognized==0` (REFUSED, not force-matched) |
| **F NOISE floor** *(RISKED, n=100, seeds 45000–45099)* | iid random cone fields: fields minting any `SurfaceIdentity` **or** producing any cross-frame identity claim | **0/100** |
| **G DOWNSTREAM / load-bearing** (§13.2) | `max|on − off|` on `lit_recognized`, `illum_inclass`, `n_identities` | all **> 0** |
| **X OFF-DAY** (§9) | flag at its default 0 ⇒ every readout inert | `n_identities==0`, `max lit_recognized==0`, `max illum_inclass==0` |

**REPORTED, NOT GATED (§7 / §8):**

- **L1 — the INTRINSIC ill-posedness.** Scaling EVERY reflectance in the scene by a
  constant is **indistinguishable** from a dimmer illuminant (the anchor scales too).
  **Predicted: the mechanism reports the same identities, and that is CORRECT** — the
  ambiguity is real (a grey surface in bright light vs a white surface in dim light)
  and no mechanism in this class can or should resolve it. Reported as the
  identifiability bound, not as a failure.
- **L2 — the RESOLUTION bound.** A REAL-valued (non-integer) gain renders through
  `round()`, so exact cross-multiplication can miss. Reported: the recognition rate
  vs gain, showing the bound FALLS OUT of the observation resolution (the
  continuous-pose precedent), NOT out of a tuned tolerance. **No tolerance is added
  to rescue it** (§5).

**§9 OFF-DAY:** vision bench `scripts/rung7_vision_bench.sh` **200 passed / 0
failed WITH `data/`** (symlinked, §10.2); sd orbit law `{2:1,3:2,4:2,6:2,12:4}`
unmoved; sibling gates (category · colour-identity · similarity · sdloop-vision ·
engine-provenance) green.

---

## 5. PREDICTION, stated in advance (§3.7), with provisos

**I predict a BOUNDED CROSSING for the low-D diagonal illuminant class: all of
A, B, C, D, E, F, G, X pass.**

Reasoning: the illuminant in this class is *exactly* a low-D cross-frame map, so
factoring it is the same operation the geometric rungs already performed; the
anchor-relative code is a genuine invariant of the group, and — the risked part —
it is **injective on non-proportional reflectance sets**, so discrimination should
survive at exact-0 rather than collapsing into a universal container.

**Provisos that would break it, named now:**

1. **B fails** (distinct materials cross-match) ⇒ the anchor-relative code is a
   universal container and the rung is **DISQUALIFIED** (§1.1) — I will report that,
   not relax B.
2. **D fails** (a spatially-varying illuminant is force-matched) ⇒ the mechanism is
   normalising blindly, not discovering; the "invariance" is worthless. Report, do
   not weaken.
3. **The anchor assumption.** Inferring the illuminant from the frame's maximum is
   Land's white-patch assumption: it is exact only when the two frames share the
   surface SET (so the max comes from the same material). If the sets differ, the
   anchor is biased and A/C degrade. **This is a real assumption of the mechanism,
   declared in advance**, and is part of the bound — not a bug to be patched.

**And the honest alternative outcome I am equally prepared to report:** if genuine
lighting-invariance in this substrate turns out to require surface-reflectance
inference the substrate lacks, the result is a **CLEAN DIAGNOSED NEGATIVE** naming
the missing mechanism. §7: a diagnosed negative is a first-class result; I will not
force a pass, and I will not relax discrimination to obtain one.

---

## 6. BOUNDS declared in advance (§8)

- **Instance-level surface identity under a DIAGONAL (von Kries) illuminant only.**
- **Abstract cone-triple grain** — integer `(cL,cM,cS)` per surface, NOT pixels, NOT
  images, NOT spectra.
- **Reflectance is GIVEN as the in-frame integer coordinate**; it is not inferred
  from spectra, and the axes are not learned from pixels (the category rung's bound,
  inherited).
- **Global illuminant only.** Multi-illuminant scenes, shadows, penumbrae,
  interreflections, specularity and spatially-varying light are **NOT solved** — the
  mechanism can only REFUSE them (arm D). **This is the named frontier.**
- **The global reflectance/illuminant ambiguity is unresolved by construction** (L1)
  and is intrinsic to the class, not a defect of the implementation.
- Also named frontier (inherited): deformation, style, and the learned
  axis-codebook at natural-image scale.

---

## 7. Provenance (§10) — to be filled at OUTCOME

Engine hash, path, source verdict, base commit and bench numbers are recorded in
`VISION_LIGHTING_RESULTS.md`. **This rung adds NO Rust**; if that changes, the
worktree is rebuilt with `scripts/engine_build.sh` and a NEW engine hash recorded.

Artifacts: runner `scripts/lighting_measure.py`; adapter `domains/lighting_world.py`;
seed builder `tools/build_vision_lighting.py` → `seeds/vision_lighting.json`; gate
`tests/test_lighting_migrated.py`; pinned raw `results/lighting_measure.json`.
