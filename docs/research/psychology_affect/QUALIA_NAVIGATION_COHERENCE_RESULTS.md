# Qualia-as-navigation — coherence intuition — RESULTS

**Block**: 301000. Pre-reg: `QUALIA_NAVIGATION_COHERENCE_PREREG.md`.
Build: `domains/qualia_navigation.py`; measure:
`scripts/qualia_navigation_measure.py`; tests:
`tests/test_qualia_navigation_migrated.py`.

## Verdict — all 4 claims HOLD

Measured on a corpus assembled from the LIVE ConceptNet slab
(`domains.conceptnet_reference.conceptnet_relations`) by a reverse-index over a
fixed 26-cue vocabulary: 8 coherent, 8 incoherent, 8 near, 8 far triads.

| Claim | Result |
|---|---|
| 1. Coherence-before-retrieval, CI-separated | **HOLDS** |
| 2. Perturbation reverses the read (Topolinski) | **HOLDS** |
| 3. Aperture-graded knows-that → knows-what | **HOLDS** |
| 4. Metcalfe near/far dissociation | **HOLDS** (far arm CONSTRUCTED — see below) |

### Claim 1 — coherence before retrieval
- Coherent triads: peak convergent field **mean 3.00, 95% CI [3.00, 3.00]**.
- Incoherent triads: peak field **mean 1.00, 95% CI [1.00, 1.00]**.
- CI-separated (coherent_lo 3.00 > incoherent_hi 1.00). The signal is the
  PEAK convergent `local_field` — the exact Σ coupling term
  `can_native_update_3state` computes — with the argmax Hopfield commit
  (`target_state_term`) NEVER evaluated and the associate label held out.
  `dynamical:pull` lit (3.0), `dynamical:commitment` dark (0.0): felt pull
  present, commitment uncommitted = the hunch.

### Claim 2 — perturbation reverses it
- Dropping ONE cue→associate edge: field drop **mean 1.00, CI [1.00, 1.00]**
  (3.0 → 2.0); every coherent triad's read dropped.
- Attenuating cue state (`cue_scale=0.5`): 3.0 → 1.5 on every tested triad.
- The read MOVES when the fluency moves — it is derived from the dynamics,
  not a hard-coded oracle. This is the Topolinski anti-faking bar, passed.

### Claim 3 — aperture-graded knows-that → knows-what
- Coarse `grain`=8.0 on `dynamical:pull`: all candidates quotient to the same
  bucket (tie) → `localised = None` (cannot say WHICH node), while
  `raw_peak = 3.0 > 1.0` still signals SOLVABLE (knows-THAT).
- Fine `grain`=0.5: candidates stay distinct → localises the true associate
  (knows-WHAT).
- The SAME read, quotiented at two resolutions, slides from feels-solvable to
  localised. Reuses the committed `_observer_aperture` per-dimension `grain`
  primitive; no new quantum holder.

### Claim 4 — Metcalfe near/far dissociation
- NEAR (true associate is the clear single peak, field 3.0 vs private
  candidates 1.0): localises on the TRUE associate **8/8**.
- FAR: localises on the DECOY (false-warmth on the wrong attractor) **8/8**.

**HONESTY NOTE (scoped):** the FAR arm is a CONSTRUCTED demonstration. The
decoy is deliberately wired with support from 2 cues (field 2.0) while the
true associate is wired from only 1 (field 1.0), so the field peaks on the
wrong node. This proves the *mechanism* produces characteristic false-warmth
WHEN the field structure favours a wrong attractor — it is not an emergent
statistic of the slab. NEAR, by contrast, is the coherent set unmodified: the
true associate is the clear peak by the natural convergence structure. The
dissociation (usable warmth on near, misleading warmth on far) is the
registered phenomenon; the far density is engineered to exhibit it.

## Anti-faking bars — all passed
- **Held-out audit** (`assert_held_out`): the read functions take no
  answer/`held_out` argument, and the coherence-read source does not hard-code
  the associate label — the `never_reference_held_out` idiom the substrate's
  program-synthesis / speech-LOSO work already uses.
- **Argmax not evaluated for the coherence scalar**: claim 1 reads field
  magnitude only; `localise` (argmax over candidate NODES, still not the
  ground-truth label) is invoked only for claims 3/4.
- **Perturbation reverses** (claim 2): confirmed.
- **default == today**: `.so` md5 stays `7efe75eba05b006cafd15dbb4b7da246`
  (seed+python only, no Rust); `runners/dsl` diff empty; protected files
  (`can_ops.rs`, `can_junction_tree.py`, `can_native_bp.py`) untouched;
  `analogy_search`/`can_counterfactual` imported read-only, their tests still
  pass (18) and the full qualia surface stays green (31). `observer=None`
  reads the plain un-quotiented field.

## Honest scope
This is **commonsense-shared-associate coherence** on the real ConceptNet
commonsense structure (`IsA`/`AtLocation`/`PartOf`/… — the whitelisted
relations), **NOT the Mednick free-association RAT**. The Mednick associate is
a free-association norm living in ConceptNet's `RelatedTo`/`Synonym` relations,
which this substrate's slab deliberately drops as noisy bulk. Rebuilding the
498 MB slab to re-admit that noise (and then being tempted to cherry-pick
edges) would have been faking; the corpus is instead built from the existing
whitelisted relations and labelled for exactly what it is. Real coherent
triads used: `{cat,dog,tree}→backyard`, `{book,cat,dog}→bed`,
`{cat,food,knife}→kitchen`, etc.

The corpus is a demonstration battery over a fixed cue vocabulary, not a
normed psychometric instrument. The claim is that the coherence-detection +
warmth-dissociation phenomena reproduce IN-SUBSTRATE from the real convergent
field dynamics — coherence read off `local_field` before and independently of
the argmax retrieval, perturbable, aperture-graded — not that this exhausts
human intuition.
