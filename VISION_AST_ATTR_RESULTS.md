# ATTR-THRESHOLD FALSE NEGATIVE — T2 CODEBOOK-CROSSING (RESULTS)

*Confirmatory run of `VISION_AST_ATTR_PREREG.md`, authored and **committed BEFORE the
run** at **`bfc1eef5`** (§3). Detector `tools/term_ast_audit.py`; runner
`scripts/ast_attr_measure.py`; gate `tests/test_ast_attr_migrated.py`; pinned raw
`results/ast_attr.json`. **NO seeds consumed — 53000–53999 remain CLEAN** (static
analysis evaluates no Term). Base `main` HEAD **fc638821**
(`git merge-base --is-ancestor fc638821 HEAD` verified, §11). Branch
`gamma-substrate/vision-ast-attr-t2-53k`, worktree
`.claude/worktrees/agent-aa49c26fd15a2ce3c`.*

*Closes the false-negative class the tripwire rung measured **in its own detector** and
deliberately left unpatched under §5 (`VISION_TRIPWIRE_REPAIR_RESULTS.md:191-203`) —
and **proves** the part of it that cannot be closed.*

---

# THE HEADLINE, IN ONE LINE

**A principled discriminator DOES fall out — but only for HALF the class, and the other
half is PROVEN undecidable rather than left open.**

- **RESOLVED (verdict):** a stored-threshold bound that **crosses the
  candidate/observation boundary** is now detected. **T2 category's four
  `Lte(Attr,Attr)` box-containment bounds are found: `T1=0 → T2=4`.** Similarity still
  reports **0** — T0's 19 do **not** return.
- **DERIVED NEGATIVE (range, not verdict):** a stored-threshold bound with **no
  candidate in scope** is **not structurally decidable**, and this is shown by
  AST-isomorphism, not conceded: the tripwire rung's own **declared non-bound**
  `N3_epoch` and a genuine `Lt(Attr(dist),Attr(bound))` are **the same AST** once
  attribute names are erased. For that class the audit table now reports
  **`[T2, T0]`**, never a verdict.

---

# Engine / bench / provenance (§10)

- **This rung adds NO Rust, NO seed, NO rule, NO constant, NO agent code.** It changes
  **instruments only** — the same class as the tripwire rung.
- `data/` symlinked to canonical (§10.2). **Baseline measured on this worktree BEFORE
  any file was added: 200 passed / 0 failed** (and 190/10-skipped *without* `data/`,
  which is why the symlink is part of the protocol).
- **Provenance self-audit — `fc638821..983d827d`, BOTH ENDPOINTS FIXED, tracked files
  only** (`git diff --stat fc638821..983d827d -- .`): **4 files**, all this rung's own —
  `tools/term_ast_audit.py` (M), `scripts/ast_attr_measure.py` (A),
  `tests/test_ast_attr_migrated.py` (A), `results/ast_attr.json` (A), plus the two
  prose files. **No other rung's file appears in the diff.**

## The §11 rule 4 waiver was DECLARED and went UNUSED

The prereg declared a waiver to edit the tripwire rung's gate and runner if the new tier
changed a number they assert. **It did not.** `tests/test_tripwire_repair_migrated.py`
and `scripts/tripwire_repair_measure.py` are **byte-unchanged**, and the tripwire gate is
**21/21 without a single edit** — the prereg's prediction, confirmed. The runner and gate
here **import** the tripwire rung's batteries rather than copying them, so the evasion
and non-bound batteries are re-run **as published**.

---

# STEP 1 — THE AUDIT (§12.4, cited)

## Where the Attr-threshold case falls through

`tools/term_ast_audit.py` @ `fc638821`: `:118` `walk_terms` recurses `dict` **and**
`list`, so the bound **is visited and IS counted in T0** — the traversal is not the
defect. `:58` declares `ATOMIC = ("Lit","Const","Attr","Var")`; `:91-99` `is_derived`
returns `root not in ATOMIC`, so `is_derived(Attr(...))` is `False`; `:106-115`
`classify` returns `any(is_derived(o) …)`. For `Lte(Attr(c,'v0lo'), Attr(R,'v0'))` **both
operands are `Attr`, so `classify` returns `False` at `:115`.** T0 hit, T1 miss — by
construction, since T1's declared semantics are *"a bound compares against a COMPUTED
MAGNITUDE"* and a stored threshold is not computed.

## The structural signal that separates the two populations

Enumerating every comparator **with the binding of every variable it references**:

