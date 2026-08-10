# Order-N over FREQUENCY — formants as a soft-admissibility frame

One operator, two axes. The agent's OWN order-N operator
(`domains/order_n_concepts.nth_order_terms` — recursive `Minus`, evaluated
NATIVELY by the substrate) aimed down the FREQUENCY axis of the cochleagram:
order-2 over frequency = spectral curvature, whose negative extrema are the
formant peaks (the vowel/place structure). This complements the syllable build
(order-N over TIME-energy) — "every frame is order-N over a dimension"
(`ozma_every_frame_is_order_n_over_a_dimension`).

## (1) The frame is the agent's own operator (donkey audit)

- Operator: `domains.order_n_concepts.nth_order_terms` (recursive `Minus`), the
  SAME operator the time-axis frames use.
- Differencing evaluated by `substrate.evaluate` (native Rust Term-tree), NOT
  numpy. The numpy recurrence is used ONLY as the audit reference.
- Audit: native order-2-freq curvature == `np.diff(.,2)` exactly; the
  negative-curvature extreme locates the peak band (true peak band 2 -> recovered
  band 2). Confirmed it is the agent's operator pointed at frequency, not a
  reinvented extractor.
- Files: `domains/order_n_frequency_frame.py` (the frame), wired into the v2
  `weighted_admissibility` collapse by `scripts/order_n_frequency_frame.py`. The
  cochleagram is the agent's gammatone front-end (`domains/filter_settings`); the
  acoustic frame is v1; the LM is real LibriSpeech n-gram counts; collapse ops are
  v2 owned. Held-out speakers never banked.

## (2) Cross-speaker numbers

Real cross-speaker word recognition, 35-word SC vocab, REAL LibriSpeech n-gram LM,
held-out speakers never banked. n = 2000 cross-speaker test items, 29 held / 78
train speakers, chance 0.029. Run: `/tmp/order_n_freq_frame.log`.

| condition | acc |
|---|---|
| (a) acoustic-only single frame | 0.096 |
| (b) multi-frame WITHOUT order-N-freq (acoustic + real n-gram) | 0.758 |
| (c) multi-frame WITH order-N-freq (onf_weight=1.0) | 0.743 |
| order-N-freq frame ALONE single-frame | 0.097 |

order-N-freq weight sweep (lift c-b over the n-gram multi-frame, REPORTED not kept):

| onf_weight | (c) with-onf | c - b |
|---|---|---|
| 0.5 | 0.762 | +0.004 |
| 1.0 (principled) | 0.743 | -0.015 |
| 2.0 | 0.642 | -0.116 |

Independence probe (acoustic frame vs order-N-freq frame, both spectral):

- single-frame argmax agreement: **0.040** (1.0 = fully redundant) -> NOT redundant
- mean soft-excluder correlation: **0.085** -> nearly orthogonal vectors
- order-N-freq right where acoustic wrong: **0.075** -> it catches independent cases
- acoustic right where order-N-freq wrong: 0.075 (symmetric)

## (3) Verdict — KILL (independent but too noisy → adds no net constraint)

The order-N-freq formant frame is the agent's OWN order-N operator pointed down the
frequency axis (donkey-clean, native eval, audited). It is **NOT redundant** with
the acoustic frame: the two barely agree (0.040), their excluder vectors are nearly
uncorrelated (0.085), and order-N-freq is correct on 7.5% of cases the acoustic
misses. But adding it to the weighted-admissibility collapse does **not** lift
recognition. At the principled cell (onf_weight=1.0) it is **-0.015** (within noise,
a slight hurt); only the down-weighted variant (0.5) is barely positive (+0.004,
within noise); above 1.0 it actively harms (-0.116 at 2.0).

Why: as a standalone recogniser the order-N-freq frame sits at the acoustic frame's
own weak cross-speaker level (0.097 vs 0.096, both ~3x chance, far from resolved).
Independent **but equally noisy** — so as a soft excluder it carves correct
candidates about as often as wrong ones; its independent correct cases (0.075) are
cancelled by independent wrong cases (0.075). The real n-gram LM already does the
heavy lifting (b=0.758 from a=0.096); a second weak, noisy spectral excluder cannot
improve on that.

Root cause is the gammatone-wall caveat, confirmed: the order-2-freq curvature peak
is a QUANTISED formant estimate (one of ~32 log-bands), too coarse to be a reliable
cross-speaker invariant. It carries genuinely different information from the
LPC-formant acoustic frame (hence the low agreement) — but that information is no
more reliable, so intersecting it in does not over-determine the word.

Honest bottom line: "every frame is order-N over a dimension" holds
ARCHITECTURALLY — the same owned operator wired down the frequency axis drops into
the same collapse with zero new mechanism. But on THIS axis, at the cochleagram's
frequency resolution, the resulting frame is too noisy cross-speaker to add
admissibility. A clean negative: the operator generalises across axes; this
particular axis does not yet pay. The complementary time-energy (syllable) axis is
the one still expected to carve.
