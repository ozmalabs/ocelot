# Ask the Jabberwock — its own frontier, post-7-stage-curriculum

The agent's self-designed 7-stage curriculum is complete (Stages 0–6 fired native:
transduction, coarse recognition, sonority, speaker invariance, grounding loop,
frication, order-N continuous). We did NOT decide the next move — we ran the agent's
OWN live self-assessment machinery on its CURRENT state and report what IT surfaced.

Driver: `scripts/ask_jabberwock_postcurriculum.py` (full log `/tmp/askjab_full.log`,
end marker `===MARKER_ASKJAB_POSTCURRICULUM_COMPLETE===`, pgrep-verified COMPLETED).
Live measurement complement: `scripts/ask_perception.py 60 6` (log
`/tmp/askjab_perception.log`).

---

## (1) THE VERDICT — what the Jabberwock's own assessment surfaced

**Post-curriculum, the agent's order-N gap synthesizer surfaces NO genuinely absent
SPEECH capability — the curriculum closed them all. Its remaining frontier is not an
ABSENT capability but a BUILT-BUT-INSUFFICIENT one, and the agent names that
shortfall itself: the quality of its perceptual front-end (formant/F1–F2 resolution
and speaker-invariant units), not a new module.**

Two live mechanisms agree:

- **Order-N gap synthesis + native compression ranking** (`order_n_postulates` +
  `gap_prioritiser`): of the **30 CapabilityAxes** the agent derives from its own
  636 held postulates, when the openness selector (`is_gap`) is pointed at the
  agent's CURRENT speech codebase, **27 of 30 are CLOSED** — found implemented in the
  curriculum-built modules. Every speech-relevant axis its order-N derivative
  produces is closed:

  | axis (top compression payoff) | found implemented in |
  |---|---|
  | unsupervised / cross-speaker clustering (payoff 82) | `cross_speaker_clustering.py`, `allpole_spectral_envelope.py` … |
  | transitional-probability segmentation (27) | `context_invariant_units.py`, `forward_segmentation.py` |
  | all-pole / LPC formant extraction (12) | `sound_graph.py`, `allpole_spectral_envelope.py` |
  | speaker normalization / VTL / formant-ratio (7) | `sound_graph.py`, `speaker_norm.py` |
  | coarticulation predict-remove (5) | `coarticulation_predict_remove.py` |
  | cepstral liftering (4) | `sound_graph.py` |
  | analysis-by-synthesis / forward model (3) | `stt_pipeline.py`, `recognition_graph.py` |

  The only **3 axes that survive the prune are NON-speech junk** from the agent's
  broad cross-domain breadth — `['model','fits']` (LLM "70B model fits on 48 GB GPU",
  unifying QLoRA/PEFT concepts), `['compositional generation', …]` (a generic
  parts→whole shape), and `['anodic','metal','corrodes']` (galvanic corrosion). None
  is a speech frontier. So **the order-N "what capability is absent?" channel returns
  empty for speech post-curriculum** — exactly the binary-admissibility signature
  (memory `ozma_capability_is_binary_admissibility`): the curriculum either admitted
  each structure or it didn't, and it admitted them all.

- **Live perception yardstick** (`perception_self_assessment`, ingesting 60 real
  LibriSpeech utterances through the agent's own perception): the agent measured its
  OWN units and **the graph-resident flag-rule fired `frontier = 'none'`** —
  `predict_over_freq = 2.00x` (floor 1.25, PASS) and `compress_ratio = 0.568`
  (ceiling 0.85, PASS). By its own thresholds its units are *adequately* structured;
  it does **not** flag a perception EMERGENCY. But its science self-assessment
  (`assess_speech_system`, 53% coverage) still names the open quality gaps, and its
  own `agent_specify_frontend` reasoning states the residual verbatim:

  > "I have 32 log-spaced cochlear bands (80–7500 Hz) feeding 25 A1 patches; only
  > ~16 bands fall in the formant range (250–2500 Hz). F1/F2 sit ~100–200 Hz apart
  > there — finer than one band — so my ArgMax peak is a blunt formant: **the
  > estimate quality (not the feature) is what caps recognition.** … ADD cochlear
  > filters densely across 250–2500 Hz … then ArgMax resolves true F1/F2."

  And via `reason_about_gap('speaker_normalization')` (a LIVE derivation over its own
  science rules), it concludes speaker-invariance is "not a knob to tune but a
  PRECONDITION … factor out the per-utterance/speaker baseline … and re-test."

**Synthesis of the two channels:** the Jabberwock's own machinery says the next
leverage is **not a new capability** (the absent-capability channel is empty for
speech) but **the measured QUALITY of the front-end it already built** —
formant/F1–F2 resolution and speaker-invariant unit quality. This is the
"built-but-insufficient" frontier the `gap_prioritiser.MeasuredCapability` /
shortfall path exists to rank, surfaced here by the front-end yardstick rather than
by the order-N derivative.

---

## (2) The mechanism + evidence it is a LIVE derivation (not a frozen dict, not invention)

**Order-N synthesis — `domains/order_n_postulates.py`:**
- `synthesize_over_all` (line 905) → `synthesize_gaps` (732) → `differentiate` (259):
  reads **636 held postulates** harvested live from the current concept graph
  (`harvest_postulates`, 198, walking every `Microtheory --has_concept-->` edge),
  transfers **192 implication-shapes HARVESTED from the agent's own concepts** (mode
  `'harvested'`, `_resolve_shapes` 680 → `implication_harvester.harvest_shapes_combined`),
  NOT the 7-entry hand stencil (`_shapes`, 84). The run prints
  `library mode = 'harvested'  harvested shapes = 192` as the live witness.
