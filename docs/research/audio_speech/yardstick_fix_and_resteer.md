# Fixing the yardstick + re-steering the loop

Two steps, both verified live on real FSDD through the agent's own perception
(`scripts/yardstick_fix_resteer.py`):

1. **Fix the yardstick** — gate `perception_self_assessment`'s frontier flag with a
   graph-resident *reliability* Rule so it never mis-fires on a starved / merge-grain
   sample.
2. **Re-steer the loop** — with the fixed yardstick the units pass at scale, perception
   drops out as the frontier, and the guided ranker lands on the genuine
   recognition-stage gap instead of the iter-6 perception/units artifact.

## Why the old yardstick mis-fired (verified)

On the 108-utterance FSDD subset the agent's DTW-merge unit stream was
**singleton-dominated**: lexicon 31, tokens 61 — about two tokens per distinct unit.
With that little data the bigram predictor has no statistical power, so its top-1 equals
its own frequency baseline → `predict_over_freq = 1.0`. The old frontier Rule fired
`frontier = 'perception'` whenever `predict_over_freq < floor`, with no check on whether
the reading could be trusted. The flag was an **unreliable-measurement artifact**, not a
real verdict on the units: at full scale (1200 utts, tok/lex 7.4) the same units clear
the floor easily (`predict_over_freq ≈ 10.7`). The real recognition loss is downstream
(chunker → lexicon), not the units.

## Step 1 — the reliability gate (graph-resident Rule)

The fix adds two **reliability witnesses** as graph predicates over dials on the
`PerceptionSelfRoot`, and routes the verdict through them in a single native
`IfThenElse` term (`install_perception_frontier_rule`):

- **(a) adequate sample** — `tokens_per_lexicon >= min_tokens_per_lexicon` (dial 4.0).
  A stream with ~1 token per distinct unit is singleton-dominated; any `pof` off it is
  noise. The 108-utt subset sits at tok/lex 1.97 → inadequate.
- **(b) shuffle bites** — a shuffle control (`shuffled_over_freq`, computed in
  `measure_unit_predictability` by pooling tokens, destroying order, re-chunking, and
  recomputing `pof`) must drop meaningfully below the real `pof`
  (`predict_over_freq - shuffled_over_freq >= shuffle_bite_margin`, dial 0.10) for an
  apparent PASS to be believed.

The verdict tree (all native Terms, dials on the root, no Python decision):

```
bad_units  = (predict_over_freq < floor) OR (compress_ratio > ceiling)
adequate   = tokens_per_lexicon >= min_tokens_per_lexicon
bites      = (predict_over_freq - shuffled_over_freq) >= shuffle_bite_margin

# a FAIL is reliable iff the sample is adequate (power to assert "no order");
# a PASS is reliable iff the shuffle bites (real order, not a small-sample fluke).
reliable   = IfThenElse(bad_units, adequate, bites)

frontier   = IfThenElse(reliable, (bad_units ? 'perception' : 'none'), 'inconclusive')
reliability= IfThenElse(reliable, 'high', 'low')
```

When the reading is unreliable the Rule writes `frontier = 'inconclusive'` and
`reliability = 'low'`, and it does **not** arm the two downstream decisions
(`frontier_rank_pending`, `perception_gap_pending`) — so an inconclusive reading can
never pull the rank to 1.0 or synthesise a perception/units gap.

### Is it a general predicate, or just "ignore 108"? (honest)

General. The gate keys off `tokens_per_lexicon` and the shuffle gap, both computed by the
maths from any unit stream — never off a sample size or a constant for the FSDD subset.
`test_gate_is_general_over_measured_streams_not_a_hardcoded_subset` proves it end-to-end:
a synthetic singleton-dominated stream (every unit unique) is gated to `inconclusive`; a
well-sampled ordered stream is a reliable `none`. And
`test_reliable_failing_sample_still_flags_perception` proves the gate still flags a
genuinely structureless **well-sampled** stream — it suppresses only *starved* readings,
not real failures, so it is not "ignore small N" blindly.

