# Harvest precision fix — fix the FIXER at the source

## The problem (iter-5 noise)

The rule-walker harvest (`domains/implication_harvester.py:harvest_shapes_from_rules`,
commit 7dced20 — walks the agent's Rules' `if->then` to harvest ~500
implication-shapes across 24 domains) produced **promiscuous shapes**. It built a
shape's `match_patterns` from the **bare single content words** of the Rule's
if-clause and `differentiate()` fired the shape if **ANY ONE** of those words
appeared in a postulate (OR semantics).

So `babble_loop_is_thermal_sampling` (if-clause: `"substrate runs babble cycles"`)
became `match_patterns = [\bsubstrate\b, \bruns\b, \bbabble\b, \bcycles\b]` and
fired whenever `\bsubstrate\b` OR `\bruns\b` appeared — on **2864 / ~5300
postulates (54%)**. A shape that fires on half the substrate carries ~0 bits and
unifies nothing: pure noise. 24 / 514 shapes fired on >10% of the corpus.

The agent's compression-payoff ranker (`payoff = Count(unifies edges)`) then
**rewards** that promiscuity — the Argmax pick landed on the most content-free gap
(`[mcmc, network]`, payoff 224, derived by one promiscuous shape with one canned
consequence text).

## The wrong fix (the one being removed)

`domains/gap_prioritiser.py` had a **specificity GATE**
(`PROMISCUITY_FRAC = 0.10`, `shape_firing_breadth`): drop the firings of any shape
that fires on >10% of the corpus before counting `unifies` edges. That *fixes the
outcome* — it makes the picker TOLERATE noise. Worse, it didn't even work: with
the gate ON the pick was STILL an artifact (`[data, placement]`, one shape, one
canned text), because gating removed the worst 24 shapes but the next-worst still
won.

## The fix (the rule-walker — specific AT BIRTH)

A Rule's `if`-clause is a **structural condition**: a conjunction of co-occurring
content terms. The fix reads that antecedent **faithfully**:

- `harvest_shapes_from_rules` now collects the content words of **all** the
  if-clauses and emits the shape with `match_mode = "all"` — the shape fires on a
  postulate only when that **whole structural signature CO-OCCURS**, not when one
  fragment appears.
- Shapes whose entire antecedent reduces to **a single content word are DROPPED**
  — one bare token cannot discriminate, so the rule-walker doesn't emit it.
- `differentiate()` (`domains/order_n_postulates.py`) honours `match_mode`:
  `"all"` → `all(re.search...)` for rule-derived shapes; the 7 hand-authored
  regex-extractor kinds keep their `any` (OR) default, since each of their patterns
  is a legitimate alternative surface form of one property.
- `shape_firing_breadth()` (`gap_prioritiser.py`) honours `match_mode` too, so the
  breadth it measures matches what `differentiate()` actually fires on.

Why a single AND-regex was NOT used: a lookahead-conjunction
(`(?=.*\bw1\b)(?=.*\bw2\b)...`) over long meta-essay text backtracks
catastrophically (~100x slower; the measurement loop hung). A list of fast
per-word anchors combined by `all()` in `differentiate` is equivalent and fast.

This is a **GENERATION** fix (the harvest), not a downstream filter. With it the
promiscuous shapes never exist, so the gate becomes moot.

## Measured live (iter-5 sample, 400 postulates; corpus ~5300)

### 1. Promiscuity — KILLED

| metric (firing-breadth over corpus) | BEFORE | AFTER |
|---|---|---|
| max firing-breadth | **2864** (54%) | **314** (5.9%) |
| median | 174 | **0** |
| p90 | 422 | **1** |
| shapes firing on >10% | **24** | **0** |
| shapes firing on >5% | 140 | **1** |
| top-5 offenders | all `rule_derived__*` @ ~2800 | NO rule-derived in top-5 |

Every rule-derived shape is now ≤19 firing-breadth (top rule-derived = 7). The
`babble_loop_is_thermal_sampling` shape that fired on 2864 now fires on a handful
or zero — exactly when "substrate runs babble cycles" structurally co-occurs.

### 2. Artifact rate / open-gap volume

| metric | BEFORE | AFTER |
|---|---|---|
| OPEN gaps recorded (400-postulate sample) | 1288 | **39** |
| distinct capability axes | 74 | 2 |
| single-shape-artifact fraction | 93.9% | (see note) |

The 1288 → 39 collapse is the *correct* consequence: ~1200 of the "open gaps" were
one promiscuous shape spamming the same canned consequence across hundreds of
unrelated postulates. Removing the noise leaves the genuine derivations.

### 3. Ranker pick is genuine (gate OFF)