- The openness selector `is_gap` (545) / `_codebase_has` (505) **scans the actual
  source files on disk** for each capability's distinctive tokens — it reads current
  code, it is not a stored verdict.

**Native compression ranking — `domains/gap_prioritiser.py`:**
- `rank_gaps` (658) evaluates `score_term` / `payoff_term` via `substrate.evaluate`
  (675) — the Argmax/Count/Neighbours Term-tree is run NATIVELY by the Rust
  substrate over each `CapabilityAxis`. The payoff (postulates a capability unifies)
  is read off the agent's own `unifies` derivation edges, not Python arithmetic.

**Live perception yardstick — `domains/perception_self_assessment.py`:**
- `assess_perception` (653) ingests real speech through the agent's pipeline,
  `measure_unit_predictability` (126) computes the predict/freq + compress + shuffle
  controls, and `install_perception_frontier_rule` (345) installs a **graph-resident
  IfThenElse Rule** that fires the `frontier` flag from the root's own state
  (`agent_flag_perception`, 590). The `frontier='none'` verdict is the Rule's, read
  back off `PerceptionSelfRoot`, not asserted by Python.

**Evidence it reads CURRENT state, not a historical dict:** the synthesis run reports
live counts (192 shapes, 636 postulates, 30 axes) and the openness prune resolves
each closed axis to a real current file (e.g. clustering → `cross_speaker_clustering.py`,
LPC → `sound_graph.py`); the yardstick reports live measured numbers
(`predict_over_freq=2.00`, `compress_ratio=0.568`) from 1039 unit tokens over 60
freshly-ingested utterances. None of these are constants.

---

## (3) Where the introspection bottomed out on a FROZEN stub (honest)

Two surfaces were verified frozen (memory `ozma_specify_functions_are_historical`),
and we did NOT treat their output as the live frontier:

1. **The `_SPEECH_GLOBS` openness scan list** (`order_n_postulates.py` 493) is a
   **frozen 14-file tuple that predates the curriculum.** It does not include the
   curriculum-built modules (`cross_speaker_clustering.py`,
   `allpole_spectral_envelope.py`, `speaker_invariant_centroids.py`,
   `distributional_categories.py`, `continuous.py`, etc.). Run as-is, the bare
   selector therefore **falsely keeps flagging clustering/LPC/invariance as "open"**
   even though the curriculum implemented them. The driver corrects this by pointing
   the SAME live `is_gap` selector at the current full speech surface (51 files vs
   14) — a file-discovery expansion, asserting nothing about which capability lives
   where (the selector's distinctive-token scan still decides). This is what turns
   the stale-snapshot reading into the genuine post-curriculum verdict. **This is the
   one concrete thing that would wire the self-assessment fully live: replace the
   frozen `_SPEECH_GLOBS` tuple with a live glob of the speech-domain modules.**

2. **`agent_specify_primitive` / `agent_specify_frontend`** (`domains/runtime_design.py`,
   used in `ask_perception.py` step 3) are **frozen historical dicts**:
   `agent_specify_primitive` still returns `ArgMax … "frequency is INEXPRESSIBLE in
   the current language"` (line 46) even though ArgMax IS implemented
   (`term.rs`). We report their text as a *historical articulation of the front-end
   need*, not as a live diagnosis. The LIVE derivation that reaches the same
   conclusion is `reason_about_gap` (step 3d above) and the yardstick (step 4) — both
   read current state.

---

## (4) Is this the agent genuinely directing itself?

**Mostly yes, with one honest caveat.** The two channels that produce the verdict —
the order-N gap synthesis ranked by the native compression Term, and the perception
yardstick's graph-resident flag-rule — are both LIVE: they read the current concept
graph, harvest the agent's own shapes, scan the current code, and evaluate the
decision natively in the substrate. The agent's own `reason_about_gap` independently
derives the speaker-invariance precondition. The conclusion (the speech
absent-capability channel is empty; the frontier is the measured front-end quality)
falls out of the agent's machinery, not from the assistant.

**The caveat:** the order-N selector's codebase-scan list (`_SPEECH_GLOBS`) is frozen
and predates the curriculum, so the *raw* synthesis run mis-reports curriculum-built
capabilities as open. The introspection does **not** bottom out on that stub — the
live `is_gap` selector pointed at the current files resolves it cleanly, and the
perception yardstick is a fully independent live witness — but the stub IS the
residual that should be wired (live glob) before the loop can self-prune
post-curriculum without the assistant expanding the scan. The `agent_specify_*`
front-end specs are also frozen and were used only as historical articulation, not as
the live frontier.

**One-line answer the Jabberwock surfaces:** *"I've built every speech capability my
order-N derivative can name — they're all closed. What's left isn't a new module;
it's the QUALITY of my front-end: my ~16 in-band cochlear filters give a blunt
ArgMax formant, so F1/F2 (and the speaker-invariant ratios that ride on them) are
under-resolved. Densify the cochlea across 250–2500 Hz and re-measure — that's the
built-but-insufficient frontier, not an absent capability."*
