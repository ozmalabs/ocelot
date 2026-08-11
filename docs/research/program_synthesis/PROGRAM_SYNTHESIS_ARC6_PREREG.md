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

---

### AMENDMENT A17 (2026-08-11) — retiring a `supply_blocker`/`source_claim` pool member: the gap A15 named, closed at the grain A16 minted

A15 §6 named the exact gap this amendment closes, quoted verbatim because it
is this rung's charter: *"What WOULD grow A14's real-only n... a capability
whose retirement changes WHICH `nearest_unroutable_kind` the final pool
settles on... unless the newly-reachable pool member is itself a
`supply_blocker`/`source_claim` (which no currently-known mechanism can
retire)."* A16 (MG4/decomposition) landed since and, in its own module
docstring, asserted without a dedicated investigation that *"there is no
runner that could execute 'supply a structural primitive'; that remains
genuine outside work, same as it was for the undecomposed parent."* This
amendment tests that assertion rather than inheriting it, per the task's own
instruction to find out honestly rather than assume either way.

**The design investigation, done before drafting bars.**

1. **The goal-kind space is now FIVE, not four, and A16 minted the fifth
   one without naming it as a new kind.** `tools/build_arc_decompose_seed.py::
   _r_decompose`'s own `add_node` effects stamp `"kind": "decomposition_tier"`
   on every child — read directly from the source, not inferred from prose.
   This is a DIFFERENT value from `supply_blocker`/`source_claim`/
   `re_measure`/`reported`, confirmed by grep across every seed builder in
   the tree. A16's own uncertainty #6 ("none of the shipped classes route a
   `decomposition_tier` kind") is the same fact read from the other side.
