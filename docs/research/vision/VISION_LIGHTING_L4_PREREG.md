# ADVANCED LIGHTING — RUNG L4: SHADOW vs REFLECTANCE EDGES — PRE-REGISTRATION

*Written and COMMITTED **BEFORE** the confirmatory run (PROTOCOL §3). Nothing in
`VISION_LIGHTING_L4_RESULTS.md` was measured before this file was committed.*

- **Base:** `main` HEAD **`07eeda24`** (`git merge-base --is-ancestor 07eeda24 HEAD`
  verified from inside this worktree).
- **Branch:** `gamma-substrate/vision-lighting-l4-shadow-edge` (own worktree, §11).
- **Engine:** `7d5f50c18673` @ `…/runners/dsl/python/substrate_rs/_native.abi3.so`
  — *shared build, Rust source byte-identical* to canonical. **This rung adds NO Rust**
  (§10.1 rule 4).
- **Baseline measured on this worktree BEFORE any file was added:
  `scripts/rung7_vision_bench.sh` → 200 passed / 0 failed.**
- **Seeds CONSUMED by this rung: `45680–45779`** (noise floor, n=100) **and
  `45780–45799`** (randomised reflectance layouts, n=20). **`45800–45999` and
  `45100–45199` remain CLEAN.**
- **Pilots used ONLY already-burned seeds `45440–45539`** (L2's consumed block) and
  deterministic scenes. *An earlier design-phase arithmetic sweep touched
  45680–45779; it was discarded and re-run on the burned block precisely so the
  confirmatory seeds stay unused (§3 clauses 3–4). The discarded run is recorded here
  rather than quietly dropped.*

---

## §1 AUDIT (§12.4) — what composes, with `file:line`

**VERDICT: COMPOSE. NO new Rust. NO new constant. NO new numeric literal.**

The classical cue — *an illuminant edge scales all channels by ONE factor and so
preserves chromatic ratios; a reflectance edge changes the ratios themselves* — is
already in this tree, in a different index.

> **L4's core predicate IS `l2_slowvar`'s clause with the quantifier moved from SPACE
> to WAVELENGTH.** `tools/build_vision_lighting_l2.py:357–384` (`_slowvar_clause`)
> tests whether two LOCALES agree on one illuminant ratio, cross-multiplied so no
> ratio is ever divided into a float:
> `| a_i·ra_j − ra_i·a_j | ≤ LS·ra_j + HS·ra_j + HS·ra_i`.
> L4 tests whether two CHANNELS agree on one illuminant ratio across an adjacency:
> `| c_Q,X·c_R,Y − c_R,X·c_Q,Y | ≤ HS·(c_Q,X + c_R,Y + c_R,X + c_Q,Y) + LS + HS`.
> **Same operator, same cross-multiplication, same two-roundings envelope; the pair of
> indices is (locale, locale) there and (channel, channel) here.**

| reused | where |
|---|---|
| the cross-multiplied ratio-agreement test | `_slowvar_clause`, `tools/build_vision_lighting_l2.py:357` |
| `Times` (**`items` LIST**, never `a`/`b`) | `runners/dsl/src/jsonio.rs:1274` |
| `Abs` / `Minus` / `Plus` / `Max` | `jsonio.rs:1267` / `:1270` / `:1269` / `:1403` |
| `Lte` / `Gt` / `Lt` / `Eq` / `And` / `Not` | `jsonio.rs:1094` and neighbours |
| `Neighbours` (hub-scoped, never a global grab, §12.1) | `jsonio.rs:437` |
| `Exists` | `jsonio.rs:1159` |
| `Argmin` over a `Filter`ed neighbourhood — **the label flood** | `jsonio.rs:1194` / `:1149`; the construction is `bo_label`'s, `tools/build_vision_border_ownership.py:176–198` |
| the min-flood-to-fixpoint idiom (O(N) per sweep under `run_rules`) | `bo_bgflood` / `bo_label`, same file |
| `Div` (report-only margin — a CROSS-FRAME ratio, never an in-frame coordinate) | `jsonio.rs:1275` |
| absence-tolerant flag read `MaxOver(…, default 0.0)` — **never `PickUnique`** (process rule 3) | L2's `ENABLED()`, `build_vision_lighting_l2.py:219` |
| the proto-object / figure-ground stage, **UNMODIFIED and UNEDITED** | `seeds/vision_border_ownership.json`, adapter `domains/border_ownership_world.py` |

**What L4 does NOT need, and this is a finding, not an omission:** it needs **no
reference frame, no `compares_to`, no `SurfaceIdentity` codebook, no locale pairing, no
spatial registration, and neither L2's per-locale gain nor L3's pooled estimate.** The
discrimination is intra-frame and purely local. **L4's assumptions are strictly WEAKER
than L2's and L3's** — it is not built on top of them, it sits beside them. (It is
therefore also unable to inherit their identity machinery; see §8.)

**Answer to the audit question:** yes — *"this edge is an illuminant discontinuity"* is
decidable with held Terms and **NO new Rust**.

---

## §2 THE MECHANISM

### §2.1 The edge-existence test — falls out (§13)

An adjacency `(R,Q)` is an EDGE at all iff the observation changes by more than the
lattice records:

```
max_ch | c_Q,ch − c_R,ch |  >  LATTICE_STEP
```

A change within one lattice step is indistinguishable from rounding, so it is not an
edge. `LATTICE_STEP = 1.0` is **L1's own falls-out step, inherited unchanged**.

### §2.2 The chromatic-ratio test — the envelope falls out of the observation's own rounding

Under the ILLUMINANT hypothesis the two sides are the SAME material under gains `g_R`,
`g_Q`: writing `u = g_R·r_X`, `v = g_R·r_Y`, `g = g_Q/g_R`, the true cone values are
`(u, v)` and `(gu, gv)`, and each observation carries its own rounding
`|e| ≤ HALF_STEP`:

```
D_XY = C_QX·C_RY − C_RX·C_QY
     = (gu+a)(v+b) − (u+c)(gv+d)
     = gu·b + v·a − u·d − gv·c + ab − cd

|D_XY| ≤ HS·(gu + v + u + gv) + 2·(HS·HS)
       ≤ HS·(C_QX + C_RY + C_RX + C_QY) + 4·HS·HS + 2·HS·HS     [true → observed]
       = HS·(C_QX + C_RY + C_RX + C_QY) + LATTICE_STEP + HALF_STEP
```

**Every term is a rounding the observation already carries. No new constant exists:**
the seed's entire numeric literal set is `{0.0, 0.5, 1.0}` — a strict SUBSET of L2's and
L3's `{0.0, 0.5, 1.0, 1.0e9}` (L4 has no codebook, so it needs no empty-population
sentinel). **Gated by `test_this_rung_adds_NO_new_constant`.**

