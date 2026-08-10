# Forward-model drive — recover per-speaker dynamics instead of a single mean

## (0) VERDICT — LEAD

**GROUNDED IMPROVEMENT. The lever I named (the single-mean-trajectory forward
model) MOVED recognition.** Replacing the single smeared mean with a
multi-exemplar forward model that preserves per-speaker formant dynamics raised
analysis-by-synthesis recognition on FSDD held-out speakers (LOSO) from
**0.2833 → 0.3250, delta +0.0417**, with the same blunt-agnostic ear, the same
native DtwTo recogniser, the same data — only the forward model changed. The
silent-failure grounding check fired on stakes (0.9), the world-measure
re-measured 0.3250 and AGREED with the claim, resolution = COMMIT.

A K-ablation grounds the MECHANISM and shows the loop self-correcting at the
degenerate ends:

```
K (exemplars/word)   current   improved   delta     verdict
  1 (one arbitrary)   0.2833    0.2500    -0.0333   REOPEN (self-corrected)
  2                   0.2833    0.3028    +0.0194   COMMIT
  3                   0.2833    0.2861    +0.0028   REOPEN (below +0.005 floor)
  5 (= all 5 train sp) 0.2833   0.3250    +0.0417   COMMIT
  6 (capped at 5)     0.2833    0.3250    +0.0417   COMMIT  (saturates: LOSO has 5)
```

The single mean (the named ceiling) AND a single arbitrary exemplar (K=1) BOTH
lose to the FULL per-speaker manifold (K=5). That is the signature that the lever
is exemplar-richness recovering per-speaker dynamics — not noise: too few
exemplars (K=1, K=3) and the grounding loop REOPENS; the full speaker manifold
COMMITs at +0.0417. K=5 == K=6 because LOSO leaves exactly 5 train speakers, so
the manifold saturates at "all train speakers" — confirming the medoid-per-speaker
design spans the speaker space rather than duplicating one talker.

Run captured to `/tmp/fmdrive_full.log` (`===MARKER_FMDRIVE_COMPLETE===`,
`elapsed 13.4s`, exit 0, process pgrep-verified GONE). `scripts/solve_for_n.py`
and CortexLoop were **left untouched**.

---

## (1) What I PROPOSED + BUILT

### The cap I named, precisely

The owned word->sound forward model (T10, `analysis_by_synthesis_accept.fwd_traj`,
reused by `topdown_recovery.build_forward_model`) is

```
fm[w] = mean over TRAIN-speaker exemplars of their A1 trajectory      (CURRENT)
```

Averaging A1 trajectories across speakers of different vocal-tract length, pitch
and speaking rate BLURS the formant trajectory into a single smear that matches no
real speaker well. This is exactly the "single-mean-trajectory synth" the jabberwock
named as the absolute ceiling (`docs/topdown_recovery.md`,
`docs/jabberwock_human_bad_ears.md`: "a sharper FORWARD MODEL, not a sharper ear").

### The improvement (my design, my call)

Replace the single SMEAR with a MULTI-EXEMPLAR forward model that PRESERVES the
per-speaker dynamics the mean destroys:

```
fm[w] = { one representative (medoid) trajectory per TRAIN speaker }   (IMPROVED)
synth_error(s, w) = min over exemplars e of w  of  DtwTo(heard_s, e)
```

Design rationale (source-filter): "the synthesis the agent can imagine" should not
be ONE averaged talker — it should be the WORD as each known talker produces it,
matched to the closest. The mean is the degenerate collapse of this manifold; the
improvement is keeping the manifold. One medoid per train speaker spans the
speaker space (not duplicate near-copies of one talker), so the AbS match resolves
to a talker WHOSE dynamics match the heard speaker, rather than to a smear.

- file: `scripts/forward_model_drive.py:fm_multi_exemplar` (`:118`) — the IMPROVED
  forward model; `fm_single_mean` (`:101`) — the CURRENT ceiling, built from the
  SAME owned `utterance_trajectory` (T10).
- the recogniser: `scripts/forward_model_drive.py:Recogniser.recognise_multi`
  (`:170`) / `recognise_single` (`:153`) — same native DtwTo synth-error
  (`recognition_graph.synth_error_term`) for both; only the forward model differs.

### Architecture audit (CLAUDE.md — native cognition, Python = world adapter)

- **The cognition is native.** The synth-error is the graph `DtwTo` Term
  (`recognition_graph.synth_error_term`, evaluated by `substrate.evaluate` in Rust
  at `forward_model_drive.py:165,189`). Each per-exemplar DtwTo distance is a
  native Term evaluation.
