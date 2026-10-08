# PREREG — resolving H2: does grounding-weighted shift beat flat shift when the instrument can SEE direction?

**Committed BEFORE any number.** Follows PREREG-then-measure + CLAUDE.md. This
reopens the ONE honest null in the induced-belief arc (INDUCED_BELIEF_RESULTS.md
H2: grounding-weighted vs flat 0.1σ came back NEUTRAL — KS worse by +0.0032 —
"unresolvable without sealed outcomes"). The claim here is that the null was an
INSTRUMENT artifact, not a real result, and names the fix before measuring it.

## Why the original H2 could not resolve (diagnosis, from the code)

`measure_h2.py` as built has two structural blindspots:

1. **Random shift direction.** `unit_dir(name, dir_seed)` is a coin flip on a
   hash, averaged over 8 random assignments. So both arms shift in an ARBITRARY
   direction; the test measures "random-direction shift of magnitude A vs
   magnitude B," never "correctly-directed shift." The ToM arm's whole value is
   that it shifts in the RIGHT direction with grounding-scaled magnitude — the
   test cannot see that.
2. **Direction-agnostic realized proxy.** `run_variogram_eval.make_realized`
   is a symmetric common-factor draw with no relation to any text signal, so a
   correctly-directed shift earns nothing and an over-confident wrong shift
   loses nothing on expectation. The instrument is blind to direction quality.

Net: the original H2 asked a question its instrument was constructed not to
answer. NEUTRAL was the only possible outcome; it is not evidence about the
mechanism.

## What is under test now

The mechanism the arm actually implements: shift the band by
`direction(winning CAN stance) × grounding_weight`, where grounding_weight is
the transitive `grounding_reach` read (grounding IS the confidence). Two things
must both be true for this to be the right design, and each is a hypothesis:

- it must HELP when the text signal is real and correctly typed (a
  well-grounded, correctly-directed shift beats no shift), and
- it must NOT HURT (much) when the text signal is absent/wrong (a poorly-grounded
  read shifts ~nothing, so it degrades gracefully — the "silence not error" /
  GroundingGap discipline, now measured on the SCORED composite, not just H3's
  shift ratio).

## The fix (named before building)

1. **A DIRECTION-AWARE realized proxy.** Extend `make_realized` (do NOT edit it;
   add a sibling `make_realized_text_aware`) so that, for a fraction `p_signal`
   of (unit, asset) cells that carry a real ToM decode with a known gold
   direction, the realized outcome is nudged in that gold direction by a fixed
   effect size `e` (in cell-σ), on top of the same common-factor co-movement the
   Phase-2 proxy already produces. Cells with no signal, and a `1 - p_signal`
   fraction of signalled cells (the typer's real error/abstain rate), get the
   UNCHANGED symmetric proxy. This makes the realized outcome correlate with the
   text ONLY to the degree the corpus actually informs it — the honest upper
   structure, with `p_signal`/`e` swept, never hand-fit to a winning number.
   Still RAW_UNRANKABLE (it is a proxy, not the sealed outcome); it is a
   direction-SENSITIVE relative instrument, stated as such.

2. **REAL per-cell shift direction from the arm**, replacing the coin flip. The
   shift direction for each (unit, asset) cell is the arm's OWN decoded
   `direction` (up/down/none) from the corpus, and the magnitude is the arm's
   OWN `grounding_weight` for that read — i.e. the SCORED forecaster runs the
   real ToM decode per cell, not a synthetic sign. Cells with no decode shift 0.

3. **Wire the graded shift into the SCORED forecaster path.** The arm's
   `decode_utterance` already returns `{direction, marginal, grounding_weight,
   shift}`; the scored forecaster must apply `shift` per cell as the band
   translation (contract-preserving per-cell additive, the same discipline
   `apply_band_shift` already uses). Confirm the scored path uses the graded
   `shift`, not a flat constant.

## Arms (all contract-preserving, same base draws)

1. `no_shift` — text-blind base (the floor).
2. `flat_0.1sigma` — shift every signalled cell by ±0.1σ in the arm's decoded
   direction (flat magnitude, correct direction). Isolates magnitude policy.
3. `grounding_weighted` — shift by `0.1σ × grounding_weight` in the arm's
   decoded direction (graded magnitude, correct direction). The mechanism.

The difference between arms 2 and 3 is now PURELY the magnitude policy, with
direction held correct for both — so a win for arm 3 is a win for
grounding-weighting specifically, not for "having a direction."

## Hypotheses (falsifiable, pre-declared)

- **H2a (helps under signal):** on a direction-aware proxy with `p_signal>0`,
  `grounding_weighted` has lower mean composite than `no_shift`. CONFIRMED iff
  composite(gw) < composite(no_shift) across the swept `p_signal ∈ {0.3,0.5,0.7}`
  and `e ∈ {0.5,1.0}σ`, at the arm's REAL per-cell directions. A null (no better
  than no_shift even when text is real+correct) means the shift magnitude is
  mis-scaled or the mechanism does not convert direction into composite gain —
  reported as headline.

