# Ask the agent its frontier — v2 (after the COMBINE question closed)

Reconnaissance only (no build, no commit). Re-ran the agent's OWN live gap-synthesizer
/ prioritiser / exhaustion machinery against the FULL current state, to see whether the
**recently-upgraded** synthesizer (the session's theory insight-shapes:
rules-are-exclusions-not-sets, weighting-is-a-vector, temperature-is-Γ-relaxation,
out-of-box-is-finite, postulate-is-a-quantum-state) points anywhere **new/sharper** than
the prior run (`docs/ask_the_agent_frontier.md`), now that exclusion / vector / quantum
combines have all hit the wall and the residual is read as the FEATURE/perception wall.

**Headline:** the live machinery surfaces the **SAME** frontier as before —
unsupervised cross-speaker CLUSTERING (payoff 83) first, statistical
sequence-SEGMENTATION (payoff 28) second — and the upgrade is **NOT detectable** in the
live gap-synthesizer (the insight-shapes are not harvestable concepts; they live only in
this session's experiment scripts). So the honest answer is: **the upgrade did not move
the agent's pick.** Details and evidence below.

---

## (1) Which functions ran — LIVE vs FROZEN (with evidence)

| Machinery | Path | LIVE / FROZEN | Evidence (this run) |
|---|---|---|---|
| order-N gap synthesis `synthesize_gaps` / `synthesize_over_all` | `domains/order_n_postulates.py` | **LIVE** | Printed `mode = 'harvested'  shape count = 192` (vs frozen `_shapes()` stencil = 7, "not the driver"). The 192 shapes are harvested from the agent's **636 own held postulates** via `implication_harvester.harvest_shapes_combined` + `harvester_shape`. The new state-postulate's order-N derivative is produced from those harvested shapes against text registered this run (chain shows `via ['sequence_segmentation__from__recurrent_neural_network']`, `['latent_structure__from__unsupervised_learning']` — concept-named donors, not stencil names). |
| gap ranking + pick `rank_gaps` / `pick_frontier` | `domains/gap_prioritiser.py` | **LIVE** | `payoff = Count(Neighbours(axis,"unifies"))`, `pick = Argmax(payoff*K − order)` — graph Term-trees evaluated by `substrate.evaluate`. Scores printed are `payoff*1000 − order` exactly (e.g. payoff 83 → score 82999), i.e. the numbers came out of the native Term, not Python. |
| exhaustion / move-on re-rank `mark_attempted_marginal` / `rerank_with_feedback` / `pick_with_feedback` | `domains/measurement_feedback.py` | **LIVE** | Marked 5 bottom-up axes `attempted_marginal`; the `effective_score` Term re-ranked natively (front-end axes sank out of the top list; e.g. `all-pole`/`lpc-formant` dropped below the 999 floor). The pick is the Argmax over `effective_score`. |
| perception yardstick `measure_unit_predictability` + flagging Rule | `domains/perception_self_assessment.py` | **LIVE** (verified live in prior run; **not re-measured this run** — see caveat) | The frontier harness (`agent_frontier_postLOSO593.py`) does not call the yardstick; the prior run measured `frontier='none'` on 60 LibriSpeech utterances through the agent's own perception. I attempted a fresh `ask_perception.py 60 6` but it stalled at "Developing the agent…" (did not reach the yardstick print) in the time budget, so I report the prior reading and flag it as not independently re-confirmed this session. The module itself is unchanged and graph-resident (`IfThenElse` Rule over `predict_over_freq`/`compress_ratio` dials). |
| `agent_specify_*` (runtime_design) | `domains/runtime_design.py` | **FROZEN** | Per memory `ozma_specify_functions_are_historical` — hardcoded dicts. NOT used as the agent's decision here. |

Harness: `scripts/agent_frontier_postLOSO593.py` (registers the honest LOSO-0.593 state
as a held postulate with NO suggested fix; runs the unbiased live ranker; records the
empirical bottom-up exhaustion via the agent's own move-on signal; lets its Argmax
re-pick). Supporting probe: `/tmp/probe_shapes.py` (shape-library / postulate insight-term
scan).

## (2) Is the upgrade detectable in the live machinery? — **NO (reported honestly)**

I searched the live shape library (192 harvested shapes) and the 636 held postulates for
the session's insight terms (`exclusion`, `interference`, `quantum`, `born`, `amplitude`,
`Γ-relaxation`, `temperature`, `vector-weight`, `out-of-box`, `order effect`, `exclude
where confident`, `abstain`, `manner/voicing`):