```
GENUINE (T2 category, cat_recognize)
  Lte( Attr(c,'v0lo'), Attr(R,'v0') )      c: Exists over NodesOfType(ObjCategory)
                                           R: the rule's own `match`
INCIDENTAL (similarity, sd_redecode)  — the ONLY Attr-vs-Attr among the 19
  Lt(  Attr(obs,'decoded_epoch'), Attr(ag,'codebook_epoch') )
                                           obs, ag: BOTH from `match`; no quantifier
```

The other 18 similarity comparators are **15 `Count`-rooted** (cardinality) and
**3 `Gt(Attr,Lit)`** config gates — both already excluded by T1's own declared semantics.

**Two signals, and BOTH are required:**

- **S-B CODEBOOK-CROSSING** — one operand is a variable bound by a quantifier over a
  **`NodesOfType` enumeration** (the codebook of held candidates), and the other operand
  does not reference it, so it reaches the matched observation. An *admission* bound is
  by definition a relation between a CANDIDATE and an OBSERVATION; with no candidate in
  scope, no admission is being decided.
- **S-A DIFFERENT-KEY** — a bound is **measurement vs threshold** (`v0` vs `v0hi`).
  Same key on two entities (`glabel` vs `glabel`, `oidx` vs `oidx`) is like-for-like
  ordering / dedup / flood propagation.

## Rivals — REJECTED BY MEASUREMENT, not by argument (§13)

Each rival was scored on the decisive pair: promote `cat_recognize`'s four **and** leave
`sd_redecode` / `N3_epoch` alone.

| # | candidate | measured outcome | verdict |
|---|---|---|---|
| **R1** | promote ALL `Attr`-vs-`Attr` | promotes `sd_redecode` (similarity **0→1**) and `N3_epoch` | **REJECTED — T0's disease returns** |
| **R2** | reachable from a `where` that gates an effect | **every** comparator in both scopes, incl. all 19 and `sd_redecode`, is in `where` | **REJECTED — separates nothing** |
| **R3** | effect kind / refusal path | `cat_recognize` effects = `set_attr`×3; `sd_redecode` effects = `set_attr`×6 | **REJECTED — measured identical** |
| **R4** | operand's node TYPE is a params/codebook type | match triples give edge names, not types; `match_type` types ≤1 var — undefined for `R` | **REJECTED — not structurally available** |
| **R5** | S-B with ANY quantifier (incl. `Neighbours`) | promotes **3 tick guards** (`ph0_wsum`, `oo_sunit_activate`, `bh_sum_weights`) | **REJECTED — over-reports** |
| **R6** | S-A alone (different key) | promotes the whole `*_step` vs `step` tick-guard family | **REJECTED — over-reports massively** |
| **D** | **S-A ∧ S-B(`NodesOfType`)** | 16 promotions corpus-wide, **0** false positives on every battery | **ADOPTED** |

## The adopted tier

> **T2 CODEBOOK-CROSSING.** A T0 comparator with **both operands rooted at `Attr`**
> (exactly the class T1 misses), where one operand references a **`NodesOfType`**-
> quantified candidate, the other does **not** reference that candidate, and the two
> operands read **different** attribute keys.
> **`T2 := T1 ∨ codebook_crossing`**, so `T1 ⊆ T2 ⊆ T0` — **T2 reverses nothing, it only
> promotes** (gated: `test_t2_fires_only_on_attr_vs_attr`, `test_tier_algebra_*`).

---

# PART A — THE ARMS

| arm | statistic | result | vs prereg |
|---|---|---|---|
| **HEADLINE — ATTR-THRESHOLD DETECTED** *(RISKED)* | T2 on `cat_recognize` | **4 promoted**, all `Lte(Attr,Attr)`, from **T1=0** | 4 ✓ |
| **CONJUNCTION — NO OVER-REPORTING** *(RISKED)* | T2 on `shape_decode_loop`; non-bound battery | **T2=0** (T0=19 does NOT return); **0/3** false positives | 0 and 0 ✓ |
| **EVASION BATTERY (re-run)** *(RISKED)* | tripwire's 7 spellings under T2 | **7/7** | 7/7 ✓ |
| **AUDIT TABLE RE-RUN** *(RISKED)* | 5 rows vs both published tables | **exactly ONE verdict moves**; every T0 and T1 **reproduces exactly** | 1 ✓ |
| **DERIVED NEGATIVE** *(ENTAILED — declared, NOT banked)* | canonical AST equality | **IDENTICAL ⇒ undecidable** | ✓ |
| **CORPUS** *(descriptive)* | corpus-wide class sizes | 170 `Attr`-vs-`Attr`; **16 promoted**; **154 residual** | ✓ |
| **X — OFF-DAY (§9)** | bench, gates, orbit law | 200/0; L1b 21/21; tripwire 21/21; orbit law unmoved | ✓ |

