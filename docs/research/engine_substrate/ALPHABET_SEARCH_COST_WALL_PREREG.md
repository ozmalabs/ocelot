# Alphabet-driven per-character constant pool — PREREG

**Date:** 2026-08-17. Base `main @ 5494752` (verified fresh:
`git log --oneline -1 main` before creating this worktree). Worktree:
`/home/matt/ozmadev/ocelot-alphabet-search-cost-wall`, branch
`alphabet-search-cost-wall`. Spec: `PBE_STRING_BENCHMARK_RESULTS.md` §2.2/
§2.3 (a NEW search-cost wall that corpus surfaced and named but did not
fix). **Not merged to `main`, not pushed** — left for the orchestrator's
independent re-verification, per house discipline.

**HEADLINE (predicted, checked below against real measurement in the
RESULTS doc): the wall is a POOL-SIZE problem, not a pricing bug, and the
fix generalizes the ALREADY-EXISTING `literal_witness_cost` MDL pricing
ladder along a second axis it was never asked to cover — bits to select
one symbol out of the spec's own observed alphabet — rather than
reaching for a new primitive, a hand-classified "useful vs. noise"
character heuristic (empirically tested below and REJECTED — see §3), or
a bespoke pruning knob.**

---

## 0. The diagnosis, re-verified against current source

