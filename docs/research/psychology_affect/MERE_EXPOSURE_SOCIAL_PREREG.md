# MERE-EXPOSURE × INITIAL-VALENCE — pre-registration (block 293000)

**Status: PRE-REGISTRATION. Committed BEFORE the confirmatory adapter/test.** The
predicted initial-valence × exposure grid + failable controls below are computed
ANALYTICALLY from the substrate's OWN confirmed update law — the CAN belief-update
primitive `concept_apply_evidence` (a flat additive step on a Concept's
`external_field`) relaxed by the engine's discrete-asynchronous 3-state rule
(`seeds/can_native_reimplementation.json`'s `can_native_update_3state`, under
`run_rules()`). The confirmatory adapter (`domains/mere_exposure_world.py`) must
reproduce this grid; any deviation is reported straight (produced ≠ oracle is
either a mapping error to fix or an early sign of the flaw described in §7).

> **HONEST NOTE ON THE ORACLE (read first).** The per-encounter step size
> (`+0.3` on `external_field` per positive encounter at the default plasticity
> `alpha=0.3`) and the discrete-3-state crossing threshold (`≈0.366` at
> `temperature=1.5`) are ENGINE constants — the first is `concept_apply_evidence`'s
> own additive step; the second is this engine's already-measured 3-state
> threshold (`DOMAIN_SELF_WORTH_PROJECTION_RESULTS.md` §2 pt 5). They were read
> from the running substrate at prereg time, not fit to a target. The oracle
> arithmetic in §4 is then pure pen-and-paper over those two constants. The
> confirmatory §5 grid follows from that arithmetic; the adapter run must
> reproduce it exactly.

## 0. Seed claim

Block **293000** (range 293000–293999) is RESERVED for hygiene / successor
safety. **No new seed is authored by this rung** (see §8), so no seed integer is
drawn and `scripts/seed_claim.py` need not be run — there is nothing to collide.
The adapter reuses the EXISTING, already-landed seeds by import
(`seeds/can_native_reimplementation.json`, `seeds/can_decay_identity.json` via
`can_self_worth_bridge.ensure_can_seed`; `seeds/shared_arousal.json`,
`seeds/hate_attribution.json`, `seeds/qualia_space.json`). This mirrors the
trait-anxiety rung's own "no new seed file to load" posture (block 292000).

## 1. The idea

The **Zajonc mere-exposure effect** is one of social psychology's most robustly
replicated findings: repeated exposure to a stimulus, with no reinforcement,
increases liking for it (Zajonc 1968, *J. Personality & Social Psychology*
Monograph Supplement 9(2, pt.2):1–27; Bornstein 1989 meta-analysis, *Psychological
Bulletin* 106(2):265–289 — a positive, decelerating exposure→affect curve across
200+ studies). The crucial **BOUNDARY CONDITION** is that this does NOT hold for
initially-DISLIKED / unpleasant stimuli: repetition raises FAMILIARITY for
everything, but only NEUTRAL and MILDLY-POSITIVE stimuli gain LIKING; genuinely
unpleasant ones do not warm (e.g. the odor-repetition study, *Frontiers in
Psychology* 2015, "Familiarity and liking following repeated exposure to odors":
after repetition all odors became more familiar, but only neutral/mildly-pleasant
odors gained pleasantness while unpleasant ones were unaffected). The
scientifically important signature is therefore the **EXPOSURE × INITIAL-VALENCE
INTERACTION, NOT a bare main effect of exposure**.

This rung asks whether the qualia/attitude substrate REPRODUCES that interaction
MECHANICALLY: does repeated POSITIVE contact with a target warm a NEUTRAL prior
quickly, while a NEGATIVE prior RESISTS warming — purely as a consequence of the
grounded CAN belief-update law and the discrete 3-state relaxation, with no Python
deciding the liking?

This is a **CAPABILITY / mechanism demonstration — the substrate reproduces the
mere-exposure × initial-valence DISSOCIATION as an emergent consequence of its own
grounded affect/attitude machinery — NOT an empirical claim about real humans.**
The wet result is cited to fix the target the mechanism must hit; the contribution
is that the negativity-bias asymmetry falls out of the belief-update dynamics, not
that we have measured a person. Synthetic-mechanism status and any benchmark
meaning are reported separately.

### The honest reframe (a pre-registered DESIGN DECISION, not a hidden limit)

