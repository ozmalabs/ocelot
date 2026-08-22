# Class C selection — chapters 5–13

Existing figures under `results/`, selected and captioned rather than redrawn.
Same rules as `CLASS_C_CH1.md`: **every selection must have a committed
generator** (none of the ~110 PNGs under `results/` is tracked in git), and
**nothing is selected without being opened first.**

Six selected across four chapters, two rejected, and **three chapters get
nothing** — which is recorded rather than papered over.

---

## Selected

### C6 — depth recovers a weak block's underfit (chapter 5)
**File** `results/cascade_ink/reconstruction.png` ·
**Generator** `scripts/cascade_ink_demo.py`

Real Omniglot ink beside four reconstructions at increasing depth: 1 block
(RMSE 0.214), 2 blocks (0.231), 4 blocks (0.086), 8 blocks (0.087).

**Caption to use.** *The leftmost panel is a real character. The rest are the
system's own reconstruction of it at increasing depth, drawn over the original
in grey. Two things are visible that a table of error figures is not: the
two-block reconstruction is slightly WORSE than the one-block (0.231 against
0.214), and the gain from four to eight blocks is nothing (0.086 to 0.087).
Depth buys a step change and then stops.*

**Why it earns space in chapter 5:** the chapter is about deltas that were noise
and one that was not. This is the same shape at a different grain — a real jump
between two configurations, and two non-differences either side of it, in a
single glance.

### C7 — mood momentum, and the shuffle that kills it (chapter 10)
**File** `results/mood_r1c/mood_r1c.png` ·
**Generator** `scripts/mood_r1c_measure.py`

Two panels with bootstrap intervals. Left: cumulative reward with the mood
layer minus without, under a persistent regime versus an i.i.d. control matched
on its marginal. Right: momentum on a trended run (good then bad) against the
*same values shuffled*.

**Caption to use.** *Left: the mood layer helps when the world has persistent
regimes and hurts when it does not — the i.i.d. arm is matched on its marginal
distribution, so the difference is the persistence and nothing else. Right: the
control that makes the first panel mean something. Feed the same values in a
shuffled order and the momentum signal goes to zero. Mood is tracking the
trend, not the values.*

**Status: taken up.** Chapter 10 now reports both arms with their intervals and
says why the second is what makes the first a result — identical marginals,
differing only in persistence, and a failable control that failed in the honest
direction.

### C8 — psychosis as a grounding failure mode (chapter 11)
**File** `results/psychosis_demo/psychosis_demo.png` ·
**Generator** `scripts/psychosis_grounding_demo.py`,
`scripts/psychosis_grounding_figure.py`

Six panels, and **the chapter currently describes three of them.**

Panels 1–3 are what chapter 11 covers: self-grounding against a matched
reality-friction control; the confirmer flipping an outcome that friction alone
corrects; and the confirmer amplifying confidence.

**Panels 4–6 are not in the chapter and should be.**

- **4 — a fold, not a slope.** Vary confirmer strength with reality friction
  held fixed and the outcome does not degrade smoothly: it sits at *corrects*
  until a threshold and then jumps to *delusion*. A sharp transition in a
  parameter nobody tuned for one.
- **5 — recovery.** Escape time falls as the grounding source strengthens. The
  chapter reports the failure regimes and never says the model recovers.
- **6 — two agents, no external anchor.** A closed loop of mutual confirmation
  holds both in the wrong basin; ground *one* of them at t=30 and **both**
  collapse to truth. The confirmer mechanism is scale-agnostic, and one
  grounded participant is enough.

**Caption to use, for panel 6 specifically:** *Two agents confirming each other,
with nothing outside the pair. Grounding one of them at tick 30 recovers both.
The mechanism does not care whether the confirmer is a person or a system, and a
single external anchor is sufficient — which is the same shape chapter 12 finds
at network scale, where one believing agent changes what unconnected nodes
believe.*

**That cross-reference is the reason to select this figure**, and chapter 11
now carries it: N4's unscripted finding and this panel are the same result in
two different threads, reached by lines that share no code.

**Status: taken up.** Chapter 11 has a new section on all three — the fold with
its single monotone boundary, recovery with its escape-time series, and the
two-agent closed loop — plus two new falsifiers covering the fold's boundary and
the closure claim.

### C9, C10 — the seizure bifurcation (chapter 11)
**Files** `results/seizure_engine_figure.png`,
`results/seizure_v2_figure.png` ·
**Generators** `scripts/seizure_science_probes.py`,
`scripts/seizure_v2_experiments.py`, `scripts/seizure_v2_figure.py`

The second failure regime, and its follow-up re-testing two limits the first
version's own science review had named. Select one for the chapter and cite the
other; V2 is the better single choice because it carries the self-correction.

---

## Rejected

### `results/per_area_settlement/per_area_settlement.png` — wrong chapter entirely
The filename reads as though it belongs to chapter 13's town. It does not:
"settlement" here means **settling**, as in convergence, and the figure is about
per-area compute budgets, rounds to a fixed point, and microseconds per settle
against dirty areas.

**This is the second filename trap in this project's figure work** — the first
being chapter 1's `eye_timing/scaling.png`, filed as an FFI-wall plot on the
strength of its name. The rule holds: *a figure identified from its filename is
an unread figure.* It may be usable in chapter 14 or 15 as an engine-cost
figure; it is not a town figure.

### `results/doom_ingraph_map/map_frame_*.png` — illegible at figure size
A map being built in-graph as the agent explores, which is exactly chapter 7's
subject. But the frames are small, low-contrast, unlabelled tile images that
carry no scale, no legend and no indication of what the agent had not yet seen —
the one thing chapter 7 is about. **Rejected on legibility, not on relevance:**
a belief-map figure for chapter 7 should be *generated* with the unknown region
marked as unknown, which is Class B work rather than a selection.

---

## Chapters that get nothing, and why

- **Chapter 6 (speech).** There are no audio or speech figures under `results/`
  at all — the thread's evidence is logs, LOSO tables and iteration documents.
  A figure for chapter 6 would have to be drawn from scratch.
- **Chapter 8 (programs).** Same: no figures exist for the synthesis thread.
- **Chapter 9 (bodies).** No humanoid or flight PNGs exist either; BODY-1 was
  drawn from JSON for exactly that reason.
- **Chapter 12 (coercive control).** Its runs live in a separate repository and
  produced tables rather than plots. CC-1 was drawn from the line summary.

Four of the nine chapters in this range have **no existing figures at all**,
which is worth knowing before anyone assumes the archive is uniformly rich. It
is deep in vision and psychology and empty everywhere else.
