# Rule signature → Rust — prereg

Registers the bars for `SHAPE_TYPE_VOCABULARY_SPIKE.md` §10.1's own
**"largest unpriced item in the whole arc"**:

> "**Anything that moves a signature computation from Python into Rust.**
> Three of the four signature functions of §3.2 are Python. […]
> `where_signature_json` is now read by production selection
> (`RULE_SIGNATURE_PRODUCTION_WIRING_RESULTS.md` Part 1). **Under
> `CLAUDE.md`'s architecture rule, a signature the agent's own decisions
> depend on wants to be a Rust Term, and it is not one.** I flag this as
> the largest unpriced item in the whole arc — not as a violation today
> (computing a signature is arguably mechanical translation, and the
> *decision* is a graph-resident Term), but as the thing that makes the
> signature un-self-repairable, which is the payoff the migration exists
> for."

and §10.2's own cost row:

> | move a signature computation to a Rust Term | `term.rs`, `jsonio.rs`, `reflect.rs`, `term_variants.rs` | a language-extension rung | **high** — and `NUM_TERM_VARIANTS` is a hard array length |

**Worktree:** `/home/matt/ocelot-rule-signature-to-rust`, branch
`rule-signature-to-rust`, detached from `main` at `b5a235e`.
**Engine at registration:** `runners/dsl/python/substrate_rs/_native.abi3.so`
sha256 `8963fb4dccaad4f8b07550ac8c8000583a5350f9d1d07d7057850b922a35f115`.

---

## The subject

`domains/rule_signature.py::rule_signature(where_clause) -> frozenset[tuple]`
— the §5.3 path-addressed, alpha-renamed flattening of a rule's `where`
clause into two row kinds:

```
("rt", path, term_type)          -- one row per Term node
("ra", path, field, atom)        -- one row per scalar field
```

with `Var.name` / binder `var_name` positionally alpha-renamed (`"?0"`,
`"?1"`, … in first-DFS-appearance order over the whole clause) and every
other scalar kept literal. Since
`RULE_SIGNATURE_PRODUCTION_WIRING_RESULTS.md` Part 1 this is **live in
production selection**: `_pick_acting_rule` / `_pick_reply_rule`
(`domains/reflective_faculty.py`) fall back to a `where_signature_json`
ranking when the `keywords_text` `StringIndexOf`-`Sum`-`Argmax` abstains,
which took the informative Class A oracle from 0/12 → 11/12 with Class B
unchanged at 12/12.

The computation is Python. That is the gap.

---

## What was read BEFORE this doc was written (registration honesty)

So a later reader can tell which of the answers below were already
suspected and which were genuinely open at registration:

- `domains/rule_signature.py` in full; `RULE_SIGNATURE_SLICE_RESULTS.md`,
  `RULE_SIGNATURE_PRODUCTION_WIRING_RESULTS.md` (Part 1 in full),
  `SHAPE_TYPE_VOCABULARY_SPIKE.md` §10.1/§10.2.
- `runners/dsl/src/term_variants.rs` in full (it is a GENERATED file —
  header line 1: "GENERATED — do not hand-edit", produced by
  `tools/gen_term_variants.py`, with a `variant_table_covers_the_enum`
  test in `scale_audit.rs` that fails on drift). `NUM_TERM_VARIANTS = 213`.
- `term.rs`'s shape-math family doc comments (`AntiUnify`, `FixedCount`,
  `Covers`, `CoversOpen`, `AntiUnifyWitness`, `Substitute`, `Unify`,
  `StructSim`) — read, not skimmed.
- The `Prog*` variant block in `term.rs` (lines ~1995–2075) and its
  inert-under-`evaluate()` / executed-only-under-`ProgEval` contract
  (`term.rs:5839-5875`, `prog_eval.rs`), plus `domains/prog_ir_emit.py`'s
  header, `NATIVE_ORACLES`, `NATIVE_RECV_ORACLES`, `_RECV_BLOCKED_METHODS`
  and the header of `tests/test_prog_read_python_migrated.py`.
