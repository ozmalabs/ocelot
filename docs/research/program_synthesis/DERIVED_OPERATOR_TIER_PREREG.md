# A derived-operator tier for `SynthEnumerate` — PREREG

Base `main @ df00b37` ("Merge oplist-admissibility-grammar: Γ-production
design for op-list gating, GO on design"), verified via `git log --oneline -1
main` immediately before creating this worktree
(`/home/matt/ozmadev/ocelot-worktrees/derived-operator-tier`, branch
`derived-operator-tier`). **This is an INVESTIGATION-AND-DESIGN-ONLY task:
zero code, zero seed JSON, zero tests, zero `.rs`/`.py` edits.** A sibling
agent is concurrently building `GroupCount`/`DictMerge` in a separate
worktree (`/home/matt/ozmadev/ocelot-worktrees/progsyn-groupcount-dictmerge`,
branch `progsyn-groupcount-dictmerge`, confirmed live via uncommitted changes
to `runners/dsl/src/{jsonio,reflect,synth_enumerate,term,term_variants}.rs`
at the time this worktree was created) — this document reads those files
FROM `main @ df00b37` (this worktree's own base, unaffected by the sibling's
uncommitted worktree state) and does not touch them.

**The question this document answers.** `OPLIST_ADMISSIBILITY_GRAMMAR_
RESULTS.md` (just merged) designed a Γ-production layer deciding which of
`OP_TABLE`'s already-existing 50 op names (see §0 correction below) are
admissible for a given spec shape — the SELECTION layer. `PROGRAM_SYNTHESIS_
DELIMJOIN_BUDGETWALL_RESULTS.md` separately built, measured, and reverted a
real composite op (`JoinListSep`) entirely from already-shipped Terms
(`Fold`/`Cat`/`Count`/`Slice`/`Lit`/`Var`) — zero new `TermNode` variants —
but as a ONE-OFF: new Rust code in `synth_enumerate.rs` (a new `OpKind`
variant, a new hand-written builder function, a new combinatorics loop), not
persisted as a reusable, cross-task unit. Today there is a PRIMITIVE tier
(new `TermNode` + evaluator arm, a real Rust/recompile cost, CLAUDE.md's own
sanctioned pathway) and an implicit COMPOSITION-AT-DISCOVERY-TIME tier
(hand-build a `Fold`/`Cat`/... tree once per investigation, either thrown
away or paid for again in fresh Rust each time it recurs). **Missing: a
DERIVED-OPERATOR tier — a named, reusable, parameterized composition of
already-existing Terms, stored as graph/seed DATA, selectable by the
enumerator's search as if it were a native op, evaluated by template
substitution over the EXISTING interpreter, and mintable by the sd loop's own
recognize→residual→mint discipline.**

This document asks, with the real code read in full: (1) what Term-tree
search architecture and evaluation mechanism actually exists today
(`synth_enumerate.rs`, `term.rs`), and — the central question, mirroring
`RULES_AS_SHAPE_DESIGN_SPIKE.md`'s own finding that *"the missing piece was
never the shape math, it was an addressable object for the shape math to
operate on"* — whether any existing mechanism ALREADY IS a parameterized
Term-tree-with-holes evaluated by substitution, just not exposed as a named,
cross-task-persistent unit; (2) precisely what a `Call`-shaped dispatch
mechanism needs, sized against the SAME touch-point accounting this arc's
own primitive-adding rungs already use (evaluator arm, `copy_subtree`,
`children()`, `term_variants.rs` regeneration, `jsonio.rs`, `reflect.rs`);
(3) a mint discipline, with the correctness risk (overfit one-off vs.
genuine reusable primitive) investigated honestly, not assumed safe; (4) how
this composes with the just-landed Γ-admissibility design; (5) a retroactive
walkthrough of whether this mechanism, had it existed, would have let
`JoinListSep` be minted as reusable data instead of built as a one-off; (6)
an honest GO/NOT-YET-READY call with a precise, buildable first slice.

## Method

1. **Read `synth_enumerate.rs` in full for the relevant sections**: the
   module doc (architecture + divergences from `generator.py`), `OpKind` +
   `OP_TABLE` (recount the entry population directly — do not trust the
   prior document's "31" figure without checking), the per-`OpKind`
   hand-written builder functions (`build_list_unary`, `build_list_binary`,
   `build_list_ho`, `build_indexed_map`), the MDL/size-accounting tables
   (`list_unary_extra_cost`, `list_binary_extra_cost`), the `local_sym`
   fabricated-Sym precedent, the per-element template-pool construction
   (`filter_templates_by_size`/`map_templates_by_size`/
   `indexed_map_templates_by_size`), the main growth loop's per-`OpKind`
   combinatorics (the size-partition + cross-product shape for each kind),
   and the `exclude` argument's local Term-JSON parser (`parse_excluded_
   term`) — noted in its own doc comment as deliberately NOT reusing
   `jsonio::term_from_json` because that function needs `&mut Interner`,
   which this engine never holds at eval time.
2. **Read `term.rs` for `TermNode`'s shape, `evaluate()`'s dispatch, and any
   existing "named template + hole substitution" mechanism** — specifically
   check for `AntiUnifyWitness`/`Substitute`/`Unify`/`StructSim` (the
   analogical-transfer Terms cited in CLAUDE.md's "SHAPE IS ACQUISITION,
   RULE IS EXECUTION" arc) AND, independently, `DerivationRegistry`/
   `Derivation`/`try_derivation!`/`EvalCtx.derivations` (found via grep, not
   assumed) — read each in full, and trace whether either is Python/PyO3/
   graph-wired today (`grep` `py.rs` and every non-`term.rs` `.rs` file for
   `with_derivations`/`DerivationRegistry`) or Rust-internal/test-only.
3. **Read `jsonio.rs`/`reflect.rs`/`term_variants.rs`/`tools/gen_term_
   variants.py` for one already-shipped small variant's exact touch-point
   footprint** (a `Vec<TermIdx>`-child variant like `Plus`, and a
   single-`TermIdx`-child variant like `Reverse`) to price a new `Call`
   variant's real, bounded, ONE-TIME cost precisely, not by analogy.
4. **Design the `Call`-shaped dispatch**: what a registered derived-operator
   template needs to encode (parameter names + pool origin per argument,
   template body, MDL extra-cost), where the registry lives, and the
   HONEST fork on whether "zero new Rust per derived op" survives contact
   with the real combinatorics loop shapes (six distinct hand-coded
   `OpKind` shapes today, each a different pool/arity combination) — does a
   derived op that needs a NOVEL pool-combination (the `JoinListSep` case:
   one arg from `list_by_size`, one from the general pool) still require new
   Rust, or does a genuinely generic N-ary/pool-typed combinator close that
   gap, and if so, is THAT combinator itself a one-time cost or a per-op one?
5. **Design the mint discipline** against the real precedents already in
   this codebase: `sd_mint_quantum`'s recognize→residual→mint +
   `Not(Exists(...))` dedup guard, `META_SHAPE_FIRST_CLASS_RESULTS.md §4.1`'s
   support=2 recurrence floor (cited by `problem_shape_growth.json`'s own
   `decompose_shape` comment as "the smallest cardinality at which recurs is
   defined"), `OPLIST_ADMISSIBILITY_GRAMMAR_RESULTS.md §6`'s own mint-sweep
   design (offline, not tick-time; forced-in candidate + held-out-row
   check), and `PROGRAM_SYNTHESIS_DELIMJOIN_BUDGETWALL_RESULTS.md §2.3`'s
   own decisive, measured finding — 6/6 checked spurious "solutions" under
   relaxed budget fail their held-out row — as the sharpest available
   evidence for why revealed-row `found:true` alone is an UNSAFE mint bar
   here, and ask explicitly whether even held-out-row agreement on the
   ORIGINATING task is sufficient, or whether cross-task recurrence
   (support ≥ 2, on INDEPENDENT tasks, not merely independent rows of one
   task) is the real bar a REUSABLE, EXECUTABLE primitive needs that a
   passive shape-quantum mint does not.
6. **Check composition with the just-landed Γ design**: does a minted
   derived operator become a new `SynthOp` node admitted via the SAME
   Production mechanism `OPLIST_ADMISSIBILITY_GRAMMAR_RESULTS.md §3` already
   designed, or does it need a separate admissibility path — and are "grow
   the derived-op vocabulary" (this document) and "grow which spec-shapes an
   op is admissible for" (the Γ document) genuinely orthogonal axes or does
   one subsume the other?
7. **Retroactively walk `JoinListSep` through the designed mechanism**,
   concretely: would it have been expressible as a registry template under
   the mechanism's real, priced constraints (§4's pool-shape honesty), and —
   separately — would the mechanism have changed DELIMJOIN's own measured
   NO-GO outcome (the size-10-vs-max_size-9 reachability ceiling, and the
   independently-decisive spurious-memorization finding at relaxed budget)?
8. **Render a GO/NOT-YET-READY call with a concrete, narrowly-scoped first
   slice**, mirroring `OPLIST_ADMISSIBILITY_GRAMMAR_RESULTS.md §8`'s own
   discipline (price before committing, do not bundle the open decisions).

## What this document will NOT do

No Rust file is touched (`runners/dsl/src/*.rs` stays byte-identical to
`main @ df00b37` for the entire duration of this task — checked at the end).
No seed JSON is written. No Python file under `domains/` is touched. No test
is run or written. Nothing in `runners/dsl/src/{jsonio,reflect,synth_
enumerate,term,term_variants}.rs` or `domains/prog_synthesis.py`-adjacent
files is edited — those are read-only citations from `main @ df00b37`, never
from the sibling's in-progress worktree. The deliverable is `DERIVED_
OPERATOR_TIER_RESULTS.md`, committed in this worktree on this branch, for
the orchestrator to review and merge after the sibling `GroupCount`/
`DictMerge` build lands.
