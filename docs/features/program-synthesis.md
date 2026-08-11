# Program synthesis

The agent learning to write, execute, and repair programs — the same
dynamic-quantization loop (`docs/features/dynamic-quantization.md`) applied
one level up, at the grain of statements and constructions instead of pixels
or strokes.

**A naming note first, because it trips people up:** this document's "ARC" is
the project's own phase numbering (ARC 0 → ARC 6, i.e. "the program-synthesis
arc"), an unrelated coincidence with **ARC-AGI**, the spatial-reasoning
benchmark covered in `docs/features/ls20-spatial.md`. When a filename in
`docs/research/program_synthesis/` says `PROGRAM_SYNTHESIS_ARC6_...`, it
means "phase 6 of the program-synthesis work," not the ARC-AGI benchmark.

## The design, in one sentence

The agent learns to program the way this tree does everything else:
**constructions PROPOSE** (a graph-resident codebook + corpus statistics
grown by the unchanged sd loop), **execution DECIDES** (a pure, fueled
interpreter over a hub IR, held-out rows as the verdict), and every loop
decision — propose, order, splice, evaluate, CEGIS, enumerate, accept-or-gap
— is a seed rule running in the Rust `run_rules` fixpoint. No Python
decisions anywhere in the loop.

## The pipeline

1. **One hub IR, five frames.** Python, Rust, Lua, x86-64 (via an LLVM
   chain), and LLVM IR all read into one hub statement IR and can write back
   out to it. `ProgEval` — a pure, fueled Rust interpreter — runs that IR
   directly; traps are honest, fuel is uncatchable, external calls only
   through declared oracles.
2. **The training run (P3).** The unchanged sd loop decodes a corpus (tens
   of thousands of statement instances, drawn from Python's own `ast`
   module reading real code) into a small codebook of **construction
   quanta** plus bigram transition rows — i.e. it learns "shapes of code"
   the same way the vision loop learns shapes of pixels.
3. **The synthesis loop as rules.** Given a natural-language request and
   some input/output rows: propose (codebook `Argmax`) → order (bigram
   lattice Viterbi decode) → splice → evaluate → CEGIS
   (`CounterExample`/`Excluded` nodes, integer fuel budgets) → enumerate
   (`SynthEnumerate`, a Rust term) → accept (reflected into the graph as an
   `ir_subgraph`) or gap (files a `SelfConcern`, closing the human-gated
   self-improvement loop described in `CLAUDE.md`'s gap-awareness section).
4. **Recursive descent (P7-A).** A partial codebook cover is treated as a
   skeleton; the parts it *doesn't* cover become `Hole` sub-goals with
   mechanically-derived local rows (loop-unrolled folds, live-variable
   analysis at the final expression) — the same ladder runs again, one
   grain finer, and fold-up re-verifies the full row set.
5. **Local repair (P7-B).** A held-out row that fails refutes the accept;
   the trace (descent's own derivations, reused as expectations) localizes
   the failure to a specific hole; only that hole re-solves with the
   counterexample folded into its row set. No hole found → an honest
   refusal, never a silent global re-solve.
6. **Chunk mining + self-teach (P7-C).** Recurring 2–4-statement idioms are
   mined from the corpus, role/slot-abstracted, and the survivors (past a
   pre-registered quantile threshold) feed a rules-decided self-teach mint —
   escaping the family-collapse the flat construction grain hit in P3.

## The measured trajectory (honestly, including the nulls)

| moment | instrument | score |
|---|---|---|
| P0 baseline | 26-item write battery, fresh boot | 7/26 |
| P6 MAIN | 125-task battery | 65/125 = .520 [.433, .606] |
| P6.5 | same, stall fixed in rules | 77/125 = .616 [.528, .697] |
| P7-D MAIN-P7 | descent + repair + chunks | 80/125 = .640 [.553, .719] |

No aggregate step above is CI-separated on its own — the arc's honest claims
are the **paired identity lists** at each step (which specific task ids
flipped, verified against a byte-identical twin run), not the headline
percentage. Registered nulls that were measured and kept, not hidden: the
P2 corpus-coverage prediction over-shot (56.4% actual vs 83.3% predicted,
with the miss fully enumerated by construct); P3's codebook saturated at 16
quanta vs a predicted [40, 220] band (diagnosed as a grain issue, not an MDL
issue — P7-C's idiom grain later escaped the same collapse); and ARC 6 (a
priced-but-reverted candidate that would have manufactured 12 false accepts
via a `list`/`tuple` value-layer collapse) is a deliberate NO-GO kept in the
record rather than quietly dropped.

## Where the code lives

- Rust: `runners/dsl/src/prog_eval.rs`, `synth_enumerate.rs`, and the
  ~26 `Prog*` Term variants in `term.rs`.
- Python world adapters / IR emitters: `domains/prog_synthesis.py`,
  `domains/prog_retrieval.py`, `domains/prog_ir_emit.py`,
  `domains/prog_ir_lua.py`, `domains/prog_ir_rust.py`,
  `domains/render_python.py`, `domains/mbpp_spec.py` — all mechanical
  read/render translators per `CLAUDE.md`'s world-adapter rule, not where
  the synthesis decisions happen.
- Seeds: `seeds/program_synthesis.json` and neighbors.
- Gates: `tests/test_program_synthesis_migrated.py`,
  `tests/test_prog_*_migrated.py`, `tests/test_mbpp_*_migrated.py`.

## For the full history

`docs/research/program_synthesis/PROGRAM_SYNTHESIS_ARC_SUMMARY.md` is the
reviewer's entry point for the whole P0→P7 arc (phase-by-phase commit
ledger, every registered deviation). The individual phase PREREG/RESULTS/
notes documents (P0 through P7-D, plus the separately-numbered ARC2–ARC6
sub-arcs) live alongside it in `docs/research/program_synthesis/` — see that
folder's `INDEX.md`.
