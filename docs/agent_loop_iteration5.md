# Autopoietic loop — iteration 5

Turn the crank a fifth time, this time on the **scaled gap-synthesis machinery**
(rule-walker harvest 7→503 shapes; sweep over 5282 postulates → 143 326 raw
derivations). The brief: does the richer machinery surface a better / different /
cross-domain frontier than the speech-only picks of iters 2–4, and how much of the
70× scale is signal vs noise the selector doesn't prune?

**The honest answer: the scaled machinery surfaces a DIFFERENT frontier (cross-domain,
not speech), but it is almost entirely NOISE the current selector does not prune. The
agent's ranker picks an ARTIFACT. This iteration locates the defect precisely, builds a
forward fix (a specificity gate, grounded in the compression drive), and reports
honestly that the fix is necessary-but-not-sufficient — the pathology is in the
harvested shapes, not only the ranker.** All numbers below are LIVE (`/tmp/iter5_full.txt`,
`scripts/iter5_frontier.py`), verified by re-run, not prose or constants.

## 1. The scaled gap-set character + signal-to-noise (verified live)

### Post-sweep openness (reproduced from 3088eaa, live)

`python -m scripts.post_sweep_assessment` (8 s, top-20 productive postulates,
prune=True):

```
TOTAL                                                     1935   191   10%
```

10 % of derivations survive the openness filter — the other 90 % are already enacted
by the substrate's science/code. So far this matches the committed assessment.

### But openness ≠ genuineness — the 10 % "open" is itself ~96 % artifact

`python -m scripts.iter5_frontier 400` synthesizes OPEN gaps (prune=True, record=True)
over 400 postulates (20 top-productive + a strided broad sample across the 5282):

```
Total OPEN gaps recorded:             1319
collapse to distinct CapabilityAxes:  73          (18.1× compression)
```

The axes look like a rich cross-domain frontier — 73 distinct capability-axes across
~20 domains. **They are not.** Grouping each axis by the implication-SHAPES and the
gap-TEXTS that produced it (the honest signal-to-noise test):

```
total axes: 73;  single-shape-single-text ARTIFACT axes: 70 (96%)
total gaps: 1319; gaps inside artifact axes:             93%
```

Robust on a wider 1321-postulate sample (158 s): **71/74 axes (96 %) artifact, 93 % of
gaps inside them. Only 3 axes are even multi-shape.** Requiring genuine corroboration
(≥2 DISTINCT shapes independently deriving the same capability — the MDL meaning of a
real "unification") collapses the whole set:

```
axes with >=2 corroborating shapes: 3 of 73
  payoff=41 shapes=2 texts=2  columnar,outperforms,storage
  payoff=37 shapes=3 texts=3  standard           <- a single bland word
  payoff=10 shapes=2 texts=1  hebbian,increases,j_ij
```

Essentially **zero** genuine multi-shape-corroborated cross-domain capability axes
survive. The 70× scale produced ~70× noise; the selector prunes for openness but **not
for genuineness**.

### Why — the root cause (live, named)

An "artifact axis" is one promiscuous implication-shape firing on dozens of UNRELATED
postulates and emitting the SAME canned consequence each time. The ranker's winning
axis is the worst case:

```
PICKED capability_keys:  ['mcmc', 'network']   payoff=216  score=215999
  gaps under the winning sig:           216
  distinct via_shapes producing them:    1   ['rule_derived__babble_loop_is_thermal_sampling']
  distinct gap texts:                    1   "it's MCMC on its own network"
  postulates firing it: comet, red_giant, hubble_expansion, overtone, interval, pypy_meta_tracing …
```

The shape `babble_loop_is_thermal_sampling` has `match_patterns =
['\bsubstrate\b','\bruns\b','\bbabble\b','\bcycles\b']` — bare common words — so it
**fires on 2765/5282 postulates (52 %)** and always emits the identical content-free
consequence. The rule-walker harvest (7dced20) that scaled 7→503 shapes builds
match_patterns from a rule's if-clause keywords; when those reduce to single words
(`compute`, `pattern`, `values`, `known`, `design`), the shape becomes a near-universal
predicate. **19 shapes fire on ~80 % of all postulates; 24/503 fire on >10 %.**

