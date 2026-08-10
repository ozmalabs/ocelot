# ARC 6 — THE FULL PAIRED SWEEP (946 files, both arms)

**Date:** 2026-08-03
**Arm A:** engine `48da7257f35d3046…` — pre-value-layer.
**Arm C:** engine `8311d4356082acf4…` — value layer live.
**Artifacts:** `results/arc6_full_sweep_armA.json`, `results/arc6_full_sweep_armC.json`
(946/946 files done in each arm).
**Independent confirmation:** a separate single-process sweep at coherent HEAD
(`var/full_sweep_coherent.log`, engine `8311d435…`) reported
**76 failed / 8617 passed / 75 skipped** in 2:19:16.

This is the sweep prereg **A5** requires: a battery-green result on an
engine-touching change is *not* evidence of no regression, because the
value-layer rung shipped two real bugs that were invisible to the 257-task
battery and visible only here.

---

## 1. The headline: red nodes went DOWN

| arm | red files | red nodes |
|---|---|---|
| **A** (pre-value-layer) | 93 | **157** |
| **C** (value layer live) | 100 | **145** |

**37 fixed, 25 new, net −12 nodes.** File count rose while node count fell —
which is why **a file count is not a baseline** and this document reports
nodes.

---

## 2. The 25 new reds, classified

### (a) Type-blind test assertions — EXPECTED, test-side, ~9 nodes
Tests asserting a list against a tuple, which passed only because the two were
the same `Value::Tuple`:

```
assert [0, 1, 2, 3, 4, 5, …] == (0, 1, 2, 3, 4, 5, …)   test_doom_eye
assert [False] == (False,)                               test_foveal_predictive_coding
assert [40, 41, …] == (np.int64(40), …)                  (numpy path)
assert [#21424, …] == []                                 test_document_memory, test_topic_span
```

These are the **type-blind spec** family the value-layer rung already named
(5 found in its 116-file sample; the full sweep extends it). **The test's
expectation is wrong, not the code** — but each needs a witness before
re-pinning, because "the spec is wrong" and "the program is wrong" look
identical from the assertion alone.

### (b) Pin drifts from the value-layer gains — EXPECTED, ~6 nodes
```
test_search_reach::test_after_pass_ids_match        [69,90,132,…161,257,…] vs […278,410,…]
test_search_reach::test_after_accepted_holdout_fail_ids_match
test_search_reach::test_still_gapped_residual_is_named_not_hidden
test_retrieval::test_ceiling_task_reproduces_measured_outcome_live[106]  'enumerate_failed' == 'no_shape'
test_reject_informs_repair::test_no_wrong_accept_regression_vs_v1_7_0_baseline
test_exact_first / test_prog_moves::test_named_regression_sweep_only_known_pins_drift
```
The ids `161, 257` appearing in the pass list are the value layer's own
measured gains. Re-pin in the improvement direction with dated notes and
constructed witnesses.

### (c) Engine-identity pins — EXPECTED, 3 nodes
`test_doom_emotion_nar…` and a `canonical_so_md5` assertion pinned
`1e7964e2…`; the coherent engine hashes `4ce2a8d9…`. These pin the binary by
hash and must move when the binary legitimately moves.

### (d) Flaky, present in BOTH arms — NOT regressions, 2 nodes
```
A: "expected ≥3x speedup; got linear=0.071ms indexed=0.035ms"
C: "expected ≥3x speedup; got linear=0.064ms indexed=0.039ms"
```
Same test, different numbers, red in both arms — a timing-sensitive gate, not
a consequence of this change. `test_eye_timing` (`1.208 > 1.6`) is the same
shape.

### (e) **THE ONE THAT MATTERS — a possible search-space regression, 5 nodes**
```
test_arc6_tier0::test_string_as_sequence_reaches_the_search_…   AssertionError: max_size
test_arc6_tier0::test_tmpl_item_in_listvar_fires                AssertionError: budget
test_arc6_tier0::test_tmpl_len_item_vs_var_fires                AssertionError: budget
test_arc6_tier0::test_tmpl_nested_reduction_fires               AssertionError: budget
test_synth_enumerate::test_list_map_extracts_per_element        {'distinct': 54, 'halt_reason': 'max_size'}
```

**These are tier-0's own units, and they passed when tier-0 measured them.**
They now exhaust budget or `max_size`.

**HYPOTHESIS, EXPLICITLY NOT CONFIRMED.** Two candidate mechanisms, and they
have opposite remedies:

1. **Search-space cost** — list and tuple no longer collide, so
   observational-equivalence pruning is weaker and the candidate count grows.
   This is the `TupleOf` 167 → 14,709 hazard recurring elsewhere. *But
   `test_list_map` reports `distinct: 54`, which is small — evidence against.*
