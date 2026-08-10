# VISION — THE CORE-EMOTION SET as regulatory patterns on the signal economy (PRE-REGISTRATION)

*Committed ALONE, BEFORE any implementation and BEFORE any measurement
(PROTOCOL §3). Isolated worktree off `main` HEAD **`ef95fcaafa`** (LEDGER 202000
learning-progress/commit-net + 203000 allocentric held-surface). Engine canonical
**`793ce09ed498a749abb79aeaea44b92e`** (`_native.abi3.so`, shared build, Rust
source identical to this worktree — `source_match` to be reported). This rung
adds **NO Rust**, `term.rs` diff EMPTY, whole `runners/dsl` diff EMPTY. Seed block
**204000–204999**.*

Seed-claim check (verbatim, run before any number):

```
$ python scripts/seed_claim.py 204000 204999
SEED CLAIM 204000-204999: CLEAN -- no collision DETECTED.
  Scope: 904 files with seed sinks; 613 UNRESOLVED sink sites tree-wide (counted, not discarded).
  CAVEAT 1 -- THE UNIT IS THE SEED INTEGER, not consecutive draws from
    one generator. default_rng(S) burns an unbounded stream downstream of
    S; a rung seeding ONCE at its block base measures as ONE seed here.
  CAVEAT 2 -- THIS TOOL UNDER-REPORTS BY DESIGN (7 declared blind spots;
    unresolvable sinks are COUNTED, not discarded). A CLEAN RESULT MEANS
    'NO COLLISION DETECTED', NEVER 'NO COLLISION EXISTS'.
```

---

## 0. FRAMING — re-derive, not invent; understanding, not judgment

This rung **re-derives** established affective science and instantiates it
graph-natively; it does not claim to invent it. Specifically it re-derives:

- **Appraisal theory** (Scherer's Stimulus Evaluation Checks / component-process
  model; Lazarus's primary/secondary appraisal; Frijda's *laws of emotion* and
  **action tendencies**): an emotion is an APPRAISAL of the situation that
  produces an ACTION TENDENCY.
- **The circumplex** (Russell): affect laid out as **valence × arousal**. Here
  **valence = the SIGN of the progress/value signal**; **arousal = the MAGNITUDE
  of the surprise/precision signal**. Both are read off the economy already built.
- **Basic-emotion theory** (Ekman): a small core set with characteristic
  functional signatures.
- **The somatic-marker cut** (Damasio): emotion is a REGULATOR of decision, not
  an epiphenomenon — the action tendency biases what the agent does next.
