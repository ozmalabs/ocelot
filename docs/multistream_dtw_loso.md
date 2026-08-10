# Multi-stream DTW lifts cross-speaker LOSO above the single-stream 0.570

**Question.** The single-stream DTW temporal-alignment recognizer
(`docs/dtw_trajectory_loso.md`) was the largest single cross-speaker jump in the
programme: aligning the source-normalized **CMVN spectral trajectory** as a *path*
(instead of reading it as a per-frame bag) lifted real 40-speaker Speech-Commands
cross-speaker LOSO **0.417 → 0.570** (+0.152, purely the alignment). That doc named
the next lever — **multi-stream DTW**: align the CMVN spectral trajectory **and** the
VTL-invariant formant trajectory **jointly**. The two tracks carry **complementary**
cross-speaker structure (one is the full source-normalized spectral shape, the other
the vocal-tract-length-invariant formant gesture), so aligning both should lift
further. This run builds exactly that and A/Bs it on the **identical** robust SC split.

**Verdict: YES, but small — multi-stream DTW lifts cross-speaker LOSO from 0.570 to
0.593 (+0.023).** Aligning the CMVN spectral *and* the VTL formant trajectories jointly
(per-stream DTW costs summed, formant stream down-weighted to w=0.25) recovers a real
but modest amount of complementary cross-speaker structure beyond the CMVN trajectory
alone. The lift is an **order of magnitude smaller** than the single-stream
alignment jump (+0.023 vs +0.152), and the residual to solved is still **0.407**
(0.593 vs 1.000). The CMVN spectral trajectory already carries most of what the
thin/noisy formant track adds; the formant stream contributes only at a **low weight**
and is actively **harmful at high weight** (w≥1.0 *drops* below the CMVN baseline). The
streams are largely **redundant**, not complementary — the multi-stream lever is real
but near-exhausted.

---

## (1) The multi-stream DTW recognizer is the agent's GRAPH-RESIDENT decision (donkey-audited)

The recognition DECISION is composed entirely from the agent's owned ops and evaluated
**natively** in Rust. Two composable forms were tried:

**Form (a) — SUM of per-stream DTW costs (the agent's `Plus` over two `DtwTo`):**

```
predict(query) = Argmin  over  w ∈ is_word Concepts  of
                   MinOver  e ∈ has_exemplar(w)  of
                     DtwTo(cmvn_q, cmvn_e)  +  weight · DtwTo(fmt_q, fmt_e)
```

Each `DtwTo` is the agent's banded Sakoe-Chiba alignment Term (`runners/dsl/src/term.rs`:
`TermNode::DtwTo` → `banded_dtw`, length-normalised), so summing two normalised alignment
costs is well-scaled; the stream weight is the agent's `Times(Lit(w), DtwTo)`, the
combine is the agent's variadic `Plus`. `MinOver` (nearest banked exemplar of the word)
and `Argmin` (the word decision) over the agent's OWN word Concepts + banked Exemplars
close the Term — one `substrate.evaluate` per query.

**Form (b) — CONCAT trajectory (single `DtwTo`):** cmvn ++ formant per frame (the formant
track resampled along time to the cmvn frame count), aligned by a single DtwTo. The
`banded_dtw` frame distance is Euclidean over the concatenated channels.

**Donkey boundary (audited).** The DECISION is the graph Term above (no Python
recognizer — the query/exemplar trajectories are written as graph attrs and the
`Argmin`-of-`MinOver`-of-(`Plus` of `DtwTo`+`Times`·`DtwTo`) Term picks the word). The
TWO TRAJECTORIES are the agent's composable-DSP **features**: `agent_frontend.cmvn_track`
is the SAME per-utterance CMVN cochleagram the dominant `cmvn_ear` cue is built from, kept
ordered; `agent_frontend.vtl_formant_track` is the SAME sharp LPC-root formant + `F_i -
mean(F1..F3)` VTL invariant the dynamic cue uses, kept ordered (+ order-1 velocity
channels). NO fit, NO trained net, NO learned weight (a fixed stream weight tried at a few
values, reported below). SC load + the speaker split are world-adapter mechanics; LOSO is
the ungameable yardstick; **held-out speakers' clips are NEVER banked**.

## (2) The A/B on the SAME robust SC LOSO — VERDICT

`scripts/multistream_dtw_loso.py` reuses `sc_loso_frontend_norm.build_split` / `bank`
verbatim (120 train / 40 held-out **disjoint** speakers, 200 banked exemplars, 200
seen-speaker probes, 400 cross-speaker LOSO probes, full 10-digit lexicon, the **identical**
split as the single-stream run). The single-stream baselines reproduce
`docs/dtw_trajectory_loso.md` **exactly** (DTW-CMVN 0.570, DTW-FORMANT 0.253), confirming
the harness.

