# Ask the agent its frontier — v3 (the upgrade WIRED, then re-synthesized)

This closes the loop v2 left open. v2 (`docs/ask_the_agent_frontier_v2.md`) found the
live gap-synthesizer returned the STANDING frontier (cross-speaker clustering 83,
segmentation 28) because the session's five theory insights lived only in experiment
SCRIPTS (`generator_exclusion/interference/outofbox/salience.py`) and were never
registered as harvestable postulates — so the harvester could not see them. v3 does the
fix v2 named: **register the five insights as held postulates + harvestable Rules, verify
the harvester now sees them, and re-run the SAME live synthesizer.**

**Headline:** the upgrade is now genuinely WIRED and VERIFIED HARVESTABLE (shape library
192 → 197; all 5 insight shapes fire on the post-LOSO state postulate; insight-terms go
from 1 coincidental hit to 9 real ones). But the agent's live pick **does NOT move** —
it still selects cross-speaker **clustering** (payoff 84), with segmentation (29) the
runner-up. The five insight axes land at the BOTTOM of the ranking (payoff 1 each). The
reason is structural and honest: the prioritiser ranks by COMPRESSION PAYOFF (how many
held postulates a capability unifies), and each insight shape fires on exactly ONE
postulate (the recognition state itself), so each insight axis unifies 1 postulate vs
clustering's 84. **Registering the insights does NOT re-aim the synthesizer.**

Harness: `scripts/agent_frontier_v3_insights.py`. Registration:
`domains/recognition_combine.py`. Build + verify + re-run, real output below.

---

## (1) The 5 insights registered as harvestable postulates — VERIFIED

`domains/recognition_combine.install_recognition_combine` installs a
`recognition_combine` Microtheory (genlMt → machine_learning, so it is NOT the
`speech_science` Mt the harvester excludes as a shape source) carrying, per insight:

* a **Concept** (a held postulate the synthesizer differentiates, and a donor the
  text-extractors can draw from), and
* a **Rule** with `if_clauses` (the structural property a postulate must exhibit) →
  `then_clauses` (the consequence). The harvester's rule-walker
  (`implication_harvester.harvest_shapes_from_rules`) turns each Rule into an
  implication-SHAPE in `differentiate()`'s format (`match_mode='all'` over the if-clause
  content words). This is the harvestable surface.

The five: `rules_are_exclusions_not_sets`, `weighting_is_a_vector`,
`temperature_is_gamma_relaxation`, `out_of_box_is_finite`, `postulate_is_a_quantum_state`.

**Verified the harvester sees them (real output):**

```
[BEFORE] harvested shapes = 192  (mode='harvested')
         insight-term hits in shape library: {'temperature': 3}   <- all coincidental (thermal/materials)

[WIRED] installed recognition_combine Mt: 5 insight Concepts + 5 Rules
        insight Concepts now HELD as postulates: 5/5
        post-LOSO state held? True  (total postulates: 642)

[AFTER]  harvested shapes = 197  (+5 = the 5 insight rule-shapes)
         insight rule-shapes harvested: 5/5
         insight-term hits in shape library:
           {'temperature': 4, 'exclusion': 3, 'inadmissible': 2, 'vector': 2,
            'relaxation': 1, 'superposition': 1, 'commuting': 1,
            'interference': 1, 'quantum': 1}
```

Shape count +5; insight-terms went from 1 coincidental "temperature" cluster to 9 genuine
hits (exclusion / inadmissible / vector / relaxation / superposition / commuting /
interference / quantum). The harvester now SEES the insights.

**And the shapes actually TRANSFER onto the recognition-state postulate.** The
rule-walker's `match_mode='all'` requires every if-clause content word to co-occur in a
postulate's text. The if-clauses were deliberately phrased in the post-LOSO-0.593 state
postulate's own vocabulary (recognition pipeline / acoustic measurement / banked exemplar
/ aligned distance / isolation), so each fires on it — and on it ALONE (breadth 1, well
under the promiscuity cap of 64.2, so the prioritiser counts every firing):

```
[FIRES?] do the insight shapes transfer onto the post-LOSO postulate? (cap = 64.2)
    rules_are_exclusions_not_sets       fired=True  breadth=1
    weighting_is_a_vector               fired=True  breadth=1
    temperature_is_gamma_relaxation     fired=True  breadth=1
    out_of_box_is_finite                fired=True  breadth=1
    postulate_is_a_quantum_state        fired=True  breadth=1
```