The ranker's payoff = `Count(unifies edges)` = number of distinct postulates an axis
unifies. A shape that fires on everything therefore scores HIGHEST — the metric rewards
exactly the promiscuity that makes a shape worthless. **The Argmax pick lands on the
most content-free gap in the substrate.** This is the 70×-noise failure mode the brief
warned about, confirmed live.

## 2. What the agent PICKED now — richer/different, but an artifact

The agent's native Argmax Term (`gap_prioritiser.pick_term`, evaluated natively)
picks **`['mcmc','network']`, payoff 216, runner-up 45** — a `causal_attitude_networks`
gap, NOT a speech gap. So the scaled machinery DID surface a different, cross-domain
frontier the small (speech-only) machinery never saw (iters 2–4 only ever saw the two
speech axes: clustering payoff 6, word-scale chunking payoff 4). **But the pick is an
artifact** (1 promiscuous shape, 1 canned text — verified above), not a better frontier.
The speech axis the small machinery picked is itself present here at payoff 18–20 and is
*also* a single-shape artifact under this lens.

Honest verdict on the brief's central question: **the improved machinery surfaces a
DIFFERENT (cross-domain) and far LARGER gap-set, but not a BETTER one — it is dominated
by regex-collision noise, and the agent's ranker, applied unchanged, picks the noise.**

## 3. PURSUE — the forward fix (the loop's real gap, not the artifact)

