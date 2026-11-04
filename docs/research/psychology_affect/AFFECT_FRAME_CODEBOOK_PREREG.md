# AFFECT FRAME + CODEBOOK — affect as log-quantised integer dimensions, decoded by the unchanged sd loop — PRE-REGISTRATION (block 369000)

**Status: PRE-REGISTRATION, written 4 November 2026 BEFORE the seed, builder or test
exists.** Every predicted value below is derived by hand from `seeds/core_emotions.json`,
the `LogQuantum` / `ShapeDecode` / `TransformDecode` semantics in
`runners/dsl/src/shape_decode.rs` and the `seeds/shape_decode_loop.json` rules, and is
reproduced by the pure-arithmetic oracle in Appendix A. None is read from a run of the
substrate. A deviation is reported as found.

## 0. Seed claim (verbatim, run at prereg time)

```
$ .venv/bin/python scripts/seed_claim.py 369000 369999
SEED CLAIM 369000-369999: CLEAN -- no collision DETECTED.
  Scope: 1373 files with seed sinks; 877 UNRESOLVED sink sites tree-wide (counted, not discarded).
  CAVEAT 1 -- THE UNIT IS THE SEED INTEGER, not consecutive draws from
    one generator. default_rng(S) burns an unbounded stream downstream of
    S; a rung seeding ONCE at its block base measures as ONE seed here.
  CAVEAT 2 -- THIS TOOL UNDER-REPORTS BY DESIGN (7 declared blind spots;
    unresolvable sinks are COUNTED, not discarded). A CLEAN RESULT MEANS
    'NO COLLISION DETECTED', NEVER 'NO COLLISION EXISTS'.
```

Deterministic; every sample set is a full enumeration. The block is claimed for hygiene.

## 1. Why, and what changes

Block 368000 ([results](AFFECT_DIRECTION_JUDGEMENT_RESULTS.md)) measured that the published
affect contract (`valence`, `arousal` on the `Appraisal`) cannot support within-category
valence direction (0/40), carries no loss magnitude in either channel, and that no rule
makes a direction judgement. The graded value (`value_progress`) is computed and kept on
the node, but it is outside the contract.

This rung represents affect **the way the substrate represents its other dimensions**:

- **Integer in-frame, log-weighted.** Each fired emotion publishes an integer *affect frame*
  of single-slot relations, as strokes publish pose (`pose_x`/`pose_o`). Magnitudes are
  turned into integer log₂ levels by the existing `LogQuantum` Term (base 2, Δ = 1, `raw`).
  The emotion seed already builds its magnitudes by shifting from a shared reference of 1024,
  so base 2 is their native grain and a ×2 change is a ±1 step.
- **Decoded against a held codebook by the unchanged sd loop.** The frame is an
  `Observation` that `seeds/shape_decode_loop.json` decodes against `ShapeSignature` parts.
  Exact frames are `recognized`; a frame that differs from its emotion's held shape only in
  level is `recognized_transformed`, a rung-1 `Transform{dims, deltas}` with no growth. This
  is the same intensity-invariant recognition the sd loop gives rotated strokes.
- **Direction as graph data.** A rule compares the frames of two successive appraisals and
  writes `val_direction` and `ar_direction` onto the later one.

**What does not change.** `seeds/core_emotions.json`, its builder, `valence`, `arousal`,
`emotion` and every existing reader stay byte-identical. The new seed is opt-in
(`self_load_only`, not registered in `domains/seed_registry.py`, loaded by nothing that
exists). No Rust. The `ModulatorState` → `AffectiveState` path, sadness's published arousal
and the mixed-event valence policy are untouched; §7 says what that leaves open.

## 2. Design (the implementation must match this; deviations are reported)

### 2.1 Files

- `scripts/build_affect_frame_seed.py`: seed builder (emits JSON; mechanical). Writes
  `seeds/affect_frame.json`.
- `seeds/affect_frame.json`: `id` `affect_frame`, `version` `0.1.0`,
  `depends_on` `["core_emotions", "shape_decode_loop"]`, `self_load_only` true.
- `tests/test_affect_frame_codebook.py`: the confirmatory test (§5).

### 2.2 Productions

