# BIGVILLE R6 — SKILL, LEARNING-BY-DOING & TEACHING — PRE-REGISTRATION

**Block 254000. Pre-registered BEFORE any recorded number.** Spec:
`BIGVILLE_MOVEMENT_ECONOMY_SPEC.md` §2 (production requires SKILL; skill scales
yield; specialization = comparative advantage EARNED from the skill distribution),
§3 R6 (this gate). Builds ON R4 `bigville_econ_world` + its production seed
(`bigville_econ_production.json` — skill ALREADY scales yield there; this rung makes
it DYNAMIC), R5 `bigville_loop_world`, and REUSES: the capability-graph competence
(`ozma_capability_graph`), the dynamic-quantization learning loop (`sd_*` — learning
from experience), the grounding-from-a-teacher / `teach` facility (language
bootstrap), the **234 `stated≠held`** deception atom (coerced-teacher sabotage), and
the **247 power lever** (coercion). Reuse ALL by import; edit no tracked file.

R6 makes SKILL — the per-(agent, activity) competence R4 seeds statically — DYNAMIC:
learnable by doing, transferable by teaching, and the teaching a real DECISION that
can be refused, coerced, and sabotaged. Every decision stays a RULE; the adapter only
arms one-shots, wires edges, co-locates movers, ticks, and reads.

## Seed-claim (verbatim `check_claim`, run before anything)

```
SEED CLAIM 254000-254999: CLEAN -- no collision DETECTED.
  Scope: 973 files with seed sinks; 681 UNRESOLVED sink sites tree-wide (counted, not discarded).
  CAVEAT 1 -- THE UNIT IS THE SEED INTEGER, not consecutive draws from
    one generator. default_rng(S) burns an unbounded stream downstream of
    S; a rung seeding ONCE at its block base measures as ONE seed here.
  CAVEAT 2 -- THIS TOOL UNDER-REPORTS BY DESIGN (7 declared blind spots;
    unresolvable sinks are COUNTED, not discarded). A CLEAN RESULT MEANS
    'NO COLLISION DETECTED', NEVER 'NO COLLISION EXISTS'.
```

## What R6 adds (graph-native, ZERO new Rust)

Two additive seeds, composing only existing DSL Terms (Plus/Minus/Times/Max/Eq/Gt/
Gte/Lt/And/Not/Attr/Var/Lit + set_attr):

- **`seeds/bigville_skill_learn.json`** (1 rule) — LEARNING-BY-DOING.
  - **`bs_practice`** — a learner with `practice_armed=1` and a `Skill` node whose
    `activity` matches the practised activity nudges that skill's `level` UP with
    DIMINISHING RETURNS: `level' = level + learn_rate·(ceiling − level)` (geometric
    approach to the ceiling; each practice adds strictly less than the last). One-shot
    via `practice_armed`. The farmer who keeps fishing slowly improves; his fishing
    YIELD (R4 `be_produce` sums skill level) rises with it.

- **`seeds/bigville_skill_teach.json`** (4 rules) — TEACHING as the teacher's DECISION
  + coercion + sabotage. Four rules DISJOINT on `(willing, coerced)`, so exactly one
  fires per teach-armed step:
  - **`bs_teach_willing`** — a co-located MORE-skilled teacher (`learns_from` edge +
    shared `is_at` cell; `teacher.level > learner.level` — you can only teach what you
    know better) who is WILLING transfers at `teach_rate` (> solo `learn_rate`) →
    a FASTER diminishing-returns rise. WILLING is a `decision_value`
    (`teach_benevolence − rival_weight·learner.is_rival > 0` — the SAME Argmax family
    as `ss_choose_burn` / the R4 credit-trust call). Sincere: `stated_rate == held_rate`.
  - **`bs_teach_refuse`** — an unwilling teacher (the learner is a competitive threat,
    `is_rival=1` drives the decision_value ≤ 0) who is NOT coerced disarms with NO
    transfer. Willingness is a real decision — the fisherman protecting his trade.
  - **`bs_coerce`** — the **247 power lever**: a coercer whose `power` DOMINATES the
    teacher's (`coercer.power > teacher.power`) forces `coerced=1` past the refusal.
    Insufficient power → no coercion (lever load-bearing).
  - **`bs_teach_coerced`** — a coerced teacher DOES transfer but SABOTAGES — the **234
    `stated≠held`** atom applied to pedagogy: he PROFESSES `teach_rate` (`stated_rate`)
    but DELIVERS `sabotage_rate` (`held_rate`) `< teach_rate` → a DEGRADED transfer,
    the `stated_rate − held_rate > 0` gap readable off the graph.

Everything else reuses R4/R5/R1 by import. No `runners/dsl` change (target: EMPTY diff).

## Pre-registered gates (`tests/test_bigville_skill_migrated.py`)

### G-skill-scales-yield (HEADLINE)
Two keepers run a FISHING shop (input bait, `be_produce` yields ∝ fishing skill).
The farmer holds a LOW fishing skill, the fisherman a HIGH one.
- **Predict:** the farmer's fishing yield ≪ the fisherman's (yield rises with skill).
- **Ablation control (skill load-bearing):** equalize the two fishing skill levels →
  the two yields become EQUAL. (Skill DIFFERENTIAL is what drives the yield gap.)
