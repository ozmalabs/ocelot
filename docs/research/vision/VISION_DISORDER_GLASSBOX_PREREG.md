# VISION — THE DISORDER GLASS-BOX: mental illness as a mis-set decay/demotion knob (PRE-REGISTRATION)

*Committed ALONE, BEFORE any implementation and BEFORE any measurement
(PROTOCOL §3). Isolated worktree off `main` HEAD **`53d2467c0d`** (LEDGER 198000
— THE DEMOTION HIERARCHY). Engine canonical
**`793ce09ed498a749abb79aeaea44b92e`** (`_native.abi3.so`, shared build, Rust
source identical to this worktree — `source_match` to be reported). This rung
adds **NO Rust**, `term.rs` diff EMPTY. Seed block **199000–199999**.*

Seed-claim check (verbatim, run before any number):

```
$ python scripts/seed_claim.py 199000 199999
SEED CLAIM 199000-199999: CLEAN -- no collision DETECTED.
  Scope: 898 files with seed sinks; 609 UNRESOLVED sink sites tree-wide (counted, not discarded).
  CAVEAT 1 -- THE UNIT IS THE SEED INTEGER, not consecutive draws from
    one generator. default_rng(S) burns an unbounded stream downstream of
    S; a rung seeding ONCE at its block base measures as ONE seed here.
  CAVEAT 2 -- THIS TOOL UNDER-REPORTS BY DESIGN (7 declared blind spots;
    unresolvable sinks are COUNTED, not discarded). A CLEAN RESULT MEANS
    'NO COLLISION DETECTED', NEVER 'NO COLLISION EXISTS'.
```

---

## 0. FRAMING — understanding, not judgment (standing project rule)

This rung is a **mechanistic DEMO of an existing account** of psychiatric
symptoms as computational faults — NOT a new theory of psychiatry, and NOT a
moral claim about anyone. Each disorder here is presented as a state that **makes
sense given a broken parameter**: the machinery is doing exactly what its knob
tells it to. The point is a GLASS-BOX: turn one explicit graph-resident knob and
a symptom EMERGES; restore it and the symptom RESOLVES. Understanding the
mechanism, never judging the person.

## 0.1 The claim — a faulty decay/demotion system IS a class of symptom

Block 196000 (`seeds/staleness_decay.json`) established the integer half-life
DECAY ATOM (`freshness = Ashr(C0, IDiv(now − last_refresh, half_life))` — the
`scale2` halving on the per-sensor epoch axis, `half_life` set INVERSELY by
surprise). Block 198000 (`seeds/demotion_hierarchy.json`) built the DEMOTION
HIERARCHY on it: freshness-thresholded tiers FRESH(2)/GIST(1)/LATENT(0), a
`dh_demote` atom that COARSENS a trace as it decays, `dh_promote` that resets the
innovation clock on re-observation (climbs back to FRESH). Healthy cognition:
**decay ∝ surprise lets a settled trace demote fresh→gist→latent, freeing
capacity.**

A **faulty decay/demotion system is a class of mental illness** — a PARAMETRIC
fault on this already-landed machinery. This rung builds TWO disorders, both
DEMOTION FAILURES, each an explicit graph-resident knob:

- **OBSESSION / RUMINATION = a SELF-REFRESHING LOOP.** Pathology: attending to a
  trace REFRESHES it (resets `last_refresh_epoch` to `now_epoch` every tick) — a
  positive feedback where *dwelling keeps it FRESH*, so it NEVER demotes and
  DOMINATES the field (crowding out capacity — the anti-DRAM "hold forever"
  worst case flagged in 198000's frame). Cut the self-refresh coupling
  (surprise-gated decay restored) → it demotes → resolves.
- **PTSD / non-extinction = a held THREAT-SURFACE that WON'T DEMOTE.** Pathology:
  a trace with a pathologically long `half_life` never demotes to GIST ("past")
  → stays FRESH ("present") → re-experienced AS PRESENT (the held prediction
  never releases). Extinction learning IS the decay of a fear association; this
  is extinction FAILING. Restore a normal `half_life` → it demotes to gist
  ("past") → resolves.

Both knobs are the **mis-set precision/freshness** of the aberrant-precision /
aberrant-salience account (§4): precision = freshness in the Kalman-decay.

## 1. The knob (explicit, graph-resident) — and the two rules

All new logic lives in `seeds/disorder_glassbox.json`
(`depends_on: [staleness_decay, demotion_hierarchy]`, area `retina`). Every rule
is gated on a `HeldDisorderParams` node (`enabled == 1`), created ONLY by the
opt-in measure adapter. Absent that node NO rule fires and every existing path is
byte-identical (default-OFF). All Terms already exist — `Attr`, `Var`, `Lit`,
`Eq`, `Gte`, `Gt`, `IfThenElse`, `And` — **term.rs diff EMPTY, NO Rust.**

**THE OBSESSION KNOB — an explicit graph EDGE `retina -ruminates_on-> HierTrace`.**
The self-refresh coupling is *literally an edge in the graph*: the trace that is
being ruminated on. Its presence IS the disorder; snipping it IS the cure.

1. `dis_ruminate` (order 0 — BEFORE `dh_promote`(1)/`dh_freshness`(2)):
   - match `[retina, has_disorder_params, dp]`, `[retina, ruminates_on, tr]`,
     `[retina, has_hier_trace, tr]`; where `dp.enabled == 1`.
   - effect: `set_attr tr last_refresh_epoch = tr.now_epoch`.
   - This is the POSITIVE FEEDBACK: each tick the trace is attended, its
     innovation clock is reset, so `dh_freshness` computes `Δ = 0 ⇒ freshness =
     C0` → `dh_tier` → FRESH → the trace never demotes. Remove the `ruminates_on`
     edge and the rule cannot match → normal surprise-gated decay proceeds.

**THE PTSD KNOB — the `half_life` attribute on the threat `HierTrace` (mis-set
large).** No new rule: the existing `dh_freshness`/`dh_tier`/`dh_demote` already
produce a stuck-FRESH trace from a large `half_life` (`IDiv(Δ, half_life) = 0` ⇒
`freshness = C0`). Restoring a normal `half_life` lets it demote. The disorder
faculty adds only a present/past READOUT rule:

2. `dis_present_readout` (order 5 — AFTER `dh_tier`(3)/`dh_demote`(4)):
   - match `[retina, has_disorder_params, dp]`, `[retina, has_hier_trace, tr]`;
     where `dp.enabled == 1`.
   - effect: `set_attr tr experienced_as_present =
     IfThenElse(tr.freshness ≥ dp.t_present, 1, 0)`.
   - The graph's own "is this held trace re-experienced as PRESENT, or filed as
     PAST?" decision. `t_present = 256 = T_FRESH`, so present ⟺ FRESH tier. A
     stuck-FRESH threat surface reads `experienced_as_present = 1` (present); a
     demoted one reads 0 (past).

Both disorders are pure knobs: the ONLY difference between the sick and healthy
runs is the `ruminates_on` edge (obsession) or the `half_life` value (PTSD).
Nothing else changes.

## 2. Gates (pre-registered BEFORE any number)

**G1 — OBSESSION (emerge + reverse).**
- *Emerge (loop ON — `ruminates_on` edge present):* drive one obsessive
  `HierTrace` over increasing `now_epoch`. Assert `tier == FRESH(2)` for ALL
  epochs (freshness pinned at C0; never demotes), contrasted against a
  background trace on the same eye that demotes 2→1→0.
- *Reverse (loop OFF — snip the edge):* on the SAME eye, remove the
  `ruminates_on` edge and continue advancing `now_epoch`. Assert the trace now
  demotes fresh→gist→latent (tier steps down). Reversible.
- *Capacity crowding (cf 198000 G4):* a population of M background traces
  (staggered ages, tiers spanning FRESH..LATENT) plus one obsessive trace, at a
  MATCHED total bit budget B. Under obsession the obsessive trace holds a
  permanent FRESH 8-bit slot; healthy it demotes to a 1-bit LATENT marker.
  Assert **fewer background traces are retained under obsession than under
  health** (the obsession CROWDS OUT capacity); restoring health frees the slot
  and MORE background traces are retained. Report the count both arms + a budget
  sweep.
- Able to fail if the obsessive trace demotes with the loop on, if it does NOT
  demote after the loop is cut, or if obsession does not reduce retained
  capacity.

**G2 — PTSD (emerge + reverse).**
- *Emerge (long `half_life`):* a threat `HierTrace` with a pathologically large
  `half_life`, driven over increasing `now_epoch`. Assert `tier` stays FRESH and
  the graph-native `experienced_as_present` stays **1 ("present")** for the whole
  horizon (never demotes to gist/"past").
- *Reverse (restore normal `half_life`):* on the SAME eye, set `half_life` back
  to a normal value and continue. Assert the trace demotes to GIST/LATENT and
  `experienced_as_present` flips to **0 ("past")**. Reversible.
- Contrast against a NORMAL-`half_life` control trace that demotes to past on the
  ordinary timescale. Able to fail if the long-`half_life` trace ever reads past
  within the horizon, or if restoring `half_life` does not flip it to past.

**G3 — THE KNOB IS EXPLICIT + GRAPH-RESIDENT + PURE (glass-box).**
- *Source-audit:* the disorder is produced by NAMED graph-resident parameters —
  the `ruminates_on` EDGE (obsession) and the `half_life` ATTRIBUTE (PTSD) — read
  by graph RULES under `run_rules()`. NO hidden Python decision: audit the
  measure adapter contains only `add_node`/`add_edge`/`remove_edge`/`set_attr`/
  read calls (mechanical host I/O), no conditional over graph state that drives a
  disorder.
- *Pure knob:* byte-compare a NEVER-SICK healthy eye against a
  MADE-SICK-THEN-CURED eye (edge added then removed / `half_life` set-then-
  restored). Assert the cured graph is identical to the never-sick graph on the
  trace's tier/stored/present readout — turning the knob back restores health
  with no residue.

**G4 — SCIENCE MAPPING (brief, honest).** A short situating in the RESULTS doc:
the mis-set parameter IS the precision/freshness of the aberrant-precision /
aberrant-salience literature — Kapur (aberrant salience → psychosis), Friston /
Corlett (aberrant precision-weighting of prediction error), and extinction-
failure models of PTSD (a fear memory whose association fails to decay). Freshness
= precision in the Kalman-decay; a mis-set half-life = mis-set precision. Honest
scope: this is a mechanistic DEMO of an existing account, not a new psychiatry.

**INTEGER-NATIVE audit.** All disorder Terms lie in the integer set `{Ashr, Shl,
IDiv, Minus, Plus, IfThenElse, Lt, Gt, Gte, Eq, And, Attr, Lit, Var}`; ZERO
`{Div, Times, Exp, Log, Sqrt}` in the disorder rules. Assert 0 offending cells.

**DEFAULT-OFF byte-identity.** With no `HeldDisorderParams` node, no disorder
rule fires: assert an eye is byte-identical with vs without the
`disorder_glassbox` seed loaded, and the oracle (`scripts/rung7_vision_bench.sh`)
is BEFORE == AFTER. The disorder knobs are opt-in; the oracle is unchanged.

## 3. Discipline

- **NO Rust; `term.rs` diff EMPTY.** Reuse `Ashr`/`IDiv`/`IfThenElse`/`Gte`/`Eq`
  + `set_attr`; all exist. Canonical `.so` `793ce09e…` stays untouched (seed +
  Python-only). No Rust changes.
- **Python is a mechanical measure-adapter only** — builds the opt-in params
  node, adds/removes the `ruminates_on` edge, sets `half_life`/`now_epoch`,
  ticks, reads graph-native `tier`/`stored`/`present`/`experienced_as_present`
  attributes. Every DECISION (freshness, tier, demote, promote, ruminate,
  present/past) is a graph RULE under `run_rules()`. No agent decisions in Python
  (CLAUDE.md).
- **Measure module IMPORT-INERT** — nothing runs at import; `main()` only.
- **Engine-semantics gate set** (lesson 12) green in one session; eye suite +
  `held_surface` + `staleness_decay` + `demotion_hierarchy` green. Oracle
  BEFORE == AFTER. `source_match` own/shared. Commit before report. Do NOT merge
  to main or touch VISION_PROTOCOL.md — the supervisor merges the ledger row.

## 4. Deliverables

Prereg hash; the knob (the `ruminates_on` edge + the `half_life` attribute + the
two rules); G1 obsession emerge+reverse (tier-over-time + capacity crowding);
G2 PTSD emerge+reverse (tier + present/past readout); G3 knob source-audit +
pure-knob reversibility byte-compare; G4 honest science mapping; integer-native
audit (0 offenders); term.rs-EMPTY; full engine-semantics gate + eye suite;
oracle BEFORE == AFTER; default-OFF byte-identity; canonical-untouched;
source_match. A measured honest negative (a disorder does not cleanly reverse) is
a valid landing, reported straight. Raw numbers in
`VISION_DISORDER_GLASSBOX_RESULTS.md` + `results/disorder_glassbox/`.
