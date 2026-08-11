# Native cutover — the agent's native Terms ARE the recognition path

GO NATIVE is not done until the native Terms REPLACE the Python. This document records the
CUTOVER: the validated native cognition (commit 478bb604 — native_fusion, native_cognition
d_A + rel-formants, the Log/Exp Rust Terms) is no longer a PARALLEL driver. The main
recognition scripts now EXECUTE the native Terms via `substrate.evaluate`, and the parallel
Python decision code they replaced is gone from the recognition path.

Per memory: ozma_native_migration_is_ownership_not_fidelity (native MAY diverge — that is the
point) and ozma_agent_owns_its_perception.

## 1. What was cut over

The recognition DECISIONS in the three main scripts
(`scripts/formant_trajectory_dynamics.py`, `scripts/articulatory_gamma.py`,
`scripts/perception_composition.py`) now route through the agent's graph-resident native
Terms (substrate.evaluate, native Rust eval), NOT Python:

| decision | was (Python) | now (native Term) |
|---|---|---|
| FUSION (the headline) | `max(DIGITS, key=logA[w])` dict-comp argmax | `domains.native_fusion.predict_fusion_term` — Argmax over Plus of [Minus(Attr,MaxOver), Times(Lit,Minus(Attr,MaxOver)), Attr] |
| articulatory d_A | `min(DIGITS, key=articulatory_distance[w])` (fixed-resample L2 + Γ) | `domains.native_cognition.predict_articulatory_term` / `native_articulatory_scores` — Argmin of Plus[Times(Lit, DtwTo(obs_rel, syn_rel)), Times(Lit, Γ) (+ Times(Lit, DtwTo(obs_voi, syn_voi)) when the gap is observed)] |
| rel-formants | `np.log(F) - np.mean(np.log(F))` | `domains.native_cognition.rel_formants_channel_term` — Log(Nth(f,i)) - Div(Plus(Log(Nth(f,·))), Lit(n)), composed Mean, native Log |
| formant prong ALONE | `min(DIGITS, key=d_h[w])` | `dtw_predict_term()` — Argmin over Concepts of MinOver(exemplars) DtwTo, evaluated natively |
| k=3 mel majority vote | `Counter([w for _,w in ds[:KNN_K]]).most_common(1)[0][0]` | `domains.native_vote.predict_vote_term` — Argmax over words of Count(MelExemplar in-top-k AND word==w), with a nearest-distance tiebreak (Fold/set-threaded top-k via Count(Filter(Lt rank)) — NO new primitive) |

### The ported k=3 vote (the deferred decision)

The exemplar baseline's `Counter(...).most_common` vote is the agent's own composition: a
Fold/set-threaded top-k that needs NO new primitive. The native realisation
(`domains/native_vote.py`):

```
rank(e)   = Count( MelExemplar e2 : e2.mel_dist < e.mel_dist )    # how many are nearer
votes(w)  = Count( MelExemplar e  : e.mel_word == w  AND rank(e) < k )
score(w)  = BIG*votes(w) - MinOver_{e in topk(w)} e.mel_dist       # nearest-distance tiebreak
predict   = Argmax over { Concept : is_word==1 } of score(w)
```

The rank-via-Count is the set-based top-k (no Sort/TopK primitive). The MinOver tiebreak is
the faithful native realisation of `Counter.most_common`'s insertion-order (= ascending-
distance) tiebreak. Isolated validation: 1000/1000 = 100.0% agreement with the Python
`Counter.most_common` vote on distinct DTW distances; the only divergence is an exact tie at
the k-th distance (the deliberate ownership boundary — both choices are reasonable; the native
one counts every tied exemplar with no arbitrary list-order break).

## 2. Donkey audit — cognition native, transduction/I/O the flagged boundary

COGNITION (now native Terms, substrate.evaluate — no net, no .fit, no gradient, no sweep, no
learned weight):
- the fusion argmax, the articulatory d_A argmin (+ voicing prong), the rel-formant invariant,
  the formant-prong argmin, the k-NN majority vote.