`runners/dsl/src/synth_enumerate.rs:2930-2958` (current line numbers,
re-found — the PREREG-spec's `2930-2960` cite still holds) unconditionally
appends every whole string AND every distinct character observed anywhere
in a spec's revealed inputs/outputs to `str_consts`. These are registered
as size-1 leaves at `:3088-3101`, each priced by `literal_witness_cost`
(`:1484-1502`) before being skipped (`cost > max_size`) or registered.

`literal_witness_cost`'s rule ladder, first-match-wins:

1. appears in ≥1 revealed INPUT → data-derived → **cost 1**.
2. appears in EVERY revealed row's output → row-invariant task constant →
   **cost 1**.
3. appears in EXACTLY ONE row's output, no input witness → single-witness
   output quote (the memorization signature) → **cost = own char count**.
4. otherwise → **cost 1** (conservative default).

**The bug is not in this ladder's classification** — it is in what
happens when `s` is a SINGLE CHARACTER. Rule 3's pricing (`s.chars()
.count()`) is the doc's own stated mechanism for making a memorized
literal EXPENSIVE in proportion to how much it says — but a
one-character string's own length is always 1, so rule 3 degenerates to
`cost 1` for every character it would otherwise apply to. And rule 1
(checked first) fires for nearly every character a realistic spec
contains, because **characters are drawn FROM the input/output strings
themselves** (`:2941-2958`) — a character is, definitionally, a
substring of whatever string it was extracted from, so it is
overwhelmingly likely to also be a substring of SOME revealed input.
Practically: for an English-word spec, essentially the WHOLE observed
alphabet (15-19 distinct characters, per `PBE_STRING_BENCHMARK_RESULTS.md`
§2.2's own measured table) registers at cost 1, all competing for the
same tiny size-1 leaf slot, and this fans out combinatorially into every
op that consumes 1-2 character/string arguments (`Replace`'s `old`/`new`,
`Split`'s delimiter, etc.) at every larger size class the growth loop
reaches. The cited measurement (§2.2's own isolated probe, same op
inventory, same budget, same task SHAPE, only alphabet size varying):

| alphabet (distinct chars) | tested | found? |
|---|---|---|
| 8 | 1,884 | yes |
| 13 | 200,000 (exhausted) | no |
| 17 | 200,000 (exhausted) | no |

This IS a pool-size problem, not a mispricing bug, exactly as the spec
states: rules 1/2/3/4 are each individually correct given what they
measure — the missing piece is that **none of the four rules can express
"this character conveys little information because the spec's own
alphabet is large,"** because that quantity (alphabet size) never enters
the ladder at all today.

---

## 1. SHAPES-NOT-NUMBERS classification, done explicitly, before any code

CLAUDE.md's own test: is this fix a *quantity that changes* (sd loop:
decode against a growable codebook, mint only when a residual won't fit),
a *set of allowed moves* (Γ: a generated Production, not a filter), or
genuinely something else?

**Checked against what each primitive actually IS in this codebase, not
assumed:**

- **The sd loop** (`shape_decode.rs`, `ShapeDecode`/`sd_recognize`/
  `sd_mint_quantum`) exists to decide when an OBSERVATION is genuinely
  novel relative to a held codebook and to MINT new capability from the
  residual. Nothing here is being learned or minted — every character in
  `str_consts` is already fully known (it is copied verbatim out of the
  spec's own revealed rows); the question is only whether an
  already-known atom is CHEAP enough to compete at a given search size.
  There is no residual, no codebook growth, no recognize/transform/infer
  ladder to run. **Ruled out**: this is not a quantity that changes in
  the sd-loop sense.
- **The Γ admissibility grammar** (`seeds/program_synthesis_opgrammar.json`,
  `GAMMA_CONSULTATION_FLIP_RESULTS.md`) is, verbatim, in its own seed
  description, scoped to "the op-list boolean gate ladder inside
  `eval_synth_enumerate`… a real generated multi-production admissible-move
  SET." Checked directly: every `SynthOp` node and every one of its 17
  Productions governs which OPERATORS are admissible for a spec SHAPE
  (`is_string_shaped`, `output_is_listlike`, …), consulted ONCE, in
  Python, BEFORE the Rust search runs (`domains/prog_synthesis.py::
  run_enumerate` reading `admissible_moves`). There is no precedent, and
  no natural node type, for treating an individual LITERAL VALUE as a
  Γ-graph object — `SynthOp` nodes denote operators, not constants — and
  a per-character graph consultation from inside `synth_enumerate.rs`'s
  hot per-leaf registration loop would be a different, much heavier
  architecture than the existing single pre-search Python↔substrate
  round-trip. Separately, and decisively for THIS wall specifically: the
  `declared` arm's fixed `PBE_OPS` (`scripts/pbe_string_battery.py`)
  ALWAYS includes `Replace` and `Split` — both literal-consuming ops — so
  a coarse "gate the whole `str_consts` pool on whether any
  literal-consuming op is present" admissibility rule (the one form of
  this that WOULD map cleanly onto the existing op-admissibility
  precedent) would fire as a no-op for exactly the corpus this wall was
  measured on. Verified, not assumed, by re-reading `PBE_OPS` at
  `scripts/pbe_string_battery.py:99-104`. **Ruled out**: the wall this
  spec targets is not resolved, and has no clean encoding, as a Γ
  admissible-move set.
- **Something else, but not unmoored from an existing primitive**: the
  fix is an in-kind extension of `literal_witness_cost` ITSELF — the
  MDL/description-length pricing ladder the MBPP arc already built and
  that CLAUDE.md's own architecture notes treat as the correct locus for
  "which size class a literal registers into, nothing else" (quoted from
  that function's own doc comment). This is not literally the sd loop
  (no mint) and not literally Γ (no generated production over graph
  data) — but `literal_witness_cost` is already a bespoke, established,
  documented pricing primitive for exactly this class of decision, and
  the fix generalizes its OWN stated principle ("price a pooled STRING
  literal by its description length given its witnesses") along a second
  axis it has never been asked to cover, rather than introducing a new
  mechanism. **This is the conclusion**: extend the existing
  witness-cost ladder, do not invent a parallel subsystem.

---

## 2. Why "classify which characters are individually useful" was tried

FIRST, and rejected, empirically

Before settling on the alphabet-cost design, the task's own suggested
starting hypothesis — narrow registration to characters that "could
plausibly matter" (appear in only SOME rows, or differ in count/position
between input and output, or are structurally implicated the way
`Replace`'s own old/new roles would need) — was built as a Python
prototype against the REAL fixture data
(`tests/fixtures/pbe_string/pbe_string_tasks.json`) and measured directly,
BEFORE writing any Rust, specifically to avoid shipping an unverified
semantic heuristic.

**Attempt A — "presence pattern is non-uniform across rows" (i.e., not
present in literally every row).** Measured against `pbe_001`,
`pbe_004`, `pbe_012`, `pbe_015`, `pbe_024`, `pbe_026`: **prunes ZERO
characters on every single task tried.** With only 2-3 revealed rows per
task (the corpus's own realistic size), almost every character's
presence pattern is non-uniform across rows purely because English words
rarely share many letters at that sample size — this signal is far too
weak to discriminate anything at this row count.

**Attempt B — "character's count differs between a row's own input and
that row's own output" (a structural-edit signal).** Measured the same
way: prunes SOME characters (`pbe_024`: 17 → 13, only 4 removed — nowhere
near enough given the doc's own table shows 13 already exhausts budget)
but, more importantly, **actively breaks the one real capability it
must preserve**: `pbe_025` (`reverse(replace('p'→'@', s))`) needs `'p'`
kept cheap as `Replace`'s `old` argument. `'p'` is present in BOTH
revealed inputs (`"apple"`, `"grape"`) by ordinary construction (you
demonstrate a replace rule by picking inputs that CONTAIN the character
you're replacing) — this is completely uniform-across-rows presence, so
Attempt A would have wrongly pruned it, and even Attempt B keeps it only
because the specific row-local count happens to differ (2→0 in row 1,
1→0 in row 2) — which is indistinguishable, on the same statistic, from
the "count differs because the output is just SHORTER than the input"
pattern that fires for nearly EVERY character in every short-output
extraction task (`pbe_024`'s own genuine `Slice`-based output is short
relative to its input, so most of ITS characters also show a row-local
count difference, for reasons having nothing to do with any op
individually consuming that character). **Both statistics are real
signal-poor with 2-3 rows and a short output**, and Attempt B in
particular cannot separate "this character is an independent literal
argument some op needs" from "this character's count merely changed
because ANY nontrivial transformation changes count statistics for most
characters when the output is much shorter than the input." Reported
here as a real, checked negative result, not smoothed over: **per-row
statistical classification of individual characters does not work at
this corpus's realistic row count, and risks REGRESSING the exact
Replace-literal capability (`pbe_025`) the fix must not break.**

This negative result is why §1's classification lands on extending
`literal_witness_cost`'s MDL pricing rather than inventing a
per-character "useful/noise" classifier: the classifier attempt was
tried, on real data, before deciding against it.

---

## 3. The design actually proposed

Generalize `literal_witness_cost`'s existing "cost = description length
given witnesses" principle along a SECOND MDL axis it has never used: a
multi-character literal's natural unit is CHARACTER COUNT (rule 3,
already correct, UNTOUCHED by this change); a SINGLE character's natural
unit is **bits to select one symbol out of the spec's own observed
alphabet** — `ceil(log2(alphabet_size))`, the textbook MDL cost of
specifying an index into a size-N code, where `alphabet_size` is exactly
the quantity `PBE_STRING_BENCHMARK_RESULTS.md` §2.2 measured and named
(the count of distinct characters already computed for `str_consts`).

Concretely: `literal_witness_cost` gains one new usize parameter
(`alphabet_size`, the distinct-character count already available at the
call site from `str_consts`), and every branch that would otherwise
return the flat `1` for a **single-character literal not already
protected by row-invariance** (rule 2) returns `alphabet_char_cost
(alphabet_size)` instead — `ceil(log2(alphabet_size))`, floored at 1, so
tiny alphabets (≤2 distinct characters) are byte-unchanged at cost 1.
Row-invariant characters (a genuine fixed task constant present in EVERY
revealed output, e.g. `pbe_025`'s `'@'`) are checked FIRST for the
single-character case specifically and stay at cost 1 unconditionally —
row-invariance is independent evidence of genuine task relevance that
alphabet size does not undermine. **Every multi-character literal's
pricing is completely untouched** — the new branch only ever fires when
`s.chars().count() == 1`.

Why this should close the wall without a semantic classifier: it does
not try to decide WHICH characters are individually useful (§2's
rejected attempt) — it prices ALL of them by the SAME alphabet-size-aware
rule, uniformly. For a small alphabet (MBPP's own short/numeric example
values, or the doc's own 4-8-char isolated probes) the cost stays at or
near 1 — near-zero behavior change. For a large alphabet (15-19 distinct
characters, this corpus's realistic English-word specs) the cost rises
to roughly 4-5 — high enough that character leaves no longer occupy the
size-1 slot alongside vars/whole-string/int leaves, so early size classes
(1-4) stop paying for character-driven combinatorial fan-out at all,
while a genuinely needed character (still costing only ~5, not
prohibitive) remains reachable well within the corpus's existing 15-20
`max_size` budgets — deferred, not excluded. This is expected to shrink
`tested` substantially at the SMALL size classes where the wall's own
combinatorial explosion originates (per §2.2's isolated-probe table),
without permanently banning any character a genuine composition needs.

**What this section does NOT establish** (checked empirically in the
RESULTS doc, not asserted here): the MAGNITUDE of the improvement on the
actual wall-blocked tasks (`pbe_012`, `pbe_015`, `pbe_024`, `pbe_026`),
whether MBPP alphabets are small enough that this is genuinely a
no-op there, and whether `ceil(log2(N))` is the right constant among
plausible MDL-consistent alternatives (e.g. a stricter bound) — this
PREREG states the chosen formula and its justification; the RESULTS doc
reports what actually happened when it ran.

---

## 4. What could go wrong, named in advance

1. **A genuinely needed character could be pushed past `max_size`** for a
   spec whose alphabet is large enough that `ceil(log2(N))` plus the
   surrounding composition's own op/var cost exceeds the search's size
   budget. Named risk, not yet measured — the RESULTS doc's holdout
   checks on `pbe_025` (needs `'p'` as a literal) are the direct test.
2. **MBPP alphabets might not be as uniformly small as assumed.** The
   task brief's own framing ("MBPP's own example values are mostly
   short/numeric, so this SHOULD be a low-risk change... but verify it")
   is taken at face value — not assumed true without the paired battery.
3. **The `alphabet_size` count itself could be gamed by an unrelated
   change to how `str_consts` is built** (e.g., if a future rung changes
   what counts as a "distinct character," this cost formula's behavior
   shifts silently) — noted as a coupling, not fixed here.
4. **`ceil(log2(N))` might be too WEAK** to meaningfully shrink `tested`
   at the specific sizes the wall bites (§2.2's table shows the effect is
   very steep — 8→13 chars moves from found-in-1884 to
   exhausted-at-200,000, a >100× step for a 62% growth in N) — measured
   directly in the RESULTS doc's `tested` counts, not assumed adequate
   here.

---

## 5. Verification plan (this PREREG commits to, before any code runs)

1. Implement in `runners/dsl/src/synth_enumerate.rs` only (`literal_witness_cost`
   + its one call site + a new `alphabet_char_cost` helper). No other
   files touched by the Rust change itself.
2. Genuine from-source rebuild (`cargo test --lib --release --
   --test-threads=1`, the `RUSTFLAGS`/`LD_LIBRARY_PATH` pair from the
   task brief on the SAME command) — baseline 778, expect 778+N after,
   confirmed via a touched-source rebuild (not a cached sub-second run).
3. `bash scripts/engine_build.sh` to install.
4. Re-run `scripts/pbe_string_battery.py` — report exact before/after
   numbers per arm, and specifically whether `pbe_012`/`pbe_015`/
   `pbe_024`/`pbe_026` move.
5. Full paired MBPP battery against the CURRENT 88/87/115 baseline
   (`results/mbpp_endgame.json`) — exact task-id set comparison,
   `lost_pass` must be empty. A regression here is a NO-GO regardless of
   the PBE result.
6. Named 9-file regression suite — expect exactly the 3 known
   pre-existing pin-drift failures, nothing new.
7. RESULTS doc + commit in the worktree, unmerged, unpushed.
