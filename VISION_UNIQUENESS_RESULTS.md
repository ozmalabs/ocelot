# RUNG L1b — THE UNIQUENESS GATE for the SILENT-ARGMIN HAZARD — RESULTS

*Confirmatory run of `VISION_UNIQUENESS_PREREG.md`, authored and **committed BEFORE the
run** at **`8015d690`** (§3). Runner `scripts/uniqueness_measure.py`; seed
`seeds/vision_uniqueness.json` (builder `tools/build_vision_uniqueness.py`); adapter
`domains/uniqueness_world.py`; gate `tests/test_uniqueness_migrated.py`; pinned raw
`results/uniqueness_measure.json`. Seeds **45340–45439** (noise floor). Base `main` HEAD
**dedd71ca** (`git merge-base --is-ancestor dedd71ca HEAD` verified). Branch
`gamma-substrate/vision-uniqueness-l1b`.*

## Engine / bench / provenance (§10)

- **Engine `7d5f50c18673`** @ `…/runners/dsl/python/substrate_rs/_native.abi3.so` —
  **shared build, Rust source byte-identical** to canonical. **This rung adds NO Rust**,
  so the shared build is a legitimate build of this tree's source (§10.1 rule 4). **No
  new engine hash — there is truly no `.rs` change.**
- `data/` symlinked to canonical (§10.2). **Baseline measured on this worktree BEFORE
  any file was added: 200 passed / 0 failed.** After the rung: **200/0**, unchanged.
- **NO new Rust, NO new constant, ONE new seed** (`vision_uniqueness`, NOT boot-loaded;
  ships `UniquenessParams{uniqueness:0.0}` **OFF by default**). **NO committed seed file
  is edited** — `git status` shows only the new files plus the one-entry registration in
  `domains/seed_registry.py`.

---

# PART A — THE AUDIT (the rung's most valuable output)

**Question: for each already-merged codebook rung, does a regime exist where ≥2
candidates fall inside the verdict bound and the `Argmin` picks silently?** The exposing
stimulus was CONSTRUCTED per rung.

| rung | search | bound | tie check | **EXPOSED?** | measured numbers |
|---|---|---|---|---|---|
| **L1 lighting** `l1_recognize` | `Argmin` over `Neighbours(ref,'has_identity')` | `Lte` 1.0 | **none** | **YES** | g=0.2: 0 rows ≥2 cand, 0 false. g=0.1: **4** rows ≥2, 0 false. g=0.08: **8** rows ≥2, 0 false. **g=0.06: 12/12 rows ≥2 (max 5), 2 false, 0 refused. g=0.05: 12/12 ≥2 (max 3), 2 false. g=0.04: 10/12 ≥2 (max 6), 4 false.** |
| **T1 continuous pose** `cp_recognize` | `Argmin` over `NodesOfType(ShapeSignature)` | `Lte` √2/2 | **none** | **YES** | **s=1: 22/63 wrong ids, ALL 22 with ≥2 candidates in bound; 63/63 rows have ALL SEVEN candidates in bound.** Winner/runner-up medians 0.2715 / 0.2969 (**margin 0.025**). |
| **T2 category** `cat_recognize` | `Exists` over an `ObjCategory` region box — **no `Argmin`, no identity assigned from a codebook** | box containment + exact signature `Eq` | n/a | **NO — by construction** | `cat_mint` dedups per signature ⇒ matching-candidate set is **always ≤1**. Baseline: 3 categories, 1 match. **Degenerate probe (two kinds SHARING a signature, OVERLAPPING boxes) MERGES into 1 category** (union box, 8 members), still 1 match. |
| **similarity / identity-untangling** `shape_decode_loop` | `Argmax` over `ShapeSignature`, but only as **label recovery AFTER** an exact verdict | **NONE — zero `Lte`/`Gte` in the whole seed**; admission is `Count(residual)==0` | none | **NOT APPLICABLE** | No verdict bound exists, so "two candidates inside the bound" is undefined. The residual hazard here is an **exact `Argmax` tie** in label recovery — a different mechanism, not measured. |
| **colour identity** `ci_assign` *(not in the brief; found by the structural audit)* | `Argmin` over `NodesOfType(ColourCategory)` | **NONE — zero `Lte` nodes** | none | **YES — the worst case** | **Equidistant probe: margin EXACTLY 0.0000** (two categories both at distance 10.0) — silently assigned. **Far out-of-gamut probe at distance 269.52 — still confidently assigned.** It has no bound, so **it can never refuse anything.** |
| **deformation** `df_recognize` *(not in the brief; found by the structural audit)* | `Argmin` over `NodesOfType(ShapeSignature)` | 3× `Lte` (`eps`) | **none** (0 `Count`, 0 `Filter`) | **STRUCTURALLY — NOT MEASURED** | Same shape as T1/L1. Declared, not measured (§8). |

