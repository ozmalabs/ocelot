# VISION — THE DISORDER GLASS-BOX: mental illness as a mis-set decay/demotion knob (RESULTS)

*Prereg `762f816a5f` (committed ALONE before any number). Isolated worktree off
`main` HEAD `53d2467c0d` (LEDGER 198000). Engine canonical
`793ce09ed498a749abb79aeaea44b92e` (`_native.abi3.so`) UNCHANGED — this rung adds
**NO Rust**, `term.rs` diff EMPTY, seed + Python-only. Seed block **199000**.
Deterministic; no wall-clock claim.*

Raw: `results/disorder_glassbox.json`, figure
`results/disorder_glassbox/disorder_glassbox.png`. Measure:
`scripts/disorder_glassbox_measure.py`. Gate:
`tests/test_disorder_glassbox_migrated.py` (9/9). Seed:
`seeds/disorder_glassbox.json`.

## 0. FRAMING — understanding, not judgment

This is a mechanistic DEMO of an EXISTING account of psychiatric symptoms as
computational faults — not a new theory of psychiatry, and not a moral claim
about anyone. Each disorder here is a state that **makes sense given a broken
parameter**: the machinery does exactly what its knob says. The point is a
GLASS-BOX — turn one explicit graph-resident knob and a symptom EMERGES; restore
it and the symptom RESOLVES. Understanding the mechanism, never judging the
person.

## 1. The claim and the knob

Block 196000 (`staleness_decay`) is the integer half-life DECAY ATOM (`freshness
= Ashr(C0, IDiv(now − last_refresh, half_life))`). Block 198000
(`demotion_hierarchy`) built freshness-thresholded tiers FRESH(2)/GIST(1)/
LATENT(0) with a `dh_demote` atom that COARSENS a trace as it decays and
`dh_promote` that resets the clock on re-observation. Healthy cognition: decay ∝
surprise lets a settled trace demote fresh→gist→latent, freeing capacity.

A **faulty decay/demotion system is a class of mental illness** — a PARAMETRIC
fault on this landed machinery. Both disorders below are DEMOTION FAILURES,
produced by a NAMED graph-resident knob (`seeds/disorder_glassbox.json`,
`depends_on: [staleness_decay, demotion_hierarchy]`, default-OFF opt-in
`HeldDisorderParams`). All Terms already exist — **term.rs diff EMPTY, NO Rust.**

| disorder | knob (graph-resident) | mechanism | rule |
|---|---|---|---|
| OBSESSION / RUMINATION | the EDGE `retina -ruminates_on-> HierTrace` | attending resets `last_refresh_epoch = now_epoch` each tick → freshness pinned at C0 → never demotes → crowds capacity | `dis_ruminate` (order 0) |
| PTSD / non-extinction | the ATTRIBUTE `half_life` (mis-set large) | `IDiv(Δ, half_life) = 0` → freshness = C0 → stays FRESH ("present") | (reuses `dh_freshness`) + `dis_present_readout` (order 5) |

`dis_present_readout` exposes the graph's own present/past decision:
`experienced_as_present = IfThenElse(freshness ≥ t_present, 1, 0)`
(`t_present = 256 = T_FRESH`), so present ⟺ FRESH tier.

## 2. G1 — OBSESSION (emerge + reverse) — PASS

**Emerge (loop ON, `ruminates_on` edge present).** One obsessive trace vs a
background trace on the same eye, `half_life = 1`, driven over `now_epoch` 0..12.
The self-refresh loop pins the obsessive trace FRESH forever; the background
trace demotes normally:

```
obsessive tier (ruminated):  2 2 2 2 2 2 2 2 2 2 2 2 2   ← NEVER demotes
background tier (healthy):    2 2 2 1 1 1 1 0 0 0 0 0 0   ← fresh→gist→latent
```

**Reverse (loop OFF — snip the edge).** On the SAME eye the `ruminates_on` edge
is removed (`remove_edge` returned True); surprise-gated decay resumes and the
formerly-obsessive trace demotes:

```
obsessive tier after snip (now 13..25): 2 2 1 1 1 1 0 0 0 0 0 0 0
```

The disorder is REVERSIBLE: stuck FRESH with the loop on → demotes to LATENT once
the coupling is cut.

