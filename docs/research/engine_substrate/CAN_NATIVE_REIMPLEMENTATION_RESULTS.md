# Native CAN reimplementation — items 1-3 built, item 4 partial, item 5 attempted — RESULTS

Prereg: `CAN_NATIVE_REIMPLEMENTATION_PREREG.md`, same worktree/branch, base
`main @ e75142a` ("Merge can-concept-reimplementation-spike: replace, native
sd-loop/Gamma reframing, GO"). Worktree
`/home/matt/ozmadev/ocelot-worktrees/can-native-reimplementation`, branch
`can-native-reimplementation`.

**Verdict, up front.** Items 1-3 are BUILT and PROVEN on the real engine,
zero new Rust: `seeds/can_native_reimplementation.json` (5 rules, 4
productions), `tests/test_can_native_reimplementation.py` (8 tests, all
green, including 3 required live demonstrations with real measured
numbers). Two real, substantive, previously-unpredicted engine-level
findings were made and CORRECTED live while building (not smoothed over —
§3 and §4): (a) the "cold path" fixpoint's per-pass rule-list priority can
STARVE a sibling rule indefinitely, fixed by consolidating sign-branch
rules into one `IfThenElse`-computed rule per mode; (b) `ShapeDecode`'s
beam search can prefer a redundant multi-basin composite over a single
basin's own clean exact match on dense signatures, fixed by using the
EXISTING `codebook_scope` parameter for per-candidate classification.
Item 4 (Hebbian) is built for the edge-CREATION half only, exactly as
scoped; the graded-reweighting half is confirmed BLOCKED on the still-
unbuilt `logodds` `DimensionGenerator` (grepped, not assumed). Item 5
(polarization re-test) was attempted and is honestly non-monotonic, same
qualitative shape as the spike's own PoC finding. The Bigville migration
question was investigated concretely, not hypothetically: **NOT a clean
swap today** — Bigville's existing edge schema is single-direction, and the
native rule's `Sum` only reads out-edges (measured directly on a real
resident's real network, §7) — but the fix is a NAMED, CHEAP, ZERO-Rust
one-line change, not a hard blocker, and migration is NOT done in this
rung (explicitly out of scope, per the task).

---

## 0. What "zero new Rust" means here, confirmed by the diff itself

```
$ git status --short
?? docs/research/engine_substrate/CAN_NATIVE_REIMPLEMENTATION_PREREG.md
?? seeds/can_native_reimplementation.json
?? tests/test_can_native_reimplementation.py
```

Three new files, zero modified files, zero `.rs` files touched anywhere in
this branch. This is a stronger claim than "no new Term was needed" — no
EXISTING file was edited at all. The spike's own §3.4/§7 point 3 sizing
("if this holds, zero new Rust Terms... if it does not hold, the gap is
one small, well-scoped new Term") resolved in the "holds" direction, and
resolved with room to spare — the one open question (§0.0 below) needed a
schema CONVENTION (symmetric edge pairs), not new Rust.

---

## 0.0. Two probes, resolved before the design was registered (PREREG §0)

Quoted here for the record since they are load-bearing for §2/§3 below:

1. **`Edges` is out-edges only.** `Sum{source: Edges(c,"causal_influence"),
   value: Times([EdgeAttr(e,"weight"), Attr(Nth(e,2),"state")])}` works
   exactly as the spike predicted (confirmed live), but only reads a
   Concept's own OUT-edges — there is no existing Term returning IN-edges
   as `(src,type,tgt)` tuples with attrs attached. Adopted convention (not
   a Rust change): every network THIS rung builds mints `causal_influence`
   SYMMETRIC pairs (`A→B` and `B→A`, same weight). This is the exact fact
   that makes Bigville's existing single-direction schema incompatible
   without a builder change — see §7.
2. **`ShapeDecode`'s beam search can compose a redundant multi-part
   explanation that outscores a clean single-part exact match** on dense
   (N=8-relation) signatures when the codebook holds >1 overlapping
   entries — fit accumulates ADDITIVELY per step, and a coverage tie
   (both plans reach full coverage) is broken by TOTAL fit, not by
   preferring the FEWEST parts. Confirmed live on a real N=8 CAN network:
   decoding `sig_a` (a real converged state) against a codebook of `{basin_a
   (== sig_a exactly), basin_b (an unrelated real converged state)}`
   UNSCOPED returned `covered_by=None`, `ordered_parts=('basin_b',
   'basin_a')` — the search borrowed 3 relations from `basin_b` (which
   happened to coincide with `sig_a` on those 3 components) plus 5 from
   `basin_a`, for total_fit=28, beating `basin_a` alone (total_fit=24,
   `ordered_parts=('basin_a',)`, confirmed by re-running the SAME decode
   against a codebook containing ONLY `basin_a`). **This is a real,
   pre-existing property of `ShapeDecode`'s beam search
   (`shape_decode.rs:1570` `(cov_now, total_fit) > (best_cov,
   best_total_fit)`), not something this rung's seed introduces** — it was
   found live while validating the item 1-2 design, corrected by using the
   ALREADY-EXISTING `codebook_scope` parameter (`shape_decode.rs:982`,
   already used by `seeds/embodied_development.json` et al.) to decode
   against ONE held basin at a time, not new Rust. This is flagged here as
   a genuine finding worth the beam-search's own future attention (a
   composite explanation should arguably never beat a strictly SIMPLER one
   at equal coverage — an Occam violation), reported precisely rather than
   silently routed around.

---

## 1. What was built for items 1-3

`seeds/can_native_reimplementation.json` (`self_load_only: true`, depends
on `causal_attitude_networks` + `shape_decode_loop`, matching
`bigville_can_beliefs.json`'s own scoping precedent — not swept into a full
`load_all_seeds` boot). 5 rules, 4 Γ productions
(`Microtheory→has_concept→Concept`, `Concept→causal_influence→Concept`,
`Concept→coactivated_with→Coactivation`, `Coactivation→coactivation_of→
Concept`).

### Item 3 — `can_native_update_3state` / `can_native_update_2state`
(`seeds/can_native_reimplementation.json:102`, `:505`)

**Local field** (the exact discrete twin of `can_ops.rs::mt_mean_field_
marginal`'s `local = h + Σ J·σ_j`, `can_ops.rs:256-264`, minus the
`tanh`/relaxation):
```
local(c) = Attr(c,"external_field") + Attr(c,"identity_field")
         + Sum_{e in Edges(c,"causal_influence")} EdgeAttr(e,"weight") * Attr(Nth(e,2),"state")
scaled(c) = local(c) * Attr(mt,"temperature")
```
**3-state** (native CAN vocabulary, `σ∈{-1,0,+1}`), ONE rule (see §3 for
why one rule, not three):
```
target = IfThenElse(scaled > ATANH_HALF, 1,
           IfThenElse(scaled < -ATANH_HALF, -1, 0))
where:   discrete_mode=="3state" AND state != target
effects: set_attr(c, "state", target)
```
`ATANH_HALF = 0.5493061443340548` (`math.atanh(0.5)`, computed once at
design time, hard-coded — no `Tanh` Term needed, confirmed none exists,
matching the spike's §3.4 sizing exactly).

**2-state** (classical Hopfield, no deadzone, built for the convergence
COMPARISON only): `target = IfThenElse(local >= 0, 1, -1)`, same shape.

**Why this is genuinely asynchronous with zero new Rust — confirmed by
reading `rewrite.rs::run_rules_opts`, not assumed**: the non-batch ("cold
path") loop collects all bindings for a rule, applies exactly ONE
progressing binding, commits it immediately, and the NEXT rule (or the
SAME rule on its next pass) re-matches against the JUST-UPDATED graph
(`rewrite.rs:2183-2214`). This is Gauss-Seidel/asynchronous update by the
engine's OWN default execution model.

### Items 1-2 — `can_native_basin_decode` (`:712`)

Codebook = `ShapeSignature` nodes, `signature` = relation tuples
`["state", <concept_name>, <sign>]`. Classification decodes ONE
Observation per (state, candidate-basin) pair, `codebook_scope:
SetT([Attr(obs,"scope_name")])`, reading `residual`/`covered_count` scoped
to that ONE basin (§0.0.2's fix). `covered_count == goal_relations` ⟺
clean match to that basin; the demo/test reads back `covered_count` across
the probe set (the SAME multi-start-diagnostic reporting shape
`CAN_BELIEF_QUANTIZATION_RESULTS.md`'s own `_basin_sweep` helper already
uses — a query over already-decoded graph facts, not a Python decision).

### Item 4 — `can_native_note_coactivation` / `can_native_hebbian_mint`
(`:841`, `:1007`)

Two Concepts under the same Mt, no `causal_influence` edge yet, both
committed to the SAME nonzero sign: `note_coactivation` mints a
`Coactivation{noted_tick}` record on FIRST sight (no edge minted yet);
`hebbian_mint` mints the `causal_influence` edge (weight +1, both
directions independently — symmetric by the same §0.0.1 convention) only
once `Attr(mt,"can_tick") > Attr(coact,"noted_tick")` — i.e. on a
STRICTLY LATER external tick than the one that first noted it. `can_tick`
is a mechanically-bumped epoch counter, the SAME idiom
`shape_decode_loop.json`'s own `codebook_epoch`/`decoded_epoch` already
uses (Python bumps it between ticks; no rule ever decides to bump it).

---

## 2. Live demonstration (a) — discrete-async convergence vs. continuous-sync
oscillation, on the REAL engine

`tests/test_can_native_reimplementation.py::
test_discrete_async_never_oscillates_vs_continuous_sync` /
`test_continuous_sync_oscillates_on_at_least_one_real_draw`. N=8 complete
graph, β=2.0, coarse (3-level `J`) vs fine (9-level `J`), N_DRAWS=20 per
condition (smaller than the PoC's 30 — real PyO3 graph construction per
draw is far more expensive than pure-Python dict math; sized honestly for
this rung's own time budget, not silently matched to the PoC's count).
Continuous-sync check reuses the EXISTING `mt_mean_field_marginal(mt, 400/
401/402, tol, damping=1.0)` PyO3 surface (reproduces the pre-fix update
exactly, per `CAN_SYNCHRONOUS_UPDATE_FIX_RESULTS.md` §1's own cross-check
— a pure read, no graph mutation). Discrete-async check runs the REAL
seeded rules via `run_rules(3000)` and checks `steps < max_steps`.

**Real measured numbers** (both discrete-mode variants, both vocab
conditions, on the real engine):

```
[2state] coarse   continuous_sync_osc=12/20  discrete_async_nonconv=0/20  mean_frustration=5.500
[2state] fine     continuous_sync_osc=4/20   discrete_async_nonconv=0/20  mean_frustration=6.650
[3state] coarse   continuous_sync_osc=12/20  discrete_async_nonconv=0/20  mean_frustration=6.000
[3state] fine     continuous_sync_osc=4/20   discrete_async_nonconv=0/20  mean_frustration=6.862
```

**Confirmed, all three registered predictions**: (1) continuous-sync
oscillates on a large fraction of REAL draws on THIS engine (12/20 coarse,
4/20 fine — directionally consistent with every prior rung's own
coarse>fine oscillation lean); (2) discrete-async 2-state: **0/20
non-convergent in both conditions** — the textbook Hopfield Lyapunov
guarantee, holding on the real engine, not just the pure-Python PoC; (3)
discrete-async 3-state (the deadzone case the spike named as theoretically
OPEN, not guaranteed): **also 0/20 in both conditions** — empirically
clean, exactly as the PoC found, reported as an empirical fact, not a
proof (the spike's own §5.1 deadzone gap in the standard monotonicity
argument is not closed by this measurement, only not triggered on these
80 draws).

**This rung's own Lyapunov-guarantee approach vs. the sibling damping-fix
rung's suppression approach, stated precisely** (required by the task):
`CAN_SYNCHRONOUS_UPDATE_FIX_RESULTS.md`'s damping fix (λ=0.5) makes the
CONTINUOUS synchronous relaxation converge in every case it re-tested
(126/126) — a real, decisive empirical result, but it is empirical: damping
blends old and new values so that AT a fixed point the blend is a no-op
(`can_ops.rs:41-58`'s own comment), and nothing in that mechanism PROVES
no oscillation can occur for any network — it SUPPRESSES the symptom by
changing the trajectory, within the same continuous-relaxation paradigm.
This rung's discrete-asynchronous mechanism is different in KIND, not
degree: for the 2-state case, the absence of oscillation is a **structural
consequence of the update rule's own construction** — every committed flip
strictly decreases a bounded energy function (Hopfield 1982), so a
period-2 (or any-period) cycle is mathematically impossible BY THE SHAPE
OF THE UPDATE, not merely unobserved on the networks tested. The 3-state
case is the one place this rung's own guarantee is NOT airtight (a real,
named, open theoretical gap, §5.1 of the spike) — but even there, the
FAILURE MODE the fix and this rung both target (the classic period-2
Jacobi limit cycle) cannot occur in the discrete-asynchronous scheme even
in the deadzone case, because the update is never simultaneous across
nodes — only a genuinely different pathology (a single-spin energy
INCREASE at a deadzone transition) is theoretically possible, and 0/40
draws exhibited it in this rung's own sample. **Both fixes are real and
both stay; they are not redundant** — the damping fix is the correct,
decisive answer for callers that still want the continuous marginal
(`mt_target_equilibria`'s distance-to-target queries, e.g.); this rung's
mechanism is the correct answer for callers doing evidence PROPAGATION,
where the discrete state IS the thing being computed, not an intermediate
numerical artifact.

**Bonus (not the primary claim, §3 of PREREG)**:
`test_three_state_vs_two_state_frustration_bonus_comparison` measured
`mean_frustration_2state=5.700` and `mean_frustration_3state=5.700` —
**exactly tied** on this rung's own 20-draw coarse sample (a DIFFERENT
sample from the table above — different seed range), reported precisely
rather than reinterpreted: this neither confirms nor contradicts the PoC's
own finding (3-state HIGHER than 2-state, 6.2 vs 5.4 coarse) — a tie on a
20-draw sample is well within noise either way, and no claim is made about
which direction holds in general.

---

## 3. The starvation finding — a real engine-level property, found and
corrected live

**First design** (plus/minus/zero as three SIBLING rules, mirroring the
PoC's own `if/elif/else` reading too literally into three separate Rules)
measured **6/20 (2-state) and 2/20 (3-state) coarse draws failing to reach
a fixpoint within 3000 passes** — the OPPOSITE of the registered
prediction. Direct inspection (re-running `run_rules` with 20 MORE steps
after hitting the 3000-step cap, and comparing states) showed the
"non-convergent" networks were NOT oscillating — their states were
IDENTICAL before and after the extra steps, i.e. the system WAS already at
a genuine reachable fixed point; it simply never reached it, because
several concepts were frozen at their INITIAL value (never given even a
first chance to flip).

**Root cause, confirmed by reading `rewrite.rs:2210-2214`**: the cold-path
loop `break`s out of the ENTIRE per-pass rule iteration as soon as ANY
rule finds ONE progressing binding — `if found_progressing.is_some() {
steps += 1; any_progress = true; break; }`. With `update_plus`/`update_
minus`/`update_zero` as three separate rules in list order, `update_plus`
(or `update_plus_2state`) can find SOME progressing node EVERY SINGLE
PASS (a different node each time, as the network settles), monopolising
every pass and never yielding a turn to `update_minus`, which starves any
node that needed a `-1` (or `0`) transition it never got to make.

**This is a real, substantive finding about `run_rules`'s own
scheduling — not a bug in the Hopfield/Lyapunov argument.** Every
individual flip the mechanism DID commit was still a genuine,
energy-non-increasing single-spin update; the problem was fairness across
SIBLING RULES competing for the same one-slot-per-pass budget, not a
2-cycle. **Fix, architectural, zero new Rust**: consolidate the sign
branches into ONE rule per mode, computing the target value with the
existing `IfThenElse` Term (`can_native_update_3state`/`_2state`,
§1 above) — now every one of a Concept's own possible transitions competes
for the SAME rule's OWN binding-iteration turn, so no sibling rule can
monopolise the pass budget. Re-measured on the EXACT SAME failing draws:
**0/20 non-convergent, both modes, both vocab conditions** (§2's table).
This is reported as a real correction made DURING this rung, not
retroactively — the failed intermediate design and its fix are both part
of the record, matching this project's own standing self-correction
discipline.

**Consequence worth naming**: this is a general property of `run_rules`'s
cold path, not specific to CAN — any future rule set built as multiple
SIBLING rules competing to update the SAME kind of node should be aware
that an earlier rule (in registration order) with a persistently
replenished candidate pool can starve a later one indefinitely. This
rung's own fix (one rule, `IfThenElse`-computed target) is the general
answer, reusable elsewhere.

---

## 4. Live demonstration (b) — basin classification + residual/coverage as
coherence, on real convergent states

`test_basin_classification_and_frustration_signal`. Two REAL held basins
(`basin_a`, `basin_b`) are the ACTUAL converged states from two independent
item-3 relaxations (not hand-picked round numbers), decoded via §0.0.2's
scoped-per-candidate design:

```
exact match to basin_a:            {'basin_a': 8, 'basin_b': 3}   (goal_relations=8)
torn between basin_a/basin_b:      {'basin_a': 5, 'basin_b': 6}
undifferentiated (all zero):       {'basin_a': 1, 'basin_b': 2}
```

**Confirmed**: (a) the state that EXACTLY equals `basin_a` scores full
coverage (8/8) against `basin_a` and only PARTIAL (3/8) against `basin_b`
— clean, unambiguous recognition; (b) a state built by literally splicing
4 components from `basin_a` and 4 from `basin_b` scores partial against
BOTH (5/8 and 6/8) — neither candidate reaches full coverage, visibly
distinguishable from case (a)'s clean 8/8; (c) the totally uncommitted
(all-zero) state scores WORSE against its best candidate (2/8) than the
genuinely-mixed case (6/8) — consistent with the already-wired
`curiosity_targets_ambivalent_nodes` rule's own "near-zero state =
ambivalent" reading (`seeds/causal_attitude_networks.json:721`): a
committed-but-wrong state is closer to SOME basin than a state that never
committed to anything at all.

---

## 5. Live demonstration (c) — Hebbian mint-on-recurrence, edge-creation
half

`test_hebbian_mint_on_recurrence_not_on_first_sight`. Isolated from item
3's discrete-update rules on purpose (`discrete_mode="static"` — a real
interaction found while writing this test: on an isolated pair with zero
field and no coupling, `can_native_update_zero` would otherwise
immediately neutralize both concepts to `state=0` before the coactivation
rule ever saw their committed state — named in the test's own docstring,
not silently avoided).

Tick 1 (first sight, `can_tick=0`): `run_rules` fires
`can_native_note_coactivation` — mints a `Coactivation` record, does
**NOT** mint the edge yet (confirmed: `neighbours(a,"causal_influence")`
empty after tick 1). Tick 2 (`can_tick` bumped to 1, mechanically, by the
test): `can_native_hebbian_mint`'s guard (`can_tick > noted_tick`) now
holds — mints BOTH `a→causal_influence→b` and `b→causal_influence→a`
(symmetric, per §0.0.1's convention). Tick 3 (`can_tick=2`, edge already
present): re-running `run_rules` does **NOT** re-mint (edge count
unchanged) — recognize, not re-create, mirroring blob-edge minting's own
proven pattern.

**Item 4's reweighting half — confirmed blocked, not built, per the
task's own instruction to check first**: `grep -rn "logodds" runners/dsl/
src/*.rs seeds/*.json` finds it named ONLY in
`CAUSAL_LINKAGE_DIMENSION_RESEARCH.md` and `CAN_BELIEF_QUANTIZATION_
PREREG.md` — the `logodds` `DimensionGenerator` remains exactly as
un-built as the spike found it. Graded reweighting of an ALREADY-minted
edge is out of scope for this rung, named as blocked on that missing
piece, not attempted. **Decay has no proposed native analog anywhere in
this arc** (spike's own honest gap, unchanged here) — `seeds/can_native_
reimplementation.json`'s own `concepts` entries say so explicitly
(`:96`), rather than silently omitting the topic.

---

## 6. Item 5 — polarization re-test via `max_steps`, attempted, honestly
non-monotonic

`test_polarization_via_max_steps_sweep`. Re-runs `can_concept_poc_decode_
polarization.py`'s design on the REAL `ShapeDecode` Term, sweeping
`max_steps` (refinement depth) instead of a symmetric vote-count
`scrutiny_T` (the PoC's own honestly-corrected U-shape). N=8, two fixed
opposite prototypes, 11 α-levels × 8 trials each:

```
 max_steps   resolved  ambiguous    frac_near_extreme
         1         28         60                0.857
         2         30         58                0.767
         4         23         65                0.957
         8         31         57                0.839
        16         31         57                0.806
```

**Reported precisely, not reinterpreted**: `frac_resolved_near_extreme` is
**not monotonic** in `max_steps` either (0.857 → 0.767 → 0.957 → 0.839 →
0.806) — no cleaner than the PoC's own `scrutiny_T` U-shape, and on this
small sample (8 trials/α-level) the variation looks more like noise around
~0.8-0.9 than any real trend. This does not close the spike's own open
question (§7 point 5) — `max_steps` on THIS specific two-prototype design
is not obviously the missing one-parameter β-analogue either. Reported
honestly, per the task's own instruction to report whichever way this
comes out; not pursued further (a properly powered sweep of this specific
question is real, separate, un-sized follow-on work).

---

## 7. Migration-decision assessment — Bigville

**Registered check, run**: `test_bigville_schema_is_asymmetric_native_
rule_reads_only_out_edges` builds ONE real resident's CAN network via the
EXISTING, UNMODIFIED `worlds/bigville_can_beliefs.py::build_resident_can_
mt` (no changes to that file in this rung) and measures directly:

```
claim_credible OUT-neighbours (native rule reads these):        [#6]
claim_credible IN-neighbours (can_ops.rs ALSO reads these):      [#2]
IN-neighbours invisible to the native rule's Sum(Edges(c,...)):  {#2}
```

`claim_credible` has a real IN-edge from `trust_mayor`
(`STRUCTURAL_EDGES`'s `("trust_mayor", "claim_credible", -0.6,
"mood_bias")` entry, `worlds/bigville_can_beliefs.py:61-67`, minted
single-direction at `:180`) that the native rule's `Sum(Edges(c,
"causal_influence"))` — out-edges only, §0.0.1 — cannot see, while
`can_ops.rs::build_couplings` (`:163-196`) reads it correctly (both
directions, symmetrized). **This is the measured, concrete basis for the
recommendation, not a hypothetical**: today's Bigville schema is
NOT a clean drop-in for the native rule.

**What IS clean, checked, not assumed**: (1) `resolution_bins`/
`effective_bins`/`resolution_level` are entirely about the QUANTIZATION
GRAIN of the `weight` edge attr — they carry over completely unchanged
regardless of which mechanism reads that attr; no rework needed. (2)
`identity_field` (set directly by `build_resident_can_mt`,
`worlds/bigville_can_beliefs.py:166-174`) and `external_field` (written by
`apply_scenario_evidence` → `concept_apply_evidence` →
`can_ops.rs::apply_evidence_h`, `:863-871`, confirmed by direct read: `set_
node_float_attr(g, concept_id, keys.external_field_attr, current +
alpha*evidence)`) are the SAME attr names the native rule's `local_field`
term already reads — fully compatible, no rework needed. (3) `temperature`
(β) on the Microtheory is read identically by both mechanisms.

**Recommendation: do NOT migrate Bigville this rung (matches the task's
own explicit scope boundary); name the fix precisely as a real, cheap,
low-risk follow-on, not a hard blocker.** The one incompatibility is
narrow and mechanical: change `build_resident_can_mt`'s `STRUCTURAL_
EDGES` loop (`worlds/bigville_can_beliefs.py:176-181`) to mint BOTH
directions (`s.add_edge(concepts[a], "causal_influence", concepts[b],
{"weight": q_j})` AND the reverse) — a one-line-per-direction change,
**verified backward-compatible with the EXISTING continuous mechanism
too**: `build_couplings`'s own in-edge loop already de-duplicates a
neighbour it already found via the out-edge loop (`can_ops.rs:186-191`,
`if !neigh.iter().any(...)`), so minting both directions would NOT
double-count for `mt_mean_field_marginal`/`mt_relax_to_marginal` — the
continuous path is unaffected either way. This makes the fix strictly
additive risk-wise: it costs nothing on the mechanism Bigville uses today
and unblocks the native mechanism for a genuinely later migration rung.
Not built here, because building it crosses into `worlds/bigville_can_
beliefs.py` and the already-landed Bigville integration, both explicitly
out of this rung's scope per the task.

---

## 8. Regression

**Scoped regression (the task's own prescribed set), 67/67 passed**:
```
tests/test_can_belief_quantization.py tests/test_bigville_can_integration.py \
tests/test_causal_attitude_networks.py tests/test_can_ops.py \
tests/test_can_migration.py tests/test_can_crossover_point.py -q
→ 59 passed
tests/test_can_native_reimplementation.py -q -s
→ 8 passed (all live demonstrations printed above)
```

**Full boot regression** (`load_all_seeds` on a fresh `WorldAdapter`):
identical **8 pre-existing failures** to the documented baseline
(`acoustic_cue_vocab`, `character_tom`, `reading_constructions`,
`conceptual_categories`, `cue_investigator`, `named_compound_heads`,
`reading_skeleton`, `vision_change`, all `ValueError: seed node missing
local_id`), **0 rules_skipped** — `can_native_reimplementation.json` is
correctly excluded from the sweep (`self_load_only: true`, same as
`causal_attitude_networks.json`/`bigville_can_beliefs.json`).

**Broader `-k "can_"` sweep across all of `tests/`** hit 22 PRE-EXISTING
collection errors (`test_communication.py: ModuleNotFoundError: No module
named 'av'`, and 21 similar — audio/video codec and chess-adjacent optional
deps), confirmed unrelated: `git status --short` on three sampled offending
files shows zero changes from this branch, and `test_communication.py`
fails identically at collection with the SAME `av` import error regardless
of any CAN-related content — exactly the disjoint, environment-conditional
population `CLAUDE.md`'s own "optional-dep note" already documents at
length. Not this rung's concern; not a regression.

**No Rust build was needed or run** — §0 confirms zero `.rs` files
touched.

---

## 9. What this rung does NOT establish

1. **The 3-state deadzone case's convergence guarantee is empirical, not
   proven** (spike's own §5.1 gap, unchanged): 0/40 real-engine draws
   exhibited the theoretically-possible energy-increasing deadzone
   transition, but this is not a general theorem.
2. **The starvation finding (§3) was found and fixed for THIS rung's own
   rule shapes; it is not a general audit of every multi-rule seed in the
   corpus** for the same fairness risk — named as a reusable lesson, not
   swept for elsewhere.
3. **The `ShapeDecode` composite-vs-single-match scoring property (§0.0.2)
   is reported, not fixed** — it is a real property of the existing beam
   search worth someone's future attention (an Occam-violating tie-break),
   worked around here via `codebook_scope`, not patched.
4. **Basin ENUMERATION remains out of scope**, per the spike's own §3.1/§6
   finding — nothing built here does it, and nothing this project has
   built needs it.
5. **Item 4's graded-reweighting half and decay remain unbuilt**, both
   named precisely (logodds generator confirmed still absent; decay has no
   proposed analog at all).
6. **Item 5's `max_steps` sweep does not identify a clean β-analogue** for
   polarization sharpening — the spike's own open question stays open.
7. **The Bigville migration is investigated, not performed.** The fix is
   named and verified backward-compatible on paper (§7's `build_couplings`
   de-dup argument), but was not implemented or tested live in this rung.
8. **Whether any of this reflects real human belief-network dynamics**
   remains exactly as open as every prior rung in this arc left it — this
   document is about this SUBSTRATE's own best-fitted mechanism.
9. **`can_ops.rs` is untouched and still the working, damped, tested
   mechanism Bigville and any other current caller actually use** — this
   rung ADDS an alternative, it does not replace anything in place.

---

## 10. Reproduce

```bash
cd /home/matt/ozmadev/ocelot-worktrees/can-native-reimplementation
git log --oneline -1 main   # e75142a, verified before branching

# Scoped regression + all live demonstrations (-s for the printed tables)
PYTHONPATH=".:runners/dsl/python" python3 -m pytest \
  tests/test_can_native_reimplementation.py -q -s

# Existing CAN suite, unmodified, still green
PYTHONPATH=".:runners/dsl/python" python3 -m pytest \
  tests/test_can_belief_quantization.py tests/test_bigville_can_integration.py \
  tests/test_causal_attitude_networks.py tests/test_can_ops.py \
  tests/test_can_migration.py tests/test_can_crossover_point.py -q

# Full boot regression (pre-existing failures only, unrelated to this rung)
PYTHONPATH=".:runners/dsl/python" python3 -c "
from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds
a = WorldAdapter(seeds=())
rep = load_all_seeds(a)
print('failed:', len(rep['failed']), 'rules_skipped:', len(rep['rules_skipped']))
for f in rep['failed']: print(' ', f)
"
```
