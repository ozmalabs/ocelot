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

## 4. Stage A: S0 / AttrByName cursor clears, delta read-out (sub-linear track)

Goal: per-batch cost sub-linear (ideally flat) in conversation length. Stage A covers
the retained-fork layers (S0, tracking, live L1/L2) and the read-out; the six
non-monotone scratch families are stage B. Pack stays 0.5.1; the wire is unchanged.

### 4.1 Diagnosis (engine instruments, 300–2,000-turn synthetic thread)

Tools: `rule_costs` (per-substrate, so the scratch fork does not pollute it),
`SUBSTRATE_TRACE_RULE` (`[TRACE-IM]` cursor state per visit), `rule_access_sets`,
scale-audit counters, and a bisection over `run_rules(k)` on forks with a probe
that dirties the rule and reports whether its cursor is MISSING.

| # | rule family | exact cause | fix (flag, default OFF) |
|---|---|---|---|
| 1 | every rule, S0 msg rules worst (`neg_op` 0.68 s at L=2k) | `eq.trk.cursor` has `del_edge w -eq_trk_pending-> m`. Under `incremental_match` a progressing rule with ANY delete effect clears EVERY rule's cursor (the global-bump equivalent kept for `DelNode` cascades). It fires once per tracked turn, so every batch cold-starts all rules. Bisection: first cold cursor after step 1 of the tracking tick, last progressing rule `eq.trk.cursor`. | `precise_rule_deletes`: a DelEdge-only rule invalidates like an external `remove_edge` (per-type delete version + where/term readers + non-local opaque readers). |
| 2 | `neg_op`, every `prov`/`eqrule:` writer | Own-write self-invalidation: an `AddEdge` effect's own type is in `term_edge_reads` (`eq_neg_next`), a `SetAttr`'s own key is in `read_set` (so `hits_attr && has_where`). Each firing cleared the rule's own cursor. | `own_write_exempt`: cursor clearing uses `read_set_strict` (where + computed-arg reads only). |
| 3 | msg rules (mint-once `eqfire:` guard), n-gram cue siblings (`eqhit:<cue>`) | Genuine where-read of a key the rule (or a sibling) writes, so the cursor is cleared on every firing and the next visit is a full re-match. | `write_frontier`: if every read of the key is on an unshadowed match variable, the written nodes are seeded and re-checked node-locally (`try_predicate_retraction` node-seeded pass). |
| 4 | negation/hedge-scope rules, `leading_marker` | External `add_edge(m, eq_has_token, t)` under `fresh_node_exempt` cleared every rule reading `Neighbours(m, eq_has_token)` in a term, so each batch cold-started them. | `write_frontier` edge locality: an edge type read only as `Neighbours`/`InNeighbours` of a match variable seeds the edge's src/tgt (rule-effect inserts via a new graph edge-write log; external inserts directly). |
| 5 | AttrByName readers (cue counters, `ep.facet`, quanta evidence) | `reads_any`, so any rule-effect write cleared their cursors. | `write_frontier`: `AttrByName(v, …)` on a match variable is local; a dynamic-key write seeds only bindings that bind the node at `v`. |
| 6 | (exposed by 1–5) | The semi-naive path itself was O(prefix) per seed. Sub-matches kept the declared edge order and dropped index hints and pushdown. A cue 5-gram driven by a new `eq_next` edge scanned every `received` edge per seed: one rule took 2.4 s per batch at L=500. The L2 counters enumerated cues × quanta without pushdown. | `seeded_join_order`: greedy connectivity order from the seed, plus the rule's index hints, plus where-conjunct pushdown, plus a smaller-side probe for both-bound edges. Traversal only. |

### 4.2 Delta read-out

- **Open questions** are now the tracking rules' graph-resident QUD set
  `w -eq_qud-> q`. It is opened when a question is tracked and closed by the tracked
  `eq_answers` edge, which is the only source of that edge. The read-out is
  O(open questions); before, it scanned every turn.
- **Quanta / episodes.** Every tick reports the nodes it wrote, via
  `run_rules_delta_report`. Only these rows are re-read and compared with the ledger
  marks:
  - rows written by this batch's retained ticks or scratch strata;
  - rows written by the previous batch's scratch strata, whose writes may have
    vanished. Their ids are an `eq_prev_touch` ledger attribute.
