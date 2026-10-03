# Equilibrium conversation scaling (track T3d): results

Branch `t3d/scaling` (based on `t3c/conversation-tracking`). The pack goes from 0.5.0 to
0.5.1 / `eq-tax-0.5.1`. The wire is unchanged apart from the version strings. One
endpoint is added, `POST /v1/conversations/_batch`, and it follows the shared batch
contract. The design note is
EQUILIBRIUM_CONVERSATION_TRACKING_DESIGN_20261003.md, §T3d.

Data: the synthetic conversations are pseudonymous (`synthetic_window`). The AMI test
split (CC-BY-4.0) is read in place and reported as aggregates only. No LLM is used
anywhere; `OZMA_NO_LLM=1` is enforced by the sidecar.

## 1. Predictions (written before measuring the T3d code)

Baseline for the T3c code was measured on this host before any change, at load
average ~19–25 on 24 cores, for a 100-turn thread batch at prefix L:

| L | batch total | S0 (retained) | strata S1–S5 (scratch) |
|---|---|---|---|
| 500 | 2.1 s | n/m | 1.2 s |
| 1,000 | 3.5 s | 0.74 s | 2.2 s |
| 2,000 | 7.3 s | n/m | 4.4 s |

The baseline grows roughly linearly per batch, so total cost is quadratic per
conversation. The rule `eq.quanta.counter.untargeted` dominates term evaluations,
because it joins cues × all turns × quanta on every batch.

- **P1 (engine flags only):** S0 and tracking become ~flat in L. Every msg and
  tracking rule is a `batch` rule. Today those rules re-enumerate every message, and
  every external `add_node` clears every where-rule cursor. With semi-naive batch
  rules plus the isolated-node exemption, a batch enumerates only its own turns.
- **P2 (live monotone strata):** the per-turn cue rules (evidence, hedged, counter),
  run, question demand, response type, answered, episode root/extend/facet and
  competence corroboration leave the scratch fork. That should remove ≥ 60% of strata
  time at L = 2,000.
- **P3 (residual, honest prediction):** the scratch tier keeps the non-monotone rules
  — floor, selective non-response, unanswered, claim grounding, generative outcome,
  and the match shapes. Each of these binds over all actors, questions, quanta or
  episodes, and unanswered/responsiveness scan later turns per question. So per-batch
  cost will still grow with L, more slowly than the baseline. Expected exponent over
  1k–10k is 0.5–0.9: sub-linear over the measured range, NOT asymptotically flat.
  - I will not call this "flat" unless the exponent is < 0.2.
- **P4 (concurrency):** threads give 2–4× throughput at 8 independent conversations
  on this loaded host. A pre-change probe gave 2.4× at 8 threads on `run_strata`
  alone. Throughput saturates around 8 workers, because Python ingest and read-out
  hold the GIL.
- **P5:** the base source revision and strong digest are unchanged after 50k turns
  over 200 conversations.
- **P6:** exactness. All 26 golden runs (351 per-batch responses) captured from the
  T3c code are byte-identical to the T3d output after normalising 0.5.0 → 0.5.1.
  These include batch sizes 1, 3, 7 and 100 and conversations of up to 650 turns.

## 2. Measurements

All runs are on one host with 24 cores and 62 GB RAM, shared with other agents. The
load average is quoted per line (18–38). Measurements are service-level, in-process,
with no HTTP, via `scripts/equilibrium_scale_bench.py`. The synthetic thread
conversations use 12 pseudonymous actors and 35% cue lines.

**(a) Per-batch latency of a 100-turn batch at prefix L** (median of 3 consecutive
probes):

| L | T3c baseline (§1) | T3d, first cut (live layer, no S0 frontier) | **T3d final** | load |
|---|---|---|---|---|
| 100 | — | 0.83 s | **0.72 s** | 19 |
| 1,000 | 3.5 s | 2.56 s | **1.76 s** | 23 |
| 5,000 | — | 11.6 s | **7.26 s** | 22 |
| 10,000 | — (≈35 s if linear) | 28.3 s | **16.1 s** | 24 |

- Growth exponent over L = 100…10k: 0.67.
- Over every batch with prefix ≥ 1,000 (94 batches): **1.02**.
- Closing at 10,300 turns takes 3.96 s. That is the scratch strata plus the full read-out.

**(b) Throughput vs concurrency.** K independent conversations × 300 turns, 100-turn
batches, 16 workers:

| K | turns/s | speed-up | load |
|---|---|---|---|
| 1 | 152 | 1.0× | 22 |
| 2 | 291 | 1.9× | 22 |
| 4 | 454 | 3.0× | 22 |
| 8 | 623 | 4.1× | 25 |
| 16 | 679 | 4.5× | 26 |

**(c) `/_batch` with 16 conversations × 100 turns** (three consecutive batches; the
third has `close: true`): 2.61 s, 2.55 s and 3.12 s, i.e. 614, 628 and 513 turns/s.
All 16/16 items succeeded (load 26).

**(d) Memory per retained conversation.**

