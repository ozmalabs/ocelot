# PROGRAM SYNTHESIS P6 — track B: the loop joins the standing self-improvement machinery (results)

**Date:** 2026-07-31. Companion to `PROGRAM_SYNTHESIS_PLAN.md` §4-P6 and
`PROGRAM_SYNTHESIS_PREREG.md` §8; consumes the carried residuals of
`PROGRAM_SYNTHESIS_P4B.md` §7.6 (write-request precision re-run) and
`PROGRAM_SYNTHESIS_P5_RUST_LUA.md` §6.1 (the `bool_text` read defect).
Deliverables: `tests/test_prog_synthesis_selfimprove_migrated.py` (5 gates),
`domains/code_curriculum.py` (additive `capability_report` extension),
`domains/ts_ingest.py` (the `bool_text` owner-fix) + 2 gates added to
`tests/test_prog_read_rust_lua_migrated.py`, this document. The powered
battery (N≥100, Wilson CIs, protected controls) is the concurrent P6-A
sibling — **no capability claim is made here**; this track wires and gates
the LOOP.

## 1. The loop as wired (the plan's RLHF analog), gate-verified end-to-end

```
NL request + example rows          "write a function weighted_pair that
  │                                 returns the weighted pair code of two
  │                                 numbers"  + 3 rows (a*10+b; outside the
  │                                 starter codebook AND outside
  │                                 SynthEnumerate's reach on these rows —
  │                                 probed deterministic: found=False,
  │                                 halt_reason='budget', tested=200000)
  ▼
P4 synthesis fixpoint      rung 1 no shape → rung 3 honest failure →
  │                        status=gapped (gap_reason=enumerate_failed)
  ▼
ps_gap_file (P4 wiring,    SelfConcern{kind:'code_write', source:'implicit',
re-gated here)             status:'noted', content:<the request verbatim>}
  │                        — the EXACT seeds/code_write_gap.json node shape
  ▼
HUMAN-GATED promote        jabberwock_daemon.promote_self_concern →
  │                        StandingConcern{status:'pending',
  │                        kind:'code_write', about:<request>}
  │                        ══ THE STANDING PIPELINE'S ENTRY ══
  │                        (scope honesty: demonstrated TO the hand-off;
  │                        running a dispatched child experiment is the
  │                        daemon _concern_tick's job, out of scope — the
  │                        gate asserts promotion mints NOTHING else)
  ▼
THE REPAIR ACTION          code_write_growth.teach_write_shape_from_example
  │                        (CODE-4, unchanged): read the pasted example →
  │                        validate-by-running → teach
  │                        taught_weighted{taught_for:<request>}
  ▼
the SAME request re-run    rung 1 proposes the taught shape → ProgEval
  │                        verifies all rows → ACCEPTED, exactly ONE
  │                        Program node; held-out (a=5,b=6) → 56
  ▼
the gap CLOSES BY RULE     resolve_code_write_gap (the agent's own rule)
                           reads the taught shape's taught_for provenance →
                           concern status='resolved' in the run_rules
                           fixpoint — no Python status write. The pending
                           StandingConcern STANDS (the human-gated record
                           of "worth improving" is not undone by closure).
```

Gate: `test_gap_promote_teach_accept_full_circle` — every leg asserted on
one substrate, in one test. This is the "failed tasks → gaps → (human-gated)
StandingConcern → repair" wiring the plan's P6 asked for, with teach-by-
example as the demonstrated repair action; the Experiment/adopt spine
(`seeds/self_optimisation.json` + `seeds/adoption_safety.json`) is
demonstrated exactly as far as its documented entry point (the pending
StandingConcern) and no further.

## 2. Capability self-report — the agent's own account now includes the loop

`capability_report` (additive; every pre-existing bucket and consumer
byte-compatible) gains:

- **`synthesized`** — every accepted `Program{provenance:'program_synthesis'}`
  node (the `ps_accept` mint), with `construction`, `attempts`, and the RUNG
  provenance (`codebook` / `lattice` / `enumerate`) read off the accepting
  Goal via the `accepted_program` edge. Pure read-back of rule-written facts.
- **`gap_counts`** — `{code_write, prog_read}` counts of held, un-retired,
  un-resolved SelfConcerns of those kinds (the `pending_code_write_gaps`
  reader shape, parameterised; `prog_read` is the P2.5
  `seeds/prog_read_gap.json` mint).

The NL surface, through the EXISTING `code_capabilities` dispatch
registration (nothing re-registered), live sample after the §1 circle plus
one open fourier gap:

> Beyond my starter code vocabulary, I have grown it: 1 taught by chat
> example (taught_weighted); 1 synthesized end-to-end from a request with
> examples (weighted_pair via taught_weighted). I still hold 1 open code
> capability gap(s) I have not closed: 'write a function fourier_transform
> that returns the spectrum of a signal'. Open gap counts: 1 code_write,
> 0 prog_read.

with `synthesized = [{"name": "weighted_pair", "construction":
"taught_weighted", "attempts": 1.0, "rungs": {"codebook": 1.0, "lattice":
null, "enumerate": null}}]`. Gates:
`test_capability_report_and_nl_surface_include_synthesis`,
`test_capability_report_prog_read_gap_counts`.

## 3. Write-request precision re-run (the P4-carried residual — CLOSED, no code change needed)

PREREG §6 carried: *"`looks_like_write_request` false-positive set from the
curriculum run (3 of 4 lesson 'exercise requests') re-run and CLOSED or
explicitly carried."* The P0-era run
(`results/code_curriculum/code_curriculum_report.json`, 2026-07-13) flagged
4 lesson sentences; 1 was genuine (the hypotenuse exercise), 3 were prose
false positives.

