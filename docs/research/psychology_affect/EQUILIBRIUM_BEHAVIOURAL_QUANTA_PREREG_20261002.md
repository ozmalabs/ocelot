# EQUILIBRIUM BEHAVIOURAL QUANTA — PREREG (stream T3b)

**Date:** 2026-10-02. **Status: DRAFT, not yet frozen.** It becomes binding when it is committed **before** any WI-5..WI-8 rule is run against the sealed synthetic sets (§4). Worktree `/home/matt/ozmadev/ocelot/.worktrees/t3b`, branch `t3b/behavioural-quanta` (based on `t3/classifier-sidecar` @ `2aefc943`). Design: [`EQUILIBRIUM_BEHAVIOURAL_QUANTA_DESIGN_20261002.md`](EQUILIBRIUM_BEHAVIOURAL_QUANTA_DESIGN_20261002.md). Predecessor PREREG: [`EQUILIBRIUM_SEED_PACK_V0_PREREG_20261002.md`](EQUILIBRIUM_SEED_PACK_V0_PREREG_20261002.md). Not merged and not pushed.

## 1. Question

Can person-level labels be replaced by open, window-scoped, combinatory **behavioural quanta**, with competence as claimed / demonstrated / acknowledged / corroborated relations and dispute episodes with etiology facets? Can this be computed entirely inside the Ocelot `run_rules` fixpoint on a fork, with:

- a thin adapter (ingest/emit only);
- cue recognition on lemma/class, negation/modality scope and reply-pair coherence rather than flat n-grams;
- no invented thresholds;
- no LLM;
- the frozen base unchanged;
- latency acceptable to Equilibrium?

## 2. Data discipline

- **Synthetic only.** Windows are hand-written with pseudonyms (`actor_a`, `actor_b`, `expert_e`, `member_###`). No corpus, `.env` or `~/.equilibrium` is read, and nothing derived from real people is used. `OZMA_NO_LLM=1` is set for every run.
- Measurement output is counts, ids, timings and digests only. No turn text appears in logs or results.

## 3. Predictions (confirmatory)

Each prediction states its pass criterion. "Golden" means an exact expected `quanta`/`episodes` JSON, written in advance, compared after deterministic sorting (DESIGN §7.3).

**P1 — Golden behaviour (synthetic, G1–G16).** All 16 goldens pass exactly. Predicted outcome: ≥14/16 pass at first full run. Any failure is reported, not edited away (§5).

| G | Window sketch (synthetic) | Expected (abridged) |
|---|---|---|
| G1 | `expert_e` states a credential twice; no code/citations; no one acknowledges | `competence.claimed:+ exact`. `competence.demonstrated` absent. `competence.claim_grounding:- weak`. |
| G2 | `expert_e` claims once, posts a code block, and `actor_b` replies conceding to `expert_e` | `competence.claimed:+ weak`, `competence.demonstrated:+ weak` (sub `.code`), `competence.acknowledged:+` (target `actor_b`), `competence.corroborated:+` with evidence {claim, concession}, `competence.claim_grounding:+` |
| G3 | "I'm not a doctor, but …" | **no** `competence.claimed`/`status.claim` evidence. That turn appears as `counter_evidence` if a quantum exists. |
| G4 | "That might be the cause" ×2 | the cue-bearing trait is `partial` (hedged). `epistemic.hedging:+ exact`. |
| G5 | "I don't think you're not right" (double negation) | **expected limitation:** innermost-scope reading only, as DESIGN §5.2. This golden records the limitation and passes if behaviour matches the documented limitation. |
| G6 | contrast reply → counter-contrast → concession → thanks | one `dispute` episode, `generative: true`, facet `epistemic` present |
| G7 | contrast → hostility → status dismissal; no concession | `generative: false`. Facets `affective` and `status`. |
| G8 | `actor_a` asks for sources twice; `actor_b` had already posted a link; no hostility | `epistemic.question_demand:+` targeting `actor_b`. `pattern.sealioning` **not emitted** (disabled). Negative control: the same window without `actor_b`'s link → no `question_demand` quantum. |
| G9 | `actor_a` writes 6 of 9 turns | `interaction.floor:+` for `actor_a` only. Tie variant (3/3/3) → no floor quantum. |
| G10 | a question to `actor_b`; `actor_b` posts later turns, none replying to it | `interaction.responsiveness:- weak`. Variant where `actor_b` posts nothing later → no quantum. |
| G11 | dispute still open at the last turn | `generative: null` |
| G12 | "you people always …" plus a collective noun | `tribal.outgroup_reference:+`, facet `tribal`. A group noun alone, with no address construction → nothing. |
| G13 | meeting window (no `reply_to`) with an adjacent contrast | episode grows by adjacency (DESIGN §8.3) |
| G14 | no cues at all (neutral logistics chat) | `quanta: []`, `episodes: []`, `messages` identical to `/v1/classify` |
| G15 | quoted hostile text (blockquote) by `actor_a` | no `stance.hostility` for `actor_a` (depends on WI-3c; if WI-3c is not built, this is reported as failing, not skipped) |
| G16 | `reply_to` naming an id outside the window | accepted, no error, no reply edge, no non-response inferred |