- `Agent -has_emotion_hub-> EmotionHub`
- `Appraisal -has_affect_frame-> Observation`
- `Appraisal -follows-> Appraisal`

(`Agent -observed-> Observation` is already declared by `shape_decode_loop`.)

### 2.3 The affect frame

For emotion tag X, the frame's predicates are `aff:X:val_sign`, `aff:X:val_level` and
`aff:X:ar_level`. The emotion lives **in the predicate** because slot 0 is never
transformable and only a part with the same predicates can cover or transform-explain a
relation. A joy frame therefore cannot be explained as a substituted curiosity shape, and
no other emotion's part can cover a fragment of it.

| X (fires when) | `val_sign` | `val_level` | `ar_level` |
|---|---|---|---|
| joy (`hit_joy`=1) | 1 | LQ(`value_progress`) | LQ(`value_progress`) |
| sadness (`hit_sadness`=1) | −1 | LQ(\|`value_progress`\|) | LQ(`ep.low_arousal`) |
| curiosity (`hit_curiosity`=1) | 1 | LQ(`learning_progress`) | LQ(`learning_progress`) |
| fulfilment (`hit_fulfilment`=1) | 1 | LQ(\|`weighted_contribution`\|) | LQ(\|`weighted_contribution`\|) |
| fear, anxiety | −1 | absent | LQ(`threat_precision`) |
| surprise | 0 | absent | LQ(`residual`) |
| anger, frustration | −1 | absent | LQ(`ep.high_arousal`) |
| disgust | −1 | absent | LQ(`ep.mid_arousal`) |
| boredom | −1 | absent | LQ(`ep.low_arousal`) |
| `none` (`n_fired`=0, `appraised`=1) | 0 | absent | LQ(`ep.low_arousal`) |

LQ(x) = `LogQuantum` with `base_num` 2, `base_den` 1, `delta_num` 1, `delta_den` 1, `raw`
true, applied to the one-frame population `[[["x", x]]]` with `value_slot` 1. That is
round(log₂ x), and x ≤ 0 gives −30. Each `ar_level` source is the same signal
`em_readoff`'s arousal branch uses for that emotion, so for a single-emotion event the
frame's arousal is LQ(published `arousal`). "Absent" means the relation is not in the
signature and the `val_level` attr is not set.

**Emission rules.** One rule per tag (12), named `af_emit_<X>`:
- match `[["ag","has_emotion_hub","hub"],["hub","has_emotion_params","ep"],["hub","has_appraisal","ap"]]`;
- where `ep.enabled == 1`, the tag's firing condition from the table, and no existing
  `has_affect_frame` neighbour of `ap` with `aff_tag == X`;
- effects:
  - `add_node f Observation {status:"pending", signature:<frame>, key:["affect", X], aff_tag:X, val_sign, val_level (value-bearing tags only), ar_level}`;
  - `add_edge ap has_affect_frame f`;
  - `add_edge ag observed f`.

The rules are installed after `core_emotions`. `run_rules` walks rules in install order
(`rewrite.rs::run_rules`), so the frames read the converged appraisal. If that assumption
fails, it shows up in G-1 as wrong or extra frames.

**The codebook.** Twelve `ShapeSignature{name:"affect:<X>", kind:"affect", signature}`
nodes in the seed's `nodes`, one per tag. The builder produces them mechanically. It boots
the `core_emotions_measure` harness with this seed's rules, runs each `CANON` appraisal
from `scripts/core_emotions_measure.py` (plus a `none` appraisal, `appraised=1` only),
and copies each resulting frame's `signature` verbatim. So the codebook is the canonical
appraisals' own frames, not hand-typed levels.

**Direction rule `af_direction`.**
- match `[["ap2","follows","ap1"],["ap1","has_affect_frame","f1"],["ap2","has_affect_frame","f2"]]`;
- where each appraisal has exactly one frame (multi-frame mixed events are excluded);
- effects on `ap2`:
  - `val_direction` = sign(K₂ − K₁), with the signed log coordinate K = `val_sign`·(`val_level` + 1) when `val_level` is present, else `val_sign`;
  - `ar_direction` = sign(`ar_level`₂ − `ar_level`₁).

