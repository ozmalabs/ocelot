# PROGRAM SYNTHESIS ARC 4 S0 TRACK B — the backward-ordering probe (HA3) and search-reach sizing (HA4)

**Date:** 2026-08-01. Companion to `PROGRAM_SYNTHESIS_ARC4_PLAN.md` (S0),
`PROGRAM_SYNTHESIS_ARC4_PREREG.md` (§3-§4, the bars derived from this
document's numbers), `scripts/arc4_backward_probe.py` (the driver),
`results/arc4_backward_probe.json` (the artifact — every number below
re-derives from it), `tests/test_arc4_probe_migrated.py` (19 gates).
Runs alongside S0 track A (`scripts/arc4_failure_anatomy.py` /
`results/arc4_failure_anatomy.json`, HA1/HA2) on disjoint files; no
synthesis/engine/seed/spec code touched by either track.

---

## 1. Method, in one paragraph each

**HA3.** For every task with a KNOWN oracle solution — arc-3's 12
retrieval-oracle-ceiling held-out-honest ids (`results/
retrieval_oracle_ceiling.json`) plus the 6 FULL-R3 tasks the enumerator
itself accepted natively (`enumerate_outcome=='ok'`) — compute a def-use/
data-dependency depth for every parameter, backward from the return
value, over the solution's own emitted hub IR (mechanical: a generic
recursive walk, with named handling for `ProgIfStmt`/`ProgForEach`/
`ProgWhile` so a gating condition/iterable counts as a dependency of
whatever it encloses — a program-dependence reading, per Crichton/
Peitek's own framing, not a bare def-use one). Rank parameters by
ascending depth (ties → original declared position) = BACKWARD ordering;
declared order = CURRENT ordering (byte-identical to what
`domains.prog_synthesis.run_enumerate` feeds `SynthEnumerate` today).
Drive the REAL Rust `SynthEnumerate` Term twice per task — the only
difference between the two calls is which row-argument value gets which
letter name — and compare `tested` (steps-to-solution).

**HA4.** Over FULL-R3's 139-task `gapped:enumerate_failed` population,
ask whether the task's OWN reference solution (read fresh from the
corpus — the Q0 histogram's own established measurement precedent, never
learning) exhibits a construct naming one of five levers: mutating-method
write-back, comprehension forms, kwargs, map/lambda, regex (out of scope,
counted for the denominator). Every lever flag is a FRESH recompute
against the CURRENT `emit_prog_ir`/ast-walk, reusing (never
reimplementing) `mbpp_blocker_histogram.py`'s own helpers — necessary
because the cached histogram artifact is measurably stale on exactly one
of these axes (§4 below).

---

## 2. HA3 — the full 18-task probe table

| task | source | arity | reorders? | verdict | tested (cur / bwd) |
|---|---|---|---|---|---|
| 105 | retrieval | 1 | no | mutual budget exhaustion | 13595 / 13595 |
| 106 | retrieval (rung b) | 2 | **yes** | mutual budget exhaustion | 16239 / 16239 |
| 115 | retrieval | 1 | — | **SKIPPED** (set-valued row, see §5) | — |
| 138 | retrieval (rung c) | 1 | no | tie | 15913 / 15913 |
| 234 | native accept | 1 | no | tie | 2391 / 2391 |
| 238 | retrieval | 1 | no | tie | 37098 / 37098 |
| 242 | retrieval | 1 | no | tie | 114380 / 114380 |
| 266 | native accept | 1 | no | tie | 47246 / 47246 |
| 284 | retrieval | 2 | no | tie | 3 / 3 |
| 309 | native accept | 2 | no | tie | 268 / 268 |
| 394 | retrieval (rung c) | 1 | no | mutual budget exhaustion | 13595 / 13595 |
| 397 | native accept | 3 | no | tie | 434 / 434 |
| 404 | native accept | 2 | no | tie | 1 / 1 |
| 405 | retrieval | 2 | no | tie | 553 / 553 |
| 406 | retrieval (rung c) | 1 | no | tie | 16317 / 16317 |
| 412 | retrieval | 1 | no | mutual budget exhaustion | 13595 / 13595 |
| 414 | retrieval | 2 | no | tie | 3 / 3 |
| 464 | native accept | 2 | **yes** | tie | 63541 / 63541 |

