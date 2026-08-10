# VISION — CODEC FIELD-GRAMMAR RULES ACTIVATED: `install_field_grammar_rules` now routes through `add_rule` (RESULTS)

Rung / seed block: **121000–121999** (NO seeds drawn — a Rust bug fix, no new Term, no
generator seeded). Branch `worktree-agent-aa92bce093ed13c81`, worktree HEAD before work
`c5bf3358`.

## HEADLINE

The dead-install bug is FIXED and it does exactly what the baseline rung proved it would —
**but only for the paths that were actually wired.** Routing `codec.rs:56` through
`Substrate::add_rule` moved **23 of the 30** codec nodes red→green (H.264 PPS decode+qp,
JPEG DQT, HEVC PPS qp, all conditional / nested / OR / mixed-DNF, all loop-by-name, and the
encode round-trips). **8 nodes remain red for a SECOND, DISTINCT cause the dead install had
masked — an incomplete HEVC / fixed-arity-array grammar.** This is the "second finding" the
brief pre-authorised, and it is a direct confirmation of `VISION_BASELINE_LIST_RESULTS.md`
§1.5, which ESTABLISHED only the H.264 PPS path and listed HEVC / loop as "listed, not
assumed."

**The oracle did not move: 222/0 before AND after (the load-bearing check).** The fix is
safe for the seed-booted agent and vision, because the ONLY caller of
`install_field_grammar_rules` in the whole tree is `tests/test_codec_graph_resident.py`.

## THE FIX

`runners/dsl/src/codec.rs:56`: `substrate.rules.push(rule);` → `substrate.add_rule(rule);`
(+ a comment). The bypass skipped not just `active = true` but the cost-based match-edge
reorder, index-hint provisioning, `derive_access`, the nine parallel bookkeeping vectors,
and the `gamma_epoch` bump. Routing through `add_rule` restores all of them. One-line
behavioural change; Rust diff is 8+/1- in one file; no `term.rs` / `rewrite.rs` touched, so
no Term variant added (`variant_table_covers_the_enum` guarantee holds statically;
indices 175–180 unmoved).

## PROVENANCE

| | value |
|---|---|
| engine BEFORE fix (own build) | `7041d2e6a7dd` |
| engine AFTER fix (own build) | `5742330bf8f1` |
| post-measurement re-verify | `5742330bf8f1` (unchanged; `test_engine_provenance_migrated` 7 passed) |
| `data/` | symlinked to canonical (read-only) → oracle runs at 222 |

## NUMBERS (measured, engine `5742330bf8f1`, `data/` symlinked)

| check | BEFORE | AFTER | verdict |
|---|---|---|---|
| **ORACLE `rung7_vision_bench.sh`** | **222 passed / 0 failed** (215.7s) | **222 passed / 0 failed** (219.5s) | **UNCHANGED — load-bearing check HOLDS** |
| `test_codec_graph_resident` (32 collected) | 30 failed / 2 passed | **8 failed / 24 passed** | 23 red→green; 8 remain (second cause) |
| `test_failure_baseline_migrated` | 11 passed | 11 passed | green (list shrunk & re-read) |
| rule-engine/seed spot-check (6 files) | — | **52 passed / 0 failed** | no blast-radius elsewhere |

check_claim 121000–121999 (§3 clause 8, VERBATIM in `VISION_CODEC_ACTIVATE_PREREG.md`):
CLEAN, 513 unresolved sinks tree-wide (advisory); this block draws none.
loadavg: oracle-before start (1.32, 0.78, 0.73); oracle-after start (2.86, 2.57, 1.64);
final (2.14, 2.84, 2.21). Concurrent rungs present — **no wall-clock verdict drawn.**

## THE SECOND FINDING — 8 nodes remain red, and one was a VACUOUS pass

7 of the 8 were in the original 30 baseline. The 8th,
`test_hevc_sps_scaling_list_bump_via_ffmpeg`, **PASSED before and FAILS after** — it was one
of the two before-passers, and it was a VACUOUS pass: with the rules DEAD the HEVC encode was
a no-op (`enc_buf` stayed `b""`), which the test's downstream splice tolerated. Activating the
rules runs the incomplete scaling-list encode, which writes `None` → `TypeError` at test line
3678. Replacing a fake green with an honest red is a strict improvement.

The 8 remaining reds (class `HEVC_GRAMMAR_INCOMPLETE_SECOND_CAUSE` in the baseline list):

- `test_loop_fixed_count_literal` — the literal-count loop (`loop_init_literal`, which the
  docstring says "models HEVC's fixed-arity arrays") **DOUBLE-emits** each iteration
  (`[(0,1),(0,1),(1,0),(1,0),…]` vs expected `[(0,1),(1,0),(2,1),(3,1)]`): two rules match one
  iteration.
- `test_hevc_sps_prefix_full_grammar`, `test_hevc_sps_conformance_window_bump_via_ffmpeg`,
  `test_hevc_sps_extended_fields_decode`, `test_hevc_pps_tile_array_bump_via_ffmpeg`,
  `test_hevc_scaling_list_data_round_trip`, `test_hevc_scaling_list_custom_matrix_branch`,
  `test_hevc_sps_scaling_list_bump_via_ffmpeg` — HEVC SPS/PPS/scaling-list fields not
  decoded / encode writes None.

