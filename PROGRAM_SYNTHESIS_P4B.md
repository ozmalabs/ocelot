# PROGRAM SYNTHESIS P4 — track B: the generation loop as seed rules (results)

**Date:** 2026-07-31. Companion to `PROGRAM_SYNTHESIS_PLAN.md` §2/§4-P4 and
`PROGRAM_SYNTHESIS_PREREG.md` §6 (H4). Deliverables:
`seeds/program_synthesis.json` (26 rules), `domains/prog_synthesis.py` (the
mechanical adapter rim), `tests/test_program_synthesis_migrated.py`
(14 gates, green, 0.2 s). Track A (the `SynthEnumerate` Rust Term) is a
concurrent sibling; its seam is structured below so wiring it is **zero rule
changes**.

## 1. The loop as landed

```
NL request + example rows
  │  ingest_spec (adapter, mechanical): Message{ps_write_request  ← the EXISTING
  │    cue machinery's verdict (code_writing.looks_like_write_request over the
  │    held code_write_request_cues Concepts), ps_spec_name, ps_tokens,
  │    ps_skeleton} + ExampleRow{inputs_json, expected} nodes
  ▼
ps_goal            Goal{kind:synth_program, status:pending, ps_budget:3 (int)}
  ▼
ps_propose         RUNG 1 (codebook): winner = Argmax over ELIGIBLE
  │                code_write_construction quanta (trigger token ∈ goal tokens,
  │                name ∉ Excluded) by SPECIFICITY (trigger-token count) —
  │                code_reading._winner's kind-filtered argmax, MIGRATED INTO
  │                THE RULE; ShapeDecode residual recorded as decode evidence;
  │                ps_attempts += 1
  ▼
ps_route_lattice / ps_route_bind        (spine attr on the winning quantum)
  │
  │  RUNG 1.5 (spine only): stamp_lattice (adapter, the
  │  ink_decode._lattice_partition precedent) stamps Hyp/LatEdge candidates on
  │  a throwaway substrate, edges scored by boarded ConstructionBigram
  │  trans_logp; the UNCHANGED seeds/viterbi_decode.json vit_step/vit_backtrace
  │  decode the order; ps_spine_ok is a recorded FACT; ps_latticed /
  │  ps_lattice_failed RULES decide
  ▼
splice_binding     (adapter, mechanical): template term → ProgSeq(params,
  │                Return(term)), or spine parts in the LATTICE-DECIDED order;
  │                ps_ir = hub-IR Term-JSON
  ▼
ps_built → eval_and_record (adapter): reflect the IR (add_term_subgraph),
  │                record the ROUND-TRIP fact ps_reflect_ok (structural
  │                verdict), then ProgEval OVER THE REFLECTED SUBGRAPH per
  │                ExampleRow → got / eval_ok / eval_attempt facts
  ▼
ps_row_pass / ps_row_fail / ps_verified      (RULES decide per row + overall)
  │
  ├─ verified → ps_accept: EXACTLY ONE Program{name, program} node
  │             (+ provenance: construction, attempts) + ir_subgraph edge to
  │             the reflected root — both representations, the scope pin's
  │             "do both"
  │
  ├─ fail → ps_counterexample: the failing row becomes a CounterExample NODE
  │         (inputs/expected/got/construction/attempt); ps_exclude_failed
  │         retires the plan (Excluded node — edge-to-NEW-node, because the
  │         engine cannot add_edge to a Term-found node); ps_reproposal
  │         re-arms while the INTEGER budget lasts; ps_ce_exhausted /
  │         ps_exhausted otherwise
  │
  ├─ codebook exhausted + examples exist → ps_enumerate_mark (RUNG 3):
  │         run_enumerate (adapter) feature-detects SynthEnumerate and records
  │         ps_enumerate_outcome; ps_enumerated / ps_enumerate_unavailable /
  │         ps_enumerate_failed read the fact
  │
  └─ ps_gap_status + ps_gap_file: SelfConcern{kind:'code_write',
            source:'implicit', status:'noted'} — the seeds/code_write_gap.json
            node shape VERBATIM (surfacing reader + human-gated promote spine
            find it with zero new plumbing), content-deduped
```