Note on the starved case: the shuffle predicate happens to read `bites=True` there
(degenerate shuffle → 0.0), but that is irrelevant — `bad_units` is true, so reliability
is routed through the **adequate** branch, which is `False`. Adequacy is what suppresses
the artifact; shuffle governs the PASS direction.

## Step 1 — live verification

```
[STARVED 108-utt subset]  108 utterances -> 28 usable sequences
  tokens=61  lexicon=31  tokens/lexicon=1.97  (min adequate 4.0)
  predict_over_freq=1.000  shuffled_over_freq=0.000  shuffle_gap=+1.000  floor 1.25
  gate predicates: adequate_sample=False  shuffle_bites=True  bad_units=True
  => FRONTIER FLAG = 'inconclusive'   reliability = 'low'

[RELIABLE at-scale sample]  1200 utterances -> 348 usable sequences
  tokens=741  lexicon=100  tokens/lexicon=7.41  (min adequate 4.0)
  predict_over_freq=10.667  shuffled_over_freq=0.500  shuffle_gap=+10.167  floor 1.25
  gate predicates: adequate_sample=True  shuffle_bites=True  bad_units=False
  => FRONTIER FLAG = 'none'   reliability = 'high'
```

The starved subset that mis-fired in iter-6/7 is now **gated** (`inconclusive`, low);
the at-scale units **read as passing** (`none`, high).

## Step 2 — the re-steered loop

With perception gated out, the frontier rank is the far-downstream default (999), so the
guided ranker no longer redirects to a perception/units gap, and the Step-1b synthesis
Rule mints no perception artifact:

```
FIXED frontier: flag='none' reliability='high' -> level='none' rank=999.0
perception/units gap synthesised from the yardstick? NO (units pass -> no gap)

--- iter-6 (OLD yardstick, starved 108-utt subset) ---
  frontier flag : 'perception' (FALSE — small-sample artifact)
  frontier rank : 1.0 (perception_units)
  GUIDED PICK   : ['improve-unit-predictiveness', 'perception-units']  (synthesised artifact)

--- re-steered (FIXED yardstick) ---
  frontier rank : 999.0 (far-downstream default -> no redirect)
  GUIDED PICK   : ['unsupervised-clustering', 'cross-speaker-clustering']  level='recognition'
```

The guided pick lands on the **recognition stage** (cross-speaker clustering — the
chunker → lexicon loss the continuous-speech end-to-end found), **not** the iter-6
perception_units artifact.

### Honest

- The gate genuinely fixes the mis-firing as a general reliability predicate (sample
  adequacy + shuffle witness), not a hard-coded "ignore 108". Proven by the general /
  reliable-fail tests.
- The loop re-steers to the real frontier: the iter-6 synthesised perception gap no
  longer lingers, because the synthesis Rule is only armed by a *reliable* 'perception'
  reading, which a passing at-scale sample never produces.
- The re-steered pick is currently the *unguided* top axis (recognition, payoff 82),
  i.e. the guidance is now a no-op (`pick_changed=False`) — correct, since with no
  upstream frontier there is nothing to redirect toward. The honest residual: the
  ranker's top recognition axis is `cross-speaker-clustering`; the related
  `transitional probability / word-scale chunking` segmentation axis is the runner-up.
  Both are the genuine downstream recognition-stage work; the loop is now pointed there
  rather than at the perception artifact.

## Files

- `domains/perception_self_assessment.py` — shuffle control + `tokens_per_lexicon` in
  `measure_unit_predictability`; reliability dials on the root; gated frontier Rule;
  `get_reliability`.
- `tests/test_perception_self_assessment.py` — 6 new gate tests; existing failing-units
  fixtures updated to adequate samples (the signal schema now carries the reliability
  fields).
- `scripts/yardstick_fix_resteer.py` — the live verification driver for both steps.