- **Inclusive fitness / generativity** (Hamilton; Erikson's generativity) for
  **fulfilment**: value defined at the level of the collective/lineage, not the
  individual.

**The contribution is not the theory.** It is (a) the **graph-native INTEGER
instantiation** of the core set on the *same* decay / curiosity / commit /
value atoms already in the tree (196000 `staleness_decay`, 202000
`learning_progress_curiosity`), with **NO new module and NO new Rust Term**;
(b) the **reference-frame-per-emotion principle** — *each emotion's value
function reads value at a LEVEL OF SELECTION*, and fulfilment reads the
SUPERGRAPH where the individual emotions read the individual; (c) the
**state-based (not observation-based) disorder taxonomy** — a disorder is a
STATE-KNOB setting, and the behavioural "factors" psychometrics measure are
SHADOWS of the knob (ties 199000 `disorder_glassbox`, understanding-not-judgment).

**Boundaries, held explicitly.** Core/basic emotions map onto the raw economy
(surprise, precision, progress, value). Complex SOCIAL emotions (guilt, pride,
shame) require self+other models; we include at least one social frame IF the
ToM seeds support it cleanly, and NAME THE GAP otherwise. We emulate the
**FUNCTIONAL emotion — the regulator (appraisal → action tendency)** — and make
**NO claim to felt qualia**. That line is held throughout: this is the
computational role an emotion plays, not a claim that the substrate *feels*.

---

## 1. The claim — each emotion is an APPRAISAL → ACTION-TENDENCY pattern over the EXISTING signal economy

The tree already contains the signal economy an emotion appraises. This rung adds
**graph rules** (a seed, `seeds/core_emotions.json`) that READ that economy and
SET an action-tendency attribute. No emotion is a Python `if`/`else`; each is a
RULE. The atoms reused verbatim:

- **precision / freshness** — 196000: `freshness = Ashr(c0, IDiv(now − last_refresh, half_life))`
  (the `scale2` half-life decay on the per-sensor epoch axis). A threat's
  precision, and whether it DECAYS (fear) or WON'T decay (anxiety), is exactly
  this atom + the 199000 present/past readout (`freshness ≥ t_present`).
- **learning-progress** — 202000: `learning_progress = residual_prev − residual`
  (the integer backward-difference of temporal surprise). `> 0` → curiosity;
  `→ 0` → boredom (the 202000 noisy-TV cut).
- **value (diminishing returns)** — 202000 commit-net: `value = V_max − Ashr(V_max, step)`.
  The signed change in this value on a valued outcome is `value_progress` (joy /
  sadness sign).
- **surprise (raw residual)** — the pre-appraisal orienting spike itself.

**The reference-frame-per-emotion principle.** Every emotion's value function
carries a **reference frame = a level of selection** at which value is read:

| Emotion | Reference frame | Appraisal (config of the economy) | Action tendency |
|---|---|---|---|
| **surprise** | individual | raw residual spike, NOT yet appraised | **ORIENT** (pre-appraisal) |
| **fear** | individual survival | threat-precision spike, short horizon (decays) | **AVOID** |
| **anxiety** | individual | threat-precision that WON'T decay (long half-life) | **VIGILANCE** (sustained) |
| **anger** | individual | blocked VALUED goal + an approachable blocker | **APPROACH-BLOCK** (energised) |
| **frustration** | individual | blocked VALUED goal, NO approachable blocker, still engaged | **PERSIST** (energised, not yet disengaged) |
| **disgust** | individual | contamination / violation | **REJECT / withdraw** |
| **joy** | individual progress | value-progress > 0 on a valued outcome | **REINFORCE / approach** |
| **sadness / grief** | individual | attachment/goal lost, un-re-groundable (value-progress < 0) | **DISENGAGE** (low energy) |
| **curiosity** | individual progress | learning-progress > 0 | **ENGAGE** (the 202000 signal) |
| **boredom** | individual | learning-progress → 0, was engaged | **LEAVE** (the 202000 cut) |
| **fulfilment** | **SUPERGRAPH** | agent's action increased the COLLECTIVE's success | **CONTRIBUTE** (deep, low-hedonic) |

**Arousal / valence read-off (the circumplex, integer):** each emotion rule also
exposes `valence` (sign of the governing progress/value signal: +1/0/−1) and
`arousal` (magnitude of the governing surprise/precision signal), so the core set
lands as points on the Russell plane, computed — not asserted.

Action tendencies are INTEGER codes (a fixed enum in the seed) so the emulation
table is gradeable by exact match.

---

## 2. GATES (pre-registered BEFORE any number)

### G1 — EMULATION (appraisal → recognised action tendency)

Given an APPRAISAL (a configuration of the signal-economy attributes on an
`Appraisal` node), the substrate — under `run_rules()`, no Python decision —
produces the RECOGNISED action tendency for each core emotion. Construct **N ≥ 11
canonical appraisals**, one per core emotion (the table above), plus at least a
few **off-diagonal / null** appraisals (a configuration that should fire NO
emotion, or a discriminator pair: fear-vs-anxiety differ ONLY in threat
persistence; anger-vs-frustration differ ONLY in blocker-approachability;
curiosity-vs-boredom differ ONLY in the sign of learning-progress). **PASS iff**
every canonical appraisal yields exactly its table tendency AND exactly one
emotion fires per canonical appraisal (no ambiguous double-fire) AND the null
appraisal fires none. Gradeable: N appraisals → N/N correct tendencies; report
the full confusion outcome.

### G2 — REFERENCE-FRAME + FULFILMENT

Emotions span LEVELS of selection. Build a minimal SUPERGRAPH model: the agent
belongs to a collective (a `Supergraph` node the agent has a `member_of` edge
to), the collective has an integer `success` signal, and the agent's action has a
`supergraph_contribution`. **PASS iff:** (a) **fulfilment fires** for
supergraph-contribution — the agent's action increased the collective's success
(`supergraph_contribution > 0` AND the collective's success rose), producing the
**CONTRIBUTE** tendency; (b) **fulfilment is DISTINCT from joy** — on the SAME
event, joy reads INDIVIDUAL progress and fulfilment reads SUPERGRAPH value, and
there exist events where one fires and the other does not (the value functions
read different reference frames). If the ToM seeds support a self+other model
cleanly, include **one SOCIAL emotion** (e.g. pride = supergraph-contribution
attributed to SELF, observed by other) to show the social frame; **else NAME THE
GAP** (a measured "social emotions need machinery not present" is a valid
landing for that sub-point).

### G3 — HEDONIC / EUDAIMONIC DISSOCIATION (the "parenthood" case)

Happiness (individual value) and fulfilment (supergraph value) DISSOCIATE on an
act that is **individual-costly but supergraph-beneficial**. **PASS iff** on that
act the two signals come APART: individual happiness (individual net
value/progress) goes DOWN while fulfilment (supergraph value) goes UP — measured
as two curves crossing / diverging over the act, the empirical signature of the
two reference frames. Report both curves. (A single act suffices; a small sweep
of individual-cost vs supergraph-benefit is preferred to show the dissociation is
structural, not a single tuned point.)

### G4 — VALUE-SIDE DISORDER GLASS-BOX (ties 199000, understanding-not-judgment)

**Psychopathy = the SUPERGRAPH-VALUE knob at ~0.** The agent still READS others
(ToM/contribution computation intact — `supergraph_contribution` is still
computed) but does NOT VALUE them: a weight `w_supergraph ≈ 0` zeroes the
supergraph value term → fulfilment collapses → the agent instrumentalises
(callous: it acts on individual value alone even when the supergraph is harmed).
**PASS iff** turning the knob DOWN produces the pattern (fulfilment → 0 while
individual value is untouched; supergraph-costly acts no longer suppressed) and
turning it BACK restores it (pure-knob reversal, byte-identical to a
never-lowered agent). Optionally: depression = value suppressed across ALL frames
(individual AND supergraph → flat-negative valence); mania = value inflated.
**AND the state-vs-observation point:** show the substrate's STATE-KNOBS
(`w_supergraph`, the half-lives, the progress signals), OBSERVED behaviourally
(the emitted action tendencies / valence-arousal points), reproduce the
recognised emotion/disorder patterns — i.e. the behavioural "factors" are
SHADOWS of the state-knobs, not primitives.

### G5 — INTEGER-NATIVE + DEFAULT-OFF byte-identity

All emotion rules are integer-native (only `Ashr/IDiv/Abs/Minus/Plus/Times/Max/Min/IfThenElse/Eq/Gt/Lt/Gte/And/Or/Not` — every one already in the DSL; **`term.rs` diff EMPTY**). Audit: zero non-integer cells produced by the emotion
rules. **Default-OFF:** every emotion rule guards on a `HeldEmotionParams.enabled`
node the measure adapter creates ONLY on opt-in; absent it, every existing path
is **byte-identical** (`held_surface` / staleness / curiosity untouched; oracle
`rung7_vision_bench` BEFORE == AFTER).

---

## 3. DISCIPLINE (declared here, enforced at report)

- **Prefer graph-data + EXISTING Terms.** No new Rust. `term.rs` diff EMPTY;
  whole `runners/dsl` diff EMPTY. An emotion is a RULE reading the economy and
  setting an action-tendency attr — never a Python decision. Python is a
  mechanical measure-adapter / seed-builder only (builds nodes/edges, ticks,
  reads attrs).
- **Measure module IMPORT-INERT** (nothing runs at import; `main()` the only
  entry; scoped context only).
- **Engine-semantics gate set (lesson 12)** — this rung touches NO engine, but
  the gate set is run anyway (adapter-only): `test_incremental_match`,
  `test_empty_match_proof`, `test_per_sensor_epoch`, `test_per_area_settlement`,
  `test_eye_binding_projection`, `test_staleness_decay`, `test_demotion_hierarchy`,
  `test_disorder_glassbox`, `test_learning_progress`, `test_dissipation_inference`,
  the eye suite, and `held_surface`. All green.
- **Canonical `.so`** stays `793ce09e…` (seed/Python-only; verify md5 untouched).
- **Oracle** `bash scripts/rung7_vision_bench.sh` BEFORE == AFTER.
  **`source_match` own/shared** reported. **Commit before report.** Do NOT merge
  to main; do NOT touch `VISION_PROTOCOL.md`.

## 4. What would falsify / an honest negative

- An appraisal configuration that maps to TWO recognised tendencies (the core set
  is NOT cleanly separable on these atoms) — reported straight, not patched.
- Fulfilment that requires machinery not present (e.g. no clean supergraph model
  is expressible) — a measured "needs a collective model we don't have" is a
  valid landing.
- Happiness and fulfilment that DON'T dissociate on the parenthood case (the two
  reference frames collapse to one signal) — would falsify the core claim.
- Psychopathy that is NOT a pure knob (lowering `w_supergraph` changes individual
  value too, or restoring it leaves residue) — reported straight.

An honest measured negative on any of these is a valid landing; the deliverable
is the MEASUREMENT behind a protected gate, not a green light.