K is monotone in signed value for integer values: a value of 1 has level 0 and K = ±1,
which is distinct from neutral's 0.

## 3. Harness and samples

- **Boot:** `scripts/core_emotions_measure.py` `_eye()`, then
  `domains.reflective_faculty._ensure_shape_decode_loop(eye.substrate, inner, eye._agent)`
  (which defaults `codebook_epoch` to 0), then
  `inner.load_seed_manifest(manifest_for("affect_frame"), eye._agent)`.
- **One event:** a fresh `EmotionHub` from `_hub` with edge `agent -has_emotion_hub-> hub`
  (world data), then `_appraise`, then `run_rules()`.
- **One trial:** a fresh hub. Author event 1, `run_rules()`. Author event 2 plus the edge
  `ap2 -follows-> ap1` (temporal order is world data), `run_rules()`.
- **Events:** the 22 events of block 368000 §3, unchanged: gain/loss k = 0…4, neutral,
  threat k = 0…4, surprise r ∈ {150, 200, 400, 800, 1600}, and mixed.
- **Trials:** the valence arm's 121 ordered pairs and the arousal arm's 4 × 25 ordered
  within-family pairs, as in block 368000.
- **Truth columns:** unchanged from block 368000 (value change for valence; family
  intensity for arousal).

## 4. The analytic oracle (Appendix A reproduces every number)

**Codebook**, as (tag, val_sign, val_level, ar_level):
- surprise (0, —, 9)
- fear (−1, —, 7)
- anxiety (−1, —, 10)
- anger (−1, —, 10)
- frustration (−1, —, 10)
- disgust (−1, —, 9)
- joy (1, 9, 9)
- sadness (−1, 9, 6)
- curiosity (1, 7, 7)
- boredom (−1, —, 6)
- fulfilment (1, 8, 8)
- none (0, —, 6)

`fulfilment` uses `quantize_weight(1.0)` = (1024, 10), so `weighted_contribution` = 300.

**Isolated frames and decodes**, written as frame → status, with deltas as observed − held:

| event | frame (val_sign, val_level, ar_level) | decode |
|---|---|---|
| gain k=0..4 | joy (1, 9−k, 9−k) | k=0 recognized; else transformed, val_level −k, ar_level −k |
| loss k=0..4 | sadness (−1, 9−k, 6) | k=0 recognized; else transformed, val_level −k |
| neutral | none (0, —, 6) | recognized |
| threat k=0,1,2 | anxiety (−1, —, 10−k) | k=0 recognized; else transformed, ar_level −k |
| threat k=3,4 | fear (−1, —, 10−k) | k=3 recognized; k=4 transformed, ar_level −1 |
| surprise 150, 200, 400, 800, 1600 | surprise (0, —, 7, 8, 9, 10, 11) | ar_level −2, −1, recognized, +1, +2 |
| mixed | two frames: joy (1, 9, 9) and fear (−1, —, 7) | both recognized |

- 23 frames in total: 8 recognized exactly, 15 recognized_transformed.
- The base of every decode is the event's own `affect:<X>`.
- **0 `CapabilityAxis` minted.**

**Directions:**
- Valence: **121/121**, within-category **40/40**. Under block 368000 these were 81/121 and
  0/40.
- Arousal: threat **25/25**, surprise **25/25**, gain **25/25**, loss **5/25**. Loss is
  unchanged from block 368000 by design, because published sadness arousal is untouched;
  loss magnitude is now carried by `val_level`.

## 5. Pre-registered gates

| gate | prediction | fails if |
|---|---|---|
| **G-0** default preserved | `seeds/core_emotions.json`, `scripts/build_core_emotions_seed.py` and `runners/` unchanged versus the start commit; `tests/test_core_emotions_migrated.py`, `tests/test_affect_direction_judgement.py` and `tests/test_affect_map_reuse_gridcode.py` pass; the seed-inventory tests listed in §8 have the same node-id outcome as on the start commit | any change or any new red |
| **G-1** codebook and frames | the seed's 12 codebook signatures equal §4; each of the 22 isolated events emits exactly the §4 frames (1 each, 2 for mixed) with exact relations and attrs | any difference, including a spurious `none` frame |
| **G-2** recognition | each of the 23 frames reaches the §4 status with base `affect:<own tag>` and exactly the §4 per-predicate deltas; 0 `CapabilityAxis` created | any difference or any mint |
| **G-3** valence direction | `af_direction` gives 121/121, within 40/40 | any count differs |
| **G-4** arousal direction | threat 25, surprise 25, gain 25, loss 5 (of 25) | any count differs |
| **G-5** old contract unchanged with the seed loaded | every event's `valence`, `arousal`, `emotion`, `n_fired` equal the block 368000 oracle; read-offs are context-free in all 221 trials | any difference |

