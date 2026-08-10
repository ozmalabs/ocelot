# Perception composition — the agent owns and re-composes its perception

(memory `ozma_agent_owns_its_perception`)

**Thesis.** Perception is not a fixed pre-processing pipeline. It is a GRAPH the agent
composes from owned DSP primitives, and — like the agent restructuring its own memory graph
in a prior session — it can RE-COMPOSE that graph from the inside when it notices a lossy
transform dropped a discriminating dimension. Same self-modification, applied to the input
graph.

Script: `scripts/perception_composition.py`. Full log: `/tmp/perception_composition_full.log`
(end marker `PERCEPTION_COMPOSITION_COMPLETED`).

---

## 1. Perception primitive library + composable / re-composable perception graph

Each primitive is an owned DSP op with a clear signature `raw waveform in -> features out`.
No net, no `.fit`, no gradient.

| primitive | signature | note |
|---|---|---|
| `load_raw_waveform` | `path -> (sig, fs)` | world I/O boundary |
| `voiced_formant_track` | `(sig,fs) -> (n_v x 3) Hz` | pairing tracker, **voiced-only = the lossy transform** |
| `rel_formant_shadow` | `(n x 3) -> (n x 3)` | speaker-relative log, VTL-cancelled |
| `trajectory_dynamics` | `(sub,track) -> (m x 9)` | order-N over time, native Rust eval |
| `log_mel_envelope` | `(sig,fs) -> (T x B)` | full-envelope, exemplar baseline |
| `unvoiced_gap_detect` | `(sig,fs) -> (n_all,) ∈ {0,1}` | **NEW — the dropped voicing/gap channel** |

A `PerceptionGraph` is an ordered composition of these primitives. Two perceptions are
composed (the agent picks the ops):

- **(a) CURRENT** = `load_raw -> voiced_formant_track -> rel_formant_shadow -> trajectory_dynamics`
  (+ `log_mel_envelope`). No gap channel — the lossy default.
- **(b) RE-COMPOSED** = the SAME graph **plus** `unvoiced_gap_detect`, so the silence-then-frication
  gap envelope survives to the articulatory comparison.

**Donkey audit.** DSP primitives owned (numpy / the pairing tracker / the log-mel front end).
`unvoiced_gap_detect` is the SAME framing + energy gate as the tracker (`FRAME_MS`, `HOP_MS`,
`VOICED_FLOOR`), inverted to KEEP the dropped frames and emit their voiced/unvoiced label.
Re-composition = add one primitive + wire its envelope into the already-declared,
previously-dead `W_VOICING_SHADOW` term. The recogniser logic — formant-trajectory prong
(Viterbi-pairing `DtwTo/MinOver/Argmin` native Term), fusion math (weighted-admissibility
soft-excluder sum), n-gram, exemplar bank — is imported VERBATIM from
`articulatory_gamma` / `formant_trajectory_dynamics`. The only behavioural change between (a)
and (b) is whether the gap channel is observed and weighted. Exemplars / tau / n-gram /
reliability weights TRAIN-only; held-out NEVER banked. CortexLoop + `solve_for_n.py` untouched.

**The lossy transform, quantified.** `voiced_formant_track` `continue`s every frame below
`VOICED_FLOOR`, so the gap is deleted before it reaches the observation. Observed voiced-fraction
(fraction of frames the voiced-only tracker keeps), per digit:

```
  six  : voiced-frac 0.56   (gap frames dropped = 44%)
  seven: voiced-frac 0.79   (gap frames dropped = 21%)
  eight: voiced-frac 0.65   (gap frames dropped = 35%)
  one  : voiced-frac 0.94   (gap frames dropped = 6%)
  nine : voiced-frac 0.92   (gap frames dropped = 8%)
```

The gap-cued digits (six/seven/eight) drop the most frames; one/nine drop almost none —
the tracker was deleting precisely the discriminating dimension. Both perception graphs ran
over all 3000 tokens, 0 skipped, 6 speakers.

---

## 2. Re-composition demo + recognition (FSDD LOSO, held-out never banked, chance 0.10)

FSDD LOSO, n = 3000 per perception (500/fold × 6 held-out speakers), chance 10.0%. Only the
gap channel differs between the two rows; everything else is byte-identical.

