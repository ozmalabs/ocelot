# Sound-as-a-GRAPH — does a graph representation dissolve the invariance problem?

Probe, not a pipeline rewrite. Code: `domains/sound_graph.py`,
`scripts/sound_graph_probe.py`. Nothing committed; left in the working tree.
`tests/test_stt_pipeline.py` stays green (7 passed).

## The reframe under test

The agent's reality is (G, Γ) typed graphs; a waveform is the one alien input an
"ear" must translate. Represent a sound AS a graph and the structure is native.
The load-bearing claim: **invariance becomes free**. Source–filter theory (the
agent's own flagged science) is the graph decomposition — SOURCE (f0 + harmonic
stack) carries pitch/speaker; FILTER (formant/resonance pattern) carries
content. As a spectrum, the same vowel from two speakers is two different signals
(absolute freqs shift with vocal-tract length). As a graph of RELATIONS, the
claim is: same structure, only node values shift — so the filter subgraph should
be speaker-invariant by construction, making CMVN/VTLN/predict-remove
unnecessary.

## (1) The schema the agent specified (surfaced from its own science)

`surface_schema()` reads `seeds/expansions/speech_production_decomposition.json`
and emits the node/edge schema its source–filter science implies. It is grounded
in the agent's held concepts (verbatim):

- **source_filter_theory**: "Speech = a SOURCE (glottal pulse or noise) passed
  through the vocal tract acting as a linear FILTER. The source sets
  pitch/voicing; the filter (tract shape) imposes the resonances (formants) =
  spectral envelope. Source and filter are largely independent."
- **production_source_filter_separation** (derivation rule): "the same vowel can
  be said at any pitch, and any pitch can carry any vowel — they factor."
- **vocal_tract_resonance_formants**: formants "appear as spectral peaks";
  "Vowels are defined by F1 (height) and F2 (backness)."

Schema:

| | |
|---|---|
| **Nodes** | `FrameNode` (voiced frame), `SourceNode` (f0/pitch = speaker), `PartialNode` (harmonic k·f0 = source structure), `FormantNode` (envelope peak = filter structure) |
| **Edges** | `has_source`, `harmonic_of` (integer ratio, source), `has_formant` (filter), `formant_above` (carries the F\_{i+1}/F\_i **ratio** — the speaker-invariant relation), `before` (temporal), `transition` (glide) |

A SOUND = a temporal sequence of FrameNodes, each holding a SOURCE subgraph
(f0 + partials) and a FILTER subgraph (ordered formants + spacing-ratio
relations), with before/transition edges between frames. The invariant subgraph
is the FILTER; the speaker-carrying subgraph is the SOURCE.

The filter is estimated by **cepstral liftering** (drop the f0 fine structure,
keep the slow envelope = the tract filter — exactly the source/filter
deconvolution the science describes), then picking the top-3 envelope peaks.

## (2) The invariance numbers — LOSO, FSDD, 6 speakers, 20 utts/(digit,speaker)

Leave-one-speaker-out nearest-class-prototype accuracy (prototypes from the
OTHER speakers only). Chance = 0.10. Session references: raw 0.32, CMVN 0.60.

| Representation | dim | LOSO acc | cross-speaker sep (same − across) |
|---|---:|---:|---:|
| filter graph (collapsed ratios) | 2 | 0.301 | **+0.090** |
| filter graph (ratio trajectory) | 12 | 0.341 | **+0.187** |
| spectrum (flat envelope) | 24 | 0.444 | +0.120 |
| spectrum (trajectory) | 96 | **0.666** | +0.122 |

The fair head-to-head is the matched-shape pair (both trajectories, relations vs
absolute): **filter graph 0.341 vs spectrum 0.666**.

## (3) VERDICT

**The graph representation does NOT, as built, give more speaker-invariance by
construction — it inherits the spectrum's noise rather than dissolving it.** On
absolute LOSO accuracy the filter graph (0.341) is well below the spectrum
(0.666) and below even the session's raw baseline. The honest cause is the one
flagged up front: the extraction (finding the formant peaks) still runs on the
spectrum, so the relational graph is only as clean as that peak-picking — and
top-3 cepstral envelope peaks on 8 kHz FSDD digits are noisy and often mis-pick
(F1/F2 merge, spurious peaks), so the ratio relations are computed from unstable
inputs. The graph inherits the spectrum's problem.

**But the nuance matters and partly vindicates the idea.** The filter graph has
the *highest cross-speaker separation per dimension* of any representation
(+0.187 same−across at dim 12, vs the spectrum's +0.120 at dim 24/96). I.e. the
relational structure that survives extraction IS more speaker-invariant — the
ratio relations genuinely cancel vocal-tract length. The problem is purely that
3 formant peaks carry far less *content* than a 96-bin spectral trajectory, and
each peak is individually unreliable. The relations are cleaner but too few and
too noisy to win on accuracy.

So: the reframe's *premise* (relations are more speaker-invariant than absolute
spectra) shows up in the separation metric, but it does **not** translate into a
representation that would make the CMVN/VTLN/predict-remove chain unnecessary —
because the bottleneck moved from "absolute freqs shift" to "the formant
extraction is lossy and noisy." You don't get invariance for free; you trade the
normalization problem for a formant-estimation problem, and at this extraction
quality the trade is a net loss on accuracy.

### What would change the verdict

The graph idea is bottlenecked on the front-end, exactly as the agent diagnosed
elsewhere ("feature coverage is the ceiling, not feature tuning"):

- **Better formant estimation** (LPC/PLP poles, or formant tracking with
  continuity constraints instead of independent per-frame peak-picking) would
  feed cleaner node values into the same relational graph. The +0.187 separation
  says the relational structure would then likely win.
- **Richer filter subgraph**: more resonance nodes + the full pairwise spacing
  relations (not just adjacent ratios), so the filter carries comparable content
  to a spectral trajectory while staying scale-invariant.
- **Fuse source + filter** rather than discarding the source: the agent's
  multi-ear / complementary-cues result (gammatone vs sharp-F2) suggests the
  separation should *route* cues, not throw the speaker subgraph away.

The reframe is right in spirit and the schema is the agent's own; the honest
finding is that invariance is **not** free — it is rate-limited by how cleanly a
waveform can be turned into formant nodes, and that front-end, not the graph, is
where the next lever is.
