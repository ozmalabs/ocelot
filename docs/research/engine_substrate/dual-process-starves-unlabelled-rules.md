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
