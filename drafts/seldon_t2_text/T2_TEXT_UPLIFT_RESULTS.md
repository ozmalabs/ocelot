# RESULTS — real-text uplift for the Seldon-confidence T2 forecaster

Reports `drafts/seldon_t2_text/run_gate.py` against
`T2_TEXT_UPLIFT_PREREG.md`. Numbers are from a single deterministic run
(seed 0 for the main table; seeds 0–9 for the multi-seed spread). Reproduce:

    python3 drafts/seldon_t2_text/run_gate.py

The CRPS correctness gate (`test_crps.py`) passed first; no number below was
trusted from an unverified scorer.

## Setup (as measured)

- Panel: 30 entities, T=300, regime-switching AR(1), integer cells (PoC DGP
  verbatim). Rolling-origin: 6 cutoffs in [140, 293], horizons h=1..5, 900
  scored (cutoff, entity, horizon) forecasts per arm.
- Corpus (seed 0): 190 rendered news items (154 real-switch, 36 spurious). The
  forecaster reads only rendered prose + tick; the struct is hidden from all
  real/tinfer arms.
- 30 entities > 26 name-stems, so ~4 entities share a surface stem — a
  deliberate, realistic alias-COLLISION minority (a precision failure mode, not
  a bug). See H2.

## Pipeline recall (prereg §6 — the proximate cause behind the uplift gap)

| quantity | measured (seed 0) |
|---|---|
| link recall, canonical name only | 34/154 = **22.1%** |
| link recall, with alias seed | 139/154 = **90.3%** |
| claim-type recall | 154/154 = **100.0%** |

Leg (ii) exact-lexical linking on the canonical name alone recovers barely a
fifth of mentions; the alias seed (tickers/short-names, still exact-lexical)
quadruples it to 90.3%. Leg (iii) typing is ~100% **by construction** — the
templates are fixed and the cue lexicon matches them. This is the honest
caveat the prereg pre-committed: **this harness isolates leg (ii) linking as the
ceiling**; it does not stress leg (iii). A real corpus would degrade typing too.

## Main CRPS table (seed 0, lower better)

| arm | mean CRPS | vs climatology |
|---|---|---|
| climatology | 2.4492 | 0.0% |
| gauss_ar1 (the baseline T2 demands uplift over) | 1.1403 | −53.4% |
| seldon_notext | 1.1164 | −54.4% |
| **seldon_text_real** | **1.0509** | **−57.1%** |
| seldon_text_oracle | 1.0211 | −58.3% |
| seldon_text_real_tinfer | 1.0509 | −57.1% |

## Hypotheses (pre-registered, resolved)

### H1 (headline) — real-text uplift is positive: **CONFIRMED**
- notext 1.1164 → real 1.0509; reduction 0.0655 = **5.86%**.
- 95% paired bootstrap CI (10k): **[2.04%, 9.94%]** — lower bound > 0.
- Multi-seed (0–9): mean **7.64%**, sd 2.51, range [3.69%, 10.76%], **10/10
  positive**. The headline is not one lucky seed.

The pre-registered plausible range was 1–8%; the measured mean (7.64% across
seeds, 5.86% on seed 0) lands inside it, near the top. **A real ingest → link →
type → as-of → confidence-shift pipeline, with graph-native entity linking,
produces a CI-separated CRPS uplift over a text-blind Seldon forecaster and over
the Gaussian-AR(1) baseline.**

### H2 (attribution) — the loss is in linking, not the mechanism: **CONFIRMED**
- oracle uplift **8.54%** (CI [4.42%, 12.90%]) vs real **5.86%**.
- linking/typing tax = oracle − real = **2.67 pp**.
- Proximate cause: link recall 90.3% (aliases) — and, importantly, the residual
  gap is driven as much by alias-COLLISION mislinks (precision) as by missed
  links (recall). The oracle recovers ≈ the PoC's ~6–8.5% clean-signal uplift;
  real gives most of it back, and what it loses is exactly the leg-(ii)
  exact-lexical tax pre-judged as the binding constraint. The mechanism (v) is
  fine; entity linking caps the number.

### H3 (graph-native projection) — TimeInfer centering does not hurt: **NEUTRAL**
- tinfer 1.0509 vs real 1.0509; (real − tinfer) mean 0.0000, CI [0.0000,
  0.0000], ε = 0.0056. CI upper ≤ ε ⇒ neutral-or-better.