These are NOT the dead install (the dead install is fixed). They are a genuinely incomplete
HEVC grammar. **Not fixed here** — a different codec, substantial, and not provably safe in a
gate-fix rung. Named and re-classified, left in the baseline for a future rung.

## THE OTHER `.rules.push(` GREP (brief step 4)

Three hits tree-wide, only one was the bug:

| site | verdict |
|---|---|
| `runners/dsl/src/codec.rs:56` | **THE BUG — fixed** |
| `runners/dsl/src/substrate.rs:1344` | INSIDE `add_rule` — the legitimate sole path. Correct. |
| `runners/dsl/src/graph_rules.rs:447` | a LOCAL `Vec<RewriteRule>` for a one-shot run, NOT `substrate.rules`. Unrelated. |

No further bypass to fix.

## THE BASELINE SHRINK (brief step 5)

`results/failure_baseline.json`: 23 fixed nodes DELETED; 7 kept + 1 new (the regressor)
re-classified `REAL_REGRESSION_ROOT_CAUSED` → `HEVC_GRAMMAR_INCOMPLETE_SECOND_CAUSE` with a
per-entry `diagnosis`. `total` 565 → **543** (derived from `len(entries)`). Only the codec
subset was re-measured (engine `5742330bf8f1`, `data/` symlinked); the other 535 entries
retain the original sweep's engine/condition, unchanged by a Rust fix no other test installs
(recorded in the file's `codec_fix_2026_07_21` block). `test_failure_baseline_migrated`
stays green (11 passed); its `test_the_known_never_green…` assertion still passes because 8
codec entries remain — I updated only its docstring for accuracy.

## WHAT I GOT WRONG (brief: report what you got wrong)

1. **Prereg prediction 1 (0.9): "all 30 codec nodes go green."** WRONG — 23 green, 8 remain.
   This is precisely the second finding the brief anticipated; the baseline rung's §1.5 hedge
   ("HEVC listed, not assumed") was right and my 0.9 over-trusted the "share the cause by
   construction" claim.
2. **Prereg prediction 5: "`test_the_known_never_green…` goes RED and must be updated."**
   WRONG in mechanism — it stays GREEN (its assertion is "codec non-empty", and 8 codec
   entries remain). I updated only the docstring, not the assertion.
3. **Did not predict the green→red regression** within the codec test
   (`test_hevc_sps_scaling_list_bump_via_ffmpeg`, a vacuous pass exposed). Found by the
   before/after node-set diff, not foreseen.
4. **Transient miscount:** first AFTER reading was "8 failed / 31 passed = 39" — I had run
   the codec test together with `test_engine_provenance_migrated` (7 tests). Re-ran codec
   alone (32 collected → 8 failed / 24 passed) and reconciled before recording.
5. **`cargo test` could not run** the Rust unit tests (`variant_table_covers_the_enum`,
   `add_rule` tests): the pyo3 extension test harness fails to LINK (`undefined symbol:
   PyExc_BaseException` …) — a pre-existing environmental condition, not caused by the
   one-line change (the engine `cargo build --release` itself succeeded). Substituted the
   static enum-untouched check + the Python oracle/spot-check as the blast-radius instrument.

## LEDGER ROW (for the supervisor to place; NOT edited into VISION_PROTOCOL.md by this rung)

**121000–121999 (unknown_sinks 513 tree-wide advisory; NONE drawn in-block; no seed, one
Rust line).** **THE NEVER-GREEN CODEC GATE WAS RIGHT — AND SO WAS ITS §1.5 HEDGE.** Routed
`codec.rs::install_field_grammar_rules` through `Substrate::add_rule` (the bypass left all 20
field-grammar rules `active:false` AND skipped the reorder / bookkeeping / gamma-epoch).
`test_codec_graph_resident` **30 red → 8 red** (23 genuinely-working nodes go green: H.264 PPS,
JPEG, conditional/nested/OR/DNF, loop-by-name, encode round-trips). **The 8 residual reds are a
SECOND cause, not the dead install — an incomplete HEVC / fixed-arity-array grammar** (literal
loop double-emits; HEVC SPS/PPS/scaling-list write None), and one of them
(`…scaling_list_bump_via_ffmpeg`) was a **VACUOUS pass** that only "passed" because the dead
rules made its encode a no-op — an honest red now replaces a fake green. **ORACLE 222/0 before
AND after (load-bearing);** the fix touches only `install_field_grammar_rules`, whose sole
caller is the codec test, so nothing else can move — empirically confirmed (rule-engine spot-
check 52/0; provenance 7/7). Only bypass tree-wide was this one (`substrate.rs:1344` is
`add_rule` itself; `graph_rules.rs:447` is a local Vec). `failure_baseline.json` **565 → 543**
(23 fixed deleted, 8 reclassified `HEVC_GRAMMAR_INCOMPLETE_SECOND_CAUSE`). Engines
`7041d2e6a7dd`→`5742330bf8f1` (own; re-verified unchanged post-measurement). No Term variant.
loadavg peaked ~2.9. **PREREG MISS: predicted all 30 green; 23 did — the 8 HEVC residuals
vindicate §1.5.**
