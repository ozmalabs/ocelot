# Qualia-as-navigation — coherence intuition — PREREG

**Block**: 301000

**Task**: The user's framing — *"the true power. Using qualia space as a
navigation. Having a problem you feel like there should be a solution for,
even when you don't know it, and using that to try and recover a way to get
there."* and *"This is where we turn to the science and study of how people
do this, and implement that (with an adjustable aperture as before)."*

This registers a NAVIGATION primitive: the felt sense that a problem is
SOLVABLE — present and usable BEFORE and INDEPENDENTLY of retrieving the
solution — read directly off the substrate's own convergent field dynamics,
not a hand-set oracle. It is the qualia-space read of the coherence-detection
literature.

## 1. Theoretical grounding

- **Bowers, Regehr, Balthazard & Parker (1990), "Intuition in the context
  of discovery"** — on the Remote Associates Test, people discriminate
  COHERENT (solvable) from INCOHERENT (unsolvable) triads ABOVE CHANCE
  *before* they can name the solution word. The guiding "hunch" of
  coherence precedes and is dissociable from explicit retrieval. This is
  the core registered phenomenon.
- **Topolinski & Strack (2009), "The architecture of intuition: Fluency
  and affect determine intuitive judgments of semantic and visual
  coherence"** — that coherence signal is driven by PROCESSING FLUENCY
  which is registered as a faint positive AFFECT; and it is PERTURBABLE.
  Manipulating fluency (their studies: masked affective priming, motor
  interference) changes the coherence judgment. This is the anti-faking
  lever: a genuine fluency read must MOVE when the fluency is perturbed.
- **Metcalfe & Wiebe (1987), "Intuition in insight and noninsight problem
  solving"** — the DISSOCIATION. Feeling-of-warmth (subjective closeness
  to solution) is a usable, smoothly-rising gradient on INCREMENTAL/near
  problems, but is FLAT until the last moment — and can give false-warmth
  on a wrong path — on INSIGHT/far problems. A real warmth read should
  reproduce this dissociation, not be uniformly informative.
