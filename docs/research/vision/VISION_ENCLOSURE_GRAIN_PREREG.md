# ENCLOSURE × GRAIN — PRE-REGISTRATION

*Written and committed BEFORE any number (§3). Seeds **108000–108999**.*

**THIS RUNG'S DEFAULT IS TO BUILD NOTHING.** It is a diagnostic. A mechanism is
written only if §5's discriminator selects OUTCOME G *and* a rival definition can be
DERIVED (not parameterised) and shown to compose with the well-posedness conjunct
(v1.2.0) and `bown_nest` (v1.3.0). Three predecessor rungs were instructed to run the
cheap diagnostic first; in all three it killed the mechanism before it was written.

---

## 0. PROVENANCE AND SEEDS

### 0.1 THE VERBATIM `check_claim` OUTPUT (§3 clause 8)

```
$ python3 -c "import sys;sys.path.insert(0,'scripts');from seed_claim import check_claim;print(check_claim(108000,108999)[1])"
SEED CLAIM 108000-108999: CLEAN -- no collision DETECTED.
  Scope: 811 files with seed sinks; 506 UNRESOLVED sink sites tree-wide (counted, not discarded).
  CAVEAT 1 -- THE UNIT IS THE SEED INTEGER, not consecutive draws from
    one generator. default_rng(S) burns an unbounded stream downstream of
    S; a rung seeding ONCE at its block base measures as ONE seed here.
  CAVEAT 2 -- THIS TOOL UNDER-REPORTS BY DESIGN (7 declared blind spots;
    unresolvable sinks are COUNTED, not discarded). A CLEAN RESULT MEANS
    'NO COLLISION DETECTED', NEVER 'NO COLLISION EXISTS'.
```

**506 unresolved sinks tree-wide.** The result is *no collision detected*, never *no
collision exists*.

### 0.2 Engine

Built in-tree by `scripts/engine_build.sh` before any measurement; the provenance gate
run as its own step, first. **No Rust change is planned in this rung.** The engine
fingerprint is re-verified AFTER the long measurement (source identity at t=0 expires
silently).

### 0.3 CPU

At most **2** concurrent workers. `os.getloadavg()` is recorded alongside every
measurement written to an artifact. **No wall-clock cutoff is used as a verdict.**

---

## 1. WHAT IS BEING ASKED

The grouping-ceiling rung measured, post-hoc, that the value flood produces
**86 / 94 / 111 / 83** components of ≥60 cells (C1 tile / C1 whole / C2 tile / C2
whole) and that the share surviving `bo_bgflood`'s enclosure test is
**1.2% / 44.7% / 0.0% / 41.0%**. It named `bo_bgflood`'s predicate — *"does not touch
the WINDOW" read as "is a FIGURE"* — and declined to start from it.

`bo_bgflood` (seed `vision_border_ownership` v1.3.0) sets `bg=1` on any cell that is a
`frame` cell or has a same-`val` 4-neighbour with `bg=1`, iterated to the `run_rules`
fixpoint. **A component is ENCLOSED iff it contains no cell of the field border.** That
is the entire predicate. The aperture `REGION=18` was adopted by the resolution rung on
**statistical** grounds (n_eff, cost) and is now load-bearing in three rungs' published
results.

**The question this rung answers, and only this one:** *what is the enclosure predicate
actually computing, at each grain, and does it carry any figure/ground information
beyond the geometry of the window?*

---

## 2. THE MEASUREMENTS

All at the incumbent quantizer `k=16`, **quantized PER FRAME over the whole 72×72 and
only then cut into tiles** — the predecessor's §6.1 defect, reproduced correctly here
and asserted against its published floor in-run.

### 2.1 THE GRAIN LADDER IS AN ENUMERATION, NOT A CHOICE (§13)

`GRAINS = [L for L in 1..GRID if GRID % L == 0]` — **every** divisor of the standing
`GRID = 72`: `1, 2, 3, 4, 6, 8, 9, 12, 18, 24, 36, 72`. It is the complete set of
window sizes that exactly tile the standing frame. **No grain is selected**; all twelve
are reported, including the degenerate small ones whose behaviour falls out of the
predicate rather than being chosen.

### 2.2 M1 — WHAT ENCLOSURE IS DOING AT EACH GRAIN (the characterisation, FIRST)

Per (corpus, grain), over the wide frame sample (§2.6):

