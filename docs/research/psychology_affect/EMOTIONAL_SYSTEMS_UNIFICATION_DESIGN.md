# Emotional systems — survey and unification design

**Status: design document, not a PREREG.** No experiment is registered
here; nothing in this document has been built. Written at the user's
explicit request, before any further code, prompted by a concrete
symptom: `sp_choose_utterance` (bigville's speech-act Argmax) needed
hand-authored `warm_aff`/`hostile_aff` coefficients per option
(`BIGVILLE_SOCIAL_EXPERIMENT_1_RESULTS.md` rung 2), then a hand-added
`shared_bucket_count` term (rung 3), and the next asks were "weight this
by mood," then "by disposition too," then the sharp catch: **"disposition
is also the psi layer... this needs to integrate all emotions available
as a single API."** Continuing to hand-add one more coefficient per
decision point is the SAME anti-pattern CLAUDE.md already names and
retired at engine scale ("SHAPES, NOT NUMBERS" §, the 60 count-divided
`1/n` learners finding): a scalar knob invented per subsystem, never
paid off, each one needing its own knob eventually. This document surveys
what already exists (more than expected — most of the needed substrate is
already built and CORRECT, just disconnected) and proposes the shape of
a unification, without committing to Term-level implementation details
yet.

## 1. What already exists

Organized by SCOPE — the axis that actually matters for unification,
since "mood" and "disposition" turn out to be two ends of ONE axis
(transient state vs. stable parameterization of the SAME modulators), not
two unrelated systems.

### 1a. The PSI modulator layer — already canonical, already named this

`seeds/affective_state_core.json`. Its own description: *"Canonical
graph-native affect contract. Every loaded agent owns a neutral
AffectiveState baseline. PSI ModulatorState projects valence, arousal,
resolution, selection threshold, securing, competence, and epoch into
that state."* This is Dörner's PSI theory, explicitly, already built:

- `AffectiveState{valence, arousal, resolution, selection_threshold,
  securing, competence, epoch}` — the canonical per-agent read surface.
- `ModulatorState` — the same six fields, `projects_affect_to` the
  AffectiveState.
- `psi_select_initial_leading_drive` / `psi_switch_leading_drive` — PSI's
  own drive-competition mechanism (a leading drive persists until a
  challenger exceeds it by a held switch threshold — motivation
  selection, not emotion per se, but the same modulator substrate).

**This is already meant to be THE single API.** The word "canonical" is
in its own docstring. The gap is not that it doesn't exist — it's that
almost nothing outside `core_emotions.json` and a partial read inside
`decide_speech` actually uses it.

### 1b. The appraisal-emotion layer — projects INTO 1a, distinct theory

`seeds/core_emotions.json`. Scherer/Lazarus/Frijda appraisal → action-
tendency, NOT PSI — a different, compatible lineage, explicitly
composed over the engine's existing integer signal economy (staleness-
decay threat precision, learning-progress, diminishing-returns value),
zero new Rust. Discrete emotions: `surprise, fear, anxiety, anger,
frustration, disgust, joy, sadness, curiosity, boredom, fulfilment,
pride`. Circumplex read-off: valence = sign of progress/value, arousal =
magnitude of surprise/precision. **Two disposition knobs are ALREADY
wired here**, and this is the one place in the whole survey where
disposition-modulates-emotion is done right, worth copying the shape of
elsewhere:
- `mood_bias` suppresses (depression) / inflates (mania) value across
  BOTH the individual and supergraph reference frames.
- `w_supergraph` near 0 = the "psychopathy" glass-box case: others'
  outcomes are still computed but not VALUED, so fulfilment collapses.
  A pure knob reversal restores it — a disposition trait acting as a
  GAIN on an existing computation, not a separate code path.

`worlds/bigville_ocelot_adapter.py::_ensure_emotional_core` wires
`ModulatorState -projects_affect_to-> AffectiveState`, and
`_update_emotion`/`record_action_outcome`/`_sync_affective_state` push
appraisal outcomes through it. `decide_speech` reads `self.
emotional_state().get("appraisal",{}).get("arousal")` and blends it into
`speaker_arousal` — the ONE existing precedent for "an unrelated decision
consults the canonical mood state," and it's ad hoc (a max-blend inline
in one method, not a reusable pattern).

