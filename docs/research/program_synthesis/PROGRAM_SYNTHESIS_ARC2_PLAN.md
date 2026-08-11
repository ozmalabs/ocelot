# PROGRAM SYNTHESIS ARC 2 — FEED THE PROPOSER, FACE THE BENCHMARK

**Date:** 2026-07-31
**Launches from:** arc 1 complete (P0 `2d9148c2` → P7-D `50a71b3e`, 11 commits,
`PROGRAM_SYNTHESIS_ARC_SUMMARY.md`).
**Status:** PLAN (no code in this commit).

## 0. The finding this arc answers

Arc 1's central measured fact: **"constructions propose, execution decides" is
carried entirely by the DECIDE half.** The verdict layer (ProgEval + held-out
rows + toolchain truth) never miscarried once across ~1,900 gated checks. The
learned proposal layer has **three powered nulls** against it (H6, H7c twice) —
each with a localized, measured cause:

1. **Domain mismatch** — the chunk codebook was mined from THIS repo's adapter
   code (guards, getattr-resolution); the battery asks for arithmetic. The
   idioms are real (they escape the P3 family collapse) but they're idioms for
   a domain nobody is asking about.
2. **Trigger poverty** — 2/15 chunks cueable. We mined *programs* without their
   *requests*: structure with no NL handle. An LLM's training pairs code WITH
   the words around it; ours didn't.
3. **Value-domain wall** — ProgEval/SynthEnumerate speak integers and integer
   lists. Everything else scores zero before proposal even starts.

The fix is not a fourth mechanism. It is **content in the asked-about domain,
paired with language, over a wide-enough value space** — and an external
benchmark to keep us honest about "asked-about." The user's standing question
("how would it fare on a programming benchmark?") becomes the arc's endgame
gate instead of an estimate.

**The arc's scientific claim to settle:** when proposal content is in-domain
and NL-paired, the learned layer's delta finally CI-separates from zero
(the decisive H6/H7c retest). If it STILL nulls with matched content, that is
a finding about the architecture, not the diet — and it gets reported as such.

## 1. Scope pin