## THE AUDIT TABLE RE-RUN — every row, every changed verdict

`T0` and `T1` are **compared cell-by-cell against the tripwire rung's published table**
(`VISION_TRIPWIRE_REPAIR_RESULTS.md:111-117`) and **all ten cells reproduce exactly**.

| rung | scope | L1b originally recorded | T0 | T1 | **T2** | residual | **range** | **verdict** |
|---|---|---|---|---|---|---|---|---|
| **colour identity** `ci_assign` | rule | *"NONE — zero `Lte`"* | 6 | 1 | **1** | 0 | `[1,6]` | unchanged (tripwire's correction stands) |
| **similarity** `shape_decode_loop` | whole seed | *"NONE"* | 19 | 0 | **0** | **1** | `[0,19]` | **HOLDS** — and now with its residual NAMED |
| **deformation** `df_recognize` | rule | *"3× `Lte`"* | 3 | 3 | **3** | 0 | `[3,3]` | unchanged — **the only TIGHT range** |
| **T2 category** `vision_category` | whole seed | *"box containment + exact `Eq`"* | 9 | 0 | **4** | 1 | `[4,9]` | **CHANGES — four bounds ARE present** |
| **L1b's own gate** `vision_uniqueness` | whole seed | *"`Lte` 1.0"* | 10 | 6 | **6** | 0 | `[6,10]` | unchanged |

### THE ONE CHANGED VERDICT, stated precisely

**The tripwire rung recorded T2 category as `T0=9, T1=0`, verdict *"unchanged — but see
the residual below"*. That residual is now measured: `T2=4`.** The four bounds are
`cat_recognize`'s box containment — `v0lo≤v0`, `v0≤v0hi`, `v1lo≤v1`, `v1≤v1hi` at
`where.items[1].predicate.items[1..4]` — which `VISION_CATEGORY_RESULTS.md:60` arm E(c)
had **already shown to be load-bearing** (an out-of-box held-out is REFUSED). The
detector now agrees with the behaviour that rung measured.

**This corrects an INSTRUMENT READING, not a measured number.** No episode, score or
seed anywhere moves. **Nothing in `VISION_UNIQUENESS_RESULTS.md`,
`VISION_TRIPWIRE_REPAIR_RESULTS.md` or `VISION_CATEGORY_RESULTS.md` is rewritten** (§7).

### A SCOPE DISCREPANCY, reported rather than quietly reconciled

The tripwire rung's table **labels** the category row `cat_recognize` but its number
(`T0=9`) is the **whole seed**; `cat_recognize` alone is `T0=5`. **The seed is
byte-unchanged since `b7c3eaeb`** (`git log b7c3eaeb..fc638821 -- seeds/vision_category.json`
is empty), so this is a labelling imprecision, not drift. Both scopes are reported here
(`T2=4` either way, since the promotions are all inside `cat_recognize`).

## THE EVASION BATTERY — re-run as published, 7/7

Loaded from `scripts/tripwire_repair_measure.py` rather than copied.

| case | T1 | **T2** |
|---|---|---|
| `E1_plain_Lte`, `E2_strict_Lt`, `E3_Lt_inside_Not_Exists`, `E4_reversed_Gte`, `E5_reversed_Gt`, `E6_double_negation`, `E7_in_a_where_clause` | ✓ ×7 | **✓ ×7** |

## THE NON-BOUND BATTERY — 0/3 false positives

| case | T1 | **T2** | why T2 must not fire |
|---|---|---|---|
| `N1_flag_read` `Gt(Attr, Lit)` | ✗ | **✗** | not `Attr`-vs-`Attr` |
| `N2_cardinality` `Lt(Count, Lit)` | ✗ | **✗** | not `Attr`-vs-`Attr` |
| `N3_epoch` `Lt(Attr,Attr)` | ✗ | **✗** | **inside T2's class** — excluded only because no codebook candidate is in scope |

**`N3_epoch` is the one that matters.** It is the same shape as the four promoted bounds,
so a detector that flags the class wholesale fails here — which is exactly what the
detect-everything control demonstrates below.

---

# PART B — THE DERIVED NEGATIVE (first-class, §7)

**The bare probe the tripwire rung named — `Lt(Attr(dist), Attr(bound))` — is NOT
recovered by this rung, and that is the correct outcome, proven not conceded.**

```
Lt( Attr(h,'dist'),  Attr(ag,'bound')          )   # a GENUINE bound
Lt( Attr(h,'epoch'), Attr(ag,'codebook_epoch') )   # N3_epoch — a DECLARED NON-bound
                                                   #   (tripwire_repair_measure.py:122-126)
⇒ erase attribute names (the ONLY difference) ⇒ ASTs IDENTICAL   [measured: True]
```

**No structural predicate can separate them**, because the distinction is what the
attribute names MEAN. Any detector that promotes the first also promotes the second, and
the second is a declared non-bound. Therefore:

- the **codebook-crossing** class gets a **VERDICT** (T2 promotes it);
- the **match-only** class gets a **RANGE** — `audit_seed` now returns `bound_range`,
  `undecidable_residual` and `range_is_tight` for every scope, and the gate
  (`test_audit_reports_a_range_not_a_verdict_where_residual_exists`) **forbids** a scope
  with residual from claiming a tight range.

**This is the outcome shape of `VISION_COLOUR_BOUND_K1_RESULTS.md` and
`VISION_MARGIN_RESULTS.md`: a derived negative, reported first, not patched around.**
The task's fallback — *"the audit table must report a RANGE (T1 lower, T0 upper)"* — is
**half-adopted and improved**: the lower bound is now **T2, not T1** (tighter by 4 on
the affected row), and the range is reported **per scope with its residual named**,
rather than as a blanket admission.

## The corpus-wide picture

| class | n |
|---|---|
| `Attr`-vs-`Attr` comparators, all 62 seed files | **170** |
| — **promoted by T2** (verdict) | **16** — `cat_recognize` ×4, `sty_project` ×12 |
| — **undecidable residual** (range) | **154** |
| — of which same-key | 28 |

The 154 are dominated by tick guards (`touched` vs `step` ×7, `burst_step` vs `step` ×6,
`theta_step` vs `step` ×5, …) — i.e. **the residual is overwhelmingly the flag/epoch
class T1 already declares non-bound**, which is why the range, though wide in count, is
not alarming in kind. `sty_project`'s twelve are the **same box-containment predicate**
re-used by the style seed.

**The 28 same-key residuals are counted INSIDE the residual, not excluded from it.** S-A
is a *measured heuristic* on this corpus, **not a proof** — a threshold stored under the
same attribute name on a params node would be a same-key bound. Excluding them would
have made the reported range flatteringly tighter on no evidence; it was considered and
declined.

---

# PART C — THE POSITIVE CONTROLS (process rules 5, 6) — measured, not asserted

Both degenerate detectors injected into the **real** `is_codebook_crossing`, gates run,
then restored (the source file is never written; its sha256 is **pinned in the gate**,
`test_positive_control_detector_source_restored_byte_identical`).

| injected defect | what goes RED | what stays PERFECTLY GREEN | what it proves |
|---|---|---|---|
| **DETECT-NOTHING** (`is_codebook_crossing → False`) | the **HEADLINE** (`T2 category 4 → 0`) and the **TABLE** arm | **the ENTIRE conjunction arm** — similarity still 0, non-bound battery still 0/3 | **process rule 5 exactly: a detector that detects NOTHING scores a PERFECT false-positive arm.** The FP arm alone is not a gate |
| **DETECT-EVERYTHING** (promote every `Attr`-vs-`Attr`) | the **CONJUNCTION** — similarity **0→1** (`sd_redecode`), and `N3_epoch` flagged | **the entire HEADLINE arm — it promotes all four correctly** | the mirror image. **The headline arm alone is not a gate either** |
| **`Times` a/b empty-product trap** (process rule 4) | **0 — INERT** | everything | **reported, NOT counted as a passed control** — see below |

**THE CONJUNCTION IS THE GATE.** The two arms pull in opposite directions and each is
scored **perfectly** by a degenerate build that the other catches. Both were injected;
both reddened.

**The `Times` trap is INERT for this rung, and is NOT banked as a control.** Process rule
4 concerns **evaluation** semantics — `Times` with `a`/`b` instead of an `items` list is
an empty product = 1 **when a Term is evaluated**. **This rung evaluates no Term**; it
inspects committed JSON structurally, so the trap cannot bite. This is the same honest
inert finding the tripwire rung recorded, and it is stated rather than counted.

**Process rule 3 (absence-tolerant guards, never `PickUnique` on a params node)** — this
rung authors **no seed and no rule**, so it introduces no guard. The audit *did observe*
`cat_recognize:where.items[0]` reading `Attr(PickUnique(NodesOfType(CategoryParams)))`;
that is T2 category's pre-existing code, **not touched here**, and is recorded for
whoever owns that rung.

---

# §9 — DEFAULTS PRESERVE COMMITTED RESULTS

- **Vision bench `scripts/rung7_vision_bench.sh`: 200 passed / 0 failed** with `data/` —
  identical to the baseline measured on this worktree **before any file was added**.
- **L1b's gate 21/21** and **the tripwire gate 21/21**, both with **ZERO edits** to
  either rung's files (`git status` shows only this rung's four files).
