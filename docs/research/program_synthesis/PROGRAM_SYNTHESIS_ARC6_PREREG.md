# ARC 6 — PREREGISTRATION

**Date:** 2026-08-02
**Status:** REGISTERED. Written after all five ceiling probes landed and
**before** any arc-6 build begins.
**Baseline:** 35/257 (13.6%, Wilson 95% CI [9.96, 18.35]) over the runnable
split; 35/427 (8.2%) over the full corpus. Settled and twin-run reproduced
(`results/arc5_final.json`).
**Engine identity:** `5c1b472fe674…`. This is part of the baseline, not a
detail — see §6.

Arc 5 had no prereg. This one does, and every bar below is derived from a
measured ceiling rather than an estimate.

---

## 1. What the ceilings measured, and what they killed

`PROGRAM_SYNTHESIS_ARC6_PLAN.md` proposed five seams. Four have now been
measured. **Three are dead and one is small.**

| seam | honest ceiling | verdict |
|---|---|---|
| **A** — SymPy kernels as `ProgEval` oracles | **5 ids** strict (`80, 246, 248, 293, 422`) | small, alive, bar RAISED (§3) |
| **B** — `extract_function` retargeted to hub IR | **1** by retarget; 3 by two one-line seed edits; 4 language ceiling | **do not build as scoped** |
| **C** — math `ShapeSignature` recognition | **0 genuine of 252 hits** | **NULL — sixth content bet** |
| **D** — theorem-derived `RequiredProperty` | **LOO 0/36, transferable +0** | **NULL — built, sound, empty** |
| **E** — shared exact numbers | mostly already true | absorbed into §5 |
| **(new)** — **structural primitives** | **6 strict / 10 at zero new `TermNode`** | **the arc** |

### The finding that reorganises the arc

Three independent measurements converged on one fact:

- **A:** no import fixes **42/53 (79%)** of live-unreached tasks.
- **B:** only **39/257** tasks even have the `f(int)→int` signature its
  grammar can emit — **218 (85%) excluded before semantics apply.**
- **Structural:** `ProgEval` **already executes** `sorted`, `split`,
  `replace`, `join`, `capitalize`, `count`, `enumerate`, `reversed`, `round`,
  `str`, `int`, strided/negative slicing, string subscripting, comprehensions,
  `dict.items()` — and `SynthEnumerate`'s 30 op names contain **none of them.**

**The MBPP residual is dominated by list/string/dict plumbing, not
mathematics.** The mathematical residual is 11 of 53 ids. Four seams were
aimed at it. **The gap is PROPOSAL, not EXECUTION** — an op-table gap, not an
engine gap.

This does not refute "the substrate is embodied mathematics." It says the
corpus's tail is plumbing, which is a statement about MBPP, not about the
tower. Registered here so it cannot be retold later as either more or less
than that.

---

## 2. The build: tier 0 only

**Scope: 8 units, ZERO new `TermNode` variants, 10 candidate ids.**

- **B0 population (10):** `18, 75, 98, 106, 161, 257, 290, 310, 424, 450`
- **Strict, witness-verified live and in budget (6):** `75, 98, 106, 161,
  257, 290`

This is the arc-4 S4 shape exactly — a `SynthEnumerate` op-table widening with
no new Term variant. **It is the only structural move in this project's
history that converted at scale (0 → 25).**

### Explicitly NOT in scope, and why

- **`term:Sort`** — blocked on a live defect (§4).
- **`term:Recurse`** — 7 paper ids, the worst inventory-to-conversion gap in
  the taxonomy.
- **`term:Format`** — one task.
- **Tiers B1/B2/B3** (26/32/42 ids) — 17 new Term variants plus a value-layer
  correction. The cost is real and the price is the trap here (§3).

---

## 3. Hypotheses and bars

### HS1 — PRIMARY. Tier-0 widening converts.
**Bar: ≥3 of the 10 B0 ids convert**, paired-id exact, each with a
**constructed witness** (not held-out rows alone), zero coincidental fits.

Derivation: S4's own reach-to-conversion prior is **8 of 25 = 32%**, so 10 ids
⇒ ~3.2 expected. The bar is the prior, not a hope.

**Null reading, registered:** fewer than 3 convert ⇒ the S4 conversion prior
does not transfer to this class, and the inventory numbers (26/32/42) are
paper reach that should not be pursued. Report and stop.

### HS2 — SOUNDNESS. Nothing regresses.
**Bar: 35/257 does not decrease. Any regression is a hard fail**, not a
trade. The 35 pass ids are enumerated in `results/arc5_final.json`; the
after-list must be a superset.

### HS3 — COST. Tier 0 stays tier 0.
**Bar: zero new `TermNode` variants.** If the build needs one, it is not tier
0 — stop and report scope creep rather than absorbing it. This is the
registered guard against the cost-hiding mechanism §4 names.

### HS4 — The op table is task-independent.
**Bar: the shipped op table must be diffable against one written from the
operator list alone, by someone who has not seen the test split** — and the
diff must be empty.

This is registered because it is the failure that has already happened twice
today: Seam D authored one atom per task and scored 36/36 that transferred to
**0**; the A-ceiling found a 5→27→60 inflation available purely by changing
import granularity. A per-task op is the same defect wearing a third name.

### Registered null readings
- If HS1 nulls, **the structural seam is reach without conversion**, and the
  honest conclusion is that MBPP's tail resists both mathematics *and*
  plumbing — a statement worth publishing, not a failure to bury.
- If HS1 passes but HS4's diff is non-empty, **the result is void**, not
  discounted.

---

## 4. The two priced hazards

### The `sorted`-on-strings defect — a live bug in shipped code
`cmp_value` compares **interner symbol ids**, so string ordering **depends on
process history**. Proven by priming the interner: `('pear','apple','fig')` →
`('apple','pear','fig')` only by accident of interning order.

**Blast radius:** every `Set`/`FrozenSet` canonical order, `Dict` key order,
string `Gt`/`Lt`, `min`/`max`/`Argmax`.

This is **not an arc-6 deliverable** — it is a correctness defect that exists
independently of this arc and should be fixed on its own terms, with the
fixture-migration question priced before `term:Sort` is ever considered.
**Registered so that a later `Sort` build cannot quietly inherit it.**

### The two trap mechanisms are DIFFERENT, and both are registered
- **Import seams inflate by GRANULARITY** — a per-task kernel buys reach a
  general module does not (A: 5 → 27 → 60).
- **Structural seams inflate by COST HIDING** — general operators reach the
  same 42 either way (cherry-picked = 42 = the same 42), but 10 ids cost zero
  variants and 42 cost seventeen plus a value-layer correction.

**Rule minted, registered as standing:** *in an import seam audit the NAMING;
in a structural seam audit the PRICE — count variants, not names.*

---

## 5. Measurement protocol

- **Paired id lists everywhere. Never a bare count.** A count can be held; a
  list has to be read. (Minted after a count-shaped baseline stood false for
  ten days.)
- **The aggregate is UNDERPOWERED BY CONSTRUCTION and must not be the
  headline.** 35/257 → 38/257 sits inside the baseline CI [9.96, 18.35]. The
  result is the paired id list plus witnesses; the score is reported **with
  its CI and with this sentence attached.**
- **Constructed witnesses, not held-out rows alone.** Seven coincidental fits
  have been caught in this project; the two most recent (task 224, task 92/464)
  were caught by witness sweep and by engine-rebuild reconciliation, not by
  held-out rows.
- **Under-sampling is a live trap, twice in two days** — task 87 row 1 and
  task 172 row 1 each matched exactly while the program was wrong in general.
  Every claim sweeps multiple inputs.
- **A bug in the refuting direction is indistinguishable from an honest null.**
  Verify both directions by live invocation. (Today: a lost `set()` wrapper
  refuted a task 0/3; a `"the number"→"n"` rewrite read level-1 as 0 instead
  of 1.)
- **Contamination:** test-split prompt text and reference code never enter any
  codebook, cue vocabulary, bigram table, or taught shape. Test-split `code`
  may be read for MEASUREMENT only. Held-out rows never enter a detection or
  selection path. Mechanical source audits gate both.
- **Architecture:** decisions are Rules/Terms; adapters are mechanical I/O
  only. The no-Python-decision audit gates this.
- **Frozen artifacts stay byte-frozen.** Only tests change; drifted pins are
  reconciled only in the improvement direction with dated notes.

---

## 6. Engine provenance is part of a measurement's identity

Today's 34/32/35 discrepancy resolved to **engine state** — a `substrate_rs`
rebuild that changed results with no seed or Python change at all.

The hazard is confirmed live: an isolated worktree or bare script **silently
imports the canonical tree's engine**, because `substrate_rs.pth` is an
absolute path and `_native.abi3.so` is gitignored. The two binaries are
**proven distinct by symbol content** — `SumList`, `MaxLenOver`, `MinLenOver`,
`JoinList`, `LastElem` are present in `5c1b472f…` and absent from
`7dd9af13…`; the canonical binary predates arc-4 S4's list-op widening.

**Every arc-6 measurement must call `engine_preamble()` and record the engine
sha256 in its results artifact.** A number from an unknown binary is not a
measurement.

**Known open gap:** `scripts/arc6_ceiling_ab.py` does not call
`engine_preamble()` and stamps no sha; its provenance is inferred (decisively,
by symbol content) but not stamped. Recorded rather than papered over.

### AMENDMENT A1 (2026-08-02) — no bar changed; two operational hazards registered

**A1.1 — A named engine sha is not a preserved engine. Archive the binary.**
`_native.abi3.so` is a **single gitignored file that every build overwrites**.
During this arc, tier-0's rebuild replaced `5c1b472f…` **94 seconds** after the
baseline agent had copied it out. Had that copy not been taken inside that
window, **arm A would have been irreproducible — the engine it names would
exist nowhere on the machine.** A results artifact that records a sha is
therefore *not* sufficient for reproducibility; the binary itself must be
preserved out of tree alongside the measurement. Registered as standing
practice, not as a one-off.

**A1.2 — Three arms, whenever an intervention includes an engine change.**
Where a build changes `.rs` (e.g. `fix:StringAsSequence`, a semantic change to
shipped Terms), a two-arm before/after **spans two binaries** and cannot
separate the intervention from the rebuild. Required:

- **A** = baseline code + baseline engine
- **B** = baseline code + the intervention's **final** engine
- **C** = intervention code + that same final engine

**B − A is what the rebuild alone did; C − B is the intervention.** Only
**C − B** may be claimed. This is the direct application of the 34→32 finding,
where a rebuild alone corrected two coincidental fits with no seed or Python
change and was misattributed until isolated. Arms A and B must differ **by the
binary and nothing else** — including invocation flags, since any drift lands
in B − A and is read as "what the rebuild did."