- 10 conversations × 1,000 turns added 120.6 MiB, i.e. ≤ 12.1 MiB per conversation.
  This is an upper bound: it includes first-use caches.
- One conversation × 10,000 turns, measured after closing those 10, added 44.1 MiB.
  The allocator reuses the freed pages, so this is **not comparable** with the 1k
  figure and is not a per-turn rate.

**(e) Base unchanged.** 50,000 turns across 200 retained conversations (three kinds,
via `/_batch`, 16 items per request) took 90 s, i.e. 554 turns/s (load 38).

- The base `source_revision` is unchanged.
- The strong digest equals the boot digest.
- Every periodic strong check passed (one every 50 requests).

**AMI replay** (the 16 test meetings at once through `/_batch`, 100 turns per item,
aggregates only):

- 12,643 turns in 15 batch requests, 30.0 s wall, i.e. 422 turns/s.
- Per-request p50 1.64 s, max 4.42 s.
- 0 item errors.
- 1,757 emitted quanta rows and 440 episode rows (deltas, summed over batches).
- Base unchanged (load 35).

**Exactness.** All 26 golden runs (351 per-batch wire responses) are byte-identical to
the T3c capture after normalising `0.5.0` → `0.5.1`. These cover the thread, climate,
declared/tracked meeting, the 5 tracking windows and 4 synthetic conversations of
240–650 turns, at batch sizes 1, 3, 7 and 100.

**Tests.** 194 passed, 1 skipped (42 min under load). The set is the 9 equilibrium
suites plus the batch-apply, empty-match, incremental-match and engine-provenance
suites. The new tests in `tests/test_equilibrium_scaling.py` cover:

- the batch contract and its validation;
- per-item errors;
- concurrent conversations equal sequential ones;
- serialisation of one conversation's batches;
- a busy session is never evicted;
- the engine flags on equal the engine flags off;
- HTTP.

**Per-rule profile at L = 3,000** (one 100-turn batch, ingest only, `rule_costs`): the
ingest takes 3.4 s.

- `eq.msg.negated_token.neg_op` takes 1.0 s: a full re-match, because its cursor is
  cleared each batch and I did not establish why.
- `eq.quanta.counter.untargeted` takes 0.38 s.
- Every other rule takes ≤ 0.07 s.
- Before the frontier marks, `eq.ep.facet`, `eq.trk.materialise`, `eq.win.*` and the
  live cue rules each re-matched the whole prefix ~110 times per batch.

## 3. Predictions vs outcome, nulls, gaps

- **P1 (S0/tracking ~flat): partly.** The window and tracking per-turn rules and the
  live layers are frontier-bound now: their full re-matches see only the batch.
  `neg_op` and the other S0 msg rules still re-match `agent -received-> m` over the
  whole conversation whenever their cursors are cleared.
  - I tried retiring `received` instead. Deleting an edge type invalidates the cursor
    of every rule matching it, so all msg rules went cold, and the hinted n-gram cue
    rules then probed the attribute index across the whole prefix. That was slower,
    so I reverted it.
- **P2 (≥ 60% of strata time leaves the scratch fork): hit.** At L = 1,000 the strata
  dropped from 2.2 s to 0.86 s.
- **P3: NULL. Per-batch cost is NOT sub-linear.**
  - The exponent over prefixes ≥ 1,000 is 1.02 (predicted 0.5–0.9).
  - The constant is about 2× lower than T3c: 1.76 s vs 3.5 s at 1k. Total cost per
    conversation is still quadratic.
  - The residual O(prefix) terms are:
    1. the S0 msg rules' cursor clears (above);
    2. the scratch tier, re-derived over the whole prefix every batch: floor,
       selective non-response, unanswered, claim grounding, generative outcome, match
       shapes;
    3. the read-out: all quanta, episodes and open questions are re-read and re-signed
       every batch;
    4. `AttrByName` rules: any attribute write clears their cursors, because
       per-node predicate retraction does not cover dynamic-key reads.
  - Removing these needs:
    - retraction rules (del_edge / attr reset) so the six non-monotone families can
      run live;
    - an engine rung for node-seeded re-evaluation on term-edge and dynamic-key
      writes;
    - a delta read-out, e.g. `run_rules_delta_report` restricted to touched quanta
      and episodes.
  - None of these is done.
- **P4 (2–4× at 8 conversations): hit.** 4.1× at 8 and 4.5× at 16, saturating as
  predicted. Python ingest and read-out hold the GIL.
  - Threads were kept because a pre-change probe measured 2.4× at 8 threads.
  - A process pool was not tried; it would lose the shared copy-on-write base.
- **P5: hit.**
- **P6: hit.**
- **Bug found by the batch tests:** NLTK WordNet is not thread-safe. Parallel items
  raised inside `synsets()`. WordNet lookups are now serialised behind a lock; the lru
  caches keep repeats lock-free.
- **Not verified:**
  - `cargo test` for the touched Rust. The Python engine suites for those flags pass,
    and the new flags default OFF.
  - Thread-safety of `kind_signals`. The 8-thread equality test passes.
  - Behaviour above 16 workers.
  - Memory per turn at 10k (see (d)).