- **No saving yet (null).** The scratch match shapes write every quantum each batch.
  At L=2,000 they touch 1,044 of 1,044 quanta and 163 of 173 episodes. So the
  candidate set is still ~everything:
  - an A/B at L=2k gives the same read-out cost either way (63–80 ms);
  - the report overhead was within noise.
  - The saving arrives once stage B makes those families live.

### 4.3 Measurements

**(a)** One host with 24 cores, shared with other agents; the load is quoted per run.
Each value is the median of 3 probes of a 100-turn batch, in ms. The baseline is the
same engine binary in the same session, with the stage-A changes switched off: the
four new flags off, the full read-out, and turn-scan open questions. That is the
289a82c1 strategy. For reference, §2 measured 289a82c1 itself at
720 / 1,760 / — / 7,260 / 16,100 ms at load 19–24.

| L | baseline total | **stage A total** | S0 (base → A) | trk | live L1 | live L2 | scratch | read-out |
|---|---|---|---|---|---|---|---|---|
| 100 | 449 | **425** | 162 → 179 | 73 → 62 | 34 → 25 | 91 → 54 | 32 → 26 | 18 → 17 |
| 1,000 | 1,177 | **580** | 618 → 193 | 92 → 61 | 60 → 38 | 213 → 69 | 116 → 131 | 39 → 52 |
| 2,000 | 2,144 | **876** | 1,190 → 193 | 121 → 67 | 79 → 70 | 283 → 82 | 296 → 353 | 70 → 82 |
| 5,000 | 4,973 | **1,719** | 3,058 → 214 | 158 → 68 | 183 → 155 | 367 → 102 | 971 → 972 | 144 → 169 |
| 10,000 | 10,322 | **3,628** | 6,481 → 233 | 264 → 65 | 334 → 263 | 404 → 111 | 2,491 → 2,554 | 294 → 315 |

- Load: baseline 7–19, stage A 9–13.
- Growth exponent over L ≥ 1,000, baseline → stage A:

  | component | baseline | stage A |
  |---|---|---|
  | S0 | 1.02 | **0.09** |
  | tracking | 0.43 | **0.02** |
  | L1 | 0.77 | 0.84 |
  | L2 | 0.28 | 0.21 |
  | scratch | 1.33 | 1.26 |
  | read-out | 0.86 | 0.78 |
  | total | 0.94 | 0.79 |

  Over every batch with prefix ≥ 1k (94 batches), the exponent goes from 1.00 to
  0.85.
- At 10k the batch takes 3.6 s against 10.3 s, a 2.8× improvement. Close at
  10,300 turns takes 2.8 s.
- **The batch as a whole is NOT sub-linear yet.** At 10k the scratch tier is 70% of
  the batch.

**Load-independent S0 check.** Scale-audit `cand_tested` for one 50-turn batch's S0
tick:

| prefix | stage A | pre-stage-A flags |
|---|---|---|
| 100 | 272,509 | 714,647 |
| 600 | 313,207 | 3,171,371 |
| 1,200 | 335,794 | — |

Under stage A the work grows 1.23× for 12× the prefix. Under the pre-stage-A flags it
grows 4.4× for 6× the prefix. The regression test
`test_s0_msg_rules_do_not_rescan_the_prefix` asserts < 2× at 6×. It fails with the
new flags off.

**Exactness.** All 26 golden runs (351 per-batch wire responses) captured from
289a82c1 before any change are byte-identical. The comparison is raw, with no
version normalisation. It was re-run after every engine change (6 builds).

### 4.4 Remaining gaps (for stage B)

1. **Scratch tier: 2.55 s at 10k, exponent 1.26.** This is the six non-monotone
   families. It also keeps the delta read-out from paying off.
2. **Live L1: 0.26 s at 10k, exponent 0.84.**
   - `eq.competence.corroborated` / `.contested` pair each new reply with every
     earlier claim of the addressed actor. That is the rule's shape: O(claims) per
     turn.
   - `ep.facet` (and the L2 counters) are gated by `eq_l1_open` / `eq_l2_open`, which
     are re-added every batch. The semi-naive pass therefore drives from the gate edge
     against all episode memberships. A permanent gate would be equivalent: the
     frontier marks already confine the bindings.