Every status transition is a rule (26 total). The Occam ladder is enforced by
guards: recognize/compose (rung 1) before lattice (1.5) before enumerate (3)
before gap — mirroring the sd rungs. The adapter (`domains/prog_synthesis.py`)
follows `_enact_advance`: evaluate bound Terms, apply results, never branch on
graph state; its `pump` is a name-keyed dispatch on rule verdicts (statuses).

## 2. Codebook reconciliation — which codebook proposes what

Two codebooks coexist, deliberately, at different grains:

| codebook | kind | grain | role in P4 |
|---|---|---|---|
| WRITE codebook (`seeds/code_write_constructions.json` + taught + this seed's `sum_of_list_spine`) | `code_write_construction` | NL-trigger → term/stmts TEMPLATE | **proposes CONTENT** (rung 1): the winning template supplies the IR material |
| P3 codebook (`prog_construction` quanta, 16, variant-grain) | `prog_construction` | statement-shape recognition | **scores the SEQUENCE** (rung 1.5): its statement-HEAD labels + the scan's bigram table order a multi-statement spine |

The P3 quanta carry no composable term content (they are recognition shapes —
P3 residual 1, "variant-grain, not idiom-grain"), so they cannot propose; the
write templates carry no corpus statistics, so they cannot sequence. The seam
between them is the statement-HEAD label (`pstmt` head, `signature[0][1]`),
which both sides speak: template parts are labeled by
`prog_ir_signature.statement_signature` (the P3 extraction walk, reused), and
the boarded bigrams are aggregated to the same head grain.

New in this seed: **one statement-grain write shape** (`sum_of_list_spine`,
trigger `TALLY`, `spine: 1.0`) whose template parts are DELIBERATELY SHUFFLED
(return first) — the spine order is the lattice's corpus-statistics decision,
proven by the gate (decoded `[ProgAssignVar, ProgForEach, ProgReturn]` ≠
template order, and the emitted IR follows the decode).

Proposal ranking within rung 1 is **specificity** (trigger-token count — the
most specific matching construction first), the Argmax now IN the rule where
`code_reading._winner` used to be Python. The adapter's `_normalise_triggers`
mechanically mirrors each write shape's JSON-string `signature` into a flat
`trigger_tokens` list attr so the rule's `Exists/In` guards can read it.

## 3. Bigram boarding (P3 residual 4 — consumed here)

`ensure_construction_bigrams` boards the 131 `ConstructionBigram` rows of
`results/prog_construction_scan.json` onto the AGENT substrate as
`ConstructionBigram{prev, next, count, prev_total, trans_logp, grain:'head'}`
nodes, aggregated from quantum-name grain to statement-HEAD grain (the
projection is mechanical: the artifact codebook's own `signature[0][1]`;
counts summed per head pair; add-1 smoothing recomputed with the SAME
registered formula `ln((c+1)/(prev_total+|V|))`, |V| = 14 at head grain).
Unseen pairs score `ln(1/(prev_total+|V|))` — exactly the consumer-side use
the P3 table's carried `prev_total` was registered for. Gated:
`test_boarded_bigrams_match_the_artifact_head_aggregation` re-derives the
aggregation from the artifact and requires byte-agreement.

Decision recorded (P3 residual 4 asked P4 to make it): the bigrams board **at
ensure time from the scan artifact**, not as a shipped seed — corpus
statistics keep tracking the corpus (re-scan → re-board), nothing frozen.

## 4. The SynthEnumerate seam (P4-A) — LANDED MID-FLIGHT, seam held

The seam was built while the Term was absent, and **P4-A's engine landed
during this track's run** — the designed property held, measured:

- Built against absence: `synth_enumerate_live` probes with a tiny evaluate
  (`UnknownTermType` → `unavailable`); the rung filed
  `enumerate_unavailable → gapped` honestly (measured before the swap).
- `ps_enumerate_mark` fires ONLY when no eligible codebook construction
  remains AND example rows exist (SynthEnumerate is spec-driven; an
  example-free request goes straight to `no_shape` → gap) AND attempts
  remain — Occam rung 3, guard-enforced.
- The adapter records `ps_enumerate_outcome` ∈ {`unavailable`, `ok`,
  `failed`}; **rules read only that fact**. When the rebuilt
  `_native.abi3.so` appeared mid-session, wiring the live Term was **zero
  rule changes** — only `run_enumerate`'s call updated to the landed
  contract (`SynthEnumerate{examples: [{inputs, output}...], ops?, consts?,
  max_size, max_candidates, saturate_k, field}` →
  `Dict{found, term (Term-JSON STRING), term_str, halt_reason, …}`,
  runners/dsl/src/synth_enumerate.rs).
- Live path, verified end-to-end: `"write a function double_it …"` (+2 rows,
  no covering shape) → rung-3 mark → SynthEnumerate finds `(a + a)` →
  spliced into hub IR (`ProgSeq[param, Return(term)]`) → the SAME ProgEval
  verify pipeline (reflect round-trip + all rows pass) → **accepted**,
  held-out `a=7 → 14`. The enumerated candidate is judged by execution
  exactly like a codebook proposal.

## 5. Gates (all green at this commit)

`tests/test_program_synthesis_migrated.py` — **14 passed, 0.19 s** (budget
120 s; `--confcutdir=.` worktree-engine discipline):

1. seed loads clean (26 rules, 0 skipped);
2. **END-TO-END HEADLINE**: `"write a function max_of_two …"` + 3 rows →
   exactly ONE accepted `Program{name, program}`; held-out inputs
   (`a=11,b=5 → 11`, `a=-3,b=4 → 4`) evaluated via the Program's
   `ir_subgraph` REFLECTED root; provenance rung-1-only; reflect round-trip
   fact 1.0; idle re-pump re-mints nothing;
3. spine: lattice rung recorded, decoded order = corpus order ≠ shuffled
   template order, emitted IR follows the decode, held-out `sum([2,4,6,8,10])
   = 30`; lattice mechanism inspected directly (10 Hyp / 15 LatEdge, 4
   on_path, boarded trans_logp values verbatim on the edges);
4. bigram boarding byte-agrees with the artifact aggregation; registered
   sanity orderings hold (`assign→foreach > assign→return`; `return→</s>`
   near-certain);
5. **CEGIS**: a 2-trigger WRONG decoy wins attempt 1 (specificity), fails one
   row → ONE CounterExample node (inputs/expected/got/construction/attempt) →
   Excluded → accepted on attempt 2 with `max_of_two`; ONE Program total;
6. Occam: covered requests carry NO rung-3 marker, no enumerate outcome;
7. honest gap: `fourier_transform` (no shape, no examples) → `gapped`,
   reason `no_shape`, SelfConcern in the standing code_write shape, deduped
   across an identical second request, zero Program nodes;
8. budget honesty: 4 wrong decoys, budget 3 → attempts exactly 3 (integer),
   one counterexample per attempt in specificity order, 4th decoy untried,
   `exhausted → gapped`, gap filed;
9. enumerate seam honest: the gate branches on the live probe — measured
   BOTH ways in one session (pre-swap: `unavailable → gapped`; post-swap:
   `ok → accepted`, held-out correct) + no-examples-no-enumerate;
10. NO-PYTHON-DECISION source audit of `domains/prog_synthesis.py` (ink-suite
    regex pattern: no argmin/argmax, no min/max(key=), no sort-on-score) +
    the prose false-positive check ("functions can make a program smaller"
    mints no goal — the wave-2 imperative-lead cue machinery's verdict, read
    not forked).

The whole battery (this suite + neighbors) was re-run AFTER P4-A's atomic
engine swap: **248 passed** on the new `_native.abi3.so` (SynthEnumerate
live). Neighbor suites: **234 passed** (`test_prog_ir` 54,
`test_prog_constructions` 10, `test_prog_read_python/rust_lua/llvm/gap`,
`test_code_growth`, `test_code_synthesis_baseline` 11 — C-BATTERY/C-BENCH
continuity). Full boot: `load_all_seeds` puts `program_synthesis` in the load
order with **zero skipped rules**, the `failed` list is byte-identical to the
pre-existing 8 `local_id` failures, and the end-to-end loop verified live on
the fully-booted agent (accepted, rung 1, <0.1 s).

## 6. Rung statistics from the gates

| gate request | rung 1 | rung 1.5 | rung 3 | attempts | terminal |
|---|---|---|---|---|---|
| max_of_two (headline) | ✓ | – | – | 1 | accepted |
| sum_of_list (spine) | ✓ | ✓ | – | 1 | accepted |
| max_of_two + decoy (CEGIS) | ✓✓ | – | – | 2 | accepted |
| fourier_transform (no shape/examples) | – | – | – | 0 | gapped (no_shape) |
| quux (4 decoys, budget 3) | ✓✓✓ | – | – | 3 | gapped (exhausted) |
| double_it (uncovered + examples), Term ABSENT | – | – | ✓ (unavailable) | 0 | gapped (enumerate_unavailable) |
| double_it (uncovered + examples), Term LIVE | – | – | ✓ (ok: `(a + a)`) | 0 | accepted (held-out a=7→14) |

## 7. Honest residuals

1. **ps_render is NOT in this phase — the P5 seam.** The accepted artifact is
   the graph-resident Program (Term-JSON + reflected subgraph); the verdict is
   EXECUTION (ProgEval on spec rows) + reflect round-trip, per the scope pin.
   Statement-grain source rendering is P5; the P1 expression-grain python
   renderer remains available for expression-grain templates via the existing
   `code_writing.write_function` path, unwired here on purpose (wiring it
   before statement-grain RenderRules exist would render spine programs
   wrongly or partially).
2. **The ordering lattice permits non-permutation paths** (label repeats at
   distance ≥ 2 — Viterbi is Markov; "each part once" is not expressible as a
   bigram constraint). The decoded sequence is recorded and `ps_spine_ok` is
   the mechanical permutation fact; `ps_lattice_failed` (a rule) retires the
   plan when it trips. Never observed on the gates (the corpus stats make the
   true order dominate); a future rung could add a used-part state dimension.
3. **Proposal ranking is trigger-specificity, not ShapeDecode's own
   shape_fit.** The rule records the ShapeDecode residual as decode evidence
   but the Argmax ranks by trigger-token count — an honest migration of
   `code_reading._winner`'s argmax at the grain the single-token write
   codebook actually distinguishes. Same-kind trigger collisions at EQUAL
   specificity fall to the engine's deterministic Argmax tie-break (the
   documented `retire_duplicate_gap` semantics) — the same exposure every
   Argmax-guarded seed rule has.
