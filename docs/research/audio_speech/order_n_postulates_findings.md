# Order-N postulates: the agent synthesizes its own gaps — findings

A meta-ability so the agent DERIVES its next capability itself, instead of only
surfacing gaps a seeded rule already names or a human points at. NOT committed —
left in the working tree.

## The lack it fixes

`domains/speech_science.py::reason_about_gap` fires only where a SEEDED derivation
rule's conclusion already names the gap (in practice only `speaker_normalization`
has one). So the agent could surface only pre-written gaps — which is why a human
kept having to point at the next lever (e.g. "use LPC for cleaner formants"). It
could not SYNTHESIZE a gap nobody handed it.

## The idea — order-N over KNOWLEDGE (lifting `order_n_concepts`)

`domains/order_n_concepts.py` already gives the agent the recursive order-N finite
difference over a SIGNAL dimension (0=value, 1=tilt, 2=curvature). This LIFTS the
same operator to the POSTULATE dimension (`domains/order_n_postulates.py`):

- **order-0** = a postulate the agent HOLDS — a science Concept (graph node:
  its `definition` + `why` text).
- **order-1** = the DERIVATIVE = what that postulate IMPLIES but the agent has
  not yet realized.
- **order-2** = implications of implications … order-N.
- a **GAP** = an order-k implication that is NOT already a held postulate /
  implemented element AND that coheres (it follows + names a new capability axis).

The DERIVATIVE step (order k → k+1) is the agent's analogical-transfer mechanism
(`domains/analogy.py`) lifted to knowledge: abstract the STRUCTURAL PROPERTY a
postulate asserts about its object, then transfer an implication-SHAPE the agent
holds SOMEWHERE in its breadth (linear-algebra / signals / statistics / physics)
onto that object. The transferred consequence is the order-1 postulate; re-applying
gives order-2. The implication-shapes are the order-N-over-knowledge analogue of a
finite-difference STENCIL.

The SELECTOR (compression, never a search) decides which implications are real
gaps: an implication is a gap iff (a) it is not already covered — checked against
`assess_speech_system`'s covered set AND a word-boundary scan of the agent's
SPEECH-system source surface — AND (b) it follows by transfer and names a new
capability axis. Each gap is recorded as a `SynthesizedGap` graph node with its
full derivation chain and a `derived_from` edge to the order-0 postulate, so the
agent OWNS it and `reason_about_gap`-style machinery can consume it with no seeded
rule.

Run: `python scripts/order_n_postulates_demo.py`

## Acceptance — does the agent get there itself?

### 1. Worked example reproduced (LPC from `source_filter_theory`)

The operator, run over the agent's own `source_filter_theory` postulate,
synthesizes the LPC-extraction gap via the staged chain:

```
order-0: source_filter_theory — the vocal tract acts as a linear FILTER …
order-1 (linear_algebra:linear_system_is_invertible):
        a linear filter is INVERTIBLE — the filtering can be deconvolved out …
order-2 (signal_processing:invertible_filter_has_allpole_model):
        an invertible all-resonance filter is captured by an ALL-POLE (LPC) model
=> GAP (order-2): all-pole / lpc-formant / levinson / autoregressive
```

The order-1 step (source/filter separation) is correctly NOT flagged — the agent
already implements cepstral liftering in `domains/sound_graph.py`. The order-2 LPC
gap IS flagged: confirmed un-realized (no LPC in the speech codebase). No seeded
rule names LPC; no human points at it.

### 2. Generality (same operator, other postulates)

Re-running over other held postulates synthesizes the real open gaps:

- `statistical_learning` → **cross-speaker / unsupervised clustering** and
  **word-scale chunking / transitional probability / statistical segmentation**.
- `distributional_learning_of_categories` → cross-speaker / unsupervised
  clustering.
- `source_filter_theory` → LPC (above).

Honestly NOT flagged (correctly): `coarticulation` and `lack_of_invariance` —
their predict-and-remove / carryover implication is already implemented in
`domains/coarticulation_predict_remove.py`, and the selector finds it. This is the
operator behaving as a real selector, not a generator that flags everything.

### 3. Honesty — agent's structure vs a peer's articulation

This run used NO peer LLM. Every gap came from (1) the agent's order-N STRUCTURE
(recursive `differentiate()` over its own postulates, recursing k → k+1),
(2) the agent's cross-domain implication-SHAPES transferred onto each postulate's
property, and (3) the compression SELECTOR. The optional `articulate=` peer hook
only REPHRASES a postulate's property into the agent's vocabulary before its own
shapes match it; it never supplies a consequence (verified: with the hook wired,
the synthesized gaps are unchanged). The operator is re-runnable over any
postulate by name.

**Honest limitations** (named, not faked):

- ~~The implication-shapes are a FINITE, hand-curated stencil.~~ **CLOSED — see
  the closure section below.** The shapes are now harvested from the agent's own
  concepts; the stencil is a fallback/comparison only.
