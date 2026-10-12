# Long-session cost: diagnosis and fix (2026-10-10)

Found during P0 of the [open-ended plan](OPEN_ENDED_P0_REPLY_QUALITY_RESULTS_20261010.md): on one conversation session, per-turn time grew superlinearly, which would degrade a long daemon conversation.

## Result

The test is a single production-path session of 150 held-out persona turns (dialogues 10–19, both seats) on a fresh conversation boot, run **offline** so no reply depends on network timing. The same session was run in a HEAD worktree (before) and in the fixed tree (after):

| Turns | Before (s/turn) | After (s/turn) |
|---|---|---|
| 1–25 | 0.317 | 0.292 |
| 26–50 | 0.581 | 0.385 |
| 51–75 | 1.444 | 0.413 |
| 76–100 | 1.814 | 0.435 |
| 101–125 | 4.262 | 0.624 |
| 126–150 | **10.601** | **0.789** |

**All 150 replies and turn outcomes are byte-identical before and after.** The improvement at turn 150 is 13×. Time still grows, by about 2.7× over 150 turns, but no longer superlinearly enough to dominate.

## Diagnosis (`evaluation/substrate_capability/long_session_cost_v1.py`)

The probe records per-phase wall time and the engine's own per-rule cost counters (`Substrate.rule_costs`) per 25-turn window.

**Before**, at turns 126–150:
- release took 5.4 s of the 6.5 s per turn;
- rules took 0.90 s per turn.

**Release (Python).** cProfile at turn 100 showed `graph_turn_reply_outcome` and `graph_turn_reply` dominating. About 30 per-turn reply lookups in `substrate/world_adapter.py` scanned **every** agent outbound message of the session and kept those with `mid in responds_to(reply)`. Each lookup was O(session length) and ran many times per turn.

**Rules,** top costs at turns 126–150:

| Rule | Cost (ms/turn) | Pattern |
|---|---|---|
| `note_unanswered_turn` | 245 | Every unanswered message whose class already had a concern stays un-noted and re-ran two scans over all Messages on each re-match, before the cheap "class already held" check |
| `note_comprehension_latency_gap` | 190 | A scan over all Messages ("is this the latest shadow turn?") ran before the cheap checks (rolling average above ceiling, concern not filed) |
| `escalate_unparsed_clauses` | 81 | Matched every (reading goal, analysis stage) pair across the session; the flow equality was only in `where` |
| `reform_overcomplex_clause` | 34 | The same, over (SentenceParse, reading goal) |

## Fix

Each change preserves behaviour by construction: a narrower candidate set that the existing filter would accept, or a reordered pure conjunction. The parity run above confirms it end to end.

1. **`WorldAdapter.agent_outbound_replies_to(mid)`** reads `mid`'s own `responds_to` in-edges (same filter: from the agent, not suppressed, node-id order). All 30 call sites use it, and each keeps its own `responds_to` filter.
2. **`unanswered_gap` v1.1.0** (`scripts/gen_unanswered_gap.py`):
   - the "class already held" check moves before the scans;
   - both scans enumerate `NodesWhere(Message, turn_outcome, 'explicit_error')`;
   - `record_turn_outcome` declares that attribute index.
3. **`comprehension_health` v1.0.1:** the latency rule's all-Message scan moves last.
4. **`reading_aperture` v1.2.0:** both reading rules carry `index_hints` joining their candidates to the source's `flow`, using the engine's existing hinted matcher.

## Verification

- **Parity:** the 150-turn offline session is identical (`evaluation/substrate_capability/long_session_run_v1.py`, run in a HEAD worktree and in this tree).
  - The same-arm controls at 40 turns are identical online too.
  - An earlier online old-vs-new comparison differed on one turn whose reply came from an external topic search. With network I/O disabled in both arms, that difference disappeared.
- **Production 120-turn stream** (tranche-24 configuration, self-improvement on): the same 3 adoptions, including the chained one, and the same experiment outcomes.
  - Post-run error/none is 26 against tranche 24's 25. One more error/none reply in post-run retest; fresh-boot retest is 68 vs 66.
  - ReplyQuality: post-run mean 0.725 against 0.733, fresh boot 0.200 against 0.217.
  - Total elapsed time is **388 s against about 1,425 s.**
  - Compared reply by reply with the P0 run: 5 of 240 retest replies differ, all from network-dependent topic searches. Four got no reply in one run or the other. Three of those four came out empty in the new run, plausibly because the harness waits a fixed 15 cycles, not a fixed time, and faster cycles can finish before an external fetch does. I haven't verified this per turn (retest statuses aren't stored). The production daemon keeps ticking until the reply lands.
- **Tests:** `tests/test_long_session_cost_migrated.py` (4):
  - the helper equals the full scan on a real session;
  - the cheap-before-scan ordering;
  - the indexed source;
  - the hints.
- **Targeted regression:** 27 files (the replay, release, reading, health and self-improvement tests). 0 new failures against the baselines.
- **Envelope:** RSS 186.5 MiB (cap 200), ingress 19.7 ms, all assertions True.

## Remaining growth

At turn 150, rules still cost about 0.49 s per turn. The largest remaining costs are `escalate_unparsed_clauses` (its `SentenceParse` counts), `steer_promote_concern`/`steer_retire_concern` (messages × concerns bindings, already hinted on `from`), and `serve_next_detail_chunk`.

The general cause is that rules matching `agent received m` re-match over every received message. The engine-level fix is delta matching on new messages only. That is larger, and it is not done here.