**Exploratory (no thresholds):**
- **X-1 mixed event:** report the frames, their decode statuses and that `af_direction`
  skips it.
- **X-2 cost:** report wall time and the number of `Observation` nodes decoded.

## 6. What each outcome means

| outcome | reading |
|---|---|
| all pass | Representing affect like the substrate's other dimensions (an integer log-level frame, decoded by the unchanged sd loop against a held codebook) gives intensity-invariant emotion recognition (rung-1 transforms, no growth), full valence direction including within category and including losses, and a graph-resident direction judgement, with the old contract byte-identical. That is the basis for a later rung to move readers (bigville's `ModulatorState` sync, the PSI projection) onto the frame. This rung does not move them. |
| G-1 fails | The emission is not what §2.3 states. Localise first (for example frames emitted before the appraisal converged). |
| G-2 fails with a different base or a mint | The sd loop's candidate selection is not what §2.3 assumes (for example a non-affect `ShapeSignature` competing, or a Str/Surface predicate mismatch between rule-built frames and JSON-loaded parts). This is a finding about reusing the sd loop and becomes the headline. |
| G-3 or G-4 differ | The direction rule or the log quantisation is not what §2.3 states. Localise. |
| G-0 or G-5 fails | The opt-in seed is not isolated. This is a blocker: revert before anything else. |

## 7. Known gaps stated in advance

- **Readers are not moved.** Nothing consumes the frame or the directions yet.
  `AffectiveState` is unchanged.
- **The mixed-event valence policy is not decided.** The frame decomposes a mixed event
  into one frame per emotion, which avoids hand-setting a single valence. But the published
  `valence` still reads +1 under a fear label, and `af_direction` skips multi-frame events.
- **The codebook comes from canonical exemplars, not experience.** Minting affect shapes
  from a stream of events is a later rung.
- **Fear, anger, frustration, disgust and boredom have no `val_level`**, because their
  inputs carry no value magnitude. K falls back to the sign for them, so, for example, fear
  versus anger is "same" in valence. That case is not in this sample.
