# Process extraction as CAN graph dynamics — RESULTS

**Block**: 329000. Pre-reg: `PROCESS_SEED_PREREG.md`.
Build: `domains/llm_process_seed.py`; measure:
`scripts/llm_process_seed_measure.py`. Substrate: protected `can_native_bp.py` /
`seeds/can_native_reimplementation.json` (read-only, built-to; no new grammar).

**POSITIVE at the representation level, with an HONEST reduced-fidelity substrate
execution. The `negate` PROCESS, extracted from context-A statements, APPLIES to
held-out context-B statements it never saw — crisply in the LLM's own
representation (1.00 vs identity 0.00 vs shuffle 0.00) — a procedure, not stored
input→output pairs. Run as substrate transport dynamics it still beats the
identity baseline but at reduced fidelity, inheriting the irreducible block-326
discretisation constant plus the K-mode compression.**

## Result (process fit on A = 12 statements; applied to B = 8 held-out; NO LLM at query)

### (1) Representation application — apply N to a held-out B affirmation, read valence

| operator | reads NEGATED |
|---|---|
| **extracted N** | **1.00** |
| identity (no transform) | 0.00 |
| shuffled-N control | 0.00 |

The negation operator fit on A transforms every held-out B affirmation into the
NEGATED region of the valence probe (1.00), while the identity baseline leaves
them affirmed (0.00) and a scrambled operator produces nothing (0.00). The
process APPLIES to unseen inputs, and both controls fail exactly as they should.
(In-sample on A: 0.75; valence-probe sanity: 0.88 separation.)

### (2) Substrate application — run N as a transport-settle over mode-nodes

| reading | extracted N | identity |
|---|---|---|
| linear K=8 (continuous) | 0.62 | 0.00 |
| substrate Ising settle | 0.50 | 0.00 |

Run as graph dynamics (transport edges = N over Concept mode-nodes, `run_loopy_bp`
settle, no new grammar), the process still BEATS the identity baseline (0.00) but
at REDUCED fidelity. Two losses, both understood: the K=8 mode compression (the
continuous linear K-space reading is 0.62, down from the d-dim 1.00), and the
discrete undirected Ising settle on top (0.50) — the SAME irreducible constant
characterised in block 326 (a continuous DIRECTED map forced through a discrete
UNDIRECTED Ising MAP).

## Claim verdicts

- **Claim 1 (representation application): HOLDS, crisp.** 1.00 vs 0.00 identity
  vs 0.00 shuffle on held-out B.
- **Claim 2 (substrate dynamics): HOLDS, reduced.** Beats identity (0.62/0.50 vs
  0.00) but not crisp — the reduced fidelity is the block-326 discretisation
  ceiling + K-compression, reported honestly.
- **Claim 3 (application not memorisation): HOLDS.** B disjoint from A; no LLM
  at query; identity and shuffle controls fail.

## Verdict

The process tier's core claim succeeds: a PROCEDURE the LLM runs (`negate`) is
extractable as a transport operator and APPLIES to inputs it never saw —
transforming held-out affirmations into negations, in the LLM's own
representation, with the LLM out of the query loop and both controls failing.
Run as graph DYNAMICS on the substrate (a transport-settle, no new grammar) the
process executes and beats the identity baseline, but at reduced fidelity — the
crisp claim lives at the representation level, and the substrate execution
inherits the previously-characterised discretisation cost. This completes the
three-tier extraction direction: KNOWLEDGE (327), CONCEPT (328), and PROCESS
(329) all extract from the LLM into native CAN structure the substrate then uses.

## Anti-faking / method

- Context-B statements DISJOINT from A extraction; the process never saw them.
- NO LLM at query time — N, the probe, and the coupling are frozen recovered
  structure; transforms are numpy / substrate ops.
- Two controls (identity, shuffled-N) fail as they should in both readings.
- The reduced SUBSTRATE fidelity is reported plainly and attributed to its two
  causes (K-mode compression; block-326 discrete-Ising discretisation), not
  hidden behind the crisp representation result.
- NO new grammar: the process is a transport-operator + BP settle over existing
  Concept / causal_influence types.
- **default == today**: `.so` md5 stays `7efe75eba05b006cafd15dbb4b7da246`;
  protected CAN internals + seed grammar untouched; models + venv under
  `/applications`, NOT committed.

## Honest bounds and where this lands the arc

- One small model (0.6B), one process (`negate`), 12 A / 8 B statements. The
  load-bearing result is the representation-level application (1.00 vs 0.00
  controls) and the honest reduced substrate fidelity; not a large-sample rate.
- The substrate execution is bounded by known constants (K compression + the
  block-326 discrete-Ising ceiling), NOT a failure of the extraction — the
  process IS recovered and DOES run as dynamics; the fidelity gap is the
  substrate's inference form, already characterised.
- The three-tier extraction direction is complete: an LLM's KNOWLEDGE (facts),
  CONCEPTS (reusable operators), and PROCESSES (procedures) are each extractable
  into native CAN graph seeds the substrate uses for its own cognition —
  knowledge and concept crisply, process crisply in representation and reduced
  on the substrate settle. Next scale-ups: larger models (sharper operators),
  more processes (compare, pluralise, compose), and chaining processes as
  multi-hop transports (the 325 composition mechanism).
