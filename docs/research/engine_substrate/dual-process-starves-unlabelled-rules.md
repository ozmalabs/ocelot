# Bug: the DualProcess plan never runs rules that have no `latency_class` or `area`

Found 2026-10-04 while scoping the Mary's Room stage 4 work. Reproduced in the
worktree (engine `b6a41e3bbba6`) and in the canonical tree. Not fixed here: the
fix changes default-boot semantics and needs its own preregistered change.

## Symptom

Under default `boot_core()`, `Substrate.tick()` returns 0 steps and every
`vision_lighting*` rule stays idle. Flags and match patterns are correct.
`s._inner.run_rules(N)` fires the same rules, and so does
`boot_core(seeds=())` + `tick()`.

- `tests/test_lighting_migrated.py`: 14 failed / 13 passed.
- `tests/test_border_ownership_migrated.py`: headline arms fail.
- `tests/test_lighting_l4_migrated.py`: 61 failed.

With `boot_core(seeds=())`, all 11 non-parametrised lighting tests pass, and the
spot-checked border-ownership and L4 arms pass. The results docs for these rungs
report the suites as passing, so this is a regression. History is a single import
commit, so it cannot be dated.

## Root cause

1. `seeds/dual_process_core.json:8-12` creates `DualProcessPolicy{enabled: 1}`. The
   seed is in `CORE_SEEDS` (`substrate/boot_core.py:18-25`). Other core seeds also
   pull it in transitively, so removing it from the list is not enough.
2. `tick()` (`runners/dsl/src/py.rs:4391`) runs
   `cognitive_cycle::execute(…, CyclePlan::Default, …)`.
3. `cognitive_cycle.rs:587-592`: `Default` becomes `DualProcess` whenever an
   enabled `DualProcessPolicy` exists (check at `:185-193`).
4. In `DualProcess`, System 1 runs only rules with
   `latency_class == hard_realtime` (`:692-698`, filter at `substrate.rs:4674-4678`).
   System 2 runs only when an escalation is requested, and only for rules whose
   `area` is in a requested string area (`:533`).
5. A missing `latency_class` or `area` parses to `Sym::default()`
   (`py.rs:9221-9231`). Such a rule matches neither branch, so it is starved, not
   deferred.

## Minimal reproduction