- **Log₂ rounding merges values within a factor of about √2.** Surprise residuals 150 and
  200 are not in the same bin here (7 and 8), but nearby values can be. Finer resolution
  belongs in refinement, not a finer base (the project's MDL rule).
- **Sadness's published arousal stays 50.** The arousal arm's loss row is therefore still
  5/25.
- **Synthetic events, declared truth columns, harness defaults only** (as in block 368000).

## 8. Files, commands, isolation

- The implementation runs in its own worktree. Start commit = the commit of this file.
- Test: `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_affect_frame_codebook.py -q -p no:cacheprovider`
- Seed-inventory tests for G-0, compared by node id against the start commit:
  - `tests/test_codebook_partition_migrated.py`
  - `tests/test_argmin_unique_migrated.py`
  - `tests/test_ast_attr_migrated.py`
  - `tests/test_rule_signature_program_migrated.py`
  - `tests/test_refusal_representable_migrated.py`
  - `tests/test_instrument_seams_migrated.py`
  - `tests/test_report_seed_boot_status.py`
- Measurements: `results/affect_frame_codebook.json`.
- Results: `docs/research/psychology_affect/AFFECT_FRAME_CODEBOOK_RESULTS.md`.

## 9. Discipline

- No constant or design element in §2–§3 changes after the run without a new prereg.
- Nulls are headline findings.
- This rung measures a synthetic mechanism. None of it measures a person.

## Appendix A — oracle (pure arithmetic; reproduces every number in §4)

```python
import math
LOW, MID, HIGH = 50, 400, 800
def lq(x):  # LogQuantum base 2, delta 1, raw: round(log2 x); x <= 0 -> round(log2 1e-9)
    return math.floor((math.log(x) if x > 0 else math.log(1e-9)) / math.log(2) + 0.5)
def sgn(x): return (x > 0) - (x < 0)
def frame(t, vp=0, lp=0, wc=0, tp=0, r=0):
    return {"joy": (t, 1, lq(vp), lq(vp)), "sadness": (t, -1, lq(abs(vp)), lq(LOW)),
            "curiosity": (t, 1, lq(lp), lq(lp)), "fulfilment": (t, 1, lq(abs(wc)), lq(abs(wc))),
            "fear": (t, -1, None, lq(tp)), "anxiety": (t, -1, None, lq(tp)),
            "surprise": (t, 0, None, lq(r)), "anger": (t, -1, None, lq(HIGH)),
            "frustration": (t, -1, None, lq(HIGH)), "disgust": (t, -1, None, lq(MID)),
            "boredom": (t, -1, None, lq(LOW)), "none": (t, 0, None, lq(LOW))}[t]
CB = {t: frame(t, **kw) for t, kw in {
    "surprise": dict(r=500), "fear": dict(tp=1024 >> 3), "anxiety": dict(tp=1024),
    "anger": {}, "frustration": {}, "disgust": {}, "joy": dict(vp=512 - 64),
    "sadness": dict(vp=64 - 512), "curiosity": dict(lp=180), "boredom": {},
    "fulfilment": dict(wc=(1024 * 300) >> 10), "none": {}}.items()}
def ev(kind, k):
    if kind == "gain": return [frame("joy", vp=(1024 >> k) - (1024 >> (k + 1)))]
    if kind == "loss": return [frame("sadness", vp=(1024 >> (k + 1)) - (1024 >> k))]
    if kind == "neutral": return [frame("none")]
    if kind == "threat": p = 1024 >> k; return [frame("anxiety" if p >= 256 else "fear", tp=p)]
    if kind == "surprise": return [frame("surprise", r=k)]
    return [frame("joy", vp=448), frame("fear", tp=128)]           # mixed
def decode(f):
    t, s, L, A = f; h = CB[t]; d = {}
    if L is not None and L != h[2]: d["val_level"] = L - h[2]
    if A != h[3]: d["ar_level"] = A - h[3]
    return ("recognized" if not d else "recognized_transformed", "affect:" + t, d)
K = lambda f: f[1] * (f[2] + 1) if f[2] is not None else f[1]
tv = lambda kind, k: ((1024 >> k) - (1024 >> (k + 1)) if kind == "gain" else
                      (1024 >> (k + 1)) - (1024 >> k) if kind == "loss" else 0)
it = lambda kind, k: 1024 >> k if kind == "threat" else k if kind == "surprise" else abs(tv(kind, k))
E = ([("gain", k) for k in range(5)] + [("loss", k) for k in range(5)] + [("neutral", 0)] +
     [("threat", k) for k in range(5)] + [("surprise", r) for r in (150, 200, 400, 800, 1600)] + [("mixed", 0)])
fr = [f for e in E for f in ev(*e)]
print(len(fr), sum(decode(f)[0] == "recognized" for f in fr))                 # 23 8
V = [("loss", k) for k in range(5)] + [("neutral", 0)] + [("gain", k) for k in range(5)]
P = [(a, b) for a in V for b in V]
ok = lambda a, b: sgn(K(ev(*b)[0]) - K(ev(*a)[0])) == sgn(tv(*b) - tv(*a))
W = [(a, b) for a, b in P if a != b and a[0] == b[0] and a[0] in ("gain", "loss")]
print(sum(ok(a, b) for a, b in P), sum(ok(a, b) for a, b in W))              # 121 40
for fam, ks in {"threat": range(5), "surprise": [150, 200, 400, 800, 1600],
                "gain": range(5), "loss": range(5)}.items():
    print(fam, sum(sgn(ev(fam, b)[0][3] - ev(fam, a)[0][3]) == sgn(it(fam, b) - it(fam, a))
                   for a in ks for b in ks))                                  # 25 25 25 5
```