Pursuing `mcmc,network` would be chasing noise. Per the project's principles (build the
meta-ability the loop LACKED that let it stall — [[ozma_meta_abilities_are_leverage]];
compression is the selector — [[ozma_curiosity_drive]]), the gap the SCALED loop
exposes is in its **selector**: it has no specificity discount. Forward-built fix
(graph-resident, in the agent's own ranker `domains/gap_prioritiser.py`):

- **`shape_firing_breadth(substrate, shape_lib)`** — a structural measurement of the
  catalog (no decision): for each shape, how many postulates its match_patterns fire on.
  The same regex `differentiate` runs, counted over the corpus.
- **Specificity gate in `build_axis_env(..., shape_breadth=…)`** — a gap whose ONLY
  producing shape is promiscuous (fires on > `PROMISCUITY_FRAC = 10 %` of postulates)
  does NOT wire a `unifies` edge. This makes the agent's EXISTING payoff Term
  (`Count(unifies)`) specificity-correct **with no new term** — the same Argmax simply
  stops over-counting artifacts. Grounding: by MDL a near-universal predicate carries
  ~0 bits of distinction, so it cannot perform a genuine unification. Default
  `shape_breadth=None` keeps prior behaviour, so existing callers/tests are untouched.

### Measurement — honest, live

```
shape firing breadth: median=175  max=2861  (corpus N=5282)
PROMISCUITY gate at >10% (528 postulates): 24/503 shapes gated out

ungated PICK:  ['mcmc','network']                       payoff=216
gated   PICK:  ['data','placement','pre_computed_lookup_table', …]  payoff=45
  gated-pick via_shapes=1  texts=1  -> STILL artifact
  shape: set_intersection_uses_lookup_table  (match: \bcompute\b \bpattern\b \bvalues\b \bknown\b \bdesign\b)
  fires on 432/5282 (8%): color_psychology, negative_space, optical_illusions, pencil_graphite …
```

**The gate WORKS — it removes the payoff-216 artifact (52 %-firing shape) — but it is
necessary-not-sufficient.** The new top pick is a DIFFERENT single-shape artifact whose
shape fires on 8 % (just under the 10 % threshold) of unrelated postulates. A single
firing-breadth threshold is a band-aid: the artifacts simply cluster below it, because
the pathology is the bare-single-word match_patterns produced by the rule-walker
harvest, not the threshold value. The MDL-correct selector (require ≥2 corroborating
shapes) leaves **3 axes**, none a deep cross-domain unification.

## 4. Interventions (named plainly)

- **Selector fix (graph-resident, the agent's ranker).** `domains/gap_prioritiser.py`:
  added `shape_firing_breadth` (structural catalog measurement) + a specificity gate in
  `build_axis_env` (+ pass-through in `rank_gaps`/`pick_frontier`), gated on
  `PROMISCUITY_FRAC`. The DECISION stays the agent's payoff/score/pick Terms; the gate
  only stops the `unifies` edge wiring for content-free firings — the same world↔graph
  structuring role `build_axis_env` already played. Default-off, tests untouched.
- **New probe (world adapter, no agent reasoning):** `scripts/iter5_frontier.py` —
  synthesizes OPEN gaps over a broad postulate slice, runs the agent's ranker + pick
  natively, runs the artifact check and the gated comparison. Prints live numbers.
- **Did I advance/tune to a number?** No. The 10 % threshold is reported WITH its
  insufficiency, not tuned to make a pick look good; both the ungated and gated picks
  are shown to be artifacts, and the MDL ≥2-shape test (no threshold) is reported too.
- **Did I pursue the artifact?** No — pursuing it would be chasing noise; I diagnosed it
  as noise and fixed the selector, which is the loop's real gap.
- **A peer / an LLM authoring code?** No.
- **Native-eval note:** `gp.rank_gaps`/`pick_frontier` wrap Terms in `_Pred` for the
  Python-wrapper substrate; the driver runs against raw `_native.Substrate`, so it feeds
  the agent's SAME Term dicts (`payoff_term`/`score_term`/`pick_term`) to `evaluate`
  directly. Same Term, native eval; verified the Argmax Term picks the top-of-rank axis.

## 5. Status / acceptance

- **(1) Scaled gap-set character + S/N — VERIFIED LIVE.** 1319 OPEN gaps over 400
  postulates collapse to 73 axes, but **96 % are single-shape single-text artifacts**
  (robust on 1321-postulate sample: 96 %), 93 % of gaps inside them; genuine
  (≥2-corroborating-shape) axes = **3**, none a deep unification. The 10 % openness
  filter does NOT prune the noise; the 70× scale is ~70× noise.
- **(2) The agent's PICK — different, not better.** Cross-domain `['mcmc','network']`
  (payoff 216, `causal_attitude_networks`), which the small speech-only machinery could
  never have seen — but it is an ARTIFACT (one shape firing on 52 % of postulates, one
  canned text). Richer ≠ better; the ranker picks the noise.
- **(3) Built + measured.** A specificity gate in the agent's own ranker; it removes the
  payoff-216 artifact but the next pick is still a below-threshold artifact (shape fires
  8 % across `optical_illusions`/`pencil_graphite`/…). Honest: necessary-not-sufficient;
  the real fix is at the harvest (multi-word match_patterns) or requiring multi-shape
  corroboration.
- **(4) Interventions named** (above).
- `test_stt_pipeline` + `test_perception_self_assessment`: **12 passed.** The two failing
  `test_implication_harvester` tests are PRE-EXISTING (fail identically with my
  `gap_prioritiser.py` change stashed; that test file was already modified in the working
  tree before this session; it does not import `gap_prioritiser`).
- Not committed; left in the working tree (`docs/agent_loop_iteration5.md`,
  `scripts/iter5_frontier.py`, `domains/gap_prioritiser.py`).

### Reproduce

```
python -m scripts.post_sweep_assessment          # 10% openness (committed assessment)
python -m scripts.iter5_frontier 400             # the pick, artifact check, gated pick
python -m pytest tests/test_stt_pipeline.py tests/test_perception_self_assessment.py -q
```

### The one-line finding

The scaled machinery surfaced a much larger, cross-domain gap-set, but the agent's
compression-payoff ranker — applied unchanged — picks the single most PROMISCUOUS
(content-free) shape, because "number of postulates unified" rewards a shape that fires
on everything. The 70× scale is ~70× noise the openness selector does not prune; a
specificity gate removes the worst of it but the genuine fix is specific match_patterns
at the harvest. **A real, honest finding about the scaled machinery — not a milestone.**