3. **Read-out: 0.32 s at 10k.** It is bounded by the scratch-touch set; see gap 1.
4. **Caveat on `own_write_exempt`.** Like the committed where-less path, a stable
   binding no longer re-fires its `SetAttr` after another writer changes the same key
   on the same node. It is exact when writers of a key do not contest it, which holds
   in this pack (goldens). This is a semantic condition, not a proof for arbitrary
   packs.
5. **Not verified:** see §4.5.

### 4.5 Tests

The run covered the 8 `tests/test_equilibrium_*.py` suites plus the batch-apply,
empty-match, incremental-match, engine-provenance and predicate-retraction suites.
It ran with `-n 6`, under load ~9–13. The result: 189 passed, 1 skipped, 2 failed.

- **`test_phase9_exit_10k_base_unchanged_no_writes`** failed because I edited two
  source files while it ran; the test watches for that. Re-run alone, it passed.
- **`test_predicate_retraction_migrated::test_covered_work_count_drops_to_constant`**
  fails identically (exponent 0.96) with the committed 289a82c1 engine binary, taken
  from `git show HEAD:…/_native.abi3.so` and loaded from a temp path. So the failure
  is pre-existing and not caused by stage A. That suite was not in §2's test set.

New tests in `tests/test_equilibrium_scaling.py`:

- delta read-out + QUD open questions equal the full re-read + turn scan (thread and
  meeting, 40-turn batches);
- the S0 matcher-work regression, shown above to fail with the flags off;
- the new setters exist and default off.

Not verified:

- `cargo test --lib` does not link in this environment: the pyo3 extension-module
  symbols are missing. This was not caused by these changes.
- There is no formal soundness proof for `write_frontier` / `own_write_exempt` beyond
  the reasoning in the field docs, the goldens and the suites.

## 5. Stage B: the six non-monotone families run live (no scratch fork)

Goal: remove the per-batch scratch fork. Six families were re-derived over the whole
conversation every batch: floor, selective non-response, unanswered, claim grounding,
generative outcome, and the match shapes. They now run on the retained fork. Each
keeps bounded rolling state and has explicit, dedicated retraction edges. Pack stays
0.5.1 (rule ids on the wire carry the version, so it cannot move); the wire is
unchanged. Design: EQUILIBRIUM_CONVERSATION_TRACKING_DESIGN_20261003.md §T3d stage B.

### 5.1 Predictions (written before the final measurement run)

One interim bench (a) run was made during development. It came after the six families
went live, but before the episode extend/facet marks and the bulk read-out. It
measured 482 / 767 / 1,055 ms at L = 1k / 5k / 10k, an exponent of 0.33 over 1k–10k.
The predictions below are for the final code.

- **B1 (a):** the 10k batch takes 0.7–0.9 s. The total exponent over 1k–10k is
  0.15–0.30.
  - S0 stays flat (~0.25 s).
  - Tracking ≤ 0.10 s (exponent ≤ 0.15).
  - L1 ≤ 0.12 s (≤ 0.4).
  - L2 ~0.11 s (flat).
  - Read-out 0.06–0.12 s, with exponent 0.5–0.8. That growth is NOT removable:
    a quantum whose evidence changed is re-emitted with its full evidence list, and
    those lists grow with L, so the wire bytes per batch grow too.
- **B2:** close at 10.3k turns takes ≤ 0.35 s (stage A: 2.8 s).
- **B3:** (b), (c), (e) and the AMI replay get faster than §2, because all of them
  paid the scratch tier. AMI should exceed 2× the 422 turns/s of §2. The base stays
  unchanged.
- **B4 (d):** memory per retained conversation is the same as §2 or up to ~20% higher
  (new state edges, and the permanent per-family quantum nodes).
- **B5:** if exactness is impossible for a family, I stop and report it rather than
  change semantics. (Verified before the run, so this is not a prediction: §5.4.)

### 5.2 What changed

**Pack** (scripts/_equilibrium_quanta_rules.py "0.5.1 stage B", `apply_nm`; the
builder asserts `check_nm_pack`). The scratch-fork rules are replaced by live
successors, which keep the same provenance names.