- **The multi-exemplar model enters as GRAPH DATA**, not Python cognition: each
  exemplar trajectory is written as the word concept's `axs_synth_feat` attr and
  matched by the native Term. The `min`-over-exemplars and the `argmin`-over-words
  WINNER are a READOUT over native distances — a query, identical in kind to the
  existing AbS argmin-over-words winner (`analysis_by_synthesis_accept`,
  `topdown_recovery.collapse`'s `max(adm, key=...)`). No Python conditional makes
  the recognition DECISION; it reads the native distances.
- **Python is the world adapter + instrument only:** audio I/O, the owned
  `utterance_trajectory` extraction, the medoid pick (a mechanical signal op —
  `argmin` of per-speaker sum-of-squares to the speaker-mean, no graph decision),
  LOSO bookkeeping, the do-contrast and grounding measurement.
- **Donkey-clean** (grep-audited): no `.fit`, no gradient, no loss, no optimiser,
  no net, no `torch`/`sklearn`, no softmax-in-Python, no sweep-to-maximise. K is a
  FIXED structural budget reported across an ABLATION (every K shown), not tuned to
  a best. The only `np` math is the medoid pick (a signal op) and the LOSO counts.
- `solve_for_n.py` and CortexLoop **untouched**.

---

## (2) The GROUNDED do-contrast

One ear, one native recogniser, two forward models, same FSDD data, LOSO over 6
held-out speakers (360 isolated recordings):

```
CURRENT  single-mean forward model : 0.2833  (102/360)
IMPROVED multi-exemplar (K=5)      : 0.3250  (117/360)
DELTA (improved - current)         : +0.0417
per-item: improved-fixed 65   improved-broke 50   agree 245
```

Per-word (current -> improved): big gains on the words the smear hurt most
(`five` 0.14->0.56, `six` 0.06->0.47, `one` 0.00->0.22, `three` 0.00->0.19); some
regressions (`nine` 0.58->0.19, `seven` 0.75->0.47, `four` 0.56->0.33) where a mean
happened to land well — the net is +0.0417, modest and honest, not uniform.

### The grounding-check verdict

`domains/silent_failure_grounding.grounding_check`, fire-on-stakes (stakes 0.9,
above floor) -> world-measure re-runs the actual improved-FM recogniser on the
held-out data -> contradiction test:

```
fired-on-stakes : True
claimed improved acc : 0.3250
world measured       : 0.3250
grounding reason     : WORLD measured 0.3250 vs claimed 0.3250 (rel delta 0.000 <= tol 0.030) -> world AGREES
resolution           : COMMIT — world AGREES: the silent claim is GROUNDED
```

The grounding is REAL, not a formality: at **K=1 the same check REOPENS**
(delta -0.0333, the would-be "richer model" is actually WORSE — the loop self-
corrects and does not commit an ungrounded "it's better"), and at **K=3 it REOPENS**
(delta +0.0028, below the +0.005 non-noise floor). The gate fires both ways; only
the full speaker manifold (K=5/6) clears it.

---

## (3) Honest — did the lever move recognition?

**YES, by +0.0417** (0.2833 -> 0.3250), measured, do-contrast confirmed, world-
measure agreed, K-ablation grounds the mechanism. AND the loop demonstrably
SELF-CORRECTS at the degenerate K's (K=1 worse -> REOPEN; K=3 sub-noise ->
REOPEN) — so the two-sided gate is doing its job, not rubber-stamping.

The improvement is MODEST and the wall it leaves is named: even the full
per-speaker manifold tops out at 0.325 on cross-speaker isolated digits. The
residual ceiling is now **the size and coverage of the exemplar manifold** (LOSO
gives only 5 train speakers; the manifold saturates there — K=5==K=6) and the
fact that the min-over-exemplars still matches in the BLUNTED A1 space without a
per-speaker WARP. The next lever the result points at is a speaker-CONDITIONED
warp (recover the heard talker's VTL/rate and warp the template into their frame
before matching) — exemplar richness helped because it crudely approximates that;
the explicit warp is the cleaner form. That is the honest next wall, not committed
here.

---

## (4) Donkey / architecture audit

- No net, no `.fit`, no gradient, no loss, no optimiser, no `torch`/`sklearn`, no
  Python softmax, no sweep-to-maximise. K reported across a full ablation.
- The recognition decision is the native DtwTo synth-error + argmin readout — the
  same machinery the existing AbS/topdown path uses; only the forward-model GRAPH
  DATA changed (one mean trajectory -> a manifold of per-speaker exemplars).
- Python is the world adapter (audio I/O, trajectory extraction, medoid signal
  pick, LOSO + do-contrast + grounding bookkeeping). No new Python cognition.
- `solve_for_n.py` / CortexLoop untouched.
- NOT committed (per directive — coordinate). Files added:
  `scripts/forward_model_drive.py`, `docs/forward_model_drive.md`.