## Two landed rungs are AFFECTED — corrections to the record

**1. T1 continuous pose: its verdict bound is NEAR-VACUOUS, and its clean result rests
entirely on the `Argmin`'s ranking.** This was not previously reported.

| resolution | wrong ids | rows with ≥2 in bound | candidates in bound (min/med/max) | winner/runner-up median | margin |
|---|---|---|---|---|---|
| **s=1** (native) | **22/63** | **63/63** | 7 / 7 / 7 | 0.2715 / 0.2969 | **0.025** |
| s=2 | 0/63 | 63/63 | 5 / 7 / 7 | 0.3766 / 0.4789 | 0.102 |
| **s=4** (T1's headline) | 0/63 | **63/63** | **2** / 4 / 7 | 0.3838 / 0.5641 | 0.180 |

**In EVERY ONE of T1's 63 headline trials at s=4, at least two candidates — and in the
median four — lie inside the `√2/2` bound.** T1's 63/63 and its "exact-0 discrimination"
remain TRUE as measured, but the bound is **not what is discriminating**: it admits
almost everything, and the ranking does the work. This is §13.2's *"works" vs "is
load-bearing"* applied to a threshold. T1's own results file reported the true residual
against the bound only for noise, never the candidate COUNT, so this was invisible.

**2. Colour identity `ci_assign` has no admission bound at all.** It is not that its
bound is loose — there is no `Lte` anywhere in the rule. Every observation, at any
distance, is assigned the nearest `ColourCategory`. The equidistant probe is decided by a
margin of **exactly zero**. This is the `PickUnique` lesson in its purest measured form.

**L1 is affected as it already reported** (this rung reproduces its table exactly, and
extends it: the ambiguity begins at **g=0.1**, two steps ABOVE the g≈0.06 floor where
wrong identities begin — 4 rows at 0.1 and 8 at 0.08 are ambiguous while still correct).

**T2 and the similarity path are CLEAN**, for structural reasons worth keeping: T2's
per-signature mint dedup makes rival candidates impossible, and the similarity path
admits by exact equality so there is no bound to be ambiguous inside.

---

# PART B — THE GATE

**VERDICT: the gate WORKS on L1, and it does NOT transfer to T1 — measured, and the
non-transfer is reported as a first-class result, not hidden.**

| arm | statistic | result | vs prereg |
|---|---|---|---|
| **A HAZARD REPRODUCED** *(the premise; RISKED)* | flag OFF at g=0.06/0.05/0.04: false ids, refusals | **2 / 2 / 4 false, 0 refused** | exactly as predicted ✓ |
| **B GATE REFUSES** *(the reason to exist; RISKED)* | flag ON, same gains: false ids | **0 / 0 / 0**, refusals explicit (`uq_ambiguous`, each recording `uq_ncand ≥ 2`) | 0 ✓ |
| **C NO REGRESSION** *(the §1.1 conjunction; RISKED)* | flag ON at the 5 real gains L1 scored 60/60 | **60/60 correct, 0 refused** | 60/60 ✓ |
| **D DISCRIMINATION exact-0** *(RISKED)* | cross-material false ids, flag ON | **0** | ==0 ✓ |
| **E NOISE floor** *(RISKED, n=100, 45340–45439)* | fields minting or claiming | **0/100** | 0 ✓ |
| **F NOVEL-material floor** *(RISKED)* | never-minted material force-matched | **0** | 0 ✓ |
| **G AMBIGUITY COST** *(declared in advance)* | correct rows retained at the floor | **0/12, 0/12, 2/12** | **the 0.04 proviso BROKE — see below** |
| **X OFF-DAY** *(§9; ENTAILED)* | flag at default 0 | no `uq_*` attribute written anywhere; L1 unmoved | ✓ |

**An admitted row is byte-identical to L1's own answer** — the identity is L1's `Argmin`
winner term-for-term (gated by `test_an_admitted_row_is_byte_identical_to_L1s_own_answer`).
The gate SUBTRACTS ambiguous claims and adds nothing; it **cannot widen an invariance
class** (§8), because it fires only where L1 already claimed.

## THE DECLARED COST — and the proviso that broke

**Pre-registered, before the run:** *"at the floor the gate refuses EVERY row, not only
the wrong ones… it trades 12 confident answers (10 right, 2 wrong) for 12 honest
refusals."*

| gain | ungated correct | ungated false | **gated correct** | gated refused |
|---|---|---|---|---|
| 0.06 | 10 | 2 | **0** | 12 |
| 0.05 | 10 | 2 | **0** | 12 |
| 0.04 | 8 | 4 | **2** | 10 |

**The prediction was 0/12 at every floor gain; at g=0.04 TWO rows were retained** (they
had exactly one candidate in bound). **That proviso broke and is recorded here and pinned
in the gate** (`test_the_declared_ambiguity_COST_is_pinned` asserts the `2`, not a
convenient `0`) rather than being smoothed over (§3.7). It is a small miss in the
direction of the gate being *less* destructive than predicted.

**And the cost extends ABOVE the floor, which the prereg did not anticipate:** the audit
shows 4 ambiguous rows at g=0.1 and 8 at g=0.08 — regimes where L1 is **12/12 correct**.
With the flag on, those correct answers become refusals too. **The gate buys honesty with
recall, and the exchange rate is worse than "only the wrong rows".** That is the honest
statement of what this mechanism costs, and it is why it ships OFF.

## WHY THE GATE IS BUILT ON L1 ONLY — decided in the prereg, from the audit

**A count-within-bound predicate is only meaningful where the bound is
DISCRIMINATIVE.** On L1 it separates cleanly (0 ambiguous rows in the clean regime, 12/12
at the floor). On T1 it does not: **≥2 candidates lie in bound in 63/63 trials at BOTH
the aliasing resolution AND the clean one**, so the same gate would refuse T1's landed
63/63 entirely. The discriminator at T1 is the **MARGIN** (0.025 aliasing vs 0.180 clean),
not the count.

**A margin gate is NAMED, NOT BUILT (§5/§13).** Choosing a margin threshold after seeing
which value separates 0.025 from 0.180 is precisely the magic number §13 forbids and the
metric surgery §5 forbids. It needs its own pre-registration and a derivation of what the
margin FALLS OUT of. L1 named L1b rather than bolting it on; this rung names **L1c (the
margin instrument)** and leaves it.

## THE POSITIVE CONTROLS (§12.3 / process rules 4 and 5) — measured, not asserted

**Control 1 — the `Times` trap.** `Times` takes an `items` **LIST**; the a/b form parses
to an **EMPTY PRODUCT = 1**. Injected into the gate's count predicate: **2 of 21 tests go
RED** (`test_GATE_the_ambiguous_regime_REFUSES…[0.04]` — a false identity survives — and
the cost pin). Reverting restores **21/21** with the seed **byte-equal** to the committed
one (verified by JSON compare).

**Control 2 — the refuse-everything build (process rule 5).** `Gte(count,1)` instead of
`2`: **3 of 21 go RED, and the one that matters is
`test_the_gate_does_NOT_regress_the_unambiguous_regime`.** A build that refuses
everything is caught by the no-regression arm, exactly as designed. **This is the arm L1's
own control showed was missing:** the discrimination and noise floors pass a
refuse-everything build, so neither is a gate — the **conjunction** is.

## §13.1 — ENTAILED vs RISKED, declared BEFORE the run, honoured here

**ENTAILED, reported as consistency and NOT banked:** arm **X** (the seed is not
boot-loaded and every rule is flag-gated at 0, so inertness is entailed by construction);
arm **G**'s direction (the pilot had already shown all 12 floor rows carry ≥2 candidates —
which is why G was declared ENTAILED in the prereg and why its *magnitude* miss at 0.04 is
reported rather than banked).

