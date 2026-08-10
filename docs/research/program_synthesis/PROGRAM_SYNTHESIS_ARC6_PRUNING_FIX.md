# ARC 6 — THE TWO "VALUE-LAYER REGRESSIONS" HAD **ONE** MECHANISM, AND IT WAS NEITHER OF THE TWO DIAGNOSED

**Date:** 2026-08-03
**Worktree:** `/home/matt/arc6-pruning-fix/research/experiments/gamma-substrate` (detached at `95096b6b7a`)
**Engine:** `8311d4356082acf4f70fab61a6e943d3dcecbd404d6e90c4f72ccc9486936df0` —
**UNCHANGED. No rebuild. `git diff runners/` is empty.**
**Bars:** `PROGRAM_SYNTHESIS_ARC6_PREREG.md` amendment **A6**, FX1–FX5.
**Artifacts:** `results/arc6_pruning_fix.json`,
`results/arc6_verdict_pruningfix_arm{A,B,C}.json`,
`results/arc6_pruning_fix_collapse_check.json`,
`results/arc6_full_sweep_pruningfix.json`.

---

## 0. The headline, and it is a premise correction

A6 registered two regressions with two different mechanisms and two
opposite remedies:

| case | registered mechanism | registered remedy |
|---|---|---|
| 1 — `test_tmpl_item_in_listvar_fires` (+3) | **BUDGET** — "list and tuple no longer collide, so observational-equivalence pruning is weaker"; `distinct` 1,434 → 16,148 | separate pruning-equivalence from semantic-equality |
| 2 — `test_list_map_extracts_per_element` | **GENERATION** — "never enumerated at any budget"; template-pool eligibility keyed on `spec_is_list_shaped` | restore the template pool |

**Measured, both are wrong, and the five reds are ONE mechanism:**

> **THE SPEC WIRE CANNOT CARRY THE SPEC'S TYPES.** `Substrate.evaluate()`
> serialises its Term dict through JSON (`py.rs::pyobj_to_json`), and JSON
> has exactly one array type. A Python `list` and a Python `tuple` inside a
> `Lit` therefore arrive **identically**, as `Value::Tuple`. That was
> harmless while list and tuple were one `Value`. Under the ARC6 value
> layer, `FilterList` / `MapList` correctly return a `Value::List` (a Python
> list comprehension **is** a list) — while these five specs, written
> pre-value-layer, declare **tuple**-typed expected outputs. So the search
> is asked for something no correct candidate can produce.

Everything the diagnosis observed follows from that, in the other causal
direction:

- **Case 1's "11× explosion" is an EFFECT, not a cause.** The search never
  halts (nothing can match), so it runs to its 200,000-candidate budget and
  **accumulates** 16,148 distinct behaviours on the way. Give the same
  search the type it means and it solves at **`distinct` = 1,434, `tested` =
  20,388 — the arm-A figures, to the unit.**
- **Case 2's "never enumerated" is false.** The term *is* built, evaluated
  and then correctly *rejected*, because the target it is compared against
  is a tuple. Under a list-typed target the same search reaches it as
  candidate **25** of 25 and halts `solved`. `distinct` plateaus not because
  the generator is exhausted of that term but because the whole (tiny,
  single-op) space is exhausted while nothing can ever match.
- **Both control experiments that "established" the diagnoses were run over
  the same lossy wire, so neither could have detected this.** A6 records
  that "expected-as-tuple and expected-as-list are byte-identical in both
  arms" as evidence that the target's type is *not* the cause. Measured, it
  is evidence the **instrument could not express the difference**: over a
  bare `Lit`, `output: [1,3]` and `output: (1,3)` are literally the same
  spec — identical `tested`, identical `distinct`, identical halt.
  A bug in the refuting direction is indistinguishable from an honest null.

**The value layer did not regress the search. It made five stale pins
visible** — the `§2(a)` **type-blind test assertion** class the full sweep
had *already named* ("EXPECTED, test-side"), which these five belong to and
were not filed under.

---

## 1. The measurement chain

