# PROGRAM SYNTHESIS P4-A — implementation notes (`SynthEnumerate`)

**Date:** 2026-07-31. Companion to `PROGRAM_SYNTHESIS_PLAN.md` §4-P4 ("Migrate
generator.py's enumerative search into a Rust `SynthEnumerate` Term
(MDL-ordered, observational-equivalence pruning, budgeted) callable from
`ps_propose`'s fallback rung") and `PROGRAM_SYNTHESIS_PREREG.md` §6.
Engine: `runners/dsl/src/synth_enumerate.rs` (module-per-engine precedent —
shape_decode.rs / prog_eval.rs; term.rs arm is a one-line handoff).
`NUM_TERM_VARIANTS` 207 → **208**.

## 1. The Term

```
SynthEnumerate{examples, ops, consts, max_size, max_candidates, saturate_k, field}
  → Dict{found, term, term_str, size, tested, distinct, pruned_equiv,
         inadmissible, saturated, halt_reason}
```

- `examples` — evaluates to rows of `Dict{inputs: Dict{var: value}, output}`
  (the SPEC). Malformed → `found:false, halt_reason:"invalid_examples"`.
- `ops` / `consts` — optional caller-declared inventories (§4 below).
- `max_size` (≤0 → 9), `max_candidates` (≤0 → 200_000), `saturate_k` (≤0 → 3)
  — integer budgets (§3).
- `field` — the ShapeDecode/prog_eval one-key selector convention.
- `term` — the winner as a Term-JSON **string** (`Surface(Text)`), in exactly
  the wire form `jsonio::term_from_json` parses: `json.loads` →
  `substrate.evaluate(dict, env)` / `add_term_subgraph(dict)` / render, all
  gated. `term_str` is generator.py's `_term_str` rendering, byte-compatible.
- **Pure**: no substrate mutation (gated in the Rust tests: node_count
  unchanged). Candidates are built in a scratch arena and evaluated through
  the standard `evaluate()` with ONLY the example bindings in scope — DSL
  semantics govern arithmetic on both sides of the parity gate, which is why
  the parity is exact.

Python mirror: `substrate/dsl.py::SynthEnumerate` (additive; refuses to run —
the ProgEval mirror precedent, no semantics fork).

## 2. Port fidelity table (source: `domains/generator.py::synthesize`)

| generator.py piece | carried? | note |
|---|---|---|
| size/MDL-ordered bottom-up enumeration (leaves → sizes 2..max) | **YES, exact** | same size partitions, same loop order (ops outer, sa ascending, ternary `(sc, st, so)` triple order) |
| variable leaves in first-appearance order | YES (see divergence 5) | vars then consts, generator.py's order |
| const set: requested + integer-valued outputs, dedup, order kept | **YES, exact** | bools excluded from the append, as in the source |
| observational-equivalence pruning (`_canon` signatures) | **YES, exact** | bool ≠ number; int folds onto float (1 == 1.0); NaN → token; −0.0 == 0.0 |
| target match first, on a new signature (`_matches_target`, 1e-9, bool→1/0) | **YES, exact** | a matching term can never be shadowed |
| saturation halt (distinct count frozen over `saturate_k` sizes) | **YES, exact** | same history window arithmetic |
| result counters (`explored`/`distinct`) | **YES, exact** | `tested == explored`, `distinct == distinct` asserted per-spec in the parity gate |
| `term_str` rendering | **YES, exact** | asserted byte-equal on every parity spec |
| `timeout_s` | **NO — replaced** | `max_candidates` count budget (§3). Wall clocks are not in-frame integers. |
| `beam` (legacy unguided width cap) | NO — dropped | dead weight the guided path superseded; generator.py default is `None` |
| `guide` / `guide_beam` / `guide_select` / `exclude` / `return_trace` | NO — not portable | Python **callables** (host hooks), not graph data. generator.py's default (`None`) "reproduces the unguided behaviour EXACTLY" — that unguided core is what lives in Rust. Guided search stays a generator.py feature. |
| `"bc"` (commutative) op kind | collapsed into Binary — **behaviour identical** | generator.py generated BOTH (a,b) and (b,a) anyway; its same-size dedup was a literal `pass`, the collapse always done by signature pruning |
| exceptions on bad spec (`float(out)` raise) | NO — honest result | `invalid_examples` (divergence 4) |

**Deliberate divergences (each registered, each gated):**

1. **`timeout_s` → `max_candidates`.** Counts, never clocks (§3).
2. **Guided/exclusion hooks not ported** (callables; unguided core only).
3. **`beam` dropped** (legacy; default-off in the source).
4. **Malformed spec → `invalid_examples`**, never a raise/panic — a
   graph-resident primitive must return.
5. **Var order source.** generator.py reads Python dict insertion order; the
   Term reads the `inputs` Dict's stored order (canonical/sorted on the wire).
   Identical whenever spec keys are alphabetically ordered — true of every
   generator.py spec and every parity case; the counters would catch a drift.

**Parity gate result** (`tests/test_synth_enumerate_migrated.py`, on
generator.py's own demo battery — x*x+1, max(a,b), a*b+c, |x−2|): exact
`term_str`, exact `size`, exact `tested==explored`, exact
`distinct==distinct`, plus observational equality on train AND held-out
inputs. The port is order-exact, not merely observationally equal.

## 3. Budget semantics (in-frame integer discipline)

- `max_size` — exactly generator.py's: candidate tree size ≤ max_size;
  exhaustion → `halt_reason:"max_size"`.
- `max_candidates` — bounds the number of candidates **evaluated**
  (`tested`); every `register` charges 1 (leaves included). Exhaustion →
  `found:false, halt_reason:"budget", tested == max_candidates`, honest
  counters, never a value. Registration is interleaved with production
  (provably order-identical to generator.py's produce-then-register — a
  size-s candidate reads only `by_size[<s]`) so the budget binds promptly.
- `saturate_k` — the saturation window; `halt_reason:"saturated"` +
  `saturated:true`.
- No wall clock, no randomness anywhere: same inputs → byte-identical
  output (gated across fresh substrates).
- Ledger invariant (gated): `tested == distinct + pruned_equiv + inadmissible`.

## 4. The op-inventory contract (for P4-B's `ps_propose` fallback rung)

**The caller says what primitives may compose** (the held-Terms discipline).
`ops` evaluates to a list of op-name strings drawn from the kernel table —
exactly generator.py's `_op_table`:

| kind | ops |
|---|---|
| binary | `Plus` `Times` `Minus` `Div` `Min` `Max` `Gt` `Lt` `Gte` `Lte` `Eq` `And` `Or` |
| unary | `Abs` `Neg` `Not` |
| ternary | `IfThenElse` |

- **Order matters** (it is the enumeration order): pass a *list* (Tuple), not
  a Set — a Set arrives canonically sorted.
- Names outside the table are **ignored** (generator.py's `if name in
  table`); an effectively-empty inventory shows up honestly as instant
  saturation with only-leaf `distinct`.
- `ops` absent/None → generator.py's `DEFAULT_OPS`:
  `Plus, Times, Minus, Div, Min, Max, Abs, Neg, Gt, Lt, Eq, IfThenElse`.
- `consts` absent/None → `(0, 1, 2, -1)`; integer-valued spec outputs are
  appended automatically either way.
- The kernel arithmetic/comparison/IfThenElse minimum set is built in; a rung
  that wants a tighter grammar restricts, it never extends past the table —
  new primitives are new Term variants, not new table rows at call time.
- Suggested seed-rule shape for the fallback rung: bind `examples` from the
  CEGIS rows (`{inputs, output}` — exactly `cegis_faculty`'s
  `(describe(inp), oracle(inp))` spec shape), set `ops` from the goal's held
  descriptor/op facts, read `found` to branch accept vs `ps_residual_gap`,
  and store `term` (the Term-JSON string) on the accepted node —
  `add_term_subgraph(json.loads(term))` reflects it whenever the plan wants
  it as matchable subgraph instead of an attr.

## 5. Candidate evaluation (which evaluator, which env)

The main `evaluate()` (term.rs), in a scratch `TermArena`, per example row,
with a fresh `Env` containing only that row's bindings — the exact analogue of
generator.py's `term.evaluate(env, substrate)`. No ProgEval involvement:
candidates are pure DSL expression Terms (Prog-free by construction). Var
names arriving as Dict keys are real interned Syms (interned at wire-parse
time); a Surface-keyed input falls back to the shape_decode.rs `local_sym`
placeholder path, and output serialization NEVER touches
`Interner::resolve` — the module carries its own Sym→String table (so a
fabricated placeholder can never panic the interner).

## 6. Gates (all green at this commit)

- **Rust:** `cargo test --release --lib` — **684 passed / 0 failed** ×1 full
  (includes 11 new `synth_enumerate::tests` + `scale_audit::
  variant_table_covers_the_enum` over the regenerated 208-entry table).
  Link note (P1): `RUSTFLAGS="-C link-arg=-lpython3.14 -C link-arg=-L/usr/lib"`.
- **Install:** `cargo build --release` then the established ATOMIC copy
  (temp file + `os.replace` — new inode, running readers keep the old map)
  over `runners/dsl/python/substrate_rs/_native.abi3.so`, only after the full
  cargo suite was green.
- **Python:** `tests/test_synth_enumerate_migrated.py` — **11 passed** (the
  parity gate ×4 specs; op-inventory restriction; budget honesty; saturation
  honesty; returned-term reflect round-trip; SynthEnumerate-term reflect
  round-trip; cross-substrate determinism; invalid-spec honesty) — 1.3s.
  `tests/test_prog_ir_migrated.py` — **54 passed** on the new lib.
- Worktree seam (P1's recorded hazard): all pytest numbers produced with
  `--confcutdir=.` + `PYTHONPATH=runners/dsl/python:.:scripts` so the
  worktree's freshly built engine is the one measured.

## 7. Residuals (honest)

- The guided-search surface (`guide`/`guide_select`/`exclude`) remains
  Python-only in `domains/generator.py`; a graph-native guide would be a
  Term-valued scoring hook (a held Program run per size cohort) — future
  work, not smuggled in here.
- `Gte`/`Lte`/`And`/`Or`/`Not` are in the kernel table but outside
  `DEFAULT_OPS` (as in the source); no parity spec exercises them beyond the
  table plumbing.
- `cegis_faculty.py` still drives the Python `synthesize`; repointing its
  SYNTHESIZE step at this Term (and the CEGIS loop's own migration to seed
  rules) is P4-B's `ps_counterexample` path, per plan §4-P4.
