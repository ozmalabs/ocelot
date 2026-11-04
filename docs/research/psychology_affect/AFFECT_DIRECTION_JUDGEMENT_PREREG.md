# AFFECT DIRECTION JUDGEMENT — can Ocelot's own affect read-off tell whether valence or arousal went up, down or stayed the same? — PRE-REGISTRATION (block 368000)

**Status: PRE-REGISTRATION, written 4 November 2026 BEFORE the confirmatory test
exists.** Every predicted number below is derived by hand from the rules in
`seeds/core_emotions.json` and reproduced by the pure-arithmetic oracle in Appendix A.
None is read from a run of the substrate. A deviation is reported as found: either a
harness error to fix and declare, or a finding about the substrate.

## 0. Seed claim (verbatim, run at prereg time)

```
$ .venv/bin/python scripts/seed_claim.py 368000 368999
SEED CLAIM 368000-368999: CLEAN -- no collision DETECTED.
  Scope: 1373 files with seed sinks; 877 UNRESOLVED sink sites tree-wide (counted, not discarded).
  CAVEAT 1 -- THE UNIT IS THE SEED INTEGER, not consecutive draws from
    one generator. default_rng(S) burns an unbounded stream downstream of
    S; a rung seeding ONCE at its block base measures as ONE seed here.
  CAVEAT 2 -- THIS TOOL UNDER-REPORTS BY DESIGN (7 declared blind spots;
    unresolvable sinks are COUNTED, not discarded). A CLEAN RESULT MEANS
    'NO COLLISION DETECTED', NEVER 'NO COLLISION EXISTS'.
```

The rung is **deterministic**. Every sample set is a full enumeration fixed below, and no
number is drawn from the block. The block is claimed for hygiene and successor safety.

**Erratum (4 November 2026, before any run, commit after `2c753aaa`):** G-0 originally said
"25 family events". The §4 table lists 4 families × 5 levels = 20 family events, 22 events
with neutral and mixed. Only the count in the G-0 text changed. No prediction, constant or
sample set changed.

## 1. The question

The predecessor rung ([`AFFECT_MAP_REUSE_GRID_CODE_RESULTS.md`](AFFECT_MAP_REUSE_GRID_CODE_RESULTS.md),
block 367000) showed that Ocelot's map machinery could carry a valence–arousal space with
no mechanism change. It did not test Ocelot's own affect. Its prereg (§7) named the gap:
`em_readoff` publishes valence as a sign.

Ma and Kragel (2026, *PLOS Biology*, doi:10.1371/journal.pbio.3003795) gave people
trajectories through affective space and asked, on each trial, whether valence (or
arousal) increased, decreased or stayed the same. Many of their face trajectories are
morphs within one emotion category. This rung asks the same question of Ocelot's own
appraisal read-off:

> Given two successive appraisal events, does the information Ocelot publishes about
> them (`valence`, `arousal`) determine whether the event's valence, or its intensity,
> went up, down or stayed the same?

**Pre-registered expectation:** valence direction is recoverable across emotion
categories but not within one (0/40 within-category pairs). Gains leak their magnitude
into `arousal`, so a judge reading both channels can order gains. Losses carry no
magnitude in either channel. A mixed event (gain plus threat) is published with positive
valence and a fear label.

**What a pass would mean, and what it would not.** A pass shows a representational limit
of the current read-off, measured. It does not show that Ocelot behaves badly on any
task, and it measures nothing about people. Whether to change the read-off is decided by
a later rung, not by this one (§6).

### 1.1 The read-off under test (read-only audit, 4 November 2026)

Ocelot has two affect read-offs. This rung tests (A).

- **(A) `seeds/core_emotions.json`.** Rules match
  `[["hub","has_emotion_params","ep"],["hub","has_appraisal","ap"]]`, guarded by
  `ep.enabled == 1`. Order-0 to order-4 rules derive `value_progress`,
  `learning_progress`, `threat_precision` and the value sums. Order-5 rules set
  `hit_<emotion>` flags. `em_readoff` (order 9) writes onto the `Appraisal`:
  - `valence`: 0 if `n_fired == 0` or surprise fired; else +1 if any of joy, curiosity or
    fulfilment fired (even when a negative emotion also fired); else −1.
  - `arousal`: residual (surprise) → `threat_precision` (fear or anxiety) →
    `learning_progress` (curiosity) → `value_progress` (joy) →
    |`weighted_contribution`| (fulfilment) → `ep.high_arousal` (anger or frustration) →
    `ep.mid_arousal` (disgust) → `ep.low_arousal` otherwise. Sadness, boredom and
    "nothing fired" all fall through to `low_arousal`.
  - `emotion`: priority surprise 1, fear 2, anxiety 3, anger 4, frustration 5,
    disgust 6, joy 7, sadness 8, curiosity 9, boredom 10, fulfilment 11, else 0.
