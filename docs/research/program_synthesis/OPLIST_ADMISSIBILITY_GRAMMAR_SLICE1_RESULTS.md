# Opgrammar first slice: a Γ parity check for the `SortBy` op-list gate — RESULTS

Design docs this rung builds (no new PREREG — both already specify this
slice precisely, per this session's own instruction):
`OPLIST_ADMISSIBILITY_GRAMMAR_PREREG.md`, `OPLIST_ADMISSIBILITY_GRAMMAR_
RESULTS.md` (§8's own buildable first slice), and `DERIVED_OPERATOR_TIER_
RESULTS.md` (its correction of the design doc's own op-count citation).

Base `main @ c1d0b4c` ("Merge progsyn-groupcount-dictmerge: two new stdlib
Terms + a real wire fix, MBPP 67->69"), verified via `git log --oneline -1
main` immediately before creating the worktree, and reconfirmed unchanged
(`c1d0b4c`) at the end of this session. Worktree:
`/home/matt/ozmadev/ocelot-worktrees/oplist-admissibility-grammar-slice1`,
branch `oplist-admissibility-grammar-slice1`, commit `d7f5f26` — **not
merged to `main`, not pushed**, left for the orchestrator to independently
verify and merge, per this session's explicit instruction not to repeat the
earlier direct-merge violation.

**Headline: GO, built exactly the scoped first slice, zero regressions,
zero new passes (as expected and correct for a parity slice). The op-list
boolean gate ladder's `SortBy` pair is now ALSO admitted by a real,
enforced Γ path (`is_edge_admissible` → `ConsistencyChecker::check_edge`),
running alongside the existing hand-written Rust ladder, and live-verified
on real MBPP tasks 64/475/2 to produce the IDENTICAL admission answer the
ladder already produces. Both prior op-count citations (the design doc's
"31", `DERIVED_OPERATOR_TIER_RESULTS.md`'s own correction to "50") are
stale a second time — the real, live-counted `OP_TABLE` population is
now 52.**

---

## 1. Re-derived, live: the real current gate population and `OP_TABLE` size

`OP_TABLE` (`runners/dsl/src/synth_enumerate.rs:289-381`, read in full and
counted programmatically — `sed -n '289,381p' ... | grep -c '^\s*("'`):
**52 entries**, not the design doc's original "31" (predates `DictItems`/
`SortBy`) and not `DERIVED_OPERATOR_TIER_RESULTS.md`'s own "50" correction
(predates the just-merged `progsyn-groupcount-dictmerge` rung, which this
worktree branches from). The two newest entries are `GroupCount`
(`OpKind::Unary`) and `DictMerge` (`OpKind::Binary`), added at lines
379-380 with their own module-doc comment block citing
`PROGRAM_SYNTHESIS_GROUPCOUNT_DICTMERGE_PREREG.md`. **This document's own
designs and sizing below use 52** — every prior citation of "31" or "50"
in this arc's earlier documents is superseded, and this correction should
itself be treated as a snapshot at `main @ c1d0b4c`, not a permanent number
(the pattern that made the prior two citations stale is structural, not a
one-off mistake — `OP_TABLE` grows every time a stdlib-port rung lands).

The two real `SortBy` gates, re-read at their CURRENT line numbers (moved
since both cited docs, per the widened `SortBy` gate + the `GroupCount`/
`DictMerge` rung both editing this file since):

- `spec_has_dict_value` (`synth_enumerate.rs:1846`, def) →
  `v.push("SortBy")` at **line 2034** (inside `if spec_has_dict_value {
  v.push("DictItems"); v.push("SortBy"); v.push("Reverse"); }`,
  lines 2032-2036) — the original, task-475 gate.
- `spec_has_list_of_lists && !spec_has_dict_value` (flag def
  `synth_enumerate.rs:1895`) → `v.push("SortBy")` at **line 2055** (`if
  spec_has_list_of_lists && !spec_has_dict_value { v.push("SortBy"); }`,
  lines 2054-2056) — the CEILING_REASSESSMENT_3 widening, task-64's gate.

Both gates read EXACTLY as `OPLIST_ADMISSIBILITY_GRAMMAR_RESULTS.md` §1.1
described them (line numbers moved, semantics byte-identical) — confirmed
by reading the live source, not inherited from the design doc's citation.

---

## 2. What was built — the four slice items, each exactly as scoped

### 2.1 Item 1 — duplicated evidence flags in Python, tradeoff documented

`domains/prog_synthesis.py::_synth_spec_shape_flags` (new function,
`prog_synthesis.py:1179-1290` in the committed tree) is FORK (a) from
`OPLIST_ADMISSIBILITY_GRAMMAR_RESULTS.md` §7's own named tradeoff table —
a second, independently-maintained copy of the ten evidence-flag
predicates (`has_dict_value`, `has_list_of_lists`, `has_string_value`,
`has_float_value`, `has_repeated_list_element`, `output_is_listlike`,
`output_is_setlike`, `output_is_bare_int`, `is_string_shaped`,
`is_list_shaped`), operating on RAW (pre-`_wire`) Python container values
so `isinstance` reads the same container kind Rust's `Value` enum decodes.
The function's own docstring names the tradeoff explicitly, cites the
Rust source of truth (`synth_enumerate.rs`'s `is_listlike`/`items_of`/the
evidence-flag block, with line numbers), and cross-references
`_examples_numeric_eligible` (line 449) as the SAME "own copy, no
cross-import" duplication idiom already used elsewhere in this file —
mirroring exactly how every other such duplication in this codebase
documents itself, per the task's own instruction. Fork (b) (expose the
Rust computation via a new PyO3 method) is explicitly NOT attempted —
zero `.rs` files are touched by this slice.

### 2.2 Item 2 — `SynthSpecShape` node type + the static `SynthOp` population

`seeds/program_synthesis_opgrammar.json` (new seed, `depends_on:
["program_synthesis"]`, loaded via the standard `load_seed_manifest` path
— `ensure_program_synthesis_opgrammar`, `prog_synthesis.py:1164-1176`,
called from `ensure_program_synthesis` alongside every other seed it
installs) mints **52 static `SynthOp{name}` nodes, one per real, live
`OP_TABLE` entry** (§1), in `OP_TABLE`'s own order. `SynthSpecShape` is
the OTHER new node type this slice introduces — it carries NO
seed-authored nodes (unlike `SynthOp`, it is minted LIVE, one per
`run_enumerate` call, exactly per the design doc's own §8 step 2 scoping:
"not deduped yet — dedup is a §6.2 optimization, not a correctness
requirement for a first slice"). Both are genuine new node types with
their own seed/registration — mirroring how `ProblemShape`/
`DirectionalCorrespondence` were scoped in this arc (real node types, not
attrs overloaded onto an existing type), confirmed by reading both
precedents' own seed JSON before building this one.

Verified live (`tests/test_opgrammar_migrated.py::
test_opgrammar_seed_installs_52_synthop_nodes_and_is_idempotent`): 52
distinct `SynthOp` names install on boot, the seed marker is idempotent
(a second `ensure_program_synthesis_opgrammar` call mints no duplicate
population).

### 2.3 Item 3 — exactly the two SortBy productions, hand-authored

`seeds/program_synthesis_opgrammar.json`'s `"productions"` array carries
EXACTLY two `Production`s (`grammar.rs:31-39`'s real shape, JSON syntax
cited from the real, shipped `seeds/abusive_u0_intent.json` precedent,
`where`/`weight` Term-JSON per `jsonio.rs::grammar_from_json`, read in
full before writing either production):

```json
{
  "provenance": "program_synthesis_opgrammar:sortby_dict_gate",
  "src": {"type": "SynthSpecShape", "var": "spec"},
  "edge_type": "admits_op",
  "tgt": {"type": "SynthOp", "var": "op"},
  "where": {"type": "And", "items": [
    {"type": "Eq", "a": {"type": "Attr", "node": {"type": "Var", "name": "op"}, "key": "name"},
               "b": {"type": "Lit", "value": "SortBy"}},
    {"type": "Eq", "a": {"type": "Attr", "node": {"type": "Var", "name": "spec"}, "key": "has_dict_value"},
               "b": {"type": "Lit", "value": true}}
  ]}
}
```

and the second, structurally identical but for `has_list_of_lists` plus a
`Not(has_dict_value)` conjunct (see the seed file for the full JSON — both
productions share `(src_type=SynthSpecShape, edge_type=admits_op,
tgt_type=SynthOp)`, so Γ's own OR-of-admitting-productions semantics
IS the disjunction the Rust `if`/`if ... && !...` ladder encodes today,
exactly as the design doc predicted).

**One implementation refinement over the design doc's own illustrative
pseudocode, made necessary by reading `production_admits`
(`checker.rs:108-130`) closely, and recorded here because it changes WHERE
the op-specificity lives.** §3.2 of the design doc sketched `where_` as
testing only the SRC's evidence flags (`Eq(Attr(spec, "has_dict_value"),
1)`), with `tgt: SynthOp{name: "SortBy"}` read as if the node PATTERN
itself pinned the name. It does not: a `NodePattern` matches by TYPE only
(`grammar.rs:20-26`), never by attrs — `Production.tgt = {type: "SynthOp",
var: "op"}` matches ANY `SynthOp` node, not specifically the one named
`"SortBy"`. Read against `checker.rs`'s real env-binding
(`production_admits` binds `{src.var: src, tgt.var: tgt}` and evaluates
`where_` against BOTH), the correct, faithful port adds an explicit
`Eq(Attr(op, "name"), Lit("SortBy"))` conjunct to each production's
`where_` — this is what makes the production admit `SortBy` SPECIFICALLY
and nothing else (verified: `test_gamma_never_admits_a_different_op_no_
matter_the_flags` confirms `Plus`/`Sort`/`DictItems`/`Reverse`/
`GroupCount` are never admitted by either production regardless of which
evidence flags are set — no production anywhere names them). This also
means BOTH productions reference `tgt` in their `where_`, so
`is_edge_admissible` always takes its documented "slow path" (materialise
a scratch node with the candidate's `(type, attrs)`, run `check_edge`,
delete it — `substrate.rs:1835-1848`) for this pair, not the src-only fast
path the design doc's §4 also described as available for tgt-unreferenced
productions. This is the CORRECT, real-Γ-enforced behaviour (per the
same §4 finding: it calls into `ConsistencyChecker::check_edge`, not a
decorative shortcut) — noted here as a genuine, load-bearing correction of
the design doc's own illustrative shorthand, not a deviation from its
intent.

A second, minor implementation choice: the design doc's pseudocode used a
numeric `1`/`0` for the boolean flags; this build uses native JSON
`true`/`false` (`Value::Bool` on the Rust side, confirmed via
`persist.rs::decode_value`), because `Eq`'s real evaluator
(`term.rs::eq_with_string_coercion`) does exact variant-and-payload
equality with NO int↔bool coercion — a `1` literal would never equal a
`Value::Bool(true)` attr. Functionally identical intent, a materially
different literal choice; recorded so a future reader comparing this
seed's JSON against §3.2's prose does not read it as a drift.

### 2.4 Item 4 — wiring `run_enumerate` through `is_edge_admissible`

The design doc's own citation (`prog_synthesis.py:1180-1186`) has moved;
the real transcription branch is now `run_enumerate`
(`prog_synthesis.py:1293` onward), `spec["ops"]` populated from
`graph_ops` at **lines 1369-1376**. This slice's wiring sits BEFORE that
branch, in the SAME function, right after the `rows`/`raw_rows` loop
(`prog_synthesis.py:1327-1341`) and right before `spec["ops"]` is built
(`1342-1360`):

1. The SAME `has_example` rows already being transcribed into `rows`
   (wired) are ALSO collected raw (pre-`_wire`) into `raw_rows`.
2. `_synth_spec_shape_flags(raw_rows)` computes the ten flags.
3. `sub.add_node("SynthSpecShape", spec_shape_flags)` mints one node.
4. `sub._inner.is_edge_admissible(spec_shape_node, "admits_op", "SynthOp",
   {"name": "SortBy"})` is called — the exact PyO3 probe
   `OPLIST_ADMISSIBILITY_GRAMMAR_RESULTS.md` §4 cites
   (`py.rs:7922-7937`, confirmed calling `ConsistencyChecker::check_edge`
   via `Substrate::is_edge_admissible`, `substrate.rs:1789-1848`).
5. The verdict is recorded as `ps_enum_gamma_sortby_admitted` on the Goal
   node `g` (a fact, `sub.set_attr`) — **never consulted for
   `spec["ops"]` construction**, which is completely unchanged below it.
   An exception (none observed in any run) is caught and recorded
   separately (`ps_enum_gamma_sortby_error`) rather than propagated, so a
   Γ-path failure can never break a battery run — but it also never
   silently succeeds: the parity test asserts the error attr is absent.

This satisfies the task's own instruction precisely: the Γ path runs
ALONGSIDE the existing hand-written gate, is provably never consulted
for production op selection (confirmed by reading the diff: the
`spec["ops"]` block, lines 1364-1376, is byte-identical to `main @
c1d0b4c` except for the pre-existing surrounding code shifting down),
and its own verdict is independently recorded for comparison.

---

## 3. Live demonstration — the two positive witnesses and the discriminating negative

All three cases below call `run_enumerate` DIRECTLY on a Goal built from
REAL rows out of `tests/fixtures/mbpp/sanitized-mbpp.json` (the same
fixture the 9-file regression suite uses), with `ps_enum_round` bumped so
the round-guard does not skip the call, and with **no explicit `ops`** set
on the Message (`ps_enum_ops` confirmed empty for every one of these three
prompts — the `SynthesisOperatorShape` NL classifier never fires for
them), so the Rust hand-written ladder's own DEFAULT decides the op
inventory — exactly the ladder this slice's two Γ productions mirror.
(Note: running these three tasks through the FULL `synthesize_from_request`
pipeline resolves tasks 64/475 via `retrieved_exemplar` before
`SynthEnumerate` is ever reached, per `PROGRAM_SYNTHESIS_CEILING_
REASSESSMENT_3_RESULTS.md` §3.2's own prior finding — `run_enumerate` is
called directly here, the same way `tests/test_prog_repair_migrated.py::
test_run_enumerate_threads_hole_scope_exclude_into_the_engine` already
does, specifically so the Rust ladder's own SortBy decision is actually
exercised.)

| task | prompt (truncated) | revealed rows (shape) | `ps_enum_gamma_sortby_admitted` | winning term uses `SortBy`? |
|---|---|---|---|---|
| **64** | "sort a list of tuples using the second value of each" | `a: List[Tuple]` — no dict, list-of-lists (Tuple counts as list-like) | **True** | **True** — `SortBy(a, __item, Sort(__item))` |
| **475** | "sort a dictionary by value" | `a: Dict` | **True** | **True** — `Reverse(SortBy(DictItems(a), __item, Sort(__item)))` |
| **2** (negative control) | "find the shared elements from the given" | `a, b: Tuple` (flat, no dict, no nested lists) | **False** | **False** — winning term is `Intersect(a, b)` |

Task 2 was chosen as the discriminating negative by scanning the real
corpus for a task that (a) is currently ACCEPTED end-to-end via the full
`synthesize_from_request` pipeline (a genuinely currently-passing task,
per the task brief's own requirement) and (b) has neither
`has_dict_value` nor `has_list_of_lists` true — confirmed directly via
`_synth_spec_shape_flags` on its real revealed rows before being used as
the control.

Reproduce (`tests/test_opgrammar_migrated.py::
test_live_demonstration_gamma_matches_the_real_ladder`, parametrized over
all three task ids — this table's own source):

```bash
cd /home/matt/ozmadev/ocelot-worktrees/oplist-admissibility-grammar-slice1
PYTHONPATH="runners/dsl/python:.:scripts" OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 \
  python3 -m pytest tests/test_opgrammar_migrated.py -q
```

---

## 4. MBPP battery — confirmed unchanged, exact task-id set-diff empty

Ran the full 257-task, three-arm battery on this worktree's committed
state (`d7f5f26`):

```
full:              69/257  p=0.268482  ci=[0.218003, 0.325781]  det_identical=True
content_stripped:  68/257  p=0.264591  ci=[0.214414, 0.321702]  det_identical=True
official:          98/257  p=0.381323  ci=[0.324101, 0.44204]   det_identical=True
```

**Byte-identical to the pre-existing baseline** this worktree branches
from (`PROGRAM_SYNTHESIS_GROUPCOUNT_DICTMERGE_RESULTS.md`'s own final
measurement at `main @ c1d0b4c`: `full`/`content_stripped`/`official` =
69/68/98) — exactly the expected, correct outcome for a pure parity slice
(§9's own scoping: this slice proves the plumbing is transparent, it does
not attempt to move the score). Independently confirmed by an EXACT
task-id set-diff, not just the aggregate count: comparing the
`results/mbpp_endgame.json` this worktree's own battery run just produced
against the ALREADY-COMMITTED `results/mbpp_endgame.json` sitting at
`main`'s HEAD in the primary tree (both descend from the same `main @
c1d0b4c` state) —

```
full:              added=[]  removed=[]  (120/120 accepted-status task ids identical)
content_stripped:  added=[]  removed=[]  (112/112 accepted-status task ids identical)
official:          added=[]  removed=[]  (100/100 accepted-status task ids identical)
```

zero regressions AND zero new passes on every arm, at the task-id grain,
not merely the aggregate count.

---

## 5. Regression discipline

**Rust suite** (`cargo test --lib --release -- --test-threads=1`, engine
rebuilt from source at the start of this session — `data/` re-symlinked
and verified, `data/wiktionary/en.jsonl.gz` resolves to the real 492MB
file; `runners/dsl/python/substrate_rs/_native.abi3.so` restored to the
COMMITTED `main @ c1d0b4c` binary afterward, since this slice makes ZERO
`.rs` changes — `git diff --stat -- runners/dsl/src/` is empty for the
entire duration, confirmed at both the start and end of this session, so
rebuilding and re-committing a binary that only differs by build
non-determinism would be pure noise): **774 passed; 0 failed; 4 ignored**
(the documented `dim_infer_tests` flakes) — both before touching any
Python/JSON in this slice and again after, byte-identical.

**Named 9-file suite.** First attempt was CONTAMINATED by running it
CONCURRENTLY with the full MBPP battery — both write to the same
`results/mbpp_endgame.json` path, the exact "shared mutable output path"
fragility this arc's own prior documents (`CEILING_REASSESSMENT_3_
RESULTS.md` §6, `GROUPCOUNT_DICTMERGE_RESULTS.md` §7) already name and
warn about; that run showed 17 spurious errors in
`test_mbpp_endgame_migrated.py` and is discarded rather than reported. A
clean, SEQUENTIAL re-run (battery finished first, then the suite alone):

```
3 failed / 241 passed in 189.89s
FAILED tests/test_mbpp_baseline_migrated.py::test_three_runnable_tasks_reverify_live
FAILED tests/test_prog_moves_migrated.py::test_named_regression_sweep_only_known_pins_drift
FAILED tests/test_exact_first_migrated.py::test_named_regression_sweep_only_known_pins_drift
```

**Exact match, same three test names**, to the ALREADY-DOCUMENTED
pre-existing "shared mutable output path" fragility
(`PROGRAM_SYNTHESIS_GROUPCOUNT_DICTMERGE_RESULTS.md` §7, itself confirmed
there against an independently-reverted clean `main @ c5aea7b` build) —
not caused by this slice, reconfirmed live rather than assumed from
citation.

**New tests**: `tests/test_opgrammar_migrated.py`, 13/13 passed — seed
install + idempotency (1), the two Γ productions probed directly on
hand-built `SynthSpecShape` flag combinations covering both gates, their
union, and the "never admits a different op" discriminator (5),
`_synth_spec_shape_flags` unit checks (4), and the live demonstration
parametrized over real tasks 64/475/2 (3, folded into §3's table above).

```bash
cd /home/matt/ozmadev/ocelot-worktrees/oplist-admissibility-grammar-slice1
PYTHONPATH="runners/dsl/python:.:scripts" OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 \
  python3 -m pytest tests/test_opgrammar_migrated.py -q
PYTHONPATH="runners/dsl/python:.:scripts" OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 \
  python3 -m pytest tests/test_prog_synthesis_battery_migrated.py tests/test_mbpp_baseline_migrated.py \
  tests/test_mbpp_endgame_migrated.py tests/test_mbpp_contamination_migrated.py tests/test_mbpp_diet_migrated.py \
  tests/test_program_synthesis_migrated.py tests/test_prog_moves_migrated.py tests/test_prog_property_migrated.py \
  tests/test_exact_first_migrated.py -q
PYTHONPATH="runners/dsl/python:.:scripts" OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 \
  python3 scripts/mbpp_endgame_battery.py
```

---

## 6. GO/NO-GO

**GO.** Built exactly the four-item first slice `OPLIST_ADMISSIBILITY_
GRAMMAR_RESULTS.md` §8 scoped, no more: duplicated evidence flags
(documented liability), the `SynthSpecShape`/`SynthOp` node types (52
static ops, live-minted spec-shape nodes), exactly the two `SortBy`
productions, and `run_enumerate` wired through `is_edge_admissible`
alongside the untouched Rust ladder. The live demonstration confirms
Γ produces the IDENTICAL admission answer the existing hand-written gate
produces on two real positive witnesses (tasks 64, 475) AND one real
discriminating negative (task 2) — not merely two positive matches. The
MBPP battery is confirmed byte-identical (69/68/98, exact task-id
set-diff empty on every arm) both before and after, exactly the expected
and correct outcome for a parity slice, not a capability-gain rung.

---

## 7. What this document does NOT establish

1. **The mint sweep is NOT this rung.** §6 of the design doc (the offline
   sweep over the 99-task `gapped:enumerate_failed` population, minting
   new Productions from verified forced-op witnesses) was not attempted —
   explicitly out of scope, per the task brief and the design doc's own
   §8 step 5 separation.
2. **No gate besides `SortBy`'s two was converted.** The other ~48
   evidence-gate sites in §1.1/§1.2 of the design doc (string-shaped
   defaults, list-shaped defaults, `Round`/`Split`/`ParseInt`/
   `IndexedMap`/`GroupCount`/`DictMerge` evidence gates, the
   `map_templates_by_size` per-element template pool) remain exactly as
   hand-written `if` statements as before this slice — untouched, and the
   Rust ladder remains the sole PRODUCTION-BEHAVIOR authority for every
   one of them (and, in fact, for `SortBy` too — see next point).
3. **Production behaviour is unchanged.** The Γ verdict is recorded as a
   fact for comparison; it is NEVER consulted when constructing
   `spec["ops"]`. The MBPP battery moving zero tasks is not incidental —
   it is the direct, structural consequence of this scoping choice, not
   evidence that Γ "doesn't work" (§3's live demonstration shows it does).
4. **The evidence-flag duplication (fork (a)) is a standing, tracked
   liability**, not resolved by this slice — if `eval_synth_enumerate`'s
   flag predicates ever change, `_synth_spec_shape_flags` must be updated
   by hand; there is no automatic sync, and no test in this repo enforces
   one. A future rung could close this via fork (b) (a new PyO3 method
   exposing the Rust computation) — not attempted here, zero `.rs` changes
   is this slice's own explicit constraint.
5. **`SynthSpecShape` nodes are not deduplicated.** One is minted per
   `run_enumerate` call (every round, every retry) — exactly the design
   doc's own §8 step 2 scoping ("not deduped yet — dedup is a §6.2
   optimization, not a correctness requirement for a first slice"). A
   production battery run at scale would accumulate one `SynthSpecShape`
   node per enumerate attempt; this was not sized or measured as a growth
   concern in this slice (out of scope — the design doc's own §7 cost
   table only prices the mint-sweep's cost, not this).
6. **The op-count "52" is itself a snapshot**, not a permanent fact —
   named explicitly in §1 as the third instance of the same staleness
   pattern that affected the design doc's "31" and `DERIVED_OPERATOR_
   TIER_RESULTS.md`'s "50". Any future rung that reads an op-count from a
   document rather than re-deriving it from live source risks repeating
   this exact defect a fourth time.