| family | rolling state (bounded) | retraction (dedicated edge type) |
|---|---|---|
| floor | `a.eq_nturns`, counted by the cursor; `a.eq_nturns_b`, the batch-final copy on the L1 frontier; compared over actors | existence `eq_nm_quantum`; runner-up `eq_floor_ru`; runner-up turns `eq_counter_nm` |
| selective non-response | per actor, the wait set `a -eq_rsp_wait-> q` → `q -eq_rsp_due-> a`, plus `q -eq_rsp_ans-> a` (cursor) | open evidence `eq_evidence_nm`, retracted when the answer edge arrives; existence |
| unanswered | per window, the wait set `w -eq_unans_wait-> q` → `q -eq_unans_due-> w` (cursor) | open evidence, retracted on `eq_answers`; existence |
| claim grounding | `a -eq_cg_grounded-> g`, permanent | '−' retires once (existence) |
| generative outcome | per-turn cue-role marks (L1 frontier) and membership marks `eq_ep_res` / `eq_ep_esc` | resolved / escalated / reopened clear each other |
| match shapes | none; evaluated only when a quantum's or facet's own edges change | siblings' provenance set to null; facet provenance on the episode cleared by a one-hop check |

- Every family has a permanent node, linked by an `eq_*_node` edge. That node
  accrues the monotone parts. Node creation is a separate rule, so the frequent
  attach / evidence rules never write a node type; such a write clears every opaque
  reader.
- `eq.ep.extend` / `eq.ep.facet` (live L1 since 0.5.1) now read per-turn cue marks
  instead of the dynamic cue look-up behind the `eq_l1_open` gate. Their output is
  identical. That gate made them re-match every episode membership each batch; at
  L = 8k `eq.ep.facet` alone was 80–100 ms of L1.

**Engine.** Two flags, both default OFF, are enabled only by `incremental_engine`.
They are rebuilt with scripts/engine_build.sh, and `_native.build.json` is
regenerated by it.

- `set_hop_frontier`. The write-frontier locality gets a second install-time variant:
  - pure set and arithmetic operators are transparent;
  - an `Exists` variable over `Neighbours` / `InNeighbours` of a match variable is
    one-hop local;
  - a `DelEdge` of a non-matched type is a read at its bound endpoints.
- `set_delete_frontier`. A rule-effect `DelEdge` re-checks only the endpoint
  bindings of a local or own-target reader, instead of clearing its cursor. A pure
  deleter is not woken at all. The graph keeps a rule-effect `edge_delete_log` for
  this.
- Rung B was needed. A rule-level formulation alone was exact, but it was not
  sub-linear. Every retraction edge deleted, or every node minted, cleared the
  cursors of the rules that add or read that edge, and those rules re-matched every
  open question each batch (§5.3, work check).

**Adapter** (domains/equilibrium_classify.py):

- `_emit` reads the retained fork. The scratch fork and the `eq_prev_touch` ledger
  attr are gone.
- Quanta come from `eq_has_quantum` ∪ `eq_nm_quantum`. Evidence is ∪ `eq_evidence_nm`
  and counter evidence is ∪ `eq_counter_nm`.
- `_refs` and `_new_quanta` read attrs in bulk (`get_attr_many`). Positions are
  unique, so the order is unchanged.
- `run_strata` is kept but no longer called.

### 5.3 Measurements

**(a)** Median of 3 probes of a 100-turn batch, in ms, at load 8.7–10.2. Same host
and same bench as §4.3.

| L | stage A total | **stage B total** | S0 | trk | L1 | L2 | read-out | scratch |
|---|---|---|---|---|---|---|---|---|
| 100 | 425 | **408** | 187 | 71 | 29 | 62 | 8 | — |
| 1,000 | 580 | **442** | 202 | 85 | 35 | 75 | 12 | — |
| 5,000 | 1,719 | **592** | 216 | 122 | 52 | 107 | 30 | — |
| 10,000 | 3,628 | **692** | 246 | 126 | 87 | 111 | 49 | — |

Growth exponent over L ≥ 1,000, stage A → stage B:

| component | stage A | stage B |
|---|---|---|
| S0 | 0.09 | 0.08 |
| tracking | 0.02 | 0.18 |
| L1 | 0.84 | 0.37 |
| L2 | 0.21 | 0.18 |
| read-out | 0.78 | 0.60 |
| scratch | 1.26 | (gone) |
| **total** | 0.79 | **0.19** |

- Over every batch with prefix ≥ 1k (94 batches), the exponent is **0.15** (stage A
  0.85). Over L = 100…10k it is 0.11.
- At 10k the batch takes 0.69 s: 5.2× faster than stage A and 15× faster than the
  289a82c1 strategy (10.3 s).