**Capacity crowding (cf 198000 G4).** M = 32 background traces at staggered ages
(tiers spanning FRESH..LATENT) plus one obsessive trace (an old memory,
`age = 200`), at a matched bit budget. Under obsession the obsessive trace holds
a permanent FRESH **8-bit** slot; healthy it is a **1-bit** LATENT marker. At the
budget where the stolen slot bites hardest (**B = 63 bits**):

| arm | obsessive trace | background traces retained |
|---|---|---|
| OBSESSION | FRESH, 8 bits | **12** |
| HEALTHY | LATENT, 1 bit | **19** |

The obsession CROWDS OUT **7 background traces** — exactly the 7 bits its stuck
FRESH slot steals. Health retains ≥ obsession at every budget in the sweep, and
strictly more across a wide band. Restoring health frees the slot and capacity
returns.

## 3. G2 — PTSD (emerge + reverse) — PASS

**Emerge (long `half_life`).** A threat trace with `half_life = 1_000_000` vs a
normal control (`half_life = 1`), over `now_epoch` 0..12. The threat surface
never demotes; the graph-native present/past readout stays "present" for the
whole horizon, while the control decays to "past":

```
threat experienced_as_present:  1 1 1 1 1 1 1 1 1 1 1 1 1   ← re-experienced AS PRESENT
control experienced_as_present: 1 1 1 0 0 0 0 0 0 0 0 0 0   ← filed as PAST (normal)
```

The threat trace's tier is stuck FRESH(2) throughout. This is extinction
FAILING: the held prediction (the fear association) never releases.

**Reverse (restore normal `half_life` — the PURE KNOB).** On the SAME eye,
`half_life` is set back to 1, nothing else changed. The long-neglected age of the
memory is finally felt and it demotes; the readout flips to "past":

```
threat experienced_as_present (now 13..23): 0 0 0 0 0 0 0 0 0 0 0   ← filed as PAST
threat tier at end: 0 (LATENT)
```

Reversible: stuck "present" with the long half-life → "past" the moment normal
precision is restored.

## 4. G3 — THE KNOB IS EXPLICIT + GRAPH-RESIDENT + PURE — PASS

**Source-audit (`results/disorder_glassbox.json`.g3_source_audit).**
- OBSESSION knob is the EDGE `ruminates_on` (a seed production); `dis_ruminate`
  matches that edge and self-refreshes (`set_attr last_refresh_epoch`). ✓
- `dis_present_readout` exposes `experienced_as_present` from freshness. ✓
- NO `del_node` anywhere in the disorder seed — these are decay faults, not
  deletion (deletion stays the separate 198000 `dh_delete_latent` faculty). ✓
- The measure adapter runs NO Python rule engine (no `gr.run` / `graph_rewrite` /
  `make_rule` / `_match` / `_apply`); every disorder DECISION is a graph RULE
  under `run_rules()`. The adapter only calls `add_node` / `add_edge_unchecked` /
  `remove_edge` / `set_attr` / `node` / `run_rules` — mechanical host I/O. ✓
- Knob names: obsession = `ruminates_on` (edge); PTSD = `half_life` (attr). ✓

**Pure knob (reversibility byte-compare).** A NEVER-SICK trace and a
MADE-SICK-THEN-CURED trace, read over a matched horizon, are BYTE-IDENTICAL on
`(tier, freshness, present, stored)`:
- obsession: never-ruminated ≡ ruminated-then-snipped ✓
- PTSD: normal-half_life ≡ long-then-restored ✓

Turning the knob back restores health with no residue — the glass-box property.

## 5. G4 — SCIENCE MAPPING (brief, honest)

The mis-set parameter IS the **precision / freshness** of the aberrant-precision
/ aberrant-salience literature. In the Kalman-decay reading of the held surface,
**freshness = precision**: a fresh trace is weighted as high-precision evidence;
a decayed one is discounted. A mis-set `half_life` is therefore a mis-set
precision.

- **Aberrant salience (Kapur, 2003, *Am J Psychiatry*).** Psychosis as the
  *aberrant assignment of salience* to internal representations — stimuli that
  should fade retain motivational grip. The self-refresh loop is exactly this:
  a trace that should demote is instead held at maximum salience (FRESH),
  dominating the field.