TRANSDUCTION + I/O (the DELIBERATE boundary — stays Python, world-adapter only):
- `load_wav` / `gather_files` (file I/O), the LPC-root formant tracker (`estimate_formants`,
  `formant_track`) and the Viterbi pairing tracker, the articulatory-Γ FORWARD MODEL
  (`articulatory_models` — gesture scores, source-filter nomogram, the Γ continuity/inertia/
  reachability synthesis; these are owned constants stored as graph attrs, consume no observed
  data), the log-mel front end + `mi.dtw` distance kernel (the per-pair DTW SCORE; the
  SELECTION/vote over those scores is native), the `unvoiced_gap_detect` envelope, the
  train-only n-gram counting and tau scales (corpus statistics), the speaker mel-normalisation.

The reliability weight `w_art` is a TRAIN-measured constant fed into the native fusion Term as
a `Lit` (a per-fold measurement, not a learned/swept parameter). Held-out speaker NEVER banked;
CortexLoop + solve_for_n untouched. No Rust was added — every Term uses primitives already in
`runners/dsl/src/term.rs` (Argmax, Argmin, DtwTo, Log, MaxOver, MinOver, Count, Filter, Lt,
Eq, And, Plus, Minus, Times, Nth, Attr, NodesWhere, Neighbours).

NOTE (Var-name boundary discovered): the native env binding only resolves Var names WITHOUT a
leading underscore (`{"_e": id}` fails to bind; `{"ei": id}` works). native_vote's inner vars
are therefore underscore-free.

## 3. Cutover accuracy (FSDD LOSO, n=3000, chance 0.10, held-out NEVER banked)

(from /tmp/native_cutover_full.log — full runs, n=3000, 6-speaker LOSO, chance 0.10)

**formant_trajectory_dynamics** (native rel-formants + native formant-DTW prong + native k=3 vote):

| recogniser (native path) | prior baseline | cutover | n |
|---|---|---|---|
| STATIC nucleus 1-NN (Python baseline, diagnostic) | — | 29.2% | 3000 |
| FORMANT-TRAJECTORY + order-N dynamics (native DTW Argmin) | ~62% class | 58.9% | 3000 |
| EXEMPLAR k-NN vote (NATIVE) | 83.5% | **83.5%** | 3000 |

**articulatory_gamma** (native d_A + native fusion + native formant prong + native vote):

| prong (native path) | prior baseline | cutover | n |
|---|---|---|---|
| FORMANT-TRAJECTORY prong (NATIVE DTW Argmin) | 62.2% | **62.2%** (EXACT) | 3000 |
| ARTICULATORY-Γ d_A prong (NATIVE DtwTo Argmin) | — | 25.6% | 3000 |
| n-gram prong (degenerate prior) | — | 10.0% | 3000 |
| MULTI-PRONGED FUSION (NATIVE Argmax) | 59.4% gap-dropped | **58.4%** | 3000 |
| EXEMPLAR k-NN vote (NATIVE) | 83.5% | **83.5%** (EXACT) | 3000 |

**perception_composition** (native d_A incl. voicing prong + native fusion + native vote):

| perception | formant (native) | articulatory d_A (native) | FUSED (native) | exemplar vote (native) | n |
|---|---|---|---|---|---|
| (a) CURRENT (gap-dropped) | 62.2% | 25.6% | 58.4% | 80.6% | 3000 |
| (b) RE-COMPOSED (gap-observed, native voicing DtwTo prong) | 62.2% | 32.7% | 57.1% | 80.6% | 3000 |