**A1.3 — `evaluate({"type": X})` is NOT a probe for symbol presence.** A
malformed term raises `UnknownTermType` exactly as an unknown term does, so the
probe reports ABSENT for terms that are PRESENT. It produced a clean-looking
refutation of a correct premise during this arc. **Substring-count the binary
instead.**

### AMENDMENT A2 (2026-08-02) — HS1's registered null reading was WRONG

**Outcome: HS1 FAILED, 0 of 10 converted.** HS2, HS3, HS4 all passed.

§3 registered this null reading in advance:

> *If HS1 nulls, the structural seam is reach without conversion, and the
> honest conclusion is that MBPP's tail resists both mathematics and plumbing.*

**That reading does not apply, and it is not adopted.** It assumed the failure
would be at the proposal layer. It was not. All eight units were built and all
eight fire (verified by live invocation). For **five of the ten B0 ids** the
enumerator proposes **the exact witness the ceiling document published**, and
`ProgEval` computes **the right answer on every revealed row** — and the *row
verdict* refuses it:

```
task 257:  expected=(20,10)  got_json=[20,10]  eval_ok=1.0  cmp_ok=1.0
           got=None          ps_verdict=fail
```

`eval_and_record` stores `got` only for scalars
(`got if isinstance(got,(int,float,str,bool)) else None`), and `ps_row_pass`
requires `Eq(got, expected)`. **A tuple-valued answer can never agree, however
correct.** The correct comparison (`cmp_ok`) is already computed and already
right; the plain row rules simply do not read it.

**This retrodicts arc-4 S4**: its 25-moved/8-converted gap is explained by its
converting ops all having returned *scalars*.

**The corrected reading: the proposal-layer gap was real and is now closed; the
binding constraint moved to the row verdict.** That is a different — and
better-localised — claim than the one registered, and it is recorded here as a
correction rather than substituted silently, because a prereg whose null
readings are quietly rewritten after the fact is worth nothing.

**Not claimed:** the single aggregate gain (task 120) is a **coincidental fit**,
refuted 4/4 by constructed inputs and pinned with a live proof. **Honest
conversion count: zero.** Eighth coincidental fit of this project, self-caught.

**Registered for the next rung, before it is built:** the non-scalar row
verdict changes **acceptance semantics for every task**, so it is priced like
`fix:StrOrder` and does not enter as a tier-0-style additive unit. And `Mod` in
the per-element template pool must be decided **by someone who has not read
task 75** — adding it because 75 needs it is the structural `perrin_sum`.

### AMENDMENT A3 (2026-08-02) — the verdict rung was priced NO-GO; the value-layer fix is registered

**The seed-only verdict fix was measured and REJECTED.** Bar clauses: ≥3 of 5
convert **PASS** (4/5); 35 preserved **PASS**; **zero false accepts FAILED,
12 of 15.** Nothing was built; the seed is byte-identical to committed.

**Root cause, and it is why no comparator variant can work:** a row's
`expected` is a **graph attr**, so a list literal is already a tuple before any
comparator sees it (`{"a":[1,2,3]}` → `(1,2,3)`; `Eq((1,2),[1,2])` = True).
**The collapse is in the VALUE LAYER.** Decisive control: of the 36 baseline
passes, **zero** have a non-scalar `expected` — the collapse had never decided
an acceptance before; in the candidate it decided 12 of 15, and all 12 fail the
corpus's own `assert` under real Python. **Seven coincidental fits in one
change.**

#### HV1–HV4: bars for the value-layer fix, registered BEFORE the build

- **HV1 — soundness (primary).** **ZERO false accepts from list/tuple
  collapse.** The 12 named collapse-accepts (`222, 249, 290, 393, 418, 424,
  457, …`, full list in `results/arc6_verdict_pricing.json`) must be **rejected**
  after the fix. This is the whole point of the rung; it is a hard gate, not a
  trade.
- **HV2 — upside.** **≥6 of the 8 measured-correct ids convert**
  (`106, 161, 257, 272, 413, 436, 450, 460`), each with a constructed witness.
- **HV3 — no regression.** The **36** current pass ids are preserved; the
  after-list must be a superset. Any loss is a hard fail.
- **HV4 — completeness of the claim.** The **fold-up lane** (`fu_got`,
  `ps_foldup_accept`/`ps_foldup_reject`) carries the *same* scalar-only cast
  with **no `fu_cmp_ok`**. Either it is fixed too, or the write-up states
  plainly that non-scalar verdicts remain broken there. **"The non-scalar
  verdict is fixed" is FALSE while that lane stands.**

**Engine change is IN SCOPE for this rung** (unlike tier 0's HS3) — the fix is
in the value layer by construction. Therefore **A1.2's three arms are
mandatory**, and A1.1's archive requirement applies to the final binary.

**Out of scope, and must not be silently absorbed:** the `sorted`-on-strings
defect (registered §4) — now known to reach *live acceptance*, not just
probes. If the fix cannot be evaluated without it, **stop and report**; do not
fold two semantics changes into one measurement.

**Also registered:** `Eq(0.0, False)` is **False** in the substrate and **True**
in Python — an unregistered scalar-row looseness found while pricing. It is a
separate defect; name it, do not bundle it.

### AMENDMENT A4 (2026-08-02) — HV1 WAS MIS-DRAFTED. The error is the author's.

**HV1 and HV2 were jointly unsatisfiable as literally worded, and that is a
defect in this prereg, not in the work.** HV1 required the 12 named
collapse-accepts to be *rejected*; HV2 required ≥6 of the 8 measured-correct
ids to *convert*. **Six of the 8 are six of the 12.** No implementation could
satisfy both.

**Why it happened, recorded so the pattern is recognisable:** A3 promoted the
pricing run's *classification* to ground truth. But that classification was
produced **through the collapsing comparison**, which by construction cannot
distinguish *"accepted BECAUSE of collapse"* from *"accepted, and merely
involving non-scalars."* A bar must name a **mechanism**, not a list of ids
inherited from an instrument that could not resolve the distinction the bar
depends on.

**Resolution — both readings reported, neither substituted.** The builder
flagged the contradiction in its design document **before implementing**, which
is the correct handling.

- **HV1 on the registered MECHANISM: PASS.** `accept_requires_list_tuple_collapse
  = []` — zero, measured per id by the same instrument that previously found
  twelve.
- **HV1 as literally worded: FAIL.** All 12 remain accepted.
- Stronger than either: for all 13 newly-accepted ids `n_norm_agree ==
  n_typed_agree`, substrate return types equal reference return types, and over
  graph attrs `Eq` now agrees with Python on **every** list/tuple pair in both
  directions (`diverging_pairs: []`).

**Standing rule minted: state bars as mechanisms, not as id lists** — an id
list inherits the blind spot of whatever instrument produced it.

### AMENDMENT A5 (2026-08-02) — the battery cannot see this class of defect

The value-layer rung **shipped two real bugs and caught them**: `set_coord`
retyping relations (9 vision gates red, `BlinkBridge` frozen), and a wildcard
sentinel kind breaking construction merging. Cause: an or-pattern rewrite made
every **read** site safe and said nothing about **copy** sites.

**Neither was visible on the battery — all arms clean and twin-run identical
while both were live.** They were found only by the **paired tree-wide sweep**.

**Consequence, registered as standing:** a battery-green result on an
engine-touching change is **not** evidence of no regression. An engine-touching
rung requires a paired tree-wide sweep, arm-A versus arm-C, same condition,
with every new red enumerated and classified.

**And the sweep's own instrument was broken:** `failure_baseline_sweep.py`
omits `--confcutdir`, so in a worktree it reports a red for nearly every file.
An instrument that fails toward alarm is as useless as one that fails toward
silence — both get discounted, then ignored.

**Correction to tier 0:** `cargo test` **does** link, with
`RUSTFLAGS="-L /usr/lib -l python3.14"`. Tier 0 recorded it as a pre-existing
pyo3 linker failure; that was wrong.

### AMENDMENT A6 (2026-08-03) — two measured value-layer regressions; bars registered before the fix

The full paired sweep (946 files, both arms) found the value-layer rung caused
**two distinct regressions**, both invisible to the 257-task battery — the
second and third instances of what A5 registers. Measured by paired live
invocation with engines swapped in an isolated copy.

| case | arm A | arm C | class |
|---|---|---|---|
| `test_tmpl_item_in_listvar_fires` | solved, `distinct=1,434` | **budget**, `distinct=16,148` | **BUDGET** — 11× search-space explosion |
| `test_list_map_extracts_per_element` | solved, `distinct=17` | **max_size**, plateaus `54→129` | **GENERATION** — never enumerated at any budget |

Case 1's cause: list and tuple no longer collide, so **observational-equivalence
pruning is weaker**. Target type is *not* the cause — expected-as-tuple and
expected-as-list are byte-identical in both arms.

Case 2's cause (likely, not proven): **template-pool eligibility keyed on spec
shape** via the new `spec_is_list_shaped` default. Established as generation,
not budget or expressibility, because (a) arm A's win was the *correct* term
`MapList(lists, __item → IndexAt(__item,0))`, not a collapse artifact; (b) that
term evaluates to `[1,3]` as a genuine `list` on arm C and *would* match; and
(c) `distinct` plateaus while `max_size` rises — the generator is exhausted.

#### FX1–FX5, registered BEFORE the fix

- **FX1 — case 1 solves again**, with `distinct` back near arm A's 1,434 (not
  merely under budget). Report the number.
- **FX2 — case 2 finds the CORRECT term**, verified to be
  `MapList(… IndexAt(…,0))` and not some other term that happens to fit. A
  found-but-different term is **not** a pass.
- **FX3 — THE TRAP, and it is the primary bar.** The obvious fix for case 1 is
  to make pruning collapse list and tuple again — which would **silently undo
  the value layer**. So: **`accept_requires_list_tuple_collapse` must remain
  `[]`, and the 12 named collapse-accepts must remain REJECTED.**
  **Pruning-equivalence and semantic-equality are DIFFERENT RELATIONS** — the
  fix must separate them, not re-merge them. If the two cannot be separated,
  **stop and report**; do not trade the value layer for the search space.
- **FX4 — no regression.** The **48** pass ids preserved (superset, zero lost);
  `test_arc6_valuelayer_migrated` 35/35 and `test_goal_residual_migrated` 31/31
  stay green.