- **New gate `tests/test_ast_attr_migrated.py`: 24/24.** Four gates in one process:
  **74 passed**.
- **sd orbit law `{2:1,3:2,4:2,6:2,12:4}` UNMOVED** (`test_sdloop_vision_migrated` 8/8).
- **No committed artifact rewritten.** `results/uniqueness_measure.json` and
  `results/tripwire_repair.json` are byte-unchanged; this rung writes only
  `results/ast_attr.json`.

---

# BOUNDS (§8) — what this rung does NOT do

- **BOUND-PRESENCE IS NOT BOUND-EFFICACY — carried forward explicitly.** T2 detects that
  a bound is *structurally present*. It says **nothing** about whether the bound does
  anything. `Lte(Attr(d), Attr(huge))` is promoted by T2 and admits everything. **That is
  L1c's η, still NAMED and NOT BUILT**, and the live example stands: **T1 continuous pose
  is 0/63 rows bound-determined under its own √2/2** — a bound this detector would
  happily report as present.
- **T2 does not make the residual decidable.** PART B proves it is not. 154 of 170
  `Attr`-vs-`Attr` comparators corpus-wide remain in the range, not the verdict.
- **The `NodesOfType`-only reading of "codebook" is a DECLARED CHOICE with a MEASURED
  COST, and the cost is reported rather than hidden.** It buys 0 false positives; it
  costs **one measured false negative**: `topic_search_verify.json::select_verified_search_candidate`
  compares `overlap_ratio` vs `min_overlap` — **a genuine bound** — but quantifies its
  candidate over `InNeighbours`, so T2 does **not** reach it (2 occurrences, both missed;
  arm `KNOWN_FALSE_NEGATIVE`). The loose reading (R5) would catch it and cost 3
  tick-guard false positives instead. **Both costs are measured; neither is hidden.**