The substrate's per-target regard is a **DISCRETE 3-state {−1, 0, +1} unit** (the
marginal ⟨σ⟩ of the CAN Concept). It is NOT a graded scalar. Consequently:

- **We do NOT predict, and CANNOT predict, a graded positive-decelerating
  MAGNITUDE curve on a single regard unit.** From neutral, once enough positive
  evidence accumulates the state jumps to `+1` and SATURATES (flat at `+1`
  thereafter). Predicting a decelerating magnitude curve here would be
  unfalsifiable-by-construction — a fake.
- **We reproduce the exposure × initial-valence interaction as CROSSING
  LATENCY:** the NUMBER of positive encounters required for the regard state to
  first reach `> 0`. A neutral prior crosses fast; a negative prior crosses only
  after many more positive encounters, and a deep-enough negative prior does not
  cross within a fixed exposure budget at all. That asymmetry-in-crossing-latency
  IS the boundary condition, expressed discretely.
- **The discrete regard is reported as a REPRESENTATIONAL LIMIT / finding, not
  smoothed over.** The `external_field` accumulator underneath moves linearly and
  is reported too (the mechanism's real graded observable), but the FELT/attitude
  quantity the human effect is about — liking sign — is the discrete state, and we
  report it as such. **Because that accumulator is a flat linear climb against a
  fixed threshold, this rung claims only the WEAK (latency) form of the boundary
  condition, not a slope-asymmetric negativity bias — see §2b for the triviality
  confound and the honest scope.**

## 2. Substrate mapping (grounded in the confirmed path — used verbatim)

The confirmatory adapter is a thin wrapper over the SAME confirmed path
`domains/hate_attribution.py` already exposes; nothing new is computed in Python.

- **EXPOSURE ↔ repeated `record_hate_incident(inner, mt, pat, negative=False)`** —
  ONE positive (non-harmful) encounter with the target (mere exposure). Internally
  it mints an `IncidentReport`, lets the seeded rules derive the attribution, then
  applies `concept_apply_evidence(regard_for, +1.0, alpha)` and `run_rules()`. The
  regard state is PRODUCED by the engine's own relaxation, never hand-set.
- **LIKING ↔ the tracked `regard_for` Concept's discrete `state` sign**
  (`+1` = warmed / likes; `0` = neutral; `−1` = disliked) — the marginal ⟨σ⟩ the
  3-state rule relaxes to. `reg = next(iter(inner.neighbours(pat, "tracks_concept")))`.
- **FELT QUALITY (qualia valence) ↔ the `dynamical:valence` coordinate** of the
  regard Concept's qualia signature:
  `[t for t in concept_signature(inner, reg) if t[0].startswith("dynamical:")]`
  (`seeds/qualia_space.json` loaded). At `state=+1` this yields
  `('dynamical:valence', 'field', 1)`; at `state=−1`, value `−1`; at `state=0` the
  valence axis is ABSENT (no `dynamical:valence` tuple). The felt-quality read must
  TRACK the produced state sign at every step (see §7 flaw iii).
- **INITIAL VALENCE ↔ the pre-exposure `external_field` of `regard_for`**, set only
  through the SAME confirmed path:
  - `neutral` — no prior encounters (`external_field = 0`).
  - `negative_noncryst` — a small number of harm encounters
    (`record_hate_incident(..., negative=True)`) that push the state to `−1`
    without a deep accumulated field.
  - `negative_cryst` — MANY / high-plasticity harm encounters that drive the
    accumulated negative `external_field` deep AND crystallize the target's
    `TargetPattern` (`crystallized == 1`, a `has_hate` node minted). See §2a for
    the honest scope of "crystallized" here.
- **PERSONALITY (optional) ↔ per-agent `base_alpha` (belief plasticity, Dweck's
  fixed↔growth axis) and `spite_gain`** — the SAME per-agent trait params
  `hate_attribution.record_hate_incident` already reads from data. They rescale the
  per-encounter step and thus the crossing latency; they are world setup (data),
  never a decision.

### 2a. Honest scope of `negative_cryst` — the crux this rung had to resolve

Two distinct "commitment" quantities exist and MUST NOT be conflated:

1. the target `TargetPattern.crystallized` flag (a `has_hate` node minted by the
   seeded stability gate after repeated confirmed harm), and
2. the regard Concept's own `identity_field` (the CAN standing/committed prior,
   entering the relaxation as `h_eff = external_field + identity_field`).