- **FX5 — the sweep does not worsen.** A full paired sweep against the current
  arm C baseline of **145 red nodes / 100 red files**; new reds enumerated and
  classified, unexplained bucket empty. A battery-green result is not evidence
  here — that is the whole point of A5.

**Engine rebuild is expected**, so **A1.2's three arms are mandatory** and
A1.1's archive requirement applies to the final binary.

### AMENDMENT A7 (2026-08-03) — A6'S DIAGNOSES WERE BOTH WRONG. The author's control was the defect.

**A6 is retracted as to mechanism.** Both registered diagnoses are refuted, and
the "decisive" control that established them could not express the distinction
it was testing.

**The wire is lossy.** `Substrate.evaluate()` serialises its Term dict through
JSON (`py.rs::pyobj_to_json`), and **JSON has one array type** — so a Python
`list` and a Python `tuple` inside a `Lit` both decode as `Value::Tuple`, **on
both arms**. The five specs were written pre-value-layer and declare
*tuple*-typed outputs; under the value layer `FilterList`/`MapList` correctly
return `Value::List`. The search was asked for something no correct candidate
could produce.

**The control was the defect, and it is the author's.** A6 recorded
*"expected-as-tuple and expected-as-list are byte-identical in both arms"* as
evidence the target type was innocent. **It is not.** It is evidence the
instrument could not express the difference — over a bare `Lit`, the two are
*literally the same spec*. This is precisely the failure this prereg warns
every agent about (*a bug in the refuting direction is indistinguishable from
an honest null*), committed at the orchestrator level and then written into the
prereg as established fact.

**Both diagnoses dissolve:**
- Case 1's 11× explosion is an **effect, not a cause** — nothing can match, so
  the search runs to its 200,000 budget and *accumulates* 16,148 on the way.
- Case 2's "never enumerated" is **false** — the term is built and evaluated,
  then correctly rejected. `IndexAt(item,0)` is pushed **unconditionally**;
  `spec_is_list_shaped` is never consulted. Refuted by reading *and* invocation.
- **Production was never affected.** `run_enumerate`, `_branch_arm_term` and
  `prog_moves._run_synth_enumerate` all already pass `_wire_rows`. **Only the
  gates used the bare wire.** These were never regressions in shipped code.

**FX1–FX5 all PASS**, and the fix is **two test files** — zero Rust, zero
`domains/`, zero `seeds/`, zero engine. `distinct` returns to arm A *exactly*
(1,434 and 17), not approximately.

**The registered remedy was built, measured, and NOT shipped.** The
`SigRel::{Exact,Coarse}` pruning split is **inert**: `distinct` 16,148 → 15,980
(−1.0%) on searches unsatisfiable by construction, byte-identical on every
search that solves. Kept at `drafts/arc6_sigrel_pruning_split.patch`. Building
the registered remedy and reporting it inert is the correct handling of a
refuted premise — not quietly dropping it.

**Standing rule minted:** *a control must be shown capable of detecting the
difference it is used to rule out.* A control that returns "identical" through
a channel that cannot represent the distinction has measured the channel, not
the hypothesis.

**A6's counts also corrected:** not 145 nodes / 100 files, but **100 non-green
files** (88 RED + 10 NOT_ESTABLISHED + 2 NONZERO) and **162 nodes across 88 RED
files**.

### AMENDMENT A8 (2026-08-03) — the `Lit` wire fix, registered before the build

Two rungs have now declined this as out of scope, and it is the root cause of
the whole A6/A7 episode: **`py.rs::pyobj_to_json` loses the list/tuple
distinction**, because JSON has one array type. `_wire_rows` is a per-caller
workaround; production callers use it, gates did not, and that asymmetry cost
one wrong prereg amendment and one wrong set of diagnoses.

**Design constraint that bounds the blast radius — this is the whole design.**
The engine already ships a tagged form (`__tuple__`/`__list__`/`__set__`/
`__fset__`, `persist.rs`), which `_wire_rows` writes. Preserve the **Python
object's actual type at encode** using that shipped form. **A bare JSON array
must keep meaning `Value::Tuple`** — every seed-resident `Lit` array literal
depends on it, and seed files never pass through `pyobj_to_json`, so they must
be byte-unaffected. Only Python-originated `Lit`s change, and each changes to
*match what the Python object already was*.

#### LW1–LW6, registered BEFORE the build

- **LW1 — types survive the wire.** A Python `list` in a `Lit` arrives as
  `Value::List`; a Python `tuple` as `Value::Tuple`. Both directions, live.
- **LW2 — bare JSON arrays are UNCHANGED.** A file-resident `Lit` array still
  decodes as `Value::Tuple`. Demonstrate against a real seed.
- **LW3 — `_wire_rows` becomes redundant, and that is checked, not assumed.**
  Show its output is now equivalent to the plain path. Do **not** delete it in
  this rung; prove redundancy first.
- **LW4 — no regression.** The **48** pass ids preserved (superset, zero lost);
  `accept_requires_list_tuple_collapse` stays `[]` and the **12** named
  collapse-accepts stay rejected; `test_arc6_valuelayer_migrated`,
  `test_goal_residual_migrated`, `test_arc6_tier0_migrated`,
  `test_synth_enumerate_migrated` all green.
- **LW5 — the sweep is the real gate.** Full paired sweep vs the current
  baseline (**162 nodes across 88 RED files**). Every new red enumerated and
  classified into: *type-blind test now correctly stricter* / *real behaviour
  change* / *pre-existing* / *environmental*. **Unexplained bucket empty.**
- **LW6 — STOP CONDITION, and it is a real instruction.** If new reds exceed
  ~40 nodes, or if any red resists classification, **STOP AND REPORT** with the
  enumeration. Do not mass-re-pin. A wave of re-pins is indistinguishable from
  a wave of absorbed defects, and this project has already retracted one
  count-shaped claim that stood false for ten days.

**Engine rebuild expected** ⇒ A1.2 three arms mandatory, A1.1 archive the final
binary. Note A7's control lesson applies directly here: **any control used to
show a type distinction survives must itself be capable of representing that
distinction.**

### AMENDMENT A9 (2026-08-04) — constraints, order-N value, and the magnitude ladder

**Framing correction, recorded because the author made it three times.** Three
guards were proposed and all three were wrong in the same way: the human gate,
a cheap-goal-convergence guard, and a bound on projected value. Each was a
**missing input** dressed as a hazard. The standing principle already covers
it: *every signal is a weight in a collapse; single-source deciding is the
failure.* **Do not add a guard where a term is missing.**

**What is missing, and why the loop would misprice without it:**

1. **Order-1 value only.** The value term is absolute headroom in tasks — a
   *spot* valuation. Re-measurement's order-1 value **is** its total value
   (completing it unlocks nothing), while a structural-primitive goal unlocks
   42 tasks *and* further goals, and a dimension-mint compounds. Under a
   correct NPV these order themselves; no guard is needed. Arc 5's π result
   (a minted dimension dropped cost by an order of magnitude) versus tier 0's
   linear operator-adding is the measured instance of the difference.
2. **No constraints.** Scope, horizon/deadline, limitations, and competing
   requirements are absent, so every goal is priced *in a vacuum*. A goal is
   not "too expensive" in the abstract — it is correct at twelve months and
   wrong at two weeks.
3. **No magnitude ladder.** Small ⇒ absorb; medium ⇒ balance in the collapse;
   **huge ⇒ push back, which is TWO actions — ask for scope AND decompose.**

