# PROGRAM SYNTHESIS ARC 3 — SUMMARY (R0 → R3): RETRIEVAL-SHAPED PROPOSAL

**Date:** 2026-08-01. Arc 3 asked one question, forked from arc 2's third
HQ3 null: does decoding against WHOLE HELD TRAIN PROGRAMS (retrieval),
rather than shape-grain chunks (arc 1) or a paired-prompt train diet
(arc 2), pay a measurable capability premium on MBPP? This document closes
the arc: R0 measured the ceiling before building anything; R1/R2 built the
mechanism; R2.5 landed the screen correctly after a first attempt was
measured and reverted; R3 is the powered endgame. Every number below cites
its own phase document; nothing here is re-derived from memory.

---

## 1. Commit ledger

| commit | phase | one line |
|---|---|---|
| `06a24dcade` | R0 | oracle ceiling measured: 12/257 (4.67%) held-out-honest, before any mechanism is built |
| `ed701de747` | R1+R2 | exemplar store (90 whole train programs) + ranked retrieval + the a-d adaptation ladder; 2/12 ceiling captured live; codebook-side screen built, measured, REVERTED (false-negatived legitimate partial covers) |
| `0a513033a5` | R2.5 | the screen redone SCOPED (SCREENABLE iff NOT descend-applicable, frozen at goal-mint against the FULL budget); decoy pool dies for free on its own dedicated fixture; 17/24 of Q5's decoy mass in scope by design, 7/24 named as the registered residual |
| *(this phase)* | R3 | the powered 257-task endgame: HR1 null, HR2 partially confirmed with a materially large named residual, HR3 confirmed, one regression named |

## 2. The arc trajectory

| moment | instrument | number |
|---|---|---|
| Q0-A zero-shot / STRESS | 240/257 | 0.42% [0.07%, 2.32%] |
| Arc 1 (chunk-shaped proposal) | — | HQ3-class nulls (H6, H7c) — shape-grain content did not pay |
| Arc 2 Q5 FULL (paired-prompt train diet, PRIMARY) | 257/257 | 7.00% [4.48%, 10.80%] |
| **Arc 3 R3 FULL-R3 (retrieval-shaped proposal, PRIMARY)** | 257/257 | **8.17%** [5.41%, 12.17%] |

