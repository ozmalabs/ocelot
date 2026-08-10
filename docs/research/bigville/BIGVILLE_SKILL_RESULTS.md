# BIGVILLE R6 — SKILL, LEARNING-BY-DOING & TEACHING — RESULTS

**Block 254000.** Prereg: `BIGVILLE_SKILL_PREREG.md` (committed before any number,
`d84b05b9b4`). Build: `seeds/bigville_skill_learn.json`,
`seeds/bigville_skill_teach.json`, `worlds/bigville_skill_world.py`,
`scripts/bigville_skill_gen_seeds.py` (seed builder),
`scripts/bigville_skill_run.py`, `tests/test_bigville_skill_migrated.py`. Everything
else (R4 economy + its production seed, R1 movement, R3 clock) reused BY IMPORT — no
tracked file edited. **ZERO new Rust** (`runners/dsl` diff EMPTY).

R6 makes SKILL — the per-(agent, activity) competence R4 seeds statically — DYNAMIC.
Every number below is read straight off the graph (`results/bigville_skill/summary.json`).
Deterministic; no RNG.

---

## G-skill-scales-yield (HEADLINE) — PASS

Two keepers run a FISHING shop (bait → fish via R4 `be_produce`, which mints output ∝
the keeper's fishing skill). Yields read straight off the stock delta of one produce
step:

| keeper | fishing skill | fish yield |
|---|---|---|
| farmer | 1 | **1.0** |
| fisherman | 5 | **5.0** |
| **gap** | | **4.0** |

**Skill scales yield.** Controls:
- **Ablate skill (skill load-bearing):** equalize the two skill levels (both = 3) → the
  two yields become **EQUAL (3.0 == 3.0)**. The skill DIFFERENTIAL is what drives the
  gap.
- **Off-specialty:** the farmer with NO fishing skill node produces **0.0** — off-
  specialty yields nothing (grounds specialization / comparative advantage; the R4
  invariant re-asserted).

## G-learning-by-doing — PASS

The farmer practises fishing (`bs_practice`, `learn_rate = 0.3`, ceiling 8, law
`level' = level + rate·(ceiling − level)`):

```
skill : 1.0 → 3.1 → 4.57 → 5.599 → 6.319 → 6.824 → 7.176
gains :   2.10   1.47   1.029   0.720   0.504   0.353    (strictly diminishing)
```

Skill (and therefore yield) **RISES over runs with strictly DIMINISHING per-step
gains** — the substrate's own experience-learning law pointed at a trade.

- **Ablate learning (learning load-bearing):** `learn_rate = 0` → the curve is **FLAT**
  (`1.0 → 1.0 → … → 1.0`) across the same six practice steps. Learning is load-bearing.

## G-teaching — PASS (all four sub-claims)

Teacher = the master fisherman (fishing 8); learner = the farmer (fishing 1,
`learn_rate 0.3`). Teacher seed: `teach_benevolence 2`, `rival_weight 5`, `teach_rate
0.5`, `sabotage_rate 0.12`, `power 1`.

**Faster than solo.** A willing teacher transfers at `teach_rate 0.5 > learn_rate 0.3`:

```
solo   : 1.0 → 3.1  → 4.57 → 5.599 → 6.319 → 6.824 → 7.176
taught : 1.0 → 4.5  → 6.25 → 7.125 → 7.562 → 7.781 → 7.891   (dominates solo at EVERY step)
```

A single willing teach gains **3.5** vs a single solo practice **2.1**. The taught curve
DOMINATES solo at every step and ends strictly higher.

**Willing-refusal (willingness is a real decision, not always-yes).** With the learner a
COMPETITIVE THREAT (`is_rival = 1`, so the decision_value `benevolence −
rival_weight·is_rival = 2 − 5 = −3 ≤ 0`) and NO coercion, the fisherman **REFUSES**:

```
rival, uncoerced : 1.0 → 1.0 → … → 1.0   (outcome = refused; NO transfer)
```

The fisherman protects his trade against a farmer who would break his fish-supply
monopoly. (With `is_rival = 0` the SAME teacher teaches — the refusal is the rival case,
not a global "never".)

**Coerced-degraded-vs-willing (247 power lever + 234 `stated≠held`).** A powerful John
(`power 9 > teacher.power 1`) forces the coercion (`bs_coerce` → `coerced = 1`); the
coerced teacher THEN transfers but SABOTAGES — delivers `sabotage_rate 0.12` while
PROFESSING `teach_rate 0.5`:

```
coerced : 1.0 → 1.84 → 2.58 → 3.23 → 3.80 → 4.31 → 4.75   (outcome = coerced; sabotaged = 1)
single coerced gain 0.84  <  single willing gain 3.5       (DEGRADED, but > 0: transfers)
stated_rate 0.50 ,  held_rate 0.12 ,  stated − held = 0.38 > 0   (234 stated≠held, readable)
```

The coerced lesson **transfers but is DEGRADED** vs a willing one, and the sabotage is
readable off the graph as the `stated − held` gap — the 234 deception atom applied to
pedagogy.

- **Lever load-bearing control:** a WEAK coercer (`power 0.5 < teacher.power 1`) →
  `bs_coerce` does NOT fire → `coerced = 0` → the teacher still **REFUSES** the rival
  (curve flat, no transfer). Power is what forces the transfer.

### The four teaching outcomes, disjoint on (willing, coerced) — glass-box
| scenario | willing | coerced | rule fired | transfer | stated−held |
|---|---|---|---|---|---|
| non-rival | yes | no | `bs_teach_willing` | teach_rate (fast) | 0 (sincere) |
| rival | no | no | `bs_teach_refuse` | none | 0 |
| rival + strong coercer | no | yes | `bs_coerce`→`bs_teach_coerced` | sabotage_rate (degraded) | 0.38 (sabotage) |
| rival + weak coercer | no | no | (coerce declines) → `bs_teach_refuse` | none | 0 |

Exactly one teach rule fires per armed step; the coercion is a separate one-shot arm.

## Payoff (the spec's R6 payoff, demonstrated)

The town's economic structure is now **CONTESTABLE and dynamic**: a farmer can LEARN to
fish and break the fisherman's supply monopoly — slowly by solo practice, fast if the
fisherman is WILLING, and, when the fisherman refuses to train a rival, only if a
powerful John COERCES him — and even then the lesson is sabotaged. **Knowledge is power:
hoarded (refuse) or extracted (coerced, degraded).** Specialization is EARNED from a
LEARNABLE skill distribution, not fixed. This is also the **labour-reallocation**
mechanism R5's shortfall lacked: a farmer can learn a needed trade.

---

## G-discipline — the ledger

| item | status |
|---|---|
| base SHA | `746d2fb5cbc4bc3919f6e64c4f97be42a18800c5` (merge-base verified == HEAD at start) |
| prereg SHA (separate commit, before any number) | `d84b05b9b4` |
| seed claim | `254000-254999` CLEAN (verbatim `check_claim` in the prereg) |
| own engine md5 | `10f65be659e0d9a9290aff39f7f5b92a` — `source_match == own` (built in THIS worktree; `test_engine_provenance_migrated` 7/7) |
| `runners/dsl` diff | **EMPTY** (no Rust; `git status --porcelain runners/dsl` empty; `term.rs` untouched) |
| canonical shared `.so` | **NOT touched** (this worktree built + `--remove-destination`-copied its OWN `_native.abi3.so`; canonical is a peer's build, md5 `fd82dc29…` — the pre-existing main provenance red, NOT mine) |
| new files (additive only) | `seeds/bigville_skill_learn.json`, `seeds/bigville_skill_teach.json`, `worlds/bigville_skill_world.py`, `scripts/bigville_skill_gen_seeds.py`, `scripts/bigville_skill_run.py`, `tests/test_bigville_skill_migrated.py`, `BIGVILLE_SKILL_PREREG.md`, this file, `results/bigville_skill/` — no existing tracked file edited (subclass/import only) |
| gate tests | `tests/test_bigville_skill_migrated.py` — **12/12 PASS** |
| failure baseline | `test_failure_baseline_migrated` — **11/11 PASS** |
| rung7 vision bench | **214 passed, 10 skipped, 0 failed** (green, 3m19s) |
| per-area settlement | **278 passed, 5 skipped, 23 failed** — all **23 failing node-ids ∈ enumerated `results/failure_baseline.json`** (verified set-wise; 5 pre-existing red files: `test_cortices_tick`, `test_composer_driver_migrated`, `test_gap_awareness_migrated`, `test_elaboration_migrated`, `test_topic_route_selfheal_migrated`) — unrelated to this rung |
| new reds | **0** (both oracle fail-sets ⊆ enumerated baseline, 543 entries; my per-area fail-set is a strict subset) |
| worktree | non-nested (`.claude/worktrees/agent-…`); no worktree under `gamma-substrate/.worktrees/` |
| source-audit | no `if/else` over graph state selects a learn/teach/coerce/sabotage outcome — the five decisions are RULES (`bs_*`); the adapter arms one-shots, wires edges, co-locates, ticks, reads (gated by `test_no_python_agent_decision_source_audit`) |

## Honest scope / residuals

- Synthetic small-cast mechanism proof on the bigville grid — mechanism-proven ≠
  benchmark. Deterministic; no RNG.
- **"Skill ablation" = equalizing the two keepers' skill LEVELS** (the differential is
  what the gate isolates), because `be_produce` is R4's rule and is not edited.
- **The mediocre-teacher plateau (an honest emergent property, not a bug).** A learner
  cannot be taught past the teacher's own level (`teacher.level > learner.level` guard).
  With a MEDIOCRE teacher (fishing 7 < ceiling 8) the taught curve plateaus at 7.125 and
  unbounded SOLO practice eventually OVERTAKES it (solo reaches 7.176 by step 6) — "you
  can't be taught past your teacher, but unbounded practice eventually surpasses a
  mediocre one." The headline uses a MASTER teacher (level 8 = ceiling) so the willing-
  teaching gate cleanly dominates; the mediocre case is reported here as a real,
  measured property.
- Coercion is modelled as a `power`-dominance test on a `coerces` edge (the 247 lever's
  essence); the full 247 office/enforcement machinery is R5's, reused conceptually, not
  re-wired here.
- `sabotage_rate` and `teach_rate` are per-teacher seeds (population axis, like `w_spite`
  / charm); a resentment-conditioned sabotage decision (sabotage only when the teacher
  RESENTS the coercion) is a natural extension left for a later rung — here every coerced
  teacher sabotages.
