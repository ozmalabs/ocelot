# PROGRAM SYNTHESIS P2 — LLVM track: LLVM IR as a read frame of the hub IR

**Date:** 2026-07-31. Companion to `PROGRAM_SYNTHESIS_PLAN.md` §4-P2 (LLVM
bullet: "lift `parse_llvm_ir`'s output into hub IR — it is already
graph-shaped; this is a correspondence-rule seed, not new parsing"),
`PROGRAM_SYNTHESIS_P1_NOTES.md` (variant set, ProgEval trap/fuel model,
divergence ledger).

**Deliverables:** `domains/prog_ir_llvm.py` (table-driven walker),
`seeds/llvm_correspondence.json` (23 `LLVMOpcodeMap` rows),
`tests/test_prog_read_llvm_migrated.py` (19 gates, green),
`tests/fixtures/prog_ir_read_llvm/*.ll` (12 fixtures).

## 1. What lifts

Scope is EXACTLY what the existing modules produce and the existing trusted
oracle can execute — `domains/llvm_ir_io.py::parse_llvm_ir` (single-block
integer subset), `domains/llvm_ir_cfg.py::parse_llvm_cfg` (+`br`/`br_cond`/
`LLVMBasicBlock`), `domains/llvm_ir_interp.py::interpret` /
`llvm_ir_cfg.interpret_cfg` (the agreement oracle, already trusted by
`test_codegen_matches_interpreter`). No parser was touched; no coverage was
invented beyond the dialect.

- **Single block** → `ProgSeq` of `ProgAssignVar` (SSA name := DSL arithmetic
  Term over prior names), `ret` → `ProgReturn`. Instruction order is the
  deterministic dependency order from the returned value (the `emit_llvm_ir`
  order); dead instructions are not lifted — matching the oracle, which never
  computes them either.
- **CFG, structured only** — the two reducible patterns the modules produce:
  - **if-then-else diamonds** → `ProgIfStmt`: both-arms-return (the corpus
    form — without phi, values cannot flow back across a merge), arms
    rejoining at a common block (arm-defined values must be dead past the
    join — see §4), the empty-arm if-then, and the guard-clause (one arm
    returns, the other continues).
  - **natural single-latch loops** → `ProgWhile`: a header `br_cond` with one
    arm a straight-line chain latching back to the header. Header
    computations are re-emitted at the end of the body so the condition is
    honestly re-evaluated each iteration (negated `Eq(c,0)` form when the
    true arm is the exit).
- **`call`** → `ProgCallExtern{name: callee}` — graph-level row only (§5).
- **Anything else** → honest residual `{ok: False, blockers: [...]}`. No goto
  emulation, no node splitting at P2.

## 2. The correspondence seed (`seeds/llvm_correspondence.json`)

Rows are `LLVMOpcodeMap` nodes (`kind ∈ {expr, call, terminator, frontier}`);
each `expr` row's `template` attr is Term-JSON with `{"__operand__": N}`
placeholders. The walker is pure table dispatch plus the two structural
pattern matches — no per-opcode `if/elif`. The seed loads clean via
`load_seed_manifest`, and `load_correspondence` reads the graph-held table
identically to the file (gated).

| opcode | hub Term | note |
|---|---|---|
| add / sub / mul | `Plus` / `Minus` / `Times` | i64-wrap divergence at overflow, fixture-avoided (§6) |
| and / or / xor | `BitAnd` / `BitOr` / `BitXor` | exact |
| shl / lshr / ashr | `Shl` / `Lshr` / `Ashr` | out-of-range count → 0 in BOTH engines (shared substrate convention) |
| sdiv / srem | `IDiv` / `IRem` | exact on nonzero divisors; zero divisor is the documented divergence (§6) |
| icmp eq/ne/slt/sle/sgt/sge | `IfThenElse(Eq/Lt/Lte/Gt/Gte…, 1, 0)` | result stays an IN-FRAME INTEGER 0/1 (i1 can feed arithmetic; the frame invariant says in-frame is integer, so no Bools leak into the frame) |
| icmp ult/ule/ugt/uge | — | NO row: the oracle refuses them too → `unsupported_opcode:<op>`, matched frontiers (gated) |
| select | `IfThenElse(Eq(c,0), b, a)` | the oracle's truthiness (any nonzero = true), no ProgEval-truthiness assumption |
| ret / br / br_cond | structural | `br_cond` rows carry the explicit-Bool cond templates (`Not(Eq(c,0))` / `Eq(c,0)`) |
| call | `ProgCallExtern` | graph-level frontier row (§5) |
| phi | frontier | documented treatment, honest blocker (§3) |

## 3. Phi treatment — the documented frontier

**The existing dialect has NO phi** (`llvm_ir_io.py` header: "no phi nodes";
neither parser mints one). Documented resolution, carried on the seed's `phi`
row for when P5 extends the dialect: **phi = a `ProgAssignVar` of the
incoming value on each incoming edge** — an init assignment before the
loop/diamond (entry edge) and a latch-edge assignment at the end of the loop
body / arm. Until then, encountering a phi opcode is an honest
`unsupported_opcode:phi` blocker, not a lift.

**Consequence (measured, not assumed): a counting loop is inexpressible in
this dialect.** Without phi there is no loop-carried value, so every loop
runs 0 iterations or forever (the oracle's own cache semantics agree: SSA
values are computed once). The loop fixture therefore gates the two honest
behaviours: exact agreement on zero-iteration inputs, and
**agreement-of-refusal** on looping inputs — `interpret_cfg` raises
`RuntimeError` at `max_steps` ⟷ `ProgEval` exhausts fuel (`halted: False`,
`trap: "fuel"`, `steps == fuel`, never a value).

## 4. The unstructured-CFG frontier + dominance honesty guards

`{ok: False, blockers: ["unstructured_cfg"]}` for anything outside the two
patterns: irreducible cycles (gated on a two-entry h/m cycle), nested
`br_cond` arms, re-entry into an already-lifted block (the no-node-splitting
rule), both-arms-latch loops without an exit.

Three additional guards refuse shapes where the lift would be *silently
wrong* rather than unstructured. The oracle (`interpret`) evaluates values
BACKWARD through producers regardless of the executed path, so it computes
dominance-violating reads anyway; the lifted program would honestly trap
`name:<n>` on the unexecuted path — a divergence. The lift refuses instead:

- `join_reads_branch_value` — code at/after a join reads a value defined in
  only one arm (gated: `join_reads_branch.ll`);
- `cross_arm_value_read` — one arm reads the sibling arm's value;
- `loop_exit_reads_body_value` — post-loop code reads a body-defined value
  (would trap on the 0-iteration path).

All are mechanical Var-read/-write scans over the lifted Term-JSON.

## 5. Calls

Neither existing parser speaks `call`, and scope is exactly what the io/cfg
modules produce — so `call.ll` gates the **parse-layer** honest residual
(`ValueError: unrecognised LLVM IR line`). The correspondence row is gated
**graph-level** (a mechanically node/edge-built call instruction, the only
way such a node can exist today): it lifts to `ProgCallExtern{name: callee,
args: uses_op*}`, evaluates against a declared oracle (`abs` → 5), and traps
`extern:abs` (halted False, no value) undeclared — plan §3.2's "no shelling
out mid-eval". The oracle cannot execute calls either, so there is no
interp-agreement row for call: matched frontiers, recorded here.

## 6. Integer semantics — the divergence ledger (per P1 notes §3)

Choice taken: **exact-agreement mappings with fixture-avoided, documented
edge divergences** (not semantic forks):

- **sdiv/srem → IDiv/IRem: EXACT on nonzero divisors** — both truncate
  toward zero with sign-of-dividend remainder (verified: `IDiv(-7,2) = -3`,
  `IRem(-7,2) = -1`; mixed-sign agreement gated). **Zero divisor diverges by
  design:** the oracle raises `ZeroDivisionError` (LLVM UB surfaced); the
  DSL's convention is silent 0. Fixtures avoid zero divisors; the choice is
  recorded on the seed rows.
- **shifts: EXACT including the poison edge** — out-of-range counts return
  0 (ashr: 0/−1 by sign) in both engines; same substrate convention on both
  sides. One true edge divergence: `lshr` by 0 of a negative value (the
  oracle re-wraps to i64, DSL `Lshr` doesn't) — fixture-avoided, noted in
  `bitops.ll`.
- **add/sub/mul: the oracle wraps at i64; DSL arithmetic is unwrapped.**
  Fixtures stay well inside i64.
- **icmp/select produce ints 0/1**, never Bools (gated:
  `test_icmp_result_is_in_frame_integer`) — result equality with the
  oracle's 1/0 is exact, and i1-feeds-arithmetic keeps working.

## 7. Agreement results + gates (all green)

`pytest tests/test_prog_read_llvm_migrated.py --confcutdir=. -q` →
**19 passed in ~0.2s** (the `--confcutdir` seam per P1 notes §6; module
skips honestly if the installed engine lacks ProgEval). Combined run with
the P1 suite + the existing `test_llvm_ir_cfg.py`: **86 passed** — the
neighbours are byte-untouched (no existing file was modified).

- **THE AGREEMENT LAW: disagreement list EMPTY.** Every in-scope fixture ×
  every input case: `ProgEval(lift)` ≡ `interpret`/`interpret_cfg` —
  straight-line arithmetic (4 cases), bitops (4), div/rem mixed signs (5),
  icmp+select clamp (5), bare-icmp ret (3), diamond-ret (5 cases, both
  arms), diamond-join (4), zero-iteration loop (3). **The law bites:** a
  mutation probe (swapped `sub` operands in the table) flips the verdict
  (oracle 12 vs corrupted −22).
- Structural: diamond → `ProgIfStmt`, loop → `ProgWhile` asserted in the
  lifted JSON; join arms execute path-dependently (verified: `da` only on
  the true path, `db` only on the false path).
- Refusals gated: unstructured, join-reads-branch, icmp_ult (matched to the
  oracle's own `ValueError`), call-at-parse, fuel/max_steps double refusal.
- Reflect round-trip on a lifted program (canonical identity + idempotence);
  determinism (two fresh parse+lift runs → byte-identical JSON, 3 fixtures);
  seed loads clean and graph-table ≡ file-table.

## 8. Honest residuals (the standing frontier)

1. **No phi ⇒ no counting loop** — the P5 emit/parse extension is where phi
   lands; the resolution recipe is already on the seed row (§3).
2. **`call` is graph-level only** — no parse path, no oracle path today.
3. **Unsigned icmp predicates unlifted** — matched to the oracle's refusal;
   a future row needs an unsigned-reinterpret Term decision first.
4. **Nested diamonds refuse as `unstructured_cfg`** — legitimately reducible
   shapes beyond the corpus's flat patterns; P2 keeps the structurer at
   exactly what the modules produce.
5. **Edge divergences fixture-avoided, not closed** (§6): sdiv/srem-by-zero,
   i64 overflow wrap, lshr-0-of-negative.
6. The lift consumes `parse_llvm_ir`'s returned `ssa` map (adapter-level
   plumbing, same as every existing caller) — the single-block graph alone
   does not carry SSA names or instruction order; the CFG form carries order
   on the BB nodes.

## 9. Frontier update (P5, 2026-07-31) — appended, not rewritten

Residual 1 is CLOSED and residual 4's inline-cond half moved: **the P5 LLVM
track landed phi in the CFG dialect** (`PROGRAM_SYNTHESIS_P5_LLVM.md`), and
the §3 resolution recipe this doc carried on the seed row is now APPLIED by
`lift_llvm_cfg` — loop-header phi → init assign before the loop + latch
assign at the end of the body; join phi → an assign at the end of each arm
(empty arm → `orelse` copies). Counting loops now parse, interpret to
values, compile via `emit_x86_64_cfg`, and lift to `ProgWhile` with
loop-carried variables; hub IR writes the frame via the NEW
`domains/prog_ir_to_llvm.py` and the emit→parse→lift round trip is gated as
a one-round fixpoint. A phi OUTSIDE the two structured patterns is still an
honest blocker (`phi_outside_supported_pattern` at the structurer;
`unsupported_opcode:phi` on the table path — the seed row, v1.1.0, stays
`kind:frontier` for exactly that reason). The single-block dialect
(`parse_llvm_ir`) remains no-phi, gated. This suite's 19 gates are
byte-unchanged and green on the extended lift: the no-phi loop fixture
keeps its zero-iteration agreement AND its agreement-of-refusal on looping
inputs (without phi there is still no loop-carried value — that measurement
stands; what changed is that the dialect can now EXPRESS the carried value).
Still open here: `call` (residual 2 — the P5 emitter refuses
`ProgCallExtern` for the same reason this doc records: the frame's own
parsers don't speak it), unsigned icmp (residual 3), nested diamonds
(residual 4 — refused symmetrically by the P5 emitter), and the §6 edge
divergences (residual 5, plus the select-eagerness note recorded in P5 §8.4).
