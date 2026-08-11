# ATTR-THRESHOLD FALSE NEGATIVE — PRE-REGISTRATION (§3)

*Committed **BEFORE** the confirmatory run. Base `main` HEAD **fc638821**
(`git merge-base --is-ancestor fc638821 HEAD` verified, §11). Branch
`gamma-substrate/vision-ast-attr-t2-53k`, worktree
`.claude/worktrees/agent-aa49c26fd15a2ce3c`.*

**Seeds 53000–53999 are allocated to this rung and are expected to remain
COMPLETELY UNCONSUMED.** This rung is STATIC ANALYSIS OF COMMITTED JSON: it evaluates
no Term, runs no episode, draws no random number. **If the run consumes zero seeds that
is the correct outcome, and it will be reported as such, not padded.**

**Charter.** Close (as far as it is closable) the false-negative class the tripwire rung
found in its own detector and deliberately left unpatched under §5:
`VISION_TRIPWIRE_REPAIR_RESULTS.md:191-203` — *"a bound whose threshold is a STORED
ATTRIBUTE rather than a computed expression — `Lt(Attr(dist), Attr(bound))` — is atomic
vs atomic, so T1 classifies it as a flag/epoch read and MISSES it."*

---

# THE §11 RULE 4 WAIVER — DECLARED BEFORE THE RUN

§11 rule 4 forbids editing another rung's tests. **This rung's charter is to extend the
tripwire rung's detector**, so by commission it edits:

- `tools/term_ast_audit.py` (the detector — adds a tier, changes no existing verdict);
- `tests/test_tripwire_repair_migrated.py` and `scripts/tripwire_repair_measure.py`
  ONLY if the added tier changes a number they assert. **Prediction: it does not**, and
  the tripwire gate is expected to stay **21/21 with zero edits**. Any edit actually
  made will be enumerated in the results.

**No committed RESULTS file is rewritten** (§7). `VISION_UNIQUENESS_RESULTS.md`,
`VISION_TRIPWIRE_REPAIR_RESULTS.md` and `VISION_CATEGORY_RESULTS.md` stand as written; a
changed verdict is reported here as a **CORRECTION**.

---

# STEP 1 — THE AUDIT (§12.4, cited)

## 1.1 The T1 traversal, and exactly where the Attr-threshold case falls through

`tools/term_ast_audit.py`:

- `:54` `COMPARATORS = ("Lt","Lte","Gt","Gte")` — the T0 population.
- `:118` `walk_terms` recurses `dict` **and** `list`, so `match` / `where` / `effects`
  and every nesting under `Not`/`Exists`/`And`/`Or`/`Filter` are reached. **The
  traversal is not the defect** — the Attr-threshold bound IS visited and IS counted in
  T0.
- `:58` `ATOMIC = ("Lit","Const","Attr","Var")` — **`Attr` is declared ATOMIC.**
- `:91-99` `is_derived` returns `root not in ATOMIC` ⇒ `is_derived(Attr(...)) == False`.
- `:106-115` `classify` returns `any(is_derived(o) for o in operands)`.

**THE FALL-THROUGH, precisely:** for `Lte(Attr(c,'v0lo'), Attr(R,'v0'))` both operands
are `Attr`, so `is_derived` is `False` for both, so `classify` returns `False` at
`:115`. The node is a T0 hit and a T1 miss. This is by construction, not by accident:
T1's declared semantics are *"a bound compares against a COMPUTED MAGNITUDE"*, and a
stored threshold is not computed.

**The affected case is real and I measured it before writing this.**
`seeds/vision_category.json::cat_recognize` box containment is four
`Lte(Attr, Attr)` at `where.items[1].predicate.items[1..4]` — `v0lo≤v0`, `v0≤v0hi`,
`v1lo≤v1`, `v1≤v1hi` — reported by the committed detector as **T0=9, T1=0**
(`VISION_TRIPWIRE_REPAIR_RESULTS.md:116`). `VISION_CATEGORY_RESULTS.md:38-39,60`
establishes these are **load-bearing** (arm E(c): an out-of-box held-out is REFUSED).

