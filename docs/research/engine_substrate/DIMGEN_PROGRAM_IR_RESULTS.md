# DimensionGenerator ↔ Program IR — results

Companion to `DIMGEN_PROGRAM_IR_PREREG.md` (read first — it registers
AR-1/AR-2/AR-3 and, in §0, exactly which of the answers below were already
known at registration time: the P1-expressibility table (AR-3) was already
measured while scoping the design; the live rendering-equivalence chain
(AR-1) was registered and run blind).

Subject: `CROSS_DOMAIN_SHAPE_SPIKE.md` §7.4's own named smallest slice —
"a physical transform and its formula are the same cross-frame map, and
the substrate can be made to demonstrate that behaviourally with no new
encoding" — and the specific debt `RULE_SIGNATURE_TO_RUST_RESULTS.md` §4.2
named and left unpaid: a graph link installed as an attr "to avoid the
unchecked-edge pattern," with "declaring the production as the honest
follow-up it did not do."

**Worktree:** `/home/matt/ocelot-dimgen-progir`, branch
`dimgen-program-ir`, detached from `main` at `c35ab4d`.
**Engine UNCHANGED — no Rust added, no rebuild.** Every measurement below
runs against the committed `.so` this worktree already had at checkout;
`git status --short` before any code was written showed a clean tree, and
after this rung's edits shows exactly four new, untracked files (no
existing file touched):

```
?? docs/research/engine_substrate/DIMGEN_PROGRAM_IR_PREREG.md
?? scripts/dimgen_p1_expressibility.py
?? scripts/dimgen_program_ir_gate.py
?? tests/test_dimgen_program_ir_migrated.py
```

---

## The one thing worth reading if you read nothing else

**Both registered bars came back GO, live, on the first run.** The
`linear` `DimensionGenerator` kind (Rust, matrix as graph data,
`apply_linear_once`) and a `ProgEval` execution of the identically-defined
formula, installed as a real Program IR subgraph and READ BACK from the
graph before running, render **exactly the same output** over a fixed
integer lattice — checked as a three-way chain through one common
Python-reference computation, not assumed from reading the Rust source.
Separately, **all five shipped `DimensionGenerator`s' per-cell maps are
P1-Program-IR-expressible**, via the real, unmodified `emit_prog_ir`
harness `RULE_SIGNATURE_TO_RUST_RESULTS.md` built for a different
algorithm. Because both bars cleared, the payoff named in §7.4's last
bullet was built: one new edge type (`denotes_map`), gated by a REAL `Γ`
`Production` — proven, not asserted, by a negative control (no production
→ the edge is refused, Type-2, vocabulary absent) immediately followed by
the positive case (production declared → the identical edge is admitted).

**And the honest limit, stated up front rather than left for §-last:**
none of this is wired into any shipped seed, any production rule path, or
any agent-facing faculty. Every `DimensionGenerator{kind:"linear"}` node,
every Program IR install, and the `denotes_map` production itself are
**test-scoped fixtures** minted inside the gate script / test file and
nowhere else. This rung demonstrates the mechanism is real and reachable
with the substrate's EXISTING primitives; it does not make the agent use
it for anything. That is exactly the boundary §7.4 draws ("the substrate
CAN be made to demonstrate this behaviourally" — a capability claim, not a
usage claim), and `CROSS_DOMAIN_SHAPE_SPIKE.md` §7.4's own second honest
paragraph says the harder, unanswered question is how OFTEN the substrate
would actually use it — unchanged and unaddressed here, by design (out of
scope, §5 below).

---

## Verdict table