- `runners/dsl/src/reflect.rs`'s header + `term_to_subgraph`.

**Already suspected at registration, and therefore NOT claimable as a
discovery of this rung:** that a `ProgEval`-executed, `emit_prog_ir`-emitted
Program IR is a candidate zero-new-Term route. **Genuinely open at
registration:** whether the flattening is actually EXPRESSIBLE in the P1
subset (the mutating-method blockers `RecvMethod:append`/`add`, no nested
`def`, no recursion are real and were known to be real), whether it is
byte-identical, whether it is fast enough to sit in a production selection
path, and whether the `AntiUnifyWitness`-family alone can do it.

---

## AR1 — does the EXISTING Term algebra already suffice?

**Bar.** Answered by reading the actual variant definitions and by a
running probe, never by the cost table's own hedge. Three candidate routes
are enumerated in advance, and AR1 is MET if any one of them reproduces
`rule_signature` **byte-identically** (Python `==` on the returned
`frozenset`) on the real rule population:

- **R1 — shape-math family.** `AntiUnifyWitness`'s `sigmas` are
  position-PATH → subterm Dicts, which is path-addressed flattening of a
  sort. Question: can `AntiUnifyWitness`/`Substitute`/`Covers`/`StructSim`,
  composed, produce the §5.3 row set (including first-appearance-order
  alpha renaming) with no new variant?
- **R2 — graph reflection.** `reflect.rs::term_to_subgraph` already turns
  any Term into `Term.<Variant>` nodes with `child.<field>` edges. Question:
  can graph Terms (`NodesOfType`/`Neighbours`/`MapSet`/`StringConcat`/…)
  walk that mirror and build the rows, given that the DSL has no recursion
  combinator and the row PATH is a root-relative route?
- **R3 — Program IR + `ProgEval`.** Express the flattening as hub Program
  IR (`Prog*` Terms — graph-resident data, reflect-round-tripping, matched/
  decoded/rendered/repaired by the existing prog_read/prog_repair
  machinery) and execute it with the one `ProgEval` window. Question: is
  the algorithm inside the P1 subset at all, given no nested `def`, no
  recursion, and `append`/`add` being named `RecvMethod:` blockers?

**AR1 verdict values:** SUFFICES (name which route, with the byte-identity
evidence) / DOES NOT SUFFICE (name what each of R1/R2/R3 structurally
cannot do — enumerated, not characterised).

## AR2 — if a new Term IS needed, what does it actually cost, measured

**Bar.** Not the abstract "language-extension rung" label. The cost is
measured against the **two real precedents in this tree's own history**,
both from this same week, both found by `git log -S` over `term.rs`:

| precedent | commit | plumbing files touched |
|---|---|---|
| `MetaShapeMint` | `933b413` | `term.rs +35`, `jsonio.rs +19`, `reflect.rs +10`, `term_variants.rs +4` (generated) — algorithm body separately in `shape_decode.rs` |
| `CoversOpen` | `98644a3` | `jsonio.rs +10`, `reflect.rs +10`, `term_variants.rs +4` (generated), `term.rs +329` (variant + impl + unit tests) |

AR2 is answered by: (a) naming the exact edit set a `WhereSignature`-style
variant would need, (b) stating whether that set is larger, equal to, or
smaller than the two precedents, and (c) naming the parts that are NOT
mechanical (engine `--release` rebuild + `sha256sum` verification +
coherence probe + the `variant_table_covers_the_enum` regeneration).

**Registered sub-claim, to be confirmed or refuted:** *moving the body of
this computation into Rust does not by itself close the "un-self-repairable"
gap §10.1 names* — Rust source is exactly as unavailable to the agent's
Experiment→judge→adopt machinery as Python source is. What §10.1's payoff
actually requires is that the computation be **graph-resident data**. If
this sub-claim survives, a Rust-variant GO is a weaker outcome than a
graph-resident GO even if the Rust variant is cheap. Registered here so it
cannot be retrofitted.

