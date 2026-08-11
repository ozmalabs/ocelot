# Top-down recovery — does the synthesis compensate for the blunt cochlea?

## (1) Verdict — LEAD

**YES — routing recognition through the TOP-DOWN recovery COMPENSATES for the
blunt cochlea.** On the SAME deliberately-blunted front end, the bottom-up
blunt-estimate recognition is capped; routing the same blunt-eared input through
the top-down recovery the agent already built (native collapse core T8 + owned
forward model T10 + surprise, with the coarse cue PRUNING the admissible set and
the full-resolution synthesis RESOLVING) lifts the cap and recovers most of the
way to the sharp-ear ceiling. The Jabberwock's postulate (top-down compensates,
don't densify the cochlea) is **confirmed** — with one honest qualification on the
*source* of the continuous gain (the prune+synthesis, not the context prior, on
random digit-strings).

The do-contrast numbers (FSDD, LOSO, 6 held-out speakers, 360 isolated recordings
+ 216 continuous segments):

```
ISOLATED DIGITS — same blunt ear, two routes:
  blunt   bottom-up   top-down   delta
   3        0.217      0.267    +0.050
   4        0.236      0.267    +0.031
   6        0.236      0.272    +0.036
  mean isolated-digit gain (top-down - bottom-up): +0.039
  sharp-ear reference (full A1) AxS acc          :  0.283
  best blunt bottom-up 0.236 -> best blunt top-down 0.272:
    recovers 76% of the blunt->sharp gap

CONTINUOUS digit-strings (blunt=4, 216 segments):
  BOTTOM-UP (blunt resolves, unigram)       : 0.083
  TOP-DOWN  (prune + synth, NO context)     : 0.204   (delta +0.120)
  TOP-DOWN  (prune + synth + bigram context): 0.204   (delta +0.120)
    of which prune+synthesis : +0.120
    of which context prior   : +0.000   (random strings -> flat bigram, honest)
```

Run captured to `/tmp/topdown_full.log` (`===MARKER_TOPDOWN_RECOVERY_COMPLETE===`,
`elapsed 29s`; process pgrep-verified gone). `scripts/solve_for_n.py` and
CortexLoop were **left untouched**.

The compensation is consistent across every blunt level (3/4/6 bands, all positive
on isolated digits) and large on continuous speech (+0.120, 2.5x the bottom-up
accuracy) — the blunt-eared input recognised far better by inverting the
full-resolution internal forward model than by letting the coarse snapshot resolve
the answer directly.

---

## (2) What was wired — native, file:line, architecture audit