**The discount is MEASURED, not chosen** — this is what makes order-N
tractable. This project has generated the attrition data: reach→conversion
**32%** (S4's 8 of 25); the structural ceiling's 42 inventory → 10 at zero-Term
cost → 6 witness-verified; seam A's 5 / 8 / 14 / 27 / 60. **And the residual
set is the calibration record**: A-ceiling projected 5 and returned 0
conversions; seam D projected 36/36 and returned 0 transferable; tier 0
projected ~3 from the 32% prior and returned 0.

**The breakdowns already exist as measured data.** A huge goal arrives with its
own tier ladder — the 42-structural-primitive goal decomposes as B0=10 / B1=26
/ B2=32 / B3=42 with per-tier cost. Decomposition splits on measured tiers, not
a heuristic.

#### MG1–MG5, registered BEFORE the build

- **MG1 — constraints are conditioned facts that LAPSE.** Horizon, scope and
  competing requirements land via `holds_under` → `ResidualCondition` (no new
  lapse machinery). The ask requests them **under T2 ignorance** — the graph is
  genuinely ignorant of scope, not refuted about it. **Demonstrate that ONE
  horizon answer reprices the pool**: ≥2 goals change relative order. That is
  the argument for asking constraints rather than per-goal approval — one
  answer reprices everything; approval returns one bit.
- **MG2 — order-N value, with attrition READ not authored.** The per-order
  factors must be **read from results artifacts** and traceable to them. **An
  authored projection is unbounded in the dangerous direction** — worse than an
  authored `cost_bits`, because it justifies rather than restrains. **A
  projection with no measured basis must default-expire at the next epoch**,
  exactly as an unconditioned human answer does. Demonstrate order-N differs
  from order-1 **on the shipped graph**, and say which goals move.
- **MG3 — the ladder routes by RATIO, not by constant.** Thresholds are ratios
  against the measured horizon; an authored cutoff is gameable the way
  `cost_bits` is. **Demonstrate the same goal changing rung when only the
  horizon changes, both directions.**
- **MG4 — decomposition: DESIGNED, NOT BUILT.** First report whether
  `question_driving.json`'s decompose / fold-up rules are **live or merely
  resident** — `gap_prioritization` and `stopping_policy` were resident and
  dead, and that check is the reason this arc did not build on sand.
- **MG5 — no regression.** 48 pass ids; `test_arc_goals_migrated`,
  `test_goal_residual_migrated`, `test_arc6_valuelayer_migrated` green. No
  Python decisions.

### AMENDMENT A10 (2026-08-04) — AG-5: the executor and the status lifecycle

**Two independent rungs have converged on this as the blocker.** The arc-goal
rung named the executor as its largest uncertainty ("a planning layer with no
hands"). The magnitude rung found decomposition **blocked on the status
lifecycle**: a parent must leave the pool or parent + children double-count the
same 42 tasks, and **nothing in this tree ever writes a terminal status** —
because retiring a goal with no executor empties the pool with nothing done.
The executor unblocks both.

**Scope: executor + terminal status + epoch producer + anti-oscillation.
NOT decomposition** (that is MG4, and it is unblocked by this rung, not
included in it).

**Only one goal class is executable.** The re-measurement goal already names an
artifact, a condition and a 15-task denominator, and
`scripts/arc6_verdict_battery.py` exists — one `route_pick`-shaped dispatch.
The other seven come from seam A's blocker split and require *building*, not
measuring. **The executor must not be able to act outside its declared class.**

**Architecture:** running a measurement script is mechanical I/O and is
admissible adapter work. **The decision of what to run is the collapse.** No
Python decisions.

#### EX1–EX6, registered BEFORE the build

- **EX1 — it actually runs.** The executor takes the selected re-measurement
  goal end-to-end, live, and **the condition refreshes as a result**. Not a
  fixture.
- **EX2 — terminal status, and the pool shrinks.** A completed goal leaves the
  pool; demonstrate the pool shrinking by **exactly one**, with the existing
  retire rule (`retired_because: source_residual_no_longer_stale`) firing.
- **EX3 — the epoch clock starts.** `arc_measure_epoch` is a counter with **no
  producer**; the executor becomes it. Demonstrate that a pending unconditioned
  reply **now expires** — the Angluin mechanism ticking for the first time.
- **EX4 — anti-oscillation, both directions.** A retired goal does **not**
  immediately re-mint; and it **does** re-mint when its condition genuinely
  re-fails. A one-directional demonstration is not a pass.
- **EX5 — THE LOOP TERMINATES, and this is the primary bar.** Run it end to
  end. Expected: re-measure → condition refreshes → residual un-stales → goal
  retires → the pool holds only unexecutable goals → **it asks**. Report what
  actually happened. **If it instead re-measures repeatedly, that is
  cheap-goal convergence observed on real data — report it as a finding, do
  not patch it.** Per A9: do not add a guard where a term is missing.
- **EX6 — no regression.** 48 pass ids; `test_arc_magnitude_migrated`,
  `test_arc_goals_migrated`, `test_goal_residual_migrated`,
  `test_arc6_valuelayer_migrated` green. Source audit passes.

**Registered for MG4, which this unblocks:**
`Sum(children.headroom × survival) == parent.orderN_headroom`, both directions.

**Still open and NOT to be silently closed:** the survival law's *shape* is
authored though its factors are not (magnitude §8.2) — the artifact justifies
"discounted twice", not "once more per order".

### AMENDMENT A11 (2026-08-04) — wire the hands to the better collapse; and the missing impotence term

AG-5 closed the loop and returned two findings that are the orchestrator's call,
not the rung's.

**1. There are TWO collapses and the hands follow the older one.** With the tier
ladder installed, `mg_sel_agid` (order-N) selects the **executable**
re-measurement goal — order-N drops the 42-task blocker to 13.64 headroom —
while `arc_sel_agid` (order-1) still selects the blocker, and `ax_dispatch`
binds `arc_sel_agid`. **Order-N independently selects the actionable goal with
no human in the scene**; the ask was needed only because of the wiring.

**Decision: wire the hands to order-N.** Justification, and its limit: order-1
credits paper inventory at **zero discount** and demonstrably misprices — the
magnitude rung showed 42 → 13.64 → ~1.9 expected, which is the arithmetic HS1
ran and which returned **0**. Order-N is measurably better calibrated *and* its
attrition factors are read from artifacts. **The known residual stands:** the
survival law's shape is still authored (§8.2), so this is "better calibrated",
not "calibrated".

**2. `ag_ask` fires on a TIE, not on IMPOTENCE.** In the unconditioned arm the
loop ended **at margin 9.5, holding a pool it could not act on, and said
nothing**. **There is no term for "I cannot act on my own agenda."** Per A9 this
is a missing term, not a hazard — do not guard it, add it.

#### WH1–WH4, registered BEFORE the change

- **WH1 — the stamp swap is behaviourally visible.** `ax_dispatch` binds the
  order-N selection. Demonstrate the executor acting on a **different** goal
  than it would have under order-1, live, in the same scene.
- **WH2 — the loop acts WITHOUT being asked.** Re-run AG-5's end-to-end
  scenario: with order-N wired, the loop should reach the executable goal
  **without needing the ask**. Report what actually happens — **including if it
  does not.**
- **WH3 — no regression.** EX1–EX6 hold; 48 pass ids; the arc-6 gate suites
  green. **`ag_ask`'s unfixed transient-Argmax exposure must not be made worse**
  (AG-5 fixed the same defect in `ax_dispatch` with two-tick agreement; `ag_ask`
  is frozen and still exposed).
- **WH4 — the impotence term: DESIGNED, NOT BUILT.** What should the collapse do
  when nothing in the pool is executable? Candidates to weigh, not assume: ask
  (a *different* question from the tie-ask), mint a goal to acquire the missing
  capability, or terminate honestly. State the trade-off and pick — but do not
  implement it in this rung.

### AMENDMENT A12 (2026-08-11) — WH1–WH4 resolved; the loop closed with nobody in it

**Outcome: WH1 PASS, WH2 PASS, WH3 PASS, WH4 PASS as scoped (designed, not
built).** Results: `PROGRAM_SYNTHESIS_ARC6_WIRE_HANDS.md`; artifact
`results/arc6_wire_hands.json`; worktree `/home/matt/arc6-wire-hands` off
`26ca9ffaa8`.

**A11's registered expectation held, and it held on the first iteration of the
first boot.** With `ax_dispatch` reading the order-N selection, the shipped boot
mints an `ExecOrder` for the re-measurement goal (order-N, 7.7) while the
order-1 collapse still names the 42-task blocker (10.0), and the loop then runs
a **real 138.6 s measurement**, refreshes the condition, un-stales the residual,
retires the goal (pool **8 → 7**), bumps the epoch **0 → 1** and closes the
order — with **`human_replies_sent: 0`**. AG-5's *"the route by which this loop
could close with nobody in it is sitting one stamp away"* was literally true;
the change is one `IfThenElse` and a **strictly dumber** adapter.

**Three findings this rung returns, none of them registered in advance.**

1. **The ask fires and is then irrelevant.** `ag_ask` still minted a question at
   iteration 0 (it reads `arc_sel_*`, margin 2.30). Nobody answered it and it
   **lapsed at the epoch the executor produced**. So `ag_ask` and `ax_dispatch`
   now read *different collapses* and, on the shipped boot, name *different
   goals*: the agent can ask about one goal while acting on another in the same
   fixpoint. Nothing broke; *"the question and the action are about the same
   thing"* has quietly stopped being true and nothing asserts it either way.
   **Registered as a property to decide deliberately, not to discover later.**
2. **The pool arithmetic is clean for the first time.** AG-5 could only show
   `8 → 7` under a *conditioned* reply, because an unconditioned one mints a
   fresh goal from the expired testimony and the net count hides the retirement.
   With **no reply at all** there is no testimony, so the retirement is visible
   in the net count directly. The arm AG-5 needed a fixture to isolate is now
   the default.
3. **The swap changed who STARTS the loop, not how it ends.** One execution,
   then it stops. The re-arm deadlock (AG-5 §5) and the missing impotence term
   are untouched, and the impotence case now reproduces under the new wiring at
   margins **35.0** (order-1) / **6.64** (order-N) — not a tie under either
   collapse, so the loop still ends silently holding a pool of 7 it cannot act
   on.

**WH4's pick, recorded so it is not re-litigated by preference: (c) TERMINATE
HONESTLY**, as an `AgendaVerdict` graph fact keyed on the pool signature, with
(a) *ask-a-different-question* and (b) *mint-a-capability-goal* deferred. The
argument is an asymmetry, not a taste: (a)'s registered risk is a **repricing
loop with no fixed point**, because AG-5 §8.3 measured that any answer penalises
the region it is about regardless of content; (b)'s is an **agenda that grows
monotonically less actionable while reading as activity**, because the goal it
mints is itself unroutable; and **(c) is the only one that produces the
measurement that would decide between (a) and (b)** — nobody has counted how
often this loop ends impotent, nor whether the impotence concentrates on one
missing `ExecClass` or spreads. **Registered for whoever builds it:** the term
must quantify over the **pool**, not the winner — the current stop string is
computed from the winner alone, in a measurement script, and a pool with one
routable goal ranked second is not impotent.

**A11's WH3 clause on `ag_ask` is satisfied structurally**: `seeds/arc_goals.json`
is byte-identical to `HEAD`, so `ag_ask`'s transient-Argmax exposure is
unchanged in every particular. Finding 1 above is a change in what the ask is
*about*, not in its exposure.

#### A12.1 — a baseline is a LIST, and this rung's baseline had to be re-taken

**Registered as standing practice.** The tree at `26ca9ffaa8` does **not build
or run out of the box** on the measuring machine: the committed
`_native.abi3.so` fails to import (`GLIBC_2.43' not found`) and the crate does
not compile on the available `rustc 1.87` (AVX-512 intrinsics — **29 `E0658`
errors**). This rung therefore measured on a **freshly built binary**,
`953b8e3fa647`, and **not** on `8311d4356082`.

Two consequences, both registered rather than absorbed:

- **A1.2's isolation is honoured the strongest way available:** the intervention
  comparison **never spans two binaries** — arms A and B run in one process on
  one binary, and the pre-change arm is `HEAD`'s own `seeds/arc_executor.json`
  loaded out of git into a second substrate. The arms differ by the seed and
  nothing else. Behavioural equivalence to the arc's usual binary was
  **measured, not assumed**: 48 pass ids and 95 accepted ids byte-identical, the
  re-measurement reproducing `newly_accepted [222]` / `collapse-dependent []` /
  NO-GO, and the blocker's order-N headroom reproducing `42 → 13.637248`.
- **`test_gr4_the_live_mbpp_pass_ids_are_unchanged` is RED under this
  condition** — its engine allowlist has three entries and a fresh binary is in
  none of them. The allowlist was **not widened**, though the measurement that
  would justify widening it is above. Red before and after the change, same
  node id.

**And the whole-suite baseline was enumerated, not counted.** Both reds in this
rung's WH3 table are named by node id and reproduce identically before and
after: `test_ex1_the_frozen_artifacts_are_STILL_byte_identical` (fails wherever
`results/` is untracked, because it witnesses via `git show HEAD:results/…`) and
`test_gr4_…` above. **`test_arc_magnitude_migrated` is 43/43 here where AG-5
recorded 42/43** — its failing assertion is a `git grep -l has_subgoal_spec`
over *tracked* files, so the same test at the same commit returns opposite
verdicts depending only on which artifacts happen to be tracked. That is not the
pre-existing failure being fixed; it is **an assertion that measures the
repository's tracking state rather than the property it names**, and it is
registered here as a gate to repair, not a green to enjoy.

#### A12.2 — A TIMEOUT IS AN ATTACKER: `finally`-based restore is not a guard

**Registered as standing practice, after tripping it.** AG-5 §9.7 named the
window between the re-measurement runner's `apply` and `revert` as a real risk.
It fired in this rung — on a **read-only confirmation run**, after all
measurements were complete and the tree verified clean. A `pytest` invocation
under a 2-minute timeout pulled in the session-scoped `live_run` fixture (which
starts the ~140 s re-measurement regardless of `-k`), and the timeout
**`SIGKILL`ed the runner inside its own `try`**. The `finally` never ran, leaving
`seeds/program_synthesis.json` patched and `results/arc6_verdict_before.json`
overwritten — the latter in the **canonical** tree, through this rung's
symlinked `results/`. Both were restored and sha-verified (the tracked file from
`git`, the untracked one from the runner's surviving stash, hash-checked against
the pristine values *before* copying back).

**The rule this registers:** *a `try/finally` save-restore is not a guard
against any wrapper that can kill the process.* For a measurement that mutates
the tree, the protection has to be (i) a lock file, and (ii) a **startup**
reconciliation that restores from any stash it finds on disk — not only a
shutdown one. Also registered: **never run a suite containing a tree-mutating
fixture under a timeout shorter than the fixture**, and prefer deselecting it
outright, because `-k` does not deselect a session-scoped fixture.

**The corollary that made recovery possible, and that should be preserved:** the
tracked file was recoverable from **git**; the untracked one only from a `/tmp`
directory that happened to survive *because* the `finally` had not run. A
measurement whose only restorable copy lives in a temp directory is one
`tmpwatch` away from unrecoverable — which is a further argument for the
re-measurement hazard AG-5 §8.7 already named (`arc6_verdict_report.py`
hard-codes its labels and output path, so a re-measurement *must* disturb
committed artifacts).

---

### AMENDMENT A13 (2026-08-11) — the impotence term, registered before the build

A12/WH4 designed and picked **(c) terminate honestly** — an `AgendaVerdict`
graph fact — but built nothing. Two things were registered for whoever built
it: **the term must quantify over the pool, not the winner**, and **it must
lapse through `gr_condition_lapse` like every other conditioned fact**. This
amendment registers the bars for building exactly that, scoped to the term
only — `ag_ask`'s tie logic, MG4/decomposition, and the other named remaining
uncertainties (silent fallback, `ag_ask`/`ax_dispatch` reading different
collapses, the re-arm deadlock) are untouched and not re-litigated here.

**The design investigation, done before drafting bars.** `ax_dispatch`'s own
route (`tools/build_arc_executor_seed.py::_routable`) is already the per-goal
"can the executor act on this" predicate — three-part key (kind +
`evidence_artifact` + `source_rid`) against the one shipped `ExecClass`. That
predicate is reused **verbatim**, lifted to the whole pool via
`Not(Exists(POOL(), g, _routable(g)))` — `POOL()` is `ag_select`'s own filter,
imported unchanged from `tools/build_arc_goals_seed.py`. **No new DSL Term is
needed**; this is exactly the "cheap" reading WH4 §5.1 predicted. The lapse
requirement is satisfiable **with zero changes to `goal_residuals.json`**:
`gr_condition_lapse`'s `match` (`[["r","holds_under","c"]]`) carries no type
constraint on `r`, so any node with a `stale` attr and a `holds_under` edge to
a `ResidualCondition` is lapsed by the existing rule, unmodified — the same
mechanism the testimony reply (`ag_reply_mints_testimony_*`) already rides
verbatim. The condition kind used is `fact_equals` against `arc_measure_epoch`,
the same "no specific condition to name, so expire at the next measurement"
idiom `TestimonyPolicy` already ships (Angluin's zero-bits reading, made
mechanical a second time).

**"Keyed on the pool signature, not the tick" is read literally, not as an
epoch-only rate bound.** `MapList` (`runners/dsl/src/term.rs`, evaluated in the
same `term.rs::evaluate` the rule engine already runs, confirmed by reading the
match arm — not a separate synth-only sub-language) turns the pool's Filter
into an ordered `Value::List` of agids in one Term; `ToJsonString` of that list
(the same `Value::List`/`Value::Tuple` → `serde_json::Array` path the coherence
probe exercises) gives a **comparable string signature with no sort** — the
mint guard compares this tick's computed signature against every **held,
non-stale** verdict's stored one by plain string `Eq`, so a genuinely different
impotent pool (even inside one epoch) mints its own verdict, and an unchanged
one does not re-mint. This sidesteps the tree's own named residual (**"no
string ordering primitive; `sorted`-on-strings is unfixed"**, `ArcGoalPolicy`'s
`tie_break` comment) because equality, not ordering, is all a signature needs
— registered here so it is not re-derived as a blocker later.

**Bars.**

- **IM1 — fires on POOL-quantified impotence, both directions.** With a
  non-empty pool where **no member** has a live `ExecClass` route,
  `AgendaVerdict{kind:"impotent"}` mints. With a non-empty pool where **at
  least one member** is routable (whether or not it is the current winner),
  it does not. Demonstrated with one constructed positive scene and one
  constructed negative scene, both live.
- **IM2 — the discriminator: does NOT fire on a winner-only misread.** The
  **shipped, untouched boot** already is this case — order-1's winner is the
  42-task blocker (unroutable) while the `re_measure` goal sits lower in the
  ranking and **is** routable. `_why_no_dispatch`'s own winner-only reading
  (WH4 §5.1) would call this impotent; the pool-quantified term must not. This
  is the bar the wrong, simpler implementation fails.
- **IM3 — no regression.** The five existing gate suites
  (`test_arc_executor_migrated`, `test_arc_goals_migrated`,
  `test_goal_residual_migrated`, `test_arc6_valuelayer_migrated`,
  `test_arc_magnitude_migrated`) produce **the same failing-node-id lists**
  before and after, paired and named, not counted. `seeds/arc_goals.json`,
  `seeds/goal_residuals.json` and `seeds/arc_magnitude.json` stay
  byte-identical to `HEAD`. `seeds/arc_executor.json` regenerates
  byte-identically from its own emitter after the edit. The adapter source
  audit (no `.evaluate(`, no `run_rules`, no `substrate_rs` import) still
  passes on any new adapter read-off.
- **IM4 — composes with the order-N wiring A11/A12 just landed.** With
  `arc_magnitude` loaded and the tier ladder installed, construct the scene
  WH2 §3.1's iteration 1 reached live: the sole routable goal has left the
  pool, so **both** `ax_dispatch`'s order-1 and order-N armed selections name
  an unroutable goal **and the rest of the pool is unroutable too**. The
  impotence fact must fire there specifically, and must not fire in the same
  scene one step earlier, while the routable goal was still in the pool.
- **IM5 — mint-once by pool signature, lapse via the UNMODIFIED
  `gr_condition_lapse`.** Two (or more) `run_rules()` passes over an unchanged
  impotent pool mint exactly one non-stale `AgendaVerdict`, never a duplicate.
  Bumping `arc_measure_epoch` marks the held verdict `stale` — asserted to be
  `gr_condition_lapse` firing (the rule is not touched by this rung; the gate
  reads the seed to confirm `goal_residuals.json` is byte-identical to `HEAD`
  while the staleness still changes).

**Registered null reading.** If the pool-quantified `Not Exists` predicate
turns out to require re-deriving `_routable` per pool element at a cost that
threatens seed size the way `RUNNER_UP`'s naive form once did (`ag_select`
design precedent, 2.4 MB), that is a clean finding to report, not a build to
force — `_routable` is a fixed-size predicate over one `ExecClass`, so this is
not expected, but the discipline is named in advance per this arc's standing
practice.

