# GroupCount/DictMerge — re-verify the priced pricing, build if it holds — PREREG

**Date:** 2026-08-15. Base `main @ c5aea7b` ("Record retelling-decay build
landed (ozmalabs/bigville acf0961)"), verified fresh via `git log --oneline
-1 main` immediately before creating the worktree (this repo's `main` is
shared with a concurrent, unrelated Bigville research session today — `main`
has already moved to `df00b37` by the time this document is written; this
rung's own work stays on its own worktree branch, not rebased mid-task).
Worktree: `/home/matt/ozmadev/ocelot-worktrees/progsyn-groupcount-dictmerge`,
branch `progsyn-groupcount-dictmerge`. `data/` re-symlinked and verified
(`data/wiktionary/en.jsonl.gz` resolves to the real 492MB file). Engine
rebuilt from source (`cargo build --release`, hash `e87c42ebbdfe` — the
IDENTICAL hash `CEILING_REASSESSMENT_3_RESULTS.md` reports for its own "after"
state, confirming this worktree's `synth_enumerate.rs` is byte-identical to
that rung's shipped source before this rung's own edits begin). Full Rust
suite green (`774 passed; 0 failed; 4 ignored`, the documented
`dim_infer_tests` flakes) BEFORE any code was touched.

**This is a continuation rung, not a fresh investigation** — `GroupCount`/
`DictMerge` were named, priced, and deliberately NOT built by
`PROGRAM_SYNTHESIS_CEILING_REASSESSMENT_3_RESULTS.md` §8 item 4, to keep that
rung's own measurement single-variable. This document re-verifies that
pricing live before building anything, per this session's own standing
discipline (the SortBy rung's own lesson: a primitive scoped to one witness
task must be re-checked against the WHOLE population before shipping, not
just its original motivating task).

---

## 1. The exact citation being re-verified

**Source of the pricing** (traced to its origin, not re-derived):

- **`PROGRAM_SYNTHESIS_ARC6_STRUCTURAL_CEILING.md`** §4.3 (Tier 2 table,
  2026-08-01/03): `term:GroupCount` — alone 1 (`88`), necessary for 2
  (`88, 283`), cost "1 new Term". `term:DictMerge` — alone 1 (`87`),
  necessary for 1, cost "1 new Term". (Also listed in that document's §3.1
  raw grouping as part of "S11 Frequency map (Counter): 88, 283" and "S16
  singletons: dict merge 87".)
- **`PROGRAM_SYNTHESIS_CEILING_REASSESSMENT_2_PREREG.md`** §6.4
  (2026-08-14): re-confirmed both still failing live
  (`gapped:enumerate_failed`, task 88 `tested=200000`, task 87
  `tested=53179`), re-stated the ARC6 pricing verbatim, and explicitly
  ranked both "priced, bundleable, not standalone-worth" (§7 table, rank 3
  tied) rather than building either.
- **`PROGRAM_SYNTHESIS_CEILING_REASSESSMENT_3_PREREG.md`** §3.3 /
  **`..._RESULTS.md`** §3.4+§8 item 4 (2026-08-15, the immediately prior
  rung): reconfirmed both still needing "a genuinely NEW `TermNode`" (neither
  is reachable by composing already-shipped Terms, unlike most of that
  rung's other candidates), reconfirmed the exact same pricing (`GroupCount`
  +1 task 88, `DictMerge` +1 task 87), and named them explicitly as "priced,
  cheap, kept separate to stay single-variable" — the exact phrase this
  rung's own brief quotes.

**What "cheap" meant precisely, quoted exactly, not paraphrased**
(`CEILING_REASSESSMENT_2_PREREG.md` §6.4): *"One new `TermNode`, same
'stdlib Term port' shape as Rung 1's own ten — a legitimate small unit, but
ONE task, same caution as Format,"* and *"Neither is individually worth a
dedicated rung under this arc's own standing rule; both are cheap enough
(stdlib Term ports, zero architecture) that they would be reasonable to
BUNDLE into a future primitive-layer rung."* The cost dimension priced was
**touch-point cost** (one new `TermNode` variant each, the same mechanical
shape as the ten Rung-1 stdlib ports), not search-budget cost; the gain
dimension priced was **+1 task each** (88 for `GroupCount`, 87 for
`DictMerge`), confidence "HIGH" on both.

## 2. Fresh live re-verification — the real baseline, run before touching code

`OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 python3
scripts/mbpp_endgame_battery.py`, run fresh in this worktree on the
unmodified engine:

```
full:              67/257  p=0.2607    ci=[0.210831, 0.317618]  det_identical=True
content_stripped:  66/257  p=0.256809  ci=[0.207253, 0.313529]  det_identical=True
official:          96/257  p=0.373541  ci=[0.316669, 0.434138]  det_identical=True
```

Byte-identical to `CEILING_REASSESSMENT_3_RESULTS.md`'s own "after" state —
confirms the prior rung's `SortBy` gate widening is genuinely on `main` and
this worktree measures from the real, current baseline, not a stale one.

`scripts/ceiling3_diag_sweep.py` (already landed on `main` by the prior
rung, reused verbatim — same `boot_full()`, same per-task
`synthesize_from_request` call, same `read_goal()` dict) re-run fresh:
190 non-passing tasks (257 − 67). **Tasks 87 and 88 both still fail, both
still `gapped:enumerate_failed`:**

```
task 87 | gapped:enumerate_failed | "Write a function to merge three dictionaries into a single dictionary."
task 88 | gapped:enumerate_failed | "Write a function to get the frequency of all the elements in a list, returned as a dictionary."
```

**Pricing reconfirmed accurate on the live, current population — neither
task converted by any of the intervening rungs (map-template-pool, SortBy
gate widening, or the `_plain()` Fraction fix).**

## 3. The whole-population coverage check — the standing lesson from `SortBy`, applied directly

The task brief's own instruction, quoted: *"check the corpus for EVERY task
that plausibly needs `GroupCount`/`DictMerge`-shaped capability... do not
repeat the mistake"* (`SortBy` shipped scoped to task 475 alone and needed a
follow-up gate widening for task 64 under different evidence, one rung
later). Applied here BEFORE writing any Rust:

Grepped all 190 currently-failing prompts for `frequen|dictionar|merge|
combine|tally|occurrence|count of|duplicate|counter|group` — 16 hits,
individually triaged:

| id | prompt (abridged) | verdict |
|---|---|---|
| **87** | merge three dictionaries | **`DictMerge` target** — the pricing's own witness |
| **88** | frequency of list elements, as a dict | **`GroupCount` target** — the pricing's own witness |
| 97 | frequency of elements in a FLATTENED list of lists | needs `GroupCount` PLUS a flatten primitive (no `Flatten`/general-combinator-`Fold` Term exists) — a SECOND gap, not closed by this rung; matches ARC6's own S11 grouping (only 88+283 listed as `GroupCount`-necessary, never 97) |
| 283 | digit-frequency check on an integer | needs `GroupCount` PLUS `Recurse` (already NO-GO'd, `CEILING_REASSESSMENT_2` §6.1) — will NOT convert from `GroupCount` alone, matches ARC6's own "necessary for 2, alone 1" distinction exactly |
| 301 | depth of a dictionary | needs `Recurse`, unrelated to `GroupCount`/`DictMerge` |
| 465 | drop empty items from a dict | needs a dict-FILTER/rebuild primitive (`FilterDict`, doesn't exist) — different gap |
| 391 | convert list(s) to a NESTED dict | needs a dict-CONSTRUCT-from-list primitive, different shape than merging two existing dicts |
| 277 | filter a dict by value threshold | needs `FilterDict`, different gap |
| 111, 140 | N-way `Intersect`/flatten-to-set over a list of sets | already named `CEILING_REASSESSMENT_3` §3.4, unrelated to Dict construction |
| 19 | contains a duplicate element (bool) | live `retrieved_exemplar` hole-fill is `Minus(Count(arr),Last(arr))` — unrelated to `GroupCount`; checked directly, not GroupCount-shaped |
| 130 | item with max frequency | `construction: None`, no retrieval record — a different (`mck_*`/template) lane; not enumerate-reachable regardless of op inventory; not expected to convert, checked post-build anyway (§ below) |
| 168 | count occurrences of a number | `construction: count_of_list`, a dedicated existing template lane, output is an Int not a Dict — not `GroupCount`-shaped |
| 237 | tuple->count-dict, `runner_exception` | a DIFFERENT defect (tuple-as-dict-key hashability, `unhashable type: 'list'`) — named out of scope by `CEILING_REASSESSMENT_2` §6.5, unrelated to this rung |
| 300, 464 | unrelated ("count of binary sequences", "all dict values same") | checked and ruled out, no Dict-construction/merge shape |

**Conclusion: exactly two tasks in the real, current 190-task failing
population are `GroupCount`/`DictMerge`-shaped and reachable by these two
primitives alone — 88 and 87, precisely the ARC6/CEILING_REASSESSMENT_2
pricing, not more and not fewer.** No SortBy-class "hidden second witness"
exists for either primitive today. This is reported as the coverage check
the task brief required, not skipped.

## 4. What's built — one `TermNode` each, evidence-gated

**`GroupCount { seq: TermIdx }`** (`OpKind::Unary`) — Python's
`Counter(seq)`: groups `Value::List`/`Value::Tuple` elements by structural
equality, returns a `Value::Dict` of `element -> count`, pairs canonically
sorted by `cmp_value` (the same invariant `MkDict` maintains — dict equality
in this engine is order-independent by construction, confirmed by reading
`MkDict`'s own comment and mirrored here, not re-derived). Non-listlike
input passes through unchanged (the `Sort`/`Reverse` degrade precedent).

**`DictMerge { a: TermIdx, b: TermIdx }`** (`OpKind::Binary`) —
`dict.update`/`{**a, **b}` semantics: `b`'s value wins on a key collision,
`a`'s entries are kept where `b` has no matching key. **The 3-way merge task
87 needs is NOT a new arity** — it composes by nesting, the identical
`ConcatList(ConcatList(a,b),c)` shape task 108's own witness already uses in
this same arc. Verified directly against task 87's real fixture rows
(`tests/fixtures/mbpp/sanitized-mbpp.json`, not assumed from the prompt
text): all three revealed asserts show the FIRST argument's value winning
every key collision (e.g. `dict1={"B":"Black",...}`, a later dict's
`"B":"Blue"` never survives) — i.e. `dict1` outranks `dict2` outranks
`dict3`, matching `DictMerge(DictMerge(dict3, dict2), dict1)` under the
`b`-wins convention (dict1 applied LAST, so it wins every conflict). This
was checked against the actual assert strings, not inferred from the
prompt's English description alone. Non-Dict-Dict input degrades to `a`
unchanged (never panics; the standing degrade convention for a
type-mismatched binary operand in this file).

Registered exactly like `Sort`/`DictItems`/`SortBy` landed
(`runners/dsl/src/synth_enumerate.rs`): `OP_TABLE` entries, `build_op`
cases, `term_json` cases. Six exhaustive-match sites elsewhere in the engine
needed the same two new arms (found by `cargo check`, not grepped blind —
`term_variants.rs` regenerated via `tools/gen_term_variants.py`, `reflect.rs`
×2 [`describe`/`from_json`-style reader], `jsonio.rs` ×3
[`variant_name`/`write_fields`/read-back]) — every site mirrors its
`DictItems`/`SortBy` precedent exactly.

**Evidence gating (never a blanket `OP_TABLE` append — Rung 1's own first
attempt at that regressed 5 tasks via budget exhaustion, the risk this
rung's own brief named explicitly):**

- New flag `spec_output_is_dictlike` (`!outputs.is_empty() &&
  outputs.iter().all(is_dict_val)`) — the OUTPUT-shape twin of
  `spec_has_dict_value` (which is INPUT-variable-shape only), mirroring the
  already-measured-safe `spec_output_is_listlike`/`spec_output_is_setlike`
  discipline exactly.
- Task 88 is list-shaped (`a` is a `List`, so `spec_is_list_shaped` is
  already true and this spec reaches the existing list-shaped typed-default
  branch) — `GroupCount` is pushed into that branch's op list ONLY when
  `spec_output_is_dictlike`, the same narrow output-type-only gate
  `Sort`/`Split`/`ParseInt` already use in that same branch. `DictMerge` is
  deliberately NOT added there (no live witness needs it under that
  evidence).
- Task 87 has THREE Dict-shaped variables and a Dict-shaped output, no
  list-shaped variable anywhere — `spec_is_list_shaped` is FALSE for it
  (`is_listlike` deliberately excludes Dict, the same exclusion
  `spec_has_dict_value`'s own doc comment already names), so it would
  otherwise fall through to the bare arithmetic `DEFAULT_OPS` bucket and
  never see either new op. A new, narrow, dedicated bucket —
  `DICT_DEFAULT_OPS = ["Eq", "IfThenElse", "GroupCount", "DictMerge"]` —
  is offered via a new `else if spec_output_is_dictlike` branch, positioned
  AFTER the list-shaped branch (so task 88's own routing is completely
  unchanged) and BEFORE the final bare-arithmetic fallback. This mirrors
  `SET_DEFAULT_OPS`'s own precedent exactly: a shape that isn't
  "list-shaped" gets its own small dedicated bucket, never layered onto the
  much larger list-shaped default.

**Regression risk, priced before building:** per §3, no currently-PASSING
task has Dict-shaped output or an all-Dict-shaped variable set (this rung's
own §3 sweep covers only currently-FAILING tasks; a dedicated canary check
against the pass set is run post-build, in the RESULTS document, not
assumed safe here). The new `DICT_DEFAULT_OPS` branch can only ever fire for
a spec that was previously routed to bare `DEFAULT_OPS` (arithmetic-only,
the narrowest bucket in the file) AND has all-Dict-shaped output — a
strictly ADDITIVE widening of what such a spec's search considers, never a
narrowing of any other bucket.

## 5. What this rung does NOT attempt

- Task 97 (needs `GroupCount` + a flatten primitive) and task 283 (needs
  `GroupCount` + `Recurse`, already NO-GO'd) — both re-confirmed NOT
  convertible by `GroupCount` alone, per ARC6's own original "alone 1,
  necessary for 2" distinction. Not built here.
- The `FilterDict`-shaped gap (tasks 465, 277) and the nested-dict-construct
  gap (task 391) — different primitives, not `GroupCount`/`DictMerge`,
  named not built.
- Tasks 19/130/168 — checked directly (§3) and found NOT to share the
  `SortBy`/task-12 "widening one op's availability silently changes a
  DIFFERENT `retrieved_exemplar` hole-fill" mechanism; their own recorded
  hole-fill/construction lanes don't reference Dict construction at all.
  This is reported as a checked-and-ruled-out finding, not an assumption —
  the ACTUAL after-build battery diff (RESULTS §5) is the real confirmation,
  not this reasoning alone.

## Reproduce

```bash
cd /home/matt/ozmadev/ocelot-worktrees/progsyn-groupcount-dictmerge
git log --oneline -1   # on top of main @ c5aea7b
bash scripts/engine_build.sh   # then: python3 domains/engine_provenance.py (build script's `python` call needs python3 on this machine)
PYTHONPATH="runners/dsl/python:.:scripts" OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 \
  python3 scripts/mbpp_endgame_battery.py
PYTHONPATH="runners/dsl/python:.:scripts" OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 \
  python3 scripts/ceiling3_diag_sweep.py
```