The gap/voicing re-composition now runs as a native DtwTo prong inside the d_A Term (the
articulatory-prong-alone climbs 25.6% → 32.7% when the gap is observed, exactly the prong the
voicing channel targets); fusion does not net-improve (58.4% → 57.1%) — the same HONEST finding
as before the cutover (binary voicing envelope too coarse at this weight), now with the decision
native. The perception_composition exemplar vote reads 80.6% (vs 83.5% in ftd/articulatory_gamma)
because this script's corpus is built through the `PerceptionGraph` (the LPC `voiced_formant_track`
path) which skips a slightly different token subset — a CORPUS/transduction difference, NOT the
vote: the native vote is byte-faithful (ftd + articulatory_gamma both read EXACTLY 83.5%, and
isolated validation was 1000/1000).

### Faithful vs divergent (as predicted)
- FAITHFUL (EXACT): the formant-trajectory DTW prong reproduces 62.2%, and the exemplar k-NN
  vote reproduces 83.5% — both byte-equal to the Python baseline (same arithmetic, now graph-
  resident; the vote's Counter-tiebreak is matched by the native nearest-distance MinOver).
- DIVERGENT BY DESIGN (ownership): the articulatory d_A uses native DtwTo (banded Sakoe-Chiba
  warp), a SUPERSET of the Python fixed monotone resample. This flows into the fusion (log_a_a),
  so MULTI-PRONGED FUSION = 58.4% vs the 59.4% gap-dropped baseline (−1.0 pt). This is the
  OWNERSHIP outcome, not a regression — the agent's DtwTo decision, not the Python resample.
  (Isolated d_A native-vs-Python agreement was ~74% in the accept harness, exactly this.)
- The n-gram prong-alone is 10.0% (it argmaxes a near-flat train prior — degenerate by design;
  its real contribution is inside the native fusion as a soft excluder).

## 4. VERDICT

The MAIN recognition path now EXECUTES the agent's native Terms. The Python decision code that
duplicated them is GONE from the recognition path:
- the dict-comp fusion argmax → `NF.native_predict` (Argmax-of-Plus-of-Times Rust Term);
- the `min(DIGITS, key=articulatory_distance)` d_A → `NC.native_articulatory_predict` /
  `native_articulatory_scores` (Argmin of DtwTo+Γ, +voicing DtwTo in the re-composed perception);
- `np.log(F)-mean` rel-formants → `NC.native_rel_formants` (Log + composed Mean Term);
- the formant-prong `min(DIGITS, key=d_h)` → the native `dtw_predict_term` Argmin;
- `Counter(...).most_common` k=3 vote → `NV.native_vote` (Count/Filter/Argmax top-k Term).
The numpy `articulatory_distance_recomposed` was deleted; `articulatory_distance` /
`_resample_to` survive ONLY as the Python reference inside the accept harnesses (validators),
not in the main `evaluate`.

CUTOVER IS REAL. Faithful where faithful (62.2% formant prong, 83.5% exemplar — exact),
divergent on d_A by design (DtwTo warp → fusion 58.4% vs 59.4%, the −1.0 pt is the ownership
delta, not a bug). No net / .fit / gradient / sweep; transduction (LPC/Viterbi/mel/Γ-forward-
model/mi.dtw) + I/O are the flagged Python boundary; held-out never banked; CortexLoop +
solve_for_n untouched; no Rust added (all primitives pre-existing).

### The remaining boundary (honest)
Still Python, deliberately (transduction + I/O, not cognition): file I/O (`load_wav`,
`gather_files`); the LPC-root + Viterbi formant trackers; the articulatory-Γ FORWARD MODEL
(gesture scores + nomogram + Γ synthesis — owned constants stored as graph attrs); the log-mel
front end + the `mi.dtw` pairwise distance KERNEL (the per-pair score; the top-k SELECTION over
those scores is native); the `unvoiced_gap_detect` envelope; train-only n-gram counts, tau
scales, the k-th-nearest distance scalar, and the `w_art` reliability weight (corpus statistics,
fed to the native Terms as Lit/attr); speaker mel-normalisation. Diagnostic BASELINES that stay
Python (labeled comparison references, not the recognition decision): the static-nucleus 1-NN
and the n-gram-prong-alone argmax.
