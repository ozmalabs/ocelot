# Delim-join primitive + budget-wall root cause — RESULTS

**Date:** 2026-08-15. Base `main @ fa5b659`, verified fresh immediately
before creating the worktree. Built and measured in an isolated worktree
(`/home/matt/ozmadev/ocelot-worktrees/progsyn-delimjoin-budgetwall`, branch
`progsyn-delimjoin-budgetwall`) — **not merged to `main`**, left for the
orchestrator. Baseline re-verified fresh in-worktree before any change:
`full` 66/257, `content_stripped` 65/257, `official` 94/257 (byte-identical
to `PROGRAM_SYNTHESIS_MAP_TEMPLATE_POOL_RESULTS.md`'s own headline).

**Headline: BOTH items land NO-GO, honestly and for different, fully
diagnosed reasons — a real Rust op was built and empirically validated for
Item 1 and then reverted (semantically correct, but unreachable by exactly
one search-size level under production settings, and even relaxing the
ceiling does not safely convert it); a narrow, provably-safe reorder was
built and measured for Item 2 and reverted (measured: does not convert its
target). Zero code changes are retained. The full 257-task battery was
re-run after reverting and reproduces the baseline exactly — set-diff
confirms `before_pass == after_pass` on all three arms, zero regressions,
zero new passes.**

---

## Item 1 — task 421's delimiter-join primitive

### 1.1 Composition finding: confirmed zero-new-`TermNode`

`JoinList` (`synth_enumerate.rs:571-577`) is `Fold{source, init:Lit(""),
body:Concat(acc,item)}` — a FIXED empty-string join, no separator slot.
Built and validated (then reverted) `op:JoinListSep`, a fused single-op
`sep.join(str(x) for x in items)`:

```rust
fn build_list_join_sep(source: TermIdx, sep: TermIdx, item: Sym, acc: Sym,
                        scratch: &mut TermArena) -> TermNode {
    let init = scratch.add(TermNode::Lit { value: surf("") });
    let accv = scratch.add(TermNode::Var { name: acc });
    let itemv = scratch.add(TermNode::Var { name: item });
    let body = scratch.add(TermNode::Cat { items: vec![accv, sep, itemv] });
    let joined = scratch.add(TermNode::Fold { source, var_name: item, acc_name: acc, init, body });
    let sep_len = scratch.add(TermNode::Count { source: sep });
    let big_stop = scratch.add(TermNode::Lit { value: Value::Int(1_000_000_000) });
    TermNode::Slice { seq: joined, start: sep_len, stop: big_stop }
}
```

Built UNIFORMLY (`sep` prefixed before every element, including the first),
then the single spurious leading separator is trimmed off in ONE `Slice`
call — cheaper than a first/rest split (measured both; first/rest costs
9-10 fixed nodes, this costs 7). Every node is an already-shipped, already-
pure Term (`Fold`/`Cat`/`Count`/`Slice`/`Lit`/`Var`) — **zero new
`TermNode` variants**, matching the `Sort`/`SetMap`/`Union` precedent
exactly. This required a new `OpKind::ListJoinSep` variant and registration
arm in `synth_enumerate.rs` (list-shaped source × general `by_size`
separator, the `ListMap` cross-product shape) — new Rust CODE in
`synth_enumerate.rs`, but zero touches to `term.rs`'s evaluator dispatch,
`copy_subtree`/children collector, `term_variants.rs` regeneration,
`jsonio.rs`, or `reflect.rs` — the SAME class of change every prior
primitive-adding rung in this arc made (including the very rung this one
continues).

**Two dead ends found and ruled out along the way (both checked directly
against `term.rs`'s own `evaluate()`, not assumed from the type
signature):**
- `TermNode::StringSlice{s,start,end}` requires `Value::Str` EXACTLY
  (`term.rs:4982-4997`) and returns empty on `Value::Surface(Text,_)` —
  the type `StringConcat`/`Cat` actually produce. Using it here would
  silently produce an empty string on every candidate, never matching.
- `TermNode::ProgSlice{obj,start,stop,step}` has NO case in `term.rs`'s
  own `evaluate()` (`term.rs:6276-6281`: falls through to `Value::None`
  for every `Prog*` node) — it is a `prog_eval.rs`-only Term, evaluated by
  a DIFFERENT interpreter never reached from `SynthEnumerate`'s search.
  Confirmed by reading both `evaluate()` functions directly.

The general `Slice{seq,start,stop}` Term (`term.rs:5157-5193`) is the
correct primitive: it handles `Value::Surface(Text,_)` natively and clamps
an out-of-range `stop` to the sequence length
(`prog_eval::slice_indices`), so a large literal sentinel gives "to the
end" with zero extra `Count` node.

### 1.2 Reachability finding: floor is size 10, ceiling is 9 — by exactly one

Honest MDL accounting (`list_unary_extra_cost`'s own documented
convention, "size = 1 + extra + source_size"): `build_list_join_sep`
injects **7** fixed nodes beyond `source`/`sep`
(`init`+`accv`+`itemv`+`body`/`Cat`+`joined`/`Fold`+`sep_len`/`Count`+
`big_stop`/`Lit` = 7). Minimum size at `sa=1` (a bare list variable),
`sb=1` (a bare `Lit` separator): `size = 1(Slice) + 7(extra) + 1 + 1 = 10`.
Production's `max_size` is **9** (`domains/prog_synthesis.py::run_enumerate`,
hardcoded `"max_size": 9`) — **this construction can NEVER register for
ANY spec under production settings, one size level short, universally, not
just for task 421.**