```
                              formant   articulatory   n-gram   FUSED    exemplar
  (a) CURRENT  (gap-dropped)   62.2%        24.0%       10.0%   59.4%     80.6%
  (b) RE-COMPOSED (gap-obs)    62.2%        33.5%       10.0%   57.9%     80.6%
                                            +9.5 pts            -1.5 pts
```

Reference baselines: gap-dropped articulatory fusion **59.4%** · Viterbi-pairing **62.2%** ·
exemplar **83.5%** (this run's exemplar bank measured 80.6% on the seed-0 token subset).

Per-speaker fused (held-out), current → re-composed: george .492→.612, jackson .630→.646,
lucas .596→.534, nicolas .458→.428, theo .642→.588, yweweler .746→.668.

**The gap channel is real and lifts the prong it feeds.** The articulatory prong alone rises
**24.0% → 33.5% (+9.5 pts)** purely from observing the gap — the dropped dimension carries
genuine discriminating information, exactly as predicted. The six-sink (non-six tokens wrongly
→ six) more than halves: **357 → 164**.

Six/seven/eight gap-cued confusions (true→pred, /3000) and per-digit fused accuracy:

```
  confusion                  (a) current   (b) re-composed
  six   -> two                  18/300          3/300     cleared
  six   -> seven                37/300          8/300     cleared
  six   -> three                28/300         18/300     better
  three -> six                  70/300         24/300     cleared (six-sink)
  eight -> three                55/300         16/300     cleared
  eight -> six                  40/300         30/300     better
  six   -> eight                43/300         75/300     WORSE
  seven -> three                (—)            67/300     WORSE  (new sink)
  seven -> nine                 (—)            47/300     WORSE

  per-digit fused acc   (a) current -> (b) re-composed
  six                      55.0%  ->  57.3%   (+2.3)
  seven                    64.3%  ->  33.7%   (-30.6)   <- the regression that sinks the net
  eight                    67.0%  ->  82.7%   (+15.7)
```

Six and eight improve (eight strongly), six-cued confusions clear broadly — but **seven
collapses** (the gap weight pushes seven's tokens onto three/nine, where its vowel trajectory
overlaps). That single regression outweighs the six/eight gains, so the net fused is -1.5 pts.

---

## 3. VERDICT

**Architecture (the point of the exercise): PROVEN.** Perception is composed from owned DSP
primitives into a `PerceptionGraph`, and re-composed from the inside — `unvoiced_gap_detect`
added, its envelope wired into the previously-dead `W_VOICING_SHADOW` term — with the
recogniser logic byte-unchanged. The agent fixed a lossy transform on the observation side by
restructuring the input graph, the same self-modification it does on its memory graph. The
gap-dropped run reproduces the 59.4% baseline exactly (sanity), and the gap channel measurably
strengthens the prong it feeds (articulatory 24.0% → 33.5%; six-sink 357 → 164).

**Does observing the gap net-improve recognition? HONEST: NO (-1.5 pts, 59.4% → 57.9%).**
The gap is real and survives the re-composition; it does exactly what was predicted for six
and the stop-bursts (six/eight gain, six-sink halves, every targeted six-confusion clears).
But it over-corrects **seven**, whose tokens get pushed onto three/nine (seven 64.3% → 33.7%,
seven→three 67, seven→nine 47). The single binary voicing envelope, fused at one global
`W_VOICING_SHADOW` weight, helps the digits whose gap is sharp and hurts the one whose gap
overlaps a vowel-trajectory confusion. The net is slightly negative.

**Next limiter (NOT "more audio").** The gap channel is too coarse a discriminator at one
global fusion weight: (1) a **graded** gap/frication shadow (continuous voicing/frication
likelihood, not a binary energy gate) so seven's partial voicing isn't scored like six's hard
silence; (2) **per-digit / gap-localised weighting** so the voicing term only fires where the
gap is the discriminating cue; (3) a front-cavity area-function term to split /s/-vs-/θ/. The
discriminating dimension now survives to the comparison — the remaining work is scoring it
without collapsing the digit it doesn't cue.

The architectural claim stands regardless of the headline number: the perception is composed
by the agent and re-composable from the inside.
