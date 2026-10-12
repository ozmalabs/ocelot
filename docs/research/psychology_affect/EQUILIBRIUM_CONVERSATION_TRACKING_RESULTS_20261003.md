# Equilibrium conversation tracking — results (T3c stage O2, pack 0.5.0)

Design: `EQUILIBRIUM_CONVERSATION_TRACKING_DESIGN_20261003.md`. No LLM (OZMA_NO_LLM=1).
Synthetic windows in tests use pseudonyms. Real data is the AMI test split
(CC-BY-4.0, 16 meetings), read in place from `hf_samples`. Only aggregate counts
were printed or kept.

Latency runs shared a busy host (load average 26–35 on 24 cores, with other
agents running), so treat the absolute ms values as upper-ish bounds.

## Predictions (written before the AMI run) vs measurements

| # | prediction | measured | verdict |
|---|---|---|---|
| P1 | 25–50% of turns tracked; 0 declared | 41.1% tracked (5,199/12,643), 0 declared, 58.9% none | hit |
| P2 | ~402 questions; 70–90% answered; 10–30% open at close | 402 questions; 400 answered (99.5%); 2 open | **miss**: closes far more than predicted |
| P3 | answer distance p50 = 1 turn, p95 ≤ 5 | p50 2, p95 14; only 165/400 answers adjacent | **miss**: mostly non-adjacent |
| P4 | 50–75% of turns root a thread | 58.9 threads per 100 turns (per meeting min 173, median 433.5, max 804) | hit |
| P5 | batch p95 1.3–1.8 s; RSS within +15% of O1 | batch p95 1.50 s (O1 1.09 s), max 1.98 s; close p50 537 ms (O1 393 ms); RSS 197.9 → 249.1 MiB peak with ≤ 4 retained sessions | hit on latency; RSS **not comparable** to O1's per-turn figure |
| P6 | name-mention addressees ≈ 0 on AMI; base unchanged | not measurable on the wire (addressee provenance is not emitted); 48.6% of turns carry an addressee; base unchanged (revision + strong digest) | null / hit |

### AMI structure vs O1

| | O1 (declared only) | O2 (tracked) |
|---|---|---|
| answers | 0 | 400 |
| open questions at close | 402 | 2 |
| inquiry.unanswered quanta | 56 | 0 |
| inquiry.answered quanta | 0 | 117 |
| episodes | 0 | 437 |
| turns with more than one target | — | 76 |

The 117 inquiry.answered quanta are counted per (answerer, asker) pair, against
400 answer edges.

Other O2 quanta counts:

- voice.dissent: 122
- interaction.run: 63 (from `eq_continues`)
- response.engagement: 17
- response.dismissal: 0
- competence.acknowledged: 17

### Reading P2 and P3 (the misses)

- **P2.** Nearly every question closes. The room question counts as answered at
  the first answer-type turn by another actor, and AMI is dense with backchannels
  ("yeah", "okay").
- **P3.** Answers are mostly non-adjacent because addressed questions stay open
  until the addressee's next answer-type turn.

This is structure only. **No accuracy is measured.** The HF AMI dump has no
adjacency-pair or addressee annotation (the original AMI corpus does, in NXT
form, but it is not downloaded). So 99.5% answered is a property of the rules,
not a validated rate. The design doc lists "room questions close too easily" as
a gap. This result supports it.

## Synthetic tests (all pass)

`tests/test_equilibrium_tracking.py` has 7 tests:

- **Non-adjacent answer.** A asks B by name; C and D chat; B answers two turns
  later. B's turn gets responds_to and answers pointing at the question, and
  inquiry.answered evidence is [question, answer].
- **Interleaved two-thread channel.** `platform_thread` separates the threads,
  and so does a name mention. With neither, the most recent open question wins.
  The test asserts this documented limitation.
- **Name mention.** A name mention resolves only for an actor who has already
  spoken.
- **Second-person reply.** It resolves to the last addresser.
- **Counter-question.** It does not close the question. After the sub-question
  is answered, the original question is back on top (QUD) and is answered.