**RISKED — this is the result:** **A** (the premise could have failed to reproduce), **B**
(the count could have failed to reproduce the recognizer's admission set — the g=0.06
rows have exactly **2** candidates, the tightest possible test of the `Gte(…,2)`
boundary, and it is in range), **C** (a `Times` defect or an off-by-one bound makes the
build refuse the clean regime — **demonstrated live in control 2**), **D**, **E**, **F**.

**Each risked arm's failure input was stated in advance and is IN RANGE** — verified, not
asserted: control 1 and control 2 between them drove **B**, **C** and **G** red on real
injected defects. No arm passed while sitting outside the region where it could fail.

---

## AUDIT (§12.4) — composition, with file:line

**VERDICT: COMPOSE. NO new Rust. ONE new seed. NO new constant.**

| reused | where |
|---|---|
| the candidate counter | `Count` (`runners/dsl/src/jsonio.rs:1148`, `term.rs:70`) |
| the in-bound predicate | `Filter` (`jsonio.rs:1149`, `term.rs:71`) + `Lte` (`jsonio.rs:1094`) |
| the ambiguity test | `Gte` (`jsonio.rs:1102`) |
| the hub-scoped codebook | `Neighbours` (`jsonio.rs:437`) — the SAME population `l1_recognize` searches, not a global grab |
| the residual | **extracted VERBATIM from `l1_recognize`** (`tools/build_vision_uniqueness.py:_l1_residual_term`) — single source of truth, so the gate counts exactly what the recognizer admits |
| the admitted identity | **`l1_recognize`'s own `Argmin` effect term, verbatim** (`_l1_argmin_id_term`) |
| the bound `1.0` | L1's own falls-out ONE LATTICE STEP — **inherited, not re-derived and not re-tuned** |
| absence-tolerant config read | `MaxOver(…, default 0.0)` — **never `PickUnique`** (§12.3), gated by `test_the_flag_is_OFF_by_default_and_absence_tolerant` |

