# Per-resident Causal Attitude Networks for Bigville — RESULTS

Prereg: `BIGVILLE_CAN_INTEGRATION_PREREG.md`, same worktree/branch, base
`main @ d061b2d`. Worktree
`/home/matt/ozmadev/ocelot-worktrees/bigville-can-integration`, branch
`bigville-can-integration`.

**Verdict, up front:** both registered predictions confirmed, on the real
live two-resident demonstration and on a population-wide supplementary
check. The manipulation check (§2, prediction 1) is clean and large: the
coarse resident's mean rounding error is **~9.2× the fine resident's**
(0.553 vs 0.060). The primary prediction (§2, prediction 2 — deliberately
NOT the naive "coarse → fewer basins" intuition, since that was already
falsified on this same engine by `CAN_BELIEF_QUANTIZATION_RESULTS.md`) is
also confirmed and large: the coarse resident's network relaxes to a
**positive-energy, highly frustrated** basin (frustration 9.86, energy
+5.19) while the fine resident's relaxes to a **negative-energy, low-
frustration** basin (frustration 1.62, energy −1.77) — under the IDENTICAL
scenario evidence. A population-wide supplementary check across all 100
residents (§5, not pre-registered with the same rigor as the two-resident
demo — reported as exploratory) shows the same direction holds on average
(low-bins group mean frustration 3.29 vs. high-bins group 1.38) and a
control that holds resolution FIXED across the population collapses the
trait↔frustration correlation from −0.33 to −0.08, confirming resolution —
not some other resident trait correlated with it — is what is driving the
effect.

---

## 1. What was built