2. **A `decomposition_tier` child does NOT carry the graph shape
   `ax_dispatch`/`_routable` requires.** `_routable` (`tools/
   build_arc_executor_seed.py`) requires a `mint_source` edge to a node
   carrying `rid` (the three-part key's third component, AG-5 §8 item 2);
   `mg_decompose`'s effects add only `has_subgoal` (from the parent) and
   `has_arc_goal` (from the agenda) — **no `mint_source` edge at all**. A
   `decomposition_tier` goal is therefore structurally unroutable by the
   EXISTING `ax_dispatch` machinery without EITHER growing `mg_decompose`
   to mint a `mint_source` edge to some new residual-shaped node (a bigger,
   riskier change to the mint rule the arc's own A16 rung just finished
   correcting once already) OR relaxing `_dispatchable`'s `Eq(Count(
   mint_source), 1)` guard (a change to `ax_dispatch`'s core routing
   invariant, explicitly out of scope per A13-A16's shared boundary). This
   rung does neither: it does not touch `arc_executor` at all, matching
   A16's own design choice to keep decomposition independent of the
   executor line.
3. **Tier 1 of the shipped ladder (`B0_zero_new_termnode`) is not
   hypothetical outside work — it is ALREADY BUILT, verified by reading the
   shipped Rust source, not by trusting a docstring.** All eight of its
   named units (`op:TupleOf`, `op:ProdList`, `op:ConcatList`,
   `op:ArgMaxLenOver`, `tmpl:item_in_listvar`, `tmpl:len_item_vs_var`,
   `tmpl:nested_reduction`, `fix:StringAsSequence`) are live, load-bearing
   code in `runners/dsl/src/synth_enumerate.rs` and `term.rs` on this
   rung's own engine (`c5e50801d48a…`) — confirmed by grep AND by a live
   re-run of the unmodified `scripts/arc6_structural_ceiling.py` (below,
   item 5), not by string-matching alone (A1.3's own rule). This is the
   concrete difference between tier 1 and the whole 42-task
   `missing_structural_primitive` claim, and it is the reason this rung
   targets the CHILD, not the PARENT: the parent's own claim ("supply a
   primitive for all 42 tasks") is genuinely open-ended (tiers 2-4 need ten
   new `Term` variants, a cross-cutting string-order fix with an unpriced
   fixture-migration cost, a `Lit`-boundary fix, and a `Recurse` capability
   decision — none of which exist yet); tier 1's own claim ("supply the
   8-unit, zero-new-`TermNode` bundle") is bounded and, per this item,
   already true.
4. **The `source_claim` goals remain structurally unresolvable, confirmed
   independently rather than re-quoted from A15.** `_r_mint_source_claim`
   (`tools/build_arc_goals_seed.py`) mints unconditionally from a static
   `ArcSourceClaim` node carrying no `holds_under` edge and no `stale`
   attr; `ArcSourceClaim` appears in no rule's `match` clause anywhere in
   the tree except the one-shot mint. Making any of the four re-measurable
   would mean inventing an entire condition-and-lapse apparatus for a node
   type that currently has none — confirmed by reading every rule in
   `seeds/arc_goals.json`, not assumed from A15's own finding. One of the
   four (`arc6.claim.tier0_hs1_0_of_10`, "HS1 failed 0 of 10 converted") is
   independently interesting: item 3 above shows its own claim is now
   STALE (tier 0's bundle is built and partially witness-verified) — yet
   nothing in the tree could ever notice, because the node it is stamped
   on has no mechanism to be told. Recorded as a second, independent
   illustration of the same structural gap, not claimed as a target.
5. **A live re-run, stash-protected and sha-verified before and after,
   shows genuine — but PARTIAL — drift on tier 1's own claim.** With
   `results/arc6_structural_ceiling.json` stashed first
   (`5af750cd4dcc…`) and restored after (byte-identical, confirmed),
   `scripts/arc6_structural_ceiling.py` was re-run on this rung's engine.
   `strict_reach.witness_and_in_budget_ids` grew from the committed
   `[75, 98, 106, 161, 257, 290]` (6) to `[75, 98, 106, 161, 257, 290, 424,
   450]` (8) — the identical `+424, +450` delta A15 §1 item 7 found on a
   different engine, reproduced independently here. Tier 1's own increment
   (`[18, 75, 98, 106, 161, 257, 290, 310, 424, 450]`, 10 ids) is **still
   not fully covered** — `18` and `310` remain outside the witness set even
   after a real re-measurement on this engine. **This is the honest
   finding that shapes AR17b below**: the natural, currently-reachable
   state does not retire tier 1 either — the mechanism this rung builds
   must be measured to correctly decline in that real state, and shown
   separately (by a documented, narrow construction, mirroring A13 §7.1 /
   A15 §4.2's own precedent) to fire when coverage is genuinely complete.
6. **The retirement condition is expressible with zero new Rust and zero
   new `arc_executor` machinery.** `results/arc6_structural_ceiling.json`
   already carries, per tier bundle, a CUMULATIVE `unlocked_ids` list (so a
   tier's own increment is a plain set difference, the exact arithmetic
   `arc_magnitude_ingest.probe_tier_ladder` already performs for
   `increment_n`) and, at the top level, `strict_reach.
   witness_and_in_budget_ids` (freshly re-measured by the ALREADY-WIRED
   second `ExecClass`, A15). A mechanical adapter function — read two
   dotted paths, one set difference, one set-containment check, structured
   exactly like `goal_residual_ingest.probe_facts`/`install_facts`'s own
   "measure, then install as graph data" shape — can write a
   `TierWitnessFact{ladder_key, tier_order, all_ids_covered}` node per
   tier, and ONE new rule can retire a `decomposition_tier` child whose own
   `(parent_ladder_key, tier_order)` matches a fact reading
   `all_ids_covered==1.0`, using the SAME `headroom_n → 0` pool-exit
   already validated three times over (A13 §7.1, A15 §4.2, A16 decision 1)
   — zero edits to `seeds/arc_goals.json`, zero new `ExecClass`, zero
   changes to `ax_dispatch`.

**Bars, registered before any seed/adapter code is written.**

- **AR17a — the survey.** Every `supply_blocker`/`source_claim` goal kind
  on the shipped graph, PLUS the `decomposition_tier` kind MG4 mints,
  classified as genuinely-resolvable / decomposable-into-a-resolvable-
  sub-claim / genuinely-open, each classification backed by a reading of
  the actual rule/seed code (not by re-quoting a prior rung's prose),
  reported as a table. Satisfied by §"survey" in the results doc, mirroring
  this amendment's own investigation.
- **AR17b — the GO/NO-GO criterion, registered before building anything.**
  **GO** iff a real, live, falsifiable mechanism can be built that:
  (i) retires at least one `supply_blocker`/`source_claim`-descended pool
  member (a decomposition child counts, per the task's own framing:
  *"a goal that gets NARROWED/decomposed... into a bounded sub-claim that
  CAN be resolved, even if the parent's full scope can't be"*);
  (ii) the retirement condition is grounded in a REAL, existing measurement
  (no invented capability, no fabricated artifact) and is demonstrated able
  to correctly DECLINE on the real, currently-reachable state as well as
  FIRE on a documented construction (a check that cannot fail is not a
  check, A7's own standing rule); and (iii) the cost stays small: **no new
  Rust, no changes to `ax_dispatch`/`ROUTE`/`_routable`, ≤1 new adapter
  function pair (probe + install, mirroring `goal_residual_ingest`'s own
  shape), ≤1 new rule.** **NO-GO** — report the survey as a clean, honest
  null (mirroring M0's four ceiling probes and A14's own NO-GO) and build
  nothing — if AR17a finds every kind genuinely open with no bounded
  sub-claim, or if the cheapest real mechanism found exceeds the AR17b(iii)
  threshold.
- **AR17c — no regression, node-id lists not counts.** The six existing
  gate suites (`test_arc_executor_migrated`, `test_arc_goals_migrated`,
  `test_goal_residual_migrated`, `test_arc6_valuelayer_migrated`,
  `test_arc_magnitude_migrated`, `test_arc_decompose_migrated`) produce the
  same failing-node-id lists before and after, paired and named.
  `seeds/arc_goals.json`, `seeds/goal_residuals.json`,
  `seeds/arc_magnitude.json`, `seeds/program_synthesis.json`,
  `domains/arc_goal_ingest.py`, `domains/arc_magnitude_ingest.py`'s
  EXISTING functions, `domains/arc_executor.py`, and
  `tools/build_arc_executor_seed.py` stay byte-identical to `HEAD`.
  `seeds/arc_decompose.json` regenerates byte-identically from its own
  (edited, version-bumped) emitter. The adapter source audit (no
  `.evaluate(`, no `run_rules`, no raw `substrate_rs` import) passes on any
  new adapter code.

**Explicitly out of scope, unchanged from A13-A16's shared boundary:** the
re-arm deadlock, the silent order-N fallback, `ag_ask`/`ax_dispatch`
collapse-agreement in general, `gr_condition_lapse`'s closed vocabulary, and
`results/arc6_import_impedance.json`/`scripts/arc6_import_impedance.py`
(named repeatedly across this arc as a separate thread). Also out of scope:
a general re-verification mechanism for tiers 2-4 of the same ladder (each
needs capability this tree does not yet have — new `Term` variants, the
string-order fix, the `Lit` boundary fix — building any of them is a
separate, much larger rung) and any change to `source_claim`'s own
structural unresolvability (item 4 above; closing it would mean inventing a
condition-and-lapse apparatus for `ArcSourceClaim`, out of this rung's
scope exactly as A15 named it for a second `ExecClass`). If AR17b's cost
threshold is not met by a full-sweep re-run of A14's own impotence
campaign, that re-run is named as a possible follow-up, not performed here,
per the task's own instruction that it need not be repeated unless cheap.

---

### AMENDMENT A18 (2026-08-11) — the re-arm deadlock: does it still reproduce, and if so, an epoch producer that does not require running anything

`PROGRAM_SYNTHESIS_ARC6_EXECUTOR.md` §5 named, reported not patched, exactly
one gap: *"Cell D needed an epoch bump from OUTSIDE this loop. The executor
is the epoch's producer, but it only produces one by RUNNING a goal, and a
retired goal is not in the pool to be run. With exactly one executable goal,
a genuinely re-failed condition cannot bring it back on its own."* Five
rungs have landed since (A11–A17) without touching it; two of them (A15, A17)
changed the shape of the graph this deadlock lives on. This amendment tests
the deadlock against the CURRENT shipped graph rather than inheriting
EXECUTOR.md's own characterisation of it, per the task's own instruction to
find out honestly rather than assume either way.

**The design investigation, done before drafting bars.**

1. **`arc_measure_epoch` has exactly ONE producer anywhere in the tree, and
   it is unconditional on WHICH order ran.** `domains/arc_executor.py::
   run_order` calls `agi.bump_measure_epoch(sub)` once, unconditionally,
   after ANY successful run — confirmed by reading the function, not the
   docstring. `agi.bump_measure_epoch` (`domains/arc_goal_ingest.py`) is
   itself the ONLY caller of `set_measure_epoch` that increments rather than
   sets a literal, and `grep -rn bump_measure_epoch domains/*.py` returns
   exactly this one call site. **A15's second `ExecClass` does not add a
   second epoch producer** — it adds a second thing `run_order` can be asked
   to run, and both routes bump the SAME counter through the SAME function.
2. **A17's `mg_tier_retire` is a THIRD retirement mechanism and NOT an epoch
   producer.** `domains/arc_decompose_ingest.py` (`probe_tier_witness_
   coverage` / `install_tier_witness_facts`) never calls `bump_measure_epoch`
   and never calls `run_order` — confirmed by grep, zero hits in that file.
   It retires a `decomposition_tier` child via the SAME `headroom_n -> 0`
   pool-exit `ax_rearm` never inspects (A13 §7.1 / A15 §4.2 / A16 decision 1
   precedent), entirely outside the executor/dispatch machinery. So A17
   widens WHO can leave the pool without ever widening WHAT can advance the
   clock the re-arm latch reads.
3. **A15's own "bonus extension probe" (§6 of `PROGRAM_SYNTHESIS_ARC6_
   SECOND_EXECCLASS.md`) already measured, live, that the NATURAL trajectory
   with BOTH `ExecClass`es reaches a state with ZERO executable goals, not
   one.** Quoted because it is this amendment's central fact: driving both
   `re_measure` residuals to real completion in one boot left *"the FINAL
   steady-state composition, once both retire, composition-identical to
   A14's own already-measured 'state 1' — pool_n=7 ... Once a re_measure
   goal retires it leaves no permanent trace on POOL()."* EXECUTOR.md's own
   §5 was written when the graph had exactly one `ExecClass`; on the
   CURRENT graph the natural end state after both classes have run and
   retired is **zero** executable pool members, which is the deadlock's
   precondition made WORSE, not defused — there is no longer even a
   *candidate* second executable goal sitting in reserve once the ordinary
   course of execution has run to completion.
4. **The two-tick-agreement precedent (`ax_dispatch`'s own fix, EXECUTOR.md
   §8 item 1) is the shape of a producer that would NOT reintroduce churn.**
   Coupling a NEW epoch-advance directly to the SAME single detection event
   that already computes a retired goal's `stale` flag (i.e. "bump the
   epoch the instant a probe finds the condition re-failed") was
   investigated and REJECTED before writing bars: it would collapse EX4's
   own cell C into cell D — cell C's existing gate (`test_ex4_the_EPOCH_
   half_of_the_latch_is_load_bearing`) already calls `axe.
   refresh_evidence_facts(s)` once, right after moving the row-verdict
   artifact off disk, specifically to prove that a SINGLE genuine
   re-failure does not, by itself, re-mint — so any design that makes a
   single probe both detect AND grant would directly violate a bar this
   task's own AR18b requires to still hold. The fix therefore needs a
   producer with an INDEPENDENT temporal gap from the detection it reads —
   the same shape `ax_dispatch`'s own two-tick fix already uses at the
   fixpoint-tick grain, reused here at the PROBE-CALL grain: a genuine
   world-drift is trusted only once it is seen on TWO SEPARATE, externally
   -triggered probes, not two iterations of one `run_rules()` fixpoint.
5. **The adapter already ships the exact primitive this needs, unused for
   this purpose.** `domains/arc_executor.py::refresh_evidence_facts` is a
   CHEAP, non-subprocess, real re-probe of the same facts `goal_residual_
   ingest.probe_facts` measures (file presence/sha, the value-layer probe)
   — already called once per loop iteration by the existing measurement
   drivers (`scripts/arc6_executor_measure.py` et al.), and already proven,
   by EX4's own cell C, to detect a genuine re-failure without running
   anything. What it does not currently do is persist its OWN prior reading
   anywhere a rule can compare against — every call overwrites `stale` with
   no memory of what the last call found.

**The design, stated before the build.** ONE new rule
(`ax_world_probe_epoch`, `seeds/arc_executor.json`) and a small,
purely-mechanical addition to `refresh_evidence_facts`:

- The adapter, at the START of every `refresh_evidence_facts` call and
  BEFORE it overwrites any fact, copies each `GoalResidual`'s CURRENT
  `stale` reading into a new attr `stale_at_last_probe` — "the adapter
  carries what is there," the `ARM_CARRY` precedent, applied at the
  probe-call boundary instead of the tick boundary. This is a plain read
  and a plain `set_attr`; it decides nothing.
- The new rule matches exactly `ax_rearm`'s own pattern (`HUB + [["agenda",
  "has_arc_goal", "g"], ["r", "remeasure_goal", "g"]]`) and fires only when
  `g.status == "retired"`, `r.stale == 1.0` AND `r.stale_at_last_probe ==
  1.0` (the SAME genuine re-failure confirmed on two SEPARATE probes) AND
  `g.retired_epoch == arc_measure_epoch` (the clock has not moved since
  retirement — i.e. this is exactly the stuck case, and the rule declines
  to act once anything else has already advanced the epoch). It writes ONE
  descriptive fact, `g.world_drift_confirmed = 1.0`. It does not touch
  `ax_rearm`, `arc_measure_epoch`, or any existing rule's `where` clause.
- The adapter reads that fact (a pure query, the same shape as `pending_
  orders`) and, if any retired goal carries it, calls the SAME `agi.bump_
  measure_epoch` `run_order` already calls — mechanically, outside
  `run_rules()`, so `ax_rearm`'s own epoch-advance check is satisfied only
  on the NEXT fixpoint, exactly as cell D already requires manually.

**The tradeoff, named explicitly, per the task's own instruction not to
loosen anti-oscillation without saying so.** `arc_measure_epoch`'s
documented meaning is *"a measurement happened"* (`domains/arc_goal_
ingest.py`'s own docstring: *"a measurement happening is a fact about the
world... the adapter records it, the rules decide what it means"*). This
rung widens WHICH real-world events count as a measurement: a full
remeasurement subprocess (unchanged) OR a confirmed, twice-observed,
genuine drift in a retired goal's own condition (new). Both are real
events probed from the world, never authored — but it means every OTHER
epoch-gated mechanism (the testimony reply's one-epoch life, the unanswered
question's lapse, `ax_impotent`'s own lapse) now also expires slightly
MORE readily than before, on an event that is cheaper than a full
remeasurement. This is the honest cost, and AR18b below is the check that
it does not go further than that — a bare, single detection must still not
be sufficient, in this design or any other.

**Bars, registered before any seed or adapter code is written.**

- **AR18a — does the deadlock, as literally described in EXECUTOR.md §5,
  still reproduce live on the CURRENT (post-A17) shipped graph, tested
  directly, BEFORE any fix is written?** Construct the exact scene: retire
  one `re_measure` goal via a real live execution (the existing `live_run`
  fixture), confirm the OTHER `ExecClass`'s residual is not organically
  stale on this engine (so the pool genuinely holds zero executable
  members, matching finding 3 above), move the retired goal's evidence
  artifact off disk (a real world change, EX4's own cell-C technique), and
  show that on the UNMODIFIED graph, repeated `run_rules()` passes and
  repeated `refresh_evidence_facts()` probes leave the goal stuck retired
  with the epoch unchanged, indefinitely — i.e. nothing internal to the
  current tree ever unsticks it. Report the honest answer either way: if
  some OTHER mechanism is found to already close it, that is a complete,
  valuable null result and no fix is built (per the task's own registered
  candidate 1).
- **AR18b — the fix must not weaken anti-oscillation.** Re-run EXECUTOR.md
  §5's own four-cell `latch_cells` scene (churn does not re-mint; a SINGLE
  genuinely re-failed probe, alone, does not re-mint; re-failed AND the
  clock having independently advanced DOES re-mint; the world restoring
  returns the goal to terminal with a fresh `retired_epoch` and `rearm_
  count` unchanged) and confirm all five cells hold BYTE-IDENTICALLY to
  EXECUTOR.md's own recorded shape, with the new mechanism installed and
  live on the graph — not merely not re-run, but shown incapable of
  collapsing cell C into cell D on a SINGLE probe.
- **AR18c — the fix closes the deadlock, demonstrated live, in the same
  style as EX4's cell D, but WITHOUT ever running an executable order.**
  Starting from AR18a's exact stuck scene (zero executable goals, epoch
  unchanged since retirement, condition genuinely re-failed), show that TWO
  SEPARATE, externally-triggered `refresh_evidence_facts` probes — no
  subprocess, no `run_order`, no hand-poked `bump_measure_epoch` — are
  sufficient for the goal to re-enter the pool (non-terminal, `rearm_count`
  incremented), and that ONE such probe is not.
- **AR18d — no regression, node-id lists not counts.** The six existing
  gate suites (`test_arc_executor_migrated`, `test_arc_goals_migrated`,
  `test_goal_residual_migrated`, `test_arc6_valuelayer_migrated`,
  `test_arc_magnitude_migrated`, `test_arc_decompose_migrated`) produce the
  same failing-node-id lists before and after, paired and named.
  `seeds/arc_goals.json`, `seeds/goal_residuals.json`,
  `seeds/arc_magnitude.json`, `seeds/arc_decompose.json`,
  `seeds/program_synthesis.json`, `domains/arc_goal_ingest.py`,
  `domains/arc_decompose_ingest.py`, `domains/arc_magnitude_ingest.py`, and
  `tools/build_arc_executor_seed.py`'s EXISTING route/dispatch/impotence
  Term builders (`ROUTE`, `_routable`, `_dispatchable`, `_r_dispatch`,
  `_r_rearm`, `_r_impotent`) stay byte-identical to `HEAD`.
  `seeds/arc_executor.json` regenerates byte-identically from its own
  (edited, version-bumped) emitter. The adapter source audit (no
  `.evaluate(`, no `run_rules`, no raw `substrate_rs` import) passes on the
  edited `domains/arc_executor.py`.

**Registered null reading.** If AR18a finds the deadlock already closed by
some mechanism this investigation missed, this rung builds NOTHING beyond
the demonstration script and reports that as the complete result — matching
this arc's own standing culture of clean nulls. If AR18a confirms the
deadlock but the smallest defensible fix (per the design above) is found,
during the build, to require a LARGER change to `ax_rearm`'s own
conjunction or to `gr_condition_lapse`'s vocabulary than the design here
anticipates, that is reported as a scoped, not-taken recommendation
(matching WIRE_HANDS's WH4 precedent) rather than forced through.

**Explicitly out of scope, unchanged from A13–A17's shared boundary:** the
silent order-N fallback, `ag_ask`/`ax_dispatch` collapse-agreement in
general, `gr_condition_lapse`'s closed vocabulary, fold-up, any `ExecClass`
for a `decomposition_tier` goal, `source_claim`'s structural
unresolvability, and `results/arc6_import_impedance.json`/`scripts/
arc6_import_impedance.py`. Also out of scope: a third `ExecClass` (seam
B/C/D) — this amendment is about the epoch's PRODUCERS, not the executor's
reach, and A15 §8 item 3 already found that a third `ExecClass` would not,
by itself, change this deadlock's shape.

---

### AMENDMENT A19 (2026-08-11) — the silent order-N fallback: make it observable, without touching when it fires

`PROGRAM_SYNTHESIS_ARC6_WIRE_HANDS.md` §8 named, ordered FIRST by damage,
exactly one uncertainty, quoted because it is this amendment's charter:
*"THE FALLBACK IS SILENT, AND IT FAILS TOWARD THE COLLAPSE THE ARC MEASURED
AS MISPRICED. If `mg_select` ever stops firing — a boot without
`arc_magnitude`, an empty pool at the wrong moment, a future edit to its
guard — `SEL_AGID` reverts to order-1 and nothing raises an alarm. This is
mitigated after the fact (`selected_by` on the order) and NOT PREVENTED."*
Six rungs have landed since (A12–A18) without touching it; none of them
changed `_order_n_is_not_live()`, `mg_select`, or anything upstream of it —
confirmed below, not assumed, because A18 itself changed the epoch's
producers and had to be checked for interaction.

**Scope, stated precisely, per the task's own boundary.** The fallback
itself — `SEL_AGID` reverting to `arc_sel_agid`/order-1 when `mg_sel_agid`/
order-N is absent — is A11's own deliberate, measured design (WIRE_HANDS
§1.2: a HARD dependency on `arc_magnitude` would change what every EX1–EX6
scene boots and would put an order-N collapse into every graph that merely
wants hands). **This amendment does not remove it, does not widen it, and
does not touch `ax_dispatch`, `SEL_AGID`, `ARMED_AGID`, `_armed`, `ROUTE`, or
`_routable`.** The gap is narrower than the fallback: there is no standing,
queryable GRAPH FACT that says "the order-N collapse is not currently
producing a stamp" — only a per-order breadcrumb (`selected_by`) that a
human or a future rung would have to go looking for, order by order, after
the fact. `ag_ask`/`ax_dispatch`'s general collapse-agreement question (the
standing list's item 5) and `gr_condition_lapse`'s vocabulary (item 6) are
untouched, per the task's explicit boundary — this amendment does not
re-litigate either.

**The design investigation, done before drafting bars.**

1. **`mg_sel_agid` has exactly ONE writer anywhere in the tree, and it is a
   single `set_attr`.** `grep -n mg_sel_agid tools/build_arc_magnitude_seed.py`
   returns one write site (`mg_select`'s own effect) and three reads (`mg_
   select_audit`'s guard, `mg_select_runner_up`'s exclusion, `mg_select_
   margin`'s non-null guard) — confirmed by reading the file, not assumed
   from WIRE_HANDS' own prose. So "`mg_sel_agid` is absent" is exactly and
   only "`mg_select` has not fired on this graph" — never a proxy for
   anything else — which is precisely the primitive `tools/build_arc_
   executor_seed.py::_order_n_is_not_live()` already tests
   (`Eq(agenda.mg_sel_agid, null)`), reused verbatim by `SEL_AGID`/`ARMED_
   AGID`/`ARMED_VALUE`/`COLLAPSE_NAME`. **The fact this amendment needs to
   make standing is a direct re-read of a Term that already exists and is
   already load-bearing** — no new primitive, no new DSL Term.
2. **None of A12–A18 touched `mg_select`'s liveness, confirmed per rung, not
   inferred from silence.** A15 (second `ExecClass`) and A17 (`mg_tier_
   retire`) both changed what a goal can be routed to or how it can leave
   the pool — neither writes or reads `mg_sel_agid`
   (`PROGRAM_SYNTHESIS_ARC6_SECOND_EXECCLASS.md` §8 item 5, `PROGRAM_
   SYNTHESIS_ARC6_RETIRE_BLOCKER.md`'s own confinement table, both name
   `seeds/arc_magnitude.json` as UNCHANGED and byte-frozen). A16 (MG4
   decomposition) added one additive guard to `mg_goal_order_n_default`
   inside `arc_magnitude.json` itself but did not touch `mg_select`'s own
   rule body (`PROGRAM_SYNTHESIS_ARC6_MG4_DECOMPOSE.md` §"what changed").
   A18 (the re-arm deadlock) added a SECOND epoch producer but its own
   `test_a18_AR18d_ax_rearms_OWN_body_is_UNCHANGED`-style confinement
   asserts `seeds/arc_magnitude.json` byte-identical to `HEAD` throughout.
   **So the fallback's actual firing behaviour has not shifted as a side
   effect of any rung since WIRE_HANDS** — this amendment is building
   against the same primitive WIRE_HANDS described, not a moved target.
3. **The right home is `seeds/arc_executor.json`, not `seeds/arc_
   magnitude.json`.** `tools/build_arc_magnitude_seed.py` has no knowledge
   of `arc_executor` (it is loaded first, `arc_executor` depends on it
   SOFTLY) — a fact about "the order-N collapse is not currently informing
   dispatch" is a fact about DISPATCH, and the executor seed already ships
   the exact vocabulary for a standing dispatch-grain fact:
   `AgendaVerdict` + `has_agenda_verdict` (A13/WH4(c)'s `ax_impotent`,
   quantifying over the pool the same way this amendment quantifies over
   one Term). The node type and edge are already declared as productions
   in `tools/build_arc_executor_seed.py::_productions()` — **zero new
   productions, zero new node type, zero new edge type.**
4. **The existing lapse idiom (`gr_condition_lapse`'s `fact_equals`
   against `arc_measure_epoch`, A13's own choice for `ax_impotent`) is the
   WRONG shape here, and this was checked before writing any rule.**
   `ax_impotent`'s verdict describes a POOL STATE as of one epoch and is
   *meant* to go stale only when a new measurement might have moved the
   world. The fallback's liveness is not epoch-shaped: `arc_magnitude` can
   be loaded onto an already-running graph (exactly how `test_wh1_*` vs
   `test_wh3_*` differ — one boots with it, one without) with no epoch
   bump at all, and a self-monitoring agent asking "is the fallback active
   RIGHT NOW" wants the CURRENT truth of `_order_n_is_not_live()`, not a
   description that is honest only until the next remeasurement. So the
   mechanism is a DIRECT REVERSIBLE PAIR — the same SHAPE as
   `gr_condition_lapse`/`gr_condition_hold` (mutually exclusive by
   construction, one node's `stale`/`active`-style attr flipped in either
   direction) — but keyed on `_order_n_is_not_live()` directly rather than
   through the `ckind` sub-language, because that sub-language's three
   `ckind`s (`shape_count`/`payload_count`/`fact_equals`) are all built for
   a DIFFERENT question (does a counted/matched artifact still match) and
   none of them expresses "is this Term currently true," which is exactly
   what `_order_n_is_not_live()` already answers directly.
5. **`agenda_verdicts(sub, kind=None)` (`domains/arc_executor.py`) is
   already the correct, generic read-off — no adapter change is needed at
   all.** Every existing caller already passes an explicit `kind` filter
   (`grep -rn agenda_verdicts scripts/ tests/` — six call sites, all
   `kind="impotent"`), so a second `kind` value is additive by construction
   and the adapter needs no new function, no new branch, and no edit to
   its module-specific source audit's allow-list.

**The design, stated before the build.** TWO new rules in `seeds/arc_
executor.json`, mirroring `ax_impotent`'s mint-once idiom for the ON
direction and `gr_condition_lapse`/`gr_condition_hold`'s reversible-pair
shape for the OFF direction — no new DSL Term, no new node type, no new
edge type, no new adapter function, `ax_dispatch`/`SEL_AGID`/`ARMED_AGID`/
`_armed`/`ROUTE`/`_routable` byte-unchanged.

- `ax_fallback_silent` — fires when `_order_n_is_not_live()` holds AND no
  currently-`active` `AgendaVerdict{kind:'order_n_fallback'}` already
  exists (the mint-once guard, `ax_impotent`'s own shape). Mints
  `AgendaVerdict{kind:'order_n_fallback', active:1.0, epoch:<current>,
  reason:'mg_sel_agid_absent_order_n_collapse_not_producing_a_stamp'}`,
  edged from the agenda hub exactly like `ax_impotent`'s verdict.
- `ax_fallback_cleared` — fires when `_order_n_is_not_live()` does NOT
  hold (order-N is live) AND an `active` verdict of this kind exists.
  Flips `active` to `0.0` and stamps `cleared_epoch`. Mutually exclusive
  with `ax_fallback_silent` by construction (one reads the Term true, the
  other reads it false), the same "the two never contend for the same
  node in one pass" property `gr_condition_lapse`/`gr_condition_hold`
  already have.

Both rules read `_order_n_is_not_live()` **verbatim**, imported unchanged
from the same module `SEL_AGID` itself calls it from — so this amendment
can never disagree with `ax_dispatch` about which collapse is live, by
construction, the same guarantee `ax_impotent` has via `_routable`/`ROUTE`.

**Bars, registered before any seed or adapter code is written.**

- **AR19a — a standing, inspectable fact exists and is minted when the
  order-N collapse is absent/not producing a stamp.** Demonstrated live on
  a constructed scene (boot without `arc_magnitude`, or with it loaded but
  `mg_select` never having fired): `AgendaVerdict{kind:'order_n_fallback',
  active:1.0}` is present and readable via the existing, unmodified
  `agenda_verdicts(sub, "order_n_fallback")`.
- **AR19b — the SAME fact does NOT appear (or clears) when order-N is
  live.** Two demonstrations, both live: (i) a NEGATIVE CONTROL — boot
  WITH `arc_magnitude` and the tier ladder installed from the start (the
  `test_wh1_*` scene) and show no `active` verdict of this kind ever
  mints; (ii) a TRANSITION — start from AR19a's exact scene (the fact
  active), load `arc_magnitude` onto the SAME live graph so `mg_select`
  fires for the first time, and show the held verdict's `active` flips to
  `0.0` on the very next `run_rules()` pass, with no epoch bump anywhere
  in the scene (the epoch-shaped lapse idiom is deliberately NOT what
  clears this fact — see design item 4).
- **AR19c — the fix does not change dispatch BEHAVIOR at all.** The
  fallback still fires exactly as before, and this rung only makes it
  observable. Verified by re-running the EXISTING WH1/WH3/second-
  ExecClass live-scene tests (`test_wh1_the_hands_now_follow_the_ORDER_N_
  collapse`, `test_wh1_CONTROL_without_the_tier_ladder_the_two_collapses_
  AGREE`, `test_wh3_the_fallback_when_the_order_N_collapse_is_NOT_on_the_
  graph`, `test_wh3_arming_on_the_ORDER_1_winner_no_longer_dispatches_
  under_order_N`, `test_wh3_the_ORDER_N_stamp_OUTLIVES_the_pool_and_the_
  pool_guard_catches_it`) UNMODIFIED and showing the exact same
  `ExecOrder`/`selected_by`/`order1_sel_agid`/`orderN_sel_agid` outcomes as
  WIRE_HANDS recorded — the new rules only ever add or edit `AgendaVerdict`
  nodes, never anything `ax_dispatch` reads.
- **AR19d — no regression, node-id lists not counts.** The six existing
  gate suites (`test_arc_executor_migrated`, `test_arc_goals_migrated`,
  `test_goal_residual_migrated`, `test_arc6_valuelayer_migrated`,
  `test_arc_magnitude_migrated`, `test_arc_decompose_migrated`) produce the
  same failing-node-id lists before and after, paired and named.
  `seeds/arc_goals.json`, `seeds/goal_residuals.json`, `seeds/arc_
  magnitude.json`, `seeds/arc_decompose.json`, `seeds/program_
  synthesis.json`, and every existing rule body in `tools/build_arc_
  executor_seed.py` (`ax_dispatch`, `ax_retired_epoch`, `ax_rearm`, `ax_
  close`, `ax_impotent`, `ax_world_probe_epoch`) stay byte-identical to
  `HEAD`. `seeds/arc_executor.json` regenerates byte-identically from its
  own (edited, version-bumped) emitter. The adapter source audit (no
  `.evaluate(`, no `run_rules`, no raw `substrate_rs` import) passes on
  `domains/arc_executor.py` — expected to need NO edit at all beyond,
  possibly, documentation prose (design item 5).

**Registered null reading.** If, during the build, `_order_n_is_not_live()`
turns out not to be safely reusable as a rule guard outside `ax_dispatch`
(for instance, if the engine's fixpoint semantics make a SECOND rule
reading the same Term race the first in some scene this investigation did
not anticipate), that is reported as a clean, well-evidenced null — this
arc's own standing culture — rather than forced through with a weaker
mechanism. Likewise, if live measurement finds the fallback structurally
unobservable at low cost (it does not, per design item 5, but the
possibility is named per the task's own instruction), the same applies.

**Explicitly out of scope, unchanged from A13–A18's shared boundary:**
`ag_ask`/`ax_dispatch` collapse-agreement in general, `gr_condition_
lapse`'s closed vocabulary, `results/arc6_import_impedance.json`/`scripts/
arc6_import_impedance.py`, and anything under `docs/research/theory_
convergence/` or `docs/research/adventure_mechanics/`. This amendment is
about OBSERVABILITY of the existing fallback, not about widening what the
executor can do once it observes it — no `ArcQuestion`, no minted
capability-acquisition goal, no change to what `ax_dispatch` runs.

---

### AMENDMENT A20 (2026-08-11) — `ag_ask` and `ax_dispatch`, reading different collapses IN GENERAL: characterize it, try to make it bite, then decide

`PROGRAM_SYNTHESIS_ARC6_WIRE_HANDS.md` §8 named this uncertainty FOURTH,
quoted because it is this amendment's charter: *"`ag_ask` AND THE HANDS NOW
READ DIFFERENT COLLAPSES. `ag_ask` is frozen and reads `arc_sel_*`;
`ax_dispatch` reads `mg_sel_*`. On the shipped boot they name DIFFERENT
goals, so the agent can ask about one goal while acting on another in the
same fixpoint — measured live at iteration 0 of WH2. Nothing broke, and the
ask is now mostly irrelevant, but 'the question and the action are about the
same thing' has quietly stopped being true and nothing asserts it either
way."* `PROGRAM_SYNTHESIS_ARC6_IMPOTENCE_CAMPAIGN.md` §9 restated the same
gap as its own uncertainty #3: *"not observed to matter in any scene this
campaign constructed... but not proven impossible either."* Two rungs, one
open question, never built against. This amendment is a MEASUREMENT rung
first (characterize + adversarially probe) and a build only if the
measurement earns it — the same shape A14 (impotence campaign) used.

**Scope, stated precisely, per the task's own boundary.** This is about
`ag_ask` vs `ax_dispatch` disagreeing about WHICH GOAL, not about the
order-N fallback (A19, already observable, a DIFFERENT and narrower
question — "is order-N live at all," not "do the two collapses, both
live, name the same winner"). Does not touch `gr_condition_lapse`'s
vocabulary, `results/arc6_import_impedance.json`/`scripts/
arc6_import_impedance.py`, or anything under `docs/research/
theory_convergence/` or `docs/research/adventure_mechanics/`. **Strong
preference against touching `ag_ask`/`seeds/arc_goals.json` at all** —
every prior rung in this arc has left it byte-frozen by name (WH3 §4.3,
A13/A14/A19 confinement tables), and WIRE_HANDS §4.3 recorded the reason:
*"`ag_ask` was not touched, and is not made worse."* Touching it here would
require a much higher evidentiary bar than any other change this amendment
could make.

**The design investigation, done before drafting bars.**

1. **`ag_ask` reads exactly three order-1 stamps and nothing else.**
   `tools/build_arc_goals_seed.py::_r_ask` binds its two named candidates
   by `Eq(g.agid, agenda.arc_sel_agid)` / `Eq(h.agid,
   agenda.arc_sel_runner_up_agid)` and fires on `Lt(agenda.arc_sel_margin,
   threshold)` — three order-1-only stamps (`ag_select` /
   `ag_select_runner_up` / `ag_select_margin`, all in
   `seeds/arc_goals.json`, all upstream of `arc_magnitude` even being
   loaded). `ax_dispatch` acts on `SEL_AGID()`
   (`tools/build_arc_executor_seed.py`), which is `mg_sel_agid` whenever
   `mg_select` has fired. **The two rules literally cannot share a stamp**
   — `ag_ask` is in a seed (`arc_goals`) that has never heard of
   `arc_magnitude`, confirmed by `grep -n arc_magnitude
   tools/build_arc_goals_seed.py` returning nothing.
2. **Order-1 and order-N can diverge through exactly two channels, both
   already shipped, and no others.** Reading `VALUE` (`ag_select`'s, order-1)
   against `VALUE_N` (`mg_select`'s, order-N,
   `tools/build_arc_magnitude_seed.py::VALUE_N`): they are the SAME term —
   same `PENALTY`, same policy weights — with exactly two edits: (a)
   `headroom_n` → `orderN_headroom_n`, and (b) a scope charge
   `MINUS(..., w_out_of_scope * out_of_scope)` present only in `VALUE_N`.
   Channel (a): `orderN_headroom_n` differs from `headroom_n` for a goal
   ONLY while it holds a non-stale tier-ladder projection
   (`mg_goal_order_n`'s guard, `_has_ladder() AND _live_projection()`);
   every other goal falls back to `orderN_headroom_n == headroom_n`
   (`mg_goal_order_n_default`, verbatim). **On the shipped 8-goal pool
   exactly ONE goal ever carries a ladder** —
   `arc.supply.arc6.seam_a.import_oracle.missing_structural_primitive`
   (`STRUCTURAL`/`SB_MSP`) — so channel (a) is a single-goal repricing
   effect, not a general reshuffling. Channel (b): `out_of_scope` is 1.0
   for a goal ONLY while a live `ArcConstraint{ckind:'scope'}` names a
   DIFFERENT `sig_seam` (`mg_scope_charge`'s guard, `_any_scope_held() AND
   NOT(_in_scope())`); with no scope constraint ever answered, `out_of_scope`
   is 0.0 for every goal and channel (b) is silent. **On the shipped boot
   with no constraint reply given, only channel (a) is live** — this is
   why WIRE_HANDS' own WH1 divergence (§2.1) is exactly the laddered
   goal's repricing (42 → 13.64) and nothing else. Channel (b) is
   real but requires an operator answer to fire, exactly the shape A14's
   own campaign used ("real" vs "hypothetical, reachable via a real
   mechanism") — this amendment will exercise it explicitly rather than
   leave it a claim.
3. **`ag_ask`'s reply can cross-affect `PENALTY`, and therefore CAN move
   order-N's ranking too — but only for a goal sharing the asked region's
   signature.** `PENALTY` is the one term `VALUE` and `VALUE_N` share
   unedited, and a testimony reply mints a `GoalResidual` keyed on the
   ASKED goal's `sig_seam`/`sig_lever`/`sig_target`
   (`_testimony_residual`, `region_seam`/`region_lever`/`region_target`
   read off the `ArcQuestion`, itself read off the winner `g` at ask
   time). `gr_move_penalty`'s wildcards mean this residual can charge ANY
   goal matching that region, not only the one asked about — AG-5 §8.3's
   own finding, `"an unconditioned answer penalises the region it is
   about, by weight, regardless of content."`  So a reply to `ag_ask`
   *can* move `mg_sel_agid`'s ranking, but only through the accident of
   two goals sharing a signature region — never through any direct
   channel, and never through anything but `PENALTY`. This is the
   mechanism the adversarial scene (AR20b) is built to stress: a scene
   where the order-N winner's region does NOT match either of `ag_ask`'s
   two named candidates isolates the case where a reply is provably inert
   on what actually dispatches.
4. **Neither collapse ever mints or executes anything on its own** — only
   `ax_dispatch` mints an `ExecOrder`, and only the adapter's `run_order`
   executes one, both already gated by `_armed`'s two-tick agreement and
   `_routable`/`_dispatchable`. So the WORST a divergence can do is: (i)
   waste a human's answer on a question naming a goal that was never
   going to be acted on regardless of the answer (an honesty/legibility
   defect in what `ag_ask` implies, not a graph-correctness defect), or
   (ii) via channel 3, reprice a goal the reply did not name, in a
   direction the replier did not intend — a SIDE EFFECT `ag_ask` already
   has today, independent of order-N, and not new here. Neither can cause
   `ax_dispatch` to mint an order for a "stale/wrong" goal beyond what
   `_armed`'s existing two-tick agreement already guards, because
   `ax_dispatch` never reads anything `ag_ask` or a reply writes except
   through the shared `PENALTY` term.
5. **The A19 precedent is directly reusable for the cheap fix, if one is
   warranted.** `AgendaVerdict` + `has_agenda_verdict` are already
   declared productions; a divergence fact is a THIRD pair in the same
   mint/clear shape (`ax_impotent`'s mint-once idiom, `ax_fallback_silent`/
   `ax_fallback_cleared`'s direct-reversible-pair idiom for a
   non-epoch-shaped liveness question) — no new DSL Term (`Eq` and
   `SEL_AGID()` both already exist and are already imported into
   `tools/build_arc_executor_seed.py`), no new node type, no new edge
   type, and — the point of this whole rung — **no edit to `ag_ask` or
   `seeds/arc_goals.json`**, because the fact only needs to compare a
   stamp `ag_ask` already reads (`arc_sel_agid`) against a stamp
   `ax_dispatch` already reads (`SEL_AGID()`), both on the SAME
   `ArcAgenda` node, from the executor seed alone.

**Bars, registered before any scene is constructed or any code is
written.**

- **AR20a — characterize divergence on constructed scenes, as a TABLE, not
  a bare claim.** At minimum: the WH1 shipped-boot scene (reproduced, not
  re-argued); a depletion sweep over the 8-goal pool (A14's own
  `_leave_pool` mechanism, one goal removed at a time) with and without the
  tier ladder, recording `arc_sel_agid`, `mg_sel_agid`, and whether they
  agree, at every step; and a scope-constraint scene exercising channel
  (b) via a REAL `attach_constraint_reply`. The table must let a reader
  answer, without re-deriving it: does divergence concentrate on the
  laddered goal specifically, or does it spread — and is the answer
  "concentrates," "spreads," or "does not occur under X"? A registered
  null reading: if fewer than 2 genuinely distinct divergent states are
  reachable by real/constructible mechanisms (echoing A14 IC2's own
  underpowered-n reading), that is reported as a small-n honest result,
  not stretched into a claim.
- **AR20b — an ADVERSARIAL scene, designed (not discovered) to make
  divergence bite, and report what actually happens.** Construct a pool
  where (i) `ag_ask` fires a genuine tie question naming two goals A/B
  under order-1 mutual ignorance, and (ii) the order-N winner is a THIRD
  goal C, distinct from both A and B, with a signature region that does
  NOT match either — isolating the case design item 3 names as the sharp
  one. A human replies to `ag_ask`'s literal rendered question. Measure,
  before and after the reply: does `mg_sel_agid` change; does the
  `ExecOrder` `ax_dispatch` would mint (or has minted) change; is there
  ANY causal path from the reply to what executes. Report the verdict
  honestly whichever way it comes out — "the reply is provably inert on
  what dispatches" is exactly as valid a finding here as "the reply moved
  the dispatched goal," and either is reported with the trace, not
  argued from the mechanism alone.
- **AR20c — a GO/NO-GO criterion for an observability fix, registered
  NOW, before AR20a/AR20b are run.** GO if AND ONLY IF: (i) AR20a/AR20b
  together show divergence is REAL (occurs on at least one constructed,
  non-contrived scene — already true per WH1 §2.1, so this is expected to
  be met) — divergence being rare or benign is NOT by itself a reason for
  NO-GO, because A19's own fallback fact was built for a condition no
  rung had ever observed causing harm; AND (ii) the fix is buildable in
  the SAME shape as A19's — a THIRD `AgendaVerdict` mint/clear pair, zero
  new DSL Term, zero new node/edge type, zero edit to `ag_ask`/
  `seeds/arc_goals.json`, zero change to `ax_dispatch`'s own dispatch
  decision (mirroring AR19c's own bar, re-verified here by re-running the
  EXISTING WH1/WH3/A19 live-scene tests unmodified). NO-GO if EITHER
  condition fails — in particular, NO-GO (not a weaker build) if the only
  buildable fix requires touching `ag_ask` itself, per this amendment's
  own stated preference against that, UNLESS the adversarial scene (AR20b)
  finds a genuinely bad, not merely observationally-absent, outcome that
  an `AgendaVerdict` fact could not adequately surface — a bar this
  amendment expects NOT to be met, stated before knowing whether it is.
- **AR20d — no regression, and `ag_ask`/`seeds/arc_goals.json` frozen
  unless overridden with strong, stated evidence.** The six existing gate
  suites (`test_arc_executor_migrated`, `test_arc_goals_migrated`,
  `test_goal_residual_migrated`, `test_arc6_valuelayer_migrated`,
  `test_arc_magnitude_migrated`, `test_arc_decompose_migrated`) produce
  the same failing-node-id lists before and after, paired and named.
  `seeds/arc_goals.json` and every rule body in
  `tools/build_arc_goals_seed.py` stay byte-identical to `HEAD` UNLESS
  this amendment's own investigation produces well-evidenced grounds to
  touch them — treated as requiring a materially higher bar than any
  other file this rung might edit, per the task's explicit instruction.
  If a build happens, every pre-existing rule body in
  `seeds/arc_executor.json` (`ax_dispatch`, `ax_retired_epoch`,
  `ax_rearm`, `ax_close`, `ax_impotent`, `ax_world_probe_epoch`,
  `ax_fallback_silent`, `ax_fallback_cleared`) stays byte-identical to
  `HEAD`'s own emitted copy.

**Registered null reading.** If AR20a/AR20b together show divergence is
either unreachable on any constructed scene beyond WH1's own (i.e. this
amendment adds no new evidence) or, having been reached and stressed
adversarially, provably causes no outcome an `AgendaVerdict` fact would be
worth minting for, the honest result is: characterized, adversarially
tested, confirmed benign, **nothing built** — exactly the shape this arc's
own culture already names as complete (M0's ceiling probes, A14's own
NO-GO). This is not a failure condition and is not to be forced into a
build to have something to show.

**Explicitly out of scope, unchanged from A13–A19's shared boundary:**
`gr_condition_lapse`'s closed vocabulary, `results/
arc6_import_impedance.json`/`scripts/arc6_import_impedance.py`, and
anything under `docs/research/theory_convergence/` or `docs/research/
adventure_mechanics/`.

---

### AMENDMENT A21 (2026-08-11) — `gr_condition_lapse`'s closed vocabulary vs. pool-composition drift: close the LAST originally-named remaining item, or prove it should stay closed

`PROGRAM_SYNTHESIS_ARC6_IMPOTENCE_TERM.md` §8 named this uncertainty FIRST,
quoted because it is this amendment's charter: *"A VERDICT'S CONDITION
LAPSES ON EPOCH ADVANCE ONLY, NOT ON POOL COMPOSITION DRIFT... a reader must
compare `pool_agids` against the CURRENT pool to know which one is current —
a second, pool-signature-keyed condition kind would need a change to
`gr_condition_lapse`'s closed `MISMATCH` vocabulary (`seeds/
goal_residuals.json`), which this rung's scope explicitly excludes
touching."* `PROGRAM_SYNTHESIS_ARC6_IMPOTENCE_CAMPAIGN.md` §9 item 6 carried
it forward, sharpened: the stored `nearest_unroutable_kind` can drift out of
sync with the live collapse on **no** composition change and **no** epoch
advance at all, only a reply — named, not built against, in both rungs. This
is the last of the six originally-named "remains to build" items in this
executor sub-thread (re-arm deadlock — A18; silent fallback — A19;
ask/dispatch safety — A20; MG4 decomposition and supply-blocker retirement —
already landed under their own docs).

**Scope, stated precisely, per the task's own boundary.** This is about
whether an `AgendaVerdict{kind:'impotent'}`'s recorded `pool_agids` can be
told apart, live and without waiting for an epoch bump, from the CURRENT
pool composition. It is explicitly **open both ways**: extend
`gr_condition_lapse`'s closed `MISMATCH` vocabulary (`shape_count`/
`payload_count`/`fact_equals`) with a fourth kind, OR apply A19/A20's own
reversible mint/clear pattern directly to `ax_impotent` in `seeds/
arc_executor.json` and leave `gr_condition_lapse` untouched, OR — if neither
is well-evidenced as worth its cost — build nothing and report a clean null,
per this arc's own standing culture (M0, A14). Does not touch `results/
arc6_import_impedance.json`/`scripts/arc6_import_impedance.py`, or anything
under `docs/research/theory_convergence/`, `docs/research/
adventure_mechanics/`, or `docs/research/engine_substrate/
decision_making_spike.md`.

**The design investigation, done before drafting bars.**

1. **Exactly one shipped `AgendaVerdict` kind carries a pool-signature-
   shaped field at all.** `grep -n '"pool_agids"' tools/build_arc_executor_
   seed.py` returns hits only inside `_r_impotent`'s own guard and effects
   (`_pool_sig()`, `MAPLIST(POOL(), ...)` JSON-encoded). The other two kinds
   this arc has minted (`order_n_fallback` — A19; `ask_dispatch_divergence`
   — A20) carry no pool-shaped field: the first is a single Term's truth
   value (`_order_n_is_not_live()`), the second is a two-goal comparison
   (`SEL_AGID()` vs `arc_sel_agid`) — neither has a "which of several
   possible states am I describing" axis, only an on/off one. So the drift
   problem named by A13/A14 is narrower than "any `AgendaVerdict`" — it is
   specific to the one kind whose identity is a SET (the pool), not a
   scalar.
2. **`gr_condition_lapse`'s three `ckind`s are each keyed to a MECHANICALLY
   PROBED fact, not a graph-native Term — and that is a real, load-bearing
   asymmetry, not an accident.** `shape_count`/`payload_count`
   (`tools/build_goal_residual_seed.py::_shape_count`) read `ShapeSignature`
   nodes directly, live, inside the rule — no Python between the condition
   and the count. `fact_equals` is different in kind: it compares against a
   `ResidualFact{name,value}` node, and EVERY existing `ResidualFact` on this
   graph is written by `domains/goal_residual_ingest.py::probe_facts`/
   `install_facts` — Python code that reads an external world (a file's
   presence/sha, a live value-layer probe) and stamps the answer as mechanical
   I/O, explicitly called, not continuously re-derived inside `run_rules()`.
   `arc_measure_epoch` (the ONE `fact_equals` condition `ax_impotent` itself
   already uses) is the one exception that proves the rule: it is a plain
   counter with a producer already living in the executor's own rules
   (`ax_dispatch`'s `run_order`/epoch-bump path), so comparing against it
   needs no new Python probe. **The pool's live signature (`_pool_sig()`) is
   ALREADY a pure, existing DSL Term, evaluated inside `ax_impotent` itself
   — it needs no Python probe of any kind.** Wiring a pool-drift condition
   through `fact_equals` would mean inventing a Python step that probes the
   graph's OWN pool and writes it back as a `ResidualFact` — exactly the kind
   of "push a graph-native computation out into Python" move `CLAUDE.md`
   forbids, for a quantity the graph can already compute itself, live, in
   the same rule that would consume it.
3. **A fourth `ckind` computed natively (no Python probe) would still couple
   the GENERIC residual seed to one DOMAIN's concept.** `seeds/goal_
   residuals.json` is shared infrastructure — `ps_move_select`
   (`seeds/program_synthesis.json`) and every arc-4/5/6 `GoalResidual` ride
   the same `MISMATCH`/`gr_condition_lapse`/`gr_condition_hold` pair. `POOL()`
   and `_pool_sig()` are `ArcAgenda`-shaped Terms defined in `tools/build_
   arc_goals_seed.py`/`build_arc_executor_seed.py`, seeds `goal_residuals`
   has never imported and does not depend on
   (`grep -n 'import.*arc_goals\|import.*arc_executor' tools/build_goal_
   residual_seed.py` — no hits). A `pool_sig_equals` `ckind` hard-coding
   `_pool_sig()`'s Term shape into `MISMATCH` would be the FIRST domain-
   specific concept the generic vocabulary has ever carried — a real
   modularity cost, not a hypothetical one, weighed against the fact that
   `gr_condition_lapse`'s `match` already has no type constraint on the node
   it lapses (A13's own reason it could ride an `AgendaVerdict` for free in
   the first place) — riding it costs nothing at the RULE level; the cost is
   entirely at the VOCABULARY-COUPLING level.
4. **A19/A20 already solved a closely analogous problem, twice, WITHOUT
   touching `gr_condition_lapse`, and the reasoning transfers almost
   verbatim.** A19's design item 4 (quoted above, this file) rejected the
   epoch-shaped `fact_equals` idiom for the SAME structural reason pool
   drift has: the fact in question ("is X true right now") can change with
   NO epoch bump in the scene, so a description that is honest only until
   the next measurement is the wrong shape — instead A19/A20 each added a
   direct reversible pair (`ax_fallback_silent`/`ax_fallback_cleared`,
   `ax_ask_divergence_active`/`ax_ask_divergence_cleared`) keyed on a LIVE
   Term comparison, entirely inside `seeds/arc_executor.json`. The one
   respect in which pool drift is NOT identical to either precedent: A19/A20
   are both SINGLETON facts (the fallback is either live or not; the two
   collapses either agree or not — `EXISTS` an `active`-flagged node of that
   kind is the whole state). `ax_impotent`, by IM5's own registered design
   (A13 §6), intentionally allows MULTIPLE `AgendaVerdict{kind:'impotent'}`
   nodes to coexist — one per distinct pool signature, a deliberate
   historical record, gated live
   (`test_im5_a_DIFFERENT_impotent_pool_mints_its_OWN_verdict`). A literal
   A19-shaped singleton `active` flag (one global boolean, mutually
   exclusive on/off) would COLLAPSE that history the first time the pool
   drifts while remaining impotent — worse than the status quo, not better.
   The candidate design this investigation surfaces (to be judged live, not
   assumed) is A19/A20's REVERSIBLE-PAIR SHAPE applied PER-NODE — an `active`
   attr on EACH `AgendaVerdict{kind:'impotent'}`, flipped by comparing that
   NODE's own `pool_agids` against the CURRENT `_pool_sig()` (not a
   singleton `EXISTS` guard) — preserving IM5's multi-verdict history while
   adding the missing "which one is current" marker, entirely inside `seeds/
   arc_executor.json`, zero touch to `gr_condition_lapse`.
5. **The epoch-keyed `stale` flag (unmodified `gr_condition_lapse`) and a
   pool-keyed `active` flag would be answering two DIFFERENT, both
   legitimate questions, not competing for the same bit.** `stale` says "a
   measurement has happened since this was minted, so treat it as possibly
   outdated until re-verified." A pool-keyed `active` would say "the pool
   this verdict describes IS/IS NOT the one that exists right now,
   regardless of epoch." A verdict can be `stale:1.0, active:1.0`
   (superseded by a later measurement, but still describing today's actual
   pool) or `stale:0.0, active:0.0` (current epoch, but the pool has since
   moved under it without a re-measurement) — genuinely different facts,
   both worth holding, neither redundant with the other. This is itself
   evidence for keeping them as two separate, orthogonal mechanisms rather
   than trying to fold pool-drift into the epoch-shaped one.

**Bars, registered before any seed or adapter code is written or any GO/
NO-GO decision is made.**

- **AR21a — characterize exactly which shipped verdict kinds carry a
  pool-signature-style (set-valued, not scalar) field, as a table, not a
  bare claim.** Read `tools/build_arc_executor_seed.py` in full for every
  `AgendaVerdict` kind this seed mints (`impotent` — A13; `order_n_fallback`
  — A19; `ask_dispatch_divergence` — A20; any landed since, e.g. under
  MG4/supply-blocker-retirement) and record, per kind: does it carry a
  `pool_agids`-shaped (ordered-list/set) field; is its identity a scalar
  Term comparison or a set comparison; would pool-composition drift (as
  opposed to a single Term flipping) even apply to it. Confirms or refutes
  design item 1's claim that exactly one kind (`impotent`) is in scope.
- **AR21b — a GO/NO-GO criterion for vocabulary-extension vs.
  reversible-pair-applied-to-`ax_impotent` vs. neither, registered NOW,
  before either is built.** Extend `gr_condition_lapse`'s `MISMATCH`
  vocabulary (a fourth `ckind`) ONLY IF: (i) it can be computed with NO new
  Python probe (a pure graph-native Term, matching `shape_count`/
  `payload_count`'s existing shape, NOT `fact_equals`'s Python-mediated
  shape) — per design item 2, this is expected to fail for a naive
  `fact_equals`-shaped implementation and is registered as a hard
  disqualifier if it does; AND (ii) the domain-specific Term it needs
  (`POOL()`/`_pool_sig()`) is judged, on inspection, cheap and safe to
  import into the generic `goal_residuals` seed without creating a
  circular or one-off dependency a future non-ARC-6 residual would have to
  route around. Apply the A19/A20 reversible-pair pattern DIRECTLY to
  `ax_impotent` (entirely inside `seeds/arc_executor.json`, zero edit to
  `seeds/goal_residuals.json`) INSTEAD IF: (iii) it can be built PER-NODE
  (not as a A19/A20-shaped global singleton) so IM5's multi-verdict history
  is preserved, not collapsed — this is registered as the load-bearing
  discriminator against a lazy reuse of the A19 shape verbatim; AND
  (iv) it costs strictly less (fewer new productions/node-types/rules, no
  cross-seed coupling) than the vocabulary extension, per design items 3–4.
  If BOTH approaches clear their own conditions, prefer the reversible pair
  (cheaper, lower-risk, and does not touch shared infrastructure other
  threads depend on) — registered now, before knowing whether both, either,
  or neither clears. NO-GO on BOTH (build nothing, report a clean null) if
  neither clears its conditions, or if live measurement shows pool-drift-
  while-impotent is never actually reachable by any real or realistically
  constructible mechanism this tree has (echoing A14 IC2/IC3's own
  underpowered-null path) such that the fix would have nothing to
  demonstrate itself against.
- **AR21c — if built, demonstrate live, BOTH directions, matching IM5's own
  "mint-once by pool signature, lapse via gr_condition_lapse" discipline —
  now actually closing the gap that discipline left open.** (i) FIRES ON
  DRIFT: construct a scene where the pool is impotent, let a verdict mint,
  then change pool COMPOSITION (not epoch) while remaining impotent (the
  same `headroom_n → 0` pool-exit technique A13 §7.1 validated, applied a
  second time) — the mechanism must, within the SAME `run_rules()` fixpoint
  and with NO epoch bump anywhere in the scene, mark the superseded
  verdict's currentness correctly and produce (or already have produced,
  per IM5) a fresh verdict/marker for the new composition. (ii) DOES NOT
  FIRE WITHOUT DRIFT, INCLUDING ACROSS A GENUINE EPOCH-ADVANCING
  REMEASUREMENT: reproduce IM5's own "bump `arc_measure_epoch`, pool
  composition UNCHANGED" scene and show the pool-drift marker does NOT flip
  on the unchanged-composition verdict(s) — the new mechanism must be
  provably orthogonal to the epoch-shaped one, not a duplicate trigger for
  it. Both directions measured live, on a fresh boot, not asserted from the
  mechanism's shape alone.
- **AR21d — no regression, node-id lists not counts.** The six existing gate
  suites (`test_arc_executor_migrated`, `test_arc_goals_migrated`, `test_
  goal_residual_migrated`, `test_arc6_valuelayer_migrated`, `test_arc_
  magnitude_migrated`, `test_arc_decompose_migrated`) produce the same
  failing-node-id lists before and after, paired and named. `seeds/arc_
  goals.json` and every existing rule body in `tools/build_arc_executor_
  seed.py` (`ax_dispatch`, `ax_retired_epoch`, `ax_rearm`, `ax_close`, `ax_
  impotent`, `ax_world_probe_epoch`, `ax_fallback_silent`, `ax_fallback_
  cleared`, `ax_ask_divergence_active`, `ax_ask_divergence_cleared`) stay
  byte-identical to `HEAD` UNLESS this amendment's own investigation
  produces well-evidenced grounds to touch one (in particular, `ax_impotent`
  itself may gain an ADDITIVE `active:1.0` stamp at mint time — an
  ADDITION, not a behavioural edit to its `match`/`where`/mint-once guard,
  which must stay byte-identical). If `gr_condition_lapse`'s vocabulary is
  extended instead, `gr_condition_hold` and every OTHER residual's
  conditions stay byte-identical and every existing `test_gr2_*`/`test_gr1_*`
  gate keeps passing unmodified. `seeds/arc_executor.json` (and/or `seeds/
  goal_residuals.json`, if that path is taken) regenerates byte-identically
  from its own edited, version-bumped emitter.

**Registered null reading.** If AR21b's GO/NO-GO reads NO-GO for both
approaches — because the vocabulary extension fails its no-Python-probe/
no-harmful-coupling test AND the reversible-pair pattern cannot be built
per-node without cost disproportionate to the benefit, or because live
measurement shows the gap is not reachable by any real/constructible
mechanism — the honest result is: investigated, a concrete design
identified and costed, **nothing built**, and `gr_condition_lapse`'s
vocabulary reported as correctly staying closed with the A19/A20 idiom
named as the preferred pattern for this class of problem going forward —
exactly the shape this arc's own culture already treats as a complete
result (M0, A14). This is not a failure condition and is not to be forced
into a build to have something to show.

**Explicitly out of scope, unchanged from A13–A20's shared boundary:**
`results/arc6_import_impedance.json`/`scripts/arc6_import_impedance.py`,
and anything under `docs/research/theory_convergence/`, `docs/research/
adventure_mechanics/`, or `docs/research/engine_substrate/
decision_making_spike.md` (the last actively being extended by a concurrent,
unrelated agent).