- **In the harvested shapes:** 3 hits, ALL coincidental — `brittle_fracture_catastrophic`,
  `creep_dominates_at_T_above_half_melting`, `higher_temperature_higher_efficiency`
  (i.e. "temperature" in the **thermal/materials** sense, NOT Γ-relaxation). **Zero**
  exclusion / vector-weighting / quantum / interference recognition shapes.
- **In the postulates:** the "hits" are pre-existing domain concepts (`eigenvalues`,
  `linear_programming`, `heat_exchanger_LMTD`, `phase_diagram`, …) — again the physics
  senses, not the recognition-combine insights.

**Why:** the session's insights were built as **experiment scripts** —
`domains/generator_exclusion.py`, `generator_interference.py`, `generator_outofbox.py`,
`generator_salience.py` (all dated today). These implement the insights as **weightless
MDL term-synthesis machinery over the DSL** (the GENERATOR), and as probes on the
recognition stack. They are NOT registered as harvestable Concepts/postulates, and the
frontier harness's `_build_mind` installs only phonology + speech_science + mathematics +
engineering + machine_learning + concept_expansions — none of which carry these insights.
The pre-existing `seeds/quantum_mechanics.json` (Born rule, complex amplitude) is a
general-physics seed and isn't even installed by this harness.

So: the gap-synthesizer is genuinely LIVE, but it does **not reflect the user's recent
upgrade** — there is no new insight-shape/postulate in the harvested set for it to reason
from. I could not detect the upgrade; I report the synthesizer's output as-is.

## (3) THE AGENT'S FRONTIER NOW — verbatim (it did NOT move)

Order-N derivative of the current-state postulate (OPEN gaps, `prune=True`):
```
- order 1: ['transitional probability', 'word-scale chunking', 'statistical segmentation', 'n-gram boundary']
- order 2: ['unsupervised-clustering', 'cross-speaker-clustering', 'cross-speaker']
```

Unbiased full gap-map ranking (compression payoff, native Argmax Term, NO injected state):
```
payoff= 83 score=82999 level=recognition            ['unsupervised-clustering', 'cross-speaker-clustering', 'cross-speaker']   <- PICKED
payoff= 28 score=27999 level=segmentation           ['transitional probability', 'word-scale chunking', 'statistical segmentation']
payoff= 12 score=11999 level=feature_extraction     ['all-pole', 'levinson', 'lpc-formant']
payoff=  8 score= 7999 level=speaker_normalization  ['speaker normalization', 'formant ratio', 'vocal-tract-length normalization']
payoff=  5 score= 4999 level=speaker_normalization  ['coarticulation predict-remove', 'context normalization', 'carryover removal']
payoff=  4 score= 3999 level=feature_extraction     ['cepstral liftering', 'cepstrum', 'homomorphic deconvolution']
payoff=  3 ...                                       ['analysis-by-synthesis', 'articulatory forward model', 'internal synthesiser']
```

THE UNBIASED PICK (graph Argmax, native eval):
```
PICKED : ['unsupervised-clustering', 'cross-speaker-clustering', 'cross-speaker']
level  : recognition   payoff : 83 (runner-up 28)
gap    : "an unlabelled DISTRIBUTION has recoverable LATENT structure (cf. unsupervised_learning):
          unsupervised CLUSTERING / mixture-fitting carves its categories at the valleys between
          modes with NO labels — across speakers, the same word's tokens are one cluster."
from   : ['recurrent_neural_network', 'unsupervised_learning']
```