### §2.3 The classification

For the three channel-pairs `(L,M)`, `(L,S)`, `(M,S)`:

- **edge exists AND all three `D_XY` inside the envelope ⇒ `l4_illuminant`;**
- **edge exists AND any `D_XY` outside ⇒ `l4_reflectance`;**
- **no edge ⇒ `l4_flat`** (a POSITIVE datum, §1.1 clause 4 — "refused" and "never ran"
  must be distinguishable).

Written on the LEFT cell of each horizontal adjacency (`l4_kind`) and the UPPER cell of
each vertical adjacency (`l4_kindv`). Unambiguous: each cell has exactly one right and
one lower neighbour.

### §2.4 The merge — how the classification reaches border-ownership

`l4_flood` is `bo_label`'s min-flood with `Eq(val,val)` replaced by the ratio-preserving
predicate: `l4_val := min over ratio-preserving 4-neighbours of their l4_val`, init
`l4_val = cid`, monotone decreasing so it terminates at the `run_rules` fixpoint. At the
fixpoint, **cells connected through illuminant edges and flat adjacencies share a label;
cells across a reflectance edge do not.**

The runner then builds border-ownership's OWN `Field` (its committed adapter, unedited)
in **two separate graphs**, because `vision_border_ownership`'s aggregates are global
`NodesOfType("Cell")` grabs and two fields in one graph would contaminate them:

- **RAW** — `val` = the observed `cL` (raw luminance);
- **L4** — `val` = `l4_val` read back out of the L4 graph.