Tuples are (steps, #Illuminant). Scene: 3 surfaces with reference and test frames;
`lighting=1`.

| Boot | Call | Result |
|---|---|---|
| `boot_core()` | `tick` | (0, 0) |
| `boot_core()` | `run_rules` | (2, 1) |
| `boot_core()`, policy `enabled=0` | `tick` | (2, 1) |
| `boot_core(seeds=())` | `tick` | (2, 1) |
| `boot_core(seeds=('dual_process_core',))` | `tick` | (0, 0) |
| `boot_core(seeds=('affective_state_core',))` | `tick` | (2, 1) |

## Likely affected

About 20 test files use default `boot_core()` + `tick` with unlabelled seeds
(INFERRED from grep). This includes the lighting T3/L1/L2/L4, border ownership,
boundary trace, vision floor, vision growth and two-eyes suites.

## Fix options (smallest first)

| Option | Change | Implication |
|---|---|---|
| a | Callers use `run_rules` or a minimal boot | No engine change. Bypasses epoch advance and reflexes, and leaves the starvation in place for every other caller |
| b | Label the affected seeds' manifests `latency_class: hard_realtime` (inherited per `py.rs:1707-1711`) | Edits committed seed bytes, and says these rules belong to System 1 (defensible for early vision). Needs per-seed review |
| c | Disable the policy per experiment | Changes cognitive state; not a scheduling fix |
| d | Engine: the DualProcess plan also runs unlabelled rules, in System 1 or in leftover budget | Most general fix. Changes every default-boot tick, so it needs §9 byte-identity re-baselining and a prereg, and it alters System-1 budget arbitration |

Recommendation: (d), with a preregistration and re-baselined gates. Meanwhile
(b) for perception seeds that are clearly System 1. The Mary's Room study uses (a)
via an explicit boot and labels its own new seeds `hard_realtime`.

## Resolution (2026-10-06, branch `experiment/marys-room-eye-qualia`, uncommitted)

Choice: option (d). The engine's DualProcess plan now settles unlabelled rules.

### Evidence that starvation was not intended

- `cognitive_cycle.rs` module header: "Every legacy plan preserves its old phase
  order; new scheduling semantics are exposed only through explicit opt-in plans
  such as `dual_process`."
- `docs/research/engine_substrate/dual_process_core.md`: "agents without that policy
  retain unrestricted legacy settlement", and "Deferred rules keep their dirty bits.
  No residual is discarded". An unlabelled rule has no area, so no escalation can
  admit it. It was never deferred; it was discarded.
- `ASYNC_COGNITIVE_CORE_RESULTS.md`: "Legacy rules intern no defaults and export
  byte-identically". `py.rs::parse_rule_json` deliberately avoids moving a Sym for
  legacy rules. The design kept legacy rules unchanged.
- `CONVERSATIONAL_MANIFOLD_PROGRESS_TRACKER.md`, Phase 7, is the regression's
  origin. It "Changed the public PyO3 `tick()` boundary from the legacy
  `GraphThenStruct` plan to `CyclePlan::Default`". `GraphThenStruct` ran every
  struct rule. The same entry says "Full Gate 5 remains failed".
- `substrate/boot_core.py` says the core seeds' rules are what "`tick()` /
  `run_rules()` runs". However, 20 rules in `CORE_SEEDS` have no label
  (decision_core 1, learning_core 4, experimentation_core 1, goal_construction 4,
  self_monitoring 5, memory_core 3, reflex_core 2). Under default `tick()` they were
  starved as well.
- No test asserts the starvation. Every gating test in
  `test_cognitive_cycle_migrated.py` and `test_dual_process_core_migrated.py` uses
  rules labelled `latency_class: soft_realtime` with an `area`.
- Evidence for the other reading, considered and not followed:
  - `dual_process_core.md` step 1 says "Settle only rules authored as
    `latency_class: hard_realtime`".
  - `motor_stack_latency_tiers.md` says "Merely changing a latency label would
    leave the rule outside the default dual-process cycle".
  - `motor_core_whole_stack_architecture.md` says "Every rule manifest carries
    `latency_class` and `area`".

  All three describe labelled sheets. None of them mentions unlabelled legacy
  rules.

### Change (`runners/dsl/src/cognitive_cycle.rs`, the only source file changed)

| Lines (new) | What |
|---|---|
| 34-37 | `CyclePlan::DualProcess` doc comment states the new unlabelled semantics |
| 547-601 | `is_unlabelled_legacy_rule` (`latency_class == Sym::default() && area == Sym::default()`). `run_unlabelled_legacy` masks every other rule, runs `run_rules_opts` to fixpoint within the given budget, then restores the masks. It returns `None`, and makes no run_rules call, no counter reset and no trace event, when no unlabelled rule is active |
| 913-928 | DualProcess plan. After System 1, trajectory feedback and System 2 (with its hard motor fold), the unlabelled sheet runs on `max_steps - steps` and adds the trace phase `legacy_unlabelled_settle` |
| 1132-1256 | 4 Rust unit tests: unlabelled rules settle under Default with a policy; labelled soft rules stay gated, including rules with `latency_class` only or `area` only; the hard sheet keeps first claim at `max_steps=1` and the unlabelled rule runs on the next cycle; a fully labelled sheet emits no legacy phase |

The following are unchanged:

- System-2 gating for labelled soft and background rules.
- Rules with only a `latency_class` or only an `area`. These are still not opened.
- The no-policy path (`StructRulesOnly`).
- Every explicit plan.

A fully labelled sheet produces exactly the same output as before, because the new
pass is skipped.

New Python gate: `tests/test_dual_process_unlabelled_migrated.py`, 5/5. It covers
the minimal repro with `boot_core(seeds=('dual_process_core',))` and with the
default core, compares against `run_rules` and a policy-free boot, checks that the
soft probe stays gated, and checks the trace order.

Rust: `cargo test --lib cognitive_cycle::tests` passes 13/13 (9 existing and 4 new).
Linking needs `RUSTFLAGS="-L <libpython dir> -l python3.13"`.

### Engine

- Built with `scripts/engine_build.sh`.
- New engine `ed9237c97f20`
  (`ed9237c97f203c6738fc36c6ac705790eff82eaff373eb9bf6968734d324d436`). The previous
  engine was `b6a41e3bbba6`.
- `provenance_line()`:
  `engine ed9237c97f20 @ /tmp/ocelot-marys-room/runners/dsl/python/substrate_rs/_native.abi3.so  [1 other tree build(s) shadowed]`.
- `engine_preamble()` passes.
- `test_engine_provenance_migrated` is 9 passed, 1 skipped. Before the change it was
  10 passed. The skip is the uncommitted-Rust-source guard
  (`M runners/dsl/src/cognitive_cycle.rs`). It clears when the change is committed.

### Before and after (per file, pytest counts, same 31-file set)

| File | Before (`b6a41e3bbba6`) | After (`ed9237c97f20`) |
|---|---|---|
| test_lighting_migrated | 14 F / 13 P | 27 P |
| test_lighting_l1_migrated | 9 F / 9 P / 1 S | 18 P / 1 S |
| test_lighting_l2_migrated | 30 F / 16 P | 46 P |
| test_lighting_l4_migrated | 61 F / 11 P / 2 S | 72 P / 2 S |
| test_border_ownership_migrated | 4 F / 5 P | 9 P |
| test_border_ownership_nesting_migrated | 9 F / 4 P | 13 P |
| test_vision_boundary_trace_migrated | 35 F / 5 P / 2 S | 40 P / 2 S |
| test_aperture_frame_migrated | 8 F / 2 P | 10 P |
| test_observer_aperture_migrated | 9 F / 2 P | 11 P |
| test_crowding_migrated | 6 F / 2 P | 8 P |
| test_uniqueness_migrated | 10 F / 11 P | 21 P |
| test_theory_residual_concern_migrated | 4 F / 1 P | 5 P |
| test_stage_a_refusal_migrated | 7 F / 1 P | 2 F / 6 P |
| test_vision_floor_migrated | 1 S | 1 S |
| test_vision_growth_migrated | 1 P / 6 S | 1 P / 6 S |
| test_vision_two_eyes_migrated | 8 P | 8 P |
| test_dual_process_core_migrated | 1 F / 21 P | 1 F / 21 P |
| test_cognitive_cycle_migrated | 9 P | 9 P |
| test_doom_dual_process_integration_migrated | 10 P | 10 P |
| test_engine_provenance_migrated | 10 P | 9 P / 1 S (uncommitted-source guard) |
| test_acting_variant | 1 F / 11 P / 1 S | 1 F / 11 P / 1 S |
| test_adoption | 1 F / 19 P / 1 S | 1 F / 19 P / 1 S |
| test_experiment_composer | 9 P / 1 S | 9 P / 1 S |
| test_salient_cache | 1 F / 8 P | 1 F / 8 P |
| test_self_delta | 1 F / 4 P / 2 S | 1 F / 4 P / 2 S |
| test_retina_2d_cones_migrated | 15 P | 15 P |
| test_spectral_scene | 19 P | 19 P |
| test_perceived_surfaces_migrated | 14 P | 14 P |
| test_colour_property_episode_migrated | 9 P | 9 P |
| test_stage4_fixes_migrated | 26 P | 26 P |
| test_spectral_forward | 38 P | 38 P |

Totals: 211 failures before, 7 after. 204 tests flipped to passing. There are no new
failures; the failing test IDs after the change are a strict subset of those before.

The 7 remaining failures predate the change and are unrelated to it. Each fails with
the same assertion message before and after:

- `test_dual_process_core::test_unique_grounded_default_commits_without_system_two`:
  the expected trace omits `trajectory_quantized_feedback`.
- `test_acting_variant`, `test_adoption`, `test_self_delta`: the conclusion seed is
  not `saved`.
- `test_salient_cache::test_real_tale_lifts_hero_agency`: `3 > 3`.
- `test_stage_a_refusal` ×2. Their message changed from rules not firing to "fixture
  inert": Stage A `proposals == 0`. This also holds under `boot_core(seeds=())` +
  `tick` and under `run_rules`, which are paths this change does not alter. It is a
  separate Stage-A issue.

### Mary's Room results under `b6a41e3bbba6` are unaffected

Those studies drive the eye through its own substrate and `run_rules` paths, and
`domains/photon_eye.py` and the stage-4 seeds are untouched. This was re-verified on
`ed9237c97f20`:

- `test_retina_2d_cones_migrated` 15/15.
- `test_stage4_fixes_migrated` 26/26.
- `test_spectral_forward` 38/38.
- The pilot smoke run directly: `GraphEye(n_az=2)` with 610/530 nm at 1000 quanta
  gives `[(0.3436120168296669, -0.3456013062040921), (-0.07537232767138446, -0.6214367610772381)]`,
  exactly equal.

### Open

- No preregistration was written, and no full-suite §9 re-baseline was done. Only
  the 31-file set above was run.
- Every default-boot `tick()` now also settles the 20 unlabelled core-seed rules.
  Results recorded under the starving engine with default boot plus `tick` may move.
- Unlabelled rules run after System 1 in leftover budget. A hard rule that reads
  their writes sees them on the next cycle, not the same one. If a continuous hard
  sheet consumes the whole budget every cycle, unlabelled rules wait. They are not
  lost.
- Rules carrying only one of `latency_class` or `area` remain unscheduled unless
  System 1 or System 2 claims them. This is unchanged and deliberate here.