**Arity-1 tasks (10/18) cannot reorder by construction** (one variable,
nothing to order). **Arity≥2 tasks (8/18: 106, 234's sibling set 309/397/
404/464/284/405/414/106) mostly tie too** — because these are FLAT,
single-`ProgReturn` solutions with no `ProgAssignVar`/`ProgAugAssign`
chain, every directly-referenced parameter gets the SAME backward depth
(0 hops), so the tie-break (original declared order) reproduces CURRENT
ordering exactly. **Only 2/17 usable tasks have a real dependency
structure to order at all**: 106 (an `ProgAugAssign` chain — the
retrieved exemplar does `test_list += test_tup; return test_list`, giving
`test_list` depth 0 and `test_tup` depth 1) and 464 (a dead first
parameter — `a` is never referenced, `b` is the sole live one). Neither
produces a backward win: 106 mutually exhausts the search budget under
BOTH orderings (the target needs list concatenation, outside
`SynthEnumerate`'s numeric/string op table regardless of naming);
464 ties exactly (a symmetric dead-variable relabelling — swapping which
of two structurally-interchangeable leaves is tried first does not change
how many candidates get registered before the unique winning shape is
reached).

## 3. HA3 — the off-corpus synthetic mechanism check

Because the natural population turned out to have almost no dependency
structure to order, two small hand-built hub-IR programs (the exact shape
a descent tree's intermediate holes already produce — never mixed into
the table above or its aggregate) were run to answer a narrower prior
question: **does the relabelling lever have any causal power over
`tested` at all, when a real chain exists?**

| id | structure | current tested | backward tested | verdict |
|---|---|---|---|---|
| `synthetic_chain2` | `x=a-b; return x-c` (1 hop; `c` depth 0, `a`/`b` depth 1) | 5403 | 5500 | **current wins** |
| `synthetic_chain3` | `x=a-b; y=x-c; return y-d` (2 hops; `d` depth 0 → `a`/`b` depth 2) | 200000 (budget) | 200000 (budget) | mutual budget exhaustion |

The lever is real (relabelling changes `tested` — 5403 vs 5500, a
~1.8% difference on a task explicitly constructed to have a genuine
dependency chain) but in this constructed case it makes backward ordering
**worse**, not better. `synthetic_chain3` shows the combinatorial cost of
adding a 4th variable: neither ordering reaches the (size-7, well within
`max_size=9`) target before the 200,000-candidate budget expires — the
default arithmetic op table's breadth (12 ops, all tried at every size)
dominates over naming choice once arity grows.

**Total across every case in this entire probe where reordering was even
possible (2 real + 2 synthetic = 4): 0 backward-wins, 2 ties/mutual-
exhaustions, 2 current-wins.**

## 4. HA4 — the search-reach sizing, full id lists

Denominator: **139/257 (54.1%)** — FULL-R3's own `gapped:
enumerate_failed` population (distinct from the plan's cited arc-2-FULL
55.3%, a different run's outcome population; both denominators are
stated so neither is later quoted bare).

| lever | inclusive ids (n) | exclusive ids (n) |
|---|---|---|
| **comprehension_forms** | 63, 97, 120, 251, 259, 261, 277, 391, 398, 399, 401, 409, 429, 445, 465, 470 (16) | same, all 16 exclusive |
| **mutating_method_writeback** | 57, 64, 74, 117, 123, 128, 140, 297, 307, 395, 408, 412, 417, 436 (14) | 74, 117, 123, 128, 140, 297, 307, 395, 408, 412, 417, 436 (12) |
| **kwargs** | 12, 57, 64, 104, 111, 130, 299, 308, 393, 457 (10) | 12, 104, 111, 130, 299, 308, 393, 457 (8) |
| **map_lambda** | 133, 249, 273, 282, 426, 447 (6) | same, all 6 exclusive |
| **regex** (out of scope, denominator only) | 305, 440, 451, 459, 478 (5) | same, all 5 exclusive |

Overlap is small and lives entirely between `mutating_method_writeback`
and `kwargs` (tasks 57, 64 need BOTH). **Ranked by exclusive mass:
comprehension_forms (16) > mutating_method_writeback (12) > kwargs (8) >
map_lambda (6) > regex (5, out of scope).** Sum of exclusive mass =
47/139 (33.8%) — the ceiling on what all five levers together could fix,
even perfectly implemented.

**The residual buckets (partition the 139, gated to sum exactly):**
- **covered by ≥1 of the 5 levers: 49/139 (35.3%)** (47 exclusive + 2
  in the mutating∩kwargs overlap).
- **`ok_already_no_named_lever`: 85/139 (61.2%)** — `emit_prog_ir`
  already returns `ok:true` for these; none of the five levers apply.
  Sampled prompts: task 11 (string splice), 18 (character removal), 19
  (duplicate detection), 59 (nth octagonal number), 65 (flatten-and-sum),
  66 (count positives), 69 (sublist containment), 70 (tuple-length
  equality). These are LIST/ITERATION-shaped tasks `SynthEnumerate`'s
  flat, non-iterative arithmetic search cannot reach at ANY op-inventory
  width — a genuine value-domain/search-reach ceiling, orthogonal to all
  five named levers. Full id list: 11, 18, 19, 59, 65, 66, 69, 70, 75,
  80, 82, 85, 87, 88, 90, 95, 98, 99, 102, 106, 116, 118, 132, 137, 139,
  141, 145, 161, 162, 163, 166, 170, 172, 226, 230, 232, 233, 246, 248,
  252, 253, 255, 257, 260, 262, 264, 265, 270, 272, 276, 278, 283, 290,
  293, 294, 301, 310, 312, 390, 400, 410, 411, 413, 418, 419, 421, 422,
  424, 435, 437, 438, 439, 442, 443, 446, 448, 450, 456, 460, 462, 472,
  473, 474, 475, 479.
- **`other_named_blocker_no_five_lever`: 5/139 (3.6%)** — a different
  structural blocker (bitwise ops, slicing, floordiv, etc), outside this
  plan's five: 71, 131, 160, 274, 428.
- **unresolved / residual-none: 0/139 each.**

`49 + 85 + 5 + 0 + 0 = 139` — the full population is accounted for with
no gap and no double-count (gated).

## 5. Honest residuals

1. **Task 115's set-valued row is a genuine JSON-Term-boundary gap,
   surfaced not patched.** `a=[{1,2}, {}, {}]` contains a Python `set`
   nested inside a list argument; this cannot cross the
   `{"type":"Lit","value":...}` boundary `SynthEnumerate`'s `examples`
   param uses — the SAME boundary production's own `run_enumerate` uses.
   Skipped honestly in this probe (never coerced); whether production
   hits the identical failure on this exact task is untested here
   (out of scope for a measurement phase) and is named for whoever next
   touches that seam.
2. **HA3's real population is nearly degenerate for this hypothesis, and
   that is itself the finding.** 15/17 usable tasks tie by construction
   because MBPP-native single-`ProgReturn` solutions have no assignment
   chain for backward-ordering to bite on. The two genuine-chain cases
   found (106, 464) both tie or mutually exhaust; the two off-corpus
   synthetic chain cases (built specifically to have real structure) show
   one loss and one mutual exhaustion. Zero wins anywhere in the whole
   probe. This does not disprove HA3 (n is far too small, and the flat
   `SynthEnumerate` call is not the grain the underlying literature
   describes — multi-hole descent is), but it is a real, non-cherry-
   picked null-leaning signal the prereg carries forward as a lowered-
   confidence, conservatively-set bar (§3 of the prereg).
3. **`results/mbpp_blocker_histogram.json` is stale on the
   `RecvMethod:*` axis** (measured 2026-07-31; `domains/prog_ir_emit.py`'s
   current `_RECV_BLOCKED_METHODS` table postdates it — task 307's
   `list.append` reads `ok:true, blockers:[]` in the cache but
   `ok:false, blockers:['RecvMethod:append']` live today). HA4's sizing
   therefore recomputes every lever fresh rather than trust the cache;
   any future phase reading that cached artifact directly for an engine
   decision should re-verify against the live emitter first.
4. **HA4's lever definitions are necessary-condition proxies, not
   sufficient-fix guarantees.** "Reachable via lever X" means "the task's
   own known-correct reference solution uses this construct" — a task
   needing the construct AND something else (list iteration, an
   out-of-plan blocker) is still counted toward the lever's mass, and the
   overlap table + `other_named_blocker`/`ok_already` buckets exist
   precisely so this is never hidden behind a single inflated count.
5. **Depth is computed from assignment/control-flow chains only, not
   within-expression tree position.** Two variables both referenced
   directly in a single return expression (no assignment between them)
   always tie at depth 0 under this walker, regardless of which operand
   of a binary op they occupy. An informal check during this probe's
   design (not gated, not part of any reported result) found that
   swapping which of two SUCH tied variables is tried first CAN move
   `tested` (e.g. a hand-built `b - a` spec: 191 vs 199 tested depending
   on which var is registered first) — a real, different, finer-grained
   lever ("which operand of a non-commutative op to search first") that
   HA3 as stated does not address and this probe does not claim to
   measure.

## 6. Determinism, runtime, gates

- **Twin-run byte-identical** for both HA3 (`ha3_backward_ordering_probe.
  determinism.identical: true`) and HA4 (`ha4_search_reach_sizing.
  determinism.identical: true`), plus the off-corpus synthetic check.
  Total elapsed **~1s** (well inside the 25-minute box).
- **`tests/test_arc4_probe_migrated.py`: 19 gates** — schema, aggregate
  re-derivation, 3 pinned rows re-verified LIVE (task 464's tie, task
  106's mutual exhaustion, `synthetic_chain2`'s current-win — none read
  from the frozen artifact only), the "zero backward-wins anywhere" gate,
  HA4's overlap-matrix symmetry + exclusive-subset + partition-with-no-
  gap-no-overlap gates, the `RecvMethod`/task-307 staleness finding
  reproduced live, in-process determinism recomputation, the set-valued-
  row skip, and the shared MBPP contamination gate run standalone.

## 7. Bars fixed for the prereg (§3-§4 of `PROGRAM_SYNTHESIS_ARC4_PREREG.md`)

- **HA3**: STRONG ≥6 net accepts CI-separated attributable only to
  reordering; WEAK 1-5; NULL ≤0 or CI-spans-zero — set conservatively
  given this probe's zero-wins result, with an additional registered
  condition that a near-zero touch-rate (paired with any accept delta)
  must be reported alongside the headline number, mirroring this probe's
  own 15/17 trivial-tie rate.
- **HA4**: STRONG ≥50% of a lever's own exclusive-mass ids convert,
  per-lever, CI-separated; WEAK 20-49%; NULL <20% or CI-spans-zero;
  registered ceiling of 47/139 (33.8%) for all five levers combined, with
  the 61.2% `ok_already` bucket explicitly named as OUT of S4's scope
  (a value-domain/search-reach gap, not an op-inventory gap).
