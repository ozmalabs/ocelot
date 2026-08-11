# Literature Positioning — Cross-Effector Drawing Kinematics & Omniglot Provenance

Where the gamma-substrate arc's measured effector findings sit against published
work. Compiled 2026-07-06 from a bounded web literature review (~10–30 queries per
question, several publishers 403-blocked and worked around via PMC/arXiv/preprints).
Novelty claims are search-bounded: absence of evidence here is *moderate*, not
strong, evidence of absence. Snippet-sourced quotes are flagged for human
verification before any external citation.

## Our measurements (sources = committed runs 33–46)

- **Mouse-drawn (Omniglot, MTurk browser):** 59–65% exact-integer sample deltas
  (pixel lattice); 56–60% exactly-0° turns with mass atoms at arctan(1/n)
  (45°/26.6°/18.4° — Bresenham staircase); median dt 15ms (~65Hz event loop);
  two-thirds power law absent (median per-writer r²=0.084, slope −0.081 vs −1/3).
- **Real tablet pen (UCI Character Trajectories, 200Hz Wacom, careful letters):**
  two-thirds law still nearly absent (r²=0.092, slope −0.056).
- **Touch subset (QuickDraw raw, device-split):** two-thirds law moderate
  (r²=0.310, slope −0.198), task-confounded (fast doodle vs careful trace).
- **Information content:** stroke-interior class information ~zero on mouse
  (1–2 identities across 10k+ strokes, all quantizations, ± denoising) but rich
  on pen (1,826 identities at 17.1× shuffled null) and touch (3.76× cross-writer).
- **Device classifier:** integer-delta-fraction cleanly splits mouse vs touch
  (bimodal, valley 0.625; QuickDraw raw = 17.1% touch / 82.9% mouse).
- **Segmentation:** velocity minima do NOT beat geometric corners as
  cross-instance-stable boundaries in deliberate drawing, any effector
  (count-matched; naive density-unmatched comparison says the opposite).

## Findings vs literature

**A. Two-thirds power law weakens in slow/deliberate movement — CONFIRMED (direction).**
Fraser, Di Luca & Cook (2025, Exp Brain Res 243:107): r²≥0.75 only above ~1 Hz.
Lacquaniti, Terzuolo & Viviani (1983, Acta Psych 54:115): exponent drifts furthest
from 2/3 at slowest speeds. Thomassen & Teulings (1985): law "not robust for normal
handwriting." Huh & Sejnowski (2015, PNAS 112:E3950): clean exponent predicted only
for single-frequency (elliptic) movement; letters smear it. Our r²≈0.08–0.09 is
lower than any published figure, but classical high-r² evidence is for continuous
rhythmic curve-tracing, not discrete letters — a methodological gap our finding sits
in. **Amends our own arc:** the kinematic-prediction failures (runs 33/46) are
*expected* under this literature — deliberate drawing is non-ballistic on any
effector; momentum was never the lever.

**B. Device precision differences known; information-content comparison — EXTENDS.**
MacKenzie/Sellen/Buxton (1991, CHI): stylus 4.9 bps > mouse 4.5 > trackball 3.3.
Zabramski (2011, OzCHI): tracing error pen 4.98px < mouse 5.84px < touch 7.95px.
Signature verification: Tolosana et al. (2017, PLoS ONE) stylus EER 10.1% vs finger
24.3%; Abazid et al. (2020, Sensors) 4–8× EER spread by device. But no matched-content
*information-content*/recognition comparison across devices was found — our
1–2 vs 1,826 vs 684 identity contrast appears to be the first.
**Correction to our framing:** QuickDraw is device-*mixed* by design; our integer-delta
split (17.1%/82.9%) is plausibly the first published estimate of its device
composition and should be described that way, not as "touchscreen data."

**C. Bresenham/pixel-lattice angular structure — theory OLD, forensic use NOVEL.**
Freeman (1961, chain codes) and Rosenfeld (1974, digital straight lines) formally give
the arctan(1/n) angular-quantization family. ScribeTokens (arXiv 2603.02805, 2026)
documents staircase artifacts — but as quantization *imposed* on smooth ink and then
smoothed away, not diagnosed in a released benchmark. Psychology mouse-tracking
(MouseTracker, mousetrap) handles *temporal* irregularity but is silent on *spatial*
grid artifacts. Bot-detection biometrics models continuous kinematics, never discrete
stepping. Cite the mechanism as background; the forensic *measurement of it in an
existing dataset's raw files* appears novel.