- Close at 10,300 turns takes **169 ms** (stage A 2.8 s).
- Two components still grow:
  - The read-out tracks the wire. The median response of a 100-turn batch is 144 KB /
    320 KB / 527 KB at L = 1k / 5k / 10k, carrying 3.0k / 15.2k / 29.5k evidence refs
    across ~210–230 changed quanta rows (exponent ≈ 0.56). A changed quantum is
    re-emitted with its full evidence list.
  - Tracking grows mildly (0.18; it was flat in stage A). The new cursor rules are
    per turn, but `eq.trk.rsp.due` re-matches a's wait set, and the wait set of an
    actor who rarely posts keeps growing. I did not isolate this further.

**Load-independent work check.** Scale-audit candidate tests of the stage-B rules
over one whole 50-turn batch (every tick) of a 700-turn synthetic meeting:

| prefix | stage-B flags on | `hop_frontier` + `delete_frontier` off |
|---|---|---|
| 100 | 2,560 | 5,031 |
| 600 | 2,520 | 8,638 |

The work is flat with the flags on (6× the prefix, 0.98× the work) and grows 1.7× with
them off. `test_nonmonotone_families_do_not_rescan_the_prefix` asserts < 1.5×. On the
2,000-turn bench thread the same count is 9.0k / 12.7k / 20.9k at prefix 200 / 1k /
2k. The residual comes from rules over actors, whose number grows with the prefix
(e.g. `floor.ru` ~A³), and from runner-up rewrites.

**(b) Throughput vs concurrency** (K × 300 turns, 16 workers, load 7.2–7.3):

| K | turns/s | §2 (289a82c1, load 22–26) |
|---|---|---|
| 1 | 247 | 152 |
| 2 | 471 | 291 |
| 4 | 771 | 454 |
| 8 | 1,020 | 623 |
| 16 | 1,131 | 679 |

**(c)** `/_batch`, 16 × 100 turns, three batches: 981 / 855 / 902 turns/s, 16/16 ok
(load 7.1–7.5). §2: 614 / 628 / 513.

**(d)** Memory: 10 retained × 1,000 turns adds 12.12 MiB per conversation (upper
bound), the same as §2 (12.1). The 1 × 10,000 figure (+5.4 MiB after closing the 10)
is allocator reuse and, as in §2, is not comparable.

**(e)** 50,000 turns over 200 retained conversations take 47 s (1,065 turns/s; §2:
554). The base `source_revision` is unchanged, the strong digest equals the boot
digest, and every periodic strong check passed (load 15).

**AMI replay** (the 16 test meetings concurrently through `/_batch`, 100 turns per
item, aggregates only):

- 12,643 turns in 15 requests, 14.6 s wall, i.e. **869 turns/s** (§2: 422, 2.06×).
- Per-request p50 0.65 s, max 2.38 s (§2: 1.64 / 4.42 s).
- 0 item errors; base unchanged; load 14.
- Emitted rows: 1,757 quanta and 440 episodes. These are the same totals as §2, as
  expected from exactness.

### 5.4 Exactness

- **Goldens.** All 26 golden runs captured from 289a82c1 before stage A (351
  per-batch responses, batch sizes 1 / 3 / 7 / 100) are byte-identical, compared raw.
  I re-ran them after every pack rebuild and after each of the 4 engine builds. A
  fifth build was a temporary cursor-clear trace; it was used for diagnosis only and
  then reverted. They are identical with the new flags off as well as on.
- **Larger conversations, beyond the goldens.** I exported HEAD 289a82c1 with
  `git archive`, including its committed engine binary, into /tmp and captured 7
  runs there:
  - a 2,500-turn thread at batch size 100;
  - a 2,000-turn meeting at 100 and at 37;
  - a 1,500-turn channel at 100 and at 250;
  - 300 turns at batch size 1;
  - a 600-turn one-shot.

  All 429 per-batch responses are byte-identical to the stage-B output.
- **Per-prefix check.** The new `test_nonmonotone_families_equal_one_shot_at_every_prefix`
  compares, after every 3rd batch of thread / meeting / channel conversations, the
  complete read-out with a fresh one-shot run over the same prefix. It also asserts
  that at least one non-monotone quantum existed at one checkpoint and was gone at a
  later one, so retraction is exercised.
- **Null.** A 1,200-turn one-shot exhausts the rule fuel (`budget_exhausted`) with
  HEAD, and also with stage B. So that case is not compared; the capture uses a
  600-turn one-shot instead.

