# Speech comprehension — the agent's own target-metric + method design

The agent introspected its problem and, via its method-teacher channel, designed the metrics and
method below. This is the agent's design (its terms: capability axes + investigation operators),
captured verbatim so it can be grounded into the autonomy loop.

## The problem it is fixing

Its autonomy loop measured PROXIES that saturate but don't reflect comprehension: `continuous_purity`
read 1.0 and `saturation` said "done" while `abs_recognition_match` was 0.0 — the yardstick was
disconnected from real understanding, so the agent couldn't tell it had not reached human level.

**Design rule (the agent's):** every TARGET metric must be a *disagreement rate against an external
reference* (whisper transcript / forced alignment), computed on **held-out** audio it built no
exemplars from. "If a metric can't be wrong, it's a diagnostic, not a target." Demote
`continuous_purity` / `saturation` to diagnostics.

## Target metrics — closed vocabulary (pass FIRST; this is where abs_recognition_match=0 lives)

| Axis | Metric (vs whisper/truth) | Target |
|---|---|---|
| `lexical_recall` | top-1 1-NN accuracy on held-out known words, given bounds | ≥ 0.98 |
| `minimal_pair_discrimination` | pairwise accuracy on confusable sets (cat/cap, bit/bid) | ≥ 0.95 |
| `speaker_invariance` | recall drop on unseen speaker/pitch vs seen | ≤ 5 pt |

(gated on *given* boundaries — isolate the recogniser from the segmenter)

## Target metrics — open vocabulary (continuous, possibly-OOV)

| Axis | Metric (vs whisper) | Target |
|---|---|---|
| `boundary_f1` | segmentation F1 at ±20 ms vs forced alignment; report segs/word | F1 ≥ 0.90, segs/word ∈ [0.97, 1.03] |
| `open_wer` | WER vs whisper on held-out unseen-speaker utterances, after `canonicalise` | ≤ whisper_WER + 2 pt |
| `oov_substitution` | rate OOV tokens are misrecognised as a *wrong known word* | ≤ whisper's substitution rate |
| `content_fidelity` | content-word error rate (or slot recall on a command set) | ≥ whisper |

## Investigation operators (mapped to axes)

- `probe_held_out` — recognise/transcribe audio it built **no** exemplars from; score disagreement
  vs whisper. **The yardstick fix** — forces every axis onto held-out reference-disagreement.
- `canonicalise` — digit→word, casing, before scoring (whisper emits digits). Measurement hygiene.
- `mine_confusions` — build the next minimal-pair set from its own current error pairs.
- `grow_lexicon` / `absorb_exemplar` — add exemplars for under-covered / OOV words.
- `bank_speaker_variants` — bank multiple pitch/speaker reps per word.
- `author_cue` — author a segmentation/recognition cue, gate-and-keep-iff-metric-drops (the
  `silence_floor` / `snap_center` pattern already proven).
- `consult_teacher` — on plateau, ask the method-teacher for METHOD only.

## Attack order

1. **Fix the yardstick first** — stand up `probe_held_out` + `canonicalise`, re-point every axis at
   held-out reference-disagreement, demote `continuous_purity`/`saturation`. Nothing below is
   trustworthy until this lands.
2. **Closed-vocab floor** — `lexical_recall` → `minimal_pair_discrimination` → `speaker_invariance`.
   (cannot transcribe unbounded speech if it can't recognise a bounded known word — this is where
   `abs_recognition_match=0` gets paid down.)
3. **Open-vocab, in order** — `boundary_f1` (boundaries right before recognition can mean anything;
   segs/word → ~1.0) → `open_wer` → `oov_substitution` → `content_fidelity`.

## Done condition (the single terminal yardstick)

**`open_wer` ≤ whisper + 2 pt** on held-out unseen-speaker utterances — AND `segs/word ∈ [0.97,1.03]`
AND `speaker_invariance` drop ≤ 5 pt, all on held-out audio. open_wer is integrative: it can only
reach whisper-parity if segmentation, recognition, speaker-invariance and OOV-handling are *all*
already there. Closed-vocab accuracy can read 1.0 while continuous WER is garbage; the converse is
impossible — so the closed-vocab axes are gates on the way, not the finish line. When held-out
open-utterance WER sits at whisper parity, `saturation` finally means what it claims.