**No new constant (§13):** the seed's entire literal set is `{0.0, 0.5, 1.0, 2.0}` —
the flag comparison, the inherited lattice step, and the count `2`, which is **the
definition of "more than one", not a threshold**. Gated by
`test_this_rung_adds_NO_new_constant`.

**Why the gate writes only `uq_*` and never `l1_*`** — this is load-bearing, not
cosmetic. `l1_recognize`'s guard does not read `l1_recognized`, so a gate that CLEARED it
would be re-fired by `l1_recognize` on the next sweep, flipping the attribute forever;
and `run_rules` terminates on **exact value equality** (§2.1), so that build would not
terminate. A fresh attribute makes every effect value constant once set. It also keeps
both verdicts readable from ONE graph, which is what makes the comparison a measurement.
Gated by `test_the_gate_never_writes_an_L1_attribute`.

**§0 / CLAUDE.md compliance:** every decision — counting the candidates, admitting,
refusing — is a seed **RULE**. The adapter (`domains/uniqueness_world.py`) blind-writes
one flag and reads four attributes. It is source-audited **on the AST, not by substring**
(`test_no_python_decision_in_the_adapter`: no `If`/`IfExp`/`Compare`/`BoolOp` node
anywhere, and no `l1_*` literal in code) — the first version of that test used a
substring scan and was caught by its own `->` type annotation, §12's defect in miniature.
Notably the adapter does **not** combine `l1_recognized` with an ambiguity marker to
derive a verdict; that combination would be a decision, and it is made in the graph by
the two rules partitioning the claimed surfaces.

---

## §9 — defaults preserve committed results

- **Vision bench `scripts/rung7_vision_bench.sh`: 200 passed / 0 failed** with `data/` —
  identical to the baseline measured on this worktree **before any file was added**. Its
  no-Python-thresholds scan reports *"(none — every knob is graph data)"*.
- **sd orbit law `{2:1,3:2,4:2,6:2,12:4}` UNMOVED.**
- **Sibling gates: 120 passed in one process** — L1 lighting **19/19**, T3 lighting
  **27/27**, continuous-pose **6/6**, category **9/9**, colour-identity, similarity,
  identity-untangling, sdloop-vision, engine-provenance, and the new gate.
- **New gate `tests/test_uniqueness_migrated.py`: 21 passed**, and **verified to fail on
  two independently injected defects** (2 red and 3 red respectively).
- The seed is **not boot-loaded** and ships its flag at **0**; **no committed seed file is
  edited at all**, so §9 holds on the files as well as at the flag.

## BOUNDS (§8) — what this rung does NOT do

**A uniqueness / refusal gate. NOT a widening of any invariance class** — no gain, angle,
deformation or category refused before is recognized now; the gate can only turn a claim
into a refusal. Specifically NOT shown:

- **The gate is built on L1 ONLY.** T1, deformation and colour identity are audited and
  left unchanged.
- **The count-within-bound predicate does not generalise** where the bound is
  near-vacuous (T1, measured) or absent (`ci_assign`, measured). **L1c — the MARGIN
  instrument — is NAMED, NOT BUILT.**
- **`df_recognize` is flagged STRUCTURALLY and was NOT measured.**
- **The similarity path's exact-`Argmax`-tie hazard was NOT measured.**
- The gate's **cost** (refusing correct-but-ambiguous rows, from g=0.1 downward) is
  measured and is the reason it ships OFF.
- Still the named frontier, untouched: **L2** spatially-varying illuminant / Retinex,
  **L3** global illuminant inference, **L4** shadow-vs-reflectance, multi-illuminant.
- Inherited from L1: abstract cone-triple grain, reflectance GIVEN, the white-patch
  anchor assumption, six materials × two patches. The `g≈0.06` floor is a property of
  THESE materials' separation, not a universal constant.

## Why this is believed

Because it fails where it must, and because **the audit found more than the brief asked
for and it is reported against the rungs' own landed claims, not around them**: T1's
bound is near-vacuous in its own headline regime, and colour identity cannot refuse
anything at any distance. The gate itself is caught by two independently injected
defects, including the refuse-everything build that L1's control showed the discrimination
floor cannot catch. The one prediction that broke (2 rows retained at g=0.04) is pinned in
a test at its measured value, and the cost the gate imposes above the floor — which the
pre-registration did not anticipate — is stated rather than omitted.