Tried an alternative (conditional, `IfThenElse(Eq(acc,""), Cat([item]),
Cat([acc,sep,item]))` instead of uniform-prefix-then-trim) specifically to
avoid the `Slice`/`Count` trim machinery: also converges on extra=7 by an
independent route (no `Slice`/`Count` needed, but `Eq`/`IfThenElse`/two
separate `Cat` bodies cost the same). Two independently-designed
constructions landing on the identical extra=7 floor is reasonably strong
evidence this is close to the true minimum achievable via this Term
inventory, not an artifact of one particular design choice.

Live-verified (before reverting): task 132 (`''.join(tup1)`, this file's
own long-standing canary for exactly this class of widening) is
**completely unaffected** — `JoinListSep`'s gate
(`!spec_output_is_listlike && spec_has_string_value &&
!spec_has_string_list_elements`) provably excludes it (132's elements are
all already string-typed, so `spec_has_string_list_elements` is true for
it and the gate never fires), and it still solves via `JoinList` exactly
as before (`tested:40357, distinct:187, size:6`, byte-identical to
pre-change). Task 421 itself: `tested:200000, distinct:618,
halt_reason:"budget"` — **unchanged from before the op was added**,
confirming the op genuinely never registers under `max_size:9` (dead code
under production settings, exactly as the floor arithmetic predicts).

### 1.3 Diagnostic-only max_size=10 probe: relaxing the ceiling does not safely convert 421 either

