# Evidence-weighted plasticity + habituated audience gain — RESULTS

Registered design: `EVIDENCE_AND_AUDIENCE_WEIGHTING_PREREG.md`. **One
half landed (`audience_gain`); one half was built, measured, and
RETRACTED before shipping (`belief_plasticity`) — reported here as the
headline finding, not a footnote.**

## 1. `belief_plasticity` — RETRACTED

Built exactly as registered: `effective_alpha = belief_plasticity /
(domain_incident_count + 1)`. Measured before finalizing (this arc's own
standing discipline): at `belief_plasticity=0.3`, the Confident resident's
belief **did not move at all after 15 repeated incidents** — computed the
harmonic sum directly: reaching the flip threshold requires `H_n > 5.88`,
i.e. **~200 incidents**, not the "still learns, just slower" the PREREG
predicted.

**This is the count-divided (`1/n`) learning-rate anti-pattern CLAUDE.md's
own F-16 retrospective already diagnosed and named** — *"1/n asserts
stationarity → declare a floor 0.05... Each rate needs a rate"* — measured
independently in that arc across 60 sites, all outside the sd-loop/
shape-codebook family, all requiring an unpaid-debt regress of ad hoc
floors and surprise factors to remain usable. This rung reproduced the
identical failure mode in a 61st site, caught it by measuring before
shipping (not after), and reverted rather than patching with a floor —
patching would have been exactly the "declare a floor 0.05" first step of
the regress the F-16 retrospective already names as the wrong fix.

**`record_incident_outcome`'s `alpha` is reverted to flat application**,
byte-identical to `DOMAIN_SELF_WORTH_PROJECTION_PREREG.md`'s original
design. `belief_plasticity` remains a real personality trait (unchanged,
correctly sourced from `resident["params"]`) — only its FURTHER
weighting-by-evidence-count is retracted, not the trait itself.

## 2. `audience_gain` — LANDED

`effective_audience_gain = base_audience_gain / (claimant_dispute_count +
1)`, `claimant_dispute_count` tracked on the `Resident` node, accumulating
ACROSS domains (audience habituation generalizes; belief content does
not). `seeds/rule_dispute_escalation.json` untouched — the habituated
value is computed entirely by `run_rule_dispute` before being supplied to
that seed's own, unedited `DisputeContext.audience_gain` field.

**Why this one does NOT reproduce the same anti-pattern, checked not
assumed**: `belief_plasticity` governs an ACCUMULATING belief strength
that must overcome an ever-larger opposing force (the harmonic sum grows
unboundedly slowly). `audience_gain` governs a single, BOUNDED per-call
classification threshold (`pressure ≷ 0`) recomputed fresh each dispute —
habituation only needs to shrink the audience TERM below whatever margin
separates the current dispute from the escalate/defuse boundary, not
overcome a compounding opposing sum. Confirmed directly: a marginal
dispute (`band_code=2`, one-slot severity) flips from `escalate` to
`defuse` by the **7th** dispute — a realistic session timescale, not ~200.

## 3. Predictions

1. **First domain incident uses full `alpha`** — moot, since `alpha`'s
   weighting is retracted; flat application was always true, unaffected.
2. **Later domain incidents move belief less, but still eventually flip**
   — `FAILED` as measured (effectively never flips), the direct cause of
   the retraction above.
3. **First dispute uses full `base_audience_gain`** — `PASS`.
4. **Nth dispute feels less audience pressure for the same witness
   count** — `PASS`, confirmed via the marginal-dispute flip.
5. **`claimant_dispute_count` accumulates across domains** — `PASS`; a
   resident habituated by 6 `monopoly_rules` disputes defuses their FIRST
   `chess` dispute at parameters that would otherwise escalate.

## 4. Honesty notes

**Does establish**: `audience_gain` is now a real, habituation-weighted
quantity, landed cleanly, zero edits to the underlying dispute-escalation
seed. Equally important: this codebase's own documented anti-pattern
(count-divided learning rates) was checked FOR, found, and avoided in a
new build — the F-16 retrospective's lesson generalized correctly to a
61st site rather than being reproduced blind.

**Does NOT establish**: any working mechanism for weighting
`belief_plasticity` against real graph state — that remains an open,
correctly-scoped-out problem. A future attempt should NOT reach for
another `1/n`-shaped decay; the sd-loop/shape-codebook family (the ONLY
family CLAUDE.md's own audit found free of this defect class) is the
more promising direction, not explored here.

## 5. Files

- `docs/research/psychology_affect/EVIDENCE_AND_AUDIENCE_WEIGHTING_PREREG.md`
- `docs/research/psychology_affect/EVIDENCE_AND_AUDIENCE_WEIGHTING_RESULTS.md` (this file)
- `domains/can_self_worth_bridge.py` (`record_incident_outcome`'s docstring records the retraction; behavior reverted to flat `alpha`)
- `domains/rule_dispute_full_pipeline.py` (edited: `audience_gain` -> `base_audience_gain`, habituated via `claimant_dispute_count`)
- `tests/test_audience_habituation.py` (4/4, new)