The recognition decision is routed through the TOP-DOWN recovery, which is the
native collapse core iterated against the owned forward model with the coarse cue
as the admissibility PRUNE. **Nothing in the engine was reinvented** — this WIRES
the pieces the agent already built (`scripts/native_collapse.py`,
`domains/recognition_graph.py`, the `DtwTo` Rust Term,
`scripts/analysis_by_synthesis_accept.py`'s forward model).

| component | what it is | file:line |
|---|---|---|
| **the BLUNT ear** | coarsen the 25-patch A1 trajectory to N effective bands (box-car spectral downsample) — the "human bad ears" copy; SAME front end for both routes | `scripts/topdown_recovery.py:blunt_matrix` (`:103`) |
| **the MATCH** | `DtwTo(heard, forward_model[w])` — the native Rust DSL Term | `runners/dsl/src/term.rs:291`, composed by `domains/recognition_graph.py:synth_error_term` (`:92`), evaluated at `topdown_recovery.py:242` |
| **T8 collapse** | native manifold max/softmax/conf/surprise as graph Term-trees in Rust | `scripts/native_collapse.py:T_MAX_LW/T_Z/T_CONF/T_SURPRISE` (`:70-90`), evaluated at `topdown_recovery.py:262-272` |
| **T10 forward model** | per-word mean A1 trajectory, LOSO (full resolution + blunt projection) | `topdown_recovery.py:build_forward_model` (`:131`), reusing `analysis_by_synthesis_accept.utterance_trajectory` |
| **the PRUNE** | coarse cue ranks candidates -> top-K admissible set (graph data: non-admissible Cand gets lw=-1e30, removed from the manifold) | `topdown_recovery.py:prune_admissible` (`:288`) + `CollapseUnit.collapse` (`:248`) |
| **the PRIOR** | learned-category prior = log of a COUNT over train data (unigram; bigram-transition on continuous) | `topdown_recovery.py:build_prior` (`:140`) / `build_bigram_prior` (`:158`) |

**The two routes (`topdown_recovery.py`):**

- **(A) BOTTOM-UP** (`recognise_bottom_up`, `:299`): the blunt estimate RESOLVES —
  native collapse over ALL candidates with the match on the BLUNT forward model
  (`match_res='blunt'`). The coarse snapshot carries the whole decision. The cap.
- **(B) TOP-DOWN** (`recognise_top_down`, `:307`): the blunt cue PRUNES to the
  top-K admissible set, then the agent inverts its FULL-resolution forward model
  (`match_res='full'`) among the admitted, collapsed natively WITH the prior. The
  blunt ear narrows; the synthesis + prior resolve.

### Architecture audit (CLAUDE.md — native, no new Python cognition)

- **The cognition is native.** The DtwTo match, the manifold max, the softmax
  denominator, the candidate confidence, and the surprise all run as graph
  Term-trees evaluated by `substrate.evaluate` in Rust (audited:
  `topdown_recovery.py:242,262,263,270-272`). No Python `exp`/`log`/softmax
  touches the manifold.
- **The PRUNE and the PRIOR enter as GRAPH DATA**, not Python cognition: the prune
  restricts which Cand nodes carry finite `lw` (the non-admissible get `lw=-1e30`,
  removed from the native manifold); the prior is added to `lw` as a scalar. The
  RESOLUTION among the survivors is the native collapse Term-tree. The
  winner-readout `max(adm, key=-err+prior)` is the argmax of the same `lw` the
  native manifold collapses — a query, not a decision the Rust doesn't make.
- **The forward model is the owned synth** (per-word mean A1 trajectory, T10) — no
  TTS net.
- **Python is the world adapter + instrument only:** audio I/O, the blunt-ear
  coarsening (a mechanical box-car downsample of the band axis), the prior COUNTS,
  and the do-contrast bookkeeping. No new Python cognition was added.
- **Donkey-clean** (grep-audited): no `.fit`, no gradient, no loss, no optimiser,
  no net, no `torch`/`sklearn`, no softmax-in-Python, no sweep. The only `np.log`
  calls convert COUNTS to log-priors in the world adapter (a count, not a fitted
  parameter). The blunt level (3/4/6 bands) and `keep_k=3` are FIXED structural
  choices reported across, not swept-to-maximise.
- `solve_for_n.py` and CortexLoop **untouched**.

---

## (3) The numbers — the do-contrast

### Isolated digits (LOSO, 6 held-out speakers, 360 recordings)

The blunt ear caps bottom-up recognition; the top-down route recovers it. Every
blunt level shows a positive gain:

```
blunt   bottom-up   top-down   td(no-prior)   delta
  3       0.217      0.267       0.267        +0.050
  4       0.236      0.267       0.267        +0.031
  6       0.236      0.272       0.272        +0.036
mean gain +0.039;  sharp-ear ceiling 0.283
```

- The td(no-prior) column equals the with-prior column: on balanced isolated
  digits the unigram prior is near-flat, so the isolated-digit gain is **purely
  the prune + full-resolution synthesis** — exactly "the coarse cue prunes the
  manifold, the synthesis resolves."
- **Recovery toward the sharp ear:** the best blunt bottom-up (0.236) -> best
  blunt top-down (0.272) closes **76%** of the gap to the sharp-ear AxS ceiling
  (0.283). The blunt cochlea is *almost* as good as the sharp one **when the
  top-down recovery is present** — the existence-proof claim, measured.

### Continuous digit-strings (LOSO, blunt=4, 216 segments)

Where bottom-up has the least to lean on, the gap is largest:

```
BOTTOM-UP (blunt resolves, unigram)       : 0.083
TOP-DOWN  (prune + synth, NO context)     : 0.204   (delta +0.120)
TOP-DOWN  (prune + synth + bigram context): 0.204   (delta +0.120)
```

Top-down recognises **2.5x** as many segments correctly (0.204 vs 0.083) on the
blunt-eared continuous stream — the strongest single compensation. The honest
decomposition: **all +0.120 is the prune+synthesis; the bigram context prior adds
+0.000** because the test digit-strings are RANDOM (no real sequential structure,
so the bigram counts are near-uniform — the context prior is correctly flat). The
context-restoration channel is wired and ready, but on random strings there is no
context to restore; the compensation here is the synthesis, not the context.

---

## (4) Honest verdict — postulate confirmed, with the precise qualification

**The agent's postulate is CONFIRMED in its core claim:** routing recognition
through the top-down recovery COMPENSATES for the blunt cochlea. The blunt
bottom-up estimate is capped (0.236 isolated / 0.083 continuous); routing the same
blunt-eared input through the collapse core + full-resolution forward model lifts
it (+0.039 isolated, recovering 76% of the blunt->sharp gap; +0.120 continuous).
The mechanism is exactly the prescription — the coarse cue PRUNES the admissible
set and the synthesis RESOLVES — and it is native cognition (collapse / DtwTo /
surprise in Rust) over the owned forward model, donkey-clean, with
`solve_for_n.py`/CortexLoop untouched. *Densifying the cochlea was not the lever;
inverting the internal forward model was.*

**The honest qualifications (read the numbers, not the boolean):**

1. **The compensating channel is the SYNTHESIS, not (yet) the context prior.** The
   isolated gain is the prune + full-resolution AxS; the continuous gain is the
   same. The bigram context prior contributed **+0.000** because the test strings
   are random — there is no sequential structure to restore. The directive named
   "restoration from context" as a top-down compensation; this run shows the
   *forward-model inversion* arm compensates strongly, but does NOT demonstrate the
   *context-restoration* arm (the venue gives it nothing to do). The precise
   remaining piece to demonstrate context-restoration is a venue with REAL
   sequential structure (structured digit-strings or LibriSpeech word n-grams),
   where the bigram/order-N context prior has signal — the order-N loop's W4
   top-down-restoration already shows boundary restoration on continuous strings;
   this would show *identity* restoration from context.

2. **Absolute accuracy is modest** (sharp-ear ceiling 0.283 on 10-way LOSO
   cross-speaker off a single mean-trajectory forward model — the known W5
   forward-model-resolution ceiling). The do-contrast is the result, not the
   absolute: top-down beats bottom-up on the SAME blunt ear at every level, and the
   blunt-eared top-down nearly matches the sharp-eared ceiling. The compensation is
   the finding; the ceiling is the next lever (a sharper forward model, W5
   babble-refinement — NOT a sharper ear), consistent with the Jabberwock's
   reframe.

3. **The prune can also bound top-down.** When the blunt cue is very coarse
   (3 bands) its top-K admissible set can occasionally exclude the truth, capping
   top-down too. With `keep_k=3` the prune still admits the truth often enough that
   the gain is positive at every level, but a fully-faithful "prune never rules out
   the answer" would use a softer admissibility (wider K or a soft mask). The
   reported gains are therefore a LOWER bound on the synthesis's compensation.

### Files

- `scripts/topdown_recovery.py` — the do-contrast: the blunt ear (world adapter),
  the two recognition routes (bottom-up blunt-resolves vs top-down prune+synthesis
  +prior) over the native collapse core + owned forward model, the LOSO harness.
  NEW.
- `docs/topdown_recovery.md` — this report. NEW.
- `/tmp/topdown_full.log` — full captured run
  (`===MARKER_TOPDOWN_RECOVERY_COMPLETE===`).

Reused unchanged: `scripts/native_collapse.py` (T8 collapse + surprise),
`runners/dsl/src/term.rs` `DtwTo` (the match), `domains/recognition_graph.py`
(`synth_error_term`), `scripts/analysis_by_synthesis_accept.py` (the forward model
+ A1-trajectory ingest). `scripts/solve_for_n.py` and CortexLoop UNTOUCHED.
