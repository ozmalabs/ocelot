# Prosody / syllable-structure frame in the multi-frame collapse

**Question (per `ozma_unabstracted_dimensions_roadmap` + `ozma_collapse_multiple_frames`):**
add the cheapest, highest-constraint frame — "how many + what type of syllables" —
to the multi-frame weighted-admissibility collapse and test whether it lifts
cross-speaker recognition. Prosody is NOT orthogonal: syllable count is a soft
**excluder on the word**, coupled to the lexical frame (a 1-syllable and a
3-syllable word are disjoint candidate sets).

## (1) What was wired (donkey audit)

- **Syllable extractor** — `domains/prosody_syllable.py:extract_syllables`. Owned
  envelope DSP, **no net, no fit**: per-frame RMS energy (10 ms hop) →
  zero-phase one-pole low-pass at 900 Hz (suppresses fricative/burst energy so
  `s`, `sh`, `t`, `k` bursts don't read as vowel nuclei) → Hann smooth (~70 ms) →
  count prominent local maxima separated by a **deep voiced-energy dip** (a real
  syllable boundary) and a minimum inter-nucleus gap (130 ms). Also returns a
  coarse primary-stress position. Thresholds are **fixed physical constants**
  (syllable ~150–400 ms, a juncture dips below 85% of the smaller peak), frozen
  from a one-time 19-word probe (count-match 0.74), **not swept-and-kept on the
  test set**.
- **Word syllable structures (lexicon = world knowledge)** —
  `WORD_SYLLABLES`: a **stated English pronunciation dictionary** for the 35
  Speech-Commands words (count + primary-stress fraction). **Source:** standard
  English dictionary syllabification, hand-stated because CMUdict was not
  available offline and the SC vocab is small and fixed (e.g. `no`:1, `seven`:2,
  `zero`:2, `visual`:3). The dictionary never sees audio.
- **Prosody frame (owned soft excluder)** — `prosody_excluder`: a word whose
  dictionary count differs from the extracted count is carved by
  `-COUNT_STEP·|Δcount|` (graded: off-by-one < off-by-two), a matching word
  abstains (0). Same `[FLOOR,0]` log-admissibility convention as the acoustic /
  n-gram frames, so it drops straight into `frame_inference_v2.weighted_admissibility`.
- **Collapse** — the agent's existing weighted-admissibility intersection
  (`domains/frame_inference_v2.py`). The prosody excluder is added alongside the
  acoustic + real n-gram (context + future-sheaf) excluders. Held-out speakers
  realise the audio and are **never banked**. CortexLoop untouched.

Harness: `scripts/prosody_syllable_frame.py` (reuses the
`under_determined_real` test-set builder; the expensive per-item DTW acoustic
read and the cheap envelope read are each computed **once**, the same set decoded
under every condition).

## (2) Cross-speaker results (n = 3000, 34 held-out speakers, vocab 35, chance 0.029)

Run: `python -m scripts.prosody_syllable_frame 120 40 16 8 3000`
(120 train / 40 held-out speakers; LibriSpeech n-gram from 2703 utterances, 1504 real items.)

| condition | cross-speaker acc |
|---|---|
| (a) acoustic-only (single frame) | **0.138** |
| (b) multi-frame WITHOUT prosody (acoustic + n-gram) | **0.767** |
| (c) multi-frame WITH prosody (b + syllable frame) | **0.761** |

**Prosody lift over the multi-frame baseline (pros_w=1.0): −0.006** (no lift).

Prosody-weight surface (verdict reads pros_w=1.0; reported, not fit):

| pros_w | (b) no prosody | (c) prosody | lift |
|---|---|---|---|
| 0.5 | 0.767 | 0.768 | +0.001 |
| 1.0 | 0.767 | 0.761 | −0.006 |
| 2.0 | 0.767 | 0.652 | −0.115 |
| 4.0 | 0.767 | 0.610 | −0.157 |

Isolated (no n-gram): acoustic 0.138 → acoustic+prosody 0.144 (**+0.006**).

**Extraction cost:** prosody envelope read **0.28 ms/item** vs acoustic DTW
**105.9 ms/item** → prosody is **377× cheaper** than the acoustic frame. Cost is a
non-issue.

**KILL diagnostic — cross-speaker syllable-COUNT extraction accuracy = 0.751**
(extracted count == dictionary count, over the 3000 test items).

## (3) Verdict

**The cheap syllable frame does NOT lift cross-speaker recognition here** (−0.006 at
the principled weight; at best +0.001 at half weight; isolated over acoustic alone
only +0.006). It is essentially flat, and it *hurts* if over-weighted. The cost
prediction held (377× cheaper than the acoustic frame, ~free); the **lift
prediction did not**. Honest KILL.

**Why (two coupled reasons, both in the evidence):**

1. **The extraction is only ~75% reliable cross-speaker.** A soft excluder built
   from a count that is wrong a quarter of the time carves the *truth* a quarter of
   the time — exactly why over-weighting it (pros_w ≥ 2) collapses accuracy. At
   pros_w=1.0 the carve is too weak to add information yet strong enough to
   occasionally remove the right answer; it washes out. Sonorant-internal junctures
   (`follow`, `zero`, `sheila`, `seven`, `visual`) under-count because the
   voiced-energy envelope barely dips between nuclei (no silence boundary).

2. **The vocab's syllable counts are too uniform to constrain.** 26 of 35 words are
   monosyllabic; a count match leaves **21.2/35 ≈ 60%** of the vocab still admissible
   on average. The frame's *maximum* possible carve is small, and the real n-gram
   already over-determines the same items (baseline 0.767), so there is almost
   nothing left for a weak, coarse constraint to add.

This is not a failure of the *idea* (prosody-as-coupled-excluder) — it is this
**vocabulary** (overwhelmingly monosyllabic, the SC word set) and this **extractor's
cross-speaker reliability** (sonorant junctures). The frame would bite on a
vocabulary with a real spread of syllable counts (where a count match carves the
candidate set hard) and/or a sharper nucleus detector. On the Speech-Commands
vocab against an already-strong n-gram, it carries no usable signal.

**Donkey boundary respected throughout:** extractor = owned envelope DSP (no
net/fit); word structures = stated dictionary (world knowledge); frame = owned soft
excluder; collapse = the agent's weighted-admissibility; held-out speakers never
banked.
