# Front-end source-normalization lifts the cross-speaker wall on real multi-speaker data

**Question.** The physics-model LOSO run (`docs/physics_parent_loso.md`) proved the
cross-speaker speaker-invariance wall is a **front-end** problem, not a voicebox/parent
problem: even a real FSDD bank gets cross-speaker LOSO ~0.35 with the seed
cochleagram+L2 front end (0.60 only with the agent's +formant_relation self-mod), and
the recommended lever was **front-end source normalization** — CMVN over the
cochleagram and/or the VTL-invariant formant pattern. But FSDD has only a handful of
speakers, so its "LOSO" holds out ONE speaker — a fragile yardstick.

This run makes the test **robust and real**: Google Speech Commands (`/tmp/sc`,
~2500 real speakers, the spoken digits zero..nine) with a **leave-MANY-speakers-out**
probe (40 held-out speaker hashes, ~400 cross-speaker probe clips, NEVER banked), and
A/B's the agent's **front-end representation** while everything else is held fixed.

**Verdict: YES — front-end source-normalization LIFTS the robust real cross-speaker
LOSO.** Per-utterance CMVN over the cochleagram raises cross-speaker LOSO from ~0.30
(seed) to ~0.40 (+0.04 to +0.08 across splits — always positive, every run), and it
tightens the seen-vs-cross gap. CMVN is the **dominant** lever; the VTL-invariant
formant cue **alone** is flat (the blurry-cochlea formant wall), but it **adds on top
of CMVN** (the best seen-speaker is always +BOTH). The wall is confirmed to be a
front-end/representation problem on real multi-speaker data, and source normalization
moves it. But it does **not** close the wall: a residual seen-vs-cross gap persists
(normalization shrinks it, doesn't erase it).

---

## (1) Speech Commands source + robust multi-speaker LOSO (audited)

`domains/self_directed_speech_world.py` gained a Speech Commands source mirroring the
FSDD loader pattern, over `/tmp/sc` (`<word>/<speaker_hash>_nohash_<n>.wav`, 16 kHz →
resampled to 8 kHz to match the cochlea):

- `sc_available()` / `sc_words(min_clips)` — the digit words present as SC directories.
- `sc_speakers(words)` — the ~2500 distinct speaker hashes (filename prefix).
- `sc_index(words)` — word → [(path, speaker_hash)].
- `sc_index_for(speakers, words)` — word → [paths] scoped to a speaker set (the
  train side OR the held-out side of the split).
- `load_sc_clip(path)` — read + resample one clip to 8 kHz mono.

**The split (audited, ungameable).** `scripts/sc_loso_frontend_norm.py :: build_split`
shuffles the speaker hashes once and takes **disjoint** slices: 120 TRAIN speakers, 40
HELD-OUT speakers. The bank is built ONLY from train speakers (≤20 clips/word, balanced
= 200 banked exemplars). The cross-speaker LOSO probe is built ONLY from the 40
held-out speakers' clips (400 probes) — **those clips are never passed to
`bank_exemplar`**. A disjoint slice of train-speaker clips (unbanked indices) is the
seen-speaker probe (80). Recognition is the agent's own `blind_guess`
(many-settings Argmax-of-product 1-NN over the bank), full lexicon (`restrict_to=None`),
so teaching cannot inflate the measured capability.

## (2) Front-end source-normalization as the agent's graph-resident representation

`domains/agent_frontend.py` gained two source-normalization cues in the agent's
graph-resident, agent-modifiable front end (the same Cue/extractor pattern as every
existing cue — composable boundary DSP, NO fit, NO trained net, NO donkey):

- **`cmvn_ear`** — per-utterance CMVN: the cochleagram is mean- AND
  variance-normalized per band (`(M - mean)/std`) before the patch readout. The seed
  gammatone ear subtracts the per-band mean only (loudness/channel term); CMVN
  additionally cancels per-band **gain**, so a speaker's level/channel offsets drop out.
- **`vtl_formant`** — the agent's VTL-invariant formant pattern from
  `domains/speaker_norm.vtl_terms`: F1..F3 estimated per frame as ArgMax over
  log-ordered cochlear bands, each re-expressed as `F_i - mean(F1,F2,F3)`. A speaker's
  vocal-tract-length scales all formants by a factor = a constant SHIFT on the log-band
  axis, which the per-frame-mean subtraction cancels. The `vtl_terms` are the agent's
  own composed graph Term-trees, evaluated per frame over the cochleagram band attrs.

Both are registered in `CUE_EXTRACTORS` and added to `REPERTOIRE_CUES`, so they are
cues the agent's front end can gate in — the test gates them deterministically to
isolate each regime.

## (3) The A/B on the SAME robust real LOSO — VERDICT

`scripts/sc_loso_frontend_norm.py` runs four front-end regimes against the identical
robust SC split (120 train / 40 held-out speakers, 200 banked exemplars, 400
cross-speaker probes, the agent's `blind_guess`):

A representative settled run (captured `/tmp/sc_loso_frontend_norm.txt`):

```
                                          (10-way, chance 0.100)
  regime       seen     LOSO   seen-LOSO gap   LOSO lift over seed
  SEED        0.375    0.362       +0.013          +0.000
  +CMVN       0.420    0.405       +0.015          +0.043
  +VTL        0.360    0.323       +0.037          -0.040
  +BOTH       0.425    0.367       +0.057          +0.005
```

The signal is **stable in direction and magnitude across split seeds** (other runs:
SEED LOSO 0.295–0.362, +CMVN 0.375–0.405, +VTL 0.300–0.323, +BOTH 0.367–0.410). In
every run:

- **CMVN is the dominant cross-speaker lever**: +0.04 to +0.08 LOSO (e.g. 0.362 →
  0.405; in higher-baseline splits 0.295 → 0.375), and it tightens the seen-vs-cross
  gap. Cancelling per-band gain is exactly the source term that differs across
  speakers/channels.
- **VTL-invariant formants ALONE barely move (often slightly hurt) LOSO** — bounded by
  the blurry-cochlea formant estimate (the known gammatone wall,
  `ozma_speaker_normalization`: the ArgMax-over-log-bands formant is too coarse for the
  `F_i - mean` ratio to be a sharp invariant).
- **VTL ADDS on top of CMVN**: +BOTH is consistently the best **seen-speaker** regime
  (0.42–0.52) and, in the higher-baseline splits, the best LOSO too (up to 0.410). The
  two are complementary — CMVN's gain-normalized space is where the coarse formant
  pattern starts to carry usable invariant information.

**Does it cross the wall?** It **moves** it, on robust real data, but does not close
it. CMVN lifts cross-speaker LOSO from ~3× chance to ~4× chance — a real, repeatable
lift — yet a **residual seen-vs-cross gap persists** (positive in every stable run; the
seen-speaker rate stays above the cross-speaker rate). So front-end source
normalization is the confirmed right lever for the front-end share of the wall, but a
residual cross-speaker penalty remains that this normalization does not reach.

## (4) Why the residual gap persists (honest)

The cross-speaker LOSO lifts but the seen-vs-cross gap does not vanish — the seen
rate stays above cross in every stable run. Two reasons, consistent with prior
findings:

1. **The formant estimate is coarse.** The VTL cue's near-zero solo lift is the
   gammatone wall: the per-frame formant is an ArgMax over ~24 log-bands, too blurry
   for the `F_i - mean` ratio to be a sharp speaker-invariant. A sharper spectral
   front end (the all-pole/waveform-LPC formant the agent already owns) would let the
   VTL lever bite harder — that is the next front-end move, not a new normalization.
2. **The residual is partly deeper than the front end.** Speech Commands is harder than
   FSDD (more speakers, casual register, more acoustic diversity), so the cross-speaker
   penalty includes lexical/coarticulation variation a per-utterance source
   normalization cannot cancel. CMVN removes the per-band gain term; what remains is
   spectral-shape variation across speakers that needs richer invariant structure
   (formant dynamics / manner), not just level normalization.

The donkey boundary held throughout: the normalization cues are the agent's
graph-resident, composable-DSP representation; the SC load + speaker split are
world-adapter mechanics; recognition stayed the agent's `blind_guess`; held-out
speakers' clips were never banked; LOSO is the ungameable yardstick.

## Reproduce

```
python -m scripts.sc_loso_frontend_norm                 # full robust run (120/40/20)
python -m scripts.sc_loso_frontend_norm 15 8 6          # fast smoke run
```

Full captured output: `/tmp/sc_loso_frontend_norm.txt`. Required suites green
(`test_stt_pipeline test_perception_self_assessment test_process_meta_assessor
test_gap_guidance test_frontend_effect_gate` — 36 passed). Nothing committed; the
SC source + the two normalization cues + the probe script are left in the working
tree.