**MEASURED at prereg time (the crux):** `record_hate_incident` moves regard via
`concept_apply_evidence`, which writes `external_field` ONLY; the hate seed never
touches `identity_field`, and the native engine only READS it. So through the
confirmed path, a `negative_cryst` target reaches `crystallized == 1` while its
regard `identity_field` STAYS `0.0`. **There is therefore no categorical,
identity-level PERMANENT block reachable on this path.** What a `negative_cryst`
target has is a DEEP accumulated negative `external_field`. The boundary condition
it produces is QUANTITATIVE: warming must first neutralise the accumulated negative
field (`≈0.3` recovered per positive encounter) before it can cross the `+0.366`
threshold, so a deep-enough prior does NOT cross within a fixed exposure budget.
**This is registered as a finding, not hidden:** the substrate reproduces the
boundary condition as a *depth-scaled latency that can exceed any fixed budget*,
NOT as an identity-level lock — because the confirmed attitude API cannot commit
`identity_field` away from 0. (A future rung that wires `identity_field` directly
could test a true permanent lock; this rung does not claim one.)

### 2b. The TRIVIALITY confound — checked, and the honest scope of the claim

A fair objection: **is this effect trivial?** Two trivial mechanisms would make
the "warming" uninteresting, and both are addressed head-on.

- **(A) A biased default baseline.** If the neutral regard started at a slightly
  NEGATIVE log-odds / prior baseline, then "known but not-yet-rated" stimuli would
  enjoy a free head-start toward liking and the effect would be a baseline artefact,
  not exposure. **MEASURED at prereg time — REFUTED for this path:** a fresh
  `regard_for` Concept reads `external_field = 0.0`, `identity_field = 0.0`,
  `state = 0.0` after relaxation, and carries NO log-odds / prior-baseline attribute
  at all (its only attrs are `name`, `state`, `external_field`, `identity_field`,
  `affinity_warm`). The accumulator is SYMMETRIC about a true zero: 2 positive
  encounters give `+0.6 / state +1`, 2 negative give `−0.6 / state −1` — mirror
  images. So on the `regard_for` path there is no negative-default advantage; the
  neutral condition's fast crossing is not a baseline trick. *(This differs from a
  peer-comparison / relative-self-worth channel, whose log-odds baseline CAN be
  offset — that channel is NOT used here.)*

- **(B) A fixed-slope linear climb (the more serious objection).** Because the
  underlying update is a flat additive accumulator (`+0.3`/encounter) against a
  fixed threshold, the "negative resists" result is, mechanically, just **"a
  negative prior starts further below the threshold and climbs the SAME slope."**
  That is MIRROR-SYMMETRY of a linear climb — NOT the qualitative negativity bias
  the human boundary condition reports (unpleasant stimuli warm *less per exposure*,
  not merely *from further away*). **This is registered as a genuine limitation, not
  hidden.** What this rung legitimately demonstrates is the WEAK form of the boundary
  condition: initial valence sets crossing latency, and a deep-enough negative prior
  does not cross within a fixed budget. What it does NOT demonstrate is a STRONG,
  slope-asymmetric negativity bias — because the only commitment quantity that could
  produce asymmetric resistance (`identity_field`, entering as `h_eff =
  external_field + identity_field` and NOT decaying like accumulated evidence) is
  unreachable through the confirmed `record_hate_incident` API (§2a). A rung that
  wires `identity_field` directly could test the strong form; **this rung explicitly
  does not claim it.** The §7 flaw (i) check (crystallized warms as fast as neutral)
  detects only the total absence of the weak effect, not the weak-vs-strong
  distinction — that distinction is stated here as scope, so no reader mistakes the
  linear-latency result for a slope-asymmetric negativity bias.

## 3. Fixed protocol constants (pre-registered)

| constant | value | role |
|---|---|---|
| `temperature`        | 1.5   | Microtheory temp ⇒ 3-state crossing threshold `≈0.366` |
| `discrete_mode`      | `3state` | regard is the discrete {−1,0,+1} marginal |
| `base_alpha`         | 0.3   | default belief plasticity ⇒ `+0.3` `external_field` step per positive encounter |
| positive evidence    | `+1.0`| `record_hate_incident(negative=False)` signal |
| harm evidence        | `−1.0`| `record_hate_incident(negative=True)` signal |
| exposure budget      | 30    | positive encounters applied per condition |
| crossing threshold   | `≈0.366` | state flips to `+1` at the first encounter with `external_field > 0.366` |