| quantity | why |
|---|---|
| components; enclosed components | exposure |
| **fraction of ALL CELLS that are enclosed** | the VACUITY axis — at what grain does the predicate stop discriminating |
| size distribution of ALL components: median / mean / p90 / max / **size-biased median** | the flood's output |
| size distribution of ENCLOSED components: same five | the figure side |
| **number of GROUND components and the share of cells they hold; largest ground component** | *what enclosure calls background* |
| **survival share at every T in the curve** `T ∈ {5,10,20,40,60,100,150,300}` | the size dependence, as a CURVE — no single T is load-bearing |

### 2.3 M2 — THE GEOMETRIC NULL, COMPUTED NOT FITTED

For a component with bounding box `h × w` inside an `L × L` window, a translation is
*inside* iff its bbox origin lies in `[0, L−h] × [0, L−w]`, and *clear of the border*
iff it lies in `[1, L−1−h] × [1, L−1−w]`. So

```
null_survival(component) = max(0, L−1−h) · max(0, L−1−w)
                           ───────────────────────────────
                              (L−h+1) · (L−w+1)
```

**This is EXACT, not an approximation** — "clear of the border" is a statement about
the bbox alone. It has no fitted parameter and no chosen constant; it is the share of
positions at which a shape of that extent *could* avoid the window edge.

The statistic is the **observed/null ratio** per size band, bootstrapped over fields.

**This is what makes "the predicate is inert" measurable rather than rhetorical.** If a
component's enclosure is predicted by its bounding box and the window size alone, then
`bo_bgflood` is computing window-fit and nothing else.

### 2.4 M3 — THE SPECKLE ARM (the floor, RE-EARNED ACROSS THE GRAIN CHANGE)

The identical grain sweep on **100 iid uniform speckle fields at 72×72**, seeds
**108000–108099**. Two roles:

1. the random-input floor for every distribution above, **re-earned at every grain**,
   not inherited from the tile grain;
2. **the information control** — is the observed/null ratio on natural frames
   distinguishable from the ratio on noise at matched size band? If not, enclosure
   carries no more figure/ground information on structured input than on noise.

**`0/100` IS NOT COPIED FORWARD.** The peer rung restated it as **≈0.6% [0.17, 2.25]**;
a zero observation bounds a rate, it does not establish one. No gate in this rung
asserts `== 0` on a fresh draw.

### 2.5 M0 — RECONCILIATION AGAINST THE GRAPH, AT MORE THAN ONE GRAIN

The claim of this rung spans grains, so the instrument must be reconciled across
grains. Live fields are put through the **substrate** (`boot_core` +
`vision_border_ownership`, `bown=1`) at **each** grain that is computationally
reachable, and the numpy enclosure mask is checked cell-by-cell against the graph's own
`bg` flag, and the numpy partition against `glabel`.

**ANY disagreement VOIDS the run.** The predecessor's §6.1 — *"I verified the PRODUCER
and reported it as verifying the PRODUCT"* — is why the published enclosed-component
totals (**C1 5047 / C2 3978**, at G72 / `REGION=18` / `k=16` / the published 7 frames)
are **asserted in-run**: the run raises rather than reports if they do not reproduce.

### 2.6 EXPOSURE

- **Floor re-earn:** the published `SAMPLED_FRAMES = (0,25,50,75,100,125,149)`, 7
  frames, `REGION=18` — the exact published configuration.
- **Grain sweep:** a wider sample, `range(0, 150, 5)` = **30 frames** per corpus, so
  the whole-frame grain has n=30 fields rather than n=7. **n per arm is reported on
  every row**; no statistic is computed over an empty population, and thin populations
  are labelled.
- Unit of analysis is the **FIELD** (§4), never the cell or the component. CIs are
  bootstrapped over fields, 10 000 resamples.

---

## 3. PREDICTIONS, STATED IN ADVANCE (§3 clause 7)

**P1.** Observed survival will track the geometric null closely across grains, because
the predicate *is* a reachability test to the window edge and, for a component whose
bbox is small relative to `L`, touching that edge is a positional accident.
**Proviso that would break it:** components are not randomly placed — the background is
*systematically* the border-touching region. If observed survival falls **below** null
for large components at large `L`, that is real content and P1 is wrong in the
informative direction.

**P2.** The enclosed-cell fraction rises monotonically with `L` and exceeds one half at
`L=72`. **This is WEAK EVIDENCE and I declare it so in advance** — the predecessor
already measured 0.637 / 0.609 at that grain, so I am re-earning a number I have read,
not predicting one I have not.

**P3.** There is **no** grain at which enclosure is both size-permissive and selective,
because they are the same axis: both are monotone in `L`. If P3 holds, the grain is not
the free parameter it appears to be.

