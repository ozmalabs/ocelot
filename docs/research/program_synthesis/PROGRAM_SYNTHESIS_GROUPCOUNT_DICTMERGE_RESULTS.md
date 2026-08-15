# GroupCount/DictMerge — re-verified pricing, built, plus one newly-found wire-boundary fix — RESULTS

Prereg: `PROGRAM_SYNTHESIS_GROUPCOUNT_DICTMERGE_PREREG.md` (this worktree).
Base `main @ c5aea7b` ("Record retelling-decay build landed
(ozmalabs/bigville acf0961)"), verified fresh immediately before creating
the worktree (`main` has since moved further under the concurrent Bigville
session — this rung's own work stays on its own branch, not rebased).
Worktree: `/home/matt/ozmadev/ocelot-worktrees/progsyn-groupcount-dictmerge`,
branch `progsyn-groupcount-dictmerge`, commit `45e987c` — **not merged to
`main`**, left for the orchestrator to independently verify and merge (this
session's explicit instruction: never merge to `main` directly, and never
`git stash`).

**Headline: GO, built and measured, on BOTH primitives — but the ACTUAL
mechanism differs from the original pricing in a way worth reporting
honestly. `full` 67/257 → 69/257, `content_stripped` 66/257 → 68/257,
`official` 96/257 → 98/257 — all three arms gain exactly `{87, 88}`, zero
regressions, confirmed by exact task-id set-diff. `DictMerge` converts task
87 exactly as priced. `GroupCount` did NOT convert task 88 as priced on its
own — live verification found a SEPARATE, pre-existing wire-boundary defect
(non-string dict keys silently losing their type through the `_wire`/
`json.dumps` boundary `SynthEnumerate`'s own internal example-row comparison
uses) blocking it; that defect was found, diagnosed, and fixed at its single
choke point using the engine's own already-tested `__dict__` round-trip tag,
and BOTH tasks now convert correctly, including on their held-out rows.**

---

## 1. The re-verified pricing — traced to its exact source, not re-derived

Full citation chain in `PROGRAM_SYNTHESIS_GROUPCOUNT_DICTMERGE_PREREG.md`
§1: `PROGRAM_SYNTHESIS_ARC6_STRUCTURAL_CEILING.md` §4.3 (original source,
2026-08-01/03) → `PROGRAM_SYNTHESIS_CEILING_REASSESSMENT_2_PREREG.md` §6.4
(2026-08-14, re-confirmed live, ranked "priced, bundleable, not
standalone-worth") → `PROGRAM_SYNTHESIS_CEILING_REASSESSMENT_3_PREREG.md`
§3.3 / `..._RESULTS.md` §3.4+§8 item 4 (2026-08-15, the immediately prior
rung, re-confirmed live again, named "priced, cheap, kept separate to stay
single-variable" — the exact phrase this rung's own task brief quotes).
**"Cheap" meant, precisely: touch-point cost = one new `TermNode` variant
each, the same mechanical shape as Rung 1's ten stdlib ports; benefit =
+1 task each (88 for `GroupCount`, 87 for `DictMerge`), confidence HIGH on
both.**

Fresh, live re-verification BEFORE writing any code (`scripts/
ceiling3_diag_sweep.py`, already landed on `main`, re-run in this worktree
against the CURRENT baseline — `full` 67/257): **tasks 87 and 88 both still
fail, both still `gapped:enumerate_failed`, unconverted by any of the
intervening rungs (map-template-pool, `SortBy` gate widening, the
`_plain()` Fraction fix).** Pricing reconfirmed accurate on the live,
current population before any implementation began.

## 2. The whole-population coverage check — the `SortBy` lesson, applied

The task brief's own instruction: before building, grep/check the corpus
for EVERY task that plausibly needs `GroupCount`/`DictMerge`-shaped
capability, not just the two original witness tasks (`SortBy` itself was
scoped to task 475 alone and needed a follow-up gate widening one rung
later for task 64, discovered under DIFFERENT evidence). Applied directly
(PREREG §3): all 190 currently-failing prompts grepped for
`frequen|dictionar|merge|combine|tally|occurrence|count of|duplicate|
counter|group` — 16 hits, individually triaged against their real recorded
`construction`/`gap_reason`/hole-fill data, not assumed from prompt text
alone.

**Result: exactly two tasks in the real population are `GroupCount`/
`DictMerge`-shaped and reachable by these two primitives alone — 88 and 87,
precisely the original pricing.** Task 97 (frequency of a FLATTENED list of
lists) needs `GroupCount` PLUS a flatten primitive that doesn't exist — a
second, separate gap, matching ARC6's own original "necessary for 2, alone
1" distinction (never listing 97 as `GroupCount`-alone-sufficient). Task 283
needs `GroupCount` PLUS `Recurse` (already NO-GO'd). Tasks 19/130/168 —
live-checked directly — have recorded hole-fills/construction lanes with no
Dict-construction shape at all (task 19's hole-fill is
`Minus(Count(arr),Last(arr))`; task 168 uses a dedicated `count_of_list`
template returning an Int, not a Dict). Tasks 465/277/391 need a DIFFERENT
primitive (`FilterDict`/nested-dict-construct), not `GroupCount`/
`DictMerge`. Full triage table in the PREREG §3. **This rung's after-build
sweep (§6 below) re-confirms every one of these predictions held — none of
the ruled-out tasks shifted outcome.**

## 3. What was built

**`TermNode::GroupCount { seq: TermIdx }`** (`OpKind::Unary`,
`runners/dsl/src/term.rs`) — Python's `Counter(seq)`: groups
`Value::List`/`Value::Tuple` elements by structural equality, returns a
`Value::Dict` of `element -> count` (`Value::Int`), pairs canonically sorted
by `cmp_value` (the same invariant `MkDict` maintains). Non-listlike input
passes through unchanged (the `Sort`/`Reverse` degrade precedent).

**`TermNode::DictMerge { a: TermIdx, b: TermIdx }`** (`OpKind::Binary`) —
`dict.update`/`{**a, **b}` semantics: `b` wins on a key collision, `a`'s
entries are kept where `b` has no match. **The 3-way merge task 87 needs is
NOT a new arity** — verified against task 87's real fixture asserts
(`tests/fixtures/mbpp/sanitized-mbpp.json`, not the prompt text): all three
revealed rows show `dict1`'s value winning every conflict regardless of
which later dict also holds that key, i.e. `dict1` > `dict2` > `dict3`
priority — reproduced by nesting `DictMerge(DictMerge(dict3, dict2),
dict1)`, the identical `ConcatList(ConcatList(a,b),c)` composition shape
task 108's own witness already uses in this arc. Non-Dict-Dict input
degrades to `a` unchanged.

**Registration** mirrors `Sort`/`DictItems`/`SortBy` exactly: `OP_TABLE`
entries, `build_op` cases, `term_json` cases
(`runners/dsl/src/synth_enumerate.rs`). `cargo check` found **six
exhaustive-match sites** needing the same two new arms —
`term_variants.rs` (regenerated via `tools/gen_term_variants.py`, NUM_
TERM_VARIANTS 226→228), `reflect.rs` (×2 — `describe`/read-back), `jsonio.rs`
(×3 — `variant_name`/`write_fields`/read-back) — every site mirrors its
`DictItems`/`SortBy` precedent, found by compiler error, not grepped blind.

**Evidence gating (never a blanket `OP_TABLE` append):**

- New flag `spec_output_is_dictlike` — the output-shape twin of
  `spec_has_dict_value`, mirroring `spec_output_is_listlike`/
  `spec_output_is_setlike`'s own already-measured-safe discipline (an
  OUTPUT-type gate, never bare input-shape).
- Task 88 (`a` is a `List`, so it already reaches the existing
  list-shaped typed-default branch): `GroupCount` pushed into that branch's
  op list ONLY under `spec_output_is_dictlike`, the same narrow gate
  `Sort`/`Split`/`ParseInt` already use there. `DictMerge` deliberately NOT
  added there (no witness needs it under that evidence).
- Task 87 (three Dict-shaped variables, Dict-shaped output, no list-shaped
  variable anywhere — `spec_is_list_shaped` is FALSE for it, `is_listlike`
  deliberately excludes Dict): a NEW dedicated `DICT_DEFAULT_OPS =
  ["Eq", "IfThenElse", "GroupCount", "DictMerge"]` bucket, offered via a new
  `else if spec_output_is_dictlike` branch positioned AFTER the list-shaped
  branch (task 88's routing completely unchanged) and BEFORE the bare
  arithmetic fallback — mirroring `SET_DEFAULT_OPS`'s own precedent exactly
  (a shape that isn't "list-shaped" gets its own small dedicated bucket).

## 4. The genuine mid-rung finding — pricing partially inaccurate, diagnosed and fixed, not silently absorbed

Direct forced-`ops` invocation of `SynthEnumerate` (the arc's own
"invocation, not inference" discipline) against task 88's real revealed
rows returned `found: True` — but at a WRONG term:
`GroupCount(MapList(a, __item, Str(__item)))` (stringifies every element
before counting). Direct re-evaluation confirmed this candidate produces
STRING keys (`{'10': 4, ...}`), which do NOT equal the true expected
int-keyed dict (`{10: 4, ...}`) — yet `SynthEnumerate`'s own internal
row-check accepted it. Forcing `ops=["GroupCount"]` alone (excluding the
spurious `MapList`+`Str` composition) returned `found: False, halt_reason:
saturated` — **the CORRECT, direct `GroupCount(Var(a))` term, size 2, does
NOT match its own comparison target inside `SynthEnumerate`'s search.**

Root cause, traced to its exact mechanism: `run_enumerate`'s own row
construction (`domains/prog_synthesis.py`) passes each row's expected
output through `_wire()`, whose OWN docstring already documents that
`Substrate.evaluate()` serialises the whole Term dict via `json.dumps` — and
JSON objects can only ever have STRING keys. `_wire`'s existing dict branch
(`{k: _wire(x) for k, x in v.items()}`) passed an int-keyed Python dict
straight through, so `json.dumps` silently stringified its keys before the
Rust side ever saw it. The GENUINE `expected` dict, once inside
`SynthEnumerate`'s own internal comparison, had already lost its key types
— so the TRUE `GroupCount(a)` (which correctly produces Int keys) could
never match its own corrupted target, while the WRONG
`GroupCount(MapList(...,Str(...)))` (which produces String keys) matched by
coincidence of the SAME corruption. (The real end-to-end pipeline's LATER,
separate re-verification step — `eval_and_record`, which evaluates the
graph-resident IR against a native-typed env via `ProgEval`, not this JSON
`Lit` boundary — correctly rejected the spurious candidate; task 88 ended up
`gapped:no_shape`, not falsely accepted. No incorrect-acceptance bug was
ever live; the defect only ever suppressed the CORRECT conversion.)

**This is the SAME class of defect `_wire`'s own docstring already names**
for container KIND (list vs tuple both being bare JSON arrays) — here it is
DICT KEY TYPE, not container kind. Verified the fix already exists on
BOTH sides of the engine and was simply never wired to this write path:
`persist.rs::encode_value`/`decode_value` already implement a `__dict__`
tag (`{"__dict__": [[k1,v1],[k2,v2],...]}`, a LIST of pairs rather than a
raw JSON object — sidesteps the JSON-object-keys-must-be-strings
restriction entirely) alongside the existing `__tuple__`/`__list__`/
`__set__`/`__fset__` tags — this is the SAME family `_wire` already emits
for container kind, just never applied to dict KEY type. **Fix: one
additive branch in `_wire` (emit `__dict__`-tagged form only when a dict has
a non-string key; byte-identical to before for every all-string-keyed
dict) and the inverse in `_unwire`** (`domains/prog_synthesis.py`) — zero
Rust changes, using already-tested, already-round-tripped infrastructure.
Verified directly: `_wire({10:4,...})` → `{'__dict__': [[10,4],...]}`,
`_unwire(_wire({10:4,...})) == {10:4,...}` exactly.

**Live-verified after the fix, both tasks, both via the REAL
`synthesize_from_request` pipeline (not forced ops):**

```
87 -> status: accepted, ir: DictMerge(DictMerge(Var(c),Var(b)),Var(a))  [dict1 wins, as priced]
88 -> status: accepted, construction: retrieved_exemplar, ir: GroupCount(Var(a))
```

Held-out rows independently confirmed passing for both
(`mbpp_endgame_battery.holdout_verdict`, `all_ok: True` for both). Task 88's
own conversion mechanism is `retrieved_exemplar`, not a raw top-level
`SynthEnumerate` accept — the SAME "widening an op's availability silently
changes what a DIFFERENT construction lane's hole-filler can propose"
mechanism `CEILING_REASSESSMENT_3_RESULTS.md` §3.2 already found and named
for task 64/`SortBy` (a finding, not fully re-traced to its exact internal
code path here either, mirroring that document's own residual — the PASS
verdict itself does not depend on the attribution being fully traced).

**This is reported as the honest re-pricing the task brief asked for: the
TOUCH-POINT cost was exactly as estimated for both Terms; the BENEFIT for
`GroupCount` required one additional, separate, previously-undiscovered
fix beyond the Term itself to actually realise — found, diagnosed to its
exact mechanism, and fixed using pre-existing engine infrastructure, not
assumed away or silently folded into "the primitive just worked."**

## 5. Regression risk, priced before measuring

11 currently-passing list-of-lists canary tasks (unaffected — the
`spec_output_is_dictlike` gate is orthogonal to `spec_has_list_of_lists`)
plus the standing task-132 canary were already covered by the immediately
prior rung's own canary set; this rung's OWN new risk surface is narrower
still: `GroupCount`'s addition to the list-shaped branch fires only when
`spec_output_is_dictlike` (a task 88-only condition among currently-passing
specs, verified via the zero-regression full-battery diff below, not
assumed), and the new `DICT_DEFAULT_OPS` branch can only ever fire for a
spec that was previously routed to the narrowest possible bucket (bare
`DEFAULT_OPS`) AND has an all-Dict-shaped output — strictly additive, never
a narrowing of any other bucket's routing. The `_wire`/`_unwire` fix is
additive-only by construction (the new branch is gated on "does this dict
have a non-string key", false for every existing all-string-keyed dict —
verified true for every other MBPP task's dict values by the full-battery
zero-regression result below, not assumed from the code alone).

## 6. Full MBPP battery — before/after, all three arms, real set-diff

**Before** (unmodified `main @ c5aea7b`, this worktree, engine hash
`e87c42ebbdfe` — byte-identical to `CEILING_REASSESSMENT_3_RESULTS.md`'s
own reported "after" hash, confirming this worktree started from that
rung's real shipped state):

```
full:              67/257  p=0.2607    ci=[0.210831, 0.317618]  det_identical=True
content_stripped:  66/257  p=0.256809  ci=[0.207253, 0.313529]  det_identical=True
official:          96/257  p=0.373541  ci=[0.316669, 0.434138]  det_identical=True
```

**After** (this rung, engine hash `0b29e5cb0767`, rebuilt from source
THREE separate times across this investigation — deterministic, identical
hash every time):

```
full:              69/257  p=0.268482  ci=[0.218003, 0.325781]  det_identical=True
content_stripped:  68/257  p=0.264591  ci=[0.214414, 0.321702]  det_identical=True
official:          98/257  p=0.381323  ci=[0.324101, 0.44204]   det_identical=True
```

**Exact task-id set-diff, all three arms** (direct set computation from
`results/mbpp_endgame.json`'s `runnable_rows`, saved before/after:
`results/mbpp_endgame_BEFORE_this_rung.json` vs. `results/
mbpp_endgame.json`):

| arm | before (n) | after (n) | newly passing | regressed |
|---|---|---|---|---|
| `full` | 67 | 69 | `{87, 88}` | `{}` |
| `content_stripped` | 66 | 68 | `{87, 88}` | `{}` |
| `official` | 96 | 98 | `{87, 88}` | `{}` |

`before_pass_ids ⊆ after_pass_ids` holds on all three arms, confirmed by
direct set computation, not visual inspection. **Both gains land exactly
where priced — no task converted outside the originally-scoped {87, 88},
no SortBy-class hidden second witness materialised.**

## 7. Regression discipline

**Rust suite** (`cargo test --lib --release -- --test-threads=1`): **774
passed; 0 failed; 4 ignored** (the documented `dim_infer_tests` flakes),
identical before and after this rung's Rust changes.

**Named 9-file suite**
(`test_prog_synthesis_battery_migrated.py`/`test_mbpp_baseline_migrated.py`/
`test_mbpp_endgame_migrated.py`/`test_mbpp_contamination_migrated.py`/
`test_mbpp_diet_migrated.py`/`test_program_synthesis_migrated.py`/
`test_prog_moves_migrated.py`/`test_prog_property_migrated.py`/
`test_exact_first_migrated.py`): **3 failed / 241 passed** after this
rung's changes. Independently verified NOT caused by this rung: reverted
every touched file to `main @ c5aea7b` (`git checkout c5aea7b -- <6
files>`), rebuilt from source (engine hash `e87c42ebbdfe`, matching the
pre-change baseline exactly), re-ran the SAME 9-file suite — **byte-identical
3 failed / 241 passed, same three test names**
(`test_mbpp_baseline_migrated.py::test_three_runnable_tasks_reverify_live`,
`test_prog_moves_migrated.py::test_named_regression_sweep_only_known_pins_
drift`, `test_exact_first_migrated.py::test_named_regression_sweep_only_
known_pins_drift`), same nested-sweep detail (`6 failed, 433 passed, 1
skipped, 23 errors` inside the sweep tests) — matching the ALREADY-DOCUMENTED
"shared mutable output path" fragility `CEILING_REASSESSMENT_3_RESULTS.md`
§6 and prior rungs have repeatedly re-confirmed present on clean `main`,
re-confirmed present again here on a genuinely fresh revert, not inherited
from citation. Restored the committed source afterward
(`git checkout HEAD -- <6 files>`), rebuilt (engine hash `0b29e5cb0767`,
identical to the pre-revert build — confirms deterministic build), re-ran
the full Rust suite (774/774) and the full battery one final time
(byte-identical 69/68/98) on the shipped state.

**Whole-population coverage re-check, post-build.** Re-ran the diagnostic
sweep after the fix (188 rows = 257 − 69): every task named
checked-and-ruled-out in the PREREG (19, 97, 111, 130, 140, 168, 237, 277,
283, 300, 301, 391, 464, 465) remains in its SAME outcome category —
no unexpected secondary conversion, no unexpected regression among them.

## 8. GO/NO-GO

**GO on both `GroupCount` and `DictMerge`, delivered together with a
necessary third fix.** Real measured MBPP gain: `full` +2 (`{87, 88}`),
`content_stripped` +2 (`{87, 88}`), `official` +2 (`{87, 88}`), zero
regressions on any arm, zero new Rust-suite failures, zero new Python-suite
failures (all confirmed against an independently rebuilt, genuinely
unmodified baseline). Two new `TermNode` variants (the originally-priced
touch-point cost, exactly as estimated) plus one small, additive,
already-infrastructure-backed wire-boundary fix (found live, not
anticipated by the original pricing, diagnosed to its exact mechanism and
fixed rather than worked around or silently absorbed).

## 9. What this document does NOT establish

1. **Task 88's exact conversion mechanism (`retrieved_exemplar`'s
   hole-filler, not a raw `SynthEnumerate` top-level accept) is inferred
   from the same pattern `CEILING_REASSESSMENT_3_RESULTS.md` §3.2 already
   found for task 64, not re-traced line-by-line through the retrieval
   engine's own source here either.** The PASS verdict (held-out row
   agreement, independently confirmed) does not depend on this attribution
   being fully traced — matching that document's own standing residual.
2. **The `_wire`/`_unwire` `__dict__` fix is scoped to the ONE choke point
   this rung's target tasks flow through** (`run_enumerate`'s row
   construction). A DIFFERENT, narrower code path
   (`domains/prog_synthesis.py`'s IfThenElse-branch-partition solver,
   `row = {"inputs": env, "output": sub.node(r)["attrs"].get("expected")}`)
   builds its own rows WITHOUT `_wire` at all and was NOT touched — named
   here, not sized or fixed, out of scope for this rung's own target.
3. **Whether any OTHER currently-passing or currently-failing task has a
   non-string-keyed dict flowing through a DIFFERENT `_wire` call site**
   (not `run_enumerate`'s) was not exhaustively swept — the full-battery
   zero-regression result covers every task THIS rung's battery run
   touches, but a hypothetical future task with a different dict-key shape
   in a different code path is not pre-emptively guaranteed safe beyond
   "the new branch is additive and off by default for all-string-keyed
   dicts," the same discipline every gate in this arc uses.
4. **Task 97's flatten-primitive gap and task 283's `Recurse` dependency**
   remain unbuilt, matching ARC6's own original "necessary for 2, alone 1"
   distinction — not re-argued here, not converted by this rung.
5. **Whether any of this reflects real human program-synthesis cognition**
   remains exactly as open as every prior document in this arc left it.

## Reproduce

```bash
cd /home/matt/ozmadev/ocelot-worktrees/progsyn-groupcount-dictmerge
git log --oneline -1   # 45e987c, on top of main @ c5aea7b
bash scripts/engine_build.sh   # then: python3 domains/engine_provenance.py (build script's trailing `python` call needs python3 on this machine)
PYTHONPATH="runners/dsl/python:.:scripts" OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 \
  python3 scripts/mbpp_endgame_battery.py
```

Named 9-file regression suite:
```bash
PYTHONPATH="runners/dsl/python:.:scripts" OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 \
  python3 -m pytest tests/test_prog_synthesis_battery_migrated.py tests/test_mbpp_baseline_migrated.py \
  tests/test_mbpp_endgame_migrated.py tests/test_mbpp_contamination_migrated.py tests/test_mbpp_diet_migrated.py \
  tests/test_program_synthesis_migrated.py tests/test_prog_moves_migrated.py tests/test_prog_property_migrated.py \
  tests/test_exact_first_migrated.py -q
```

Per-task diagnostic sweep (§2/§7's own data source):
```bash
PYTHONPATH="runners/dsl/python:.:scripts" OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 \
  python3 scripts/ceiling3_diag_sweep.py
```