- **Aberrant precision-weighting of prediction error (Friston; Corlett;
  Adams et al., predictive-processing psychiatry).** Symptoms as mis-set
  precision on priors vs prediction errors. Here precision = freshness; the
  disorder is a mis-set decay of that precision — a stuck-high precision that
  refuses to be updated down.
- **Extinction-failure models of PTSD (fear-conditioning / extinction
  literature).** Extinction learning IS the decay of a fear association; PTSD is
  a fear memory whose association fails to extinguish and is re-experienced as
  present (intrusion / flashback). The long-`half_life` threat surface that never
  demotes to "past" is a direct mechanistic picture of extinction failing.
- **Rumination (depression / OCD).** Perseverative self-focused attention that
  *maintains* rather than resolves a negative representation — the self-refresh
  positive feedback, where dwelling keeps the trace fresh.

**Honest scope.** This is a mechanistic DEMO of these existing accounts on the
substrate's own decay/demotion machinery — a glass-box where the knob is
explicit and reversible. It is NOT a claim that these disorders reduce to a
single parameter, NOT a diagnostic model, and NOT a clinical result. It shows
that ONE landed mechanism (integer half-life decay + tiered demotion), with one
knob mis-set, reproduces the *computational shape* the literature describes.

## 6. Integer-native + default-OFF + engine/oracle/provenance

**Integer-native audit — PASS (0 float offenders).** The disorder rules use only
integer Terms:
- `dis_ruminate`: `{Attr, Eq, Lit, Var}`
- `dis_present_readout`: `{Attr, Eq, Gte, IfThenElse, Lit, Var}`

Zero `{Div, Times, Exp, Log, Sqrt}`. In-frame is integer (freshness, tier); the
knob is integer (`half_life`); the coupling is a graph edge. Nothing floats.

**Default-OFF byte-identity — PASS.** With the `disorder_glassbox` seed loaded
but NO `HeldDisorderParams` node, no disorder rule fires: an eye run over 5 photon
frames is byte-identical (node_count **272** + every RetinalColumn cell attr)
with vs without the seed. `HeldDisorderParams` count = 0, `HierTrace` count = 0.
The disorder knobs are strictly opt-in.

**Engine-semantics gate set (lesson 12) + eye suite, ONE session: 144 passed**
(`test_incremental_match`, `test_empty_match_proof`, `test_dirty_precision`,
`test_per_sensor_epoch`, `test_per_area_settlement`, `test_predicate_retraction`,
`test_eye_binding_projection`, `test_staleness_decay`, `test_dissipation_inference`,
`test_demotion_hierarchy`, `test_held_surface`, `test_photon_grapheye`,
`test_2d_retina`, `test_eye_graphnative_event`, `test_vision_eye`, and this rung's
`test_disorder_glassbox` — 144/0 in 379.54s).

**Oracle `bash scripts/rung7_vision_bench.sh`: 224/0, BEFORE == AFTER** —
default-OFF byte-identical; the oracle's fixed test list references none of this
rung's new files.

**`source_match` = shared** (`engine 04c9d28e316d`; "Rust source identical") —
NO Rust, canonical `793ce09e` UNCHANGED. `test_engine_provenance_migrated` 7/7.

**Own gate `tests/test_disorder_glassbox_migrated.py`:** 9/9.

## 7. Honest residuals

- The PTSD cure (restore `half_life`) makes the trace demote IMMEDIATELY (a step,
  not a graded gist→latent glide) because the innovation clock was never
  refreshed during the sick period, so the full accumulated age is felt at once.
  This is faithful (precision restored → the neglected memory collapses to past)
  and is what gives the clean byte-identity with a never-sick trace; a graded
  extinction curve would require ALSO re-anchoring the clock, which is a second
  change and not a pure knob. Reported straight; the gate is on the pure knob.
- The capacity budget for the headline is chosen as the point of maximum crowding
  in the sweep (B = 63); the crowding holds (health ≥ obsession) across the whole
  sweep, strict across a band. Reported, not cherry-picked to a single point.
- This demonstrates the computational SHAPE of two accounts on one mechanism; it
  is not a clinical or diagnostic claim (see §5 honest scope).