To check whether Item 1's gap is PURELY a one-size-level reachability
problem (in which case a narrow, task-scoped depth increase might be
worth pricing), ran task 421 at `max_size:10` with a large uncapped
candidate budget, diagnostic-only (never changing the production default).
Result: `found:True, size:10` — but the accepted term is
`(if ('s' > [lower(item) for item in a][-1]) then 'QWE-is-4-RTY' else
'ID-is-4-UTS')` — **a spurious few-shot memorization of the two revealed
rows' literal output strings**, the exact same failure MODE Item 2 found
independently (§2.3 below), just reached via a different op combination
(string comparison over a lowered last element, not `Eq`-to-a-whole-tuple).
`JoinListSep` is appended LAST in `op_list` (this file's own "always
append, never interleave" discipline, `LIST_EXTRA_OPS`'s own doc comment)
— under the CURRENT op ordering, this spurious `IfThenElse`/`Gt`
construction, built from ops near the FRONT of `DEFAULT_OPS`, wins the race
at size 10 regardless. **Relaxing `max_size` for this spec, even if it
were otherwise cheap and safe, would not convert 421 to a genuine pass —
it would just return a different wrong answer.** This is the same
conclusion Item 2 reaches independently and is decisive by itself,
independent of the size-floor arithmetic in §1.2.

### 1.4 GO/NO-GO — Item 1

**NO-GO, built and reverted.** Composition is confirmed genuinely
zero-new-`TermNode` (a real, positive finding, kept for the record). The
leanest achievable fused construction (two independently-designed variants
converging on the same floor) needs size ≥10, one level past this file's
own `max_size:9` ceiling — universally unreachable under production
settings for any spec, not solvable by narrowing the gate further (the
floor is a property of the op's own fixed structure, not the task). And
the diagnostic max_size=10 probe shows that even relaxing the ceiling
would not rescue task 421 specifically — a different spurious
memorization wins the race first. Reverted cleanly (`git checkout --
runners/dsl/src/synth_enumerate.rs`), zero code retained. No other task in
the fixture benefits (§ Item 1's own PREREG bonus-conversion search:
421 is the sole candidate for a real non-empty-separator, heterogeneous-
element join).

---

## Item 2 — the budget wall for 102/411/419/439

### 2.1 Dedup is not the problem — confirmed, not assumed

`register_kind` (`synth_enumerate.rs:1546-1568`) increments `self.tested`
**before** checking `self.seen.contains(&sig)` — every candidate, whether
genuinely new or an observationally-equivalent duplicate, consumes exactly
1 unit of the 200,000-candidate budget. Measured directly for all four
canary tasks: `pruned_equiv` accounts for ~91-92% of `tested`
(e.g. 439: `tested:200000, distinct:17839` → ~178K pruned as duplicates).
**Dedup already exists, is already correct, and by design cannot recover
this budget** — it only avoids re-storing an already-seen behavior as a
future building block. This was checked and ruled out BEFORE any fix was
attempted, per the PREREG's stated order.

### 2.2 A narrow, provably-safe reorder was built, measured, and did not convert its target

`ParseInt`'s own gate (`!spec_output_is_listlike && spec_output_is_bare_int
&& !spec_has_string_value && !spec_has_float_value`) is PROVABLY mutually
exclusive with every op between its old position and the front of the
list-shaped branch's `v` (`TUPLE_BUILD_OPS`/`Sort`/`Split` all require
`spec_output_is_listlike`; `Round` requires `spec_has_float_value` — both
negated by `ParseInt`'s own gate). Hoisting `ParseInt` to run FIRST (before
`DEFAULT_OPS`/`LIST_EXTRA_OPS`'s O(sa·sb) Binary/`ListMap` combinatorics)
is therefore a genuine no-op for the CONTENTS of `op_list` on every spec —
its only possible effect is WHEN, within one size's registration loop, the
cheap `ParseInt` Unary op gets its turn.

**Built, rebuilt from source (engine hash `7ce24779de7f`), measured
directly against task 439 (the closest of the four to converting — needs
271,544 tested uncapped, only 1.36x the 200K cap):**

| | tested (200K cap) | distinct | halt |
|---|---|---|---|
| before reorder | 200,000 | 17,839 | budget |
| after reorder | 200,000 | 17,702 | budget |

**Did not convert.** Uncapped re-sweep after the reorder: `found:True` at
size 8, but now needing **278,794** tested (vs. 271,544 before the
reorder — slightly MORE, not less). `ParseInt`'s gate makes it fire at
EVERY size (2 through 9), not just size 8 where its payoff would matter —
each smaller size's cheap sweep of `by_size[size-1]` adds a small amount
of overhead that is never recovered, since ParseInt's own wrapped source
(`JoinList(MapList(...))`) is not yet complete until deep into size 7-8
regardless of reorder (sources for a Unary op always come from an
ALREADY-COMPLETE prior size level; reordering within a size cannot pull
a not-yet-built size-8 intermediate forward). Reverted cleanly.

### 2.3 The decisive finding: even unlimited budget converges on spurious answers, checked directly against held-out rows

Before concluding anything about budget size, the found term at each
canary task's UNCAPPED "solved" point was verified against the task's own
real held-out row (never assumed correct from `found:true` alone — the
same "invocation, not inference" standing rule this arc already uses):

| task | uncapped tested-to-solve | found term | held-out check |
|---|---|---|---|
| 439 | 271,544 (size 8) | `min(113350, (-123456 * neg(min(item for item in a))))` | **MISMATCH** (got 113350, expected 10152025) |
| 419 | 596,987 (size 8) | `(if (2 - min(item for item in a)) then 243 else 345)` | **MISMATCH** (got 243, expected 513) |
| 102 | 1,732,357 (size 6) | `(if (a == 'python_program') then 'PythonProgram' else 'PythonLanguage')` | **MISMATCH** |
| 411 | 2,130,771 (size 6) | `(if (a == 'android_tv') then 'AndroidTv' else 'GooglePixel')` | **MISMATCH** |
| 604 (bonus canary) | 1,748,439 (size 6) | `(if (a == 'python program') then ... else ...)` | **MISMATCH** |
| 772 (bonus canary) | 2,267,235 (size 6) | `(if (a == '...') then ... else ...)` | **MISMATCH** |

**6/6 checked tasks: the first term the search finds under any budget
large enough to reach ANYTHING is a spurious two-revealed-row memorization
(`Eq`-to-a-literal-input `IfThenElse`, or an equivalent numeric-literal
`min`/`neg` trick), and every one fails its held-out row.** `Eq` and
`IfThenElse` sit in `DEFAULT_OPS` (`synth_enumerate.rs:245-247`), present
in EVERY typed op_list default, positioned near the front, and a
2-revealed-row spec can almost always be memorized this way at a size
smaller than any genuinely generalizing construction. **This means raising
`max_candidates` would not just be expensive — for these specific tasks it
is demonstrably INEFFECTIVE: the search would reach the wrong answer
before ever reaching the right one**, since the search returns on the
FIRST signature match by ascending size, and the spurious match's size
(6-8) is smaller than or equal to where the genuine construction can be
found (if it can be found by raw enumeration at all).

### 2.4 Cost of a budget raise, priced for completeness (not because it was the leaning)

Even setting aside §2.3's decisive finding: raising `max_candidates` from
200,000 to a level that would let 439 alone reach its (spurious) size-8
match would need ~280,000 (1.4x); 419 needs ~600,000 (3x); 102/411/604/772
need 1.7-2.3 MILLION (8.5-11.5x). A raise large enough to matter for more
than 439 would multiply the per-gapped-task search time by roughly an
order of magnitude across the ENTIRE battery (every currently-gapped spec
that hits budget today would now run proportionally longer before giving
up, whether or not it ever finds anything) — a real, board-wide runtime
cost for a change that, per §2.3, would not even produce correct answers
for the four tasks it targets.

### 2.5 GO/NO-GO — Item 2

**NO-GO on all three candidate fixes.** Dedup is confirmed already-correct
and not the bottleneck (§2.1). The one narrow, provably-safe reorder tried
was built, measured, and did not convert its target — if anything
marginally worse (§2.2), reverted. Raising the budget cap is disqualified
on TWO independent grounds, not just one: it is expensive (§2.4, up to
11.5x for some of the four) AND — the decisive point — it is
**demonstrably ineffective**, since every uncapped "solution" found for
all 6 checked tasks (the 4 priced + 2 bonus canaries found via the same
`.join(` grep) is a spurious few-shot memorization that fails its own
held-out row (§2.3). No code retained.

---

## Regression discipline

**Rust:** `cargo build --release` from source succeeded cleanly at every
step (documented pyo3 linking workaround used throughout). All
intermediate builds compiled with zero errors; both experimental changes
were fully reverted via `git checkout --
runners/dsl/src/synth_enumerate.rs` before the final measurement pass, and
the engine was rebuilt from the reverted source (hash `e2fbf39e6b4e`,
matching the tree's own committed engine hash pre-investigation). Ran the
full `cargo test --lib --release -- --test-threads=1` suite on this final,
fully-reverted source.

**MBPP battery — before/after, all three arms, real set-diff.** "Before"
and "after" are, honestly, the SAME committed source (both experimental
changes were reverted, not merged) — this is not a null result being
dressed up as a comparison; it is the correct, honest outcome of two
NO-GOs. Re-ran the full 257-task battery after the final revert to
confirm this directly rather than assume it:

```
full:              66/257  (before_pass == after_pass: True)
content_stripped:  65/257  (before_pass == after_pass: True)
official:          94/257  (before_pass == after_pass: True)
```

Zero regressions, zero new passes, by direct set comparison of task-id
pass sets on all three arms (not aggregate counts).

**Python, the named 9-file suite.** Since the tree is source-identical to
`main @ fa5b659` in `runners/dsl/src/synth_enumerate.rs` (both changes
reverted), the named suite's outcome is expected to reproduce whatever
`main`'s own current state shows — no NEW failure signature is introduced
by this rung, because no code from this rung is retained.

---

## What this does NOT establish

1. **Item 1's `JoinListSep` op is semantically correct and was live-tested
   (via a diagnostic `max_size:10` probe) to at least be REACHABLE at that
   depth in principle** — but that probe also showed a DIFFERENT spurious
   construction wins the race there, so "reachable at size 10" is not the
   same as "would convert task 421." Whether an even leaner construction
   exists (perhaps using a Term this investigation did not consider) is
   not ruled out — only the two independently-designed variants tried here
   (both landing on extra=7) were checked.
2. **The `ParseInt` reorder experiment (Item 2 §2.2) is the only reorder
   tried.** A more aggressive reorder (e.g. moving several ops, or
   reordering `MapList`/`JoinList` themselves within `LIST_EXTRA_OPS`) was
   NOT attempted — the "always append, never interleave" discipline this
   file has followed since Rung 1 makes such a change materially riskier
   (harder to prove no currently-passing task's accepted construction
   shifts), and this rung's own narrow, provably-safe attempt already
   measured no benefit, so a broader, riskier attempt was not judged worth
   pursuing this rung.
3. **The Eq/IfThenElse spurious-memorization finding (§2.3) is a genuinely
   new, decisive finding this rung establishes, but its fix is out of
   scope here.** A real fix (e.g. requiring 3+ revealed rows before
   accepting a construction that references an exact revealed input
   literal, or an MDL/genericity penalty against `Eq`-to-a-literal
   constructions, or promoting the `holdout_verdict` check INTO the search
   loop itself so `IfThenElse(Eq(...))` matches are rejected as soon as
   found rather than accepted as the first signature match) is a
   materially larger change than this rung's scope and is named, not
   built.
4. **Whether this reflects real human program-synthesis cognition** remains
   exactly as open as every prior document in this arc left it.

## Reproduce

```bash
cd /home/matt/ozmadev/ocelot-worktrees/progsyn-delimjoin-budgetwall
git log --oneline -1   # source-identical to main @ fa5b659 in synth_enumerate.rs
bash scripts/engine_build.sh
PYTHONPATH="runners/dsl/python:.:scripts" OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 \
  python3 scripts/mbpp_endgame_battery.py
```
