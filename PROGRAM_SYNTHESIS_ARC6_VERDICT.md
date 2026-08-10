# ARC 6 — THE NON-SCALAR ROW VERDICT: PRICED, NOT BUILT

**Date:** 2026-08-02
**Status:** PRICED. **NO-GO.** The candidate was applied, measured on the
full 257, and **reverted** — `seeds/program_synthesis.json` is byte-identical
to its committed form (sha256 `5302b959daf2…`, verified after revert).
**Artifact:** `results/arc6_verdict_pricing.json` (paired id lists,
constructed witnesses, three live probes, engine sha256).
**Arms:** `results/arc6_verdict_before.json` / `results/arc6_verdict_after.json`.
**Engine:** `48da7257f35d3046e9bd18952b817a51d9f7ffbc19b08f52965bc07c5c429929`
— the tier-0 engine, **identical in both arms**, and **archived out of tree**
at `~/ozma-engine-archive/_native.abi3.so.48da7257…` (prereg A1.1).

---

## 0. The one-paragraph answer

**The gain is real, large, and mostly not worth having.** Reading the
already-computed `cmp_ok` from the plain row rules is a **seed-only** change
(zero Rust, zero Python, zero `TermNode` variants) that moves the aggregate
36 → 49 and converts **four of the five known ids** with constructed
witnesses. It also **manufactures seven coincidental fits in one change** —
more than the eight caught in this project's entire history — of which
**five become passes**. And **twelve of the fifteen newly-accepted candidates
are accepted only because `list` and `tuple` are the same `Value::Tuple`**:
they do not satisfy the corpus's own `assert f(...) == [...]` under real
Python. The registered bar said *zero* false accepts from that collapse.
It is twelve. **NO-GO**, and the most useful thing this measurement
produced is the reason: the collapse is **not a property of reading
`cmp_ok`** — it is a property of the value layer, so **every** possible
non-scalar row verdict in this substrate inherits it. That is a much harder
finding than "this variant is wrong."

---

## 1. Per-bar verdict, against the bar registered before measuring

| bar (registered in advance) | verdict | evidence |
|---|---|---|
| **≥3 of the 5 known ids (`106, 161, 257, 424, 450`) convert with constructed witnesses** | **PASS — 4 of 5** (`106, 161, 257, 450`; `424` is a coincidental fit) | §3 |
| **ZERO false accepts from the list/tuple collapse** | **FAIL — 12 of 15** | §4 |
| **The 35 pass ids are preserved** | **PASS — 49 ⊃ 36 ⊃ 35, zero lost** | §5 |

**GO requires all three. NO-GO.**

---

## 2. What was priced, exactly

The candidate is the smallest possible form of the unit tier-0 §9.1 named,
and it takes the instruction "prefer making the row verdict read the
comparison that already exists" literally:

```
ps_row_pass:  Eq(Attr(r,"got"), Attr(r,"expected"))   ->  Eq(Attr(r,"cmp_ok"), 1.0)
ps_row_fail:  Not(Eq(Attr(r,"got"), Attr(r,"expected"))) -> Eq(Attr(r,"cmp_ok"), 0.0)
```

Nothing else. `eval_and_record` is untouched — `got` keeps its scalar-only
meaning; the rules stop reading it. This is exactly the comparison
`ps_row_pass_special` already makes on tol/unordered rows.

- **Files changed:** `seeds/program_synthesis.json` only. **Zero Rust, zero
  Python, zero new `TermNode` variants.**
- **Therefore the engine is identical across arms** (`48da7257…` both sides,
  verified by sha256 in both artifacts), so **A1.2's three-arm requirement
  does not apply**: there is no rebuild to separate. This was checked, not
  assumed.
- Apply/revert is scripted and idempotent: `scripts/arc6_verdict_patch.py`.
  The measured `after` arm is reproduced exactly by `apply` (seed sha256
  `ae3dfea8590a…`).
- Both arms are **twin-run identical** (`before` hash `c49a0e30…`, `after`
  hash `4b4a2e58…`), and the `before` arm reproduces `arc6_tier0_after.json`'s
  36-id pass list exactly.

**The rule fires, in both directions, verified live** (an unknown attr key is
a silent no-op here, so this had to be proven):

```
task 257 row:  got=None  got_json=[20,10]  cmp_ok=1.0  ->  ps_verdict=pass   (NEW)
task 6   row:  got=None  got_json=null     cmp_ok=0.0  ->  ps_verdict=fail, 10 CounterExamples minted
```

---

## 3. UPSIDE — paired lists, and the two numbers are very different