- **The generalised Seldon APERTURE** (this substrate's own primitive,
  committed dd76f8c3 as `concept_signature(..., observer=)` reading an
  Observer node's `resolves`/`grain`) is the RESOLUTION DIAL: coarse grain
  answers *knows-THAT* (a solution exists / it feels solvable); fine grain
  answers *knows-WHAT* (which attractor). Same read, quotiented at
  different resolution.

## 2. Substrate mapping — the mechanism is REAL, not an oracle

The coherence signal is the substrate's own **convergent local field**, the
Σ coupling term that `can_native_update_3state` already computes inline and
that `domains/can_counterfactual.py:local_field_term` mirrors verbatim:

```
local(node) = external_field(node) + identity_field(node)
              + Σ_{e ∈ Edges(node,'causal_influence')} weight(e) · state(target(e))
```

Build a triad as three CUE Concepts (`state=1.0`, active) wired by
`causal_influence` edges to candidate associate nodes. A node that is the
common target of all three active cues accumulates the summed field of all
three; a node reachable from one cue accumulates only one. The **coherence
signal** is the PEAK convergent field over the candidate region:

```
coherence = max_{node ∈ candidates} Σ_{cue active} weight(cue→node) · state(cue)
```

Two facts make this the coherence-BEFORE-retrieval read and not a disguised
answer lookup:

1. **`local_field_term` is SEPARATE from `target_state_term`** (the argmax
   Hopfield commit). The coherence read evaluates the FIELD magnitude; it
   never evaluates the threshold ladder that would name a winning node.
2. **The `ATANH_HALF` deadzone** (`target_state_term`, 3-state) means a node
   can carry a HIGH local field while STILL committing to state 0
   (uncommitted). High-field-uncommitted is exactly *feels-solvable but not
   yet retrieved*.

In qualia-space terms (`concept_signature`, `_qualia_schema` field_axes):
the convergent field drives `external_field → dynamical:pull` (the overlay
axis) while `identity_field → dynamical:commitment` stays DARK (idf is 0 for
a fresh, uncommitted candidate). **Felt pull lit, commitment dark** = the
coherence hunch.

### Aperture dial

`grain` on `dynamical:pull` (per the committed `_observer_aperture`
per-dimension quantum) quotients the coherence read:
- **coarse** (large quantum): the read collapses to "peak field is high /
  low" — a binary *feels-solvable* — WITHOUT resolving which node. knows-THAT.
- **fine** (small quantum): distinct candidate fields separate, the argmax
  node localises. knows-WHAT.

## 3. Corpus — honest scope

**This is commonsense-shared-associate coherence, NOT the Mednick free-
association RAT.** The Mednick RAT associate is a free-association norm,
carried by ConceptNet's `RelatedTo`/`Synonym` relations — which this
substrate's slab (`domains/conceptnet_reference._KEEP_RELATIONS`)
deliberately DROPS as noisy bulk. Rather than rebuild the 498 MB slab and
re-admit that noise (and then be tempted to cherry-pick edges to manufacture
triads — that would be faking), the corpus is built from the EXISTING
whitelisted commonsense relations (`IsA`, `AtLocation`, `PartOf`, `UsedFor`,
…):

- **COHERENT triad**: 3 cue concepts that all point to a common associate
  node via whitelisted relations (found by reverse-index over a fixed cue
  vocabulary; associate shared by ≥3 cues). Real examples from the live
  slab: `{cat,dog,tree}→backyard`, `{book,cat,dog}→bed`,
  `{cat,food,knife}→kitchen`.
- **INCOHERENT triad**: 3 cue concepts with NO shared target.
- **NEAR** (Metcalfe incremental): the true associate is the clear peak —
  shared by all 3 cues, no competitor shared by ≥2.
- **FAR** (Metcalfe insight): a DECOY shared by 2 cues out-peaks a true
  associate that is only reachable indirectly — the field localises on the
  WRONG node = false-warmth.

The associate identity is **HELD OUT**: the navigator receives the cue set
and the candidate node-set, computes the field, and returns the coherence
scalar (and, at fine aperture, the argmax NODE) — the ground-truth associate
label is never passed into the read path. Enforced by a
`never_reference_held_out`-style source audit (the substrate's proven
program-synthesis / speech-LOSO discipline).

## 4. Falsifiable claims

1. **Coherence-before-retrieval**: over the corpus, the coherence scalar
   (peak convergent field) is CI-separated HIGHER for coherent than
   incoherent triads — measured from the FIELD alone, with the argmax
   commit never evaluated and the associate label held out. `dynamical:pull`
   lit, `dynamical:commitment` dark.
2. **Perturbation reverses it (Topolinski anti-faking)**: perturbing the
   fluency — dropping a cue→associate edge, or attenuating the cue state /
   edge weight — DROPS the coherence read of a coherent triad toward the
   incoherent range. The signal is derived from the dynamics, not hand-set,
   so it MUST move when the dynamics move.
3. **Aperture-graded knows-that → knows-what**: at coarse `grain` the read
   reports *solvable* without localising a node; at fine `grain` the SAME
   read localises the peak node. A monotone dial between them.
4. **Metcalfe dissociation**: on NEAR triads the peak node is the true
   associate (warmth localises correctly); on FAR triads the peak node is
   the DECOY (characteristic false-warmth on the wrong attractor). The read
   is usable on near, systematically misled on far — the registered
   dissociation, not uniform informativeness.

Each claim is reported with its measured outcome; any that fail are reported
as failing.

## 5. Anti-faking bars

- **Held-out audit**: the coherence read path may reference cue identities
  and candidate NODE fields, but NEVER the ground-truth associate label. A
  source audit asserts the label symbol does not appear in the read.
- **Argmax not evaluated for the coherence scalar**: claim 1 is computed
  from `local_field_term`-shaped field only; `target_state_term` is invoked
  only at fine aperture for localisation (claim 3/4), never to produce the
  coherence-before-retrieval number.
- **Perturbation MUST reverse** (claim 2): a coherence read that survives
  fluency perturbation would be a hard-coded oracle, not a fluency read —
  that would falsify the whole construction.
- **default == today**: the navigator is a NEW module. Existing
  `concept_signature` / `find_analogies` are byte-identical when the
  navigator is not invoked; `observer=None` / no-grain reads are unchanged.
  `.so` md5 stays `7efe75eba05b006cafd15dbb4b7da246` — seed+python only, no
  Rust.

## 6. Scope boundaries

- Commonsense-shared-associate coherence, NOT Mednick free-association RAT
  (Sec 3) — stated plainly here and in RESULTS.
- The corpus is derived from a fixed cue vocabulary over the existing slab;
  it is a demonstration battery, not a normed psychometric instrument.
- The aperture dial reuses the committed `_observer_aperture` grain
  primitive; this rung does not add a new per-agent quantum.
- No claim that this exhausts human intuition — it reproduces the specific
  coherence-detection + warmth-dissociation findings above, in-substrate,
  from real dynamics.
