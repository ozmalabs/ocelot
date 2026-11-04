# AFFECT FRAME v0.2 — mixed events, an experience-grown codebook, and a reader on AffectiveState — PRE-REGISTRATION (block 370000)

**Status: PRE-REGISTRATION, written 5 November 2026 BEFORE any v0.2 code exists.** It
closes the open items of block 369000 ([results](AFFECT_FRAME_CODEBOOK_RESULTS.md)). Every
prediction comes from the block 369000 seed, `seeds/shape_decode_loop.json`, and the
oracle in Appendix A. The design was informed by one feasibility probe, declared in §1.4.

## 0. Seed claim (verbatim, run at prereg time)

```
$ .venv/bin/python scripts/seed_claim.py 370000 370999
SEED CLAIM 370000-370999: CLEAN -- no collision DETECTED.
  Scope: 1373 files with seed sinks; 877 UNRESOLVED sink sites tree-wide (counted, not discarded).
  CAVEAT 1 -- THE UNIT IS THE SEED INTEGER, not consecutive draws from
    one generator. default_rng(S) burns an unbounded stream downstream of
    S; a rung seeding ONCE at its block base measures as ONE seed here.
  CAVEAT 2 -- THIS TOOL UNDER-REPORTS BY DESIGN (7 declared blind spots;
    unresolvable sinks are COUNTED, not discarded). A CLEAN RESULT MEANS
    'NO COLLISION DETECTED', NEVER 'NO COLLISION EXISTS'.
```

Deterministic; full enumerations only.

## 1. The open items and what this rung does with each

### 1.1 Mixed events had no valence policy → per-component directions

A mixed event (gain plus threat) emits one frame per fired emotion. `af_direction` skips
any appraisal with more than one frame, so a mixed event got no direction at all. Rather
than hand-set one valence for a mixture, this rung compares **like with like**. A new rule,
`af_component_direction`, writes a `ComponentDirection{tag, val_direction, ar_direction}`
for every emotion tag the two successive appraisals share. A mixed event then gets a
direction for each of its components that the previous event also had. The published
`valence` (+1 under a fear label) is untouched and stays an old-contract issue for its own
readers.

### 1.2 The codebook came from canonical exemplars → it can now grow from experience

The block 369000 seed is split into two seeds:
- `affect_frame` (v0.2.0): the rules only.
- `affect_frame_canonical` (v0.1.0): the 12 canonical codebook nodes, byte-identical to
  block 369000's, with `depends_on: ["affect_frame"]`.

A new rule, `af_grow_codebook`, adds a `ShapeSignature{name:"affect:<tag>", kind:"affect",
signature:<the frame's signature>}` when an affect frame was minted (no held shape
explained it) and no shape of that name exists, and increments `ag.codebook_epoch`. This
is the graph-native form of `grow_part_library`. `sd_redecode` then re-arms the
observations and the frame is recognised against its own new shape.
- With `affect_frame_canonical` loaded, nothing mints, so the growth rule never fires.
- Without it, the first experienced frame of each emotion becomes that emotion's held shape.

### 1.3 Nothing read the frame → a projection onto the canonical AffectiveState

`affective_state_core` already declares `EmotionHub -has_affective_state-> AffectiveState`.
A new rule, `af_project_affective_state`, writes the frames of the hub's **latest**
appraisal (the one with no incoming `follows` edge) onto that AffectiveState as new,
additive attrs:
- `frame_components`: a list of `[tag, val_sign, val_level, ar_level]`, one per frame;
- `frame_count`;
- `frame_key`: the signed log coordinate K when there is exactly one frame, else null.

Existing AffectiveState attrs (`valence`, `arousal`, …) are not written. Moving bigville or
PSI readers onto these attrs remains a separate decision, because it changes behaviour in
those worlds.

### 1.4 Sadness's published arousal was flat → closed as not a defect

Block 368000 declared loss *intensity* as the arousal truth for losses. That was a
mis-specification. In the valence–arousal circumplex (Russell 1980) sadness is a
low-arousal, negative-valence state. A larger loss makes valence more negative; it does not
make the state more aroused. `core_emotions` gives sadness `low_arousal` on purpose, and the
graded loss magnitude now lives in `aff:sadness:val_level` (block 369000, 40/40). So the
loss row's 5/25 is the correct outcome of a correct design, not a gap. **No change.** This
corrects the reading of block 368000's G-4 loss row; its numbers stand.

**Feasibility probe (declared, before this prereg).** One gain event on the block 369000
rules with the codebook removed reached `status: minted`, with one `CapabilityAxis`
(`capability_keys` ("affect","joy"), `minted_from_signature` = the frame). That confirms
the mint path that §1.2's growth rule hangs off. No gated number below was read from it.

