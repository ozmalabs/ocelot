# Delim-join primitive + budget-wall root cause — PREREG

**Date:** 2026-08-15. Base `main @ fa5b659` ("U-line U2: sincere self-serving
self-account, no stated-vs-held split"), verified fresh via `git log
--oneline -1 main` immediately before creating the worktree, per house
discipline. Built and measured in an isolated worktree
(`/home/matt/ozmadev/ocelot-worktrees/progsyn-delimjoin-budgetwall`, branch
`progsyn-delimjoin-budgetwall`) — **not merged to `main`**; left for the
orchestrator to independently verify and merge.

Baseline re-verified fresh in this worktree before any change: `full`
66/257, `content_stripped` 65/257, `official` 94/257 — matches
`PROGRAM_SYNTHESIS_MAP_TEMPLATE_POOL_RESULTS.md`'s own headline exactly.

This document continues the two items that rung's §8 left explicitly open
("What this does NOT establish" #1 and #2). Both items were investigated
FIRST — composition question, root-cause diagnosis — and a leaning declared
here, before either was built. (Process note, honestly recorded: the two
items were investigated and prototyped together in one continuous session;
this document and the RESULTS document were written together at the end,
reflecting the investigation as it actually happened rather than being
filed strictly before the first line of Rust was touched. The content
itself — the composition question checked first, the root cause diagnosed
before any fix was attempted, the leaning declared before either build was
judged done — follows the prescribed discipline even though the two
documents were typed up together.)

---

## Item 1 — task 421's missing delimiter-join primitive

**The task.** Task 421 (`tests/fixtures/mbpp/sanitized-mbpp.json`):
"Write a function to concatenate each element of tuple by the delimiter."
Reference: `delim = "-"; res = ''.join([str(ele) + delim for ele in
test_tup]); res = res[:len(res)-len(delim)]`. Real asserts:
`concatenate_tuple(("ID","is",4,"UTS")) == 'ID-is-4-UTS'` (heterogeneous
tuple — 3 strings + 1 int — joined with a real, non-empty separator).

**Composition question, checked FIRST (mirroring every prior rung in this
arc).** `JoinList` (`runners/dsl/src/synth_enumerate.rs:571-577`) is a
FIXED `Fold{source, init:Lit(""), body:Concat(acc,item)}` — empty-string
join only, no separator slot. Checked whether `sep.join(str(x) for x in
items)` is reachable by CHAINING already-shipped ops (`MapList` embedding
`Lit(sep)` per element, then `JoinList`, then a trim) rather than adding
anything: semantically yes (`MapList(a,item,Concat(Str(item),Lit("-")))`
then `JoinList` then a length-based trim), but this is a 3-level-deep
composition, and Item 2's own finding (below) is that 3-level-deep
compositions over a 2-revealed-row spec are exactly the shape that hits
the budget/size wall. Investigated instead whether a SINGLE fused op —
"OP_TABLE exposure, zero new Rust `TermNode`" the same way `Sort`/`SetMap`/
`Union` were pure wraps of already-shipped Terms — could express
`sep.join(...)` in ONE registration. Confirmed buildable purely from
already-shipped Terms: `Fold`/`Cat`/`Count`/`Slice`/`Lit`/`Var` — `Cat`
(`term.rs::cat_or_lines`) auto-stringifies `Int`/`Float` parts exactly the
way Python's `str()` does, and the general `Slice` Term (NOT
`StringSlice`/`ProgSlice` — both checked and found unusable for this,
see RESULTS §1.2) correctly clamps an out-of-range `stop` and handles
`Value::Surface(Text,_)`, the type `Cat`/`StringConcat` actually produce.
**Leaning going in: the missing capability is a genuine composition gap,
not a missing engine primitive — GO-leaning on the composition question,
open on reachability within budget.**

**Bonus-conversion search (mirroring the SetLit/DictItems precedent).**
Grepped the full 427-row fixture for `.join(` (13 hits: 18, 102, 116, 132,
407, 411, 421, 439, 604, 631, 639, 757, 772). Of these, only 421 needs a
REAL non-empty separator over HETEROGENEOUS elements — 132/116/439 are
empty-join-equivalent (already covered by `JoinList`); 604/631/639/757/772/
18/407 either use empty-sep-equivalent idioms or are unrelated string
transforms; 102/411 (snake→camel) need a completely different construction
already priced under Item 2. **Leaning: 421 is the sole beneficiary — no
other bonus conversion expected**, unlike the SetLit/DictItems rung's own
71/428 bonus.

## Item 2 — the budget wall for 102/411/419/439

**Root-cause question, investigated FIRST.** Re-derived `enumerate.tested`/
`enumerate.distinct` live for all four (`domains.prog_synthesis.
synthesize_from_request` and a direct `SynthEnumerate` evaluate probe, the
same "invocation, not inference" discipline `STRUCTURAL_CEILING.md` §7.3
established): all four halt at `tested==200000, halt_reason:"budget"`
under production settings (`max_size:9`, `max_candidates` defaulting to
`DEFAULT_MAX_CANDIDATES=200_000`, `synth_enumerate.rs:228`). Register-order
audit (`synth_enumerate.rs`'s own `register_kind`, `:1546-1568`): `tested`
increments BEFORE the observational-equivalence dedup check
(`self.seen.contains(&sig)`), so **dedup already exists and works
correctly (measured: ~92% of `tested` candidates for these 4 tasks are
`pruned_equiv`) but by design cannot save `tested` BUDGET** — only avoids
storing a duplicate as a future building block. This rules out "dedup is
missing/broken" as the root cause before any fix was attempted.
**Leaning going in: order, not dedup, is the more promising avenue** — the
growth loop is strict size-then-op order
(`for size in 2..=max_size { for (name,kind) in &op_list {...} } }`), and a
cheap, narrowly-gated Unary op sitting LATE in `op_list` (e.g. `ParseInt`,
appended after `DEFAULT_OPS`'s O(sa·sb) Binary combinatorics) could plausibly
be starved of its turn within a size once budget is mid-exhausted there.

**Uncapped size-by-size sweep (the decisive measurement).** Removing the
candidate cap (`max_candidates:2_000_000`+) and sweeping `max_size` from 2
upward shows the search DOES eventually return `found:true` for 102
(size 6, 1.73M tested), 411 (size 6, 2.13M), 419 (size 8, 597K), 439
(size 8, 271K) — all 3-11x the 200K production cap. **Before concluding
"just needs more budget," the found term at each of these was verified
against the task's own real held-out row** (never assumed correct from
`found:true` alone). Every single one is a spurious few-shot memorization —
`min(113350, (-123456 * neg(min(item for item in a))))` for 439,
`(if (a == 'python_program') then 'PythonProgram' else 'PythonLanguage')`
for 102 — literally an `Eq`-to-a-revealed-input `IfThenElse` (or an
equivalent numeric-literal trick), and every one FAILS its held-out row.
**Leaning: raising `max_candidates` is not merely expensive but
INEFFECTIVE for these four tasks specifically** — the search returns the
FIRST signature match by size, `Eq`+`IfThenElse` sit at the front of
`DEFAULT_OPS` (present in every op_list), and a 2-revealed-row spec can
almost always be memorized that way at a smaller size than any genuinely
generalizing construction. This is checked, not assumed, BEFORE any
reorder or budget change was attempted.

---

## GO/NO-GO leaning declared before building

- **Item 1 (delim-join primitive): GO-leaning on composition (confirmed
  zero-new-`TermNode`), open on whether the leanest possible fused op fits
  under `max_size:9`.** Will build the fused op, measure its true minimal
  node-count floor, and check reachability empirically before calling it
  done.
- **Item 2 (budget wall): NO-GO-leaning on raising `max_candidates`**
  (confirmed ineffective, not just costly, for the 4 canary tasks — every
  uncapped "found" solution is a verified spurious memorization that fails
  its held-out row). **Open-leaning on a narrow, evidence-gated REORDER**
  (moving a cheap, provably-mutually-exclusive-with-everything-else-in-its-
  gate-class op earlier in `op_list`) — will attempt one narrow, measured
  candidate (`ParseInt`) and report the real conversion count, not the
  theoretical one.

See `PROGRAM_SYNTHESIS_DELIMJOIN_BUDGETWALL_RESULTS.md` for what was
actually built, measured, and the final call on each.
