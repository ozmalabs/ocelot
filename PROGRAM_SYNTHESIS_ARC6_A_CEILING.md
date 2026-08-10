# ARC 6 — SEAM A, THE A-CEILING: the import list, measured

**Date:** 2026-08-01. Companion to `PROGRAM_SYNTHESIS_ARC6_PLAN.md` §1 Seam A
and §3 M0, `RESEARCH_IMPORT_SOURCES.md` (which established SymPy as the import
vehicle and the no-shelling-out constraint), and `PROGRAM_SYNTHESIS_ARC6_M0_AB.md`
§1 (which measured the same ceiling against the *tower's own* kernels over the
222-task unreached population; this document measures it against **SymPy** over
`PROGRAM_SYNTHESIS_ARC4_S4_NOTES.md`'s **60-task residual**).

**Status: MEASUREMENT. Nothing was built.** No file under `seeds/`, `runners/`,
`domains/`, or any adapter was modified or read-for-edit. No `git add`/`commit`/
`stash`. Artefacts created: `scripts/arc6_a_ceiling.py`,
`results/arc6_a_ceiling.json`, this document.

**Contamination discipline.** MBPP test-split `code` was read for MEASUREMENT
classification only. No prompt text and no reference code entered any codebook,
cue vocabulary, or taught shape. Every claim below is a **paired id list**, never
a count alone.

**Engine provenance (added 2026-08-02 after the two-binary hazard was raised).**
This measurement **loads no engine at all** — `substrate_rs` modules loaded: `[]`.
The one engine-dependent *input* was audited and traced to the intended binary
**`5c1b472f…`**. Full audit in §1.1; stamp in
`results/arc6_a_ceiling.json :: engine_provenance`. **No number in this document
moved.**

---

## 0. The one-paragraph answer

Registering SymPy modules **at module granularity** — the only granularity that
is not a disguised copy of the answer key — unlocks **5 of the 53 live-unreached
tasks** (`80, 246, 248, 293, 422`) under the strictest honest reading, or **8**
(`+88, 141, 255`) if you also accept `sympy.utilities.iterables`, whose
blind-registration case is weak and whose yield is mostly *not mathematics*. A
per-task cherry-pick would report **27**, and the same move taken to its limit
reports **60**. **The gap between 5 and 27 is not a measurement difference — it
is the difference between an import and a leak.** The one result that is
qualitatively stronger than its size: **4 ids are blocked by a missing
*dimension***, not by search budget, and arc 5 already proved that supplying such
a dimension converts (it closed 6 of these very ids).

---

## 1. Population, and a correction to it

| step | n | source |
|---|---|---|
| S4's 85-task bucket | 85 | `results/arc4_backward_probe.json :: ha4_search_reach_sizing.ok_already_no_named_lever` |
| moved off `gapped:enumerate_failed` by S4 | 25 | `PROGRAM_SYNTHESIS_ARC4_S4_NOTES.md` §3's three tables |
| **S4 residual** | **60** | derived, never retyped |

**The 60 is stale by 7, and the direction of the staleness is the finding.**
Cross-checked against the most recent live full-test-split pass list
(`PROGRAM_SYNTHESIS_ARC6_M0_AB.md` §0, measured 2026-08-01 through the unmodified
`mbpp_endgame_battery` driver, twin-run identical):

> **S4-residual ids that now PASS: `59, 82, 85, 139, 233, 276, 312` (7).**
> **Live unreached: 53.**

Six of those seven (`82, 85, 139, 233, 276, 312`) are the π-geometry tasks, and
they were closed by **arc 5's exact-first rung — i.e. by supplying a missing
dimension exactly.** That is not a coincidence; it is the single strongest piece
of prior evidence bearing on this seam, and §4 leans on it.

*Condition on that pass list, stated because a claim quoted without its condition
is this project's own named defect:* it was measured on 2026-08-01 and is **not
re-run here**, because a sibling agent is concurrently editing `seeds/` and a
battery run today would measure a half-edited seed state. A dated number with its
condition beats a fresh number measured against a moving target.

### 1.1 Engine provenance — which binary every claim rests on

**The hazard is real and I reproduced it in this worktree.** A bare script here
resolves `substrate_rs` to the **canonical** tree's binary, because
`site-packages/substrate_rs.pth` is an absolute path into the canonical tree and
`_native.abi3.so` is gitignored:

```
bare script in this worktree  ->  .../gamma-substrate/runners/.../_native.abi3.so
                                  sha256 7dd9af13…   (the CANONICAL one)
```

**The two binaries are not interchangeable, and I confirmed it by symbol content
rather than by date or path.** `strings` finds `SumList`, `MaxLenOver`,
`MinLenOver`, `JoinList`, `LastElem` in `5c1b472f…` and **not** in `7dd9af13…`.
The canonical binary predates **arc4-S4's list-op widening entirely**. (`MapList`
and `FilterList` appear in both, because those are pre-existing `TermNode`
variants in `term.rs`, not the enumerator op names — consistent with S4's own note
that it added no new Term variant.)