- **Benchmark:** MBPP (sanitized split) — chosen over HumanEval because its
  3 assert statements ARE the example-row interface the loop already consumes,
  and it has a train/test separation we can use for content vs eval.
  Protocol mirror of arc 1's battery: per task, asserts split into revealed
  example rows vs held-out rows (exact split rule fixed in Q0's prereg);
  pass = accepted Program, ProgEval-correct on held-outs. pass@1, primary
  protocol, held-outs never revealed.
- **Value-domain target:** strings, bools, floats, None, dicts — chosen and
  bounded BY MEASUREMENT (Q0 histogram), not ambition. `set`/generators etc.
  only if the histogram forces them.
- **Out of scope (explicit):** editing existing code; HumanEval; multi-round
  oracle protocols beyond the labeled arc-1 secondary; the LLVM `call`
  frontier; new languages. Renders stay a read-off concern — MBPP is scored on
  the hub IR via ProgEval, with render/toolchain validity reported secondarily
  (the arc-1 pattern).

## 2. Phases

Ordering is the same discipline as arc 1: measure → widen the floor → feed →
retest at power. Q1 is the only Rust phase.

### Q0 — Prereg + the external baseline + the blocker histogram (measure first)
- Vendor the MBPP sanitized subset as fixtures with provenance/license record;
  hard **contamination guard**: test-split task text and programs may never
  enter any codebook, cue vocabulary, or bigram table (gated, list-based).
- Run the arc-1 stack AS-IS on the full test subset: the frozen **zero-shot
  external baseline** (expect: most tasks refused at the value-domain wall or
  the request-recognition step — enumerate the refusal taxonomy; this number
  is the arc's 7/26 analog).
- **Blocker histogram over MBPP**: which value types / ops / statement shapes /
  prompt forms block, ranked by task mass, greedy cumulative curve — THIS
  picks Q1's op set and Q2's comprehension scope, exactly as P0's histogram
  picked the IR variants (and note arc 1's lesson: the histogram
  over-predicted by ~25pp on sub-construct blockers — Q0 must model
  sub-construct features explicitly this time).
- `PROGRAM_SYNTHESIS_ARC2_PREREG.md`: HQ1 (value-domain coverage bar from the
  curve), HQ2 (request-recognition rate bar), HQ3 (train-content transfer:
  the learned-layer delta CI-separates on MBPP test — THE claim), HQ4 (no
  internal-battery regression, paired), null readings for each.

### Q1 — The value-domain floor (Rust; the arc's one engine phase)
- ProgEval + the DSL expression layer over the Q0-picked types: string
  ops (len/concat/slice/in/compare/case per the histogram), dict get/set/keys/
  in, float arithmetic with the divergence ledger extended (repr, NaN, int/
  float equality — pinned, fixture-avoided where ambiguous), None/bool
  semantics. `ProgContainerLit` kinds already carry list/tuple/set/dict — the
  work is evaluator + enumerator reach, not new IR.
- SynthEnumerate: typed leaves/ops over the new domains + the **`exclude`
  parameter** (arc-1's named repair lever — refuted sub-terms excluded at the
  engine, closing P7-B's within-round iteration gap properly).
- Gates: CPython agreement on a new fixture corpus per type; reflect
  round-trips; enumerate parity re-run (frozen arc-1 cases byte-stable);
  fuel/trap honesty on the new ops; the P2 Python reader re-measured (kwargs/
  slices were 1,700 functions of blocked mass — the histogram says how much
  Q1 recovers for free).

### Q2 — Spec comprehension for benchmark prose (adapter + rules, no NL magic)
- Mechanical extraction: MBPP asserts → ExampleRow nodes (pure parse); prompt
  sentence → request facts via the existing cue machinery, extended with
  cue vocabulary EARNED from the train split (Q3 feeds this too). Signature
  facts (arg count/types) derived from the asserts, not guessed from prose.
- The decision "this is a write request about X" stays in rules; anything the
  cue layer can't ground files the honest `not_recognized` — HQ2's bar is a
  recognition RATE with the failures enumerated, not a parser rewrite.

### Q3 — The paired diet (the actual LLM-analog training step)
- Read the MBPP **train** split — programs through the P2 Python reader into
  hub IR, prompts alongside — and grow, per arc-1 machinery, all three
  learned layers AT ONCE, now paired and in-domain:
  - **chunks** at the P7-C discovered grain, mined from train programs;
  - **triggers** earned from the paired prompts (chunk ↔ co-occurring request
    tokens — the cue-vocabulary route arc 1 never had data for);
  - **bigrams** at construction grain from train programs (replacing the
    adapter-corpus statistics that scored the wrong domain).
- Self-teach stays on: every accepted synthesis during the arc feeds the
  codebook (provenance-tracked, contamination-gated to train/internal only).
- Gates: mining determinism; trigger coverage measured (vs arc 1's 2/15);
  contamination list-gate green; the internal battery's frozen arms untouched.

### Q4 — Descent + repair widening (rules; close arc 1's named scope cuts)
- Scalar-loop descent (the `while`-accumulator class arc 1 guarded out);
  multi-item fold-row derivation using Q1's `exclude`-powered iteration;
  branch_arm hole derivation (rows partition by decided condition — now has
  benchmark mass, per Q0's histogram); hole-level CEGIS with the engine
  exclusion. Paired non-regression against every arc-1 suite.

### Q5 — The powered endgame (the benchmark number + the decisive retest)
- MBPP test subset at power (all in-scope tasks; Wilson CIs; twin-run
  determinism): arms = FULL (Q1-Q4 + train diet) / CONTENT-STRIPPED (same
  mechanisms, starter codebook, no train content — the HQ3 contrast) /
  ZERO-SHOT-FROZEN (the Q0 baseline, continuity control).
- Verdicts: the external number with CI (the user's question, answered with
  data); HQ3 delta with Newcombe CI — **the arc lives or dies on whether
  in-domain paired content finally separates the learned layer from zero**;
  refusal taxonomy vs Q0 (what did each phase actually buy, paired ids);
  internal-battery non-regression (frozen arms).
- `PROGRAM_SYNTHESIS_ARC2_SUMMARY.md` in the arc-1 pattern: every number,
  every null, honest.

## 3. What stays Python (unchanged boundary)

MBPP file/JSON handling, assert parsing, train-split mining drivers, toolchain
subprocess runs — mechanical adapter I/O. Every decision (recognition, plan,
descent, repair, accept, gap) remains rules + engine Terms, source-audited per
phase as in arc 1.

## 4. Risks (honest)

1. **HQ3 nulls again even in-domain.** Then the architecture's proposal grain
   is wrong, not its diet — the finding would point at retrieval-shaped
   proposal (decode against WHOLE held train programs, not chunk shapes) as
   arc 3. Named now so a third null is a fork, not a surprise.
2. **String semantics divergence surface is large.** The ledger discipline
   (pin, fixture-avoid, refuse-on-ambiguity) held twice; it must scale to a
   messier domain. Budget Q1 the way P1 was budgeted — it is the arc's
   biggest rung.
3. **MBPP prompt idiom** ("Write a python function to...") may make HQ2
   trivially high while constraint SEMANTICS ("balanced", "primes") stay
   unreachable — separate recognition rate from solve rate in every claim.
4. **Contamination** is the credibility risk: the guard is a list-gate from
   day one, and provenance attrs on every codebook entry make it auditable.
5. **Benchmark ceiling honesty:** even at full Q1-Q4 scope the reachable
   subset is bounded (no classes, no regex, no I/O). Q0's curve states the
   ceiling BEFORE the endgame; the reported number always carries its
   coverage denominator (standing rule: eval-subset coverage is part of every
   claim).

## 5. Launch shape

Same execution pattern as arc 1: Q0 two parallel agents (baseline runner +
histogram/prereg); Q1 one Rust agent (solo on the crate); Q2 ∥ Q3 (disjoint:
adapter/cues vs mining); Q4 solo on the synthesis seed; Q5 solo closer.
Per-phase commits on this worktree branch; frozen artifacts append-only.