All rows below are live invocations, engine sha in each block.

### 1.1 The wire is lossy on **both** arms (so it is not a value-layer defect)

| probe | arm A `48da7257` | arm C `8311d435` |
|---|---|---|
| `Lit` ← Python `list [1,2]` | `(1, 2)` **tuple** | `(1, 2)` **tuple** |
| `Lit` ← Python `tuple (1,2)` | `(1, 2)` tuple | `(1, 2)` tuple |
| env var ← Python `list [1,2]` | `(1, 2)` tuple | `[1, 2]` **list** |
| node attr ← Python `list [1,2]` | `(1, 2)` tuple | `[1, 2]` **list** |

The value layer made the **graph** and the **env** faithful. The `Lit`/JSON
term wire was left as-is *by design* — a bare array still means `Tuple` so
that no seed-resident `Lit` literal changes meaning — and
`domains/prog_synthesis.py::_wire` is the shipped **write side** of the
engine's own tagged form (`__list__` / `__tuple__` / `__set__` / `__fset__`,
decoded in `persist.rs`).

**Every production caller already uses it** —
`prog_synthesis.run_enumerate`, `prog_synthesis._branch_arm_term`,
`prog_moves._run_synth_enumerate` all pass `_wire_rows(...)`. **Only the
gates did not.** The defect was in the instrument, and only in the
instrument.

### 1.2 The five specs, both directions, engine `8311d435` unchanged

Bare wire = as the gates shipped. Faithful wire + list-typed expected = as
they mean.

| spec | bare wire (before) | faithful, LIST-typed (after) | faithful, TUPLE-typed (refuting) |
|---|---|---|---|
| `tmpl_item_in_listvar` | budget, `distinct` **16,148** | **solved**, tested 20,388, `distinct` **1,434** | not found |
| `tmpl_len_item_vs_var` | budget, `distinct` 12,917 | **solved**, tested 15,391, `distinct` 1,167 | not found |
| `tmpl_nested_reduction` | budget, `distinct` 22,212 | **solved**, tested 57,926, `distinct` 3,630 | not found |
| `string_as_sequence` | max_size, `distinct` 10,106 | **solved**, tested 2,020, `distinct` 140 | not found |
| `list_map_extracts_per_element` | max_size, `distinct` 54→129 | **solved**, tested **25**, `distinct` **17** | not found |

Arm A's own figures for case 1 and case 2 were `20,388 / 1,434` and
`25 / 17`. **Identical.** The search space never moved.