**P2 — Negation/modality handling.** On a sealed synthetic negation set N (≥40 cue sentences, each with a plain, a negated and a hedged variant), every negated variant yields no `+` evidence for that cue's trait, and every hedged variant yields `match ≠ exact`. Predicted: 100% on single negation. Double negation and negation across clause boundaries are reported separately and expected to fail as documented.

**P3 — Graph-native compliance.**
- (a) `grep` of `domains/equilibrium_classify.py` and the server shows no new `if`/`for` over graph-read values, and no Python cue sets, trait names or thresholds. Every trait/cue string lives in `seeds/*.json` or teach-manifest inputs.
- (b) Every emitted quantum and episode has ≥1 rule id, each of the form `name:<pack_version>` with no `@`.
- (c) A search of the new seed rules finds no numeric literal used as a comparison operand. The only literals allowed are attr-key/enum strings and the structural `0`/singleton comparisons of DESIGN §6.2.
- (d) `OZMA_NO_LLM=1`, and no module on the request path imports `teacher_via_claude`. This is checked by import graph and by the Equilibrium `check_no_llm.py` on the consumer side.

**P4 — Determinism and invariance.**
- (a) The same request twice gives byte-identical responses.
- (b) **Relabelling invariance:** a consistent permutation of `actor_ref` strings and turn ids gives the correspondingly permuted output.
- (c) Prepending N neutral turns (G14 style) changes only positions, not the quanta set. One exception is `interaction.floor`, which is expected to change and is listed as such.

**P5 — Open vocabulary without code change.** A new trait is added via a teach manifest only (`EqTrait` + `EqTraitCue` + `LabelStatus` + its cues). The test trait is `epistemic.source_request`, whose definition is fixed now: evidence = question turns containing a `verb.communication` lemma with a source/evidence noun. `git diff --stat` then touches only `seeds/*.json`, the manifest input and the version constants. A synthetic window shows the new trait emitted with correct evidence.

**P6 — Throughput and memory.** Measured in-process and over loopback HTTP at c=1 on synthetic windows of 50, 200 and 500 turns, with turn lengths matched to the v0 synthetic set.
- Targets: 500-turn window p95 ≤ 1.5 s, 200-turn ≤ 0.5 s, peak RSS (`VmHWM`) ≤ 384 MB.
- Prediction: the 500-turn p95 is between 0.6 and 1.5 s. Ingest dominates (the v0 slice measured `kind_signals` at ~0.3 ms/msg), and quanta rules add < 50% over `/v1/classify`'s `run_rules` time for the same messages.
- Also reported: `run_rules` steps used against `DISCOURSE_FUEL`. This is how the fuel cap is set (DESIGN §2). It must give ≥2× headroom over the maximum observed on the synthetic sets.

**P7 — Base unchanged after 10k turns.** 20 windows × 500 turns plus 100 windows × 100 turns are replayed through `/v1/discourse`. Pass criteria:
- `snap.source_revision` is equal before and after;
- `strong_digest(base)` is equal at boot and after replay (including the periodic check);
- the worktree tree-state diff is empty;
- no file writes outside tmp (strace, negative-controlled as in the v0 slice).

**P8 — Fairness audit (descriptive; gates promotion, not this PREREG).** On the sealed red-team set R (DESIGN §10), report per trait the count of quanta emitted for each stratum: banter, quotation, sarcasm, dialect variant, non-native phrasing, protected-group mention, chair-led meeting, single-turn participant. Pre-registered expectation: zero `stance.hostility` on quotation items, zero `tribal.outgroup_reference` on bare protected-group mentions, and zero `competence.claimed` on negated credentials. Other strata are reported without a pass bar. Nothing moves from `shadow` to `audited` in this PREREG.

**P9 — Exploratory (not confirmatory).**
- Count of residual-minted dimensions (`sd_mint_quantum`) per window. They are not emitted on the wire.
- Coverage of `eq.coh.unmarked` if the ShapeDecode spike (WI-4) succeeds.
- The fraction of v0 n-gram cue matches that the lemma/class cues reproduce, on the v0 synthetic message set.

## 4. What is sealed

These are sealed at freeze (each artefact hashed; SHA-256 recorded in the freeze commit message by the orchestrator):

1. Golden expected outputs G1–G16 (DESIGN §8 semantics). They are written before WI-5 rules are run on them.
2. The negation set N and the red-team set R (synthetic). The authors write them and do not look at rule output until the run.
3. The `match` shape definitions (DESIGN §6.2): exact = plural evidence, no counter, no hedge; partial = E > C or hedged; weak = otherwise. The singleton/plural boundary may **not** be changed to any other count after data is seen.
4. The trait vocabulary v0.3.0 (DESIGN §8.1), facet definitions, the `generative` three-way shape, and the P5 test-trait definition.
5. The P6 targets and the P7 replay protocol.

These are **not** sealed, because they are engineering choices recorded in results: the `DISCOURSE_FUEL` value (derived per P6), lemma source (DESIGN §5.5), and WI ordering.

## 5. Reporting rules

- Report all predictions, including failures, with actual command output (counts, timings, digests).
- A changed golden or shape after freeze requires a new dated PREREG, with the deviation listed.
- Unverified machinery (DESIGN §12.3) is reported as verified, worked around (stating how), or not available, and never silently assumed.
- No real-corpus evaluation is part of this PREREG. Any later corpus work needs its own PREREG under Equilibrium's T7 split protocol.