**Per-encounter law (the engine's, read verbatim):**
`external_field ← external_field + alpha·evidence`; the 3-state state is `sign`
of `external_field` once `|external_field| > 0.366`, else `0`.

### The three initial-valence conditions (pre-registered recipes)

| condition | seeding recipe (harm encounters) | pre-exposure `external_field` | `crystallized` |
|---|---|---|---|
| `neutral`            | none                                   | `0.0`  | 0 |
| `negative_noncryst`  | 2 × `negative=True` @ alpha 0.3        | `−0.6` | (pattern gate may fire; regard field shallow) |
| `negative_cryst`     | many/high-alpha `negative=True` (deep field)| `≤ −3.0` (deeper ⇒ later/never) | 1 |

## 4. The analytic oracle (pure arithmetic over the engine constants)

```python
ALPHA_STEP = 0.3          # concept_apply_evidence step at base_alpha=0.3
THRESHOLD  = 0.366        # engine's 3-state crossing threshold at temperature=1.5

def external_field_after(initial_ext, n_positive, step=ALPHA_STEP):
    # each positive encounter adds +step (mirrors concept_apply_evidence)
    return initial_ext + step * n_positive

def regard_state(ext, thr=THRESHOLD):
    # the discrete 3-state marginal: sign once past threshold, else 0
    if ext >  thr: return +1
    if ext < -thr: return -1
    return 0

def crossing_latency(initial_ext, budget=30, step=ALPHA_STEP, thr=THRESHOLD):
    # first positive-encounter count n at which regard_state > 0; None if never
    for n in range(1, budget + 1):
        if regard_state(external_field_after(initial_ext, n)) > 0:
            return n
    return None
```

`crossing_latency` returns the predicted number of positive encounters to first
reach `regard_state > 0` (liking) — the discrete crossing latency that IS the
exposure effect. `None` = does not cross within the budget (the boundary
condition's strong form).

Closed form: `latency = ceil((thr − initial_ext) / step)`, capped/None past
`budget`. With `thr=0.366`, `step=0.3`: `neutral (0) → ceil(0.366/0.3)=2`;
`−0.6 → ceil(0.966/0.3)=4`; `−0.9 → 5`; `−3.0 → ceil(3.366/0.3)=12`;
`−7.2 → 26`; `−9.0 → ceil(9.366/0.3)=32 > 30 → None`.

## 5. Predicted initial-valence × exposure grid (ANALYTIC — deterministic)

Regard `state` (and `dynamical:valence`, in parentheses; `∅` = valence axis
absent) after `n` positive encounters. The **crossing latency** column is the
headline. `qval` ALWAYS equals `state`'s sign (or `∅` at state 0) — §7 flaw iii.

| initial valence (pre-ext) | n=1 | n=2 | n=4 | n=5 | n=12 | n=26 | n=30 | **crossing latency** |
|---|---|---|---|---|---|---|---|---|
| **neutral** (0.0)                    | 0 (∅) | **+1 (1)** | +1 | +1 | +1 | +1 | +1 | **2** |
| **negative_noncryst** (−0.6)         | −1 (−1) | 0 (∅) | **+1 (1)** | +1 | +1 | +1 | +1 | **4** |
| **negative_cryst / shallow** (−0.9)  | −1 | −1 | 0 | **+1 (1)** | +1 | +1 | +1 | **5** |
| **negative_cryst / mid** (−3.0)      | −1 | −1 | −1 | −1 | **+1 (1)** | +1 | +1 | **12** |
| **negative_cryst / deep** (−7.2)     | −1 | −1 | −1 | −1 | −1 | **+1 (1)** | +1 | **26** |
| **negative_cryst / very deep** (−9.0)| −1 | −1 | −1 | −1 | −1 | 0 | 0 | **None (>30)** |

Monotone as required: deeper initial negativity ⇒ strictly longer crossing
latency, up to non-crossing within the budget.

## 6. The INTERACTION prediction (explicit)

- **Crossing latency DEPENDS ON initial valence — the boundary condition.** A
  NEUTRAL prior crosses to liking in **2** positive encounters; a NEGATIVE prior
  resists, crossing only after **4, 5, 12, 26** encounters as the prior deepens,
  and a DEEP negative prior does **NOT cross within 30**. This is the mere-exposure
  × initial-valence INTERACTION expressed as latency.
- **Exposure warms every non-crossed condition monotonically** (the
  `external_field` climbs `+0.3`/encounter in ALL conditions) — the FAMILIARITY /
  accumulation side is present everywhere, exactly as the odor study found
  familiarity rising for all stimuli.
- **But LIKING (the discrete state / qualia valence) crosses to positive fast for
  neutral and slowly-or-never for negative** — the pleasantness side is gated by
  initial valence. Rising exposure has a large early effect for neutral and a
  delayed-to-absent effect for a committed negative: **an INTERACTION, not a bare
  main effect of exposure.**

## 7. Falsifier and what a substrate FLAW would look like

- **FALSIFIER (the effect must depend on the evidence update).** Freeze the update:
  set `base_alpha = 0` (equivalently do not apply the `concept_apply_evidence`
  step). Then `external_field` never moves, `regard_state` never changes, and there
  is **NO exposure effect in ANY condition** (neutral never crosses; negative never
  recovers). **MEASURED at prereg time — confirmed:** with `base_alpha=0`, neutral
  held `state=0 (ext=0.0)` across 5 encounters and a seeded negative held
  `state=−1 (ext=−0.9)` across 10. If the crossing SURVIVES with the update frozen,
  the effect is not coming from the belief-update pathway and the claim is false.
- **WHAT A SUBSTRATE FLAW WOULD LOOK LIKE.**
  - (i) **A `negative_cryst` target warms just as fast as neutral** (same crossing
    latency) ⇒ negativity-bias / accumulated-commitment MISSING ⇒ the boundary
    condition is NOT reproduced (bare main effect only). Reported straight.
  - (ii) **The `neutral` condition does NOT cross** within the budget ⇒ no
    mere-exposure effect at all ⇒ the warming pathway is dead.
  - (iii) **The qualia valence does not track the produced regard state** (e.g.
    `dynamical:valence = +1` while `state ≤ 0`, or absent while `state = +1`) ⇒ the
    felt-quality read is DISCONNECTED from the dynamics ⇒ the qualia mapping is
    decorative, not grounded. Reported straight.

## 8. Files (all additive, mere_exposure_ / MERE_EXPOSURE_ prefixed)

- `docs/research/psychology_affect/MERE_EXPOSURE_SOCIAL_PREREG.md` — this
  pre-registration.
- `domains/mere_exposure_world.py` — the mechanical world adapter (ingest →
  `record_hate_incident`/`run_rules` → read; NO Python computes the liking).

### Seed / isolation choice

**No new seed is authored.** The adapter reuses the EXISTING, already-landed seeds
by import: `ensure_can_seed` (the native CAN engine + decay/identity rules),
`seeds/shared_arousal.json`, `seeds/hate_attribution.json`, and
`seeds/qualia_space.json`. Every one is loaded only when the adapter is
instantiated (opt-in). Because there is NO new seed file, `load_all_seeds` / the
base tree is **byte-identical when the adapter is absent** — the same posture as
the trait-anxiety rung (block 292000), which likewise authored no seed. Block
293000 is reserved for successor safety only.

## 9. Discipline

Agent = graph; world = mechanical adapter. The adapter only SETS node attrs /
drives encounters through `record_hate_incident` (which itself only calls
`concept_apply_evidence` + `run_rules()` over the seeded rules) and READS the
produced `regard_for.state` + its `concept_signature` qualia coordinates. No
`graph_rewrite.run` / `_match` / `_apply` / `make_rule`; no `if/else` over graph
state selecting the emotion/liking; no reward/punishment shaping (a positive
encounter is a fixed `+1.0` evidence signal, never a learned reward). NO Rust
(`runners/dsl` untouched); `_native.abi3.so` untouched; toolbox solvers
(`can_junction_tree.py`, `can_native_bp.py`) untouched; the FROZEN seeds
(`can_native_reimplementation.json`, `shared_arousal.json`) are loaded and consumed
read-only, never edited.

Do NOT merge to main; do NOT write the ledger row; NO git commit.