### 5.5 Predictions vs outcome

- **B1 total: met.** 0.69 s at 10k against the predicted 0.7–0.9 s, and an exponent of
  0.19 against 0.15–0.30.
  - S0 flat: yes.
  - Tracking ≤ 0.10 s: **missed**. It was 0.13 s, exponent 0.18 against the predicted
    ≤ 0.15.
  - L1 ≤ 0.12 s: met (0.09 s, exponent 0.37 within ≤ 0.4).
  - L2 flat: yes.
  - Read-out within the predicted 0.06–0.12 s: **missed, but better**. It was 0.05 s;
    the exponent 0.60 is inside the predicted 0.5–0.8.
- **B2 close: met.** 169 ms against ≤ 0.35 s.
- **B3: met.** AMI 2.06×; (b), (c) and (e) all faster; base unchanged. The load was
  lower than in §2 (7–15 against 22–38), so part of that gain is the host.
- **B4: met.** Memory per conversation is unchanged (12.1 MiB).
- **Not "flat".** The read-out is bounded below by the wire size, which grows with L.
  The total exponent 0.19 is near-flat over 1k–10k, not O(1).

### 5.6 Remaining gaps

1. **The read-out follows the wire** (exponent 0.6). To go further, the wire contract
   would have to change, e.g. evidence deltas instead of full lists. That is a contract
   change, not an evaluation change, so I did not do it.
2. **Tracking grows mildly** (0.18). The suspected cause is the wait sets of rarely
   posting actors in `eq.trk.rsp.due`; I have not verified it.
3. **Floor runner-up changes** rewrite O(turns / actors) `eq_counter_nm` edges. Each
   delete also does O(population) `retain` work in the graph. The wire change is the
   same size, so this is inherent to the semantics; it happens in roughly half the
   batches of the bench thread.
4. **`eq.competence.corroborated` / `.contested`** still pair a reply with every
   earlier claim of the addressed actor (stage A gap 2).
5. **Pack conditions instead of proofs.**
   - `check_nm_pack` asserts that no cue row names a non-monotone trait, and that
     there are no compose rows.
   - Unanswered reads "answered" off `eq_answers` + `enabled(inquiry.answered)`, which
     is exactly the input that `eq.quanta.inquiry.answered` consumes. If that rule's
     shape changes, this equivalence must be re-checked.
   - The stage-A `own_write_exempt` caveat (uncontested writers) applies to the
     switching shape rules too. Their writers are mutually exclusive by construction.
6. **No formal soundness proof** for `hop_frontier` / `delete_frontier` beyond the
   reasoning in the field docs, the goldens, the HEAD-reference runs and the suites.
   `cargo test --lib` still does not link here (pre-existing).

### 5.7 Tests

The run covered the 8 `tests/test_equilibrium_*.py` suites plus the batch-apply,
empty-match, incremental-match, engine-provenance and predicate-retraction suites. It
ran serially under load ~5–15 and took 31.6 min. The result: **195 passed, 1 skipped,
1 failed.**

- The failure is `test_predicate_retraction_migrated::test_covered_work_count_drops_to_constant`
  (exponent 0.96). It is the same failure stage A found on the committed 289a82c1
  binary (§4.5), so it predates stage B.
- The skip is `test_engine_provenance_migrated.py:414`, which skips because the tree
  has uncommitted Rust source.
- The first run also failed 3 pack-shape tests, all fixed before the second run:
  - two new rule names had more than 3 segments, so they were renamed;
  - the turn counter used the numeric literals 0 and 1, which PREREG P3(c) forbids.
    It now counts |{}| / |{m}|;
  - the climate pack's rule set gained `inquiry.unanswered.node` / `.retract`, so the
    expected set in `test_climate_traits_are_shadow_and_versioned` was updated.

New tests in `tests/test_equilibrium_scaling.py`:

- `test_nonmonotone_families_equal_one_shot_at_every_prefix` (thread / meeting /
  channel; asserts that retraction happens);
- `test_stage_b_flags_equal_without` (the hop / delete frontier on vs off);
- `test_nonmonotone_families_do_not_rescan_the_prefix` (< 1.5×; it fails with the two
  flags off);
- the default-off setter test, which now also covers `set_hop_frontier` /
  `set_delete_frontier`.