### 1c. The CAN self-belief network — resident-level, disposition-driven

`worlds/bigville_can_beliefs.py`. Five Concepts per resident
(`trust_mayor`, `claim_credible`, `world_safe`, `self_worth`,
`debtor_trustworthy`), identity fields set as FIXED FORMULAS over
bigville's own drawn disposition params:

```
trust_mayor.identity_field  = (charm_weight - hostile_weight)*0.5
                              + 0.5*(prior_others_trust - 0.5)
claim_credible.identity_field = (claim_weight - 1.0)*0.5 + (w_supergraph - 0.5)
world_safe.identity_field   = 2.0*(prior_world_safe - 0.5)
self_worth.identity_field   = 2.0*(prior_self_worth - 0.5)
```

This is the clearest EXISTING precedent for "disposition = a stable
per-resident param that sets a BASELINE/PRIOR before any evidence
arrives" — exactly the shape the user is asking to generalize. It is
NOT PSI-labeled (no `valence`/`arousal` fields here), but structurally
it's the same idea: `hostile_weight`/`prior_others_trust`/`charm_weight`
are disposition GAINS on a belief, computed once, resident-specific,
never touched again except by real evidence (`record_incident_outcome`).

### 1d. Bigville's own disposition trait table — drawn once, mostly unused elsewhere

`worlds/bigville_town100_world.py::_PARAM_SPEC` (13 params, drawn per
resident from `numpy.default_rng`, `seeds/bigville_cast100.json`):
`charm_weight, w_supergraph, w_spite, hostile_weight, mood_bias, cred_on,
claim_weight, prior_world_safe, prior_others_trust, prior_self_worth,
valence, arousal, resolution_bins`. Usage today:
- `mood_bias`, `w_supergraph` → §1b (core_emotions).
- `charm_weight`, `hostile_weight`, `claim_weight`, `prior_others_trust`,
  `prior_world_safe`, `prior_self_worth` → §1c (CAN network).