### 1.5 A separate finding, out of scope here

`sd_recognize`'s `covered_by` ties to an unrelated part for codebook parts whose
`signature` is a JSON string. This was confirmed by a probe on `boot_core`: an exact match
against a JSON-string part named `zz_part_B` reported `fractal`, and the native-list form
reported `zz_part_B`. It is a `shape_decode_loop` issue, not an affect issue, and gets its
own rung. Code reading predicts a second sd-loop issue that this rung exercises (§4.2):
an observation that was `recognized_transformed` and is then re-armed by `sd_redecode`
cannot return to `recognized_transformed`. Its `has_transform` edge already exists and
blocks `sd_recognize_transformed`'s re-mint guard, so it stays `decoded` with
`transform_explained` = 1.

## 2. Design (the implementation must match; deviations are reported)

Builder `scripts/build_affect_frame_seed.py` (extended) emits both seeds.

**`seeds/affect_frame.json` v0.2.0.**
- The block 369000 rules (`af_emit_*` ×12, `af_direction`) are byte-identical.
- New rules:
  - `af_component_direction`
    - match `[["ap2","follows","ap1"],["ap1","has_affect_frame","f1"],["ap2","has_affect_frame","f2"]]`
    - where `f1.aff_tag == f2.aff_tag` and `ap2` has no `has_component_direction`
      neighbour with that `tag`
    - effects: `add_node cd ComponentDirection{tag, val_direction: sign(K(f2)−K(f1)), ar_direction: sign(ar_level₂−ar_level₁)}`, then `add_edge ap2 has_component_direction cd`
  - `af_grow_codebook`
    - match `[["ag","observed","obs"],["obs","minted","axis"]]`
    - where `IndexAt(obs.key, 0) == "affect"` and no `ShapeSignature` has
      `name == StringConcat("affect:", obs.aff_tag)`
    - effects: `add_node sig ShapeSignature{name: StringConcat("affect:", obs.aff_tag), kind:"affect", signature: Attr(obs,"signature")}`, then `set_attr ag codebook_epoch = codebook_epoch + 1`
  - `af_project_affective_state`
    - match `[["hub","has_affective_state","affect"],["hub","has_appraisal","ap"]]`
    - where `Count(InNeighbours(ap,"follows")) == 0` and `Count(Neighbours(ap,"has_affect_frame")) ≥ 1`
    - effects:
      - `affect.frame_components = MapList(Neighbours(ap,"has_affect_frame"), f, Vec(f.aff_tag, f.val_sign, f.val_level, f.ar_level))`
      - `affect.frame_count = Count(...)`
      - `affect.frame_key = Ite(count == 1, K(only frame), null)`
- New productions:
  - `Appraisal -has_component_direction-> ComponentDirection`
  - `Agent -observed-> Observation` (re-declared harmlessly, if the loader requires it)
  - Note: `EmotionHub -has_affective_state-> AffectiveState` is already in `affective_state_core`.
- `depends_on: ["core_emotions","shape_decode_loop"]` and `self_load_only` are unchanged.

**`seeds/affect_frame_canonical.json` v0.1.0.** The 12 codebook nodes copied verbatim from
the block 369000 `affect_frame.json` (native-list signatures), with
`depends_on: ["affect_frame"]` and `self_load_only: true`. No rules.

**Block 369000's test.** `tests/test_affect_frame_codebook.py` must load both seeds,
`affect_frame` then `affect_frame_canonical`. Before and after the split, it must produce
identical gate payloads in `results/affect_frame_codebook.json` (all sections except
`header`/`timing`). That is the semantics-preserving check for editing a committed test
(VISION_PROTOCOL §12.3). Its G-1 codebook reader reads `affect_frame_canonical.json`.

## 3. Harness and samples

- **Boot:** as in block 369000 (`core_emotions_measure._eye`, `_ensure_shape_decode_loop`,
  load `affect_frame`). For each arm:
  - **A** also loads `affect_frame_canonical`.
  - **B** loads only `affect_frame`.
  - **C** also loads `affect_frame_canonical` and `affective_state_core`, then adds the edge
    `hub -has_affective_state-> <agent's AffectiveState>` (boot data).
- **Events:** the 22 events of block 368000/369000, in the fixed order E =
  loss 0–4, neutral, gain 0–4, threat 0–4, surprise 150/200/400/800/1600, mixed.
