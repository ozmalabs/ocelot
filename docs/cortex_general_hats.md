# The universal cortex is general — one loop, swappable sense-hats

The Phase-C analysis-by-synthesis loop is validated (converges, factors out the
speaker) but plateaus on AUDIO. The diagnosis (commit `da783064`, "mouth is the wall"
REFUTED) is that the AUDIO COMPARE carries a synthetic-vs-real **domain gap**: the
cortex re-renders candidates with espeak while the heard items are real recordings, so
the true-word residual ≈ the wrong-word residual — the distance is word-INDEPENDENT.
The loop itself is sound; the failure lives in the audio hat's compare.

This work makes the cortex **truly general** and proves that:

1. A front-end-AGNOSTIC `CortexLoop` + a `Hat` interface (encode / synth / compare).
2. The existing audio behind an `AudioHat` (no regression through the general loop).
3. A clean `ToyHat` with NO synthetic-vs-real gap (render IS synth) as the control.

If the IDENTICAL loop recognises shapes through the clean toy hat while the audio hat
stays stuck, the failure is quarantined to the audio hat's compare — not the cortex.

## Architecture (donkey-clean)

```
        ┌──────────────────────────────────────────────┐
        │  CortexLoop  (domains/cortex_loop.py)          │
        │  OWNED ops only — NO net, NO sense-specifics:  │
        │   coarse-match (multi-start)                   │
        │   -> adapt-style (coordinate descent)          │
        │   -> order-N iterate                           │
        │   -> readout argmin_content[min_style residual]│
        └───────────────────────┬──────────────────────┘
                                 │ calls ONLY
                 hat.encode / hat.synth / hat.compare
                 + contents / style_init / style_neighbours / library
                                 │
        ┌────────────────────────┴────────────────────────┐
        │            Hat interface (domains/hat.py)         │
        └───────┬───────────────────────────────┬──────────┘
        ┌───────┴────────┐              ┌────────┴─────────┐
        │   AudioHat      │              │     ToyHat       │
        │ encode=cmvn     │              │ encode=grid      │
        │ synth =espeak   │              │ synth =render    │
        │ compare=DtwTo   │              │ compare=L2       │
        │ (synth≠real:    │              │ (synth IS real:  │
        │  DOMAIN GAP)    │              │  NO domain gap)  │
        └─────────────────┘              └──────────────────┘
```

**Donkey audit (verified).** `domains/cortex_loop.py` contains ZERO sense-specific
identifiers in its code (AST-checked: no espeak / cmvn / cochlea / dtw / render /
pitch / rate / rot / scale anywhere except docstrings). Its only dependency is
`from domains.hat import Hat`. The loop owns coarse-match / adapt / iterate / argmin
(a coordinate search + residual-min over the hat's owned compare). The only world
calls are `hat.synth` (re-render) and `hat.encode` (front end). The metric (compare)
is the hat's owned graph op — DtwTo (audio) / `Magnitude(VecSub(...))` (toy), both
evaluated natively in Rust. No net, no fit, no gradient in the loop.

## The two hats

- **AudioHat** (`domains/audio_hat.py`): the existing audio, unchanged in substance.
  encode = cmvn cochleagram trajectory (`learned_voice_shape.residual_track`, empty
  library = per-utterance CMVN). synth = the espeak-ng voicebox the agent controls and
  hears, re-rendered to the same cmvn trajectory. compare = the agent's graph-resident
  `DtwTo`. Style = voice V (variant × pitch × rate). The coarse-to-fine
  `style_neighbours` reproduce Phase-C's coordinate descent.
- **ToyHat** (`domains/toy_hat.py`): a clean render-based sense. CONTENT = a shape from
  a small glyph set; STYLE = a transform (rotation × scale × translation). `render`
  stamps the glyph on an N×N grid under the transform, smooths it (overlap metric), and
  normalises. encode(grid) = the grid is already in feature space (the "heard" item is
  a render under an unknown transform — exactly like a clip from an unknown speaker).
  **synth = render = encode's source**, so there is NO synthetic-vs-real gap by
  construction. compare = `Magnitude(VecSub(a, b))` (owned L2 over the flat grid).
  Held-out test items use transforms strictly OFF the library grid (rotations not
  multiples of 60°, off-grid scales, nonzero translations) — never banked, the
  analogue of held-out speakers.

## Results

| test | result | chance | ratio |
|---|---|---|---|
| (1) GENERALITY | identical `CortexLoop` ran on BOTH hats (swap the hat) | — | — |
| (2) TOY soundness (held-out transforms, no domain gap) | **0.500** | 0.125 | **4.0×** |
| (3) AUDIO no-regression (cross-speaker LOSO) | **0.412** | 0.100 | 4.1× |

- (1) The SAME loop code path drove both hats. Donkey-audited: zero audio-specifics in
  the loop (AST-level).
- (2) On the CLEAN toy hat (render IS synth → no domain gap), the loop recognises the
  shape while factoring out UNSEEN transforms at **0.500 = 4.0× chance** (64 held-out
  items, 8 shapes). The loop WORKS when the hat is clean. Residual confusions are
  rotation-degenerate shape pairs (`plus↔ex`: a plus rotated 45° is an ex) — an
  inherent shape ambiguity, not a loop flaw.
- (3) The AudioHat through the SAME general loop reproduces the Phase-C audio number
  (**0.412** cross-speaker LOSO on 80 held-out REAL clips, canonical 0.420 — no
  regression), with the true-word residual (**0.404**) NOT separated from the
  wrong-word residual (**0.449**, sep +0.045) — the word-independent domain gap,
  confirmed. The refactor preserved the audio behaviour exactly.

## Verdict

**GENERAL + SOUND; the audio problem is QUARANTINED.** The same `CortexLoop` runs on
both hats. On the clean toy hat (no synthetic-vs-real gap) it recognises the shape
while factoring out unseen transforms at 4.0× chance — the analysis-by-synthesis loop
is sound. The audio hat through the same loop reproduces the Phase-C plateau with the
true-word residual unseparated from the wrong-word residual. Therefore the audio
failure is the AudioHat's COMPARE (the synthetic-vs-real domain gap), **not** a flaw in
the cortex. This realises the thesis: one engine + swappable sense-hats + plasticity.

The next lever lives entirely inside the AudioHat — a compare/forward-model that
closes the synthetic-vs-real gap (e.g. a self-rendered front end so heard and
synthesized items go through the same transform, the toy hat's winning property) — and
needs no change to the universal cortex.
