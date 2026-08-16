# Ceiling reassessment 6 — the bundled `DICT_DEFAULT_OPS` widening +
   `max_size`/`max_candidates` raise `DICTFROMPAIRS`/`MAX_SIZE_SEAM_PRICING`
   both named but declined to build alone — PREREG

**Date:** 2026-08-16/17. Base `main @ aed1d12` ("Build hate attribution:
outward attribution-locus residual + stability gate"), verified fresh via
`git log --oneline -1 main` before creating the worktree. Worktree:
`/home/matt/ozmadev/ocelot-worktrees/progsyn-ceiling-reassessment-6`, branch
`progsyn-ceiling-reassessment-6`.

**Headline finding, stated up front: a single, zero-new-`TermNode`,
three-part BUNDLED fix — (1) widen `DICT_DEFAULT_OPS` with the
already-shipped `DictItems`/`FilterList`, (2) raise `run_enumerate`'s
hardcoded `max_size` from 9 to 20 (Python, a bare-literal change, not a new
decision), (3) a `ZIP_MAX_CANDIDATES`-shaped scoped `max_candidates` raise
gated on the resolved op-list containing both `DictItems` and `FilterList`
— converts tasks 277 ("filter a dict by value ≥ n") and 465 ("drop empty
items from a dict"), the exact witness pair
`PROGRAM_SYNTHESIS_DICTFROMPAIRS_PREREG.md`/`_RESULTS.md` named and
`PROGRAM_SYNTHESIS_MAX_SIZE_SEAM_PRICING_PREREG.md` explicitly declined to
convert because each rung, taken ALONE, is real but insufficient — this
rung is the "future rung that reconsiders BOTH together, bundled" that
`MAX_SIZE_SEAM_PRICING_PREREG.md §6` item 1 named and explicitly left
unbuilt. All three parts were re-verified live against the CURRENT corpus
before building anything, and a mid-build surprise (the Rust-internal
typed-default op selection explores a genuinely larger space than an
explicit hand-typed `ops` list of the same names — see §5) required a
third component (the `max_candidates` scoped raise) that neither
predecessor document's own probes exposed, because both probed with an
EXPLICIT `ops` list rather than letting the real pipeline's typed-default
selection run.**

---

## 0. Method — this is the 6th reassessment in the chain

Read in full, as instructed: `PROGRAM_SYNTHESIS_CEILING_REASSESSMENT_5_
PREREG/RESULTS.md` (the immediate predecessor — `tmpl:item_mod_eq`, +2/+2/+2
on tasks 412/426), `PROGRAM_SYNTHESIS_ZIP_ELEMENTWISE_PREREG/RESULTS.md` +
`_ZIPWITH_FOLLOWON_PREREG/RESULTS.md` (the 8-task `ZipWith` cluster, the
precedent for the `ZIP_MAX_CANDIDATES` scoped-raise mechanism this rung
reuses), `PROGRAM_SYNTHESIS_META_SKILL_ASSESSMENT_PREREG.md` (the standing
architectural finding — most residuals are category-(a) missing-primitive
gaps or category-(c) something-else, not meta-skill-shaped; not
re-litigated here), and the three already-NO-GO'd survey documents
(`HOLDOUT_FAIL_SURVEY`, `STRUCTURAL_REJECT_SURVEY`, `BUDGET_EXHAUSTED_
SURVEY`) — not re-surveyed wholesale, per the task brief's own instruction.

This rung additionally read `PROGRAM_SYNTHESIS_DICTFROMPAIRS_PREREG/
RESULTS.md` and `PROGRAM_SYNTHESIS_MAX_SIZE_SEAM_PRICING_PREREG.md` in full
— both directly relevant to the cluster this rung targets, and both
explicitly named (but declined to build) the bundled fix this rung builds.

## 1. Real baseline, confirmed live

`OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 python3
scripts/mbpp_endgame_battery.py`, run fresh in this worktree on the
unmodified build (gitignored fixtures copied from the canonical tree's
`results/` first, per every predecessor rung's own documented
prerequisite):

```
full:              86/257  p=0.33463   ci=[0.279751, 0.394381]  det_identical=True
content_stripped:  85/257  p=0.330739  ci=[0.276082, 0.390382]  det_identical=True
official:         111/257  p=0.431907  ci=[0.372789, 0.49303]   det_identical=True
```

`head` in the resulting `results/mbpp_endgame.json` reads
`aed1d12f9782217a80c7345a01848703d28eed1c`, byte-identical to `git log
--oneline -1 main` — matching the task brief's own cited baseline
(86/85/111) exactly. Saved as `results/mbpp_endgame_BEFORE_this_rung.json`.

## 2. Failure-cause population, re-derived (not assumed)

`scripts/ceiling3_diag_sweep.py` (unmodified on `main`, reused verbatim),
run against this baseline before any code change — **171 rows** (257−86,
NOT the task brief's own back-of-envelope "173−10=163" — the brief's
arithmetic used 173 as the pre-reassessment-5 failing count and 10 as the
combined ZipWith-followon+reassessment-5 conversion, but reassessment-5
converted only 2 tasks (412/426) on top of ZipWith-followon's 8, i.e.
76→84→86 passing, 181→173→171 failing — 171 is the correct, directly
re-derived figure, confirmed exactly against 257−86):

| outcome | n |
|---|---|
| `gapped:enumerate_failed` | **69** |
| `accepted_holdout_fail` | **60** |
| `gapped:property_verdict_reject` | **17** |
| `gapped:structural_verdict_reject` | **14** |
| `gapped:exhausted` | **5** |
| `gapped:no_shape` | **3** |
| `not_recognized` | **1** |
| `runner_exception:ValueError` | **1** |
| `runner_exception:TypeError` | **1** |

**Reconciles exactly against `PROGRAM_SYNTHESIS_CEILING_REASSESSMENT_5_
RESULTS.md`'s own pre-build sweep** (measured at the 84/257 baseline):
every bucket is byte-identical except `enumerate_failed`, which shrank by
exactly 2 (71→69) — matching reassessment-5's own +2 conversion (412/426,
both `enumerate_failed` before converting). Population is stable,
well-understood, no bucket churned unexpectedly.

`gapped:enumerate_failed` (69) splits the same way every prior rung has
split it:

```
budget-exhausted (tested == 200,000 exactly): 60
saturated (tested < 200,000):                  9
```

Saturated task ids: `97, 117, 277, 299, 305, 417, 462, 465, 470` — down
from reassessment-5's own 13 (`97, 117, 277, 299, 305, 308, 391, 408, 412,
417, 462, 465, 470`): `412` converted (reassessment-5); `308, 391, 408`
moved from "saturated <200,000" into the budget-exhausted bucket at their
own `ZIP_MAX_CANDIDATES=300,000` ceiling (unchanged mechanism, just a
bucket-boundary artifact of this script's own `<200,000` split test, not a
real population change).

## 3. The target — reading every saturated task's ground-truth code,
   looking for a NEW ≥2-witness cluster

Read `tests/fixtures/mbpp/sanitized-mbpp.json`'s `code` field for all 9
saturated tasks directly (not inferred from the prompt alone):

```
97:  frequency of each element in a flattened list of lists -> dict           (flatten + count, GroupCount-adjacent but needs flatten first)
117: convert all possible convertible elements in a list of lists to floats  (per-element try/except coercion — named residual #15 in META_SKILL_ASSESSMENT, single witness)
277: filter a dict by value >= n                                            (dict-comprehension FILTER)
299: max aggregate from list of tuples (groupby + argmax)                    (named residual #15, single witness, already surveyed)
305: return two words starting with 'p' (regex)                             (unrelated — regex match, no clean primitive path)
417: find common first element in list of tuples (groupby)                  (unrelated — groupby-merge, no live witness partner)
462: all possible combinations of elements (powerset, recursive)            (unrelated — no live witness partner)
465: drop empty (None) items from a dict                                    (dict-comprehension FILTER — SAME shape as 277)
470: pairwise addition of neighbouring tuple elements                       (zip(t, t[1:]) — a self-zip-with-offset, NOT reachable by `ZipWith`'s own two-DISTINCT-var gate; single witness, named not built)
```

**277 and 465 share one exact root cause**: both ground-truth solutions are
a dict comprehension with a filter predicate over `.items()`:
`{k:v for (k,v) in d.items() if PRED(v)}`. Confirmed this is the ONLY
shared pattern in the currently-failing population by a direct scan (not
sampled) of every failing task's `code` field for `.items()` + `if`:

```python
cands = [tid for tid in failing_ids
         if '.items()' in byid[tid]['code'] and 'if' in byid[tid]['code']]
# -> [277, 465], exactly, no third witness
```

**This is exactly the pair `DICTFROMPAIRS_PREREG.md §1` already named and
targeted, using the same `Fold(FilterList(DictItems(...), item,
predicate))` composition its own §3 already live-verified zero-new-`Term`**
— this rung does not discover a new cluster; it re-derives the SAME cluster
two predecessor documents already diagnosed and priced two SEPARATE,
individually-insufficient halves of, and finishes the job by bundling both
halves together plus one additional piece neither predecessor measured
(§5).

## 4. What the two predecessor documents already established, and where
   each stopped

**`DICTFROMPAIRS_PREREG/RESULTS.md`** (base `main @ 27db12b`, well before
this rung): built `DictFromPairs` (zero new `TermNode`, a `Fold`/`MkDict`/
`DictMerge` composition) and added it alone to `DICT_DEFAULT_OPS`.
Deliberately did NOT add `DictItems`/`FilterList` to the same bucket,
believing (§5 of the PREREG) that `filter_templates_by_size` has no
"project a fixed index out of the bound item" template shape, so raw
search could never reach `dict_filter`/`drop_empty` even with those two ops
present — pricing the addition as pure regression risk with "no realistic
raw-search benefit." **The RESULTS document's own §1 corrected this belief
LIVE, in the same rung**: forcing the full 7-op set
(`DictItems,FilterList,DictFromPairs,Eq,IfThenElse,GroupCount,DictMerge`)
via a direct `SynthEnumerate` call found BOTH targets, using the
ALREADY-EXISTING `tmpl:nested_reduction` template (`MinOver`/`MaxOver`) —
not the index-projection shape the PREREG predicted was needed. `item` is a
`(key: Str, value: Int)` pair, and a min/max reduction over a heterogeneous
pair reliably selects the Int element under this engine's own `cmp_value`
ordering (Int sorts below Str). **The RESULTS document then found the
SHIPPED pipeline still doesn't convert either task, for two SEPARATE,
jointly-necessary reasons, neither of which its own single-variable scope
was set up to fix**: (a) `DICT_DEFAULT_OPS` (as shipped) still excludes
`DictItems`/`FilterList` — the forced-op finding was never actually
applied to the real op-table constant; (b) `run_enumerate`'s hardcoded
`max_size: 9` is far below the ~19-20 the winning candidate needs.

**`MAX_SIZE_SEAM_PRICING_PREREG.md`** (base `main @ a3a9d4b`, one rung
later, investigation-only): priced factor (b) ALONE, honouring
single-variable-rung discipline. Found: raising `max_size` globally 9→20
is SAFE (+2.1% wall-clock, ZERO outcome drift across all 257 tasks × 3
arms, measured exhaustively) but, taken alone, converts **ZERO** MBPP
tasks anywhere in the corpus — because `DICT_DEFAULT_OPS`'s CURRENT 5-op
inventory `halt_reason: 'saturated'`s on both target specs **independent
of `max_size`** (§2.2: byte-identical `tested`/`distinct`/`halt_reason` at
every `max_size` from 9 to 25) — the search has already concluded there is
nothing more to find with 5 ops, at any size. **§6 item 1 of that document
names, explicitly, the exact bundled fix this rung builds**: *"Whether
widening `DICT_DEFAULT_OPS`... together [with max_size]... a FUTURE rung
that reconsiders BOTH together, bundled, is a real, un-costed candidate
this document explicitly declines to build."*

**This rung is that future rung.**

## 5. Re-verified fresh, this worktree, before any code change — including
   a mid-diagnosis surprise neither predecessor document's own probe
   exposed

### 5.1 Hand-composed term, real fixture rows (not made-up data)

Both tasks' REAL revealed+held-out rows (`domains.mbpp_spec.parse_asserts`
+ `split_rows`, `protocol="primary"`), both string-keyed dicts (no
`MkDict`-Str-key-only edge case — confirmed directly, ruled out as a
concern for THIS witness pair; a made-up int-keyed probe during this
rung's own early exploration DID hit `MkDict`'s documented Str-key-only
restriction, but the REAL task 277 test data never exercises it):

```
task 277: Fold(FilterList(DictItems(a), item, Gte(MinOver(item,inner,inner), b)), init=MkDict([]), body=DictMerge(acc, MkDict([item[0],item[1]])))
  a={'Cierra Vega':175,'Alden Cantrell':180,'Kierra Gentry':165,'Pierre Cox':190}, b=170 -> {'Cierra Vega':175,'Alden Cantrell':180,'Pierre Cox':190}  == expected (revealed)
  same a, b=180 -> {'Alden Cantrell':180,'Pierre Cox':190}  == expected (revealed)
  same a, b=190 -> {'Pierre Cox':190}  == expected (HELD-OUT)

task 465: Fold(FilterList(DictItems(a), item, Gt(MinOver(item,inner,inner), 0)), init=MkDict([]), body=DictMerge(acc, MkDict([item[0],item[1]])))
  a={'c1':'Red','c2':'Green','c3':None} -> {'c1':'Red','c2':'Green'}  == expected (revealed)
  a={'c1':'Red','c2':None,'c3':None} -> {'c1':'Red'}  == expected (revealed)
  a={'c1':None,'c2':'Green','c3':None} -> {'c2':'Green'}  == expected (HELD-OUT)
```

6/6 exact matches, including both held-out rows, `substrate_rs.Substrate()
._inner.evaluate()` on hand-built term-JSON. Minimum `max_size` for the
FORCED 7-op set to find this composition, real rows, swept directly:
**19** (both tasks; `max_size` 9-18 all `found:False,halt:max_size`; 19-20
both `found:True`, tested 158,703 / 68,694, well under the default 200,000
candidate budget).

### 5.2 The surprise: the Rust-internal typed-default selection explores a
   LARGER space than the SAME 7 op names passed explicitly

Neither `DICTFROMPAIRS_RESULTS.md §1` nor this rung's own §5.1 probe ever
let the real pipeline pick its own typed-default op list — both forced
`ops` explicitly. Live-verified in this rung, SAME rows, SAME `max_size`,
SAME `max_candidates`, the ONLY variable toggled is whether `ops` is passed
explicitly or omitted (letting Rust's own `spec_output_is_dictlike` branch
select `DICT_DEFAULT_OPS.to_vec()` internally):

```
explicit ops=[DictItems,FilterList,DictFromPairs,Eq,IfThenElse,GroupCount,DictMerge]:
  found=True,  tested=158,703, distinct=868,  halt=solved
omitted (Rust typed-default selection, evidence flags confirm it selects the SAME 7 names):
  found=False, tested=200,000, distinct=987,  halt=budget
```

Read `synth_enumerate.rs`'s own evidence-flag computation directly (not
inferred): `spec_is_list_shaped` is FALSE (no var/output is List/Tuple/
Set/FrozenSet-shaped — `a` is Dict, `b` is Int, output is Dict);
`spec_output_is_dictlike` is TRUE (`outputs.iter().all(is_dict_val)`); the
branch taken is `else if spec_output_is_dictlike { DICT_DEFAULT_OPS.to_vec()
}`, which returns EXACTLY the 7 names above, unextended by any further
evidence gate in this branch. **The op NAMES are provably identical between
the two runs; the `distinct` count differs (868 vs 987) anyway** — this is
not yet fully root-caused to a specific mechanism (candidate-signature
dedup order, some other internal state difference between an
externally-supplied vs internally-derived `Lit` op list — not resolved
here), but it is REPRODUCIBLE (confirmed twice, byte-identical both times)
and DIRECTLY MEASURED against the real pipeline's own actual behaviour
(§6.1's own debug-print trace confirmed the real `run_enumerate` spec omits
`ops` entirely for both tasks, exactly mirroring the "omitted" condition
above) — so it is the number this rung designs against, not the smaller
number either predecessor document's own explicit-`ops` probe reported.

**Consequence: `max_size` raised to 20 alone (matching `MAX_SIZE_SEAM_
PRICING`'s own already-measured-safe value) is NOT sufficient for task 277
under the REAL pipeline's own typed-default selection — it needs
~204,522 candidates tested (2 revealed rows) to ~264,789 (3 revealed rows,
`official` protocol), both over the 200,000 default.** Task 465 converges
under the default 200,000 budget in both protocols (measured: 68,694-
83,069 tested) — only 277 needs the extra `max_candidates` headroom.

### 5.3 Task 87 — the bucket's one live canary, re-verified unaffected

Task 87 (`merge_dictionaries_three`) is the ONLY currently-passing task
routing to `DICT_DEFAULT_OPS` (confirmed by the same
`spec_output_is_dictlike`-and-not-`spec_is_list_shaped` population check
`DICTFROMPAIRS_PREREG.md §2` already ran, re-confirmed present and
unchanged on the current corpus). Its own accepted solution
(`DictMerge(Var(b), DictMerge(Var(c), Var(a)))`, size 5, found via the
SAME typed-default bucket) is unaffected by widening the op list with
`DictItems`/`FilterList` — the search is size-ordered and short-circuits on
the first solved candidate, and neither new op composes any smaller
dict-merge-shaped alternative. Re-verified live post-build (§ RESULTS).

## 6. The bundled fix, as designed (built and measured in the paired
   RESULTS document)

Three parts, all reusing already-proven mechanisms — no new design
primitive, no new `TermNode`:

1. **`DICT_DEFAULT_OPS` widened** (`runners/dsl/src/synth_enumerate.rs`,
   the constant array): append `"DictItems"`, `"FilterList"` — both
   already-shipped, already-registered ops (`OpKind::Unary` /
   `OpKind::ListFilter` respectively). Same class of edit as every prior
   `*_DEFAULT_OPS` widening in this arc (`SET_DEFAULT_OPS`'s own
   precedent, cited by `DICTFROMPAIRS_PREREG.md §4` itself).
2. **`run_enumerate`'s `max_size` raised 9→20** (`domains/prog_synthesis.py`,
   ONE bare-literal change, matching `MAX_SIZE_SEAM_PRICING_PREREG.md §4`'s
   own already-measured-safe value exactly — reusing a proven number rather
   than inventing a new one). A bare constant change is NOT a new
   CLAUDE.md-forbidden Python decision (no new `if`/`else` over graph
   state is added) — `MAX_SIZE_SEAM_PRICING_PREREG.md §3` itself draws this
   exact distinction when explaining why a CONDITIONAL Python gate would
   violate CLAUDE.md but says nothing against the unconditional literal
   the module already carries.
3. **A new, `ZIP_MAX_CANDIDATES`-shaped scoped `max_candidates` raise**
   (`DICT_FILTER_MAX_CANDIDATES: u64 = 300_000`, same file): applied ONLY
   when the resolved `op_list` for the call contains BOTH `DictItems` AND
   `FilterList` AND the caller passed `max_candidates <= 0` (asking for the
   engine's own default — never overriding an explicit caller-supplied
   budget). Value chosen to match `ZIP_MAX_CANDIDATES`'s own already-proven
   300,000 rather than a freshly-invented number, and confirmed (§5.2) to
   clear BOTH the `full`/`content_stripped` ceiling (204,522) and the
   `official` ceiling (264,789) with real headroom.

## 7. Regression risk, priced before building

- **Population**: exactly 3 tasks route to `DICT_DEFAULT_OPS` on the
  current corpus — 1 passing canary (87), 2 target failures (277, 465).
  Confirmed by direct set computation, not assumed.
- **`DictItems`/`FilterList` widening**: `OpKind::Unary` / `OpKind::
  ListFilter`, the cheapest registration classes this search loop has
  (never `O(n²)` pairing). Task 87's own solution needs neither op and is
  size-ordered ahead of anything either new op could plausibly compose for
  a 3-Dict-variable, no-list-anywhere spec.
- **`max_size` 9→20**: already measured GLOBALLY safe across the ENTIRE
  257-task corpus, all 3 arms, by `MAX_SIZE_SEAM_PRICING_PREREG.md §4`
  (zero outcome drift on any of 771 row×arm comparisons) — re-confirmed
  fresh in THIS worktree, Python-only (no rebuild), before touching Rust
  at all (§ RESULTS §1).
- **`DICT_FILTER_MAX_CANDIDATES`**: gated on a two-op-name conjunction that
  currently only `DICT_DEFAULT_OPS` can ever produce (no other
  typed-default bucket offers both `DictItems` and `FilterList` together)
  — the gate's blast radius is provably the SAME 3-task population as the
  op-list widening itself, not the whole corpus, mirroring `ZIP_MAX_
  CANDIDATES`'s own scoping argument exactly.
- **Full population regression**: the authoritative check is the paired
  MBPP battery's own exact task-id-set diff, all 3 arms, run in the RESULTS
  document — not sampled, not assumed from the above architectural
  argument alone.

## 8. The plan

Build all three parts together (a genuinely bundled, two-variable-plus-one
change, explicitly sanctioned by `MAX_SIZE_SEAM_PRICING_PREREG.md §6`'s own
naming of exactly this combination as the correct next step). Rebuild from
source, run the full paired MBPP battery (exact task-id set diff against
the 86/85/111 baseline), run the Rust suite (778/778 expected — no new
Rust tests, this rung touches only op-table/search-loop registration
code), run the named 9-file Python regression suite (3 known pre-existing
pin-drift failures expected), run `test_retrieval_migrated.py` and
`test_reject_informs_repair_migrated.py` (retrieval-adjacent machinery
touched) WITHOUT editing either file (per the task brief's own collision
note — a sibling agent owns `tests/test_retrieval_migrated.py` this
session), then write the RESULTS document.

**What this rung does NOT attempt**: task 470 (self-zip-with-offset,
`zip(t, t[1:])`, not reachable by `ZipWith`'s two-DISTINCT-var gate, single
witness); tasks 97/117/299/305/417/462 (each a distinct, single-witness
shape, several already named/surveyed elsewhere — 117/299 as residual #15
in `META_SKILL_ASSESSMENT_PREREG.md`); the `accepted_holdout_fail`/
`*_verdict_reject` population (91 tasks, already NO-GO'd); the `gapped:
no_shape`/`gapped:exhausted` buckets (8 tasks, no shared pattern found in
this rung's own look); root-causing §5.2's explicit-vs-typed-default
search-space discrepancy to its exact internal mechanism (named, not
chased further — the number that matters for THIS rung's own design is the
REAL pipeline's own measured behaviour, which was used throughout).

## What this document does NOT establish

1. §5.2's exact root cause (why an internally-selected op list of the
   SAME names explores a different candidate count than an externally
   supplied one) — reproduced and measured, not explained to the
   instruction level.
2. Whether `DICT_FILTER_MAX_CANDIDATES=300,000`'s margin is the tightest
   correct value — chosen to match `ZIP_MAX_CANDIDATES`'s own already-
   proven number rather than independently tuned to the minimum.
3. Whether any OTHER currently-failing task (beyond 277/465) newly reaches
   `DICT_DEFAULT_OPS` and is affected — the full battery (RESULTS) is the
   population-wide, unsampled check.
4. Tasks 97/117/299/305/417/462/470 — each named, none built, matching
   this arc's own single-variable/single-cluster-per-rung discipline.
5. Whether any of this reflects real human program-synthesis cognition
   remains exactly as open as every prior document in this arc left it.

## Reproduce

```bash
cd /home/matt/ozmadev/ocelot-worktrees/progsyn-ceiling-reassessment-6
git log --oneline -1   # on top of main @ aed1d12, verify fresh
PYTHONPATH="runners/dsl/python:.:scripts" OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 \
  python3 scripts/mbpp_endgame_battery.py
PYTHONPATH="runners/dsl/python:.:scripts" OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 \
  python3 scripts/ceiling3_diag_sweep.py
```

The explicit-vs-typed-default discrepancy (§5.2), no code change needed
(pre-build engine):
```bash
PYTHONPATH="runners/dsl/python:." python3 -c "
import substrate_rs as srs
rows = [{'inputs': {'a': {'Alden Cantrell': 180, 'Cierra Vega': 175, 'Kierra Gentry': 165, 'Pierre Cox': 190}, 'b': 170}, 'output': {'Alden Cantrell': 180, 'Cierra Vega': 175, 'Pierre Cox': 190}}, {'inputs': {'a': {'Alden Cantrell': 180, 'Cierra Vega': 175, 'Kierra Gentry': 165, 'Pierre Cox': 190}, 'b': 180}, 'output': {'Alden Cantrell': 180, 'Pierre Cox': 190}}]
ops = ['DictItems','FilterList','DictFromPairs','Eq','IfThenElse','GroupCount','DictMerge']
for label, extra in (('explicit-ops', {'ops': {'type':'Lit','value':ops}}), ('no-ops', {})):
    s = srs.Substrate()
    spec = {'type': 'SynthEnumerate', 'examples': {'type': 'Lit', 'value': rows}, 'max_size': 20, 'max_candidates': 200000, 'saturate_k': 0, 'field': ''}
    spec.update(extra)
    r = s._inner.evaluate(spec, {})
    print(label, {k: r.get(k) for k in ('found','tested','distinct','halt_reason')})
"
```