Re-run through the CURRENT machinery (held cue Concepts + the wave-2
imperative-lead gate — the same verdict `ps_goal` consumes via the recorded
`ps_write_request` fact):

| measurement | P0-era | now |
|---|---|---|
| the 4 recorded sentences, flagged | 4 (1 TP + 3 FP) | **1 (the genuine exercise only)** |
| precision on the flagged set | 0.25 | **1.00** |
| recall on the genuine exercise | 1/1 | **1/1** (preserved) |
| full 3-lesson sentence sweep (32 non-code sentences, region+sentence machinery) | not measured | **1 flagged, 0 false positives** |
| `synth_program` Goals minted from the 4 | (pre-P4) | **1** — the genuine request only |

**No data fix was applied and no Python heuristic was touched**: the
measurement shows the false-positive set was already closed by the
wave-2 imperative gating (`_has_imperative_write_lead` over held cue
Concepts) that landed with the whole-curriculum wave — what this track adds
is the RE-RUN ITSELF and its permanent gates
(`test_p0_flagged_set_reruns_at_precision_one`,
`test_full_lesson_sentence_sweep_flags_only_the_genuine_exercise`), so a
cue-set regression now fails a test instead of silently flooding the gap
pipeline. Per the CLAUDE.md boundary this classifier remains a sanctioned
thin I/O-boundary check whose word sets are held (teachable) Concepts — a
future precision break is a cue-seed data change, and the gates will name it.

## 4. The `bool_text` closure (P5-B §6.1, owner-fixed)

tree-sitter's rust `boolean_literal` carries its text on a token CHILD (the
node itself is not a leaf, so the ingest attaches no `text` attr);
`ts_ingest._leaf_value("bool_text")` read the PARENT's absent text, so every
re-read rust `true`/`false` came back `Lit false`. Fix (one line + comment,
`domains/ts_ingest.py`): the reader now takes `flat_text(nid)` — the node's
leaf text rebuilt in order — which is the identity on a genuine leaf, so a
leaf-borne bool is unchanged (lua's `true`/`false` rows use `const` readers
and never touched this path; the fixture corpus is byte-identical). Gates
added to the OWNING suite (`tests/test_prog_read_rust_lua_migrated.py`, now
64 passed):

- `test_rust_boolean_literal_reads_as_the_right_lit` — `fn always_yes() ->
  bool { true }` ProgEvals to true and `false` to false (the defect returned
  false for BOTH — the `true` direction discriminates);
- `test_rust_boolean_literal_in_condition_branches_correctly` — `if true {
  1 } else { 2 }` returns 1 (with the defect it took the else branch;
  toolchain truth: rustc returns 1 on this source).

P5-B's `loop`-as-`While(Lit true)` render decision (which dodged this
defect) is unchanged — it was the correct `rs_loop` inverse on its own
merits; the round-trip of a rendered standalone rust bool literal is now
also correct.

## 5. Suites (this track's surface, all green on the worktree engine)

| suite | result |
|---|---|
| `test_prog_synthesis_selfimprove_migrated.py` (NEW) | 5 passed, ~3s |
| `test_prog_read_rust_lua_migrated.py` (+2 bool gates) | 64 passed |
| `test_program_synthesis_migrated.py` (neighbor) | green |
| `test_code_curriculum_migrated.py` (capability_report consumer) | green |
| `test_code_growth_migrated.py` / gap suites (consumer) | green |

## 6. Honest residuals

1. **The Experiment/adopt spine is entered, not traversed.** The gate stops
   at `StandingConcern{pending}` — the documented entry the daemon's
   `_concern_tick` consumes. Running a dispatched child experiment over the
   synthesis rules themselves (and landing agent-authored construction
   seeds in `seeds/generated/`) is the plan's remaining P6 line, not
   claimed here.
2. **The demonstrated repair action is teach-by-example.** A capability gap
   whose close needs a NEW RULE (not a new write shape) still goes through
   the promote → experiment path this track only enters (residual 1).
3. **`resolve_code_write_gap` requires the seed.** The lean boots used here
   install it explicitly (`cwg.ensure_growth_rules`); a substrate booted
   without `seeds/code_write_gap.json` files gaps that never auto-resolve —
   same standing behaviour as before this track, now visible in the gate's
   fixture.
4. **Precision is measured on the published-lesson corpus** (4 recorded
   sentences + the 32-sentence fixture sweep) — eval-subset coverage per
   the standing rule; a broader prose corpus could surface new cue-set
   false positives, which would now fail a named gate instead of flooding
   the pipeline.
5. **`Div` float-semantics teach hazard (found en route, not this track's
   surface):** teaching `def halve_down(n): return n // 2` reads `//` as
   DSL `Div` (float division); validate-by-running can AGREE on an
   even-valued sample and teach a shape that then honestly fails odd-input
   example rows in the synthesis loop (counterexamples minted — the CEGIS
   layer catches it downstream, which is how it surfaced). The read-side
   floordiv fidelity belongs to the CODE-1/2 reader (`code_reading` /
   `ast_term_rules`), recorded here as the found gap with its reproduction.
6. **Program-node name collision across goals** is unhandled: two accepted
   goals with the same spec name mint two Program nodes; the report lists
   both (facts, not identity). Naming/versioning of synthesized Programs is
   future work alongside `seeds/generated/`.