---

### AMENDMENT A14 (2026-08-11) — the impotence CAMPAIGN: measure (a) vs (b), before building either

A13 built `ax_impotent` and named, unbuilt, exactly the gap this amendment
registers bars for (its §8 item 3, quoted in full because it is this rung's
charter): *"THE OTHER TWO CANDIDATES ((a) ask-a-different-question, (b)
mint-a-capability-goal) ARE NOW MEASURABLE, AND STILL NOT BUILT…
`AgendaVerdict.nearest_unroutable_kind` / `.exec_classes_held` are exactly
that count's raw material, but no sweep across scenes has been run to
actually decide (a) vs (b) — this rung built the measuring instrument, not the
measurement campaign."* This amendment registers the campaign's bars, before
running it, per this arc's own §3 house rule ("measure the ceiling before
building, every time").

**The design investigation, done before drafting bars.** Two things were
established by reading the shipped seeds rather than assumed:

1. **The goal-kind space is small and closed.** `tools/build_arc_goals_seed.py`
   mints exactly four `ArcGoal.kind` values on this graph:
   `re_measure` (the ONE routable kind — `residual_stale` source),
   `supply_blocker` (`residual_blocker` source — three shipped instances,
   `missing_structural_primitive` / `budget` / `missing_dimension`),
   `source_claim` (`not_ingested` source — four shipped instances, each
   `headroom_n=1.0`, UNSIGNATURED so each pays `w_unsignatured=25.0`), and
   `reported` (`self_concern` source — zero shipped instances; requires a
   `SelfConcern` node reachable only through the separate gap-awareness
   pipeline this seed set does not load). A sweep must draw its scenes from
   exactly this space — inventing a fifth kind would not be evidence about
   this system.
2. **The pool has exactly one internally-reachable exit.** A goal leaves
   `POOL()` only by (i) `ag_remeasure_retire` (real execution — and the ONE
   `ExecClass` can only ever retire a `re_measure` goal) or (ii) the
   `headroom_n → 0` synthetic path A13 §7.1 already validated as safe
   (`ax_rearm` never inspects it, unlike `status → 'retired'`, which walked
   straight into the anti-oscillation latch). **Nothing in this tree can
   currently retire a `supply_blocker` or `source_claim` goal on its own** —
   doing so requires an external actor (a human supplying budget, building a
   structural primitive, etc.), which is exactly the capability gap this
   campaign is measuring the shape of. This means the loop's OWN naturally
   reachable impotent state is a SINGLE state (up to which goal testimony
   happens to have penalised) — concentration on the natural trajectory is
   TRIVIAL, a fact about capability COUNT, not about the underlying kind
   distribution. The kind-distribution question A12/WH4 actually asked
   therefore needs a wider sweep than the loop's own current reach — built
   HONESTLY, as (b) itself would be, per the general legal path
   `ArcGoalPolicy` already documents (weights are authored graph data): the
   same `headroom_n → 0` technique, applied to *other* kinds, is used to
   explore what the impotence verdict would say about hypothetical pool
   states this system does not yet have the hands to reach on its own —
   every such scene is labelled HYPOTHETICAL in the artifact and never
   conflated with the one REAL, currently-reachable trajectory.