- **(B) `seeds/affective_state_core.json` + `seeds/modulators.json`.**
  `psi_project_canonical_affect` copies `ModulatorState.valence` and `arousal` onto the
  agent's `AffectiveState`. `mod_valence` computes a graded `valence_raw`
  (pleasure − displeasure − urge) and publishes only its sign. **Not tested here.**
- **No seed rule stores a previous valence or arousal, a delta or a trend.** The only
  temporal inputs are adapter-authored `*_prev` attrs on the event itself. A direction
  judgement therefore has no rule that makes it. This rung measures what an
  ideal observer *could* recover from the published values. It does not claim the agent
  makes the judgement.

## 2. Harness (assemble, do not invent)

The confirmatory test is measurement only and reuses the existing harness unchanged:
`scripts/core_emotions_measure.py` `_eye`, `_hub`, `_appraise`, `_attrs`, with its
`EP_DEFAULTS` (`low_arousal` 50, `mid_arousal` 400, `high_arousal` 800,
`residual_thresh` 100) and `APPR_DEFAULTS` (`v_max` 1024, `attach_v0` 1024,
`threat_c0` 1024, `t_present` 256, `threat_half_life` 1, every other input 0).

- **One event** = one fresh `Appraisal` attached to a hub, followed by one
  `inner.run_rules()`. Read `valence`, `arousal`, `emotion`, `n_fired`.
- **One trial** = an ordered pair of events on a **fresh hub**: author event 1,
  `run_rules()`, author event 2, `run_rules()`, read both.
- One `GraphEye` per arm. Hubs are not shared between trials.
- The direction comparison is **offline measurement**: an ideal observer applied to the
  read-off values. No Python result is written back into the graph.
- No change under `runners/` or `seeds/`.

## 3. Event families (fixed constants)

All attrs not listed take `APPR_DEFAULTS`. Level index k ∈ {0, 1, 2, 3, 4}.

| family | inputs | world quantity (truth) |
|---|---|---|
| **gain** (joy) | `appraised=1, valued_goal=1, goal_blocked=0, step_prev=k, step=k+1` | value change v = (1024≫k) − (1024≫(k+1)) = 512, 256, 128, 64, 32 |
| **loss** (sadness) | `appraised=1, attachment=1, regroundable=0, attach_k_prev=k, attach_k_now=k+1` | v = (1024≫(k+1)) − (1024≫k) = −512, −256, −128, −64, −32 |
| **neutral** | `appraised=1` | v = 0 |
| **threat** (fear/anxiety) | `appraised=1, threat=1, threat_half_life=1, threat_last_refresh=0, threat_now_epoch=k` | intensity 1024≫k = 1024, 512, 256, 128, 64 |
| **surprise** | `appraised=0, residual=r`, r ∈ {150, 200, 400, 800, 1600} | intensity r |
| **mixed** | gain inputs with `step_prev=1, step=4` **plus** threat inputs with `threat_now_epoch=3` | — |

**Why value change is the valence truth.** `core_emotions.json` describes its own read-off
as "valence = sign of progress/value". The graded truth is therefore the progress
itself, `value_progress`, which the substrate already computes as an integer (in-frame,
per the integer invariant).

**Why these intensities are the arousal truth.** Each is the driving signal the family's
emotion is about: threat precision (recency), prediction residual, and the magnitude of
the value change. Anger, frustration and disgust are excluded because their inputs have
no graded intensity to test.

**Judgement.** For an ordered pair (e₁, e₂) the true direction is sgn(t₂ − t₁) ∈
{−1, 0, +1}, where t is the family's truth column.

- **Valence-only observer:** judges sgn(valence₂ − valence₁).
- **Joint information bound:** a pair is *resolvable* iff t₁ = t₂ or the published tuples
  (valence, arousal) differ. This is an upper bound on any observer that reads only the
  published tuple and knows the read-off map.
- **Arousal observer:** judges sgn(arousal₂ − arousal₁) within one family.

**Sample sets.**
- **Valence arm:** the 11 levels (5 loss, neutral, 5 gain), all **121 ordered pairs**
  including same-level pairs.
