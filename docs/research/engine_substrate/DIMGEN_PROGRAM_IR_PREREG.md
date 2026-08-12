# DimensionGenerator ↔ Program IR — pre-registration

Companion to `CROSS_DOMAIN_SHAPE_SPIKE.md` §7.4 (read in full before this
doc was written), whose closing sentence is this rung's charter, quoted
verbatim:

> "A physical transform and its formula are the same cross-frame map, and
> the substrate can be made to demonstrate that behaviourally with no new
> encoding."

Also read in full before writing this doc, per the task brief:
`RULE_SIGNATURE_TO_RUST_RESULTS.md` §1-2 (the `emit_prog_ir` / P1-subset
harness this rung reuses unmodified) and its own PREREG's registered-vs-
suspected discipline, which this doc follows.

**Worktree:** `/home/matt/ocelot-dimgen-progir`, branch
`dimgen-program-ir`, detached from `main` at `c35ab4d` (`Research spike:
cross-domain shape comparison, via synesthesia -- a shape, not one
answer`), verified via `git log --oneline -1 main` immediately before
`git worktree add`.

---

## 0. What was read, and what was already run, BEFORE this doc was locked

Per the house discipline this project uses (`RULE_SIGNATURE_TO_RUST_PREREG.md`'s
own convention): scoping this measurement required reading the Rust source
closely enough that one of the three registered questions below was
already answered by the time this doc was written. Reported honestly
rather than re-staged as a blind prediction:

- **Read in full, source not doc comments:** `runners/dsl/src/shape_decode.rs`
  — `apply_linear_once` (`:752-782`), `rotate90_once` (`:605-622`),
  `reflect_once` (`:629-637`), `scale_pow2_once` (`:659-683`),
  `modular_step_once` (`:713-735`), `apply_generator_once`'s kind dispatch
  (`:836-852`), and `eval_dim_infer` (`:2090-2226+`, the `DimInfer` Term
  evaluator) — to determine (a) the exact per-cell arithmetic each shipped
  generator performs and (b) that none of these functions is exposed to
  Python directly (no `pub fn`, no `#[pyfunction]` wrapper) — the ONLY
  reachable entry point is the `DimInfer` Term via `native.evaluate(...)`.
- **Read `runners/dsl/src/term.rs:1082-1167`** (`DimInfer`'s doc comment
  and field list) to get its exact input/output contract (`goal`,
  `codebook_type`, `generator_type`, `max_dims`, `field` in; a Dict with
  `explained`/`identity`/`generator`/`k`/`dims`/`transforms`/`checked` out).
- **Read `seeds/shape_decode_loop.json`** and extracted the five shipped
  `DimensionGenerator` nodes verbatim (§2 below) — this is the "five
  shipped generators" the task's §3 refers to, confirmed by grep, not
  assumed from memory.
- **Read `tests/test_dimension_inference_migrated.py`** in full (its
  `_boot`/`_add_part`/`_observe_decoded` helpers and its TROMINO/rotation
  fixtures) as the worked precedent for driving `DimInfer` from Python —
  this rung's own test harness follows its conventions where they apply,
  but calls the RAW `DimInfer` Term directly (`native.evaluate`) rather than
  going through the `sd_infer_dimension` seed rule, because the object
  under test here is `apply_linear_once`'s arithmetic itself, not the
  rule-driven recognise/mint pipeline (which is already gated elsewhere).
- **Read `domains/rule_signature.py:255-297`** in full as the worked
  `emit_prog_ir(...)` → `add_term_subgraph` → `term_subgraph_json` →
  `ProgEval` call-site example named in the task brief, and reused its
  exact idiom (§4 below) rather than inventing a new one.