- **BEFORE** top pick: `[mcmc, network]`, payoff 224, via 1 promiscuous shape
  `rule_derived__babble_loop_is_thermal_sampling`, 1 canned text → **ARTIFACT**.
- **AFTER** top picks (gate OFF):
  1. `unsupervised-clustering, cross-speaker-clustering` — payoff 24
  2. `transitional probability, word-scale chunking` — payoff 12

  Both are **genuine speech capabilities the agent derived itself** (the
  cross-speaker clustering + word-scale chunking frontier the loop already found),
  not the content-free meta-artifact.

### 4. The gate is MOOT

With the harvest fixed, `PROMISCUITY_FRAC = 0.10` gates **0 / 511 shapes** (was
24). Picks are **byte-identical with the gate ON vs OFF**:

```
GATE OFF picks: [('unsupervised-clustering,...', 23), ('transitional probability,...', 16)]
GATE ON  picks: [('unsupervised-clustering,...', 23), ('transitional probability,...', 16)]
MOOT (identical top picks): True
```

Fixing the source removed the need for the outcome-patch. The gate code is left in
place (it does no harm and breaks nothing) but is no longer load-bearing.

## Honest limits

1. **The fix is fully done for the named source (the rule-walker, 7dced20).** All
   rule-derived shapes are now specific (≤19 breadth, mostly 0–7).

2. **A separate, pre-existing promiscuity source is now exposed.** Once the
   rule-walker noise clears, the two highest-breadth shapes are the
   hand-authored **regex-EXTRACTOR** kinds (NOT the rule-walker, NOT 7dced20):
   `latent_structure__from__unsupervised_learning` (314, 5.9%) and
   `sequence_segmentation__from__recurrent_neural_network` (169, 3.1%). These use
   OR-of-single-broad-words by design (`distribut`, `\bmodes?\b`, `statistic`),
   so they pick up some false positives (e.g. `sculpting_3D`, `layers_blend_modes`
   via the bare word `modes`).

   I deliberately did **not** tighten them, and this is the honest part: requiring
   co-occurrence (`distribut AND cluster/categor/...`) drops their genuine
   derivation surface from 144 → **4** postulates, which would gut the very
   clustering/segmentation capability the agent designed these shapes to derive
   (and which is the genuine top pick). Tightening the hand-authored extractors is
   a *different* tradeoff than fixing the rule-walker; it would need the agent's
   own judgement about which broader speech postulates the clustering axis should
   legitimately unify. Flagged, not silently changed.

3. **Corroboration (≥2 distinct shapes → same capability) did not rise** (3 → 0
   under the strict measure). This is because the genuine surviving axes are each
   produced by ONE *specific* shape — which is NOT the iter-5 "artifact" pathology
   (a *promiscuous* shape). The iter-5 artifact heuristic ("1 via_shape = artifact")
   conflates "promiscuous" with "single-shape"; after the fix the single shape
   behind each axis is highly specific and unifies genuinely-related postulates, so
   the count of *promiscuous-shape* artifacts is what dropped to ~0, even though the
   count of *multi-shape-corroborated* axes did not rise. The cleaner signal is the
   firing-breadth distribution (criterion 1), which is unambiguous.

## Parallel-stream note

The rule-walker is commit 7dced20 (a parallel stream). This fix **layers on top**
of `harvest_shapes_from_rules` (it does not delete or rewrite the rule-walker — it
changes WHAT it extracts and adds the `match_mode` field). No clobbering. The
`match_mode` field is additive and back-compatible: shapes without it default to
the prior `any` behaviour, so existing callers/tests are unchanged.

A **pre-existing** test failure
(`tests/test_implication_harvester.py::test_harvest_excludes_the_speech_science_postulates`)
fails identically on the pristine tree — it is a test-vs-corpus drift in the
`harvest_shapes` (regex-extractor) exclude logic (the corpus now holds math
concepts like `determinant` in non-speech Mts), unrelated to this change. Left
as-is.

`tests/test_stt_pipeline.py` and `tests/test_perception_self_assessment.py` stay
green (12 passed). 15 / 16 implication-harvester + frontier tests pass (the 1
failure is the pre-existing one above).

## Files changed

- `domains/implication_harvester.py` — `harvest_shapes_from_rules`: full-antecedent
  conjunction patterns + `match_mode="all"`; drop single-content-word shapes.
- `domains/order_n_postulates.py` — `differentiate`: honour `match_mode`
  (`all`/`any`).
- `domains/gap_prioritiser.py` — `shape_firing_breadth`: honour `match_mode`.
- `scripts/_harvest_precision_measure.py` — the before/after measurement harness.