3. **Testimony (`ag_ask` → reply → `gr_move_penalty`) is a REAL, already-built
   mechanism that reweights the remaining pool without changing its
   membership** — AG-5 EX5 arm 2 already measured this shifting the winner
   from `supply.budget` to `claim.seam_b` under repeated replies. Because
   `REGION(g)` falls back to `g.agid` whenever `sig_seam` is unset (true of
   every `supply_blocker` and `source_claim` goal on this graph), a reply
   penalises the SPECIFIC asked-about goal, not a class of goals — so
   chaining replies through an already-impotent 7-goal pool is a second,
   REAL (not hypothetical) axis of variation for `nearest_unroutable_kind`,
   using only the adapter's existing `attach_reply` translation, zero new
   mechanism.

**Bars, registered before the sweep is run.**

- **IC1 — the sweep's own methodology is sound and reproducible.** Every scene
  is a legitimately reachable graph state: either a REAL live execution (the
  `live_run`-equivalent, order-1 and order-N, at most one live remeasurement
  per collapse — this campaign does not need a second one, because A13 IM4
  and this campaign's own group 1 already establish the synthetic
  `headroom_n → 0` path reproduces what a real execution reaches), or the
  SAME narrow `headroom_n → 0` attribute poke A13 §7.1 validated, or a real
  `attach_reply` (never a hand-faked `AgendaVerdict`, never a `status →
  'retired'` bypass, never an edited `ArcGoalPolicy` weight, never an
  invented `ArcGoal.kind`). Every HYPOTHETICAL scene (group 3/4 below,
  reachable only by depleting goals this system cannot currently retire
  unaided) is labelled as such in the artifact and reported separately from
  the REAL/natural-trajectory scenes. At least one twin-run determinism
  check (the `IM5` precedent). No Python decision in the sweep script beyond
  which scene to construct next — every verdict read is `axe.agenda_verdicts`,
  the same pure read-off the adapter already ships.
- **IC2 — a concrete, falsifiable concentration/spread threshold, fixed before
  looking at the data.** Over the SWEEP SET S = every DISTINCT impotent pool
  signature (`pool_agids`) reached across groups 1–4 (real, testimony-shifted,
  and hypothetical-depletion scenes together — deduplicated by signature, so
  a scene reached two ways counts once): let the modal `nearest_unroutable_kind`
  value account for fraction *f* of |S|.
  **CONCENTRATED if *f* ≥ 0.75. SPREAD if *f* ≤ 0.50 (i.e. at least half of
  S's distinct impotent states name a DIFFERENT kind than the mode). AMBIGUOUS
  in between, or if |S| < 5** (too few distinct signatures to read a
  distribution) — either counts as a clean null on this bar, not a tie-break
  in either direction. Reported SEPARATELY: the same statistic computed over
  the REAL-only subset (groups 1–2), since that is the currently-decision-
  relevant population, with the trivial-concentration reading of finding 2
  above stated explicitly rather than let it pass as if it were evidence
  about the kind space.
- **IC3 — the GO/NO-GO criterion for building (a) or (b), stated as a
  COMPOUND test, because A12/WH4 §5.2 already registered a decisive,
  frequency-INDEPENDENT objection to each candidate and a concentration
  number cannot by itself discharge either:**
  - **GO for (b)** (mint a capability-acquisition goal, e.g. for
    `supply_blocker`) requires ALL of: (i) IC2 reads CONCENTRATED on the
    REAL-only subset; (ii) the hypothetical extended sweep does not
    contradict that concentration at scenes near the CURRENT pool
    composition (i.e. the dominance is not an artifact of removing exactly
    one goal); AND (iii) A12/WH4's registered objection — the minted goal is
    itself unroutable, so each impotence event grows the pool
    monotonically less actionable — has been independently resolved or
    shown not to apply (e.g. a concrete, cheap, ALREADY-EXISTING runner this
    campaign finds that could discharge the named capability, not assumed).
    Condition (iii) is a check to actually perform, not a foregone
    conclusion either way.
  - **GO for (a)** (ask a different, impotence-specific question) requires
    ALL of: (i) IC2 reads SPREAD on the REAL-only subset; (ii) A12/WH4's
    registered objection — ANY reply penalises the region it is about
    regardless of content, so an impotence-ask risks a repricing loop with
    no fixed point — is measured NOT to apply in this campaign's own group-2
    testimony-chain scenes (i.e. the chain reaches a fixed point rather than
    cycling).
  - **If neither compound condition is met, NO-GO for both.** The
    concentration/spread read is still reported as the honest answer to the
    measurement question; a NO-GO here is a complete, valuable result under
    this arc's own standing culture of clean nulls (M0's four ceiling
    probes, the D-seam leave-one-out), not a failure to find something to
    build.
- **IC4 — no regression.** The five existing gate suites
  (`test_arc_executor_migrated`, `test_arc_goals_migrated`,
  `test_goal_residual_migrated`, `test_arc6_valuelayer_migrated`,
  `test_arc_magnitude_migrated`) produce the same failing-node-id lists
  before and after this rung, paired and named, not counted. If this rung
  builds nothing (the registered null path), IC4 reduces to "the sweep script
  and its artifact are the only new files, and every existing seed / adapter
  is byte-identical to `HEAD`" — asserted, not assumed.

**Registered null reading, stated in advance.** If IC2 reads AMBIGUOUS, or if
IC3's compound test is not met for either candidate, this rung builds
NOTHING beyond the measuring campaign itself (the sweep script and its
artifact) and reports the concentration/spread read as the complete result —
exactly the shape A13 §7's own null-reading discipline names, one rung up.

Not a score. **35/257 → 38/257 is not detectable and will not be claimed as
detection.**

The arc succeeds if it establishes, with witnesses, whether the proposal-layer
gap is real and convertible — and it succeeds equally if the answer is no,
provided the answer is clean. Three seams already returned clean nulls today,
and those nulls are the most useful output of the day: they redirected the arc
from mathematics it already owned to plumbing it could already execute but
could not propose.

**The measured claim to settle:** *can the enumerator propose what the
evaluator can already run, and does that convert?*

---

### AMENDMENT A15 (2026-08-11) — the second `ExecClass`: a ceiling probe on the executor's reach

Four consecutive rungs (A10/AG-5, A11/A12/WH1-4, A13, A14) have independently
named the same standing gap: `ax_dispatch` has been built, wired to the
better collapse, extended with an impotence term, and swept for a
concentration/spread verdict — but its entire demonstrated reach is **exactly
one `ExecClass`**, one goal `kind`, one runner
(`scripts/arc6_remeasure_row_verdict.py`). A14 §9.2 names this explicitly as
the reason its own real-only bar cannot be powered further: *"only new
capability (an execution route for a second `ExecClass`) or further
hypothetical depletion can [add a third distinct composition] ... the
campaign cannot power its own real-only bar without partially pre-empting
the question it is asking."* This amendment registers bars for a ceiling
probe on that reach, in the same spirit as M0 and A-ceiling: **measure
before building**, and report an import-list-style answer even if the
answer is a clean NO-GO.

**The design investigation, done before drafting bars.** Read before any bar
was written, mirroring A13/A14's own practice of investigating first and
letting the investigation justify the bars:

1. **The full residual set is six, not one.** `domains/goal_residual_ingest.py`'s
   `SPEC` carries **six** entries, each a `GoalResidual` with a `holds_under`
   edge to a `ResidualCondition`, each eligible for `ag_mint_remeasure`
   (`seeds/arc_goals.json`, byte-frozen) to mint an
   `ArcGoal{kind:'re_measure'}` the moment its condition lapses:
   `arc6.seam_a.import_oracle`, `arc6.seam_b.ir_retarget`,
   `arc6.seam_c.shape_codebook`, `arc6.seam_d.property_atom`,
   `arc6.structural.enum_op_table`, and `arc6.verdict.row_verdict_seed_only`
   (the ONE wired one). All six carry the identical structural shape —
   confirmed by reading `seeds/goal_residuals.json` directly, not assumed:
   every one is a `GoalResidual` node with a `rid`, a `stale` attr and a
   `holds_under -> ResidualCondition` edge.
