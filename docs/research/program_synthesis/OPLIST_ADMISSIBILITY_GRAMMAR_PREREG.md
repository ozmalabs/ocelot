# Should the MBPP op-list gate ladder become a Γ production? — PREREG

Base `main @ c5aea7b` ("Record retelling-decay build landed (ozmalabs/bigville
acf0961)"), verified via `git log --oneline -1 main` immediately before
creating this worktree (`/home/matt/ozmadev/ocelot-worktrees/oplist-
admissibility-grammar`, branch `oplist-admissibility-grammar`). The working
tree at that tip carries no `bigville_*`/other in-flight modifications
relevant to this document. **This is an INVESTIGATION-AND-DESIGN-ONLY task:
zero code, zero seed JSON, zero tests, zero `.rs`/`.py` edits.** A sibling
agent is concurrently landing `GroupCount`/`DictMerge` in
`runners/dsl/src/synth_enumerate.rs` and adjacent `domains/prog_synthesis.py`
territory — this document does not touch either file and does not depend on
that work landing first.

**The question this document answers.** `PROGRAM_SYNTHESIS_STRUCTURAL_
CEILING_REASSESSMENT_PREREG.md` (Q1, already landed) established that
`OP_TABLE` in `runners/dsl/src/synth_enumerate.rs` splits into two layers: a
PRIMITIVE layer (new `TermNode` variants — correctly NOT sd-loop/Γ-growable,
CLAUDE.md's own sanctioned "new primitive → Rust" pathway) and a SELECTION
layer (which of the already-existing ops to offer a given task). That
document's own §1.4 considered and explicitly rejected re-platforming the
enumerator's Term-tree search space onto Γ, but scoped that rejection to the
SEARCH SPACE itself (Term-tree AST vs. graph edges) — it did not evaluate
whether the narrower, already-separately-identified SELECTION layer's
BOOLEAN-GATE HALF (the `spec_has_dict_value`/`spec_has_list_of_lists`/…
ladder inside `eval_synth_enumerate` itself, as opposed to the NL-prose-token
`SynthesisOperatorShape` classifier that document's own Rung 4 already
recommends aligning to the sd loop) is Γ-shaped. `PROGRAM_SYNTHESIS_CEILING_
REASSESSMENT_3_RESULTS.md` is live, first-hand evidence that this ladder is
a real, recurring maintenance liability: `SortBy` was gated to
`spec_has_dict_value` alone to serve task 475, and a LATER rung had to add a
second disjunct (`spec_has_list_of_lists && !spec_has_dict_value`) by hand to
reach task 64's structurally different but Term-compatible shape — precisely
the "hand-maintained enumeration where a codebook belongs" anti-pattern
CLAUDE.md's SHAPES-NOT-NUMBERS section names.

**This document asks, with the real code read in full, not assumed:** is
this specific ladder — the evidence-flag → op-list construction inside
`eval_synth_enumerate` — better represented as a Γ production set (a
GENERATED admissible-move set) than as hand-written Rust `if` statements, and
if so, (a) what does the production LHS/RHS need to encode, (b) where would
it live, citing a real existing Γ-production precedent, (c) how would
productions be MINTED from real evidence rather than hand-transcribed, and
(d) is this cheap (an existing-shaped refactor) or does it need genuinely new
machinery (a new admissibility-checking path in the enumerator, mirroring
`SHAPE_AUDIT.md`'s already-found 159/634-seed zero-Γ-production gap)?

## Method

1. **Read the real gate population.** Every `spec_has_*`/evidence-flag test
   and every `v.push(...)` in `eval_synth_enumerate` (`synth_enumerate.rs`),
   plus the `map_templates_by_size`/`indexed_map_templates_by_size` gates one
   level down (these gate TEMPLATES within an admitted `MapList`/`SortBy`/
   `SetMap` op, not the op names themselves, but are the same shape and must
   be counted or explicitly excluded with a stated reason).
2. **Read the two REAL Γ implementations** — Rust (`grammar.rs`/`checker.rs`)
   and the Python mirror (`substrate/grammar.py`/`checker.py`/
   `seed_loader.py`) — to fix the actual `Production` shape (`src`,
   `edge_type`, `tgt`, `where_`, `weight`, `provenance`) and find one
   concrete, already-shipped, non-empty seed JSON production to cite as the
   literal syntax precedent (not invented).
3. **Read `domains/problem_shape.py`'s `_AXES`/`goal_signature`/
   `signature_key`** (cited in the task brief as a directly relevant
   precedent for "extract axes from real observed structure") and determine
   whether its exact idiom transfers to a `SynthEnumerate` spec's own
   evidence flags.
4. **Read how `SynthEnumerate`'s op inventory reaches the engine today from
   the graph side** (`domains/prog_synthesis.py::run_enumerate`,
   `ps_enum_ops`/`graph_ops`) to establish whether a Γ-generated op-list can
   reuse that EXISTING transcription path (cheap) or needs a new one
   (expensive), and to correctly distinguish this ladder from the SEPARATE,
   already-scoped `SynthesisOperatorShape` NL-trigger-token classifier
   (Rung 4 of the earlier PREREG) so the two are not conflated.
5. **Read whether the enumerator's evaluation context (`EvalCtx`) or any
   PyO3-exposed method can reach `ConsistencyChecker::check_edge`/
   `Substrate::admissible_moves`/`admissible_edges_from`/`is_edge_admissible`
   today**, to answer honestly whether wiring Γ into op-list construction
   needs new Rust admissibility-evaluation machinery or can reuse
   already-exposed calls — the direct analogue of `SHAPE_AUDIT.md`'s §4
   finding (159/634 seeds mint edges via rule `add_edge` effects that bypass
   `check_edge` entirely) applied to this specific site.
6. **Design the MINT mechanism** against the real methodology
   `PROGRAM_SYNTHESIS_CEILING_REASSESSMENT_3_RESULTS.md` already used by
   hand for task 64/12 (force a candidate op into `ops`, check `found:true`
   AND held-out-row agreement) — ask whether that methodology can run as an
   offline residual sweep that MINTS a Production on a verified hit, mirror
   the sd loop's own recognize→residual→mint discipline
   (`seeds/shape_decode_loop.json::sd_mint_quantum`) and the dedup/novelty
   guard idiom (`Not(Exists(...))`) already used elsewhere in this codebase
   (`seeds/gap_awareness.json`), and be honest about where this MINT's cost
   profile differs from the sd loop's (a graph pattern-match vs. an actual
   enumerator search run per candidate).
7. **Size the total build honestly** — new node types needed, new ingest
   wiring, whether the evidence-flag computation must be duplicated in
   Python or newly exposed from Rust as a single source of truth, and
   whether the mint sweep is cheap or combinatorially expensive.
8. **Render a GO/NOT-YET-READY call with a concrete, narrowly-scoped first
   slice** — mirroring this arc's own established discipline (Rung 1 before
   Rung 2, price before committing, canary-check against the known-passing
   population) rather than proposing a monolithic enumerator redesign.

## What this document will NOT do

No Rust file is touched (`runners/dsl/src/*.rs` stays byte-identical to
`main @ c5aea7b` for the entire duration of this task). No seed JSON is
written. No Python file under `domains/` is touched. No test is run or
written. The deliverable is `OPLIST_ADMISSIBILITY_GRAMMAR_RESULTS.md`, committed
in this worktree on this branch, for the orchestrator to review and merge
after the sibling `GroupCount`/`DictMerge` build lands.