4. **Slot binding is template-verbatim** (`ps_bind` fills params from the
   template's own args; identifier synthesis via the P1 naming primitives is
   not yet exercised — no gate needed it). The Term-computed
   binding-candidate Argmax (task card's "e.g." for richer templates) becomes
   necessary only when templates grow open slots; the seam is
   `splice_binding`, one function.
5. **Enumerate-candidate row failure** (a term SynthEnumerate fitted under
   DSL semantics that ProgEval fails — possible only via a DSL-vs-ProgEval
   divergence) re-enters `pending` with no construction to exclude; the
   `ps_no_shape` Or-arm (`ps_rung_enumerate` marked) routes it to the gap
   instead of a terminal `pending`. Guard-closed, not exercised by a gate
   (constructing the divergence needs a semantics wedge this phase does not
   own).
6. **`looks_like_write_request` false-positive set**: track B re-verifies one
   representative prose false positive (the wave-2 measured flood case) and
   reads the cue verdict without forking it; the full curriculum-run
   false-positive set re-run is carried to the P4 phase close (both tracks),
   per prereg §6 — explicitly carried, not closed here.
7. **Budget/attempt values are stored as f64** by the substrate attr store
   (integral-valued; gated `.is_integer()`); in-frame integer discipline is
   observed at the value level, the storage type is the engine's.
8. **Adapter status-dispatch strings** (`_DISPATCH`) mirror the seed's status
   vocabulary; a renamed status is a two-file edit. Acceptable coupling — the
   statuses ARE the rule-verdict API the task card sanctions dispatching on.

## 8. Residual closure (P6-B, 2026-07-31)

**§7.6 (`looks_like_write_request` false-positive set) is CLOSED by
measurement — no code or cue-data change was needed.** The full P0-era
flagged set (the 4 recorded lesson sentences of
`results/code_curriculum/code_curriculum_report.json`: 1 genuine hypotenuse
exercise + 3 prose false positives) re-run through the current cue machinery
(held cue Concepts + the wave-2 imperative-lead gate — the same verdict
`ps_goal` reads via `ps_write_request`): only the genuine exercise flags
(precision 0.25 → 1.00 on the flagged set, recall preserved), and a full
32-sentence sweep of all three published-lesson fixtures flags exactly that
one sentence. Goal-mint wiring agrees: 1 `synth_program` Goal from the 4.
Permanently gated (a cue regression now fails a named test instead of
flooding the gap pipeline):
`tests/test_prog_synthesis_selfimprove_migrated.py::
test_p0_flagged_set_reruns_at_precision_one` and
`::test_full_lesson_sentence_sweep_flags_only_the_genuine_exercise`.
Numbers + protocol: `PROGRAM_SYNTHESIS_P6_SELFIMPROVE.md` §3.

## 9. Residual closure (P6.5, 2026-07-31) — the powered battery's stall, fixed in the rules

**The P6 battery surfaced a REAL defect this track owned** (not listed in §7
— the gates never constructed the shape): `stalled:evaluated`, 15/125.
When a codebook decoy consumed attempt N (CEGIS: row fail → CounterExample
→ Excluded → re-arm) and the enumerate rung then ran, `run_enumerate` built
the IR at the SAME attempt number N; the example rows already carried
`eval_attempt == verdict_attempt == N`, so `ps_row_pass`/`ps_row_fail`'s
`verdict_attempt < eval_attempt` guard never re-armed, `ps_verified` /
`ps_counterexample` both stayed unsatisfiable, and the goal parked on the
non-terminal `evaluated` — no accept, no gap, no SelfConcern. The P4 gates
missed it because their enumerate case (`double_it`) had no prior codebook
attempt (rows still at the −1 sentinels).

**Design decision (recorded per the task's choice point):** of the two
candidate designs — (a) give the enumerate rung's evaluation a fresh
attempt number vs (b) re-arm the verdict guard by resetting row facts on
the rung transition — (a) was chosen, keyed on the EXACT collision. (b) was
rejected because rewinding `verdict_attempt`/`ps_eval_done`/`ce_attempt`
re-uses one attempt number for two different IRs, muddies the
CounterExample provenance, and still leaves the enumerate-candidate-fails
case colliding with `ce_attempt`. The landed rule
(`ps_enumerate_fresh_attempt`, seed v1.1.0, rule 27):

- match `g -about_message-> m`; where `kind == synth_program`,
  `status == enumerate_pending`, and `Exists r ∈ Neighbours(m,
  has_example): r.eval_attempt == g.ps_attempts` — i.e. the current attempt
  number is CONSUMED;
- effect: `ps_attempts += 1` (integer). Nothing else.

Invariants preserved, all gated: the Occam ladder guards are untouched (the
rule fires between mark and build, only on the collision); the integer
budget semantics hold (`ps_enumerate_mark` requires `attempts < budget`, so
`attempts <= budget` after; `ps_reproposal`/`ps_ce_exhausted` unchanged);
every status transition is still a rule (this rule is attempt BOOKKEEPING
on an existing status — the adapter changed only its seed-version marker);
the CEGIS gates, the Occam-order gate and the no-Python-decision audit all
still pass. Non-colliding paths are byte-unchanged — a fresh enumerate
still runs at attempts 0 (§1's "attempt numbers start at 0 on the
enumerate rung" remains true there), which is why the battery's pinned
live-reverify rows reproduce without touching that gate.

Downstream of the fix the loop is closed on every branch: enumerate
candidate passes → `verified → accepted` at the fresh attempt; candidate
fails a row (the §7.5 divergence case) → CounterExample at the fresh
attempt → the standing `ps_no_shape` Or-arm or `ps_ce_exhausted` → `gapped`
+ SelfConcern. §7.5's guard-closure is thereby exercised-adjacent rather
than purely theoretical: the re-entry path now runs at a non-colliding
attempt number.

**Gates:** `test_stall_regression_decoy_then_enumerate_reaches_terminal`
(decoy → enumerate → terminal accepted on attempt 2; non-colliding control
at attempts 0; counterfactually verified — the v1.0.0 seed body fails it at
`status == 'evaluated'`); `test_seed_loads_clean` now pins 27 rules. Suite
15 passed; neighbors green (battery 11, selfimprove 5, baseline 11,
prog_ir 54 — 96 total).

**Re-measurement:** `PROGRAM_SYNTHESIS_P6_BATTERY.md` §7 — arm
MAIN-POSTFIX appended to the artifact (frozen rows untouched): stalled
15 → 0, overall 52.0% → 61.6% [.528, .697], the changed-row set exactly
the 15 stalled ids (12 → accepted_holdout_ok, 3 → accepted_holdout_fail
caught by held-out rows, 0 → gapped), twin-run byte-identical.