- **ALREADY RUN, before this doc was written** (§4 of the task's own
  instructions: "the single number nobody has" — AR-3 below): `emit_prog_ir`
  on five pointwise Python functions, one per shipped generator's per-cell
  map (arithmetic only — no host loop over the whole signature, since the
  loop-over-cells is host orchestration, not part of the map itself, exactly
  as `apply_linear_once`'s own doc comment frames it: "maps EACH CELL's
  coordinate vector `v`..."). **Result, disclosed here rather than staged as
  a blind prediction: all five returned `ok=True`, zero blockers.** This
  is reported as the actual measured answer to AR-3 below, not re-run for
  drama; §1 registers why this was NOT the expected default outcome before
  running it, so the registration is not vacuous.

**What was genuinely NOT yet run when this doc was locked, and is
registered blind below:** the rendering-equivalence chain (AR-1/AR-2) —
whether `DimInfer`'s `apply_linear_once` path and a graph-resident
`ProgEval` execution of the matching Program IR agree, over a real lattice,
via the Rust engine (not assumed from reading the arithmetic on paper).
Reading two functions and confirming they encode the same formula on paper
is not the same claim as watching the Rust interpreter and the compiled
generator agree at runtime — REPL type-o's, sign errors in the matrix
convention, or a mismatched row/column-major reading would all be invisible
to a paper read and visible to a live run. That is what AR-1/AR-2 test.

---

## 1. AR-1 — does the `linear` generator kind, exercised through the real
   `DimInfer` path, render identically to a `ProgEval` execution of the
   corresponding Program IR, over a fixed integer lattice?

**Method (registered before running):**

1. Build a `ShapeSignature` "held part" whose signature is a small integer
   lattice of `["cell", r, c, "x"]` relations (predicate `cell`, coord
   slots 1/2, a constant value slot 3), `dim_types=["pred","coord:r",
   "coord:c","val"]` — the exact convention
   `tests/test_dimension_inference_migrated.py` already uses.
2. Mint ONE `DimensionGenerator{kind:"linear", coord_dims:[1,2],
   matrix:[m00,m01,m10,m11], params:[1]}` node as the codebook (an
   isolated, test-scoped fixture — not installed into any shipped seed).
3. Compute the GOAL two ways and compare them to each other AND separately
   to the held signature transformed via the real Rust path:
   a. **Python-reference** — apply `out0 = m00*(r-min_r) + m01*(c-min_c)`,
      `out1 = m10*(r-min_r) + m11*(c-min_c)` to every lattice cell by hand,
      in plain Python (the independently-typed formula, not derived from
      either engine path).
   b. **`DimInfer` / `apply_linear_once`** — call the raw `DimInfer` Term
      (`native.evaluate({"type":"DimInfer", "goal": <Lit of the
      python-reference goal>, ...})`) with the minted linear generator as
      the sole codebook entry. Read the `identity`/`explained`/`dims`
      fields off the returned Dict.
   c. **`ProgEval` on graph-resident Program IR** — `emit_prog_ir` a
      pointwise `linear_map_point(v0, v1, min0, min1, m00, m01, m10, m11)`
      Python function computing the identical formula, install it via
      `add_term_subgraph`, read it back via `term_subgraph_json` (so what
      executes is what the graph holds, exactly like
      `rule_signature.py::signature_program`), then run it once per lattice
      cell via `native.evaluate({"type":"ProgEval", ...})` and collect the
      per-cell outputs.
4. Compare (a) vs (c) element-wise (a direct value diff) and confirm (b)
   reports `identity=True`/`explained=True`/`dims=()` (which is only
   possible if `apply_linear_once`'s actual output equals the (a) goal
   EXACTLY, cell for cell, under `build_candidate`'s exact-match branch —
   see `shape_decode.rs:1650-1654`). This is a three-way chain through one
   common reference, the same shape of comparison
   `RULE_SIGNATURE_TO_RUST_RESULTS.md` §4.1 ran for a different algorithm.

**Falsifiable predictions, registered before running:**

- **P1 (GO condition):** (a) == (c) element-wise on every lattice cell,
  AND (b) reports `identity=True, dims=()`. If both hold, the `linear`
  generator kind and the Program IR execution of the same formula are
  observationally indistinguishable over the tested lattice — this is the
  narrow, specific, falsifiable form of the charter's claim.
- **P2 (a plausible NO-GO):** `apply_linear_once`'s row/column convention
  (`matrix[i*n+j]`, `acc += matrix[i*n+j] * (cols[j][cell] - mins[j])`,
  `shape_decode.rs:768-772`) does not match the naive
  `out_i = sum_j M[i][j] * v_j` reading on a first attempt — e.g. a
  transposed-matrix mismatch — and (b) reports `identity=False` on the
  first try. This is registered as a REAL possible outcome, not a
  strawman: matrix row/column convention mismatches are exactly the kind
  of silent-wrong error the frame/continuum invariant's own text warns
  about, and getting it wrong on paper vs confirming it live is the entire
  reason AR-1 is a live-run bar and not a source read.
- **P3 (a different plausible NO-GO):** `emit_prog_ir` on the pointwise
  linear-map function itself fails (blocked construct) — registered as
  unlikely given RULE_SIGNATURE_TO_RUST's own P1 corpus statistics
  (arithmetic BinOp/AssignVar/Return are the P1 subset's home ground, not
  its edge), but not ruled out until run.

## 2. AR-2 — the five shipped generators, exact contents (read from source,
   not recalled)