The winning terms, shape-verified (FX2's bar):

```
tmpl_item_in_listvar   [__item for __item in a if not((__item in b))]      FilterList,In,Not
tmpl_len_item_vs_var   [__item for __item in a if (len(__item) == b)]      FilterList,Count
tmpl_nested_reduction  [__item for __item in a if (max(__inner for __inner in __item) <= b)]
string_as_sequence     [__item[-1] for __item in a]                        MapList,IndexAt
list_map               [__item[0] for __item in lists]                     MapList,IndexAt(_,0)
```

### 1.3 The registered mechanisms, refuted individually

**"Template-pool eligibility keyed on `spec_is_list_shaped`" — REFUTED.**
Read at `synth_enumerate.rs:1888-1935`: the `IndexAt(item, 0)` template is
pushed into `map_templates_by_size[3]` **unconditionally** whenever
`map_wanted`, with no reference to `spec_is_list_shaped`. Confirmed live:
the same op set, same budget, same engine finds it in 25 candidates the
moment the target's type survives the wire.

**"Observational-equivalence pruning is weaker" — REFUTED as the cause.**
Implemented and measured the honest version of the registered remedy (a
`SigRel::{Exact, Coarse}` split: coarse — list ≡ tuple — for `seen`, exact
for `matches_target`, with the target checked *before* the pruning lookup so
the coarser relation can never hide a semantic solution). Built, installed,
measured, and **reverted**, because it is inert:

| spec | engine `8311d435` | engine with the SigRel split (`d234bd5a`) |
|---|---|---|
| case 1, bare wire | budget, `distinct` 16,148 | budget, `distinct` 15,980 (−1.0%) |
| case 1, faithful LIST wire | **solved, 20,388 / 1,434** | **solved, 20,388 / 1,434** (identical) |
| case 2, faithful LIST wire | **solved, 25 / 17** | **solved, 25 / 17** (identical) |
| four other specs, faithful | identical | identical but one (`2,439` → `2,438`) |

A ~1% pruning gain on searches that are unsatisfiable by construction, and
**zero** effect on any search that solves. The engine change was not needed
to clear any bar, so it was not shipped: **`git diff runners/` is empty and
the binary is byte-identical to the baseline.** The patch is preserved
verbatim at `drafts/arc6_sigrel_pruning_split.patch` if the orchestrator
wants the architecture separated on its own merits — but it should then be
priced as architecture, not as this fix. The binary it produced
(`d234bd5a7209…`) is archived out of tree per A1.1 as
`~/ozma-engine-archive/_native.abi3.so.MEASURED_NOT_SHIPPED_d234bd5a…`.

---

## 2. The fix

**Two test files. Zero Rust, zero `domains/`, zero `seeds/`, zero engine.**

- `tests/test_arc6_tier0_migrated.py` — `synth()` now delivers its spec via
  `domains.prog_synthesis._wire_rows` (the shipped write side), and six
  specs are **re-pinned to the type they actually mean**: the four A6 cases
  plus `op:ConcatList` and `op:ArgMaxLenOver`, whose expected outputs were
  tuples while their own *inputs* were lists (`Argmax` returns an element of
  `a`; `a`'s elements are lists). Three new gates pin the mechanism: the
  list-typed spec is SOLVED, the tuple-typed spec is REFUSED, and the bare
  `Lit` wire is shown to be the lossy thing.
- `tests/test_synth_enumerate_migrated.py` — `rows()` delivers via
  `_wire_rows`; `test_list_map_extracts_per_element` now asserts the winning
  term's **shape** (`MapList` over `IndexAt(_, 0)` over `Var(lists)`), not
  merely `found`; and a new `test_tuple_typed_variant_of_the_map_spec_is_refused`
  pins the refuting direction.

**These re-pins are STRICTER, not wider.** Before, a list-declared spec and
a tuple-declared spec were the same spec; the gates could not have detected
a re-collapse. Now each one is paired with its refutation, so if a later
change re-merges list and tuple in the spec-target relation, the suite goes
red.

---

## 3. FX1–FX5

### FX1 — case 1 solves again, `distinct` back near 1,434 · **PASS**

`solved`, `halt_reason == "solved"`, **`distinct` = 1,434** — not "near",
**exactly** arm A's figure, with `tested` = 20,388 also identical. Pinned in
`test_tmpl_item_in_listvar_fires`. The other three case-1 gates solve at
1,167 / 3,630 / 140.

### FX2 — case 2 finds the CORRECT term · **PASS**

`MapList{source: Var(lists), var_name: __item, value: IndexAt{seq: Var(__item),
index: Lit 0}}`, asserted field by field, not by `found`. `tested` = 25,
`distinct` = 17 — arm A's figures.

### FX3 — THE TRAP · **PASS on the registered mechanism reading; unchanged on the literal reading**

**Not applicable in the direction feared, and verified anyway.** The trap
was that fixing case 1 by collapsing list and tuple in pruning would
silently undo the value layer. The fix shipped touches **no comparison at
all** — no Rust, no seed, no adapter — so there is nothing to undo. Measured
rather than argued:

- `accept_requires_list_tuple_collapse` = **`[]`**, measured live with the
  shipped instrument (`arc6_verdict_report.sweep`) over this arm's own
  accepted IRs for the full 14-id cohort (HV1's twelve ∪ HV2's eight ∪ the
  13 newly-accepted). `results/arc6_pruning_fix_collapse_check.json`.
- Each of the **12 named collapse-accepts is REJECTED under that reading** —
  every one measures `accept_requires_list_tuple_collapse: False`, with
  `n_typed_agree == n_norm_agree` on 18–24 constructed probes.
- **Literal reading, reported not substituted:** all 12 remain in
  `accepted_ids`, exactly as at the baseline. That is the state the value
  layer itself recorded and explained (commit `9611ed98`: HV1-literal and
  HV2 are jointly unsatisfiable, because 6 of HV2's 8 ids *are* 6 of the
  12). **This rung moved it by zero**: arm C's `per_task` is
  **byte-identical** to arm B's.
- The separation is *pinned* rather than merely preserved: the two new
  refuting gates fail if list and tuple are ever re-merged in the
  spec-target relation.

### FX4 — no regression · **PASS**

| | arm A `48da7257` | arm B `8311d435`, baseline code | arm C `8311d435`, this fix |
|---|---|---|---|
| pass ids | 26 | **48** | **48** |
| accepted ids | 46 | 95 | 95 |
| outcome hash | `00e7e30d…` | `aa889608…` | `aa889608…` |
| determinism (2 runs) | identical | identical | identical |

`lost_pass = []`, `lost_accepted = []`, `C − B = ∅` (per-task byte-identical).
`test_arc6_valuelayer_migrated` **35/35** and `test_goal_residual_migrated`
**31/31** green (66 passed together).

**On A1.2.** The final engine **is** the baseline engine — no rebuild, sha
verified equal — so `B − A` as A1.2 words it is empty *by binary identity*
rather than by measurement, which is a weaker fact than the prereg wants.
Substituted a stronger control: arm A above runs the **same code** on the
**pre-value-layer binary** and moves 22 ids (`B − A` = 69 90 120 132 145 161
249 272 278 290 393 394 410 413 418 433 436 443 450 457 460 472). **The
instrument is demonstrably engine-sensitive**, so `C − B = ∅` is a live null
and not a dead instrument.

### FX5 — the sweep does not worsen · **PASS** · *detail in §4*

Red **nodes 162 → 153**, red **files 88 → 87**, non-green files 100 → 98.
**13 fixed, 4 new, all four classified, unexplained bucket EMPTY.**

---

## 4. The paired sweep

946/947 files, `scripts/arc6_valuelayer_sweep.py` (the `--confcutdir`
instrument, **not** `failure_baseline_sweep.py`), 6 workers, 420 s per-file
timeout — the baseline's own settings. Engine sha **identical** across both
arms (`8311d435…`). Baseline: the frozen `results/arc6_full_sweep_armC.json`.
This arm: `results/arc6_full_sweep_pruningfix.json`.

**On the baseline's own counts.** A6 quotes *145 nodes / 100 files*.
Recounted from the artifact itself: **100 non-green files** (88 `RED` + 10
`NOT_ESTABLISHED` + 2 `NONZERO_NO_NODES`) and **162 reported nodes across 88
`RED` files**. Both countings are recorded; the diff below is on **node
ids**, which is unambiguous under either.

| | baseline arm C | this arm | Δ |
|---|---|---|---|
| red nodes | **162** | **153** | **−9** |
| red files | 88 | 87 | −1 |
| non-green files | 100 | 98 | −2 |
| GREEN files | 846 | 849 | +3 |

The file sets differ by exactly one: `tests/test_goal_residual_migrated.py`
post-dates the baseline sweep. It is **GREEN** here (31/31).

### 4.1 The 13 fixed nodes

- **The five A6 targets** — the four `test_arc6_tier0_migrated` template
  gates and `test_synth_enumerate_migrated::test_list_map_extracts_per_element`.
- **Eight NOT credited to this fix** (`test_run67_migrated` ×3,
  `test_run82_migrated` ×3, `test_varcomp_migrated` ×2) — they were red in
  the baseline sweep only because the gitignored `results/run*_checkpoints`
  were absent; this run symlinks them in per the run instructions.
  Environmental. Recorded so the −9 is not read as −9 of mine.

### 4.2 The 4 new reds, each classified — **unexplained bucket empty**

1. **`test_engine_provenance_migrated::test_loaded_engine_is_a_build_of_THIS_TREES_rust_source`
   — MY OWN ARTIFACT. Fixed and re-verified.** `runners/dsl/target/release/`
   still held the *measured-not-shipped* `SigRel` build (`d234bd5a…`) while
   the installed `.so` was the shipped `8311d435…`, so the tree's binary did
   not match its own release build. Rebuilt from the reverted source: it
   reproduces **`8311d4356082…` byte-for-byte**. The build is deterministic
   — which incidentally establishes an A1.1 fact worth keeping: **HEAD's
   Rust source is exactly the source of the archived baseline binary.** File
   re-run: **7/7 green.** *(This red is in the sweep artifact because the
   sweep ran before the rebuild; it is reported as measured, then fixed.)*
2. **`test_arc5_widest_gap_migrated::test_determinism_fresh_reproduces` —
   PRE-EXISTING, PRESENT IN BOTH ARMS.** Reds identically in the **pristine
   baseline worktree** (`/home/matt/arc6-baseline`, baseline code, same
   engine). Its twin-run half *passes* (`h1 == h2`); what fails is
   reproducing the **committed artifact hash**, and the live hash differs
   per worktree — this arm `63a5c986…`, baseline arm `800a5e52…`, artifact
   `07043d75…`. A worktree-portability defect of that pin, not a regression.
   Not absorbed, not re-pinned.
3. **`test_browse_authoring::test_browse_gate_end_to_end` — FLAKY.** Green
   on immediate re-run in the same worktree (4/4).
4. **`test_run79_migrated::test_build_prep_reports_k_writer_counts_decreasing_in_k`
   — ENVIRONMENTAL.** `JSONDecodeError` at char 5,412,292 of a large
   artifact under the **symlinked shared `data/`**, which the other live
   session writes concurrently. Green on re-run (17/17).

---

## 5. What remains unfixed, named

- **The `Lit`/JSON term wire is still lossy by default.** A bare array means
  `Tuple`; only the tagged form carries the distinction. This is the same
  boundary family as the already-named-and-unfixed `inputs_json` (a tuple
  *argument* arrives as a list) and "bare JSON array → Tuple". **Not fixed
  here** — it changes what every program sees, which is exactly why the
  value-layer rung declined the symmetric fix. What *is* fixed is that the
  callers who need the distinction now all use the shipped tagged form; the
  gates were the last holdout.
- **A test that writes a bare `Lit` list still silently means tuple.** There
  is no lint or gate that catches a *future* spec written that way. The new
  `test_the_bare_lit_wire_is_the_thing_that_was_lossy` documents the trap but
  does not prevent it.
- **`SynthEnumerate`'s pruning relation is still the semantic relation.**
  Priced above at ~1% on unsatisfiable searches; the `SigRel` patch exists
  and is measured, and is deliberately **not** shipped inside this fix.
- **The constructed-witness sweep (`arc6_verdict_report.sweep`) crashes on
  scalar-argument tasks** (`_variants` assumes subscriptable elements), which
  is why FX3's cohort is the shipped 14 rather than all 95 accepts.
  Pre-existing instrument limit, recorded not absorbed.
- Known-unfixed and untouched, as instructed: `sorted`-on-strings,
  `Eq(0.0, False)`, `inputs_json`.

---

## 6. What made me want to exceed scope, and did not

1. **Fixing the `Lit` wire globally** (Python `list` → `Value::List` inside
   `Lit`, via a tagged `pyobj_to_json`). It is the *root* cause of all five
   reds and would delete a whole class of future ones. Not taken: it changes
   the meaning of every `Lit` array in every seed and every test — the same
   blast radius the value-layer rung refused for `inputs_json`.
2. **Shipping the `SigRel` split.** Implemented and measured; inert. Left
   out on the "the premise is refuted, so do not ship the remedy" rule.
3. **Auditing the whole tree for other type-blind specs.** The sweep is the
   instrument for that and §4 reports what it found; I did not go looking
   beyond it.