- **Arm A, components:**
  - the 221 single-frame trials of block 369000;
  - 43 mixed trials: mixed→s and s→mixed for each of the 21 single events s, plus
    mixed→mixed.
  - Each trial uses a fresh hub; event 2 gets `follows` → event 1.
- **Arm B, growth:** one stream. Each event of E on a fresh hub in the same agent, with
  `run_rules()` after each.
- **Arm C, projection:** one hub. E in order, each event `follows` the previous, with
  `run_rules()` after each. Read the AffectiveState after each event.

## 4. Predictions (Appendix A reproduces every number)

**4.1 Arm A — components.**
- In the 221 single-frame trials, a `ComponentDirection` exists exactly in the **139**
  trials whose two frames share a tag. In each it equals that trial's `af_direction`
  values. The other 82 have none.
- In the 43 mixed trials, components exist in **15** trials (16 components), as follows:
  - mixed→gain k: joy (0,0) for k=0, else (−1,−1).
  - gain k→mixed: joy (0,0) for k=0, else (1,1).
  - mixed→threat 3: fear (0,0). threat 3→mixed: fear (0,0).
  - mixed→threat 4: fear (0,−1). threat 4→mixed: fear (0,1).
  - mixed→mixed: fear (0,0) and joy (0,0).
  - Every other mixed trial has none.
- `af_direction` stays unset in all 43 mixed trials.

**4.2 Arm B — experience-grown codebook.**
- **6** shapes grown, in this order: sadness (−1, 9, 6), none (0, —, 6), joy (1, 9, 9),
  anxiety (−1, —, 10), fear (−1, —, 7), surprise (0, —, 7).
- **6** `CapabilityAxis` minted. Final `codebook_epoch` = **6**.
- Final statuses of the 23 frames:
  - **8 `recognized`:** loss 0, neutral, gain 0, threat 0, threat 3, surprise 150, mixed joy, mixed fear.
  - **4 `recognized_transformed`:** surprise 200/400/800/1600, with `ar_level` +1/+2/+3/+4
    relative to the first experienced surprise.
  - **11 `decoded` with `transform_explained` = 1 and one `has_transform` each:** loss 1–4,
    gain 1–4, threat 1, 2 and 4. This is the predicted re-arm defect of §1.5. Each keeps its
    run-time Transform deltas: loss val_level −k; gain val_level −k and ar_level −k;
    threat 1/2 ar_level −1/−2; threat 4 ar_level −1.

**4.3 Arm C — projection.** After each event of E, the AffectiveState holds exactly that
event's frames:
- `frame_count` 1, with `frame_key` = K;
- the mixed event: `frame_count` 2 with components fear (−1, —, 7) and joy (1, 9, 9),
  compared order-insensitively, with the emitted order recorded, and `frame_key` null.

K along E is: −10, −9, −8, −7, −6, 0, 10, 9, 8, 7, 6, −1 (×5), 0 (×5), then null.
The AffectiveState's `valence`, `arousal` and `baseline` are unchanged from their seeded
values (0.0, 0.0, 1.0) throughout.

## 5. Gates

| gate | prediction | fails if |
|---|---|---|
| **G-0** isolation | `core_emotions.json`, its builder and `runners/` unchanged versus the start commit; the block 369000 test passes after the split with identical gate payloads; `tests/test_core_emotions_migrated.py`, `tests/test_affect_direction_judgement.py` and `tests/test_affect_map_reuse_gridcode.py` pass | any change or difference |
| **G-1** components, single-frame | 139 trials with exactly one component equal to `af_direction`; 82 with none | any difference |
| **G-2** components, mixed | §4.1's 15 trials and 16 components; `af_direction` unset in all 43 | any difference |
| **G-3** growth | §4.2's 6 shapes (order, signatures), 6 axes, epoch 6, and the 8/4/11 status split with the stated deltas | any difference. If the 11 come out `recognized_transformed`, the §1.5 defect prediction was wrong; report it, do not count it as a pass |
| **G-4** projection | §4.3 after every one of the 22 events; old AffectiveState attrs unchanged | any difference |
| **G-5** block 369000 re-run | 8/8 with the split seeds | any failure |

Sadness arousal (§1.4) has no gate, because nothing changes.

## 6. Reading

- **All pass:** a mixed event is handled per component without a hand-set valence policy.
  The affect codebook can be grown from experience by the same mint/grow/re-decode loop the
  sd loop uses elsewhere. The canonical AffectiveState carries the graded frame for future
  readers, while its old contract stays unchanged. The two sd-loop findings (§1.5) go to
  their own rung.
- **G-3's 11 not `decoded`:** the re-arm defect does not exist as read. Report it as a
  correction to §1.5.