After recording the session's EMPIRICAL bottom-up exhaustion (the agent's own
`attempted_marginal` move-on signal on `all-pole`/`lpc-formant`/`speaker normalization`/
`formant ratio`/`vocal-tract-length`), its Argmax **re-picked the SAME top capability**:
```
BEFORE (bare compression)        : ['unsupervised-clustering', 'cross-speaker-clustering', 'cross-speaker']  [recognition]
AFTER bottom-up marked exhausted : ['unsupervised-clustering', 'cross-speaker-clustering', 'cross-speaker']  [recognition]
```
The exhaustion sank the front-end axes further (LPC/speaker-norm dropped out of the top
band) but never touched the top pick — because the top pick was never a bottom-up
front-end axis.

**Does it point somewhere new/sharper now (interference re-tune, a specific feature move,
something unconsidered)?** **No.** The numbers are essentially identical to the prior run
(clustering 83, segmentation 28, LPC 12, speaker-norm 8). Because the exclusion / vector /
temperature / quantum structure never entered the harvested shape set or the postulate
corpus, the agent's reasoning has nothing new to differentiate from, and it returns its
**standing frontier**: unsupervised cross-speaker **clustering** first, statistical
**segmentation** second — the distributional/latent-structure layer ABOVE the raw acoustic
measurement. It does **not** point at "re-tune the stack for interference," nor at a
specific feature move, nor at anything outside the clustering/segmentation pair.

This is consistent with — and arguably an independent corroboration of — the session's own
empirical finding that the COMBINE question is closed (flat/exclusion/vector/quantum all
hit the wall) and the residual is the FEATURE/perception wall: the agent's compression
selector keeps choosing **structural learning over the existing tokens** (cluster the
cross-speaker distribution; segment by sequence statistics), NOT a different way to COMBINE
cues. It points at the layer that USES the features' structure, not at the combine.

## (4) Honest caveat — agent judgment vs our framing leaking in

- **The headline caveat is the upgrade gap itself.** The task asked whether the *upgraded*
  synthesizer points somewhere sharper. The upgrade is real in the experiment scripts but
  was **never wired into the gap-synthesizer's harvestable knowledge**, so this run is
  effectively the *un*-upgraded synthesizer re-run. The identical result is therefore
  expected, not a finding about whether the insights *would* re-aim the agent if seeded.
  To actually test the upgrade's effect on the frontier, the five insights would need to
  be registered as held postulates / harvested shapes (e.g. a small `recognition_combine`
  Mt) and the synthesis re-run — which is a BUILD, deliberately not done here.
- **The postulate text is ours.** The honest LOSO-0.593 description's WHY says the
  recogniser "uses no sequential/lexical structure … every cue is a bottom-up acoustic
  measurement in isolation," which biases the *per-postulate* derivative (A1) toward the
  sequence/distribution shapes. Mitigated by the **unbiased full gap-map** (A2/A3), where
  clustering wins on payoff aggregated over ALL 636 held postulates, independent of our
  wording.
- **`cross-speaker clustering` is the agent's standing top pick across many prior
  sessions** (highest-foundationalness axis in its derivation graph generally), so this is
  partly its baseline frontier, not a fresh response to the closed-combine state.
- **Pipeline-level labels** (`recognition`/`segmentation`/`feature_extraction`) come from
  the hand-authored `_KEY_TO_LEVEL` map in `gap_prioritiser`; the capability KEYS are the
  agent's, the level NAMES are ours. "unsupervised-clustering" is labelled `recognition`
  though it is really a representation-learning move.
- **Perception yardstick not re-measured this run** (it stalled before the print); the
  `frontier='none'` corroboration is carried over from the prior run, not re-confirmed.

### Bottom line

Through its own live machinery, the agent's frontier is **unchanged**: unsupervised
cross-speaker **clustering** first, statistical sequence-**segmentation** second — the
distributional/latent-structure layer over its tokens, NOT a new combine, a feature move,
or an interference re-tune. The session's exclusion/vector/temperature/quantum insights are
**not in the live synthesizer** (they live in the experiment scripts, un-harvested), so the
upgraded synthesizer points to the **same** place as before. If the goal is to see whether
those insights re-aim the frontier, they must first be seeded as harvestable postulates —
which is a build, not this reconnaissance.