**D. Integer-delta-fraction device classifier — NOVEL (well-searched).**
~40 queries across mouse-dynamics survey (ACM Comput Surv 2024, arXiv:2208.09061 —
treats device heterogeneity only as a confound), bot-detection, anti-cheat,
fingerprinting. Nothing. Closest analogs are a different channel (touch pressure/size
degeneracy for emulator detection, Ding et al. 2025, arXiv:2510.07809) and an
unformalized front-end heuristic (scroll-wheel deltaY granularity). Cleanest novelty
claim in the set.

**E. Velocity-minima segmentation fails on deliberate drawing — CONFIRMED (adjacent lit).**
Van Galen (1991) confirms velocity-minima as the *standard* motor-control definition.
But sketch-recognition contradicts it for deliberate drawing: Wolin/Paulson/Hammond
(2009, SBIM) geometric corners 0.667 vs speed+curvature 0.298 (>2×, matching our
qualitative result); Xiong & LaViola (2009) corroborate; Zheng/Liu/Sun (2006) and
Pu & Gur (2009) state the mechanism directly ("constant speed → segmentation points
missed"). Chance-correction machinery (Cohen's κ / Scott's π; Adjusted Rand,
Hubert & Arabie 1985; Pk/WindowDiff, Pevzner & Hearst 2002) is decades old — not ours;
its specific application to the velocity-vs-corner comparison appears to be a gap.

**F. Omniglot mouse-provenance & BPL consequence — PARTIALLY NOVEL (searched hardest).**
Lake, Salakhutdinov & Tenenbaum (2015, Science 350:1332, read directly): data collected
via MTurk "holding down a mouse button and moving the mouse (or trackpad, tablet, etc.)";
SM §2.3.1 notes "non-uniform spatial and temporal sampling... synthesis of drawing data
from many different web browsers and computers." The Discussion leans on sub-stroke
trajectory shape reflecting genuine motor programs — the exact assumption our finding
undermines. **Real precedent:** Fabi, Otte & Butz (2020–2022) independently judged
Omniglot's mouse data kinematically unrealistic enough to build two pen-collected
replacement datasets (their 440-trajectory lab set; DigiLeTs, 23,870 Wacom trajectories),
one describing Omniglot chars as "traced with a computer mouse... arbitrary strokes"
(snippet-sourced, unverified verbatim). So the *qualitative* problem was known.
**What appears new:** the Bresenham mechanism, the quantified statistics (59–65%,
56–60%, 15ms), the stroke-identity collapse to 1–2 families, and the explicit tie to
BPL's motor-program assumptions. Frame as "quantifying and mechanistically explaining a
previously-suspected-but-unmeasured problem," not "discovering" it. No paper modeling
Omniglot's raw coordinates (BPL codebase, Feinman & Lake 2020, compositionality-RNN line)
was found to correct for or acknowledge pixel-grid quantization.

## Apparent novelty (ranked, search-bounded)

1. **Integer-delta-fraction device classifier** (D) — high confidence, ~40 queries.
2. **Bresenham-signature forensic diagnostic on a released benchmark** (C+F) — high.
3. **Information-content quantification of device effects on stroke shape** (B) — high.
4. **Omniglot mouse-artifact mechanism + BPL consequence** (F) — medium; qualitative
   problem previously flagged (Fabi/Otte/Butz), quantification/mechanism new.
5. **Count-matched chance-correction for velocity-vs-corner segmentation** (E) — medium;
   known statistics, new pairing.
6. **r²≈0.08–0.09 magnitude for the 2/3 law in careful writing** (A) — low; direction
   confirmed, magnitude in an undertested task regime.

## Access gaps (honesty)
Lake 2011 CogSci and 2014 thesis inaccessible (403/binary). Fabi et al. 2022 IEEE TCDS
"arbitrary strokes" quote is snippet-synthesized, not verified verbatim. Several
ScienceDirect/IEEE/ACM pages 403-blocked, worked around via PMC/arXiv/preprints or not
at all. Snippet-sourced claims need a human primary-source pull before external citation.