2. **The four `arc6.claim.*` goals (`ax_dispatch`'s other pool members) are a
   DIFFERENT, weaker shape and are NOT re-measurable in this sense.**
   `tools/build_arc_goals_seed.py`'s `claims` tuple mints them as
   `ArcSourceClaim` nodes — `denominator_n: 1.0`, `headroom_n: 1.0`, a
   verbatim-quoted prose string, **no `ResidualCondition`, no `stale` attr,
   no lapse mechanism of any kind**. `ag_mint_source_claim` mints their
   `ArcGoal{kind:'source_claim'}` unconditionally, once, from the static
   node — there is nothing here that could ever re-trigger without
   inventing an entirely new condition-and-lapse apparatus for
   `ArcSourceClaim`, which is a materially bigger and different build than
   "wire a second `ExecClass`." **Ruled out as candidates for this rung's
   cheap-wiring question**, answering the task's own §1 question directly:
   no, they are not re-measurable in the row-verdict sense.
3. **Every one of the five unwired residuals already has a standalone
   measurement script that writes its evidence artifact**, in the identical
   shape `arc6_verdict_report.py` has for row-verdict (a fixed, hard-coded
   `OUT` path, no argv needed): `scripts/arc6_a_ceiling.py` (seam A),
   `scripts/arc6_bc_ceiling.py` (seam B **and** seam C — one script, one
   shared artifact, two `rid`s), `scripts/arc6_d_loo.py` (seam D),
   `scripts/arc6_structural_ceiling.py` (the structural residual). None of
   this rung's investigation needed to write a new measurement — only a
   thin runner wrapper, mirroring `arc6_remeasure_row_verdict.py`'s
   stash/subprocess/restore shape.
4. **`reingest_evidence` (`domains/arc_executor.py`) is ALREADY generic over
   `rid`.** It looks up the matching entry in `gri.SPEC` by `rid` and reads
   the SAME dotted paths (`honest_ids_path`, `denominator_path`,
   `mechanism_path`, `engine_sha_path`) the original ingest used — read in
   full, confirmed there is no row-verdict-specific logic in this function
   at all. Wiring a second residual therefore needs **zero changes** to
   `goal_residual_ingest.py` or to the re-ingest half of
   `domains/arc_executor.py`.
5. **`ax_dispatch` / `ROUTE` / `_routable` / `_dispatchable`
   (`tools/build_arc_executor_seed.py`) are ALREADY generic over the
   `ExecClass` table, confirmed by reading the Term builders, not assumed
   from the prose comments.** `ROUTE()` is
   `Argmin(Filter(NOT_("ExecClass"), ec, _cue_matches(ec, goal)), priority)`
   — a filter over **every** `ExecClass` node, not a single hard-coded one.
   Adding a second `ExecClass{name:'re_measure', runner:<new>,
   evidence_artifact:<new>, source_rid:<new>}` node requires **zero new
   rules**: the existing `ax_dispatch`, `ax_impotent`'s `_dispatchable`, and
   `_routable`'s three-part key (kind + evidence_artifact + source_rid,
   AG-5 §8 item 2's own measured reason for the three-part key) all
   discriminate the new class from the old one automatically, because the
   key already includes `evidence_artifact` and `source_rid` and the two
   residuals have different artifacts and different rids. This is the
   single most load-bearing fact in this investigation: **the cost of a
   second `ExecClass` is a SEED DATA addition, not a rule change.**
6. **Live-probed, not assumed: the five unwired residuals' conditions are
   currently WEAKER than row-verdict's.** `grep`'d across every caller in
   the tree (`domains/`, `scripts/`, `tests/`): `goal_residual_ingest.
   probe_facts`'s `expected_shas` parameter — the thing that would make an
   `<artifact>_present` fact check CONTENT (sha), not just existence — is
   **never populated by any call site**. So today, the only way any of the
   five `<artifact>_present`-conditioned residuals can lapse is outright
   **file deletion**, never content drift, unlike row-verdict's
   genuinely behavioural `value_layer_list_eq_tuple` engine probe. Named as
   a real, load-bearing asymmetry between the wired residual and the
   candidates — not a disqualifier, but the honest shape of what "genuinely
   re-measurable" means for each.
7. **And yet: a live re-run shows the asymmetry in #6 is hiding REAL drift.**
   With `results/arc6_structural_ceiling.json` stashed first and restored
   after (byte-identical, sha-verified both before and after — the
   protected-file discipline A12.2/A14 §7.2 register as mandatory for any
   tree-touching probe), `scripts/arc6_structural_ceiling.py` was re-run on
   this rung's engine (`953b8e3fa647`). It completed in **0.13 s** (`/usr/bin/
   time -v`, exit 0) and produced a **genuinely different** result from the
   committed evidence (measured on `engine_provenance.sha256 ==
   5c1b472fe674…`, an older engine): `witness_ids` grew from **7 to 9**,
   gaining tasks **424 and 450**. This is real engine drift the current
   condition mechanism cannot see (per #6, only file-presence is checked) —
   an honest, additional, **unregistered-but-found** residual of the
   pipeline, reported here and not repaired (repairing `probe_facts`'s
   sha-check is a bigger, separate lift than "wire a second `ExecClass`"
   and is out of this rung's scope).
8. **One candidate carries a real environmental cost the others do not.**
   `scripts/arc6_a_ceiling.py` requires `sympy`; on this measuring machine
   `sympy` is importable under `/usr/bin/python3` (3.12) but **not** under
   the `python3` resolved first on `PATH` (Homebrew 3.13, the interpreter
   `substrate_rs` and every other measurement in this rung ran under).
   `scripts/arc6_bc_ceiling.py`, `scripts/arc6_d_loo.py` and
   `scripts/arc6_structural_ceiling.py` have **no** third-party dependency
   beyond `substrate_rs` and in-repo `domains/*` modules — confirmed by
   reading their import blocks. **Incident, recorded in full because the
   process is the result (A11/A12/A13/A14's own standing practice):** the
   first attempt to probe seam A's cost tripped exactly this gap —
   `arc6_a_ceiling.py`'s `main()` caught the `ImportError` internally and
   wrote a **partial** artifact to its hard-coded `OUT` path before
   returning 1, silently corrupting the canonical, symlinked
   `results/arc6_a_ceiling.json` (sha `c65bfc0e…` → `e95078cd…`). A stash
   had been taken before the probe per this rung's own registered
   discipline (§ above), so recovery was immediate and sha-verified
   (restored to `c65bfc0e…`, confirmed byte-identical); `git status
   --porcelain` in the canonical tree was re-checked clean throughout,
   since `results/` is gitignored and the corruption would not otherwise
   have shown as a tracked diff. **The rule this adds to A12.2's own
   registered practice:** stash the protected file(s) BEFORE running ANY
   measurement script directly, even a fast one with no known
   tree-mutation hazard — the hazard here was not a timeout, it was a
   script's own internal error-handling path writing a partial result to
   its hard-coded output on FIRST TOUCH, with no `finally` to catch it.
9. **Runtime, measured or self-reported, is cheap across the board** — far
   below row-verdict's ~140 s: `arc6_bc_ceiling.json` self-reports
   `elapsed_seconds: 1.6`; `arc6_d_loo.json` self-reports `elapsed_seconds:
   8.37`; `arc6_structural_ceiling.py` measured live at **0.13 s** (#7).
   `arc6_a_ceiling.py`'s own runtime was not measured this rung (blocked by
   #8 under the default interpreter; not re-attempted under `/usr/bin/
   python3` to avoid a second live touch of a residual not chosen as the
   candidate).

**Bars, registered before any seed, adapter or runner change is written.**

- **EC1 — at least one genuinely re-measurable second candidate exists on
  the graph, MEASURED, not assumed.** Satisfied if: (i) `goal_residual_ingest.
  SPEC` is enumerated in full and every entry's structural shape
  (`GoalResidual` + `ResidualCondition` + `ag_mint_remeasure` eligibility) is
  confirmed by reading the seed, not the docstring; (ii) an existing runner
  script is identified for the chosen candidate; (iii) AT LEAST ONE candidate
  is shown, by a real (stash-protected, sha-verified) live re-run, to produce
  content that genuinely differs from its committed evidence on this rung's
  engine — the same "it can re-fail, not just hold" standard A13/EX1's own
  gate applies to a condition (AG-5 §2.2 / A13 IM-precedent), applied here to
  the CONTENT rather than only the presence-condition.
- **EC2 — a concrete cost estimate for wiring the top candidate, in files and
  rule count, produced by reading the ACTUAL generality of `ax_dispatch` /
  `ROUTE` / `_routable` / `_dispatchable` and `reingest_evidence`, not
  estimated in the abstract.** Satisfied by a table of exactly which files
  change, how many new rules (a number, not a range), and confirmation
  (by reading, not by assumption) of whether `ax_dispatch`'s own
  route-matching Terms need to change shape at all or only receive a second
  data row.
- **EC3 — the GO/NO-GO threshold, named before looking at the cost number.**
  **GO** iff a candidate clears EC1 AND its EC2 cost is **≤ 2 new seed
  rules, ≤ 1 new runner script, and no change to `ax_dispatch`'s own
  route-matching Term structure** (only new `ExecClass` seed DATA). If GO:
  build exactly that candidate — one `ExecClass` node + edge, one runner
  script mirroring `arc6_remeasure_row_verdict.py`'s stash/run/restore
  shape sized to the candidate, one `RUNNERS` table entry — gate it with
  live scenes in the same shape EX1/WH1/IM1 used (it actually runs, live,
  not a fixture; the route confinement still holds in both directions;
  no regression on the five existing suites, node-id list not count), and
  if time and the registered null-reading discipline allow, re-run a
  SCOPED slice of A14's own sweep to see whether the new capability
  produces a genuinely distinct real pool state — not to re-litigate A14's
  own IC2/IC3 verdict, which stands as measured, but to report whether the
  ceiling this rung raises actually moves what A14 §9.2 named as the
  blocker. **NO-GO** — report the ceiling as a clean, named import-list
  (mirroring M0's four ceiling probes and the D-seam leave-one-out) and
  build nothing — if EC1 fails (no candidate shows real re-measurable
  drift) or every candidate's EC2 cost exceeds the threshold above.

**Explicitly out of scope, per the task's own boundary, unchanged from
A13/A14:** the re-arm deadlock (AG-5 §5), the silent order-N fallback
(WIRE_HANDS §8.1), and `gr_condition_lapse`'s closed `MISMATCH` vocabulary
(A13 uncertainty #1 / A14 §8's own discovered finding) are NOT to be
touched by this rung even if a fix would make the chosen candidate's
condition more behaviourally accurate (per finding #6/#7 above) — repairing
`probe_facts`'s sha-check is named as a follow-up, not built here.

---

### AMENDMENT A16 (2026-08-11) — MG4: order-N decomposition, the piece A9 designed and A9/A10/A11 all declined to build

The magnitude rung (`PROGRAM_SYNTHESIS_ARC6_MAGNITUDE.md` §6) designed
decomposition in full — `mg_decompose`, the child-mint shape, the registered
arithmetic identity — and built none of it, because the parent could not
leave the pool without a terminal status and nothing in the tree wrote one.
The executor rung (A10) built the status lifecycle (`ax_retired_epoch`,
`ax_rearm`) for a DIFFERENT goal kind (`re_measure`) and, in its own §10,
reported wanting to build MG4 anyway, declining only because *"this rung's
own mechanism has a reach of one node, and adding a second mechanism on top
of a one-node demonstration is how a measured result becomes a story."* That
reach concern is weaker now than when it was written: the executor has since
gained a SECOND `ExecClass` (A15, seed data not a rule change) and four more
rungs of regression history to build against. Decomposition is a THIRD,
independent mechanism from either — it operates on `ArcGoal`/`ArcTier` data
alone and needs no `ExecClass`/dispatch machinery of its own — so this
amendment does not inherit A10's reach objection by association; it states
its own bars.

**The design investigation, done before drafting bars — three decisions the
design underspecifies, made here and named, not discovered mid-build.**

1. **The parent's pool-exit does NOT edit `seeds/arc_goals.json`.** The
   design's own §6.2(2) considered adding a `"decomposed"` status to
   `POOL()`'s filter and declined because it requires editing the
   byte-frozen `arc_goals.json`. It still does, if the exclusion is written
   as a literal third status disjunct there. **This rung does not do that.**
   `POOL()` already excludes on `Gt(headroom_n, 0.0)` — the SAME clause A13
   §7.1 and A15 §4.2 already validated as a safe, narrow pool-exit technique
   (`headroom_n → 0`) for constructing scenes. Setting the parent's own
   `headroom_n` to `0.0` at decomposition time removes it from `POOL()` —
   and therefore from BOTH `ag_select`'s order-1 pool and `mg_select`'s
   order-N pool, since `mg_select`'s pool is `ag_select`'s own `Filter`,
   machine-lifted verbatim — with **zero edits to `arc_goals.json`,
   zero change to its pinned margin, zero risk to the byte-identical gates
   every rung since MG1 has carried.** `status: "decomposed"` is still
   written, exactly parallel to `"retired"`, but as a **descriptive,
   readable terminal token** for a human or a later rung to query — the
   mechanical exclusion is the existing headroom clause, not the string.
2. **Decomposition respects the SAME horizon truncation the parent's own
   order-N value already respects.** `mg_decompose` mints a child only for a
   tier that is `in_horizon` (the same flag `mg_goal_order_n`'s own sum
   already filters on) — not for every tier on the ladder unconditionally.
   This is not in the §6.1 pseudocode literally, and it is added here for a
   measured reason: without it, the registered arithmetic identity
   (`Sum(children.headroom_n × children.tier_survival) ==
   parent.orderN_headroom_n`) is **false** the instant a horizon is bound
   tightly enough to trigger `decompose_required` at all — because
   `decompose_required` is set exactly when even the smallest tier's
   cumulative cost exceeds the horizon (`magnitude_ratio_first_tier > 1`),
   which by the ladder's own monotonic cumulative cost means **every** tier
   exceeds it, so the parent's `orderN_headroom_n` reads `0` at that exact
   moment (`PROGRAM_SYNTHESIS_ARC6_MAGNITUDE.md` §4.2's own horizon=5 row).
   Minting children with their full, untruncated increments in that state
   would sum to the ladder's full projected value while the parent reads
   `0` — a mismatch, not a rounding difference. Gating each child's mint on
   `in_horizon` makes the identity hold **by construction** in every scene,
   not only a cherry-picked one, and it has a named, reportable consequence:
   **at a horizon so tight not even the cheapest tier fits, decomposition
   mints nothing.** This is stated as a deliberate property (declining to
   propose children promising work nobody has budget for) rather than
   patched around, and it means the existing pinned scene
   (`test_mg3_push_back_marks_DECOMPOSE_REQUIRED_and_names_its_MEASURED_ladder`,
   horizon=5) is expected to still show **zero** children and **zero**
   `parent_agid`-bearing goals after this rung lands, unchanged — the
   mechanism is demonstrated on a wider, constructed horizon instead (MG4a).
> **CORRECTION, MADE DURING BUILD, BEFORE ANY GATE WAS WRITTEN.** Decision 2
> as registered above is **wrong**, and the reason is arithmetic rather than
> a matter of taste: `decompose_required == 1.0` requires
> `magnitude_ratio_first_tier > 1`, i.e. `cost_first > horizon_net`, where
> `cost_first` **is** the cheapest tier's own `cum_cost_units` (the exact
> field `in_horizon` compares against `horizon_net`). Because tier cost is
> cumulative and therefore monotonic, `cost_first > horizon_net` implies
> `cum_cost_units(t) > horizon_net` — i.e. `NOT in_horizon(t)` — for **every**
> tier `t`, not only the cheapest. So `decompose_required == 1.0` and
> `EXISTS t, in_horizon(t)` are **mutually exclusive, for any ladder,
> always** — gating the mint on `in_horizon` does not make decomposition
> decline gracefully under a tight horizon, it makes `mg_decompose`
> **permanently unreachable under its own natural trigger**: resident and
> structurally dead, exactly the failure mode §1/JOB 0 found for
> `qd_decompose` and named as *worse* than merely unreached. It also
> contradicts §6.3's own stated point — children are meant to be
> **independently** re-priced against the horizon so a cheap tier (B0, 8
> units) can become individually actionable even when the full ladder (28
> units) was not, which requires minting the whole ladder, not a
> horizon-pre-filtered slice of it. **Corrected: `mg_decompose` mints every
> un-materialised tier unconditionally, gated only on `decompose_required`
> and dedup — no `in_horizon` check.** Each child is then priced
> individually by the existing, unmodified `mg_rung` (it matches every
> `ArcGoal`) via `cost_bits`, which is why the child now also carries
> `cost_bits: t.cum_cost_units` (a decision beyond §6.1's literal attr list,
> needed for exactly this). **The honest consequence, not hidden:** the
> registered arithmetic identity now holds on a **constructed** scene
> (`decompose_required` forced true while no horizon truncates the parent's
> own `orderN_headroom_n` reading) but does **not** hold, as literally
> stated, on the **natural** push_back trigger — there, the parent's own
> `orderN_headroom_n` is horizon-truncated to `0` (nothing fits, by the same
> mathematical fact above) while the children correctly sum to the ladder's
> full, untruncated projected value. Both scenes are measured and reported
> in `PROGRAM_SYNTHESIS_ARC6_MG4_DECOMPOSE.md` rather than only the one that
> passes; MG4a is registered (below) against the constructed scene, matching
> its own text, and the mismatch on the natural-trigger scene is named as a
> genuine tension in the ORIGINAL bar wording for whoever revisits it, not
> patched into invisibility.

3. **The parent moves to `"decomposed"` only once decomposition of the
   FULL tier set is complete (every tier of the ladder, per the correction
   above — not only a horizon-affordable subset) AND at least one child
   exists** — never on the flag alone. The "at least one child" guard is a
   defensive no-op today (a real ladder always has tiers), kept because it
   documents the invariant for free.

**What is explicitly NOT built, named rather than silently dropped:**

- **Fold-up is not twinned.** §6.2(3) calls for lifting
  `qd_compound_resolve`/`qd_compound_wall` onto `ArcGoal`. Nothing in this
  tree resolves a decomposition child's status — no `ExecClass` targets a
  structural-primitive tier — so a twinned fold-up rule would be dead code
  with nothing to trigger it, the same shape JOB 0 already found for
  `qd_decompose` itself. MG4 is, again, *"a BUILD for the split and a HOOK
  for the fold-up"* — the child shape is legible to a future fold-up rule
  (`parent_agid`, `tier_order` are exactly what `Count`-over-neighbours
  needs), but wiring it here would be untestable construction.
- **No new seed dependency on `arc_executor`.** Decomposition needs no
  `ExecClass`, no dispatch, no re-arm — it is graph arithmetic over
  `ArcGoal`/`ArcTier`. The new seed depends on `arc_magnitude` (for
  `ArcTier`/`decompose_required`) and, through it, `arc_goals` — not on
  `arc_executor`. This keeps decomposition addable/removable independent of
  the executor line, and keeps it out of the re-arm/dispatch scope this
  task explicitly excludes.
- **A new, additive-only seed**, `seeds/arc_decompose.json`
  (`tools/build_arc_decompose_seed.py`), rather than growing
  `seeds/arc_magnitude.json`'s own rule list — MG5's own precedent ("this
  rung adds a second seed rather than editing the first"), so MG1-3/5's
  existing 43 gates load a graph that has not changed under them. The one
  exception is a single, additive, purely-inert-on-every-existing-scene
  guard added to `arc_magnitude.json`'s `mg_goal_order_n_default` (excluding
  nodes carrying `parent_agid`) — required because that rule otherwise
  unconditionally recomputes ANY laddered-orphan goal's `orderN_headroom_n`
  from its raw `headroom_n` every fixpoint pass, which would silently
  overwrite a decomposition child's own order-N value back to its
  undiscounted order-1 figure — precisely the inflation §6.2(4) warns
  against. A new `mg_child_order_n` rule (in the new seed) computes the
  child's own `orderN_headroom_n = headroom_n × tier_survival`.

**Bars, registered before the build.**

- **MG4a — the registered arithmetic identity, both directions.**
  `Sum(children.headroom_n × children.tier_survival) ==
  parent.orderN_headroom_n`, on a constructed decomposition scene (wide or
  unheld horizon, so every tier is in-horizon and the sum is non-trivial —
  not the degenerate horizon=5 scene where it is `0 == 0`). Both
  directions: the identity holds on the correctly-built scene, AND a
  negative control (a child's `tier_survival` corrupted/dropped) is shown
  to break the same check — a check that cannot fail is not a check.
- **MG4b — a decomposed parent leaves the pool, reported as a paired list.**
  Before/after pool membership (agid sets), not a bare delta: the pool
  loses exactly the one parent agid and gains exactly the N child agids for
  N tiers on the ladder (per decision 2's correction: every tier mints,
  unconditionally — the horizon determines which of the N children are
  individually `absorb`-able afterward, not how many mint). Demonstrated on
  at least two horizons (e.g. the natural push_back trigger, horizon=5, and
  a wider constructed one) so each child's OWN `magnitude_rung` is shown to
  vary with the horizon even though N itself (fixed by the ladder, 4 on the
  shipped graph) does not — the horizon-dependence decision 2's correction
  actually buys is per-child affordability, not mint count.
- **MG4c — no double-counting, demonstrated live.** The parent is never
  simultaneously present in `POOL()` alongside its children: read `POOL()`
  (both the order-1 and, with `arc_magnitude` live, the order-N pool) at
  the tick the parent's `headroom_n` is stamped to `0.0` and assert the
  parent is absent while any already-minted children are present. Also:
  the parent's own `VALUE`/`VALUE_N` contribution is unreachable once
  excluded (`MaxOver` over `POOL()` cannot read a filtered-out element),
  asserted structurally rather than merely by absence from a printed rank.
- **MG4d — no regression, node-id lists not counts.** The five existing
  gate suites (`test_arc_executor_migrated`, `test_arc_goals_migrated`,
  `test_goal_residual_migrated`, `test_arc6_valuelayer_migrated`,
  `test_arc_magnitude_migrated`) produce the same failing-node-id lists
  before and after, paired and named. `seeds/arc_goals.json`,
  `seeds/goal_residuals.json` stay byte-identical to `HEAD`.
  `seeds/arc_magnitude.json` regenerates byte-identically from its OWN
  (edited, version-bumped) emitter, and the ONE new guard clause in
  `mg_goal_order_n_default` is shown inert on every existing MG1/2/3/5
  scene (same values before/after on the 43 pre-existing magnitude gates).
  `seeds/arc_decompose.json` regenerates byte-identically from its own
  emitter. The adapter source audit (no `.evaluate(`, no `run_rules`, no
  raw `substrate_rs` import) passes on any new adapter code, mirroring the
  existing `arc_magnitude_ingest`/`arc_executor` module-specific audits.

**Explicitly out of scope, unchanged from A13/A14/A15's own boundary:** the
re-arm deadlock, the silent order-N fallback, `ag_ask`/`ax_dispatch`
collapse-agreement in general, and `gr_condition_lapse`'s closed vocabulary.
Also out of scope, named here rather than assumed: fold-up (decision above),
and any `ExecClass` for a decomposition-tier goal (there is no runner that
could execute "supply a structural primitive" — that remains genuine outside
work, same as it was for the undecomposed parent).