```
before  pass (36): 16 20 58 59 69 82 84 85 89 90 120 127 132 135 138 139 142 145 227
                   233 234 266 276 278 281 309 312 394 404 406 410 433 443 458 472 477
after   pass (49): the same 36, PLUS 106 161 249 257 272 290 393 413 418 436 450 457 460
lost pass: []      lost accepted: []      superset: TRUE
```

| quantity | paired id list | n |
|---|---|---|
| **newly accepted** | `106 161 222 249 257 272 290 393 413 418 424 436 450 457 460` | **15** |
| **newly accepted AND correct** (constructed witnesses, 18–24 probes each) | `106 161 257 272 413 436 450 460` | **8** |
| **newly accepted, COINCIDENTAL FIT** (refuted by constructed inputs) | `222 249 290 393 418 424 457` | **7** |
| **newly PASS** | `106 161 249 257 272 290 393 413 418 436 450 457 460` | **13** |
| newly pass AND correct | `106 161 257 272 413 436 450 460` | **8** |
| **newly pass but WRONG IN GENERAL** | `249 290 393 418 457` | **5** |

**Aggregate, with its caveat attached as registered.** 36/257 = 14.0 %
[10.3, 18.8] → 49/257 = 19.1 % [14.7, 24.3]. **The intervals overlap; this
is underpowered by construction and is not a detection.** The result is the
id list and the witnesses.

### 3.1 The five known ids

| id | outcome | accepted program | witness verdict |
|---|---|---|---|
| **106** | **CONVERTS** | a loop with `Eq` (not the tier-0 witness) | 24/24 constructed probes agree |
| **161** | **CONVERTS** | `[__item for __item in a if not(__item in b)]` | 24/24 |
| **257** | **CONVERTS** | `(b, a)` | 24/24 |
| **450** | **CONVERTS** | `[__item for __item in a if len(__item) == b]` | 24/24 |
| **424** | **does NOT convert** | a `range(N+1)` DP construction — **not** the published witness | 11/20; **traps `index:oob` on the held-out row**, so accepted-but-not-pass |

**A correction to tier 0, recorded rather than absorbed:** tier-0 §4 reported
that the enumerator proposes the published witness for 424. Once the row
verdict accepts non-scalars, an **earlier rung** (a DP construction) is
accepted **before** the enumerator ever runs. **Fixing the verdict changes
which rung wins, not only whether a proposal is accepted** — three of the
eight correct conversions (`106`, `272`, `413`) are likewise programs the
tier-0 trace never named.

---

## 4. DOWNSIDE — the bar that fails, and it fails structurally

### 4.1 The collapse is in the value layer, not in the comparator

`list` and `tuple` are one `Value::Tuple`. Measured live:

```
substrate node attr {"a": [1,2,3]}  reads back as  (1, 2, 3)
substrate Eq((1,2), [1,2])          = TRUE          Python (1,2)==[1,2] = FALSE
```

A row's `expected` is a **graph attribute**, so by the time any comparator
sees it, a list literal from the corpus's assert **is already a tuple**.
`_row_cmp_ok` therefore reports agreement, and so would `Eq(got, expected)`
if `got` were stored. **Storing the non-scalar `got` and keeping `Eq`
collapses identically.** There is no variant of this unit that avoids it —
only a change to `Value` would, and that is a different, much larger job.

`Set` and `Dict` are **not** collapsed (`Value::Set` / `Value::Dict` are
distinct), so the collapse can only ever equate two sequences with identical
elements and different container types. It cannot equate two different
element sequences.

### 4.2 It was never load-bearing before, and now it is, for almost everything

Measured mechanically: **of the 36 baseline passes, ZERO have a non-scalar
expected value.** The collapse has never decided an acceptance in this
project. Under the candidate:

