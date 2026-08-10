# VISION — CODEC FIELD-GRAMMAR RULES: ROUTE `install_field_grammar_rules` THROUGH `add_rule` (PRE-REGISTRATION)

Seed block: **121000–121999**. Predicted draws: **NONE** (this is a Rust bug fix — no
new Term, no new seed, no generator seeded).

## §3 clause 8 — check_claim VERBATIM (before any number)

```
$ python scripts/seed_claim.py 121000 121999
SEED CLAIM 121000-121999: CLEAN -- no collision DETECTED.
  Scope: 825 files with seed sinks; 513 UNRESOLVED sink sites tree-wide (counted, not discarded).
  CAVEAT 1 -- THE UNIT IS THE SEED INTEGER, not consecutive draws from
    one generator. default_rng(S) burns an unbounded stream downstream of
    S; a rung seeding ONCE at its block base measures as ONE seed here.
  CAVEAT 2 -- THIS TOOL UNDER-REPORTS BY DESIGN (7 declared blind spots;
    unresolvable sinks are COUNTED, not discarded). A CLEAN RESULT MEANS
    'NO COLLISION DETECTED', NEVER 'NO COLLISION EXISTS'.
```

unknown_sinks: 513 tree-wide (advisory). My block draws none.

## Engine (before), provenance

`engine 7041d2e6a7dd @ .../agent-aa92bce093ed13c81/.../python/substrate_rs/_native.abi3.so` —
own build of this worktree.

## The bug (already diagnosed by the baseline rung, §1)

`runners/dsl/src/codec.rs:56` in `install_field_grammar_rules` does
`substrate.rules.push(rule)`, bypassing `Substrate::add_rule` (`substrate.rs:1262`) — the
"sole path that pushes into `self.rules`". The bypass skips, in full: `rule.active = true`;
the cost-based `reorder_match_edges_with_hints`; `declare_attr_index` for index hints;
`derive_access`; and the NINE parallel bookkeeping vectors (`rule_edge_type_deps`,
`rule_has_where`, `rule_dirty`, `rule_cost_micros`, `rule_cost_count`,
`rule_cost_progress`, `rule_cursors`, `rule_where_jit`) plus `gamma_epoch.bump()`. The
observed symptom is `active:false` → matcher skips all 20 → 0 firings.

## The fix

Change `codec.rs:56` from `substrate.rules.push(rule);` to `substrate.add_rule(rule);`. This
restores active=true AND every other invariant `add_rule` owns. No change to `add_rule`
itself, `run_rules`, or any Term. Rust bug fix, additive-in-spirit: no new variant (index
175–180 unmoved; `variant_table_covers_the_enum` predicted GREEN).

## PREDICTIONS (falsifiable, pre-registered)

1. **`test_codec_graph_resident`: 30 FAILED / 2 passed → 32 passed / 0 failed.** All 30 red
   nodes go green. Confidence 0.9. If any of the 30 does NOT go green, that is a SECOND
   finding (a node red for a reason OTHER than the dead install) — reported, NOT a reason to
   touch the test.

2. **Oracle (`scripts/rung7_vision_bench.sh`, with `data/` symlink): 222/0 → 222/0,
   UNCHANGED.** THE LOAD-BEARING CHECK. Confidence 0.98. Mechanism for the confidence: the
   ONLY caller of `install_field_grammar_rules` in the whole tree is
   `tests/test_codec_graph_resident.py` (grep: `failure_baseline.py` only quotes the name in
   a diagnosis string). The 20 rules are NEVER installed into the seed-booted agent, any
   seed, or any other test's substrate — so activating them cannot change behaviour outside
   the codec test BY CONSTRUCTION. If the oracle MOVES, the rules were inactive-but-load-
   bearing-by-absence via some path I did not find → STOP, report, do not force.

3. **Blast radius elsewhere: NOTHING else changes.** No other landed number moves. Spot-
   check: the broader rule-engine/seed-adjacent migrated tests and the Rust unit tests
   (`cargo test` in `runners/dsl`, incl. the `add_rule` tests and
   `variant_table_covers_the_enum`) stay green. Confidence 0.95 (same only-one-caller
   argument).

4. **Other `.rules.push(` bypasses: exactly ONE existed (the bug).** Already grepped:
   `codec.rs:56` (the bug), `substrate.rs:1344` (INSIDE `add_rule` — the legitimate sole
   path), `graph_rules.rs:447` (a LOCAL `Vec<RewriteRule>` for a one-shot run, not
   `substrate.rules` — unrelated). Prediction: no further bypass to fix. Confidence 0.97.

5. **`results/failure_baseline.json`: 30 codec entries removed, `total` 565 → 535.** The 30
   nodes filed under `tests/test_codec_graph_resident.py` (class
   `REAL_REGRESSION_ROOT_CAUSED`) — verified to be EXACTLY the 30 currently-failing nodes —
   are deleted with a recorded reason (a real fix, not a silenced red). Consequently
   `test_failure_baseline_migrated::test_the_known_never_green_entries_are_recorded_as_such`
   (which ASSERTS codec IS present) will, BY ITS OWN DOCSTRING, go red on the fix and demand
   "UPDATE THE LIST and this doc" — I update that one assertion to record the fix (codec now
   ABSENT because fixed-and-green), keeping the file's discipline (a regression would return
   the reds NOT in the baseline → a NEW-red). Confidence 0.9.

## BEFORE numbers (measured, this engine, this tree)

- codec test: **30 failed / 2 passed** (measured).
- oracle: **222 passed / 0 failed** (measured, data/ symlinked, 215.7s).
- check_claim: CLEAN (above).
- loadavg at oracle-before start: (1.32, 0.78, 0.73). Concurrent rungs present; NO
  wall-clock verdict is drawn.

## Discipline

Own engine rebuilt after the fix; provenance re-verified; fingerprint recorded before
(7041d2e6a7dd) and after. CPU ≤2 workers; loadavg recorded each step. Ledger row goes in the
RESULTS doc, NOT VISION_PROTOCOL.md.