The headline move across all three arcs (0.42% → 7.00% → 8.17%) is real in
the point estimate, but the DOMINANT mover was always the PRIMARY protocol
(arc 2's HQ2 richer reveal, not content) — every arc-1/arc-2/arc-3 content
architecture change on top of that floor has bought single digits of net
passes, each measured honestly, none of them CI-separated from zero at
n=257. This is the throughline the meta-finding (§6) states plainly.

## 3. What retrieval-shaped proposal measurably is

- **The ceiling is small and was measured BEFORE the mechanism was built**
  (R0): 12/257 (4.67%) held-out-honest — the maximum any as-is/permute/
  leaf-edit retrieval mechanism could reach against this exact 90-exemplar
  pool, even with a perfect ranker at zero search cost.
- **Trap mass is large at every grain it was measured** — R0's oracle sweep:
  55.6%-60.0% of revealed-row-passing candidates fail their held-out row.
  R3 reproduces this live, in the wild, at the real mechanism grain: of
  retrieval's engagement footprint (63/257 tasks reach a non-"none" rung),
  the concrete failure/regression evidence (task 17's preemption, §5's new
  traps at 105/143/164/165/300/452) is the SAME phenomenon, not a
  coincidence — the honest verdict discipline (holdout, never peeking) is
  the load-bearing defence throughout, not the ranker's precision.
- **Captured, honestly counted:** R1/R2's own end-to-end ceiling-capture
  table found 2/12 (138, 406). R3's full-corpus paired measurement against
  NO-RETRIEVAL finds 3 net-attributable retrieval GAINS (20, 142, 281) and
  1 retrieval-caused REGRESSION (17) — net_passes = 2, CI spans zero (HR1
  null, §5). The mechanism engages, finds real solutions on a real subset
  of the ceiling, and ALSO — a genuinely new finding this phase adds —
  can preempt an already-correct enumerator solution with a held-out trap,
  because retrieval runs FIRST in Occam order.
- **The mechanism finds independent solutions the oracle sweep never
  measured** (R1/R2's own honest finding, reproduced structurally in R3):
  both 138/406's original captures, and R3's 20/142/281, go through rung
  (d) or (c) via a DIFFERENT exemplar than R0's single-anchor oracle sweep
  used — retrieval's live SynthEnumerate-backed rung (d) is a genuinely
  more powerful search than the pure oracle's masked-prefix proxy, so the
  real mechanism's reach is not strictly bounded by the R0 ceiling's own
  12-task list, even though its AGGREGATE size (net 2-3 passes) stayed
  inside that ceiling's order of magnitude.

## 4. The screen's decoy-kill — the arc's durable, if narrower-than-hoped, win

The single cleanest, most legible result of the whole arc is task 464
(`ck_prog_if_stmt_n1_q0`, "check if all values are same in a dictionary"):
Q5 named it the CLEAN EXEMPLAR of the decoy tax (a wrong chunk cue consumes
the full 3-attempt budget; the enumerator, which would have solved it in
one attempt, never gets to run). R2.5's screen was purpose-built to kill
exactly this pattern; R3 confirms LIVE, at full-corpus scale, that it does:
464 now PASSES, screen `kills:4`, going straight to `enumerate` with its
whole budget. This is the arc's one unambiguous mechanism win — a Q5-named
defect, fixed, verified in the wild, not just on a dedicated fixture.

**But the reach is measurably narrower than the "~0" bar hoped for**
(HR2, §5): only 4/17 of the covered decoy class actually engage the
screen at all (`screen.kills > 0`); the other 10/17 have a frozen initial
trigger-matching pool SMALLER than the 3-attempt budget, so the screen's
own `NOT_SLACK` gate — an all-or-nothing design choice R2.5 named as its
own residual but had not yet measured at scale — never fires for them.
The durable win is real; its SCOPE, now measured, is about a quarter of
what the raw "chunk-cued" label suggested.

## 5. Every hypothesis verdict, stated plainly

| hypothesis | verdict | evidence |
|---|---|---|
| **HR1** (retrieval content pays, net paired passes vs NO-RETRIEVAL) | **NULL** (registered reading) | net_passes = 2 (3 gains, 1 regression); CI [-3.97pp, +5.55pp] spans zero. Below the 12-task ceiling's own honest bound, exactly as the prereg's §5 null-reading anticipated for a small-ceiling mechanism under an imperfect ranker. |
| **HR2** (decoy tax → ~0 within the covered scope) | **PARTIALLY CONFIRMED, materially narrower than registered** | The 7-row registered residual (starter-codebook-shape, out of scope by design) is 100% unchanged, exactly as registered. The 17-row covered class does NOT reach ~0: 10/17 (59%) remain unchanged because the screen's OWN `NOT_SLACK` scoping never engages for them — a real, now-quantified boundary, not a new defect. Attempts-per-accept also measurably INCREASED (0.931→1.000), missing that registered bar too, for a root-caused, non-alarming reason (more goals reach the 1-attempt accept floor via retrieval, pulling the population mean up). |
| **HR3** (non-regression) | **CONFIRMED** | 659 tests green across the required + neighbour sweep; both frozen continuity artifacts (arc-2 FULL, R0 ceiling) byte-untouched; one regression (task 17) found and named as a CONTENT finding, not a suite failure — no pinned test anywhere flipped unexpectedly. |

## 6. Consolidated residual ledger + named levers

1. **Corpus scale / exemplar density** (R0, quantified further in R3 §7's
   density extrapolation): the 90-exemplar pool has zero arity-4 supply
   against 2 arity-4 test tasks (permanently unreachable), and a 3.6x
   arity-3 demand/supply gap. R3's labelled linear extrapolation projects
   ~11.7% end-to-end at a 10x pool under the CURRENT measured 0.25 capture
   rate — a real, material, but not step-change lever. **The single
   highest-leverage next move this arc's own numbers point at.**
2. **No stemming/lemmatization in prompt-token scoring** (R1/R2, unfixed):
   a plural/singular mismatch (`"tuple"`/`"tuples"`) zeroes real token
   overlap between a genuinely related request and exemplar (task 405 vs
   exemplar 808) — cheap, not yet done.
3. **The spec-layer set-serialization defect** (task 115, pre-existing,
   `domains/mbpp_spec.py`'s own documented residual): a raw `set`-valued
   row is not JSON-serializable via `_add_example_row`, blocking
   end-to-end measurement of one ceiling task entirely, unrelated to
   retrieval, never patched (out of every phase's ownership so far).
4. **The 7-row screen residual** (starter-codebook-shape decoys,
   DESCEND_APPLICABLE by construction): explicitly out of the R2.5
   screen's scope by design, confirmed 100% unchanged this phase. Closing
   it needs a screen that can distinguish a wrong BRANCH/scalar-fold cue
   from a legitimate partial-cover one — a sharper discriminator than
   "not descend-applicable," named, not attempted.
5. **Combinatorial/coincidental matches invisible to content-based
   scoring** (R1/R2): several R0-ceiling tasks (105, 238, 405, 414) have
   an oracle exemplar match that shares zero prompt-content tokens with
   the request (e.g. "sum of an array" solving "count true booleans"
   because Python bools are ints) — no token-overlap ranker can ever
   surface these; a structural/type-signature-only ranking mode is the
   named, unattempted lever.
6. **NEW this phase — the `NOT_SLACK` all-or-nothing screen boundary has
   real, now-quantified weight** (§4): 10/17 of the covered decoy class,
   not a handful. The all-or-nothing per-goal freeze (chosen deliberately
   in R2.5 to avoid the per-round regression that broke `br_19`) trades
   away exactly the goals with a small (1-2 chunk) trigger-matching pool —
   a graduated or per-candidate screening design is the named next
   refinement, with R2.5's own regression (a real, measured one) as the
   reason it was not attempted this arc.
7. **NEW this phase — the preemption regression is a structural property
   of Occam-first retrieval ordering, not a one-off bug** (task 17, §5):
   ANY top-level goal where the enumerator alone would find a correct
   answer is now exposed to a possible retrieval trap claiming the goal
   first. The trap-mass finding (R0, 55.6%-60%) predicts this WILL recur
   as the exemplar pool grows, proportionally — a bidirectional screen
   (verify a retrieval accept doesn't discard a codebook/enumerate
   candidate that would ALSO have passed) is the named, unattempted
   mitigation.
8. **NEW this phase — attempts-per-accept increased, not decreased**
   (§5): a mechanical consequence of more goals reaching the 1-attempt
   retrieval-accept floor (population-mean effect), not any single accept
   costing more. Worth watching as the exemplar pool grows (more goals
   pulled toward the 1-attempt floor could keep pushing this bar the
   wrong way even as absolute capability rises) — named, not urgent.

## 7. The three-arc meta-finding: where does capability actually live?

Three arcs, three different proposal-architecture bets — arc 1's mined
IDIOM CHUNKS (shape grain), arc 2's paired-prompt TRAIN DIET (corpus
grain, same domain), arc 3's WHOLE-PROGRAM RETRIEVAL (program grain,
adaptive ladder) — have now each been measured against the SAME protocol,
the SAME 257-task split, with the SAME non-regression discipline. The
verdict, stated plainly with what the numbers actually say:

- **The verdict layer (holdout discipline, execution-as-ground-truth) has
  been solid and load-bearing throughout, unglamorously.** Every arc's
  headline finding — arc 1's H6/H7c nulls, arc 2's HQ3 decoy-tax
  attribution, arc 3's own trap-mass reproduction and the task-17
  regression — was FOUND by the holdout verifier, never smoothed over by
  it. The verdict layer is not where capability lives, but it is the
  reason every claim in this arc is trustworthy.
- **Protocol was, and remains, the single largest capability mover ever
  measured in this program.** The 0.42% → 7.00% jump (Q0-A STRESS →
  arc-2 PRIMARY) dwarfs every content-architecture delta measured since
  (all single digits of net passes, none CI-separated). This was true
  before arc 3 started and remains true after it ended.
- **Search (the bare enumerator) still carries nearly all measured
  capability.** `gapped:enumerate_failed` is the largest failure class in
  EVERY arm of EVERY arc measured so far (54.09% here, 55.3% in arc 2's
  Q5 FULL) — representability was rarely the obstacle; finding a program
  that fits the revealed rows is. Task 17 (§5) is the sharpest possible
  illustration: the bare enumerator alone, unaided, found a correct
  program that THREE ARCS of proposal-architecture experimentation then
  collectively failed to preserve.
- **Proposal content — across all three architectures now tried — is a
  measurably real but THIN, single-digit lever, never the dominant one.**
  Chunks nulled three times (arc 1 H6, H7c; arc 2 HQ3 third null). The
  train diet's OWN engagement was real (Q3's leave-N-out: content used in
  11/20) but net-zero-to-negative on the benchmark (HQ3: 0 exclusive
  gains, 1 pass lost). Retrieval is the first of the three to show a
  clean, attributable, CI-adjacent-if-not-separated positive number (net
  2, 3 gains) — genuinely the best-performing proposal architecture of
  the three, but still inside the noise floor at n=257, and it introduces
  its OWN new failure mode (the preemption regression) that the other two
  architectures did not have, because it runs FIRST.
- **The state of the art after three arcs, stated without hedging:**
  proposal-CONTENT architecture is not where the next big capability
  jump will come from at this corpus scale. The two levers with real,
  quantified headroom are (a) **corpus/exemplar-pool SCALE** (§6.1's
  extrapolation — a real, bounded, honestly-labelled projection to
  ~11.7% at 10x pool, still not a step-change) and (b) **the
  search/enumerate half itself** (54% of all outcomes are a search
  failure, not a representability or proposal failure — the enumerator's
  own reach, not what feeds it, is the largest remaining block of
  unclaimed capability). Retrieval-shaped proposal was a genuine,
  well-measured architecture change; it is not, on this evidence, the
  thing that was missing.

## 8. Files

- `scripts/mbpp_arc3_battery.py` — the R3 measurement driver.
- `results/mbpp_arc3_endgame.json` — the R3 artifact (three arms, HR1/HR2
  blocks, migration matrix vs arc-2 FULL, remaining-failure taxonomy,
  density extrapolation).
- `tests/test_mbpp_arc3_endgame_migrated.py` — 40 gates, ~3.3s.
- `PROGRAM_SYNTHESIS_ARC3_R3.md` — the powered tables and full verdict
  write-up this summary condenses.
- `PROGRAM_SYNTHESIS_ARC3_PREREG.md` — outcomes appended (append-only), R0
  through R3.
- Prior phase docs, unchanged, cited throughout: `PROGRAM_SYNTHESIS_ARC3_
  R0_NOTES.md`, `PROGRAM_SYNTHESIS_ARC3_R12_NOTES.md`,
  `PROGRAM_SYNTHESIS_ARC2_Q5.md`, `results/mbpp_endgame.json`,
  `results/retrieval_oracle_ceiling.json` (both frozen, hash-verified
  untouched by this phase).