## AR3 — GO / NO-GO, registered BEFORE AR1/AR2 are known

- **GO-A (zero-new-Term, graph-resident route)** iff ALL of:
  (i) one of R1/R2/R3 reproduces `rule_signature` byte-identically on
  **100%** of the real `RuleSummary` where-clause population on a full
  `load_all_seeds` boot (the same population `ensure_where_signature`
  already walks; ≥46 rules per `RULE_SIGNATURE_SLICE_RESULTS.md` §1), AND
  (ii) the wired production numbers are UNCHANGED (Class A informative
  11/12, Class B informative 12/12 — this is a representation migration,
  not a behaviour change), AND (iii) no engine rebuild is required.
- **GO-B (new Rust Term variant)** iff GO-A fails AND the AR2-measured
  edit set is ≤ the `CoversOpen` precedent AND the engine builds
  `--release` clean, passes the coherence probe, and `sha256sum` confirms
  the committed `.so` is the built one.
- **NO-GO** otherwise → this rung ships a precise sizing document and no
  code, per the brief's own sanction. A NO-GO must still enumerate what
  the build would need, not merely assert expense.

## AR4 — if GO: live demonstration

1. **Byte-identical.** New computation `==` Python `rule_signature` on
   every real where-clause in the booted population, and on the 40-probe
   oracle's own inputs (reusing `scripts/rule_signature_measure.py`'s
   `CLASS_A_*`/`CLASS_B_*` tables and the committed
   `scripts/rule_signature_measurement_results*.json`, unedited — no new
   oracle invented).
2. **Genuinely resident**, not a Python re-implementation in a costume:
   the artefact must round-trip through the substrate's own reflection
   (`add_term_subgraph` → `term_subgraph_json` canonically identical) and
   be executable from the graph, i.e. addressable the way other Terms are.
3. **Wired at the real production call site** (`ensure_where_signature`,
   which `_pick_acting_rule`/`_pick_reply_rule` both call) with the
   POST-wiring production numbers re-measured and unchanged.
4. **Python left as a thin caller**, per the brief — no second
   decision, no divergent second implementation left live and unreachable.

## AR5 — no regression, paired failing-node-id LISTS not counts

Per CLAUDE.md's own retracted-baseline rule ("A BASELINE MUST BE A LIST OF
NODE IDS, NEVER A COUNT OR A CHARACTERISATION"):

- Baseline captured on this worktree at `b5a235e` **before** any edit, on
  the production-wiring rung's own 8-file suite
  (`tests/test_acting_variant.py`, `tests/test_structural_variant.py`,
  `tests/test_self_delta.py`, `tests/test_gap_awareness_migrated.py`,
  `tests/test_self_concern_promote_migrated.py`,
  `tests/test_agent_authors_new_rule_migrated.py`,
  `tests/test_composers_graph.py`, `tests/test_experiment_composer.py`),
  plus `tests/test_prog_ir_migrated.py` and
  `tests/test_prog_read_python_migrated.py` if route R3 is taken.
- Re-run after. The two sorted failing-node-id lists must be
  **byte-identical** (`diff` empty). A count is not evidence.
- If any Rust is touched: `cargo test --lib` before/after as well.

## Registered non-goals

- Not building a full Experiment→judge→adopt cycle **against** the
  signature computation — the brief itself scopes that out. The bar is
  that the computation becomes the KIND of thing that machinery can reach.
- Not touching `domains/analogical_thinking.py`,
  `runners/dsl/src/py.rs`, `world_adapter.py`'s checkpoint-load region,
  `seeds/meta_shape_growth.json`, `seeds/shape_decode_loop.json` — owned by
  other threads today.
- Not changing selection BEHAVIOUR. Any measured change in the 24
  informative oracle rows is a FAILURE of AR4, not an improvement.