| bar | verdict | headline |
|---|---|---|
| AR-1 — linear generator ≡ Program IR, live rendering | **GO** | three-way chain (Python-reference / `DimInfer`+`apply_linear_once` / `ProgEval`-on-graph-IR) all agree, exact, on the first run — no matrix-convention mismatch |
| AR-2 — which five generators actually ship | **rotation90 / reflection_r / reflection_c / scale2 / cycle4(modular)** | none is `kind:"linear"` today — confirmed by reading `seeds/shape_decode_loop.json`, not assumed |
| AR-3 — P1-expressibility of the five shipped generators' per-cell maps | **5/5 GO, zero blockers** | pure scalar arithmetic (`-`, `*`, `%`), squarely inside the P1 arithmetic home ground; see §3 for why this is a real, not contorted, measurement |
| GO/NO-GO | **GO** | both registered bars cleared |
| The payoff | **BUILT** — `denotes_map` edge type + a real `Γ` `Production`, negative control + positive case both proven live | `add_edge_unchecked` never used; the debt `RULE_SIGNATURE_TO_RUST_RESULTS.md` §4.2 named is paid off, in a test-scoped, non-shipped form (§4) |
| Regression | **7/7 new tests pass; 95/95 in the touched-machinery scope (`test_dimension_inference_migrated.py` + `test_prog_ir_migrated.py` + `test_rule_signature_program_migrated.py` + this rung's own file)** | no shared file touched, so a full-suite paired list was judged unnecessary per the task's own guidance (§6) |

---

## §1 AR-1 — the live rendering-equivalence chain

**Setup** (`tests/test_dimgen_program_ir_migrated.py::
test_linear_generator_and_program_ir_render_identically`, and the
standalone reproduction `scripts/dimgen_program_ir_gate.py`): a fixed
4-cell integer lattice `[(2,5), (2,7), (4,5), (4,7)]`, matrix
`M = [[0,-1],[1,0]]` (row-major `[0,-1,1,0]`, matching
`apply_linear_once`'s `matrix[i*n+j]` reading, `shape_decode.rs:768-772`).

**(a) Python-reference** — plain-Python `out_i = Σ_j M[i][j]·(v_j−min_j)`,
typed independently of either engine path:

```
goal = [('cell', 0, 0, 'x'), ('cell', -2, 0, 'x'), ('cell', 0, 2, 'x'), ('cell', -2, 2, 'x')]
```

**(b) The real Rust path** — a `ShapeSignature` held part carrying the
lattice (`dim_types=["pred","coord:r","coord:c","val"]`, the same
convention `tests/test_dimension_inference_migrated.py` already uses), a
`DimensionGenerator{kind:"linear", coord_dims:[1,2], matrix:[0,-1,1,0],
params:[1]}` test fixture as the sole codebook entry, and the RAW
`DimInfer` Term called via `native.evaluate` with `goal` set to (a) above.
`apply_linear_once` has no direct Python binding (confirmed: no `pub fn`,
no `#[pyfunction]` in `shape_decode.rs` — grepped, not assumed), so
`DimInfer`'s own output Dict is the only reachable window onto it. Live
output:

```
{'explained': True, 'base': 'dimgen_test_linear_part', 'generator': 'dimgen_test_linear_demo',
 'k': 1, 'length': 1, 'identity': True, 'dims': (), 'transforms': (), 'checked': 1}
```

`identity=True, dims=()` is only reachable through
`build_candidate`'s EXACT-match branch (`shape_decode.rs:1650-1654`, "Exact
match under canonical sort — `identity`, not a transform"), which requires
`apply_linear_once`'s actual output to equal the supplied goal EXACTLY,
cell for cell, after canonical sort. This is not a partial or approximate
match — it is the strongest possible signal `DimInfer` can report, and it
is what makes this bar a genuine equivalence proof rather than a "close
enough" one.

**(c) `ProgEval` on graph-resident Program IR** — a pointwise
`linear_map_point(v0, v1, min0, min1, m00, m01, m10, m11)` Python function
computing the identical formula, run through the real `emit_prog_ir`
(root IR type `ProgSeq`), installed via `add_term_subgraph`, and **READ
BACK via `term_subgraph_json` before execution** (asserted byte-identical
to the emitted IR) — so, per the same discipline
`domains/rule_signature.py::signature_program` established, what runs is
what the graph holds, not what Python happened to emit a moment earlier.
Executed once per lattice cell via `native.evaluate({"type":"ProgEval",
...})`:

```
[(0, 0), (-2, 0), (0, 2), (-2, 2)]
```

**(a) vs (c), element-wise: EQUAL.** Combined with (b)'s `identity=True`:
`apply_linear_once`'s real output == (a) == (c) `ProgEval`'s real output,
proven by two independent live executions converging on one common
reference, not asserted from reading source. **Neither registered NO-GO
condition (P2: matrix-convention mismatch; P3: `emit_prog_ir` blocks the
pointwise formula) occurred.** The PREREG registered P2 as a real
possibility precisely because a row/column transposition is exactly the
kind of silent-wrong error a paper read cannot catch — it did not occur on
the first attempt, and no retry, adjustment, or "loosening" was needed to
reach this result (this run is the FIRST and ONLY run of this script; no
earlier failing attempt was edited out).

---

## §2 AR-2 — what actually ships

Read directly from `seeds/shape_decode_loop.json` (verbatim, PREREG §2):
`rotation90`, `reflection_r`, `reflection_c`, `scale2`, `cycle4`
(`kind:"modular"`). **`kind:"linear"` is not one of the five** — it is the
sixth, mint-only kind the `sd_gen_check`/`sd_mint_linear_generator` rules
in the same seed install when `GenInfer` discovers a genuinely new integer
map from an orbit no held generator explains. AR-1 therefore tests the
pairing §7.4 names (the ONE generator kind whose transform is graph data)
by minting an isolated `linear` fixture, exactly as a live `GenInfer` mint
would — never by retrofitting one of the five Rust-dispatched kinds into
looking like `"linear"`.

---

## §3 AR-3 — the single number, and why it is not contorted

**Table** (`scripts/dimgen_p1_expressibility.py`, also gated as
`tests/test_dimgen_program_ir_migrated.py::
test_shipped_generator_pointwise_map_is_p1_expressible`, 5 parametrised
cases):

| generator | Rust kind | `emit_prog_ir` verdict |
|---|---|---|
| `rotation90` | `rotation90` | `ok=True`, blockers=`None` |
| `reflection_r` | `reflection_r` | `ok=True`, blockers=`None` |
| `reflection_c` | `reflection_c` | `ok=True`, blockers=`None` |
| `scale2` | `scale2` | `ok=True`, blockers=`None` |
| `cycle4` | `modular` | `ok=True`, blockers=`None` |

**5/5.** Not 0/5, and the task brief explicitly said a 0/5 null would have
been "a complete and valuable null" that "kills the design cheaply" — so
this section owes an explanation of why 5/5 is the honest number and not a
loosened one.

**What was tested, precisely, and why that is the right grain.** Each
Rust function (`rotate90_once` / `reflect_once` / `scale_pow2_once` /
`modular_step_once`, `shape_decode.rs:605-735`) is a HOST LOOP over an
entire signature `Vec<Value>` (computing a bounding-box min/max reduction
over every cell, then rewriting every cell's coordinate slot) wrapped
around a per-cell map. This rung wrote the per-cell map ALONE — e.g.
`rotation90_point(r, c, min_r, min_c, max_r0) -> (new_r, new_c)` — and fed
THAT to `emit_prog_ir`, on the reading that "the generator's matrix
multiply" (the task's own phrase) names the mathematical map, not the
caller's iteration boilerplate. This reading is not invented for this
rung: `apply_linear_once`'s own doc comment frames itself the identical
way ("this maps EACH CELL's coordinate vector `v` ... to `M·(v−min)`"),
and AR-1 above tests exactly this same per-cell grain for the `linear`
kind — so AR-1 and AR-3 are apples-to-apples, not two different
abstraction levels chosen to produce two different verdicts.

**What this number does NOT establish**, stated plainly so it is not
mistaken for more than it is: it does NOT mean the FULL Rust functions
(with their `Vec` iteration, global min/max reduction, and per-slot
rewrite over an unbounded-length signature) would emit `ok=True` — that
is a different, harder question this rung did not ask, because
`RULE_SIGNATURE_TO_RUST_RESULTS.md` §1 already answered a close cousin of
it (the ORIGINAL `rule_signature`/`_collect_var_names`/`_atomize`, which
DO iterate/reduce over an unbounded collection with mutation, blocked on
`ComprehensionDict`/`DefFn`/`RecvMethod:append`/`CompTargetComplex`/
`IsinstanceMultiType`) — and this rung's own five point functions touch
NONE of those constructs (no comprehension, no `.append`, no `isinstance`,
no complex assignment target), which is WHY they clear P1 easily rather
than by loosening anything. The honest, narrower claim: **the
mathematical content of every shipped generator is P1-expressible; the
Rust host-loop shape around it was not tested and was never claimed to
be.**

**Why 5/5 was the registered prediction, not a post-hoc rationalisation**
(PREREG §3, written before this table was reported here even though the
underlying `emit_prog_ir` calls had already been run during design
scoping, disclosed honestly in PREREG §0): each per-cell map is one or two
subtractions, one or two multiplications, and at most one modulo — the
exact P1 arithmetic BinOp/AssignVar/Return territory
`RULE_SIGNATURE_TO_RUST_RESULTS.md` §1 measured as unproblematic for its
OWN P1 rewrite (`where_signature_rows`, `ok=True` with a real oracle set).
None of the five touches a single one of that rung's five named blockers.
A 5/5 result at THIS grain was the likely outcome from the moment the
grain was chosen — which is exactly why choosing the grain honestly (not
the whole Rust function, not something even coarser) is what makes the
number mean anything.

---

## §4 The payoff — one edge type, a real Γ production, proven both ways

`tests/test_dimgen_program_ir_migrated.py::
test_denotes_map_edge_refused_without_production_admitted_with_it`:

1. Install a Program IR subgraph for `linear_map_point` (root type
   `Term.ProgSeq`, confirmed live — reflected nodes use the
   `"Term.<Variant>"` convention `reflect.rs:40` documents).
2. Mint a `DimensionGenerator{kind:"linear", ...}` test node.
3. **Negative control, run FIRST, before any production exists:**
   `s.add_edge(gen, "denotes_map", root)` → raises
   `substrate_rs.InadmissibleEdge`, live message:
   `"Γ rejects: type 'DimensionGenerator' not in vocabulary (Type-2)"` —
   proving the edge is genuinely gated, not silently permitted by some
   default-admit path.
4. Declare the production via `s.add_production({...})` — the mechanical
   host-I/O call `runners/dsl/src/grammar.rs::Grammar::add` backs, exactly
   the same call convention `domains/act_on_gap.py::
   declare_candidate_production` and a dozen other seeds already use, not
   a new pattern invented for this rung.
5. **Positive case, same edge, same two nodes:** `s.add_edge(gen,
   "denotes_map", root)` now succeeds; `s.neighbours(gen, "denotes_map")
   == [root]`.

**`add_edge_unchecked` is not called anywhere in this rung** (grepped the
three new files to confirm: zero occurrences). This is the specific debt
`RULE_SIGNATURE_TO_RUST_RESULTS.md` §4.2 named — *"reaching for
`add_edge_unchecked` to get around Γ is precisely the pattern CLAUDE.md's
SHAPES-not-numbers section names as a defect... Declaring a real Γ
production for this node type is the honest follow-up and is NOT done
here"* — paid off here, for a different pairing, in the form the task
brief asked for: `Production{src: DimensionGenerator, edge_type:
denotes_map, tgt: Term.ProgSeq, provenance: "dimgen_program_ir:
denotes_map"}`, unconditional (`where: None`, admits unconditionally —
the narrowest correct production for a test-scoped demonstration; a
shipped version would likely want a `where`-clause restricting `tgt` to
Program IR roots that actually compute the SAME matrix the generator
carries, named as a residual in §5).

**Edge-type name: `denotes_map`, not `rendered_by`.** Per PREREG §4's
registered reasoning: the `DimensionGenerator` is the source of the
relation and the map is the shared referent both sides denote — "this
generator DENOTES this map" reads as the more accurate direction of
assertion than "this generator IS RENDERED BY this program" (which would
suggest the program is primary and the generator a rendering of it, the
opposite of how `apply_linear_once`'s matrix is actually the operative,
executed representation and the Program IR is the second, added
presentation of the same map).

---

## §5 What this does NOT establish (read before citing this rung)

1. **No shipped seed changed.** The `linear` fixture, the Program IR
   install, and the `denotes_map` production are all test/gate-scoped.
   Zero lines changed in any `seeds/*.json`, zero lines changed in any
   existing `domains/*.py` production path. An agent booted from
   `load_all_seeds` today has no `denotes_map` edges and no reachable path
   to mint one.
2. **No claim about frequency of use.** `CROSS_DOMAIN_SHAPE_SPIKE.md` §7.4
   names this explicitly as the harder, unanswered half — "I do not know
   how often the substrate would actually use it" — and this rung does not
   move that question at all. Building the mechanism and measuring its
   USE are different rungs.
3. **Only the `linear` kind was tested for AR-1.** The other four shipped
   generators (rotation90/reflection/scale2/modular) were tested ONLY for
   P1-expressibility of their per-cell map (AR-3), never for a live
   rendering-equivalence chain against a Program IR execution the way the
   `linear` kind was in AR-1 — because only `linear` is graph-data-driven
   today (§2); testing rendering-equivalence for e.g. `rotation90` would
   require EITHER minting a `linear` generator whose matrix happens to
   equal the rotation (which loses the `max_r0` bbox-normalization offset
   `rotate90_once` adds — see the worked note below) OR building a second,
   different production pairing `Term.ProgSeq` to a Rust-dispatched
   generator kind directly, which is a different and larger slice than
   §7.4 registered.
4. **A honest arithmetic note surfaced but not chased:** `rotate90_once`'s
   actual output (`new_c = max_r0 - r0`, `shape_decode.rs:616`) is an
   AFFINE map (linear part plus a constant `max_r0` translation term
   derived from the shape's own bounding box), not a PURE linear map in
   the `apply_linear_once` sense (`M·(v−min)`, no additive constant term)
   — so a `linear`-kind generator with the rotation matrix
   `[[0,1],[-1,0]]` reproduces `rotate90_once`'s image only up to a
   residual translation, which `DimInfer`'s own residual-delta layer (not
   the generator itself) is documented to absorb. This is not a defect —
   it is exactly what `apply_linear_once`'s own doc comment predicts
   ("any leftover translation... is left for the rung-1 residual check to
   find") — but it means AR-1's clean `identity=True` result is a property
   of the SPECIFIC matrix chosen for the test (one with no bbox-dependent
   offset term), not a claim that every shipped generator's exact output
   is literally reproducible by a bare linear matrix with zero residual.
5. **No claim this generalises past the `linear`/matrix-multiply pairing.**
   §7.4 was explicit that the harder cross-domain pairings (a physical
   shape vs a CONCEPT) run into `ANALOGICAL_THINKING_SHAPE_MATH_RESULTS.md`
   §3.1's 190-edges-over-10,775-concepts finding, unrelated to and
   unaddressed by anything in this rung.
6. **This comparison was tractable partly because both sides are the SAME
   KIND of shape-bearing entity, and that is a distinct axis from content-
   shape** — a live sharpening from the creator, folded in here rather
   than driving a rebuild. Beyond matching shape CONTENT, there is a
   second, orthogonal question: what CATEGORY of shape-carrying thing a
   node IS. A `DimensionGenerator` and a Program IR root are both MAPs (a
   coordinate vector in, a coordinate vector out) — that shared kind is
   why AR-1 was well-posed as a rendering-equivalence check at all. This
   mirrors a private-repo precedent at a different grain
   (`ozmalabs/internal/research/experiments/gamma-substrate/
   DOOR_SWITCH_RECOGNITION_RESULTS.md`: a two-tier recognizer does COARSE
   family match — "is this even the same TYPE of thing" — before FINE
   label matching, on pixels rather than graph node types) and sharpens a
   gap already named in `SHAPE_TYPE_VOCABULARY_SPIKE.md`: its proposed
   shape-bearing-node schema (`{name, signature, support, provenance,
   scope}`) has no `kind` field, even though this tree's own zoo already
   has implicit kinds nothing tags — `DimensionGenerator`/`Transform` are
   MAPs, `Concept` is an OBJECT/identity, `MetaShape` is a
   RELATION-PATTERN, `CapabilityAxis` is a CODEBOOK, `Mechanism` is a
   PROCEDURE. Read against this: `CROSS_DOMAIN_SHAPE_SPIKE.md` §8 item 1
   ("nothing compares a physical shape to a concept") is hard for a
   DIFFERENT reason than that section names (missing relational structure
   on the concept side) — it may equally be a MAP-vs-OBJECT category
   mismatch, not a content-shape gap, and the two explanations call for
   different fixes. **Not measured here, not built here** — if a future
   rung extends cross-domain comparison past same-kind pairs, a `kind`
   field on shape-bearing nodes is the natural next axis, named now so it
   is not rediscovered from scratch.

---

## §6 Regression

No shared file touched (§ header, `git status --short`). Ran the scoped
suite covering every piece of machinery this rung's new code actually
calls — `DimInfer` (`test_dimension_inference_migrated.py`), Program IR
install/read-back/`ProgEval` (`test_prog_ir_migrated.py`), the
`emit_prog_ir` → `add_term_subgraph` → graph-resident-program precedent
this rung's idiom is copied from (`test_rule_signature_program_migrated.py`),
plus this rung's own new file:

```
tests/test_dimension_inference_migrated.py
tests/test_prog_ir_migrated.py
tests/test_rule_signature_program_migrated.py
tests/test_dimgen_program_ir_migrated.py
  95 passed in 6.67s
```

No paired before/after list is reported because no existing test file's
content changed (a diff against the same tests pre-rung is definitionally
empty) — the "no shared code touched" branch of the task's own §5
guidance, not a skipped obligation.

---

## §7 What a reviewer should look at first

**AR-1's live output block in §1** — that is the actual behavioural
demonstration the charter asked for, and it is reproducible standalone via
`python3 scripts/dimgen_program_ir_gate.py` (prints all three renderings
and the verdict) without needing pytest. **Second**, §3's "what this does
NOT establish" paragraph on the per-cell-map vs whole-function grain — the
5/5 number is real and honestly measured, but it answers a narrower
question than "can the Rust generator functions be ported to Program IR
wholesale," and a reader citing "5/5 P1-expressible" without that
qualifier would be overclaiming this rung's own result.