1. **`worlds/bigville_town100_world.py`** — 54 lines added
   (`_draw_resolution_bins`, its 4 grounding constants, and one insertion
   point in `generate_cast100`). A 13th `params` field,
   `resolution_bins` (integer, `[2,12]`), drawn from a two-component
   Normal mixture in continuous space (floor `Normal(3.0,1.0)`, ceiling
   `Normal(7.5,2.0)`, `P(ceiling)=0.35`), rounded and clamped to the
   integer lattice per the frame/continuum invariant. Drawn from its OWN
   RNG stream (`rrng = np.random.default_rng(seed + 13)`, mirroring the
   file's own existing `nrng` isolation pattern for names) — **confirmed
   by direct diff, not assumed**: regenerating the seed changes ONLY the
   100 new `resolution_bins` values; every one of the 12 pre-existing
   `_PARAM_SPEC` values, for every one of the 100 residents, plus
   `role_identity`/`class`/`literacy`, is byte-identical to the
   pre-rung committed file (`git diff --stat`:
   `seeds/bigville_cast100.json | 100 +++...`, 100 insertions, 0
   deletions — one new line per resident, nothing else touched).
2. **`seeds/bigville_can_beliefs.json`** — declares the 3 Γ admissibility-
   grammar productions a personal belief network needs
   (`Resident -has_belief_mt-> Microtheory`, `Microtheory -has_concept->
   Concept`, `Concept -causal_influence-> Concept`) plus documentation
   (`concepts` entries, house style) naming the 5-topic template and its
   grounding. `self_load_only: true`, `depends_on:
   ["causal_attitude_networks"]` — same category as
   `bigville_cast100.json`/`causal_attitude_networks.json` themselves, not
   swept into a full `load_all_seeds` boot.
3. **`worlds/bigville_can_beliefs.py`** — the builder. Pure mechanical
   translation (no rule engine, no agent decision — verified by the same
   forbidden-substring grep `test_cast100_migrated.py` already runs on
   `bigville_town100_world.py`, now also run on this file, §6). Exposes:
   `effective_resolution_bins`, `quantize_j`, `true_edge_j`,
   `install_productions`, `build_resident_can_mt`, `apply_scenario_evidence`.
4. **`scripts/bigville_can_integration_demo.py`** — the live demonstration
   runner: picks the real lowest/highest-`resolution_bins` residents from
   the committed `bigville_cast100.json`, builds both networks, applies
   identical scenario evidence, relaxes + audits with the real `can_ops`
   PyO3 surface, runs a 20-restart multi-start basin sweep.
5. **`tests/test_bigville_can_integration.py`** — 12 new tests (§6).

No new Rust. No new `can_ops.rs` function. The existing PyO3 surface
(`mt_relax_to_marginal`, `mt_audit_basin`, `mt_mean_field_marginal`,
`mt_frustration_given_state`, `mt_energy`, `concept_apply_evidence`,
`set_attr`, `add_node`, `add_edge`, `add_production`) was sufficient, as
predicted in the PREREG before any code was written.

## 2. Scoping decision (confirmed against the real code, PREREG §1.3-2)

`can_ops.rs`'s `mt_id: NodeID` parameter is used only via
`g.neighbours(mt_id, has_concept_edge)` and one `temperature` attr read
(`can_ops.rs:142-144,207`) — it needs to be ANY node owning `has_concept`
edges, not a distinct type. But σ/h/identity live as attrs **on the Concept
node itself** (`can_ops.rs:33-48`), so genuine per-resident independence
requires **distinct Concept nodes per resident** — confirmed live by
`test_two_residents_get_genuinely_distinct_concept_nodes`. Each resident
therefore gets: one personal `Microtheory` (β=1.5, held fixed across both
demo residents to isolate resolution as the manipulated variable), 5
distinct `Concept` nodes using a shared 5-name TEMPLATE
(`trust_mayor`, `claim_credible`, `world_safe`, `self_worth`,
`debtor_trustworthy`), 5 `causal_influence` edges (a sparse structural
template, not a complete graph). All 5 topics and all 5 structural
relationships are grounded in already-wired Bigville mechanics
(`bd_villager_backs`'s `cred_john`/`cred_mary` formulas,
`bl_townsfolk_opinion`'s standing/badmouth arithmetic, the Bowlby IWM
prior correlation) — no invented topics; `market_fair`/`watch_effective`/
`guild_loyalty` were checked and found genuinely unwired, and excluded.

## 3. The mixture design — grounding recap

| component | mean | sd | grounding |
|---|---|---|---|
| floor (naive/general) | 3.0 | 1.0 | CRT floor regime + CAN's own already-tested "coarse" (3 J values), `CAUSAL_GRANULARITY_POPULATION_DISTRIBUTION_RESEARCH.md` §8 pt.1/3 |
| ceiling (exposed/educated) | 7.5 | 2.0 | Miller(1956)/Preston&Colman(2000) convergent optimum (7) + deliberate past-ceiling extension (9-12), same doc §6.3/§8 pt.1 |
| mixing weight (ceiling) | 0.35 | — | inside Frederick's 17% (combined-sample perfect-score rate) .. Stieger&Reips' ~33% (educated/exposed-subgroup perfect-score rate) bracket, §2.1-2.2 |
| range clamp | [2,12] | — | §8 pt.1's full registered crossover-test range |

Measured population shape on the real regenerated 100-resident cast
(`resolution_bins`, before the arousal-state modulation):

```
2: 18   3: 29   4: 19   5: 5   6: 9   7: 4   8: 4   9: 6   10: 3   11: 3
```

Real, not unimodal: a dominant floor cluster (2-4: 66/100) plus a genuine,
smaller, right-extending ceiling tail (7-11: 20/100) — exactly the
mixture shape §7 point 4 of the research doc predicted from the real CRT
literature, not a bell curve collapsed onto one mean.
`test_resolution_bins_not_cloned_and_not_unimodal` gates this shape
(floor_ct>30, ceiling_ct>5) as a regression.

## 4. State/trait composition — confirmed clean, no redesign needed

```
effective_bins = max(2, round(resolution_bins_trait · resolution_level))
resolution_level = max(0, 1 − res_gain·arousal)     # bigville_motivation.json's
                                                      # mv_arousal formula, reused
                                                      # verbatim
```

This composed cleanly with the EXISTING `resolution_level` state mechanic
with **no redesign required** — confirmed, not assumed: `resolution_level`
was already a `[0,1]` fraction and `resolution_bins` is already an integer
ceiling, so multiplicative composition + re-quantization to the integer
lattice is a direct, one-line application of the project's own frame/
continuum invariant, not a new mechanic. `res_gain=1.0` is a documented
DEMO CHOICE (§ PREREG 4) — `bigville_motivation.json`'s own `res_gain` is
per-agent-declared and was not set anywhere for cast100 residents before
this rung (confirmed zero pre-existing connection between the two seeds,
per the orchestrating session's own grep). Registered honest limitation
(PREREG §4): this composition is computed once at demo-setup time, not
wired as a live `run_rules` production recomputing `effective_bins` every
tick — that wiring is named as straightforward, not built here.

## 5. Live two-resident demonstration — real measured numbers

Mechanical, non-cherry-picked selection: lowest/highest `resolution_bins`
in the real, committed `bigville_cast100.json`, tie-broken by index.

| | **Barnaby Furlong** (low, idx 5) | **Bartholomew Quirke** (high, idx 11) |
|---|---|---|
| role | labourer | labourer |
| `resolution_bins` (trait) | **2** | **11** |
| `arousal` (state input) | 0.2838 | 0.2632 |
| `effective_bins` | **2** | **8** |
| mean \|true_j − quantized_j\| | **0.5529** | **0.0603** |
| single-relax energy | **+5.191** | **−1.772** |
| single-relax frustration | **9.861** | **1.621** |
| single-relax coverage | 5/5 | 5/5 |
| 20-restart mean frustration | **8.687** | **2.070** |
| 20-restart mean energy | 3.464 | −1.219 |
| 20-restart basin count | 4 | 3 |

Both residents' `arousal` values are close (0.28 vs 0.26 — comparable
state), so the trait ceiling (`resolution_bins`) is what actually drives
the large `effective_bins` gap (2 vs 8), isolating resolution as the
manipulated variable as designed.

**Mechanistic reading of why**: at `effective_bins=2`, `quantize_j`'s
vocabulary is exactly `{-1, +1}` — every one of Barnaby's 5 real,
individually-nuanced "true" couplings (which range `0.35` to `0.55` in
magnitude, none anywhere near ±1) gets rounded to a MAXIMAL value.
Every relationship becomes either maximally attractive or maximally
repulsive; there is no way to represent "somewhat positive." That is a
direct, mechanical demonstration of the creator's own framing
(`CAN_BELIEF_QUANTIZATION_PREREG.md §0`): "lower metacognition leads to
lack of nuance… mechanically explained by the quantisation of causal
linkage" — here it produces measurable spin-glass frustration between
simultaneously-held maximal commitments that the resident's own true
psychological profile never actually endorsed at that strength.
Bartholomew's `effective_bins=8` vocabulary (`linspace(-1,1,8)`, 7
distinct non-endpoint levels available) keeps his quantized weights within
`0.06` of his true values on average — his network's structure barely
distorts what his own params actually implied, and it relaxes to a stable,
negative-energy basin instead.