`seeds/shape_decode_loop.json`, five `DimensionGenerator` nodes:

```
{"name":"rotation90",   "kind":"rotation90",  "coord_dims":[1,2], "params":[1,2,3]}
{"name":"reflection_r", "kind":"reflection_r","coord_dims":[1,2], "params":[1,2]}
{"name":"reflection_c", "kind":"reflection_c","coord_dims":[1,2], "params":[1,2]}
{"name":"scale2",       "kind":"scale2",      "coord_dims":[1,2], "params":[1,2,3]}
{"name":"cycle4",       "kind":"modular",     "coord_dims":[1],   "params":[1,2,3], "modulus":4}
```

**None of the five shipped generators is `kind:"linear"`.** `"linear"` is
the sixth, MINT-ONLY kind (`sd_gen_check`/`sd_mint_linear_generator` in the
same seed) — the only kind whose transform is graph-data-driven rather than
Rust-dispatched (`shape_decode.rs:414-428`'s own doc comment, quoted in the
charter). AR-1 above therefore mints a `linear` generator as an isolated
test fixture (never installed into a shipped seed) specifically because it
is the one kind whose map IS graph data already — the exact pairing §7.4
names. AR-3 below is a DIFFERENT, complementary question: how many of the
FIVE SHIPPED (Rust-dispatched) generators' underlying per-cell maps are
themselves expressible in the P1 subset AT ALL, regardless of whether they
ship as `kind:"linear"` today.

## 3. AR-3 — the single number: P1-expressibility of each shipped
   generator's per-cell map