- **Honest reading:** the exact-zero delta is not "TimeInfer helped." It is
  TimeInfer FLOORING on every series: a mean-reverting integer walk is not an
  orbit under a single rigid generator, so `TimeInfer.explained` is false and
  the arm falls back to the last-value center — identical to real, by
  construction (prereg §1.1). This is a clean, localising null about the OP's
  shape-fit: `TimeInfer`'s exact-orbit rigidity is the wrong shape for a noisy
  mean-reverting series. It confirms the substrate op is *usable* here (no
  regression, drop-in) but supplies no signal a mean-reverting DGP can exploit.
  The op earns its keep on trending/accelerating series (its F-16 / sensor-
  channel home ground), not on this one.

### H4 (as-of validity) — the bound is load-bearing: **VALID (direction mispredicted)**
- real CRPS as-of ON 1.0509, as-of OFF 1.1095; |Δ| = 0.0586 (5.25% of notext).
- The bound materially changes the score ⇒ the pipeline is genuinely using the
  text (a forecast that ignored text would be invariant to the bound).
- **Honest surprise:** the prereg predicted the no-bound arm would score BETTER
  (cheat). It scored WORSE. On this lead-token DGP a switch announced for
  `t_switch` emits its informative token at `t_switch − lead`, so the useful
  item is ALREADY ≤ cutoff; peeking forward grabs later, often past-horizon or
  contradictory items that are net noise. Removing the as-of bound therefore
  degrades rather than cheats. The validity conclusion (text is load-bearing)
  holds; the directional prediction was wrong, and is reported as wrong.

## Calibration (prereg §6 — an uplift on a miscalibrated forecast is not a win)

Randomised-PIT histogram for the real arm is close to flat with mild
center-heaviness; KS calibration error **0.0926**. Not perfectly calibrated
(some over-dispersion), but no gross miscalibration that would void the CRPS
comparison. T2's calibration gate would want this tightened; it is not
disqualifying here.

## Reconciliation with the prior assessment

The two reframes that drove this build both survive measurement:

1. **The arxiv-importer + referent-linking combination is the right foundation.**
   Legs (i) ingestion and (iii) typed-record are adapted templates that work;
   leg (ii) linking is real and graph-native (drives the actual
   `rule_mention_resolves_to_concept` rule). The end-to-end pipeline produces a
   CI-separated uplift.

2. **Time is a coordinate to mint, not special infrastructure.** As-of masking
   is a bound on `coord:t` (H4 shows it is load-bearing); the forward-projection
   op `TimeInfer` is a drop-in that composes without regression (H3). No bespoke
   `valid_time` subsystem was built or needed.

The one place the substrate did NOT lift the number: `TimeInfer`'s exact-orbit
projection is the wrong shape for a mean-reverting panel (H3 null). That is a
finding about the op's applicability, not about time-as-dimension.

**Revised expected real-T2 CRPS uplift over text-blind baselines: ~4–10%
(mean ~7.6% across seeds, all positive), CAPPED by leg-(ii) exact-lexical
entity linking** (recall + alias-collision precision), with the mechanism itself
(v) proven and the oracle ceiling ~8.5%. This is a modest but CI-separated,
multi-seed-robust positive — an upward revision of the earlier "0–5%, possible
null" discount for the FLOOR (the pipeline is real, not from-scratch), holding
the earlier ceiling caveat (linking is the binding constraint).

## Honest residuals (what this does NOT establish)

- **Typing is not stressed.** Leg (iii) at 100% is a fixed-template artifact.
  Real prose would inject typing precision/recall loss this harness does not
  measure; the real-world number is ≤ what is reported here.
- **Corpus is semi-synthetic.** Panel + event schedule are a known DGP (needed so
  a null means "mechanism failed," not "text uninformative"); only the surface
  prose is natural-language. A fully real corpus (real filings/news + a real
  panel) is the next instrument and would move both linking and typing off their
  controlled values.
- **`TimeInfer` null is DGP-specific.** On a trending/accelerating series the op
  would contribute a nonzero center; this panel cannot exercise that.
- **Calibration is imperfect** (KS 0.0926); a T2 submission would tighten it
  before claiming the gate.