- **G-0/G-5 fail:** the split is not semantics-preserving. Revert before anything else.

## 7. Gaps stated in advance

- **Readers outside the substrate core are not moved.** Bigville and PSI still use the old
  contract. `frame_*` on AffectiveState has no consumer yet.
- **Growth order matters.** The first experienced exemplar defines each held shape, so
  later levels are read relative to it.
- **Each grown emotion costs one CapabilityAxis.**
- **The §1.5 defects are not fixed here.**
- **Synthetic events, harness defaults.** Nothing measures a person.

## 8. Files and commands

- New/changed:
  - `scripts/build_affect_frame_seed.py`
  - `seeds/affect_frame.json`
  - `seeds/affect_frame_canonical.json` (new)
  - `tests/test_affect_frame_codebook.py` (harness load only)
  - `tests/test_affect_frame_v02.py` (new)
- Run: `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_affect_frame_v02.py tests/test_affect_frame_codebook.py -q -p no:cacheprovider`
- Results: `docs/research/psychology_affect/AFFECT_FRAME_V02_RESULTS.md`
- Start commit: the commit of this file.

## Appendix A — oracle (pure arithmetic)

```python
import math
LOW = 50
def lq(x): return math.floor((math.log(x) if x > 0 else math.log(1e-9)) / math.log(2) + 0.5)
def sgn(x): return (x > 0) - (x < 0)
def frame(t, vp=0, tp=0, r=0):
    return {"joy": (t, 1, lq(vp), lq(vp)), "sadness": (t, -1, lq(abs(vp)), lq(LOW)),
            "fear": (t, -1, None, lq(tp)), "anxiety": (t, -1, None, lq(tp)),
            "surprise": (t, 0, None, lq(r)), "none": (t, 0, None, lq(LOW))}[t]
def ev(kind, k):
    if kind == "gain": return [frame("joy", vp=(1024 >> k) - (1024 >> (k + 1)))]
    if kind == "loss": return [frame("sadness", vp=(1024 >> (k + 1)) - (1024 >> k))]
    if kind == "neutral": return [frame("none")]
    if kind == "threat": p = 1024 >> k; return [frame("anxiety" if p >= 256 else "fear", tp=p)]
    if kind == "surprise": return [frame("surprise", r=k)]
    return [frame("fear", tp=128), frame("joy", vp=448)]          # mixed, emission order
K = lambda f: f[1] * (f[2] + 1) if f[2] is not None else f[1]
E = ([("loss", k) for k in range(5)] + [("neutral", 0)] + [("gain", k) for k in range(5)] +
     [("threat", k) for k in range(5)] + [("surprise", r) for r in (150, 200, 400, 800, 1600)] + [("mixed", 0)])
# 4.1 components
def comp(a, b):
    fa, fb = {f[0]: f for f in ev(*a)}, {f[0]: f for f in ev(*b)}
    return {t: (sgn(K(fb[t]) - K(fa[t])), sgn(fb[t][3] - fa[t][3])) for t in fa if t in fb}
V = [("loss", k) for k in range(5)] + [("neutral", 0)] + [("gain", k) for k in range(5)]
fam = {"threat": range(5), "surprise": [150, 200, 400, 800, 1600], "gain": range(5), "loss": range(5)}
single = [(a, b) for a in V for b in V] + [((f, x), (f, y)) for f, ks in fam.items() for x in ks for y in ks]
print(len(single), sum(1 for a, b in single if comp(a, b)))                       # 221 139
mixed = ([(("mixed", 0), s) for s in E[:-1]] + [(s, ("mixed", 0)) for s in E[:-1]]
         + [(("mixed", 0), ("mixed", 0))])
print(len(mixed), sum(1 for a, b in mixed if comp(a, b)), sum(len(comp(a, b)) for a, b in mixed))  # 43 15 16
# 4.2 growth stream
held, axes, st = {}, 0, []
for e in E:
    for f in ev(*e):
        h = held.get(f[0])
        if h is None:
            held[f[0]] = f; axes += 1
            for s in st: s[1] = "decoded" if s[2] else "recognized"
            st.append([e, "recognized", False])
        else:
            d = (f[2] is not None and f[2] != h[2]) or f[3] != h[3]
            st.append([e, "recognized_transformed" if d else "recognized", d])
from collections import Counter
print(list(held.values()), axes, Counter(s[1] for s in st))  # 6 shapes, 6, decoded 11 / recognized 8 / transformed 4
# 4.3 projection keys
print([K(ev(*e)[0]) if len(ev(*e)) == 1 else None for e in E])
```