- **T2's promotions are not independently validated as load-bearing.**
  `cat_recognize`'s four are known load-bearing from `VISION_CATEGORY_RESULTS.md` arm
  E(c); **`sty_project`'s twelve are structurally identical but NOT verified by this
  rung.**
- **The evasion battery is not claimed exhaustive** — it is the tripwire rung's seven,
  re-run. A composition outside all seven could still evade T2.
- **Only L1b's five audit-table rows were re-run.** Other rungs' gates were not audited
  for the same weakness; the method transfers, the finding does not.
- **Nothing here revisits** T1's near-vacuous bound, `df_recognize` (still structural,
  still unmeasured), the similarity path's exact-`Argmax`-tie hazard, or **L1c the margin
  instrument — still NAMED, NOT BUILT.**

## Why this is believed

Because the discriminator was **derived against rivals that were rejected by
measurement, not by preference** — R2 and R3 were killed by showing they separate
nothing on the decisive pair, and R5's cost was counted (3 tick guards) rather than
argued. Because the tier is **algebraically constrained** (`T1 ⊆ T2 ⊆ T0`, gated) so it
can only promote, and every T0 and T1 number in the audit table **reproduces exactly**.
Because the gate is a **conjunction demonstrated rather than claimed**: a detect-nothing
build scores a perfect false-positive arm and a detect-everything build scores a perfect
headline arm, **both were injected, and each reddened the arm the other passed**. Because
the control that could not fire is reported **inert** instead of banked. And because the
half of the problem that is **not solvable was proven unsolvable** — by AST-isomorphism
against the tripwire rung's *own declared non-bound* — and is reported as a **range with
its residual named**, rather than closed with a heuristic that would have looked better
and been wrong.