- **Dismissal.** It does not close the question. The test runs incrementally
  over two conversation batches and checks open_questions after each.
- **Declared reply.** A declared reply to an older turn is honoured over
  tracking: basis is declared and the reply answers that turn.

`tests/test_equilibrium_conversations.py::test_incremental_batches_equal_one_shot`
gained 4 windows: tracked meeting G-M1, non_adjacent, counter (plus contrast and
concession turns), and a 240-turn synthetic meeting. With batch sizes 1, 3 and
100 (7 and 100 for the 240-turn window), every per-turn row and the final
quanta, episodes and open questions equal the one-shot result. For the short
windows, every emitted delta also equals the one-shot read-out over that prefix.

Goldens updated for O2:

- **G-M1 without replies.** Asserts the full tracked structure and quanta.
- **Thread golden.** interaction.run is restored, via `eq_continues`.
- **Climate meeting.** The tracked meeting reproduces the declared-reply result
  exactly.
- **Climate golden.** c09 now declares a self-continuation reply, so c08 stays
  unanswered as the golden intends. Without it, tracking reads lead_l's next
  turn as the answer.

## Scale (synthetic, concurrency 1)

| run | measured | O1 |
|---|---|---|
| 100 retained conversations × 100 turns, batch | p50 408–414 ms, p95 484–491 ms, max 582–607 ms (two runs) | p95 388 ms |
| same run, memory | 1.85 MiB per retained conversation (upper bound) | 1.77 MiB |
| second wave of 100 conversations | +0.4 MiB | — |
| 1500-turn thread, 100-turn batches | last batch 4.40–5.15 s, close 3.14–3.64 s (two runs) | last 5.2 s, close 4.5 s |
| /v1/discourse, 500-turn window | p95 6.3 s; 8.9 s before the thread fix | not reported |
| /v1/discourse, 200-turn window | p95 1.6 s; 2.1 s before the thread fix | not reported |

The long thread is no slower than O1, and in one run faster, because thread ids moved into the cursor (see
below). The 10k-turn base was unchanged: source revision and strong digest
equal.

The PREREG P6 targets (500-turn ≤ 1.5 s, 200-turn ≤ 0.5 s) are **not met**. I
did not measure whether O1 met them. Every /v1/discourse chunk re-runs the
strata over the whole prefix (an O1 design point).

Ablation on a 500-turn window, tracking rules on vs off, 3 seeds:

| window | on | off |
|---|---|---|
| meeting | 3.6–4.5 s | 1.3–1.5 s |
| thread | 3.4–4.0 s | 1.7–2.1 s |

"Off" also drops thread ids, so it is not exactly O1. The extra cost is mainly
the S2 work over the new structure. On a 500-turn meeting batch, the ticks are:
S0 267 ms, cursor 239 ms, strata 808 ms.

## Engine-cost findings (fixed during O2)

1. **Writing `eq_responds_to` per cursor step re-enumerated every reply-pair msg
   rule on every pass.** The cursor tick took 771 ms per 100 turns at 500 turns.
   With targets written as `eq_trk_to` and materialised once after the sweep,
   it takes 225 ms.
2. **O1's S1 `thread.root` / `thread.inherit` propagate one chain hop per pass.**
   With tracked chains this cost 1.45 s of a 1.5 s S1 tick at 500 turns. Thread
   ids are now decided once per turn in the cursor (earliest parent's thread,
   else root), and S1 is 65 ms.

## Nulls and what was not verified

- **Accuracy.** No accuracy of responds_to, addressees or answers against human
  annotation. No annotated corpus was used.
- **Addressee breakdown.** Name-mention vs second-person vs target-derived
  addressees are not separable on the wire.
- **topic_id.** Always null; no topic shape was built.
- **Concurrency.** Per-conversation concurrency is still a global lock (O1).
- **Equilibrium client.** The Equilibrium-side client was not exercised against
  O2 output in this stage.