**Predictions, scored:**
1. Manipulation check (rounding error higher for coarse): **CONFIRMED**,
   large (9.2×).
2. Primary (coarse shows higher frustration / shallower dominant basin —
   the direction `CAN_BELIEF_QUANTIZATION_RESULTS.md` actually measured
   previously, deliberately not the naive "fewer basins" intuition):
   **CONFIRMED**, large (6.1× on single-relax frustration, 4.2× on
   20-restart mean frustration; energy sign flips from negative/stable to
   positive/frustrated).
3. Basin count itself (registered as NOT the primary prediction, per the
   prior rung's own null on this specific metric): 4 (coarse) vs. 3
   (fine) — technically MORE basins for coarse, consistent with
   `CAN_BELIEF_QUANTIZATION_RESULTS.md`'s own prior finding that coarse
   quantization does not straightforwardly reduce basin count; reported
   exactly as registered, not reinterpreted.

## 5.1 Supplementary population-wide check (exploratory, not pre-registered
with the same rigor as §5)

Ran the same builder + single-relax audit (no multi-start) across all 100
committed residents:

- `corr(effective_bins, frustration)` = **−0.335**
- `corr(effective_bins, energy)` = −0.075 (weak — energy sign is noisier
  population-wide than the two clean demo residents happened to show)
