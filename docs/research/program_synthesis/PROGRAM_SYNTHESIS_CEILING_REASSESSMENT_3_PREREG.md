# Fresh ceiling reassessment at the post-delimjoin/budgetwall baseline — PREREG

**Date:** 2026-08-15. Base `main @ f1bb4f6` ("Scope the Bigville gossip gap:
not a missing drive, two missing bridges"), verified fresh via
`git log --oneline -1 main` immediately before creating the worktree, per
house discipline (this repo's `main` is shared with a concurrent, unrelated
Bigville research session today). Worktree:
`/home/matt/ozmadev/ocelot-worktrees/progsyn-ceiling-reassessment-3`, branch
`progsyn-ceiling-reassessment-3`, `data/` re-symlinked and verified
(`data/wiktionary/en.jsonl.gz` resolves to the real 492MB file), engine
rebuilt from source (`cargo build --release`, hash `e2fbf39e6b4e`), full Rust
suite green (`774 passed; 0 failed; 4 ignored`, the documented
`dim_infer_tests` flakes).

**This is a fresh investigation, not a continuation of a named candidate.**
Per the task brief: the delimiter-join primitive for task 421 and the
search-budget wall for 102/411/419/439
(`PROGRAM_SYNTHESIS_DELIMJOIN_BUDGETWALL_RESULTS.md`) are both closed,
correctly NO-GO'd, zero code retained — not re-litigated here. This document
starts from the real, freshly measured baseline and re-runs the
failure-cause grouping from scratch.

---

## 1. Real baseline, confirmed live (not trusted from the brief)

`OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 python3
scripts/mbpp_endgame_battery.py`, run fresh in this worktree after a
from-source engine rebuild:

```
full:              66/257  p=0.256809  ci=[0.207253, 0.313529]  det_identical=True
content_stripped:  65/257  p=0.252918  ci=[0.20368,  0.309434]  det_identical=True
official:          94/257  p=0.365759  ci=[0.309252, 0.426219]  det_identical=True
```

This matches `PROGRAM_SYNTHESIS_DELIMJOIN_BUDGETWALL_RESULTS.md`'s own
"before" measurement exactly (byte-identical aggregate AND, independently
re-derived here, byte-identical exact pass-id sets on all three arms) —
confirming the stated "previously-named queue is fully resolved, zero code
retained" claim directly rather than by citation. `full` (n=257) is used as
the primary denominator throughout, per the harness's own convention.

Worktree provisioning note (matches the documented gap in
`PROGRAM_SYNTHESIS_DICTITEMS_SORTBY_RESULTS.md` §7): the fresh worktree's
gitignored `results/` directory lacked
`mbpp_zero_shot_baseline.json`/`prog_construction_scan.json`/
`arc4_structural_verdicts.json`/`prog_chunk_mine.json` (referenced at
import/fixture time by `mbpp_endgame_battery.py`/`prog_synthesis.py`/
`prog_chunk_growth.py`); copied the specific closure of referenced files
from the primary tree (never a blanket directory copy) — a provisioning gap,
not a code defect, confirmed by the missing-file errors disappearing the
moment each named artifact is present.

## 2. Failure-cause grouping — the real 191 currently-failing runnable tasks

Every one of the 191 non-passing `full`-arm runnable tasks (257 − 66) was
individually re-run through `domains.prog_synthesis.synthesize_from_request`
directly (same `boot_full()` the battery itself uses), reading the FULL
`read_goal()` dict — not the battery's trimmed row — for
`enumerate.tested`/`enumerate.ops`/`construction`/`gap_reason`/`retrieval`,
mirroring `PROGRAM_SYNTHESIS_CEILING_REASSESSMENT_2_PREREG.md` §2's own
methodology exactly (script: `scripts/ceiling3_diag_sweep.py` in this
worktree, output `results/ceiling3_diag_sweep.json`).

| outcome | n | what it means |
|---|---|---|
| `gapped:enumerate_failed` | **99** | reached `SynthEnumerate`, found nothing |
| `accepted_holdout_fail` | **51** | a candidate was ACCEPTED (revealed rows fit) but disagrees on a held-out row |
| `gapped:property_verdict_reject` | **26** | a candidate was built and REJECTED by a held self-verifying property check |
| `gapped:structural_verdict_reject` | **10** | a candidate was built and REJECTED by a structural-trap detector |
| `runner_exception:TypeError` | **2** | an uncaught Python exception aborted the whole attempt |
| `not_recognized` | **1** | the request text itself was never recognized |
| `gapped:no_shape` | **1** | no cover-parts / operator shape matched at all |
| `gapped:exhausted` | **1** | attempt budget exhausted before any status resolved |

**This is exactly the CEILING_REASSESSMENT_2 population (194) minus the 3
tasks the map-template-pool rung converted (104, 118, 456) — every other
count is unchanged**, confirming the population has genuinely not shifted
in shape since that rung landed, only shrunk by the tasks it actually
converted. `gapped:enumerate_failed` (99) sub-splits the same way that
document found:

```
budget-exhausted (tested == 200,000 exactly):  84
genuinely saturated under budget (<200,000):   15
```

`ops=None` (`SynthesisOperatorShape` never fires) for all 99 — reconfirms
CEILING_REASSESSMENT_2's Q1 finding that the selection layer contributes
nothing today; still not chased as its own rung here for the same reason
that document gave (no task fails FOR that reason specifically — the typed
default's own evidence gates are the effective selector).

The `accepted_holdout_fail`/`*_verdict_reject` population (87) has the
identical construction breakdown CEILING_REASSESSMENT_2 measured: 60
`retrieved_exemplar`-sourced (24 holdout-fail + 26 property-reject + 10
structural-reject) — `SynthEnumerate` never invoked at all for any of
them (`enumerate.tested is None`, reconfirmed directly) — plus 27
`mck_*`/template-family `accepted_holdout_fail` where a non-enumerate
construction lane wins wrongly even though the search does run.

## 3. What's newly reachable — checked directly, not assumed, per the task's
   own instruction to check WHOLE requirements, not per-primitive slices

### 3.1 Task 64 — `SortBy`, live-verified, genuinely new finding

`SortBy` (landed by the DictItems/SortBy rung, gated ONLY on
`spec_has_dict_value` — narrowly scoped to serve task 475's `Counter`
shape, never re-checked against the WHOLE population once shipped, exactly
the failure mode this task brief named). Task 64's prompt ("sort a list of
tuples using the second value of each tuple") has NO dict anywhere — its
input is `List[Tuple]` — so `spec_has_dict_value` is false and `SortBy`
never enters `op_list` for it under the automatic typed default.

**Live-verified**, direct `SynthEnumerate` call with `ops=["SortBy"]`
forced (`substrate_rs.Substrate()._inner.evaluate`, the standing
"invocation, not inference" discipline):

```
found: true, halt_reason: solved, size: 4, tested: 9, distinct: 7
term: SortBy(a, item, Sort(item))
```

The found key template (`Sort(item)`, NOT `IndexAt(item,1)`) already exists
in `map_templates_by_size`, gated on `set_map_wanted || spec_has_list_of_lists`
(the map-template-pool rung's own flag) — task 64's `a` is `List[Tuple]`,
and a `Tuple` counts as list-like, so `spec_has_list_of_lists` is already
TRUE for this spec. **`Sort(item)` on a mixed `(Str, Int)` 2-tuple always
places the `Int` first under the DSL's cross-type total order, so sorting
BY that canonicalized key reproduces "sort by the numeric field" for this
exact (str, int) shape** — confirmed correct on both revealed rows AND the
held-out row (`[('Physics', 96), ('Chemistry', 97), ('Biology', 45)] →
[('Biology', 45), ('Physics', 96), ('Chemistry', 97)]`, exact match).

**The gap is therefore purely a gate**: `SortBy` needs to be OFFERED for
this spec, and the key-template machinery it needs is already present and
already safely gated by an existing, previously-measured-safe flag.
**Zero new `TermNode`, zero new template — one gate widening.**

### 3.2 Task 12 — also a live `SortBy` witness, but NOT reachable by the
   same fix (named, not converted by this rung)

Task 12 ("sort a matrix by row sum") has an exact live witness too —
`SortBy(a, item, Sum(item))` matches all three rows including held-out,
confirmed directly. **But task 12's current outcome is
`accepted_holdout_fail` via `construction: retrieved_exemplar`, with
`enumerate.tested is None` — `SynthEnumerate` is never invoked for this
task at all**, because a WRONG `retrieved_exemplar` candidate is accepted
first and there is no fallthrough to enumerate on a rejected retrieval
(the same construction-precedence gap CEILING_REASSESSMENT_2 §4 named and
explicitly declined to build blind, for a 60-task blast radius). Widening
`SortBy`'s op-list gate cannot help task 12 — the search that would use it
never runs. **Named here as a second confirmation that the
retrieved-exemplar-fallthrough gap is real and separable, not built.**

### 3.3 Other candidates checked and ruled out or deferred

- **Task 108** ("merge three lists into a single sorted list") — a genuine
  `Sort(ConcatList(ConcatList(a,b),c))` composition exists over
  already-shipped ops, but the task is `budget-exhausted` (`tested:200,000`)
  under the current default, and per
  `PROGRAM_SYNTHESIS_DELIMJOIN_BUDGETWALL_RESULTS.md` §2's own decisive
  finding (raising the budget surfaces spurious `Eq`/`IfThenElse`
  memorizations before the genuine construction, board-wide runtime cost),
  this is a budget-wall case, not a gate/template gap — not re-attempted
  here, matching that document's own NO-GO reasoning.
- **Tasks 87/88/97/283/301** (dict-merge, frequency-map/`Counter`, nested
  frequency, digit-frequency, dict-depth) — re-confirmed still needing a
  genuinely NEW `TermNode` (`GroupCount`/`DictMerge`, or — for 283/301 —
  `Recurse`, already NO-GO'd). `DictItems` only ITERATES an existing dict;
  none of these tasks have a dict to iterate — they need to CONSTRUCT one,
  which no already-shipped Term does. Unchanged from
  `PROGRAM_SYNTHESIS_CEILING_REASSESSMENT_2_PREREG.md` §6.4's own pricing
  (`GroupCount` +1 task 88, `DictMerge` +1 task 87, both LOW cost/HIGH
  confidence/bundleable, not standalone-worth) — reconfirmed, not built in
  this rung (see §5).
- **Task 465** ("drop empty items from a dictionary") — same
  dict-construction gap as above (needs a filtered-dict-rebuild primitive
  that does not exist); named, not sized further here.
- **Tasks 111/140** (N-way `Intersect`/flatten-to-`Set` over a *list* of
  sets, not two fixed args) — `Intersect`/`Union` exist only as 2-ARG
  `ListBinary` ops (the `ConcatList` precedent); a fold-reduce over a
  variable-length list of sets needs either a new `IntersectAll`/`UnionAll`
  op (zero-new-`TermNode`-shaped, the `ConcatList` class) or a first/rest
  binder this arm doesn't have today. Sized qualitatively as "plausible,
  same class as `ConcatList`, not yet witnessed line-for-line" — NOT
  live-verified with a hand-built witness the way §3.1 was, so not
  recommended for this rung; named as a future candidate only.
- **Recurse** (7 ids, tasks 99/260/265/283/301/448/462) — re-confirmed
  still failing, still NO-GO per `CEILING_REASSESSMENT_2` §6.1's own
  strengthened finding (spurious holdout-failing accepts on task 99 even
  without Recurse). Not re-investigated further here — no new evidence to
  add.
- **Format** (task 390, `term:Format`) and **Combinations** (task 255) —
  re-confirmed still exactly one legitimate task each, still NO-GO per the
  standing "one task does not justify a new Term" discipline.

## 4. The plan

**Build the single, cheap, live-verified fix from §3.1: widen `SortBy`'s
inclusion in the list-shaped-branch typed default from
`spec_has_dict_value` alone to `spec_has_dict_value || spec_has_list_of_lists`**
(exact touch point: `runners/dsl/src/synth_enumerate.rs`, the
`if spec_has_dict_value { v.push("DictItems"); v.push("SortBy");
v.push("Reverse"); }` block, ~line 1990) — split into two guards so
`DictItems`/`Reverse` (which need an ACTUAL dict/string-list respectively
to be useful) stay exactly as narrowly gated as they are today, and only
`SortBy` additionally fires under `spec_has_list_of_lists`.

This is the single cheapest, best-evidenced candidate found: **zero new
`TermNode`, zero new template, one evidence-gate widening reusing an
already-shipped, already-measured-safe flag** (`spec_has_list_of_lists`,
proven safe for the `Sort(item)` template addition by the map-template-pool
rung already) — the exact same risk class as every prior evidence-gate
widening in this arc, and cheaper than the map-template-pool rung itself
(one touch point, not two).

**Regression risk, priced before building:** 11 currently-passing tasks
have `spec_has_list_of_lists=true` (104, 120, 272, 290, 393, 413, 418, 457,
460, 473, 475) — every one of these is a canary: adding `SortBy` to their
`op_list` means their search now ALSO tries `SortBy`-shaped candidates at
every size, which could (a) cost budget that was previously spent on the
op that actually solves them, or (b) — more subtly — cause `SortBy` to
register a spurious matching candidate FIRST (ascending-size search
returns on first signature match), changing which construction wins. Both
will be checked directly post-build, not assumed safe. Task 132 (this
arc's standing canary) has no list-of-lists content and is expected
unaffected by construction, but will be checked anyway per house
discipline.

**What this rung does NOT attempt:** the retrieved-exemplar-fallthrough gap
(§3.2, up to 60 tasks inventory, genuinely unpriced, explicitly NOT
recommended to build blind by the prior document and re-confirmed here with
a second concrete example, task 12); `GroupCount`/`DictMerge` (priced,
cheap, but a DIFFERENT risk class — new `TermNode`s — bundled as a
lower-priority follow-on, not this rung, to keep this rung's measurement
tight and single-variable); the `IntersectAll`/`UnionAll` N-way-set
candidate (not live-verified); the 27-task `mck_*` construction-precedence
question (named, not investigated, matches the prior document's own
scoping).

## 5. What this document does NOT establish

1. §3.1's `SortBy` gate widening is priced and live-verified for its ONE
   target witness (task 64) via a direct `SynthEnumerate` call with
   explicit `ops`; whether the AUTOMATIC typed default (after the gate
   widening lands) reaches the same witness within the real
   `max_candidates:200,000` budget is a build-time question, checked in
   the RESULTS document, not assumed here (mirrors this whole arc's
   standing "reach is not conversion" discount).
2. Whether any of the 11 list-of-lists canary tasks regress is unmeasured
   until the build lands — priced as a real risk above, not dismissed.
3. §3.3's `IntersectAll`/`UnionAll` sizing is qualitative only — no hand
   witness was built or evaluated the way §3.1's was.
4. This document does not re-litigate the delimjoin/budgetwall NO-GOs or
   the retrieved-exemplar-fallthrough sizing question — both are named at
   the depth the task brief asked for (confirm still-true, look for new
   evidence) and no further than that.
5. Whether any of this reflects real human program-synthesis cognition
   remains exactly as open as every prior document in this arc left it.

## Reproduce

```bash
cd /home/matt/ozmadev/ocelot-worktrees/progsyn-ceiling-reassessment-3
git log --oneline -1   # on top of main @ f1bb4f6
bash scripts/engine_build.sh   # (or manual cargo build --release + cp, see log)
PYTHONPATH="runners/dsl/python:.:scripts" OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 \
  python3 scripts/mbpp_endgame_battery.py
PYTHONPATH="runners/dsl/python:.:scripts" OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 \
  python3 scripts/ceiling3_diag_sweep.py
```