## 1.2 What structurally separates T2's four genuine bounds from similarity's 19

I enumerated every comparator in both scopes with its operand roots **and the binding
of every variable each operand references** (scope-tracking walk; a `var_name` on a
quantifier binds that name over its subtree).

`shape_decode_loop` (19 comparators): **15** are `Count`-rooted (cardinality, excluded
by T1's declared semantics), **3** are `Gt(Attr, Lit)` config gates, and **exactly ONE**
is `Attr`-vs-`Attr`:

```
sd_redecode   Lt( Attr(obs,'decoded_epoch'), Attr(ag,'codebook_epoch') )
              obs, ag  BOTH bound by the rule's own `match` [["ag","observed","obs"]]
```

`cat_recognize`'s four:

```
cat_recognize Lte( Attr(c,'v0lo'), Attr(R,'v0') )   ... and three more
              c  bound by Exists(source=NodesOfType(ObjCategory), var_name='c')
              R  bound by the rule's `match` [["scene","has_obj","R"]]
```

**Two structural signals separate them, and BOTH are needed.**

- **S-B CODEBOOK-CROSSING.** In `cat_recognize` one operand's variable is bound by a
  quantifier ranging over a **`NodesOfType` enumeration** — a global collection of held
  candidates, i.e. THE CODEBOOK — and the other operand does **not** reference that
  candidate, so it reaches the matched observation. In `sd_redecode` there is **no
  quantifier in scope at all**: both operands are match-bound, so the comparison relates
  the matched context to itself. An *admission* bound is by definition a binary relation
  between a CANDIDATE and an OBSERVATION; a comparison with no candidate in scope cannot
  be one.
- **S-A DIFFERENT-KEY.** A bound compares a **measurement against a threshold**
  (`v0` vs `v0lo`/`v0hi`). A comparison of the **same key on two entities**
  (`glabel` vs `glabel`, `oidx` vs `oidx`, `cx` vs `cx`) is like-for-like ordering,
  dedup or flood propagation — never an admission bound.

**Corpus measurement over ALL 62 seed files** (the ground truth against which the
candidates below are judged; labels read from the compared attribute KEYS, which is
semantics used ONLY to score structural rivals, never inside the detector):

| class | n |
|---|---|
| `Attr`-vs-`Attr` comparators, all seeds | **170** |
| — codebook-crossing (S-B via `NodesOfType`) **and** different-key (S-A) | **16** |
| — everything else | **154** |

The 154 are dominated by tick guards (`touched` vs `step` ×7, `burst_step` vs `step` ×6,
`theta_step` vs `step` ×5, …) and same-key ordering/flood comparisons — exactly the
"flag/epoch read" class T1 already declares non-bound. The 16 are `cat_recognize` ×4 and
`vision_style.json::sty_project` ×12, which is **the same box-containment predicate**
(`v0lo≤v0≤v0hi`, `v1lo≤v1≤v1hi`) re-used by the style seed.

## 1.3 Discriminator candidates — and how each is measured

Every rival is scored on the **same** decisive pair: it must promote `cat_recognize`'s
four AND leave `sd_redecode` / the tripwire's `N3_epoch` synthetic alone.

| # | candidate | measurement | verdict |
|---|---|---|---|
| **R1** | promote ALL `Attr`-vs-`Attr` | count promotions on `shape_decode_loop` and on `N3_epoch` | **REJECTED — over-reports.** Promotes `sd_redecode` (similarity 0→1) and `N3_epoch`. This is T0's disease returning |
| **R2** | comparator is reachable from a `where` clause that gates an effect | check where each comparator sits | **REJECTED — separates nothing.** *Every* comparator in both scopes, including all 19 similarity ones and `sd_redecode`, is in `where`. Measured, not argued |
| **R3** | comparator participates in the refusal path / effect kind | compare `effects` of the two rules | **REJECTED — measured identical.** `cat_recognize` effects are `set_attr`×3; `sd_redecode` effects are `set_attr`×6. Effect kind does not discriminate |
| **R4** | one operand's node TYPE is a params/codebook type | resolve operand node types structurally | **REJECTED — not structurally available.** Match triples give edge names, not types; `match_type` types at most one variable. Undefined for `R` in `cat_recognize` |
| **R5** | **S-B alone** (any quantifier, incl. `Neighbours`) | count promotions corpus-wide | **REJECTED — over-reports.** Promotes 3 tick guards (`ph0_wsum` `touched`vs`rate_step`; `oo_sunit_activate` `bstep`vs`step`; `bh_sum_weights` `touched`vs`step`) quantified over `InNeighbours`. `Neighbours`/`InNeighbours` is navigation **within the observation's own locality**, not a codebook |
| **R6** | **S-A alone** (different key) | count promotions corpus-wide | **REJECTED — over-reports massively.** Promotes the whole `*_step` vs `step` tick-guard family |
| **D** | **S-A ∧ S-B(`NodesOfType`)** — the DERIVED discriminator | corpus count + the decisive pair + FP battery | **ADOPTED — see §1.4** |

## 1.4 THE DERIVED DISCRIMINATOR — tier T2 CODEBOOK-CROSSING

> A comparator is a **T2 bound** iff it is a T0 comparator whose two operands are both
> rooted at `Attr` (**exactly the class T1 misses — T2 changes NO other verdict**), AND
> one operand references a variable bound by a quantifier whose `source` is a
> **`NodesOfType` enumeration** (the codebook), AND the other operand does **not**
> reference that candidate variable, AND the two operands read **different** attribute
> keys.
>
> **`T2_bound_like := T1_bound_like ∨ codebook_crossing`.** T2 ⊇ T1 and T2 ⊆ T0 by
> construction.

This is the prompt's candidate *"one operand derives from the observation and the other
from the codebook/params"*, made structural: `NodesOfType(T)` **is** the codebook.

## 1.5 THE DERIVED NEGATIVE — the residual class is NOT structurally decidable

**The bare probe named by the tripwire rung is NOT recoverable, and I can prove it
rather than assert it.** Erase attribute-key strings and variable names (the only things
that differ) and the two ASTs are **equal**:

```
Lt( Attr(h,'dist'),  Attr(ag,'bound')          )   # a GENUINE bound
Lt( Attr(h,'epoch'), Attr(ag,'codebook_epoch') )   # N3_epoch, a DECLARED NON-bound
                                                   #   (tripwire_repair_measure.py:122-126)
⇒ canonicalised ASTs are IDENTICAL  (verified: True)
```

**No structural predicate can separate them.** They differ only in what the attribute
names MEAN. Therefore:

- **the codebook-crossing class gets a VERDICT** (T2 promotes it);
- **the match-only `Attr`-vs-`Attr` class gets a RANGE** — the audit table must report
  `[T2 lower bound, T0 upper bound]` for it, never a verdict.

This is the `VISION_COLOUR_BOUND_K1_RESULTS.md` / `VISION_MARGIN_RESULTS.md` outcome
shape: a derived negative, reported first-class (§7), **not** patched around.

---

# STEP 2 — PREDICTIONS AND ARMS (§13.1)

**Overall prediction.** T2 promotes **exactly 16** `Attr`-vs-`Attr` comparators
corpus-wide (`cat_recognize` 4 + `sty_project` 12), changes **exactly ONE** row of the
audit table (T2 category, `T1=0 → T2=4`), leaves similarity at **0**, and leaves the
tripwire rung's 7-case evasion battery and 3-case FP battery **unchanged**.

| arm | statistic | prediction | status | **the input that would FAIL it** |
|---|---|---|---|---|
| **HEADLINE — ATTR-THRESHOLD DETECTED** | T2 count on `cat_recognize` | **4** (from T1=0) | **RISKED** | any of the four `Lte(Attr,Attr)` at `where.items[1].predicate.items[1..4]` scoring `False` ⇒ FAIL. **In range: they are T1=0 today, measured** |
| **CONJUNCTION — NO OVER-REPORTING** | T2 count on `shape_decode_loop`; T2 on the 3 FP synthetics | **0** and **0/3** | **RISKED** | `sd_redecode`'s `Lt(Attr(obs,'decoded_epoch'),Attr(ag,'codebook_epoch'))`, or `N3_epoch`, scoring `True` ⇒ FAIL. **In range: both are `Attr`-vs-`Attr`, i.e. inside the class this rung reclassifies — a detect-everything build FAILS here** |
| **EVASION BATTERY (re-run)** | tripwire's 7 spellings under T2 | **7/7** | **RISKED** | any spelling regressing to 6/7 ⇒ FAIL. In range: T2 rewrites `classify`'s call site |
| **AUDIT TABLE RE-RUN** | 5 rows vs L1b's original AND the tripwire's corrected table | **exactly 1 verdict moves** | **RISKED** | ≥2 or 0 moving ⇒ FAIL. In range: 4 of 5 rows contain no `Attr`-vs-`Attr` at all |
| **DERIVED NEGATIVE (indecidability)** | canonicalised AST equality of the `dist/bound` probe vs `N3_epoch` | **EQUAL** ⇒ undecidable | **ENTAILED — declared, NOT banked** | — |
| **RANGE** | size of the undecidable residual class | reported as `[T2, T0]`, corpus-wide | **descriptive** | — |
| **POSITIVE CONTROLS** | detect-nothing AND detect-everything injected into `classify` | **both RED**, on DIFFERENT arms | **RISKED** | either degenerate build passing ALL arms ⇒ the gate is not a gate |
| **§9 OFF-DAY** | bench / L1b gate / tripwire gate / orbit law | 200/0, 21/21, 21/21, `{2:1,3:2,4:2,6:2,12:4}` | **RISKED** | any regression ⇒ FAIL |

## Process-rule compliance, stated up front

- **Rule 3 (absence-tolerant guards, never `PickUnique` on a params node)** — this rung
  authors **no seed and no rule**, so it introduces no guard. Note the audit *observed*
  `cat_recognize:where.items[0]` using `Attr(PickUnique(NodesOfType(CategoryParams)))`;
  that is T2 category's pre-existing code, **not touched here**, and is recorded as an
  observation for whoever owns that rung.
- **Rule 4 (the `Times` a/b empty-product trap)** — **this rung evaluates NO Term.** It
  inspects committed JSON structurally. **The trap is therefore INERT for this rung and
  is NOT counted as a passed control**, exactly as the tripwire rung recorded it.
- **Rule 5 (both degenerate detectors)** — a detect-nothing build must fail the HEADLINE
  and EVASION arms; a detect-everything build must fail the CONJUNCTION arm. Both are
  injected into the real detector and measured, then reverted under a sha256
  byte-equality check.

## BOUNDS carried forward (§8) — stated BEFORE the run

- **BOUND-PRESENCE IS NOT BOUND-EFFICACY.** T2 detects that a bound is *structurally
  present*. It says nothing about whether the bound *does anything*. A near-vacuous
  bound (`Lte(Attr(d), Attr(huge))`) is promoted by T2 and admits everything. **That is
  L1c's η, and it remains NAMED, NOT BUILT** — and the live example stands: T1
  continuous pose has **0/63 rows bound-determined under its own √2/2**.
- **T2 does not make the residual class decidable** — §1.5 proves it is not. The honest
  reporting form there is a RANGE.
- **T2's promotions are not validated as load-bearing.** `cat_recognize`'s four are
  known load-bearing from `VISION_CATEGORY_RESULTS.md` arm E(c); `sty_project`'s twelve
  are **structurally identical but NOT independently verified** by this rung.
- **The `NodesOfType`-only reading of "codebook" is a declared choice, not a proof.** A
  codebook reached by `Neighbours` from a hub node would be missed. R5 measures the cost
  of the looser reading (3 tick-guard false positives); the tighter reading's cost is
  one measured false negative (`topic_search_verify::select_verified_search_candidate`,
  `overlap_ratio` vs `min_overlap`, quantified over `InNeighbours` — **a genuine bound
  T2 does NOT reach**). **Both costs are reported; neither is hidden.**