- **H2b (grounding-weighting vs flat — the reopened question):** compare
  `grounding_weighted` to `flat_0.1sigma`, BOTH correctly directed. Pre-declared
  reading: grounding-weighting should win or tie when the typer's confidence is
  informative — i.e. when higher grounding_weight correlates with correct
  direction. Measure composite AND tail for both. WIN iff composite(gw) ≤
  composite(flat) AND tail(gw) ≤ tail(flat)+5% tol, across the sweep. If flat
  wins, that is a real finding: a flat shift at the typer's precision is as good
  as grading it, and grounding-weighting buys calibration but not composite —
  report it, do not tune to reverse it.

- **H2c (graceful under no signal):** at `p_signal=0` (text carries nothing),
  `grounding_weighted` composite is within noise of `no_shift` (the poorly-/un-
  grounded reads shift ~0). CONFIRMED iff |composite(gw) − composite(no_shift)|
  at p_signal=0 is smaller than the p_signal>0 gain in H2a — degrades
  gracefully, does not actively hurt on empty text. This is the composite-level
  version of H3's guard.

## What a null means (pre-committed)

- H2a null → the arm types direction well (H1) but the shift does not convert to
  composite gain even on a direction-aware proxy: the band-shift magnitude/shape
  is the problem, not the typer. Localises the remaining work to the shift
  transform, not the ToM decode.
- H2b flat-wins → grounding-weighting is calibration-neutral-to-positive but not
  a composite lever over a flat correctly-directed shift; ship flat (simpler),
  keep grounding_weight only for the H3 guard (attenuate-to-0 on ungrounded).
  A legitimate, useful finding.
- H2c hurts → the guard does not hold at the composite level; the shift must be
  hard-gated to 0 on GroundingGap in the scored path, not just attenuated.

## Discipline

- REUSE the Phase-5 PIT/KS/tail machinery + the REAL reference scorer
  (`qfbench2_common.scoring.crps`) + the Phase-2 proxy as the SYMMETRIC base.
  Only ADD `make_realized_text_aware` and the real-direction arm; invent no new
  metric.
- Sweep `p_signal`/`e`; never hand-fit to a winning cell. Report the whole grid.
- RAW_UNRANKABLE stated on every number; the proxy is direction-SENSITIVE but is
  not the sealed outcome.
- No fabricated numbers; nulls are findings; proven vs assumed explicit.

## Deliverables

- `H2_RESOLUTION_RESULTS.md` — the swept grid for H2a/H2b/H2c, verdicts, and an
  honest statement of what the direction-aware proxy can and cannot establish
  about the sealed board.
- `measure_h2_directed.py` (new; original `measure_h2.py` left intact as the
  record of the instrument-blind null) + `make_realized_text_aware` sibling.
- confirmation the scored forecaster applies the graded per-cell `shift`.

---
MEASUREMENT GATE — nothing above this line is edited once numbers exist.