- **Arousal arm:** within each of threat, surprise, gain and loss, all **25 ordered
  pairs** of its 5 levels (100 trials).
- **Mixed:** one isolated event.

## 4. The analytic oracle (Appendix A reproduces every number)

Predicted isolated read-offs, as (valence, arousal, emotion):

| family | k = 0 | 1 | 2 | 3 | 4 |
|---|---|---|---|---|---|
| gain | (+1, 512, 7) | (+1, 256, 7) | (+1, 128, 7) | (+1, 64, 7) | (+1, 32, 7) |
| loss | (−1, 50, 8) | (−1, 50, 8) | (−1, 50, 8) | (−1, 50, 8) | (−1, 50, 8) |
| threat | (−1, 1024, 3) | (−1, 512, 3) | (−1, 256, 3) | (−1, 128, 2) | (−1, 64, 2) |
| surprise | (0, 150, 1) | (0, 200, 1) | (0, 400, 1) | (0, 800, 1) | (0, 1600, 1) |

- **Neutral:** (0, 50, 0), `n_fired` 0.
- **Mixed:** joy and fear both fire (`n_fired` 2). Read-off (+1, 128, 2): **positive
  valence, fear label, threat arousal**.
- Each non-mixed, non-neutral event fires exactly one emotion (`n_fired` 1). Threat
  levels k ≤ 2 are anxiety, because precision ≥ `t_present` (256).

Valence arm:
- distinct published valence values over the 11 levels: **3**;
  distinct (valence, arousal) tuples: **7**;
- valence-only observer: **81/121** correct;
  - within-category pairs (distinct levels, both gain or both loss): **0/40**;
  - cross-category pairs: **70/70**;
  - same-level pairs: **11/11**;
- joint information bound: **101/121** resolvable. The 20 unresolvable pairs are exactly
  the distinct-level loss–loss pairs.

Arousal arm (arousal observer): threat **25/25**, surprise **25/25**, gain **25/25**,
loss **5/25** (only the 5 same-level pairs).

## 5. Pre-registered gates

| gate | prediction | fails if |
|---|---|---|
| **G-0** harness reproduces the oracle | every isolated read-off in §4 (20 family events, neutral, mixed: 22 events) equals its predicted (valence, arousal, emotion), and `n_fired` is 1 (0 for neutral, 2 for mixed) | any mismatch. **Every later gate is then uninterpretable until the cause is localised.** |
| **G-1** context independence | in every one of the 221 trials, each event's read-off equals its isolated read-off | any difference (the first event changes the second) |
| **G-2** valence-only direction | 81/121 correct; within-category 0/40; cross-category 70/70; same-level 11/11 | any count differs |
| **G-3** joint information bound | 3 distinct valences, 7 distinct tuples; 101/121 resolvable; the unresolvable set is exactly the 20 distinct-level loss–loss pairs | any count or set differs |
| **G-4** arousal direction | threat 25/25, surprise 25/25, gain 25/25, loss 5/25 | any count differs |
| **G-5** mixed event | (+1, 128, 2), `n_fired` 2 | any difference |
| **G-6** zero mechanism change | `git diff --stat <start-commit> -- runners/ seeds/` empty at the end of the run | any change |

There are no exploratory arms.

## 6. What each outcome means

| outcome | reading |
|---|---|
| G-0–G-6 pass | Ocelot's appraisal read-off supports cross-category valence direction but **no within-category valence direction** (0/40), which is the core of the Ma & Kragel task on morph trajectories. Gain magnitude survives only through `arousal`; **loss magnitude survives in neither channel**, an asymmetry between gains and losses. A mixed event is published with **positive valence under a fear label**. And no rule makes a direction judgement at all. Together these support, but do not themselves make, a change: publish a graded integer valence (for example from `value_progress`), give sadness an arousal from the loss magnitude, and state a valence policy for mixed events. That change needs its own prereg, its own gates, and a check that the 11/11 G1 table in `tests/test_core_emotions_migrated.py` and every reader of `valence` listed in §1.1 still behave. |
| G-0 fails | The read-off is not what §1.1 states. Localise it before reading anything else. If the hand derivation is wrong, rerun under a new prereg and report both. |
| G-1 fails | Events on a hub interact. That is a finding about the substrate (for example latched `hit_*` flags leaking across appraisals) and becomes the headline. |
| G-2 or G-3 within-category counts are above prediction | The read-off carries more graded valence than §1.1 states. Localise which channel. |
| G-4 loss above 5/25 | Sadness arousal is graded after all. Localise the rule. |
| G-5 differs | Mixed-event valence is not "positive dominates". Report the actual policy. |