2. **Expressibility** — the target is now *list*-typed and `SynthEnumerate`
   may only construct tuples, making list-typed targets **unreachable at any
   budget**. That would be the mirror of the already-named `inputs_json`
   boundary (a tuple *argument* arrives as a list), one layer out.

Mechanism (2) would be the more serious finding: it is a *missing dimension*,
not a budget problem, and arc 5 established those are unreachable at any
search size. **I attempted an inline probe and got the API shape wrong; I am
recording the hypothesis rather than asserting a mechanism I did not verify.**
Determining which — by live invocation, both directions — is the first job of
the next rung.

---

## 2(e) RESOLVED (2026-08-03) — **BOTH, and they are two different regressions**

Measured by paired live invocation, same rows, same ops, engines swapped in an
isolated copy (arm A `48da7257…` verified loaded from outside the shared tree,
list/tuple confirmed collapsing; arm C `8311d435…`).

### Case 1 — `test_tmpl_item_in_listvar_fires` → **BUDGET.** Search-space explosion.

| arm | found | halt | distinct |
|---|---|---|---|
| A | **True** | solved | **1,434** |
| C | False | budget | **16,148** |

**An 11× explosion in distinct candidates**, turning a solved search into
budget exhaustion. Target type is *not* the cause: expected-as-tuple and
expected-as-list give byte-identical results **in both arms** (A: solved/1,434
either way; C: budget/16,148 either way). This is the `TupleOf` 167 → 14,709
hazard recurring — **list and tuple no longer collide, so
observational-equivalence pruning is weaker.**

### Case 2 — `test_list_map_extracts_per_element` → **NOT budget. The candidate is never generated.**

| arm | found | halt | distinct |
|---|---|---|---|
| A | **True** | solved | 17 |
| C | False | max_size | 54 |

And raising the budget does **not** help — `distinct` *plateaus*:

```
max_size= 9  found=False  distinct=54
max_size=11  found=False  distinct=54
max_size=13  found=False  distinct=129
max_size=15  found=False  distinct=129
```

Three facts establish this is generation, not budget or expressibility:

1. **Arm A's win was GENUINE, not a collapse artifact** — it found exactly the
   term the test docstring describes:
   `MapList(lists, __item → IndexAt(__item, 0))`. Checked because a
   type-collapse false-positive would have inverted the diagnosis.
2. **That term is expressible and matchable on arm C** — evaluated directly, it
   produces `[1, 3]` as a **`list`**, type-equal to the target. So the answer
   exists and would match.
3. **It is never enumerated, at any size tried.** `distinct` plateauing while
   `max_size` rises means the generator is exhausted — it cannot build the
   candidate at all.

**Likely cause (stated as likely, not proven): template-pool eligibility keyed
on spec shape.** The value layer introduced a `spec_is_list_shaped` typed
default; a list-typed spec now selects a different pool, and the
`IndexAt(item, 0)` template appears no longer to be offered for this op set.

### Why this matters, and why the two need OPPOSITE fixes

- **Case 1** wants **pruning-equivalence and semantic-equality separated.**
  Observational equivalence should treat list and tuple as the *same* for
  pruning while the verdict keeps them *distinct*. These are different
  relations and the value layer collapsed them into one.
- **Case 2** wants the **template pool restored** for list-shaped specs. It is
  unreachable at any budget, which by arc 5's framing is the
  missing-dimension class, not the budget class.

**Neither is a pin. Both are genuine regressions of the value-layer rung**,
invisible to the 257-task battery — which is exactly the claim prereg A5
registers, now with a second and third instance.

**The MBPP net stays positive** (48 pass ids, zero lost) — but that is evidence
the cost *did not bite there*, not evidence of no cost.

---

## 3. What this sweep vindicates

**37 nodes went green**, almost all `test_arc6_valuelayer_migrated`, which was
red on arm A precisely because the value layer was absent from that binary:
`list_literal: tuple vs list`, `identity_list`, `list_call`, `list_of_zip`,
`item_assignment`, `aug_concat`, `assert 'fail' == 'pass'`. The fix does what
it claims across the whole tree, not only on the battery.

---

## 4. Open

- Resolve §2(e) by invocation — **budget or expressibility?** Different rungs.
- Re-pin §2(a)–(c) with witnesses; do not widen assertions.
- §2(d) is flaky in both arms — quarantine or fix, but do not attribute it here.
- `test_arc6_tier0::test_no_python_decision_was_added` reds for **any**
  uncommitted work under `domains/` or `seeds/` by design. Not a defect.