**Method (already run — see §0's disclosure):** for each shipped
generator, write ONE pointwise Python function computing exactly the same
per-cell arithmetic as its Rust counterpart (`rotate90_once`/
`reflect_once`/`scale_pow2_once`/`modular_step_once`), parameterised by the
cell's own coordinate(s) plus whatever shape-level constants
(`min_r`/`min_c`/`max_r0`/`modulus`) that Rust function reads from the
WHOLE signature — because the whole-signature reduction (computing a
bounding-box min/max over every cell) is HOST ORCHESTRATION in the Rust
function (a loop over `sig`), not part of the map itself, exactly as
`apply_linear_once`'s own doc comment frames the per-cell map ("maps EACH
CELL's coordinate vector"). This is the same level of abstraction the task
brief's phrase "each generator's matrix multiply" names — the mathematical
map, not the caller's iteration boilerplate. Writing the WHOLE
signature-iterating Rust function verbatim in Python (with its `Vec`
push/iteration) would conflate "is the MAP P1-expressible" with "is an
unbounded host loop over an unknown-length collection P1-expressible" —
a different and less interesting question this rung is not asking, and
the task brief's explicit warning against contorting the test cuts against
inflating scope this way as much as it cuts against deflating it.

**Falsifiable prediction, registered before running (per §0, already
measured — reported honestly, not restaged):** the task brief itself names
the two live possibilities without picking one — "if the answer is 'none
of the five generators are expressible... that is exactly what §7.4
predicts'" vs an unstated GO count. Prediction registered at design time,
before running: **most or all of the five would be `ok=True`**, because
each per-cell map, once separated from its host loop, is pure scalar
integer arithmetic (subtraction, multiplication, one `%`) — squarely
inside the P1 arithmetic BinOp/AssignVar/Return home ground
`RULE_SIGNATURE_TO_RUST_RESULTS.md` §1 already measured as unproblematic,
and NOT anywhere near the blockers that rung found (`ComprehensionDict`,
`DefFn`, `RecvMethod:append`, `CompTargetComplex`, `IsinstanceMultiType` —
none of which a pure arithmetic function touches). This prediction is
registered as the LIKELY-GO case specifically so a NO-GO reported below
would be a genuine surprise worth investigating, not a foregone conclusion
dressed as a test.

## 4. GO/NO-GO bar for the payoff (edge type + Γ production)

Per the task brief: **only if AR-1's equivalence check (P1) is confirmed
live** does this rung build anything. AR-3 (the P1-expressibility count)
is reported regardless of AR-1's outcome — it answers a real, standing
question about the tree (per `RULE_SIGNATURE_TO_RUST_RESULTS.md`'s own
"one unpriced item, two more found" pattern) independent of whether the
payoff is built. If AR-1 comes back NO-GO (P2/P3), this document and its
RESULTS companion are the complete deliverable, no code changes ship, and
the worktree's commit contains only these two docs recording the null —
per the task's explicit standing instruction that a clean NO-GO is a
complete, valuable, expected-possible outcome.

If AR-1 is GO: build exactly one edge type (`denotes_map`, chosen over
`rendered_by` because the DimensionGenerator is the SOURCE of the relation
— "this generator DENOTES this map" reads more naturally than "this
generator IS RENDERED BY this program", and the map is the shared
referent, not a rendering of the generator) linking the minted `linear`
`DimensionGenerator` test node to the installed Program IR root node
(`Term.ProgSeq`, per the emitted IR's own root type), with a REAL
`Production` declared via `substrate.add_production(...)` (never
`add_edge_unchecked`) — paying off the exact debt
`RULE_SIGNATURE_TO_RUST_RESULTS.md` §4.2 named and left unpaid.

## 5. Explicitly out of scope (§7.4's own list, restated so it is not
   silently expanded mid-rung)

Any unified cross-domain encoding; any codebook pool merge; retrofitting
Concepts with relational structure; consolidation (the literature's "a
frequent mapping migrates into the target domain" mechanism); any
benchmark-movement claim. Also out of scope per the task's explicit
instruction: reproducing `rotate90_once`/`reflect_once`/`scale_pow2_once`/
`modular_step_once` EXACTLY including their bounding-box normalisation as a
graph-resident whole-signature Program IR loop — AR-3 tests the per-cell
map's expressibility, not a full re-implementation of the host loop around
it, and building that full loop is not named anywhere in §7.4 as part of
this slice.

## 6. Regression scope

This rung, if it builds anything, adds one new node type
(`DimGenLinearDemo`-scoped test fixture data, not a shipped seed change),
one new edge type (`denotes_map`), and one new `Production` — all confined
to a dedicated test file and, if AR-1 is GO, a small demonstration script.
No shipped seed, no existing Rust file, no existing Python production path
is touched. Per the task's own guidance or a full-suite run only if shared
code is touched: since nothing shared is touched, this rung's own new test
file is the regression gate, run standalone; `pytest tests/ -k migrated`
is NOT run in full unless AR-1 turns out to require touching something
shared (it should not, per the design above).