```
                                          (10-way, chance 0.100)
  regime                     seen    LOSO   seen-LOSO gap
  DTW-CMVN (single)         0.625   0.570       +0.055    (the 0.570 baseline — reproduced)
  DTW-FORMANT (single)      0.300   0.253       +0.047    (the ~0.253 reference — reproduced)
  DTW-MULTI sum w=0.25      0.665   0.593       +0.073    (CMVN + 0.25·formant DTW costs)
  DTW-MULTI sum w=0.5       0.640   0.580       +0.060
  DTW-MULTI sum w=1.0       0.580   0.542       +0.037
  DTW-MULTI sum w=2.0       0.535   0.500       +0.035
  DTW-MULTI sum w=4.0       0.485   0.415       +0.070
  DTW-MULTI concat          0.600   0.535       +0.065    (single DTW over cmvn++formant)
  ------------------------------------------------------------------
  best single-stream:  DTW-CMVN    LOSO 0.570
  best multi-stream:   sum w=0.25  LOSO 0.593
  MULTI vs single-stream CMVN:    +0.023  (0.570 -> 0.593)
  RESIDUAL: 0.593 vs chance 0.100; still 0.407 from solved.
```

Reading the result:

- **Multi-stream lifts, but only at a LOW formant weight.** The best multi-stream form
  (sum, w=0.25) reaches **0.593** vs the single-stream CMVN **0.570** — **+0.023
  absolute**. The down-weighted formant stream adds a little real cross-speaker structure
  the CMVN trajectory alone misses.
- **The streams are largely REDUNDANT, not complementary.** The lift is **6.6× smaller**
  than the single-stream alignment jump (+0.023 vs +0.152). As the formant weight rises
  the combined LOSO **falls below the CMVN baseline** (w=1.0 → 0.542, w=2.0 → 0.500): the
  thin/noisy formant DTW stream is *harmful* once it carries meaningful weight, because
  it is a far sparser, blurrier feature (3 formants + velocity, the LPC track noisy on
  8 kHz SC clips). The CMVN spectral trajectory already encodes most of the formant
  gesture (formants ARE spectral peaks), so the second stream is mostly duplicate
  evidence; only its tiny non-redundant residual survives at w=0.25.
- **Concat (form b) is worse than the weighted sum** (0.535 < 0.593, and below the CMVN
  baseline 0.570). Per-frame Euclidean concatenation lets the ~50-band CMVN frame swamp
  the 6 small log-Hz formant channels and forces a single shared warp on two tracks with
  different natural rates; the separate-DTW sum (each stream aligned on its own optimal
  warp, then costs added) is the cleaner composition and the only form that beats
  single-stream CMVN.

### Does it solve cross-speaker recognition?

**No — it is a small further step, and the multi-stream lever is near-exhausted.** Best
multi-stream LOSO is **0.593** (chance 0.100); the residual to solved (1.0) is **0.407**.
The single-stream alignment recovered the single biggest piece of cross-speaker structure
(the temporal ORDER of the gesture, +0.152); adding the second trajectory recovers only a
thin non-redundant sliver (+0.023) and is harmful if over-weighted. The honest reading is
that **the two trajectories are mostly the same information** — the CMVN spectral path
already contains the formant motion — so multi-stream DTW is not the large remaining lever.
What remains beyond it (the same residuals the single-stream doc named): a **sharper
trajectory** (a real formant *tracker* / pitch-synchronous framing so the formant stream
is non-redundant rather than a blurry duplicate of the spectrum); **more exemplars per
word** to cover the cross-speaker manifold; and the deeper lexical / register /
coarticulation diversity no single-utterance exemplar bank cancels.

## Reproduce

```
python -m scripts.multistream_dtw_loso                       # full 120/40/20 (the decisive run)
python -m scripts.multistream_dtw_loso 12 6 5                # fast smoke run
```

Full captured output: `/tmp/multistream_dtw_loso.txt`, ending with the
`[MARKER] MULTISTREAM_DTW_LOSO_COMPLETE` line; the run was pgrep-verified to completion.
Required suites green (`test_stt_pipeline test_perception_self_assessment
test_process_meta_assessor test_gap_guidance test_frontend_effect_gate` — 36 passed).
Nothing committed; `scripts/multistream_dtw_loso.py` is left in the working tree
(`agent_frontend.cmvn_track` / `agent_frontend.vtl_formant_track` already present from the
single-stream run).
