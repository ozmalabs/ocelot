# PROGRAM SYNTHESIS P5 — LLVM track: hub IR writes the llvm-ir and x86-64 frames

**Date:** 2026-07-31. Companion to `PROGRAM_SYNTHESIS_PLAN.md` §4-P5 (LLVM
bullet: "extend `emit_llvm_ir` coverage to the IR statement set (branches,
loops via CFG blocks); x86-64 = IR → existing cfg_to_asm chain. No direct
statement templates for asm") and `PROGRAM_SYNTHESIS_P2_LLVM.md` (whose §3/§8
frontier — "no phi ⇒ no counting loop" — this track closes from the emit side).

**Deliverables:** NEW `domains/prog_ir_to_llvm.py` (hub IR → .ll text, the
emit half of the P2 read frame); phi in the dialect —
`domains/llvm_ir_cfg.py` (parse + forward interpreter),
`domains/llvm_ir_interp.py` (explicit backward-walk refusal),
`domains/llvm_ir_cfg_to_asm.py` (phi lowering via edge copies);
`domains/prog_ir_llvm.py` lift extended to consume phis structurally
(public read API unchanged); `seeds/llvm_correspondence.json` v1.1.0 (phi
row note records the flip; no row semantics changed);
`tests/test_render_llvm_migrated.py` (29 gates, green).

The chain, end to end — **no direct statement templates for asm; the chain
IS the x86-64 frame**:

```
hub IR ──emit_prog_to_llvm──▶ .ll text
       ──parse_llvm_cfg────▶ substrate CFG graph
       ──interpret_cfg─────▶ oracle value          (agreement leg 2)
       ──emit_x86_64_cfg───▶ AT&T asm ──gcc──▶ .so (agreement leg 3)
       ──lift_llvm_cfg─────▶ hub IR again          (the round-trip law)
```

## 1. The loop mechanism decision: PHI (design (a)), not memory-form SSA

P2 measured the frontier: the dialect had no phi, so no loop-carried value —
every loop ran 0 iterations or forever. The two candidate closures:

- **(a) phi** — CHOSEN. (i) The resolution recipe was already documented on
  the P2 seed row ("phi = a ProgAssignVar of the incoming value on each
  incoming edge") — the read side was designed for it; P5 just applies it.
  (ii) Under `cfg_to_asm`'s never-reuse bump allocator, phi lowers to plain
  edge copies (classic phi elimination) with no liveness analysis — a
  pre-pass allocates each phi's register, each incoming edge `movl`s into
  it. (iii) Phi is the real LLVM instrument for loop-carried values; the
  emitted text is honest LLVM.
- **(b) alloca/load/store** — REJECTED. (i) It breaks the backward
  interpreter categorically: a `load` has no producer semantics (its value
  is time-dependent), so `llvm_ir_interp.interpret` — the trusted oracle
  under every existing suite — could not evaluate ANY value downstream of a
  load. (ii) `cfg_to_asm` explicitly "doesn't spill to stack"; memory form
  would force stack-slot allocation + prologue management into a module
  whose contract is register-only. (iii) The lift would need a mem2reg
  reconstruction to recover `ProgWhile` — strictly more machinery than
  consuming phis at the two structural positions the lift already owns.

## 2. Dialect deltas (phi) — every existing suite re-run green

| module | delta |
|---|---|
| `llvm_ir_cfg.parse_llvm_cfg` | `%v = phi i32 [ <val>, %<lbl> ], …` — 2–3 incomings (`uses_op0..2` is the production set), predecessor labels on the `incoming_labels` attr index-aligned with the operand edges; incoming `%values` may be forward references (loop latches), resolved after the parse like branch targets; **phi must lead its block** (ValueError otherwise) |
| `llvm_ir_cfg.interpret_cfg` | tracks the predecessor block; commits a block's phis ATOMICALLY at entry (all incomings read before any result written — parallel semantics); **recomputes each executed instruction per execution** (with phi, operands legitimately change across iterations; the old compute-once cache read stale values). Phi-free programs are byte-identical in behaviour — nothing can change across re-executions without phi. Phi commits count toward `max_steps`. |
| `llvm_ir_interp.interpret` | explicit refusal on a phi producer BEFORE walking operands (a loop phi's latch chain leads back to itself — unbounded recursion otherwise). The backward walk is path-independent by construction; phi is path-dependent. |
| `llvm_ir_cfg_to_asm.emit_x86_64_cfg` | pre-pass allocates every phi result's register (predecessors may emit first); the phi emits no code; each incoming edge materialises the value with `movl` before its jump. `br_cond` edges carrying copies are SPLIT into local stubs (`jne .<fn>_<bb>_t; <false movs>; jmp F; .<fn>_<bb>_t: <true movs>; jmp T`) so a copy never executes on the wrong path (`movl` preserves EFLAGS — the stub sits safely after `testl`). Same-block phi-reads-phi (the parallel-copy swap hazard) → `NotImplementedError`, refused not mis-lowered. |
| `llvm_ir_io` | **untouched** — the single-block dialect remains no-phi (gated: phi text in `parse_llvm_ir` is still an `unrecognised LLVM IR line` residual). |
| `prog_ir_llvm.lift_llvm_cfg` | phis consumed STRUCTURALLY at exactly two positions, per the P2 §3 recipe: **loop-header phi** → init assign before the loop (entry edge) + latch assign at the end of the body; **join phi** → an assign at the end of each arm (an empty arm materialises as `orelse` copies; a header-edge incoming carries the pre-branch value). NEW: when a loop header's computations feed only the branch condition, they INLINE into the while cond (re-evaluated per iteration by construction) instead of the pre-loop + body-end re-emission (which remains the fallback when header values are read elsewhere). Guards refined: `join_reads_branch_value` now fires on names defined in exactly ONE arm (phi copies are written in both — defined on every path, legal to read); `loop_exit_reads_body_value` excludes phi names (defined pre-loop by the inits). Phis anywhere else → `phi_outside_supported_pattern`; malformed/ambiguous incomings → `phi_incoming_mismatch:*`; same-block phi-reads-phi → `phi_parallel_copy_unsupported`. Public API unchanged (`lift_llvm_block`/`lift_llvm_cfg`/`load_correspondence`); all 19 P2 gates green unchanged — the P2 no-phi loop fixture keeps its zero-iteration + agreement-of-refusal semantics. |
| `seeds/llvm_correspondence.json` | v1.1.0 — the phi row's NOTE records the flip; `kind:"frontier"` retained deliberately: it governs the TABLE path, and a phi outside the two structured patterns is still an honest blocker. No expr row changed. |

## 3. The emitter (`domains/prog_ir_to_llvm.py`)

`emit_prog_to_llvm(prog, fn_name, params=None) → {ok, text, params, blockers}`.
A minimal SSA constructor over a var → operand environment; a pure copy
(`x = y`, `x = 3`) is a REBIND emitting no instruction (SSA has no copies).

In scope (the frame is integers + structured control flow): straight-line
`ProgSeq`/`ProgAssignVar`/`ProgAugAssign(add|sub|mult)`/`ProgReturn` over
Plus/Minus/Times, BitAnd/Or/Xor, Shl/Lshr/Ashr, IDiv/IRem, Eq/Lt/Lte/Gt/Gte,
IfThenElse (→ `select`; `IfThenElse(cmp,1,0)` → bare `icmp` — the in-frame
0/1 integer shape); `ProgIfStmt` → both-arms-return diamond, guard clause,
or join-with-phis (arm-assigned vars); `ProgWhile` → single-latch loop,
loop-carried = assigned-in-body ∧ bound-before; `ProgForEach` over
`range(n)` / `range(a,b)` → desugared counting loop (`stop` evaluated once,
pre-loop); `ProgDefFnParam` → i32 parameters. Literal-first comparisons are
COMMUTED (predicate flipped) so no immediate lands where the asm layer needs
a `cmpl` destination.

Honest refusals (each a named blocker, deterministic, gated): containers,
strings/floats, try/raise, comprehensions, `ProgLoopCtl`, nested control
inside loop bodies or if arms (the lift's structured subset is flat — emit
and lift refuse the SAME shapes), return-inside-loop, foreach over
non-range, missing return, unreachable code, unbound vars, `div`
aug-assign (DSL `Div` is float — out of the integer frame). **ProgCallExtern
does NOT grow a call row**: neither dialect parser speaks `call` (P2 §5
unchanged), so emitted call text would be unparseable by the frame's own
reader — `call_extern_unsupported:<name>` is the recorded frontier (the
`range` in ForEach position desugars away and never reaches it).

## 4. THE ROUND-TRIP LAW + the canonicalization ledger

Gated form (`test_round_trip_law`, all 7 fixtures):

1. **Semantic identity:** `ProgEval(P) == ProgEval(lift(parse(emit(P))))`
   on pinned inputs (both equal the pinned expected value). Exact, no
   canonicalization.
2. **The lift image is the canonical form, reached in ONE round:**
   `L = lift(parse(emit(P)))` satisfies `lift(parse(emit(L))) == L`
   byte-identical Term-JSON.
3. **Text canonicality:** `emit(L) == emit(P)` byte-identical .ll for
   while-loops, both-arms-return diamonds, join-with-else, select-form and
   straight-line fixtures; and `emit(L)` is itself a text fixpoint for ALL
   fixtures (the empty-arm join reaches it one round later — delta 7).

The enumerated P → L canonicalization deltas:

1. every instruction result is a named assignment — compound expressions
   flatten to `t<k>` temps; `Return(expr)` → temp + `Return(Var)`;
2. comparisons come back as in-frame integers `IfThenElse(cmp,1,0)`; branch
   conditions come back truthiness-wrapped (`Not(Eq(c,0))` / `Eq(c,0)` — the
   P2 br_cond templates);
3. phi resolution inserts init assigns before the loop and latch copies at
   body end; a body redefinition keeps its SSA-derived name
   (`acc` → `acc_2` + `acc = acc_2`);
4. loop-header computations inline into the while condition when read
   nowhere else (fallback: pre-loop emission + body-end re-emission);
5. literal-first comparisons commute (`Lte(0,n)` → `Gte(n,0)`);
6. `ProgDefFnParam` rows drop (parameters live in the `define` signature;
   re-emission passes them via `params=`);
7. an empty else arm at a join materialises as an `orelse` holding the phi
   copies (hence `emit(L) != emit(P)` for that one shape — the else block
   now exists — with the text fixpoint at `emit(L)`);
8. when the then arm returns, the post-if continuation is ABSORBED into the
   else arm (every function-terminating if lifts as both-arms-return);
9. `ProgForEach` comes back as its desugared `ProgWhile`;
10. `ProgAugAssign` comes back as `ProgAssignVar` of the binary op;
11. a select under an inverted condition comes back with arms swapped
    (`Not`/`Eq(·,0)` normalise away in both directions).

## 5. THE TRIPLE-AGREEMENT LAW (the x86-64 read-off)

`test_triple_agreement`: for every compiled fixture and pinned integer
input, `ProgEval(P) == interpret_cfg(parse(emit(P))) == the gcc-assembled
.so` — disagreement list EMPTY:

| fixture | shape | pinned inputs | agreed values |
|---|---|---|---|
| SUM | while, 2 phis | n ∈ {0, 5, 10, −3} | 0, 15, 55, 0 |
| MAX_RET | both-arms-return diamond | (3,9)(9,3)(4,4)(−7,−2) | 9, 9, 4, −2 |
| IFJOIN | join phi, both arms assign | x ∈ {11, 10, −4} | 22, 110, 96 |
| IFJOIN_NOELSE | empty-arm join phi (br_cond edge-split lowering) | x ∈ {5, 0, −6} | −5, 0, −6 |

Plus the frontier-closed gate: a phi counting loop PARSES, INTERPRETS to
values (`tri(n) = Σ0..n`, the P2-measured impossibility), COMPILES, and
LIFTS to a `ProgWhile` ProgEval agrees with.

## 6. The P4 artifact chain (gated end-to-end)

`test_p4_artifact_chain_max_of_two_and_synthesized_loop` — the REAL P4
pipeline (`prog_synthesis.ensure_program_synthesis` + `ingest_spec` +
`pump`), not a replay:

- **max_of_two** (the P4B headline artifact): accepted on rung 1 →
  `Program{name, program}` → emit (`icmp sgt` + `select`) → x86-64 →
  held-out inputs (`a=11,b=5`, `a=−3,b=4`, `a=6,b=6`) agree with ProgEval.
- **sum_to_n** (a synthesized LOOP program): taught as a statement-grain
  spine with SHUFFLED parts (`[Return, While, Assign]`, spine=1.0) — the
  corpus bigrams order it (`assign→while` 24, `while→return` 23; decoded
  `[Assign, While, Return]` ≠ template order), every example row passes
  ProgEval, accepted → emit (loop with 2 phis over `acc` and the
  count-down parameter) → x86-64 → held-out n ∈ {7, 12, 100} → 28, 78,
  5050, agreeing with ProgEval.
- Measured en route (a P4B-residual-2 corollary, recorded not patched): the
  ordering lattice connects DIFFERENT labels only ("each part once"), so a
  spine with two adjacent same-head parts (`[Assign, Assign, While,
  Return]`) cannot decode its true order — the corpus-best interleaving
  `[A, W, A, R]` failed its rows and CEGIS excluded it honestly (the
  verify loop working as designed). The taught spine therefore uses three
  DISTINCT statement heads (count-down loop over the parameter).

## 7. Gates

`pytest tests/test_render_llvm_migrated.py --confcutdir=. -q` → **29 passed,
~0.3 s** (compile-bearing gates skip honestly without gcc; the module skips
honestly on a ProgEval-less engine — the P1 §6 worktree seam).

Combined battery on this engine (`test_llvm_ir_cfg` + `test_cfg_codegen` +
`test_codegen_matches_interpreter` + `test_llvm_ir_io` +
`test_prog_read_llvm_migrated` (19/19, byte-unchanged expectations) +
`test_term_jit` + `test_llvm_ir_to_asm` + `test_llvm_pass_compiler` +
`test_llvm_teacher` + `test_llvm_vocab_baker` +
`test_program_synthesis_migrated` + `test_prog_ir_migrated` + this suite):
**325 passed**. Baselines: `test_code_synthesis_baseline_migrated` +
`test_failure_baseline_migrated` + `test_prog_constructions_migrated`:
**32 passed**.

## 8. Honest residuals (the standing frontier)

1. **`call` remains a frontier** — no parse row, no interp path, no asm
   call lowering; the emitter refuses `ProgCallExtern` (except the
   desugared `range`). Growing a call row is a parser+interp+asm+linker
   decision this rung did not need.
2. **Nested control flow refuses on BOTH sides** (emit
   `nested_control_unsupported`, lift `unstructured_cfg` /
   `phi_outside_supported_pattern`): the structured subset is flat
   sequences of {straight-line, guard, diamond, single-latch loop}. Loop
   bodies and if arms are straight-line. Nesting is the next rung, and it
   lands symmetric (emit + lift together) or not at all.
3. **Phi ≤ 3 incomings** (the `uses_op0..2` production set) and **no
   same-block phi-reads-phi** (parallel-copy swap): parser/lift/asm all
   refuse; structured emission never produces either.
4. **Integer width seam, fixture-avoided as before**: `interpret_cfg`
   wraps at i64, the compiled code is i32 (`test_cfg_codegen`'s own
   `_i32_wrap` precedent), ProgEval arithmetic is unwrapped. Fixtures stay
   well inside i32. Also inherited from P2 §6: sdiv/srem-by-zero
   divergence, and `select` in the interp evaluates both arms (eager)
   where ProgEval's `IfThenElse` is lazy — a trapping unreached arm
   (division by zero) would diverge; fixture-avoided, recorded.
5. **Register discipline unchanged from Phase 1**: bump allocation, no
   spill (`NotImplementedError` on exhaustion); `sdiv/srem/shift` clobber
   `%eax/%edx/%ecx`, which a long-lived phi could occupy — loop fixtures
   avoid div/shift in bodies; a clobber-aware allocator is real future
   work, not a P5 line item.
6. **`ProgForEach` post-loop counter is dropped** (desugar leaves it at
   `stop`; CPython/ProgEval leave the last item) — a post-loop read is an
   `unbound_var` refusal, not a silent divergence.
7. **The emitted-text identity `emit(L) == emit(P)` excludes the empty-arm
   join** (delta §4-7); its text fixpoint is `emit(L)`. Gated as such,
   not hidden.
8. **The P4 lattice cannot order adjacent same-head spine parts** (§6) —
   inherited P4B residual 2, now with a measured corollary; the fix
   (a used-part state dimension) belongs to the P4 seed, not this track.