- `w_spite`, `cred_on`, `valence`, `arousal` (the raw param, distinct
  from AffectiveState's live `arousal`) → **not read anywhere found in
  this survey outside their own draw** — live, real, generated data with
  no current consumer.
- **None of these 13 reach `_speech_bond`/`sp_choose_utterance` at all**
  — confirmed the exact gap the last three rungs were patching around
  with fresh, unrelated constants (`FAMILIARITY_CAP`, hand-picked
  `warm_aff`/`hostile_aff` per SpeechOption) instead of reading data
  that already existed.

### 1e. The target-scoped social-disposition family — this session's own build

`domains/hate_attribution.py` + `domains/resident_trust.py` +
`domains/envy.py` + `domains/shared_arousal.py`. Per (resident, target)
pair: `regard_for`, `removal_desire_for`, `pity_for`, `admiration_for`,
`devaluation_for`, `controllability_for` (a ToM belief), `competence_for`/
`willingness_for` (trust), `resentment_debt`/`gratitude_debt` (ledgers on
the `TargetPattern` node), `deservingness_belief_for:<domain>`,
`TargetArousal.level` (shared per-target excitation pool, Schachter-
Singer). All plain CAN Concepts (`state`/`external_field`/
`identity_field`), evidenced via `concept_apply_evidence`, crystallizing
via the shared `HATE_STABILITY_THRESHOLD` ladder. **Zero connection to
AffectiveState/ModulatorState** — arousal here is a SEPARATE, per-target
pool (`TargetArousal`), not PSI's own global `arousal` field, and nothing
here reads `valence`/`resolution`/`securing`/`competence` at all.

### 1f. The domain-scoped self-belief family

`domains/can_self_worth_bridge.py` + `domains/self_efficacy.py`.
`self_worth:<domain>` (projection-then-decoupling from the global
CAN `self_worth`), `reparative_desire_for:<domain>`/`withdrawal_
desire_for:<domain>` (guilt/shame consequences), `relative_self_worth`
(peer-comparison log-odds), `self_efficacy_for:<domain>` (Bandura,
explicitly wired into `AffectiveState.competence` via
`sync_competence_to_affective_state` — **the ONE place outside
core_emotions where something writes into the canonical PSI surface**).

### 1g. The preference layer

`domains/shape_fit_preference.py`. Berlyne's inverted-U (Wundt curve)
over `ShapeDecode` fluency + a target-scoped arousal pool (reusing
`shared_arousal.mint_target_arousal`, same as §1e). Citation-compatible
with the appraisal/PSI arousal concept but a structurally separate
computation — no shared node.

### 1h. The declarative personality-theory catalog — inert, held as knowledge only

`seeds/psy_personality.json`. 23 Concepts: Big Five, HEXACO, need for
achievement/affiliation/power, self-determination theory, locus of
control, self-esteem, self-efficacy belief, self-concept clarity,
trait-state distinction, **CAPS (cognitive-affective personality
system — literally the trait × situation interaction framework this
whole document is reaching for)**, five-factor neuroscientific
substrate, heritability, narrative identity. Confirmed (CLAUDE.md's own
Phase 0 note, this session): **no rules, no `match`/`where`/`effects`
anywhere in this file — the agent can STATE these facts if asked, but
none of them compute anything.** A rich, correct theoretical vocabulary
sitting completely unconnected to every executable system above it.

### 1i. Bucket-familiarity — just landed, same shape as everything else

`domains/bigville_disposition_apply.py`'s `ingroup_affinity`/
`outgroup_suspicion` self-priors + `bigville_ocelot_adapter.py::
_speech_bond`'s new third branch (rung 3, this session). Another
resident-level disposition scalar, wired into exactly one place
(`_speech_bond`), the same way `mood_bias` is wired into exactly one
place (core_emotions) and `hostile_weight` into exactly one place (CAN).

## 2. Diagnosis

Every one of §1a–1i is individually well-built, well-cited, and
internally consistent — this is NOT a mess of bad code. The problem is
exactly what the user named: **each system was generalized once, along
one axis, then stopped.** A table of which systems currently READ from
which others:

| System | Reads AffectiveState/ModulatorState? | Reads `_PARAM_SPEC` disposition? | Reads target-scoped Concepts (§1e)? |
|---|---|---|---|
| core_emotions (§1b) | writes it | `mood_bias`, `w_supergraph` | no |
| CAN network (§1c) | no | `charm_weight`,`hostile_weight`,`claim_weight`,`prior_*` | no |
| hate/trust/envy/arousal (§1e) | no | no | (is itself) |
| self_efficacy/self_worth (§1f) | writes `competence` only | no | no |
| shape_fit_preference (§1g) | no | no | no (own arousal pool) |
| speech decision (§1i + prior rungs) | reads `arousal` only, ad hoc | no | no |
| psy_personality (§1h) | — inert — | — inert — | — inert — |

No system reads MORE than one or two of the others. The canonical PSI
surface (§1a) — explicitly built to be the single integration point — is
the LEAST-read node type in the entire survey outside its own source.
This is the same shape CLAUDE.md's own retrospective already diagnosed
for learning rates (60 disconnected `1/n` knobs, "each rate needs a
rate") — here it's disposition/mood knobs instead of rates, but the
generative mistake is identical: **a new subsystem needing "does this
feel warm or hostile" invents its own small local answer instead of
consulting the one place that already knows.**

## 3. Human grounding — automatic appraisal, and what the tails reveal

User's directive: *"emotions should be automatically applied to things
that match — the bolting on of emotions should not be required one by
one — the edges/shapes should be automatic. check how this works in
humans. particularly the tails — disorders and medications and damage
that reduces or enhances emotions."* Checked before revising the
proposal below, not asserted from memory alone.

### 3a. Normal operation: appraisal is a small fixed check-set applied to
### EVERY stimulus automatically, not hand-wired per stimulus type

Scherer's Component Process Model (CPM) — already the appraisal lineage
`core_emotions.json` cites — is explicitly built this way: a SMALL,
FIXED sequence of appraisal checks (novelty, intrinsic pleasantness,
goal relevance, coping potential, norm/self compatibility) runs on
WHATEVER stimulus arrives; the resulting profile of check outcomes, not
a per-stimulus lookup table, determines which emotion results (Scherer
2001, "Appraisal considered as a process of multilevel sequential
checking"). No stimulus is exempt and none needs individual wiring —
the checks themselves are the generalization.

Below the level of deliberate appraisal, LeDoux's amygdala pathway
(LeDoux 1996, *The Emotional Brain*) and Öhman & Mineka's "fear module"
(2001) describe a genuinely AUTOMATIC, template-matching system: a
small set of learned associative templates (feature patterns, not
per-object hand-coding) fire on ANY matching input, faster than
conscious appraisal and resistant to deliberate override. This is
structurally a graph/pattern match, not an enumerated case list — the
closest existing analogue in this codebase is the sd-loop's own
`sd_recognize`/`ShapeDecode` (decode against a held, growable codebook),
not a hand-authored `if stimulus == X` branch.

Bower's mood-congruent processing (1981, already cited in this
codebase's `shape_fit_preference`/Phase-B lineage) is the clearest
precedent for "automatic, not per-decision": mood was modeled as a NODE
in an associative semantic network, and its activation SPREADS to
congruent nodes via the network's own edges — nothing decides,
per-retrieval, "should mood affect this memory"; the coupling is
structural (shared edges), not procedural (a hand-written rule per
memory type). Russell's Core Affect model (2003) generalizes this
further: valence+arousal are modeled as an ALWAYS-PRESENT continuous
2D backdrop, and any specific emotional episode is that backdrop being
ATTRIBUTED to a particular object as the object is appraised — the
ambient state is default-present everywhere; a stimulus doesn't need to
"opt in" to being affect-eligible.

**Translation for this codebase**: the human default is closer to "every
appraised object inherits an ambient modulator state via shared graph
structure" than to "each decision type is manually taught to consult
mood." §4 below revises the proposal accordingly — the coupling should
be a RULE that matches any node carrying a small affinity tag, firing
automatically wherever that shape exists, not a per-decision Python
call site.

### 3b. The tails — clinical/pharmacological "knockouts" as natural
### experiments, and what they converge on

Every case below is a real, cited clinical or pharmacological
phenomenon that dials emotional processing up or down. Read together,
they converge on ONE architectural claim: **the human system is
normally an automatic, always-on coupling between a shared affect
substrate and appraised objects, and every disorder/drug/lesion that
changes emotional intensity does so by adjusting a SMALL number of
GAINS on that shared substrate — never by rewriting the coupling logic
object-by-object.** This is strong convergent evidence for the
architecture in §3a, and against per-decision hand-tuning.

- **vmPFC damage / the Somatic Marker Hypothesis** (Damasio 1994,
  *Descartes' Error*; Bechara, Damasio, Tranel & Damasio 1994/1997, the
  Iowa Gambling Task). Patients with ventromedial prefrontal damage
  (the Phineas Gage lineage; patient "EVR") keep intact IQ and abstract
  reasoning but LOSE the automatic affective tag normally attached to
  each decision option, producing catastrophic real-world choices
  despite flawless deliberate logic. **This is the single most directly
  relevant case**: it shows the DEFAULT human architecture already IS
  "every option gets an automatic affect-weighted tag before deliberate
  reasoning," and that damage REMOVES the automatic coupling specifically
  — forcing costly, slow, deliberate evaluation per option instead
  (measurably worse). The user's request — automatic, not bolted-on
  one-by-one — is what the INTACT system does; hand-wiring per decision
  is closer to modeling the LESIONED case.
- **Amygdala damage** (Adolphs, Tranel, Damasio, Damasio 1994; Feinstein,
  Adolphs, Tranel & Damasio 2011, patient SM). Bilateral amygdala
  damage produces a SPECIFIC loss of fear (SM could not be induced to
  feel fear by snakes, haunted houses, or a gun) while other emotions
  stayed largely intact — a clean dissociation showing the substrate is
  MODULAR (separate pathways per emotion family, e.g. insula for
  disgust), not one monolithic dial. Directly supports keeping distinct
  target-scoped Concepts per emotion family (regard/pity/admiration/
  devaluation as separate Concepts, §1e) rather than collapsing
  everything into a single scalar — modularity is the correct target
  shape, not a limitation to unify away.
- **Depression / mania** (Beck's cognitive triad; standard DSM
  affective-disorder literature). A GLOBAL valence bias across every
  appraisal — already exactly `mood_bias` in `core_emotions.json`
  ("suppresses (depression) / inflates (mania) value across BOTH
  frames"). The one place in this codebase's own survey that already
  matches the tails evidence precisely.
- **Psychopathy** (Blair 2005, "Responding to the emotions of others";
  Hare's PCL-R literature). A SELECTIVE reduction in responsivity to
  OTHERS' distress specifically, with instrumental/reward learning
  intact — not a global flattening. `w_supergraph≈0` in this codebase
  ("reads others... but does not VALUE them... pure-knob reversal
  restores it") gets the SIGN right, but the design doc's own citation
  is DIMENSIONAL literature (PCL-R scores span a range, not a taxon) —
  and until `SUPERGRAPH_WEIGHT_MAGNITUDE_PREREG.md`, the CODE encoded a
  taxon: `em_fulfilment_value` was a sign gate (`Gt(w_supergraph,0)`),
  so every `w>0` read as behaviorally identical regardless of how much
  the agent actually valued the collective — "a clean single-pathway
  gain" was the design intent, not yet what the rule did. Fixed: the
  design doc was right and the code was wrong.
- **Flat affect (schizophrenia negative symptoms)**. Global blunting of
  expressed/experienced INTENSITY specifically — an arousal/reactivity
  gain, not a valence-signed bias (unlike depression) — evidence that
  valence-gain and arousal-gain are separately dial-able, matching
  `AffectiveState`'s own separate `valence`/`arousal` fields.
- **SSRIs and pharmacological emotional blunting** (Price, Cole &
  Goodwin 2009, systematic review — "Emotional side-effects of
  antidepressant drugs"). A well-documented clinical side effect,
  independent of the depression itself resolving: reduced reactivity to
  BOTH positive and negative stimuli. Another global reactivity-gain
  case, this time pharmacological rather than lesion-based — same
  architectural shape.
- **Propranolol and emotional memory** (Cahill, Prins, Weber & McGaugh
  1994, *Nature*). A beta-blocker blocking peripheral epinephrine
  specifically blunts the AROUSAL-driven enhancement of memory for
  emotional material, without blocking the memory or the appraisal
  itself — a clean pharmacological isolation of "arousal amplifies
  downstream salience" as ONE separately-blockable coupling, exactly the
  `arousal_gain × speaker_arousal × hostile_aff` term already found (and
  left deliberately un-tuned) in `sp_choose_utterance`.
- **Alexithymia** (Nemiah & Sifneos 1970 onward). Difficulty identifying/
  describing one's OWN emotions, while physiological/behavioral affect
  responses can remain largely present — a dissociation between the
  computed affect state and the introspective REPORT of it. Supports
  this codebase's own existing framing (`core_emotions.json`'s own
  docstring: *"Understanding not judgment; the FUNCTIONAL regulator, NOT
  a claim to felt qualia"*) — the computed `AffectiveState` and any
  future narrative self-report surface are legitimately separate graph
  paths, and should stay separate.

### 3c. What this settles, going into §4

1. The coupling must be AUTOMATIC and structural (matched by shape,
   §3a) — not a per-decision-type Python call site, which is closer to
   modeling vmPFC damage than the intact system.
2. Modularity is correct, not a defect — separate target-scoped emotion
   Concepts (§1e) should stay separate; unification means a SHARED
   coupling MECHANISM, not one collapsed scalar.
3. The tails converge on a SMALL, finite gain vocabulary, not one per
   decision: a global valence gain (mood_bias, already built), a global
   arousal/reactivity gain (not yet built — the SSRI/flat-affect/
   propranolol case names it directly), and per-pathway selective
   gains (amygdala/fear, w_supergraph/collective-value, both precedented
   already). §4 should enumerate a similarly small, named gain set
   rather than leave it open-ended.
4. Computation and self-report are separably wired (alexithymia) — the
   unification target is the COMPUTATION layer; any future "how do you
   feel about X" reflective surface reads from it but is not required to
   be the same graph path.

## 4. Unification proposal (shape, not yet a build plan)

### 4a. Disposition IS PSI parameterization, not a fourth system

The user's own framing, confirmed by §1c and §1b's `mood_bias`/
`w_supergraph`: a disposition trait is not a separate kind of thing from
a PSI modulator — it is a **stable per-resident GAIN or BASELINE on one
of PSI's own modulator dimensions**, drawn once at generation time,
never updated by evidence (unlike the modulator's live STATE, which
moves continuously). Concretely:

- `hostile_weight` → gain on how strongly `arousal` converts into a
  hostility-flavored reading, wherever arousal is consulted (currently:
  only `sp_choose_utterance`'s undifferentiated channel, hand-tuned per
  rung; should be: ANY decision that reads arousal).
- `prior_others_trust`/`charm_weight` → baseline/floor on
  trust-flavored valence, already correctly shaped for `trust_mayor`
  (§1c); should ALSO seed `resident_trust.py`'s `competence_for`/
  `willingness_for` cold-start (named as a real gap in
  `RESIDENT_TRUST_PREREG.md` itself: "Optionally consumes Phase B's
  preference signal as a cold-start prior... named, not required" — this
  IS that missing prior, already drawn, never connected).
- `mood_bias`/`w_supergraph` → already correctly wired (§1b) — the
  MODEL for how every other trait should be wired, not a special case.
- `w_spite`, `cred_on` → currently unused ANYWHERE; likely candidates
  for the target-scoped devaluation/removal_desire route (§1e) and the
  CAN `claim_credible` gate respectively, but this document does not
  commit to that mapping — a build-time decision, not a design one.

### 4b. Mood is PSI's live state; the ONE canonical read surface stays AffectiveState

No new "mood node" — `AffectiveState`/`ModulatorState` (§1a) already IS
this and is already described as canonical. The fix is making every
OTHER system actually read it, the same way core_emotions writes it and
`self_efficacy` writes `competence` into it (§1f) — that's the pattern
to generalize, not invent fresh.

### 4c. The single reusable coupling shape — a RULE matching a SHAPE, not a Python call site

Per §3a-§3c: the coupling must be automatic (fires wherever the shape
exists) and structural (a small, shared gain vocabulary), not "every
decision type gets manually taught to consult mood." Concretely, this
means the coupling is a SEEDED RULE with a `match` clause over a small,
generic TAG shape — e.g. any node carrying `affinity_valence`/
`affinity_arousal` attrs, regardless of whether it's a `SpeechOption`, a
target-scoped Concept (§1e), or something not yet built — NOT a Python
method that a new subsystem's author remembers (or forgets) to call.
Every decision surveyed above that wants to be affect-sensitive is
structurally the SAME operation: **`value(option) = base_value(option) +
Σ modulator_i × option_affinity_i`**, where `option_affinity_i` is a
small, DATA-level tag (this is literally what `warm_aff`/`hostile_aff`
already are on `SpeechOption` nodes, and what `regard`/`admiration`/
`devaluation` already are as evidence signs in `_apply_social_aspects`).
The generalization is: instead of every subsystem (Argmax over
SpeechOptions, evidence sign on a target Concept, a CAN identity-field
formula) hand-writing its own version of this sum in its OWN rule, there
should be ONE reusable Rule (or a small, composable Term) — matching
`NodesWhere(has "affinity_*" attrs)` generically — that any seed
AUTHOR opts into purely by tagging their option/Concept nodes with the
right DATA attrs, the same way `Argmax`/`IfThenElse` are already reusable
DSL primitives many seeds compose differently, and the same way §3a's
appraisal checks apply to whatever stimulus shows up rather than being
re-taught per stimulus.

Two levels this composes at, matching the mood/disposition split
(§3c point 3 — a SMALL, named gain set, not one per decision):
- **Dynamic** (mood): read `AffectiveState`'s live fields directly.
- **Stable** (disposition): read the resident's own `_PARAM_SPEC`-drawn
  disposition attrs (currently sitting inert on `bigville_cast100.json`
  records, never copied onto the Ocelot-side agent node at all for most
  of them — a real, first, small wiring gap: `BigvilleOcelotResident`
  would need these attrs on `self.agent` or `self.personality`, the
  same way `ingroup_affinity` already rides in via `personality.get(...)`).
- Named gain candidates directly from §3b's tails, not invented fresh:
  a global valence gain (`mood_bias`, already correct), a global
  arousal/reactivity gain (new — the SSRI/flat-affect/propranolol
  evidence names it), and per-pathway selective gains keyed to WHICH
  Concept family a tagged node belongs to (`hostile_weight` → the
  hate/devaluation family specifically, mirroring the amygdala's
  fear-specific dissociation rather than one global "badness" dial).

### 4d. What does NOT change

The target-scoped/domain-scoped Concept families (§1e, §1f) stay exactly
as built — they are not being replaced. The proposal is that their
EVIDENCE APPLICATION and the DECISIONS that consult them (speech, future
action-selection) gain an ADDITIONAL modulation term reading the shared
PSI surface, composed alongside — not instead of — the real,
incident-driven evidence that already correctly drives them
(confirmed working end-to-end in `BIGVILLE_SOCIAL_EXPERIMENT_1_
RESULTS.md`). Mood/disposition should shade a decision, not overwrite a
real relationship history — the same "familiarity is a weak prior, not
a strong bond" cap discipline rung 3 already established for bucket
membership applies here too.

## 5. Explicitly deferred — not decided by this document

- Exact Term/Rust shape of the reusable coupling (§4c) — whether it's a
  new DSL Term, a composable Rule-effect pattern, or purely
  data-conventions over existing Terms (`Attr`/`Times`/`Plus` composed
  the same way `sp_choose_utterance` already does by hand). Needs a
  build-time investigation into what the DSL already supports before
  committing.
- Which of the 4 currently-unused `_PARAM_SPEC` traits (`w_spite`,
  `cred_on`, raw `valence`, raw `arousal`) map to which modulator/
  decision — named as candidates in §4a, not assigned.
- Migration order — whether to wire the speech-decision path first
  (since it's the one with three already-hand-patched rungs demanding
  this), or start from the target-scoped family (§1e), or from making
  `BigvilleOcelotResident` copy the full `_PARAM_SPEC` set onto its own
  agent/personality at `seed_character` time first (a prerequisite
  either way — most of these traits currently never reach the Ocelot
  side of the adapter at all for cast-100 residents, the same "identity
  never gets seeded automatically" gap named in
  `BIGVILLE_SOCIAL_EXPERIMENT_1_RESULTS.md`'s own out-of-scope list).
- Whether `psy_personality.json`'s inert Big Five/HEXACO/CAPS catalog
  should EVER become executable, or stays purely declarative knowledge
  the agent can discuss but not compute from. Out of scope for the
  functional-modulation goal this document addresses.

## 6. Files surveyed

`seeds/affective_state_core.json`, `seeds/core_emotions.json`,
`seeds/psy_personality.json`, `worlds/bigville_can_beliefs.py`,
`worlds/bigville_town100_world.py` (`_PARAM_SPEC`),
`domains/hate_attribution.py`, `domains/resident_trust.py`,
`domains/envy.py`, `domains/shared_arousal.py`,
`domains/can_self_worth_bridge.py`, `domains/self_efficacy.py`,
`domains/shape_fit_preference.py`, `domains/bigville_disposition_apply.py`,
`worlds/bigville_ocelot_adapter.py`, plus every PREREG/RESULTS doc in
`docs/research/psychology_affect/` produced this session.
