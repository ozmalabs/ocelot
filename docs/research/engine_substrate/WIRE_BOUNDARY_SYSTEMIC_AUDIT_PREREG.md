# Wire-boundary systemic audit — PREREG

## Why

`domains/prog_synthesis.py`'s `_wire`/`_unwire` (the `Lit`-boundary
type-tagging helpers introduced by the ARC6/CEILING rungs) have now had
THREE separate coverage gaps found and patched in one session: a missing
`frozenset` case, a missing `Fraction` case
(`PROGRAM_SYNTHESIS_STRUCTURAL_CEILING_REASSESSMENT_2_RESULTS.md` or
sibling doc — verify exact filename during audit), and a missing
non-string-dict-key case
(`PROGRAM_SYNTHESIS_GROUPCOUNT_DICTMERGE_RESULTS.md`, landed `main`
c1d0b4c). Each fix was narrow and correct in isolation. The standing
instruction is to stop patching this reactively and instead find every
sibling copy of the same shape and the real systemic fix.

This is an audit-first investigation, per house discipline. No fix is
assumed correct until priced against two questions: (1) does a
type-complete canonical serializer already exist elsewhere in the
codebase that `_wire`/`_unwire` (and siblings) are re-deriving a lossy
subset of; (2) is a richer binary/native wire format, as the user
mused, real additional work or something that already exists.

## Audit plan

1. **Grep sweep** of `domains/*.py` for wire/unwire/plain/flatten-shaped
   helpers and any `json.dumps`/`json.loads` sitting at a PyO3 boundary
   crossing (attr storage, `native.evaluate()` inputs/outputs). Not
   scoped to `prog_synthesis.py` — the codebase's own "same pattern, own
   cache, no cross-import" convention (CLAUDE.md, confirmed load-bearing
   elsewhere this session) predicts independent sibling copies with
   independently-incomplete type coverage.
2. **Read `runners/dsl/src/value.rs`'s `Value` enum in full** — this is
   the ground truth for "every type that might need to survive a
   round-trip." Enumerate every variant.
3. **Cross-reference against `persist.rs::encode_value`/`decode_value`**
   (cited in the dict-key fix's own RESULTS doc as the engine's own
   already-tested `__dict__`-tag round trip) for completeness against
   the `Value` enum, and check whether it is a strict superset of what
   every hand-rolled Python flattener does.
4. **Check whether the PyO3 boundary itself (`py.rs::py_to_value` /
   `value_to_py`, used by `set_attr`/`node()`/`add_node`/`evaluate()`)
   is ALSO a type-complete, already-used-everywhere native converter** —
   if attrs already round-trip losslessly through `set_attr`/`node()`,
   the JSON-string flattening some Python call sites do may be
   unnecessary work reinventing what the attr storage layer already
   gives for free.
5. **Check whether `encode`/`decode` (or equivalent) are exposed as
   direct Python-callable primitives** wrapping the Rust-native codec —
   if so, prefer "use the existing primitive" over "harden the Python
   reimplementation," per CLAUDE.md's Rust-primitive-reuse rule.
6. **Price the user's own binary-format idea honestly**: is `persist.rs`
   (or `py_to_value`/`value_to_py`) already that richer format, or is
   building a new one real additional work? Skeptical audit, not
   assumed-correct.
7. **Size a concrete first slice** (file:line touched, call sites
   affected, test surface to re-run) and make a GO / NOT-YET-READY call.

## Predictions (falsifiable, checked against findings before writing RESULTS)

- P1: at least one other `domains/*.py` file has an independently
  hand-rolled flattener with DIFFERENT missing type coverage than
  `prog_synthesis.py`'s current (post-3-fixes) `_wire`/`_unwire`.
- P2: `persist.rs::encode_value`/`decode_value` already covers the full
  `Value` enum (all variants), making it a strict superset of what any
  hand-rolled Python `_wire`/`_unwire` does.
- P3: the richer-binary-format idea is EITHER already substantially
  built (as `persist.rs` or the PyO3 native converter) OR is real,
  separately-scoped work — not assumed correct either way before
  reading the code.

## Scope boundary

This audit does not touch `runners/dsl/src/synth_enumerate.rs` or mint
`SynthSpecShape`/`SynthOp` graph nodes — that is a concurrent sibling
rung's territory (Γ-admissibility first slice). Serialization/wire-layer
only: `domains/prog_synthesis.py` and siblings,
`runners/dsl/src/jsonio.rs`, `runners/dsl/src/persist.rs`,
`runners/dsl/src/value.rs`, `runners/dsl/src/py.rs`.

## House discipline

Isolated worktree (`/home/matt/ozmadev/ocelot-worktrees/wire-boundary-audit`,
branch `wire-boundary-systemic-audit`, detached from `main`@c1d0b4c,
re-checked fresh before worktree creation). No merge to `main`. Commit to
this branch only; orchestrator merges. `data/` symlinked and verified
(`data/wiktionary/en.jsonl.gz`, 492MB, resolves).