- `corr(effective_bins, mean rounding error)` = **−0.901** (expected —
  this is close to definitional, same status as §5's manipulation check)
- low-bins group (`effective_bins≤3`, n=78) mean frustration **3.29** vs.
  high-bins group (`effective_bins≥7`, n=4) mean frustration **1.38** —
  same direction as the two-resident demo, smaller margin, and the group
  sizes are heavily imbalanced (the ceiling tail is genuinely thin at
  this `arousal`-modulated grain — reported honestly, not smoothed over;
  this is descriptive, not a powered test, per this project's own
  standing "power the gate before the endgame" rule).

**Control, to rule out a confound**: held `effective_bins` FIXED at 8 for
every one of the 100 residents (so each resident's OWN individually-
nuanced "true" couplings still varied, only the QUANTIZATION GRAIN was
held constant) and recomputed frustration. The correlation between what
each resident's trait-driven `effective_bins` WOULD have been and this
fixed-bins frustration collapsed to **−0.075** (from −0.335) — confirming
resolution, not some other resident trait incidentally correlated with
`resolution_bins`, is what drives the population-level effect.

## 6. Regression

Targeted run:
```
python3 -m pytest tests/test_cast100_migrated.py tests/test_can_ops.py \
  tests/test_causal_attitude_networks.py tests/test_bigville_can_integration.py -q
```
→ **56 passed** (9 + 12 + 23 + 12), all green:
- `tests/test_cast100_migrated.py`: **9/9** (unchanged, byte-for-byte —
  confirms the new trait did not perturb the existing generator's own
  gates, including its own `test_same_seed_identical_cast_and_map`).
- `tests/test_can_ops.py`: **12/12**, unchanged (this rung added zero
  lines to `can_ops.rs`/`py.rs`).
- `tests/test_causal_attitude_networks.py`: **23/23**, unchanged.
- `tests/test_bigville_can_integration.py` (new): **12/12** — trait
  presence/range/mixture-shape, RNG-isolation (existing 12 params
  provably unperturbed by monkeypatching the new draw to a deliberately
  different value), committed-seed-matches-fresh-regen, the 3 pure
  builder functions' boundary behavior, distinct-node independence, the
  no-rule-engine grep, and the §5 measured direction encoded as a
  regression assertion (`test_low_resolution_resident_shows_more_
  rounding_error_and_more_frustration`).

**Broad sweep, run synchronously to completion (not backgrounded/guessed
at)**:
```
python3 -m pytest tests/test_bigville_*.py tests/test_cast100_migrated.py \
  tests/test_can_ops.py tests/test_causal_attitude_networks.py -q
```
→ **688 passed, 1 failed**, 400s. The one failure —
`tests/test_bigville_decision_migrated.py::
test_discipline_no_rust_edits_and_engine_unchanged` — asserts `git ls-files
*.so` is empty (no tracked native binary). **Confirmed pre-existing and
unrelated to this rung**: `runners/dsl/python/substrate_rs/_native.abi3.so`
is already tracked at the base commit (`git show
d061b2d:runners/dsl/python/substrate_rs/_native.abi3.so` succeeds), this
rung's diff never touches that path (`git diff --stat d061b2d HEAD --
runners/dsl/python/substrate_rs/_native.abi3.so` is empty), and the file's
last modifying commits (`4621dca`, `1415ff9`, `46e18a1`) all predate this
branch. This assertion would fail identically on a clean `main` checkout
with zero changes from this rung — named honestly as a pre-existing
failing node, not silently worked around, per this project's own
"baseline must be a list of node ids" discipline.

## 7. What this rung establishes, and what it does NOT

**Establishes**: a real, individually-parameterized CAN belief network per
resident is mechanically buildable from `bigville_cast100.json`'s existing
params using ONLY the already-compiled `can_ops.rs` PyO3 surface; a
population-grounded, cited, mixture-drawn (not unimodal) trait-level
resolution parameter composes cleanly with the pre-existing arousal-state
`resolution_level` mechanic with no redesign; on a real, non-cherry-picked
two-resident comparison AND a population-wide supplementary check with a
confound-ruling-out control, resolution genuinely and substantially changes
measured basin frustration/energy in the predicted direction, using the
exact quantization mechanism this project's own prior CAN rung already
validated.

**Does NOT establish**: N-scaling behavior (this is the explicitly-excluded
crossover-point experiment's job, not this rung's); basin-count as the
right primary metric (registered as NOT primary here, per the prior rung's
own null on that specific reading); anything about multi-resident
interaction (each of the 100 residents' networks is fully independent in
this rung — no resident's Concept nodes couple to another's); anything
about live-tick dynamics (Hebbian learning, identity drift, evidence decay
are all real `can_ops.rs` functions, none exercised here — this rung is a
single relax + a cold-restart sweep, not a simulation run); the population-
wide §5.1 numbers are exploratory, not a powered claim — the low/high-bins
group split is heavily size-imbalanced (78 vs 4) at this arousal-modulated
grain, named honestly rather than smoothed over.

## 8. Tractable now vs. named follow-on

**Tractable now (this rung, done)**: the mechanism, on 2 real residents
plus a 100-resident supplementary sanity check, all independent networks,
single relax + cold-restart sweep only.

**Named, not built** (explicitly out of scope, per the task):
- Full multi-resident interaction (residents' Concept nodes coupling to
  each other's — e.g. resident A's `trust_mayor` influencing resident B's
  via a testimony/gossip edge).
- Live simulation-tick integration (`effective_bins` recomputed every tick
  as arousal changes; Hebbian `J` learning; identity-field drift;
  evidence/field decay over simulated time).
- The Matthew-effects/collapse-failure-driven-avoidance-learning mechanism
  (explicitly the next rung after this one).
- The shape-recognition/compression tractability layer for scaling CAN
  relaxation past small hand-built networks (already named as future work
  in `CAN_BELIEF_QUANTIZATION_PREREG.md §4.5`, untouched here).
- The crossover-point N-scaling experiment itself (a sibling rung's
  explicit territory, not touched or collided with in this branch).

## 9. Worktree

`/home/matt/ozmadev/ocelot-worktrees/bigville-can-integration`, branch
`bigville-can-integration`, base `main @ d061b2d`.