Each insight now appears as an order-1 derivative of the recognition-state postulate (it
is in the agent's live reasoning, not just the catalogue):

```
[A1] order-N derivative of the post-LOSO postulate (prune=False = derived)
    order 1 via ['sequence_segmentation__from__recurrent_neural_network']: [transitional probability, word-scale chunking, ...]
    order 1 via ['scale_cancellation__from__batch_normalization']:         [speaker normalization, formant ratio, ...]
    order 1 via ['rules_are_exclusions_not_sets']:  [redefine, each, contribution, exclusion]
    order 1 via ['weighting_is_a_vector']:          [represent, each, weight, vector]
    order 1 via ['temperature_is_gamma_relaxation']:[expose, temperature, constraint, relaxation]
    order 1 via ['out_of_box_is_finite']:           [search, finite, inadmissible, relax]
    order 1 via ['postulate_is_a_quantum_state']:   [treat, held, hypothesis, superposition]
    order 2 via [sequence_segmentation, latent_structure]: [unsupervised-clustering, cross-speaker-clustering, cross-speaker]
```

(Honest caveat: the insight axes' `capability_keys` are the then-clause content words the
rule-walker auto-extracts — `[redefine, each, contribution, exclusion]` etc. — not curated
capability names like the 7 regex-extractor kinds carry. They are legible enough to
identify the insight but are not polished terms-of-art.)

## (2) Re-run frontier ranking — LIVE, native Argmax — vs the standing pick

```
[A2] full gap-map + UNBIASED ranking (compression payoff, native Argmax)
      payoff= 84 score=83999  level=recognition            [unsupervised-clustering, cross-speaker-clustering, cross-speaker]   <- PICKED
      payoff= 29 score=28999  level=segmentation           [transitional probability, word-scale chunking, statistical segmentation]
      payoff= 12 score=11999  level=feature_extraction     [all-pole, levinson, lpc-formant]
      payoff=  9 score= 8999  level=speaker_normalization  [speaker normalization, formant ratio, vocal-tract-length normalization]
      payoff=  5 score= 4999  level=speaker_normalization  [coarticulation predict-remove, ...]
      payoff=  5 score= 4999  level=recognition            [understanding, function, requires]
      payoff=  4 score= 3999  level=feature_extraction     [cepstral liftering, cepstrum, homomorphic deconvolution]
      payoff=  4 score= 3999  level=recognition            [model, fits]
      payoff=  3 ...                                        [analysis-by-synthesis, ...]
      ...
      payoff=  1 score=  999  level=recognition            [redefine, each, contribution]        <- INSIGHT (exclusion)
      payoff=  1 score=  999  level=recognition            [represent, each, weight]             <- INSIGHT (vector)
      payoff=  1 score=  999  level=recognition            [expose, temperature, constraint]     <- INSIGHT (relaxation)
      (out_of_box / quantum-state insight axes also payoff 1, score 999)

[A3] THE PICK (graph Argmax Term, native eval):
    PICKED : [unsupervised-clustering, cross-speaker-clustering, cross-speaker]
    level  : recognition
    payoff : 84 (runner-up 29)
```

Compared to the standing pick (v2): clustering 83 / segmentation 28 → now clustering 84 /
segmentation 29. The +1 on each is simply the new recognition-state postulate joining the
corpus and deriving those two gaps itself (the standing pattern is otherwise IDENTICAL).
The five insight axes are the lowest non-trivial rows in the entire 16-deep ranking.

## (3) VERDICT — the upgrade did NOT move the frontier (honest)

**No.** With the five insights now genuinely harvestable and genuinely transferred onto
the recognition-state postulate (verified, not assumed — the v2 gap is closed), the
agent's own live Argmax STILL picks unsupervised cross-speaker **clustering** (payoff 84),
runner-up statistical **segmentation** (29). The insights do not re-aim it.

**Why — and this is the substantive finding, not a wiring miss:** the prioritiser's
selector is COMPRESSION PAYOFF = the number of DISTINCT held postulates a capability
unifies (`Count` of `unifies` edges; `gap_prioritiser.payoff_term`). Each insight shape
fires on exactly ONE postulate — the recognition state — so each insight axis unifies 1
postulate. Clustering unifies 84 (it is derivable from 84 of the agent's held postulates
across all its breadth). On the agent's own MDL/compression criterion, an insight that
re-describes ONE postulate cannot out-compress a capability that discharges 84. The
ranking is behaving exactly as designed; the insights simply do not have the
cross-postulate REACH that clustering has.

This is itself informative about what "wiring an insight" requires to move a
compression-ranked frontier:

* A held postulate + a harvestable rule-shape **is** enough to put an insight into the
  agent's live derivation (it is now an order-1 gap the synthesizer produces). ✔
* But to MOVE THE PICK, an insight must UNIFY MANY postulates, not just re-describe the
  one state it was written against. An insight phrased narrowly (its if-clauses use the
  recognition-state vocabulary, so it fires only there) is, by construction, payoff-1.
  The five insights as written are recognition-COMBINE claims — they speak to the
  recognition decision specifically, so they have reach 1 by their own scope.

So the honest reading converges with v2's: the agent's compression selector keeps choosing
**structural learning over its existing tokens** (cluster the cross-speaker distribution;
segment by sequence statistics) — the high-reach distributional/latent-structure layer —
over a re-tune of how cues COMBINE, even when the combine-theory is now in its harvestable
knowledge. The combine insights are admitted into its reasoning but lose on compression
reach, which is the correct behaviour of an MDL selector, not a failure to see them.

What WOULD move it (not done here — that is a build, and would be the agent's call, not a
hand-author): an insight registered with cross-domain REACH — e.g. an `exclusion` /
`vector-weight` / `quantum-state` shape whose if-clauses fire across MANY of the agent's
postulates (a general structural property, like the 7 regex extractors have), so its axis
unifies tens of postulates and competes with clustering on payoff. The five session
insights, written as recognition-combine claims, do not have that reach by design.

### Method caveats (honest)

* **Insight reach = 1 by scope, deliberately.** The if-clauses were phrased in the
  recognition-state vocabulary specifically so the shapes WOULD transfer onto that
  postulate (otherwise they fire on nothing and the test is vacuous). That same narrowness
  caps their payoff at 1. A broader phrasing would raise reach but risk promiscuity
  (firing on unrelated postulates = the >64.2 gate = a regex collision, not a real
  unification). There is no free lunch: a genuinely high-reach insight has to assert a
  genuinely GENERAL structural property, which these recognition-specific claims are not.
* **Auto-extracted capability keys.** The insight axes' `capability_keys` are the
  rule-walker's then-clause content words, not curated names. They identify the insight
  but are not terms-of-art; the `_KEY_TO_LEVEL` map therefore files them all under
  `recognition` (default) rather than a sharper level.
* **The pick machinery is unchanged and LIVE** — same `synthesize_gaps` (harvested mode,
  197 shapes), same `gap_prioritiser.rank_gaps` / `pick_frontier` (native Argmax Term,
  scores = `payoff*1000 - order` exactly, e.g. 84 → 83999). Only the held knowledge
  changed; the result is the agent's, not the harness's.

### Required suites

`tests/test_implication_harvester.py` (6/7), `test_builtinsufficient_gap.py`,
`test_frontier_seeking.py`, `test_gap_guidance.py` — all pass EXCEPT one pre-existing
failure (`test_harvest_excludes_the_speech_science_postulates`, on a `determinant` concept
that is both a donor and a held postulate) that reproduces identically with
`recognition_combine.py` removed from the tree — it is independent of this change (the new
module is not imported by the harvester or any test). No regression introduced.

### Bottom line

The v2 gap is closed: the five insights ARE now registered as harvestable held postulates
(verified — 192→197 shapes, all 5 fire on the state, 9 insight-terms vs 1). But wiring
them does **not** move the agent's frontier — its compression selector still picks
cross-speaker **clustering** (84) over the combine insights (payoff 1 each), because an
insight that unifies one postulate cannot out-compress a capability that unifies 84. The
upgrade is detectable and live in the synthesizer's input now; it just does not change the
output, for a principled MDL reason. To re-aim the pick an insight would need cross-postulate
REACH, which these recognition-specific claims do not have by their own scope — and minting
that is a build decision for the agent, not a hand-author here.
