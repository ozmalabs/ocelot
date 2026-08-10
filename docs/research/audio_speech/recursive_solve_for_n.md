# Recursive / hierarchical solve-for-N — the fix for the compositional break

**Script:** `scripts/solve_for_n_recursive.py`
**Run:** `python -m scripts.solve_for_n_recursive` (full) / `--quick` (smoke)
**Status:** built, run to completion, real numbers below. `SOLVE_FOR_N_RECURSIVE_COMPLETED`,
exit 0, pgrep-verified (no lingering process).

## The break this fixes

The diagnostic ladder (commit `a2c87ae0`, memory `ozma_diagnostic_ladder_method`) found the
**compositional break** at rung 3: the FLAT solve-for-N (`scripts/solve_for_n.py`) peels
low-level components by energy (matching pursuit) and has **no operator to GROUP** them.
On a melody it shatters each note into several partials — a flat over-complete bag
(8 components for ~3 notes, RMSE stuck ~0.22). The partials of one note are scattered
across the bag instead of being recognised as one thing.

## (1) What was built — recursive/hierarchical solve, flat engine reused per level

**Hierarchical forward models** (owned, EXACT, ground truth known):

```
MELODY  =  sum of NOTES                       synth_melody()
  NOTE  =  gated harmonic STACK of partials    synth_note()  = f0 + 2f0 + 3f0 ...
                                               under one raised-cosine envelope
                                               params = [f0, onset, dur, partial_amps, phases]
```

**Recursive solve** (`recursive_solve_melody`):

- **TOP LEVEL (melody)** — matching pursuit over NOTES. Propose a note = the strongest
  FUNDAMENTAL in the residual (`propose_fundamental`), scored by **harmonic-comb energy**
  (f0 + 2f0 + 3f0 ...), *not* a lone partial — so a real note's comb out-scores any stray
  harmonic and we propose the fundamental, never a scattered partial. **This is the new
  mechanism the flat engine lacked.** Subtract the synthesised note → recurse. Stop when a
  new note explains < 1% of the energy (the note count is *recovered*, not fixed).
- **SUB-SOLVE (note)** — `sub_solve_note` fits one note's f0 + partial amplitudes +
  envelope as a UNIT: the partials are a single closed-form least-squares onto the gated
  harmonic basis (`_fit_partials_lsq`). **The partials of one f0 are grouped by the joint
  fit — never peeled separately, so they cannot shatter.**
- **Octave/sub-multiple correction** at the leaf (the failure mode the prediction warned
  about): a proposal can land on a sub-multiple (true/m → empty in-between partials → snap
  UP) or a super-multiple (m·true → a denser real comb fits as well → snap DOWN). Snapping
  is gated on the empty-gap signature so two genuinely octave-apart notes are never merged.
- **Joint back-fitting** over the admitted notes (order-N co-refinement at the note level)
  + a **consolidation pass** that merges a same-pitch / octave-related overlapping twin
  (a note peeled in two pieces) and drops any redundant note — the top-level GROUP cleanup.

The proven flat engine is **reused unchanged**: `scripts/solve_for_n.py` is imported
byte-for-byte (no git diff), the leaf calculus (closed-form LSQ on the exact basis +
golden-section on frequency) is the same analysis-by-synthesis the flat engine runs for a
sinusoid, and the flat solve is run on the *same* melodies as the baseline below.

### Donkey audit

Recursive solve = owned numpy (matching pursuit at the note level + back-fitting +
consolidation). Leaf = closed-form least-squares on the EXACT harmonic basis +
golden-section against the exact model. Forward models = owned EXACT generative numpy.
Ground truth constructed → every error exact. **NO neural net, NO `.fit()`, NO
gradient-descent training.** CortexLoop untouched. The flat engine
(`scripts/solve_for_n.py`) is imported unchanged.

## (2) Composition result — vs the flat-solve baseline (n = 30 trials)

Gated-harmonic melodies, 2–4 notes, 3–5 partials per note with a random spectral
roll-off, fs = 4000 Hz, T = 1024. Ground truth known.

| metric | RECURSIVE | FLAT baseline (same signals) |
|---|---|---|
| mean notes/components used | **3.17** (true 3.10) | 8.00 (for 3.10 true notes) |
| exact note-count recovery | **96.7 %** | — (shatters) |
| note recovery rate (matched) | **100.0 %** | — |
| mean spurious notes | **0.07** | (flat bag, ~5 spurious) |
| octave / mis-group errors | **0.00** | — |
| median f0 rel err | **0.00 %** | — |
| median onset rel err | **0.00 %** | — |
| median dur rel err | **0.00 %** | — |
| median fit RMSE | **0.0000** | 0.3631 |

Generalisation (4 unseen seeds × 12 trials, not the acceptance seed): **46/48 = 95.8 %**
exact note-count recovery with RMSE ~0 — not overfit to the acceptance seed.

## (3) VERDICT

**The recursive solve COMPOSES — the compositional break is FIXED.**

- **Recovers NOTES as units (no shatter):** YES — 3.2 notes for 3.1 true, vs the flat
  engine's 8.0 components. The harmonic-comb proposal + the grouped partial sub-fit stop
  the shattering at the source.
- **Exact note-count + clean:** YES — 96.7 % exact note count, 100 % of true notes
  recovered, 0.07 spurious, 0.00 octave errors. Params (f0, onset, dur) recovered to
  ~0.00 % median error.
- **RMSE collapses below the flat floor:** YES — 0.0000 (recursive) vs 0.3631 (flat).
  The hierarchical model fits the harmonic melody essentially exactly.

### Honest notes / where it can still mis-group

- ~3–4 % of trials leave **one** extra note from a residual octave artifact (e.g. a strong
  harmonic of one note proposed as a phantom note that the consolidation does not fold in,
  or a snap-down that lands near a genuinely-separate nearby pitch). The signal is still
  reconstructed exactly (RMSE ~0) — the error is purely an over-count of one, located at
  the **note proposal / octave-correction** stage, not the sub-solve (the sub-solve fits a
  given note exactly even from the fully-mixed signal, verified directly).
- The octave correction is gated on an empty-gap signature; it is the hardest part and is
  where the remaining failures concentrate. It holds across unseen seeds (95.8 %) but is
  the named place to harden next if the melody domain is pushed further (denser chords,
  simultaneous octave-apart notes).

## Tests

`scripts/solve_for_n.py` and `scripts/solve_for_n_ladder.py` are unchanged (no git diff);
the flat engine still passes its own acceptance (`recovers: YES`, `super-resolves: YES`).
No existing pytest suite references solve-for-N. Not committed (coordinate).