**P4.** The observed/null ratio on speckle will be indistinguishable from the ratio on
natural frames at matched size band.

**P5.** At `L=72` the ground will be dominated by ONE giant component holding a large
share of the field, so "enclosed" at whole-frame grain means *"not part of the single
largest connected equal-value region"* — a percolation statement, not an objecthood
one.

**P1, P3 and P4 are ONE BET** — three readings of *"the predicate computes window-fit"*
— and cannot independently confirm each other. Declared in advance so it limits them
rather than being offered later as a rescue. **P2 and P5 are separate and are about
what the predicate calls GROUND.**

---

## 4. CONTROLS THE RUN VOIDS WITHOUT

| control | requirement |
|---|---|
| **Provenance** | its own step, FIRST; re-verified AFTER the long measurement |
| **Oracle** | `bash scripts/rung7_vision_bench.sh` before and after |
| **M0 partition ≡ `glabel`** | every reconciled field, at every reconciled grain |
| **M0 enclosed ≡ `bg`** | every reconciled field, at every reconciled grain |
| **Published floor 5047 / 3978** | asserted IN-RUN on the sweep's own code path |
| **Corpus pins** | C1 `08630d4b`, C2 `119eca43`, asserted at run time |
| **Ideal exemplar** | a genuine isolated disc, clear of the border, must read ENCLOSED at every grain that can contain it — and must read GROUND when translated to touch the edge. *The instrument must see the structure it exists to see, and must also see it disappear for the stated reason.* |
| **Null positive-control** | the null must return 1.0 for a 1-cell component in a large window and 0.0 for a component whose bbox spans the window |

---

## 5. THE DISCRIMINATOR — REGISTERED IN ADVANCE

The brief names three legitimate verdicts. Each is selected by a stated pattern in the
numbers, **fixed before the numbers exist**:

- **OUTCOME P — THE GRAIN IS CORRECT AND THE PREDICATE IS WRONG.** Observed survival is
  statistically indistinguishable from the geometric null across grains **and** the
  natural-frame ratio is indistinguishable from speckle's. Then `bo_bgflood` computes
  the aperture's geometry, carries no figure/ground information, and no choice of
  window repairs it.
- **OUTCOME G — THE PREDICATE IS CORRECT AND THE GRAIN IS WRONG.** Observed survival
  departs from the null in a **size-independent** way at some grain, while the
  enclosed-cell fraction remains selective there. Then the predicate has content and
  the aperture is chopping it.
- **OUTCOME N — NEITHER.** Any other pattern. Then the deliverable is **naming what
  actually gates it**, with the measurement that shows it, and no mechanism.

**A mechanism is written ONLY under OUTCOME G**, and only if a rival enclosure
definition can be derived from the border-ownership literature (Zhou / von der Heydt)
rather than parameterised, and shown to compose with **one** rival definition — not
three — against v1.2.0 and v1.3.0. Under **P** or **N** this rung builds nothing and
says so.

---

## 6. WHAT THIS RUNG WILL NOT CLAIM (§8)

- **It will not claim the discarded components are OBJECTS.** Nothing here inspects
  what they are; many will be wall, sky, floor. This was the grouping-ceiling rung's
  own first scope note and it binds here unchanged.
- **It will not claim removing the aperture is a fix.** At whole-frame grain the
  enclosure test stops being selective, which is its own failure mode, and no
  downstream gate has been priced on that population.
- **One quantizer, one relation.** `k=16` exact-value. The value family is closed by
  the grouping-ceiling rung and is not reopened.
- **Components are computed OUTSIDE the graph** and reconciled against it; the sweep is
  a characterisation of the relation, not a measurement of a mechanism.
- **Two corpora, one video source.** C1 cartoon, C2 live-action.

---

## 7. §13 AND §9

- **§13:** no literal, no size test, no count threshold decides anything. The grain
  ladder is the divisor enumeration of the standing GRID; the T ladder is a curve
  reported in full; the null is computed from the window and the bbox. Every sink
  `scripts/gate_audit.py` reports is enumerated ONE AT A TIME in the results, by class,
  with the defence being **what the number IS**, not what it is called. The audit is
  positive-controlled **by injection, and the injection is verified to LAND IN THE
  REGION** — a predecessor's `verify_lands` checked the FILE and produced seven false
  verdicts.
- **§9:** if nothing is built, `git diff -- seeds/ runners/` is EMPTY and byte-identity
  is by construction. If anything is built it ships OFF by default and byte-identity is
  proven with the flag off.