Copying a value the graph decided into a second graph is mechanical adapter I/O — no
conditional, no decision (CLAUDE.md; AST-gated by
`test_no_python_decision_in_the_adapter`).

---

## §3 THE SCENES (fixed in advance)

**Materials** (T3/L1/L2's six, unchanged): `a(10,20,30) b(40,15,25) c(12,44,8)
d(33,9,41) e(21,37,14) f(6,28,36)`. **Base illuminant `g0 = 2.3` — deliberately
NON-INTEGER so that `round()` is genuinely active.** *(A pilot on integer gains gave
`D_XY ≡ 0` exactly: the arm would have been unexercised. Recorded here because a test
that cannot round is a test that cannot fail.)*

- **1-D COMBINED scene (13 surfaces, the disagreement scene):** positions 0–5 material
  `a`, positions 6–12 material `c`; gain `g0` at positions 0–8 and `g0×0.4` at 9–12.
  **Exactly two edges: a REFLECTANCE edge at 5|6 and an ILLUMINANT edge at 8|9.**
- **1-D SHADOW sweep:** 6 materials × 6 jumps `{1.5, 1.7, 2.0, 2.6, 3.0, 5.0}` = **36
  shadow edges.**
- **1-D REFLECTANCE sweep:** all **15** unordered material pairs, uniform gain `g0`.
- **2-D scene (12×12):** background material `a` at gain `g0`; a **material patch**
  `c` at rows 2–5 × cols 2–5 (16 cells, gain `g0`); a **cast-shadow rectangle** at rows
  7–10 × cols 7–10 (16 cells, material `a`, gain `g0×0.4`). Both strictly interior and
  mutually non-adjacent.

---

## §4 ARMS, STATISTICS, DECISION RULES

| arm | statistic | decision rule |
|---|---|---|
| **A SHADOW EDGE CLASSIFIED** *(headline)* | of 36 shadow edges + the combined scene's 8\|9, how many read `l4_illuminant` | **37/37** |
| **B REFLECTANCE EDGE CLASSIFIED** *(RISKED — the discrimination)* | of the 15 material pairs + the combined scene's 5\|6, how many read `l4_reflectance` | **≥14/16**, and every miss must be explained by a reported proportionality margin |
| **C1 THE DEFECT IS REAL** *(RISKED positive control)* | ProtoObjects minted by unedited border-ownership on the **RAW** field | **exactly 2**, one rooted in the shadow rectangle |
| **C2 NOT AN OBJECT BOUNDARY** *(headline)* | ProtoObjects minted on the **L4** field | **exactly 1**, root = the material patch, members = 16, and **no proto at the shadow rectangle's root** |
| **D NO REGRESSION — THE CONJUNCTION** *(RISKED, process rule 5)* | sibling gates + bench + orbit law | L2 **46/46**, L3 **39/39**, L1 **19/19**, T3 **27/27**, border-ownership **9/9**, bench **200/0**, sd orbit law `{2:1,3:2,4:2,6:2,12:4}` |
| **D′ DISAGREEMENT** *(RISKED, process rule 5)* | in the ONE combined scene, ONE tick: adjacencies read `l4_illuminant` and adjacencies read `l4_reflectance` | **both non-empty** (≥1 each) |
| **E PENUMBRA** *(RISKED; prediction below)* | a `ρ` ramp over 8 cells, `ρ ∈ {1.15, 1.3}`: ramp adjacencies read `l4_illuminant` | **all adjacencies that ARE edges** read `l4_illuminant`; the count of sub-lattice (`l4_flat`) adjacencies is REPORTED |
| **F FLOOR — noise** *(RISKED)* | over 45680–45779, 13 random triples each, 12 adjacencies: how many read `l4_illuminant` | **exactly 0** *(the brief's rule; see the proviso — I predict it FAILS)* |
| **F-alive** *(§1.1 clause 4)* | how many noise adjacencies got ANY classification | **≥99%** — a silent classifier is a dead arm, not a good floor |
| **G CHROMATIC SHADOW** *(RISKED, predicted NEGATIVE)* | per-channel gain `(×4.0, ×4.4, ×5.2)` on all 6 materials | **0/6 read `l4_illuminant`** — the cue is PREDICTED TO FAIL |
| **H PROPORTIONAL MATERIALS** *(RISKED, predicted NEGATIVE)* | `(10,20,30)` vs `(20,40,60)` and vs `(15,30,45)` | **2/2 read `l4_illuminant`** — a genuine reflectance edge PREDICTED TO BE MISREAD |
| **I BOUND OCCUPANCY** *(process rule 7)* | the margin `max_XY D_XY/envelope_XY`, and the COUNT of channel-pairs inside the envelope, for every classified adjacency; plus the COUNT of distinct `l4_val` components and of ProtoObjects | **REPORTED** (min / median / max per class) |
| **J RANDOMISED LAYOUTS** *(RISKED, 45780–45799)* | 20 shuffled 13-surface material layouts at uniform gain: material-boundary adjacencies read `l4_reflectance` | **≥95%** |
| **X OFF-DAY** (§9; ENTAILED) | flag at default 0 | **no `l4_*` attribute written anywhere**; bench 200/0; sd orbit law unmoved |

**Process rule 7 is discharged by arm I.** L4's bound is a per-adjacency envelope rather
than a codebook, so the honest analogue of "candidates inside the bound" is the
**margin distribution on BOTH sides** — if illuminant edges sit at margin ≈0 and
reflectance edges at margin ≈0.001, the bound is doing nothing and the classes are
separated by something else. Both distributions are reported, plus literal counts
(channel-pairs inside the envelope; `l4_val` components; ProtoObjects).

---

## §5 PREDICTION, WITH PROVISOS (§3 clause 7)

**I predict A, C1, C2, D, D′, E, G, H and J hold, B holds at 16/16, and F FAILS.**

1. **Arm F will FAIL its pre-registered exact-0 rule.** Piloted on the BURNED block
   45440–45539: **1/1200 (0.083%)** of random adjacencies read `l4_illuminant`. The
   mechanism is architectural, not statistical: **the envelope is ABSOLUTE-additive
   (`HS·Σc + LS + HS`), so at small cone values it is large RELATIVE to `D_XY`, and a
   pair of small near-proportional random triples fits inside it.** I predict the
   confirmatory block measures **0–5 of 1200**, and I am pre-registering the exact-0
   rule anyway, so that a non-zero result is recorded as the failure it is rather than
   retro-fitted into a pass (§5).
2. **Arm A is ENTAILED BY THE DERIVATION, modulo implementation** — see §6. It is
   reported as consistency; its informative content is the CONJUNCTION with B, G and H.
3. **Arm B's margins will be LOOSE, not hugged.** Piloted on the deterministic pairs:
   margins **9.77–66.94** against a bound of 1, worst-case shadow margin **0.7797**.
   **So the bound is hugged on the illuminant side (0.78 of 1.0) and comfortable on the
   reflectance side (≥9.8×).** I therefore predict B at 16/16 rather than at the
   ≥14/16 rule, and I am pre-registering the weaker rule because the pilot is
   deterministic and a rule tuned to a known answer is not a rule.
4. **Arm C1 could be vacuous and is not.** If the shadow rectangle failed to mint under
   RAW, arm C2 would be demonstrating nothing. C1 is stated as a REQUIREMENT, not an
   observation, and a result of 0 or 1 protos on RAW INVALIDATES C2 rather than
   improving it.
5. **Arm E's honest bound, stated in advance:** *a penumbra is not one edge — it is a
   SEQUENCE of sub-edges*, and the shallowest part of a real penumbra falls below one
   lattice step and is correctly **not an edge at all**. I predict `l4_illuminant` on
   every ramp adjacency that clears the lattice, and I am REPORTING (not gating) the
   count that does not.
6. **Arms G and H are predicted NEGATIVES and are the rung's real bound.** A physically
   realistic shadow (blue skylight in shade vs yellow sun in light) is CHROMATIC, and
   the ratio cue is then simply WRONG — it will call the shadow a material change.
   Symmetrically, two materials that are scalar multiples are indistinguishable from an
   illuminant change **in principle, by any local ratio cue.** If G reads
   `l4_illuminant` or H reads `l4_reflectance`, my understanding of the mechanism is
   wrong and that is the more interesting outcome.

---

## §6 §13.1 — ENTAILED vs RISKED, declared BEFORE the run

**ENTAILED — reported as consistency, NEVER banked:**

- **Arm A.** §2.2 derives the envelope as a valid upper bound on `|D_XY|` *under the
  neutral-illuminant hypothesis*. **So a neutral shadow CANNOT exceed it, and arm A
  cannot fail unless the implementation does not match the derivation.** This is §13.1's
  third category — *architecture that forces the signature* — and I am naming it against
  myself rather than presenting 37/37 as a discovery. What arm A genuinely tests is that
  the seed computes what the algebra says (the `Times` empty-product trap would break it;
  positive-controlled in §7). **The rung's evidence is the CONJUNCTION A ∧ B ∧ G ∧ H:**
  the same envelope must ADMIT neutral shadows, REJECT 15 material pairs, REJECT
  chromatic shadows, and ADMIT proportional materials. **No single arm is the result.**
- **Arm X.** The seed is not boot-loaded and every rule is flag-gated at 0, so inertness
  is entailed by construction.
- **C2's shadow half, PARTLY.** Once `l4_flood` merges the shadow with the background,
  the shadow *cannot* mint — that is what merging means. **The risked half is that the
  PATCH still mints, with the right root and 16 members**, which is exactly what a
  merge-everything build fails.

**RISKED — with the input that would redden each (process rule 6):**

| arm | the input that would redden it | in range? |
|---|---|---|
| **B** | a material pair whose chromatic ratios differ by less than the rounding envelope | **YES** — measured margins run down to **9.77** (`a|f`); a pair at margin <1 fails. Arm H is a CONSTRUCTED such pair and is predicted to fail. |
| **C1** | a RAW field in which the shadow rectangle does not mint (e.g. if it touched the frame, or if `cL` collided with the background's) | **YES** — the values are 23 / 9 / 28 and a collision would give 1 proto, not 2. |
| **C2** | a merge that over-merges (patch absorbed → **0** protos) or under-merges (shadow survives → **2** protos) | **YES** — both are reachable: an always-true predicate gives 0, an always-false one gives 0 by a different route (every cell its own component ⇒ nothing singly-surrounded). **Positive-controlled in §7.** |
| **D** | any sibling gate moving | **YES** — demonstrated red under an injected refuse-everything build. |
| **D′** | a build that classifies everything the same way | **YES** — refuse-everything and accept-everything BOTH empty one side. |
| **E** | a ramp whose per-step change is multiplicative but whose rounding exceeds the envelope | **YES** — piloted margins reach **0.664** of the bound at `ρ=1.3`; a steeper ramp closes the remaining 0.336. |
| **F** | any noise adjacency inside the envelope | **YES** — piloted at 1/1200 on the burned block. |
| **G** | a chromatic gain small enough to sit inside the envelope | **YES** — piloted margins 3.61–13.04; a gain ratio nearer 1 would drop below 1.0. |
| **H** | proportional materials that nonetheless read reflectance | **YES** — would falsify §2.2's algebra outright. |
| **J** | a shuffled layout containing an adjacent near-proportional pair | **YES** — the 15-pair margin floor is 9.77, so this needs the shuffle to be unlucky; the rule is ≥95%, not 100%. |

---

## §7 POSITIVE CONTROLS, DECLARED IN ADVANCE (§12.3, process rules 4 and 5)

Both will be injected, measured, reverted, and the seed verified **byte-equal** after
reversion.

1. **The `Times` EMPTY-PRODUCT trap (process rule 4).** Rewrite `Times([x,y])` as the
   `a`/`b` form. An empty product is 1, so `D_XY` collapses to `|1−1| = 0` and **every**
   adjacency reads `l4_illuminant`. **Expected RED: arms B, C2, D′, G, J.**
2. **The REFUSE-EVERYTHING build (process rule 5, the trap confirmed FOUR times).**
   Force the ratio predicate to be unsatisfiable. Every adjacency reads
   `l4_reflectance`, nothing merges, **and arms A, F, G, H all score PERFECT FLOORS**
   (F reads exactly 0 — a flawless pass on a build that recognizes nothing).
   **The arms that MUST redden are C2, D′ and D** — that is precisely why they exist.

**I am recording in advance the expectation that arm F PASSES under control 2 and that
arm A FAILS under control 1 but arm F still PASSES.** *Neither floor alone is a gate;
the CONJUNCTION is* — the fifth demonstration in this arc.

**The composition changed once during design (process rule 4's second clause):** the
scenes were re-derived at a NON-INTEGER base gain after an integer-gain pilot made
`D_XY ≡ 0`. Which arm should redden was re-derived accordingly: arm A is the arm that
integer gains rendered unfalsifiable, and it is the arm the non-integer base restores to
a genuine (if still entailed) computation.

---

## §8 BOUNDS, STATED BEFORE THE RUN (§8)

**L4 is SINGLE-ILLUMINANT, NEUTRAL-SHADOW edge attribution by a local chromatic-ratio
test, and nothing more.**

- **CHROMATIC (spectrally non-neutral) SHADOWS ARE NOT HANDLED** — arm G measures this
  as a predicted failure. This is the physically common case and it is NOT solved.
- **PROPORTIONAL MATERIALS ARE IRREDUCIBLY AMBIGUOUS** — arm H. No local ratio cue can
  separate them; it would need the identity machinery L4 deliberately does not use.
- **MULTI-ILLUMINANT scenes — unsolved even computationally.** Untouched.
- **"THE ANCHOR OF THE ANCHOR" (L3's residual recursion) — untouched.** L4 uses no
  anchor at all, so it neither fixes nor inherits L3's self-corroborating centre.
- **The abstract cone-triple grain with REFLECTANCE GIVEN — inherited from T3/L1/L2/L3.**
- **ADJACENCY IS GIVEN, NOT GROWN.** The 4-neighbourhood is world layout.
- **The ratio-preserving relation is NOT transitive**; `l4_flood` takes its transitive
  closure. A chain of individually-admissible steps can merge two materials that are not
  ratio-preserving with each other. NOT tested here; NAMED.
- **L4 CLASSIFIES EDGES; IT DOES NOT RECOVER REFLECTANCE.** It does not tell L2 or L3
  anything, and no L2/L3 arm consumes an L4 attribute. Wiring the attribution back into
  constancy is a FURTHER rung.
- **The 2-D arm has ONE shadow rectangle and ONE patch, both axis-aligned, both 4×4,
  both strictly interior.** Every number is a property of THIS scene.
- **Border-ownership is used UNMODIFIED and its committed results are untouched;** L4
  changes what `val` it is SHOWN, never how it decides.

---

## §9 / §10 / §11 COMPLIANCE

- **Flag `LightingL4Params.lighting_l4` ships at `0.0` — OFF by default (§9).** The seed
  is NOT boot-loaded. Read absence-tolerantly via `MaxOver(…, default 0.0)`, **never
  `PickUnique` on a params node** (process rule 3).
- **NO committed seed file is edited.** T3, L1, L1b, L2, L3 and border-ownership seeds
  stay byte-identical. The only edit to a committed file is the additive
  `domains/seed_registry.py` registration (the mechanism L2 and L3 both used), which
  installs nothing unless the seed is explicitly requested.
- **Provenance (§10, process rule 8):** the self-audit diffs
  **`07eeda24..<this rung's commit>`**, **tracked files only** — an immutable commit
  range, never base→worktree and never a repo-wide untracked scan.
- **§11:** all git operations run inside this worktree; the canonical tree
  `/home/matt/ozma/internal` is never touched. Only paths this rung owns are staged, by
  name — never `git add -A`.

## §10 DELIVERABLES

`tools/build_vision_lighting_l4.py` → `seeds/vision_lighting_l4.json`;
`domains/lighting_l4_world.py`; `scripts/lighting_l4_measure.py` →
`results/lighting_l4_measure.json`; `tests/test_lighting_l4_migrated.py`;
`VISION_LIGHTING_L4_RESULTS.md`; ledger + ladder entries in `VISION_PROTOCOL.md`.