## 7. Known gaps stated in advance

- **Path (B) is not tested.** The `AffectiveState` that other seeds read gets its valence
  from `ModulatorState`, which is also sign-quantised by inspection (`mod_valence`), but
  no number here measures it.
- **Ideal observer, not agent.** The direction judgement is computed offline. The agent
  has no rule for it.
- **Synthetic events.** Families are hand-authored appraisal configurations, not events
  generated by a world. The truth columns are declared, not measured.
- **Anger, frustration, disgust, curiosity, boredom and fulfilment are not in the sample.**
  Anger, frustration and disgust have constant arousal by construction; curiosity and
  fulfilment are graded positive families like gain; boredom shares sadness's
  `low_arousal` fall-through.
- **Harness defaults are the only parameter set.** A different `low_arousal`, for
  instance, changes no count here, because every loss and the neutral event share it.

## 8. Files

- This pre-registration: `docs/research/psychology_affect/AFFECT_DIRECTION_JUDGEMENT_PREREG.md`
- To be written, test (measurement only): `tests/test_affect_direction_judgement.py`.
  It uses `pytest.importorskip("substrate_rs")` and the `scripts/core_emotions_measure.py`
  helpers unchanged. One test per gate. Measurements go to
  `results/affect_direction_judgement.json`.
- To be written, results: `docs/research/psychology_affect/AFFECT_DIRECTION_JUDGEMENT_RESULTS.md`,
  reporting every gate, the start commit, the engine provenance line and the G-6 diff.
- Run with: `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_affect_direction_judgement.py -q -p no:cacheprovider`

## 9. Discipline

- The start commit is the commit of this file. G-6 diffs against it.
- No constant in §3 changes after the run. A wrong constant means a new prereg, with
  both reported.
- Report nulls as headline findings.
- This rung measures a synthetic mechanism. None of it measures a person.

## Appendix A — oracle (pure arithmetic; reproduces every number in §4)

```python
LOW, T_PRESENT = 50, 256

def sgn(x): return (x > 0) - (x < 0)

def readoff(kind, k):
    if kind == "gain":     return (1, (1024 >> k) - (1024 >> (k + 1)), 7)
    if kind == "loss":     return (-1, LOW, 8)
    if kind == "neutral":  return (0, LOW, 0)
    if kind == "threat":
        p = 1024 >> k;     return (-1, p, 3 if p >= T_PRESENT else 2)
    if kind == "surprise": return (0, k, 1)

def truth_value(kind, k):
    if kind == "gain": return (1024 >> k) - (1024 >> (k + 1))
    if kind == "loss": return (1024 >> (k + 1)) - (1024 >> k)
    return 0

V = [("loss", k) for k in range(5)] + [("neutral", 0)] + [("gain", k) for k in range(5)]
P = [(a, b) for a in V for b in V]
t = {lv: truth_value(*lv) for lv in V}; r = {lv: readoff(*lv) for lv in V}
ok = lambda a, b: sgn(r[b][0] - r[a][0]) == sgn(t[b] - t[a])
within = [(a, b) for a, b in P if a != b and a[0] == b[0] and a[0] in ("gain", "loss")]
cross = [(a, b) for a, b in P if a[0] != b[0]]
print(len(P), sum(ok(a, b) for a, b in P),                                   # 121 81
      sum(t[a] == t[b] or r[a][:2] != r[b][:2] for a, b in P),               # 101
      len(within), sum(ok(a, b) for a, b in within),                         # 40 0
      len(cross), sum(ok(a, b) for a, b in cross),                           # 70 70
      len({x[0] for x in r.values()}), len({x[:2] for x in r.values()}))     # 3 7

FAM = {"threat": range(5), "surprise": [150, 200, 400, 800, 1600],
       "gain": range(5), "loss": range(5)}
def intensity(kind, k):
    return 1024 >> k if kind == "threat" else k if kind == "surprise" else abs(truth_value(kind, k))
for kind, ks in FAM.items():
    print(kind, sum(sgn(readoff(kind, b)[1] - readoff(kind, a)[1]) ==
                    sgn(intensity(kind, b) - intensity(kind, a)) for a in ks for b in ks))
# threat 25, surprise 25, gain 25, loss 5
# mixed (joy + fear, now_epoch 3): (+1, 1024 >> 3 = 128, 2)
```