| | paired id list | n |
|---|---|---|
| newly accepted whose accept **requires** the collapse (measured on the task's own rows) | `161 249 272 290 393 413 418 424 436 450 457 460` | **12 / 15** |
| of those, **fail the corpus's own `assert` under real Python** | the same 12 | **12** |
| newly accepted **not** needing it | `106 257` (pure tuples) and `222` | 3 |

`extract_rear(('Mers','for','Vers'))` must equal `['s','r','s']`. The
substrate returns `('s','r','s')`. In Python that assert **fails**. Twelve
of fifteen conversions are graded by a comparison the corpus does not make.
The registered bar is *zero*.

### 4.3 A second, unregistered looseness — on SCALAR rows

The comparator swap is **not** semantics-preserving even where nothing is
non-scalar. Measured live:

| pair | substrate `Eq` | Python `==` (`cmp_ok`) |
|---|---|---|
| `1, True` | True | True |
| `0, False` | True | True |
| `1, 1.0` | True | True |
| **`0.0, False`** | **False** | **True** |
| **`1.0, True`** | **False** | **True** |

**Task 222 is newly accepted entirely because of this**, not because of
non-scalar support: its revealed rows are `got=1 / expected=True` (agreed
before) and `got=0.0 / expected=False` (**refused** before, accepted now).
Its program is `len(a) / a[-1]` for a task that asks *"do all elements have
the same type?"* — it returns a `Fraction` where a bool is wanted, and
`Fraction(1,1) == True`. The bar did not name this mechanism because nobody
knew it was there; it is the third false-accept mechanism this change opens.

### 4.4 It inherits the `sorted`-on-strings defect — reproduced

Prereg §4 registers `cmp_value`'s interner-symbol-id string ordering as a
live defect and says a later build **must not quietly inherit it**. A
non-scalar row verdict newly admits list-output programs that order strings.
Reproduced live, on task 393's accepted program, input
`[["zz"],["aa","bb"],["cc","dd"]]`:

```
fresh substrate                     -> (2, ('cc','dd'))
booted substrate                    -> (2, ('cc','dd'))
booted + interner primed in reverse -> (2, ('aa','bb'))     <- DIFFERENT
reference meaning max(key=len)      ->     ['aa','bb']
```

The row verdict evaluates on the **goal's own long-lived substrate**
(`eval_and_record` → `sub._inner.evaluate`), which the seed load and the
task's own history have already primed — so this is not a synthetic
condition. **An accept can depend on interner history.** I did not fix the
defect and did not build on it; this is the report §4 asks for.

### 4.5 The coincidental fits, named

| id | accepted program | why it is wrong |
|---|---|---|
| **222** | `len(a)/a[-1]` | returns a number for a bool question; §4.3 |
| **249** | `sorted` + arithmetic | order/duplicate-sensitive; 12/24 |
| **290** | `(len(a[-1]), a[-1])` | the **last** sublist, not the longest — tier 0 predicted exactly this; 12/20 |
| **418** | a `Sum` loop | returns the last element, not the longest; 9/20 |
| **424** | a `range(N+1)` DP | 11/20, and traps on the held-out row |
| **393** | `(len(max(a)), max(a))` | **ties only** (20/21) — `cmp_value` orders tuples by length then lexicographically; the reference takes the first. §4.4 shows this one is also interner-unstable |
| **457** | a `Sum` loop | **ties only** (19/21), same tie-break divergence |

**393 and 457 are the honest edge of this list** and are called out rather
than counted silently: they diverge from the reference *only* on
length-ties, where the task statement is ambiguous. They are still counted
as fits because the reference is the grading oracle — but a reader who
disagrees should read the coincidental count as 5 substantive + 2 tie-break,
not 7 flat. **It does not change the verdict:** bar 2 fails on 12 collapse
false accepts, independently of how these two are classified.

---

## 5. REGRESSION — clean

- `after ⊇ before ⊇ arc5_final`: **49 ⊃ 36 ⊃ 35**, verified as sets.
- **`lost_pass = []`, `lost_accepted = []`.**
- Both arms twin-run identical.
- Runtime 20.8 s → 23.7 s per pass — no search-space blow-up (the change
  does not touch `SynthEnumerate`, so the `TupleOf` distinct-signature
  hazard does not apply; more tasks simply terminate on an earlier rung).

**Bar 3 passes.** It is the only bar whose failure would have been a hard
stop on its own, and it is clean.

---

## 6. WHERE ELSE `got` IS READ — question 4, answered

`got` is a graph attr. Every reader, and whether the candidate touches it:

| site | kind | affected? |
|---|---|---|
| `domains/prog_synthesis.py:784` `eval_and_record` | **WRITES** `got`, scalar-only cast — the source of the block | **NO.** The candidate leaves it alone; the rules stop reading it. `got` keeps its scalar meaning and becomes dead for the verdict. |
| `domains/prog_synthesis.py:785` `got_json` | full result, recorded, read by no rule | no — diagnostic only |
| `domains/prog_synthesis.py:794` `cmp_ok` | the comparison fact, off the RAW result | **YES** — newly load-bearing for every plain row |
| **`ps_row_pass` / `ps_row_fail`** (seed) | the row verdict | **YES** — this is the change |
| `ps_row_pass_special` / `ps_row_fail_special` (seed) | already read `cmp_ok`, scoped to tol/unordered | no — unchanged, and the candidate makes the four rules differ only by scope |
| **`ps_counterexample`** (seed) | copies `got` onto a `CounterExample` | **INDIRECTLY.** No decision changes, but a non-scalar counterexample still records `got=None`, so **CEGIS repair sees a blank** for exactly the class the change admits. Not fixed by this candidate. |
| **`ps_foldup_accept` / `ps_foldup_reject`** (seed) via **`fu_got`** (`prog_synthesis.py:2001`) | the **descent fold-up** verdict, with the **same** `Eq(fu_got, expected)` shape and the **same** scalar-only cast | **NO — AND THAT IS THE POINT.** This is a **second, independent non-scalar blindness**, on a different lane, with **no `fu_cmp_ok` fact to read**. Any claim that "the non-scalar row verdict is fixed" would be false while this stands. |
| `scripts/mbpp_arc3_battery.py:225` `agree()` | the **held-out** verdict | no — but note it is **already** list/tuple-blind (`_norm`), which is why a collapse-dependent accept still reaches `pass` |
| `prog_synthesis.py:2369` read-back | reports `CounterExample` attrs out of the goal | no — mechanical |

**The change is not local just because it looks local**: it moves the plain
row verdict onto a different comparator for *every* task, leaves a
second verdict lane (`fu_got`) blind, and leaves CEGIS repair blind for the
newly-admitted class.

---

## 7. The price, in one table

| what it buys | what it costs |
|---|---|
| 8 genuinely correct new conversions (`106 161 257 272 413 436 450 460`) | 7 new coincidental fits, 5 of them scored as passes |
| 4 of the 5 known ids, with witnesses | 12 of 15 accepts exist only under the list/tuple collapse and fail the corpus's own assert |
| zero Rust, zero Python, zero `TermNode` variants, zero regressions | acceptance semantics change for **every** task, including scalar rows (`0.0 == False`) |
| the aggregate moves 36 → 49 | the aggregate becomes **less trustworthy**, not more: 5 of the 13 new passes are wrong |
| — | the pipeline inherits the registered `sorted`-on-strings defect, reproduced |
| — | the fold-up lane (`fu_got`) stays blind — the fix would be advertised as complete and would not be |

**A measured "this costs more than it returns" is a good outcome and is what
pricing is for.** Recorded as such.

---

## 8. What a GO-able version would have to establish first

Not taken here, and deliberately not scoped — naming them is the deliverable,
not doing them:

1. **A type-faithful sequence verdict.** MBPP's asserts distinguish `list`
   from `tuple`; `Value` does not. Either the row schema carries the
   expected container type as a separate fact the verdict reads, or the
   claim "task X passes" must be restated as "passes modulo container type"
   — **explicitly, in every artifact**, because §4.2 shows it would apply to
   12 of 15 conversions and to essentially every future list-output task.
2. **Then, and only then, the row verdict.** With the container type fact
   available, `cmp_ok` (or a stored non-scalar `got`) is a small, honest
   change and the 8 correct conversions above are what it is worth.
3. **`fu_got` in the same motion**, or the fix is partial by construction.
4. **`Eq` vs Python `==` decided deliberately**, not inherited: the
   float/bool divergence (§4.3) is a semantics choice that currently differs
   between the two comparators and nobody has chosen.
5. **The string-order defect fixed on its own terms first** (prereg §4
   already says this), because §4.4 shows the non-scalar verdict is what
   makes it reachable from an accept.

---

## 9. Reproduce

```
# the two arms (each writes results/arc6_verdict_<label>.json)
OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 python scripts/arc6_verdict_battery.py before
python scripts/arc6_verdict_patch.py apply       # -> seed sha256 ae3dfea8590a...
OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 python scripts/arc6_verdict_battery.py after
python scripts/arc6_verdict_patch.py revert      # -> seed sha256 5302b959daf2... (committed)

# the artifact (re-runs every witness sweep and all three probes LIVE)
OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 python scripts/arc6_verdict_report.py
```

Any pytest invocation in this tree needs `--confcutdir=<this worktree>` and
`COLUMNS=250`; the worktree is nested inside the canonical repo, so pytest
otherwise loads the parent's `conftest.py` and every module collapses to
`ImportError`. **That is not a red.**

**Contamination.** Constructed inputs are generated mechanically from the
row schema by type-driven mutation, and every generated input equal to a
revealed **or** held-out row is discarded. `task["code"]` is executed only
as the measurement oracle, **after** both arms were already measured; it
enters no codebook, cue vocabulary or taught shape. Held-out rows entered
no detection or selection path.

**Engine.** Both arms and every probe ran on
`48da7257f35d3046e9bd18952b817a51d9f7ffbc19b08f52965bc07c5c429929`, stamped
in every artifact and **archived out of tree** — the binary is a single
gitignored file every build overwrites, and a measurement whose engine no
longer exists is not reproducible (prereg A1.1).