**Finding 1 — this measurement is engine-independent.** The process loads **no
`substrate_rs` module** (`modules_loaded == []`, now asserted and recorded every
run). All 20 probes, the family inventories, the namespace absence checks, and
every ceiling number are pure Python + SymPy. **Nothing here can move with the
binary.**

**Finding 2 — the one engine-dependent input traces to the intended binary.**
The staleness cross-check (§1's 7 ids) reads `pass_ids` from
`results/arc6_ceiling_ab.json`, which *was* produced by running an engine. It was
`5c1b472f…`, established two independent ways:

- *By path (weaker):* `scripts/arc6_ceiling_ab.py` derives `ROOT` from its own
  `__file__` and inserts `ROOT/runners/dsl/python` at `sys.path[0]` — so unlike a
  truly bare script it **pre-empts the `.pth`**. That artifact's recorded
  `environment.cwd` is this worktree. Reproducing the exact preamble live
  resolves to `5c1b472f…`.
- *By content (decisive, and independent of all path reasoning):* that pass list
  contains **all eight** of S4's list-op conversions — `69, 90, 132, 145, 278,
  410, 443, 472`. Tasks **90** and **132** require `MaxLenOver` and `JoinList`,
  symbols that **do not exist** in `7dd9af13…`. A run on the canonical binary
  **could not have produced that list.**

**Finding 3 — the analysis is stated relative to `5c1b472f…`, and the error
direction is safe.** The `BLOCKER` and `residual_blocker_after_kernel`
classifications assert what the enumerator can compose, assuming S4's op set. That
is true of `5c1b472f…`. Had I unknowingly reasoned against the canonical binary,
the mistake would be **conservative**: fewer ops means *more* tasks blocked, so
the strict ceiling could only fall, never rise. The 5 is not inflated by this.

**Caveat I cannot close from here:** `scripts/arc6_ceiling_ab.py` does not call
`engine_preamble()`, and `results/arc6_ceiling_ab.json` records no engine sha —
its provenance is *inferred* above, not stamped at the time. The content argument
makes the inference strong, but the general fix belongs in that script, not this
one. **`scripts/arc6_a_ceiling.py` now pre-empts the `.pth` and stamps the engine
on every run regardless.**

---

## 2. What is actually blocking the 60 — and how much of it a kernel can even touch

Classified per task from prompt + reference code (analysis, labelled as such;
full per-task reasons in `results/arc6_a_ceiling.json :: blocker_split.
per_task_reason`).

| blocker class | over the 60 | over the live 53 | can an import fix it? |
|---|---|---|---|
| **`missing_dimension`** — needs a value not constructible in-frame at **any** search size (π, an irrational, a complex argument) | 10 | **4** | **YES, and this is the strong claim** |
| **`budget`** — every primitive exists; the composition is deeper than `max_size=9` or outside the bounded template pool | 8 | **7** | yes, but a kernel only **shortens a search** |
| **`missing_structural_primitive`** — sort, dict/tuple construction, string split/replace/reverse, `(index,element)` binding, nested iteration | **42** | **42** | **NO mathematical kernel does.** See §3.1(b) |

`missing_dimension` ids over the live 53: **`163, 246, 252, 293`**
(over the full 60, additionally `82, 85, 139, 233, 276, 312` — the six already
closed by arc 5).

`budget` ids over the live 53: **`80, 137, 162, 248, 422, 435, 442`**.

`missing_structural_primitive` ids (all 42): `11, 18, 75, 87, 88, 98, 99, 102,
106, 118, 141, 161, 170, 172, 226, 230, 232, 255, 257, 260, 262, 264, 265, 283,
290, 301, 310, 390, 411, 419, 421, 424, 437, 439, 448, 450, 456, 462, 473, 474,
475, 479`.

**The dominant fact about this population, stated first because it bounds
everything after it: 42/53 (79%) of the live-unreached tasks are blocked by
something no import can supply.** S4's own taxonomy said as much (classes D/F/G
were sort, advanced string ops, dict construction); the arc-6 plan's framing of
the residual as "folds, combinatorics, number theory, and sqrt/trig composites"
describes **class E only**, which is the smallest of them. That framing is
corrected here.

---

## 3. The import list, ranked by tasks-unlocked per unit of import work

Every kernel below was **verified by live invocation on that task's own example
rows**, never accepted on the strength of its name (§5 contains three cases where
the name was right and the invocation was wrong). Every family carries an
explicit answer to: **would this be registered if the test split did not exist?**

`n_strict` = kernel verified **and** the remaining composition is already inside
the enumerator's reach. `n_verified` = kernel verified, but something else may
still block the task. **Only `n_strict` is a claim about conversion.**

| rank | import unit (module granularity) | callables | blind? | `n_strict` (ids) | `n_verified` (ids) | cost |
|---|---|---|---|---|---|---|
| 1 | **`sympy.functions.combinatorial.factorials`** — factorial, factorial2, binomial, subfactorial, ff, rf | 23 | **YES** | **2** (`80, 422`) | 2 | **LOWEST** — `math.comb` is already imported and called inside `domains/reason.py`; this is registration, not import |
| 2 | **`sympy.functions.combinatorial.numbers`** — the named integer sequences (fibonacci, lucas, catalan, bell, bernoulli, euler, harmonic, partition, …) | 73 | **YES** | **1** (`248`) | 1 | **LOWEST** — one module, one concept |
| 3 | **`sympy.functions.elementary.{miscellaneous,trigonometric,complexes}` + `sympy.pi`** — sqrt, cbrt, root, sin/cos/tan/atan2, Abs/arg/re/im, π, e | 133 | **YES** | **2** (`246, 293`) | **4** (`+163, 252`) | **MEDIUM** — the only family that needs an exact→rendered step at the ProgEval boundary (§6) |
| 4 | **`sympy.ntheory`** — the exact integer callables | 71 | **YES** | **0** | **3** (`99, 283, 479`) | **LOWEST** — but see the inversion below |
| 5 | **`sympy.utilities.iterables`** — subsets, multiset, ordered, dict_merge, partitions, … | 64 | **WEAK** | **3** (`88, 141, 255`) | 4 (`+232`) | LOW — but the blind case is weak and the yield is mostly non-mathematical |
| — | **`sympy.concrete.summations` / `sympy.solvers.recurr`** | 90 | **NO — rejected** | — | — | takes **symbolic** arguments, not Values; an oracle receives evaluated Values. Wiring it is **Seam B's** job (prose→formula), not Seam A's. Listed so the exclusion is visible. |

### 3.1 Two inversions in that ranking, both worth more than the ranking itself

**(a) The impedance probe's rank-1 recommendation yields zero.**
`RESEARCH_IMPORT_SOURCES.md` §5 ranked `sympy.ntheory` first — correctly, on
exactness, licence and walk cost. Against *this* population it strictly unlocks
**nothing**. Its three kernel-verified hits (`99` base conversion, `283` digit
frequency, `479` leading digit) each compute the mathematics exactly and are then
**blocked by a structural primitive** the enumerator lacks — a drop-first slice,
dict-items iteration, and an `IndexAt(_,1)` template respectively. A source can be
the best import in the abstract and the wrong import here; only the cross-check
against the actual population separates those, and the impedance probe explicitly
named that cross-check as unperformed future work. It is performed here, and it
inverts the ranking.

**(b) The family with the *weakest* registration case tops the strict list —
and all three of its wins are tasks §2 classified as *not fixable by a kernel*.**
`sympy.utilities.iterables` strictly unlocks `88, 141, 255`, and every one of
those three sits in the `missing_structural_primitive` bucket. That is not a
classification error; it is the point. `multiset` is a frequency counter,
`ordered` is a sort, `subsets` is a combination generator — **F4 converts by
importing the structural primitives the enumerator lacks, dressed as a
mathematics import.** It is an honest consequence of module granularity and it is
also the warning: **if a family's yield sits entirely outside the concept the
family is named for, the "module" unit has stopped doing its job of being
task-independent.** F5's yield is all cross-frame mathematics; F3's is all
combinatorics; F4's is a grab-bag. That asymmetry is the tell, and it is why the
5-id strong-families figure, not the 8-id figure, is the one to scope from.

The constructive reading of the same fact: **`sort`, `frequency-map` and
`combination-generator` are worth adding as enumerator primitives on their own
merits** — 42/53 of this population is blocked by that class of thing. But that
is Seam A's neighbour, not Seam A: it is a search-reach widening in the S4 style,
and calling it a kernel import would misattribute it.

---

## 4. The two ceilings, and the gap between them

| reading | n | ids | what it means |
|---|---|---|---|
| **HONEST, strict, strong families only** (F1/F2/F3/F5) | **5** | `80, 246, 248, 293, 422` | a callable already present in a module registered *as a whole* computes the task's mathematics, verified on the task's own rows, and nothing else blocks |
| HONEST, strict, all families (incl. weak F4) | 8 | `+88, 141, 255` | as above, accepting the grab-bag module |
| HONEST, kernel-verified (composition may still block) | 14 | `+99, 163, 232, 252, 283, 479` | the kernel is **necessary but not sufficient** |
| **CHERRY-PICKED, concept level** | **27** | every math-shaped id in the 60 | one bespoke kernel per task, named after that task's own concept: `octagonal()`, `perrin_sum()`, `newman_prime()`, `area_polygon()`, `tetrahedral()`… |
| **CHERRY-PICKED, reductio** | **60** | all of them | an oracle named `mbpp_task_<id>` per task |

**The gap is 5 → 27 → 60: a 5.4× and a 12× inflation, available for free, from
the same measurement, by changing nothing but the granularity of the import
unit.** Every step of that inflation is individually defensible in prose ("we
just need a Perrin kernel; Perrin numbers are a real mathematical object") and
the aggregate is a fabricated result: an oracle table assembled that way encodes
the test-split answers, and every later conversion is a coincidental fit by
construction. Four coincidental fits have already been caught in this project.
This would have been the fifth and the largest, and — unlike the previous four —
it would have been produced by the *natural* way of doing the task.

**The rule that keeps 5 from becoming 27, stated so it can be reused:** the
import unit must be nameable **before** the population is read, and its yield
must be a *consequence* of the unit rather than the *reason* for it. `register
sympy.ntheory` passes that test and yields 0. `register a Perrin kernel` fails it
and yields 1. The unit that fails the test is worth less than the one that yields
nothing.

### 4.1 The missing-dimension split — a different and stronger claim

A kernel that **shortens a search** and a kernel that **supplies a dimension** are
different claims, and only the second is unreachable-at-any-search-size.

- **Supplies a missing dimension** (live-unreached): **`163` (π and tan), `246`
  (sqrt), `252` (complex modulus/argument), `293` (sqrt)** — 4 ids, all served by
  family F5, none reachable by any budget increase.
- **Merely shortens a search** (live-unreached, kernel-verified): `80`, `422`,
  `248` — closed forms replacing folds/deep compositions that the primitives could
  in principle express given a bigger `max_size`.

**The prior evidence for the first list is unusually strong and it is already
in hand.** Arc 5's exact-first rung supplied π exactly and converted `82, 85,
139, 233, 276, 312` — six ids that sat in exactly this class in exactly this
bucket. The dimension claim is therefore not speculative here: it has already
been run once, on this population, and it worked. F5 is the same move continued
into sqrt/trig/complex.

**Honest counterweight, in the same breath:** of the 4, only 2 (`246`, `293`) are
strictly unlocked. `163` still exceeds `max_size=9` after the kernel, and `252`
still needs tuple construction — which task `257` ("return a tuple with the second
number then the first") proves the enumerator cannot do at all.

---

## 5. Refuted by invocation — the cases where the name was right and the kernel was wrong

The brief's instruction not to judge from the name earned its keep three times.

| task | kernel that *looks* like the answer | rows matched | why it fails |
|---|---|---|---|
| **462** "all possible combinations of a list" | `sympy.utilities.iterables.subsets` | **0/3** | `subsets` emits **size-lexicographic** order; the task asserts **binary-reflected** order. The concept matches perfectly; the extension does not. |
| **87** "merge three dictionaries" | `sympy.utilities.iterables.dict_merge` | **1/3** | `dict_merge` is **last-wins**; the reference is `ChainMap({}, d1, d2, d3)`, i.e. **first-wins**. Row 1 passes only because its duplicate keys happen to agree. |
| **475** "sort a dictionary by value" | `sympy.utilities.iterables.ordered` | n/a | `ordered` sorts by SymPy's own `default_sort_key`, **not** by a caller-supplied key. There is no family callable for this task; the probe falls back to plain `sorted(...)` and is **excluded from every ceiling**. |

Row 1 of task 87 is the sharpest of the three: **a kernel verified on one example
row and reported as a match would have been a fifth coincidental fit, produced by
under-sampling rather than by cherry-picking.** All three rows are required.

**The converse error is also real, and the same instrument catches it.** A live
namespace search over every registered family found **no callable named
`tetrahedral`** — and yet `binomial(n+2, 3)` reproduces task 80 on all three
rows. Name-search *understates* reach exactly as often as name-matching
*overstates* it. Invocation is the only instrument that is correct in both
directions.

**Verified absent by namespace search** (no callable in any registered family):
Perrin (`448`), Newman–Shanks–Williams / Pell (`260`), octagonal/polygonal
(`59`). Those three are precisely the ids a concept-level cherry-pick would have
claimed most confidently.

---

## 6. What broke while measuring — import cost that nobody had priced

Breakage is signal about real import cost, so it is recorded rather than
smoothed over.

1. **An exact SymPy result does not compare equal to the assert's float.**
   Task 422: `binomial(3,2)**2/2` returns `Rational(9,2)`; the assert is
   `== 4.5`. Under Python `==` that is **False**, and the first run of this
   measurement duly reported task 422 as `verified_partial` (2/3) — a *refutation
   caused by the harness*, not by the kernel. **The oracle is right to return the
   exact Rational.** This is CLAUDE.md's frame/continuum invariant surfacing as an
   integration cost: the exact value is the in-frame datum, the float is the
   rendering, and the *verdict layer* owns the comparison. **Any real Seam A build
   needs an explicit exact→rendered step at the `ProgEval` boundary, and that step
   is import work that appears in no cost estimate so far, including this
   document's own MEDIUM rating for F5.** Fixed by recording
   `rendering_required` per row instead of failing silently.

2. **`assert set(f(...)) == set(...)` lost its wrapper**, so task 232's list
   result was compared against a set and spuriously refuted on all 3 rows. A
   measurement bug in the *refuting* direction is the dangerous kind here: it
   under-reports the ceiling and is indistinguishable from an honest null. Found
   by reading the row-level `got`/`expected` pairs rather than the aggregate.
   Fixed by carrying the LHS wrapper through to the probe's own result.

3. **`sympy.utilities.iterables` emits a `SymPyDeprecationWarning` on import**
   (`default_sort_key` moved, deprecated since 1.10, "will be removed in a future
   version"). F5's modules do not. This is a small live signal that F4 is not a
   stable public API surface, which compounds its already-weak
   blind-registration case.

4. **A generator/dict-valued return may not cross the Value boundary at all.**
   F4's strict yield (`88` returns a dict, `141`/`255` return lists of tuples)
   depends on the `{"type":"Lit","value":…}` JSON boundary that
   `PROGRAM_SYNTHESIS_ARC4_S4_NOTES.md` §4.3 already names as a live gap for
   set-valued specs (task 115). **This was NOT tested here** — testing it would
   mean invoking the pipeline, which is a build, not a measurement. Named as an
   unpriced risk that lands entirely on the lowest-ranked family.

5. Inherited, and re-confirmed as still relevant: the impedance probe's own
   SymPy walk hung with no traceback until a per-call `signal.alarm` timeout was
   added (`RESEARCH_IMPORT_SOURCES.md` §4.5). This measurement's probes are all
   small-argument and none hung, but a *registration* pass over 364 callables
   would hit the same wall.

---

## 7. What would make Seam A a null

Stated explicitly, in advance, so the answer cannot be renegotiated afterwards.

**Seam A is a null if any of the following hold.**

1. **The strict honest ceiling does not survive the pipeline.** The 5 ids
   (`80, 246, 248, 293, 422`) are unlocked *in principle*: a registered kernel
   computes the value and the residual composition is nominally in reach. If a
   built M1 converts fewer than 5 of those 5 — for any reason: the exact→rendered
   boundary (§6.1), the Value/JSON boundary (§6.4), the decoy tax — then module
   registration does not convert and the seam is a null **even though every
   kernel claim in this document is true**.

2. **The conversions arrive but only via per-task registration.** If M1 needs an
   oracle table that could not have been written before reading the population,
   the number it produces is the 27, not the 5, and it is not a result. The test
   is procedural, not statistical: **the oracle table must be diffable against a
   table written from the module list in §3 alone.**

3. **A conversion has no constructed witness.** Per the plan's own rule, and
   because four coincidental fits are already on the record.

4. **The dimension claim does not separate from the budget claim.** If `246`/`293`
   (dimension) convert at the same rate as `80`/`422`/`248` (budget) once
   `max_size` is raised, then F5 bought nothing that a bigger search would not
   have bought, and the strongest claim in §4.1 collapses.

### 7.1 The cross-seam convergence (added 2026-08-02, after B/C/D reported)

Seam D came back a **total null** (leave-one-out 0/36, transferable contribution
**+0** — its "properties" were per-task lookup keys, i.e. the *same* contamination
failure this document was built to avoid, realised). Seam C is a **sixth content
null**. Seam B converted **1**, and hit a wall it described in its own terms:
**only 39/257 tasks even carry the signature its grammar can emit — 85% excluded
before semantics are considered at all.**

**B's 85% and this document's 79% are the same finding approached from opposite
ends,** and neither was predicted by the arc-6 plan. B measured *"the proposal
grammar cannot express the population"*; §2 here measures *"the population is
blocked by structural primitives no kernel supplies."* Both are statements that
**the MBPP residual is dominated by list/string/dict plumbing**, not by
mathematics or by hypothesis-space restriction. Four seams aimed at the
mathematical residual; the mathematical residual is **11/53 ids**.

Two consequences worth stating plainly:

1. **Seam A is now the only seam with a live positive number**, which raises the
   evidential bar on it rather than lowering it. A 5-id result is small enough
   that a single unnoticed engine mix-up, or a single per-task kernel slipping
   into the table, would account for all of it. That is exactly why §1.1 was
   worth doing properly and why the strict/verified distinction in §4 must not be
   collapsed in any summary.
2. **The highest-value target in this population is not a seam in the plan at
   all.** It is the 42-id structural class — sort, dict/tuple construction,
   string split/replace/reverse, `(index,element)` binding — reachable by an
   S4-style enumerator widening, which is the one move in this project's history
   that has actually converted at scale (S4: 0→25 ids). §3.1(b) reached the same
   conclusion from the F4 anomaly, independently.

**What a null would and would not mean.** Per the plan's registered null reading,
a null here says *the tower's/SymPy's coverage does not overlap this corpus* —
a statement about MBPP, not about the import. This measurement sharpens that:
**79% of the live-unreached population (42/53) is blocked by structural
primitives that no import can supply.** So a Seam A null would be **substantially
predetermined by the population**, and the honest framing is that Seam A was
scoped against the wrong 42 ids from the start. The corresponding positive
statement is small and specific: **on the 11 ids where mathematics is actually the
blocker, module-granularity SymPy registration reaches 5 of them, and 4 of the 11
need a *dimension* rather than a *budget*.**

---

## 8. Recommended scope for M1, if it is built

Take **F3 + F2 + F5** and nothing else: 3 modules, 229 callables, blind-registrable,
**5 ids** (`80, 246, 248, 293, 422`), of which 2 are dimension claims with prior
evidence from arc 5's own conversions.

**Do not take F1 despite it being the cheapest** — measured zero strict yield here
(its 3 hits are blocked downstream), and taking a family because it is cheap
rather than because it converts is how an import list becomes a wish list.

**Do not take F4** — its blind-registration case is weak, its yield is
non-mathematical, it carries a deprecation warning and it owns the entire
untested Value-boundary risk.

**Price the exact→rendered boundary step (§6.1) before committing**, because it
is a prerequisite for F5 — the only family carrying the strong claim — and it is
currently unpriced.

**Reproduce with:** `OZMA_NO_LLM=1 python scripts/arc6_a_ceiling.py`
(deterministic; two consecutive runs produced byte-identical output modulo the
timestamp; `id_hash=ea6c4e913f673823`).