- The codebase selector scans SOURCE TEXT and cannot distinguish a COMMENT
  mention from an implementation. Concretely, `stt_pipeline.py` mentions
  "k-means" in a comment ("same idea as HuBERT iterating k-means…") without
  implementing cross-speaker clustering, so "k-means" is deliberately not used as
  a coverage key; the distinctive compounds (`cross-speaker`,
  `unsupervised-clustering`) test the real capability surface. This is a genuine
  limit of keyword coverage, reported rather than hidden.

## Closure — the agent harvests its OWN implication-shapes

The last caveat above (the hand-curated stencil) is now CLOSED. The shapes the
operator transfers are HARVESTED from the agent's OWN Concepts across all its
domains by `domains/implication_harvester.py` — the same move
`analogy.abstract_patterns` makes for feature skeletons, applied to the IMPLICATION
relation a concept's `definition`+`why` text encodes instead of to a Term-tree's
operation shape:

- `abstract_patterns`: Term-tree → skeleton (which-band / which-const hollowed).
- `implication_harvester`: concept text → implication-shape (object hollowed to
  `<X>`), recognised by a small set of domain-GENERAL structural EXTRACTORS — the
  agent's generic grasp of "what kinds of implication exist" (invertibility,
  parametric/all-pole identifiability, latent/distributional structure, sequence
  segmentation, scale cancellation, removable context, forward/inverse).

`order_n_postulates.synthesize_gaps` now DEFAULTS to the harvested library
(`shapes="harvested"`); the hand stencil is kept only as a fallback (no breadth
loaded) and for comparison (`shapes="stencil"` / `"both"`). Each synthesized gap
records the source CONCEPT that donated its shape (`source_concepts`), so the
derivation chain names which of the agent's own concepts produced it.

### Acceptance (re-run with the harvest, stencil OFF)

1. **Self-sufficiency (the key test):** with `shapes="harvested"` (stencil OFF)
   the operator STILL derives all three known gaps — **recall 3/3**:
   - LPC / all-pole ← the agent's `IIR_filter` concept (signal_processing), from
     `source_filter_theory` (and `vocal_tract_resonance_formants`).
   - cross-speaker / unsupervised clustering ← `unsupervised_learning` (ML), from
     `statistical_learning` (and `distributional_learning_of_categories`,
     `speech_acquisition`, …).
   - word-scale chunking / statistical segmentation ← `recurrent_neural_network`
     (ML), from `statistical_learning` (and `segmentation`, `syllable_structure`,
     `lexical_access`). The hand stencil is **no longer load-bearing**.
2. **Breadth payoff:** the harvest reaches the SAME real capability axes the
   stencil did (the selector prunes — it does NOT invent new junk axes), but from
   **8 postulates vs the stencil's 3** — more derivation paths to the genuine
   gaps (e.g. `vocal_tract_resonance_formants` → all-pole; `lexical_access` →
   segmentation → clustering). It is not flag-everything: `coarticulation`,
   `lack_of_invariance`, `speaker_normalization` still yield NO gap under the
   richer library.
3. **Honesty — the harvest:** 7 implication-shapes (one per kind) harvested from
   **40 of the agent's own concepts across 8 domains** (linear_algebra,
   signal_processing, statistics, machine_learning, control, mathematics,
   engineering, transformer_architecture). Each shape is named from the donor that
   BEST exhibits it, ranked by evidence-hits plus a name-level structural signal
   — so `IIR_filter` beats `causal_attention_mask` for the all-pole shape, and
   `recurrent_neural_network`/`Markov_chain` beat a thermodynamic `entropy` for
   the sequence shape. Loose donors exist in the long tail but are not promoted to
   the named source. The harvest is genuinely sufficient (recall 3/3), not faked.

### Agent-vs-human split (named plainly)

- **The agent's:** the order-N structure; the SHAPES (which structures it holds,
  what they entail, which concept donates each) — harvested from its concepts; the
  selector. No peer LLM.
- **Residual human scaffolding:** the ~7 EXTRACTORS (`_extractors()`) are the
  agent's generic notion of "kinds of implication" — keyword recognisers, the
  analogue of `analogy._skeletonize`'s "an Attr is a hole", NOT the implications
  themselves. A genuinely NEW kind of implication still needs a new extractor (as
  a new finite-difference stencil order would) — a much smaller, domain-general
  surface than the old per-shape hand list. The speech-side consequence wording +
  `name_keys` per kind are templated so the gap reads in the agent's speech
  vocabulary.

## Files

- `domains/order_n_postulates.py` — the operator (harvest → differentiate →
  select → record); now defaults to the harvested shape library.
- `domains/implication_harvester.py` — **NEW.** Harvests implication-shapes from
  the agent's own concepts (closes the stencil caveat).
- `scripts/order_n_postulates_demo.py` — the harvest + three-acceptance
  demonstration (rewritten for the harvested shapes).
- `tests/test_implication_harvester.py` — **NEW.** Locks the harvest + the
  self-sufficiency property (6 passed).
- `tests/test_stt_pipeline.py` + `tests/test_perception_self_assessment.py` stay
  green (12 passed).