- **Off-specialty control:** a keeper with NO fishing skill produces yield 0 (R4
  invariant, re-asserted — grounds specialization).

### G-learning-by-doing
The farmer practises fishing repeatedly (`practice()` each step).
- **Predict:** the fishing skill level (and therefore the yield) RISES over runs, with
  strictly DIMINISHING per-step gains (`gain[i] > gain[i+1]`; monotone increase; never
  drops).
- **Ablation control (learning load-bearing):** set `learn_rate = 0` → the skill is
  FLAT across the same practice sequence (no gain).

### G-teaching
Teacher = the skilled fisherman; learner = the farmer.
- **Faster-than-solo:** the taught curve DOMINATES the solo-practice curve at every
  step and ends strictly higher (`teach_rate > learn_rate`); a single willing teach
  gains more than a single solo practice.
- **Willing-refusal (willingness is a real decision, not always-yes):** with the
  learner a competitive threat (`is_rival=1`) and NO coercion, the fisherman REFUSES —
  `teach_outcome = refused`, NO skill transfer (level unchanged). With `is_rival=0` the
  same teacher teaches (the refusal is the rival case, not a global "never").
- **Coerced-degraded-vs-willing (247 + 234):** a powerful coercer (`power` ≫ teacher's)
  forces `coerced=1`; the coerced teacher THEN transfers but DEGRADED —
  `0 < coerced_gain < willing_gain`. The sabotage is readable as `stated≠held`
  (`stated_rate = teach_rate`, `held_rate = sabotage_rate`, `stated − held > 0`); a
  willing teach has `stated == held` (gap 0).
- **Lever load-bearing control:** a WEAK coercer (`power < teacher.power`) → `bs_coerce`
  does NOT fire → `coerced=0` → the teacher still REFUSES a rival (no transfer). Power
  is what forces the transfer.

### G-discipline (HARD — every item a checked artifact, not a claim)
- **NON-NESTED worktree** (`.claude/worktrees/agent-…`, never under
  `gamma-substrate/.worktrees/`).
- **NO Rust:** `git diff` over `runners/dsl` (incl. `term.rs`) is EMPTY. If a new
  primitive seemed needed I would STOP and report — none did.
- **Own engine:** `cargo build --release` in this worktree; `source_match ∈ {own,
  shared}` (INVARIANT — never a pinned `.so` md5). Canonical shared `.so` untouched
  (this worktree built + `--remove-destination`-copied its OWN `_native.abi3.so`).
- **Oracles:** `rung7_vision_bench.sh` + `per_area_settlement_regression.sh` — fail-set
  ⊆ enumerated `results/failure_baseline.json`; `test_failure_baseline_migrated` green;
  ZERO new reds. A PRE-EXISTING main provenance red (canonical stale vs a peer's Rust)
  is NOT mine; the enumerated baseline is the arbiter.
- **Additive only:** all-new files prefixed `bigville_skill_`; no existing tracked file
  edited (subclass/import R4/R5).
- **Source-audit:** no `if/else` over graph state selects an agent action — a test
  greps the adapter + seeds to confirm every learn/teach/coerce/sabotage decision is a
  RULE (`bs_*`), never Python.

## Pre-registered design risks (bind this prereg)

- **Sneaking a Python decision** (`if is_rival: refuse`). FORBIDDEN — it is a rule
  (`bs_teach_refuse`'s `where`). Source-audit gate.
- **Double-fire** (both a teach rule and `bs_practice` on one step). Prevented by
  DISJOINT arms (`practice_armed` vs `teach_armed`) + the four teach rules being
  mutually exclusive on `(willing, coerced)` — exactly one fires per armed step (the
  R4 one-shot-arm pattern).
- **Learning that never saturates** (a linear +k forever). The diminishing-returns law
  `rate·(ceiling − level)` is pre-registered; a strictly-decreasing gain sequence is
  the gate, and a learner cannot be taught past the teacher's own level
  (`teacher.level > learner.level` guard) — a real, checked plateau.
- **Sabotage indistinguishable from refusal.** No — refusal transfers NOTHING
  (`held=0`), coerced sabotage transfers a DEGRADED-but-positive amount
  (`0 < held < teach_rate`) while professing the full rate — the `stated≠held` gap is
  the discriminator, and it is a distinct `teach_outcome` code.

## Honest scope (pre-declared)
- Synthetic small-cast mechanism proof on the bigville grid — mechanism-proven ≠
  benchmark. Deterministic (no RNG).
- "Skill ablation" = equalizing the two keepers' skill LEVELS (the differential is what
  the gate isolates), since `be_produce` is R4's rule and is not edited.
- Coercion is modelled as a `power`-dominance test on a `coerces` edge (the 247 lever's
  essence); the full 247 office/enforcement machinery is R5's, reused conceptually, not
  re-wired here (honest scope).
