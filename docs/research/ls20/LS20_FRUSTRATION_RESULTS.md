# FRUSTRATION — futile repetition triggers an emotional STOP (RESULTS)

Block **226000**. Worktree off `main` HEAD `80f1e12cb2` (LEDGER 224000). Engine
canonical **`793ce09ed498a749abb79aeaea44b92e`** (unchanged). Prereg committed
ALONE at **`0521da02f03a8cc78cb2a396bb52b9a817b8481c`**, BEFORE any number below.

**Headline (lead with the discriminator):** frustration tracks **FUTILITY**, not
repetition. At W=6 IDENTICAL repeats of one `(state,action)`, frustration is
**36.0 [36.0, 36.0]** when the repeats yield NO understanding, and **0.0
[0.0, 0.0]** when the SAME repeats keep yielding understanding — CI-separated.
The productive-repetition control (which a plain repeat-counter fails) holds at
zero. The emotion FEELS the futility; it does not count repeats.

---

## The mechanism (graph-native; NO Rust; reuse 207 + 215 + 208)

ONE `self_load_only` seed `seeds/ls20_frustration.json` (builder
`domains/ls20_frustration_seed.py`), wired to an `EmotionHub` like the 215000
grievance. The trajectory is GRAPH DATA (`FrustrationModulator -has_step-> Step`);
three rules, every Term pre-existing:

| rule | order | what it decides |
|---|---|---|
| `fr_mark_futile` | 0 | THE DISCRIMINATOR — `st.futile=1` iff `d_hyp==0 AND d_state==0 AND s_drop==0` AND `Exists` an earlier `has_step` Step with the same `sig` (recurrence is a graph MATCH; no-gain is the three raw observables the adapter stamps, the 208000 `ev_*` pattern) |
| `fr_accumulate` | 1 | the 215000 leaky **scale2** accumulator: `frustration = Sum Times(futile, Ashr(frust_unit, age/half_life))` over `has_step` — FUTILE steps only |
| `fr_break` | 2 | the regress-break: `frustration >= frustration_thresh` → `break_now=1`, `action_tendency="STOP"`, `emotion_code=1` |

Frozen constants (prereg §4): `frust_unit=8`, `half_life=4`,
`frustration_thresh=20`, cap `CAP=40`. The adapter
(`domains/frustration_world.py`) only adds the immutable `Step`, advances
`now_epoch`, `run_rules()`, and reads `break_now`. No `if repeated: stop`.

---

## The gates (SYNTHETIC scenario, N=200/arm, bootstrap 95% CI — `results/frustration.json`)

### G-frustration-tracks-futility — HEADLINE + teeth ✅
Frustration after W=6 looped repeats:

| arm | mean | 95% CI |
|---|---|---|
| FUTILE (repeat, no gain) | **36.0** | [36.0, 36.0] |
| PRODUCTIVE (repeat, still gaining) | **0.0** | [0.0, 0.0] |

CI-separated; the productive upper CI is exactly 0. Mean frustration trajectory
over the first 10 looped repeats:

- FUTILE: `0, 8, 16, 24, 32, 36, 40, 44, 48, 50` (rises, then the scale2 decay on
  the oldest futile events bends the slope — a leaky accumulator, not a counter).
- PRODUCTIVE: `0, 0, 0, 0, 0, 0, 0, 0, 0, 0` (flat).

**The teeth:** identical repetition; the ONLY difference is whether the repeats
keep yielding understanding. A plain repeat-counter would raise on both and FAIL
the productive control. It does not — frustration stays 0 under productive
repetition. Gain via ANY of the three observables (`d_hyp`/`d_state`/`s_drop`)
suppresses frustration (unit test).

### G-breaks-the-loop ✅
FUTILE scenario, regulation ON vs OFF (paired on seeds):

| | steps-to-break | 95% CI | ever broke |
|---|---|---|---|
| ON | **5.54** | [5.37, 5.69] | 200/200 |
| OFF | **40.0** (cap) | [40.0, 40.0] | 0/200 |

CI-separated (ON ≪ OFF). The un-regulated agent NEVER self-stops — it cycles to
the cap (exactly the "just cycling" the owner saw); the emotion breaks the loop
in ~5–6 steps.

### G-no-false-break (selectivity) ✅
PRODUCTIVE scenario, regulation ON: false-break count **0 / 200**; false-break
rate 0.0 (Wilson 95% CI [0.0, 0.019]), vs the FUTILE break rate 1.0 [0.981, 1.0].
Productive upper CI < futile lower CI → **selective**. The regulation never stops
an agent that is still gaining.

### G-graph-native ✅ (source audit)
Every decision is a rule (`fr_mark_futile` / `fr_accumulate` / `fr_break`); the
adapter is mechanical I/O. `fr_mark_futile`'s recurrence is a graph `Exists`
match over the step history — verified in the manifest. Adapter source scan
(code, docstrings stripped): NO `graph_rewrite.run` / `gr.run(` / `._match(` /
`._apply(` / `make_rule`; the ONLY stop condition read is `break_now` (set by the
rule). `source_match` = MATCH (provenance `assert_measuring_engine` green; loaded
engine `04c9d28e316d` ≡ this tree's Rust source; canonical `.so`
`793ce09e…`).

### G-narration ✅ (208000 tie-in)
On break the adapter emits the `FrustrationNarration` template keyed by
`emotion_code`, from graph state. Verbatim sample (futile run, break at step 4):

> *"Same thing over and over, no progress — this is frustrating. Stop and try
> something else."*

### G-discipline ✅
- Integer-native (every literal whole; `Sum/Ashr/IDiv/Times/Minus/Max/Eq/Gte/Lt/
  And/Exists/Attr/Lit`).
- **Default-OFF byte-identity:** `ls20_frustration.json` is `self_load_only:true`,
  `depends_on:[]`, nothing depends on it → skipped by `load_all_seeds`. With
  `enabled=0` the rules never fire (test: futile input, 40 steps, no break,
  frustration 0).
- **`term.rs` diff EMPTY; whole `runners/dsl` diff EMPTY** (NO Rust). Canonical
  `.so` md5 **`793ce09ed498a749abb79aeaea44b92e`** unchanged.
- **Oracle** `rung7_vision_bench.sh`: BEFORE `214 passed, 10 skipped`; AFTER
  `214 passed, 10 skipped` — SET identical.
- **Regression** `per_area_settlement_regression.sh` (34-file): BEFORE
  `23 failed, 277 passed, 5 skipped`; AFTER `23 failed, 277 passed, 5 skipped` —
  failing-node-id SET identical (`diff` empty; the 23 are pre-existing
  conversation-seed reds:
  composer_driver / cortices_tick / elaboration / gap_awareness /
  topic_route_selfheal — untouched by this rung).
- New gate suite `tests/test_ls20_frustration_migrated.py`: **12/12 green**.

---

## The ls20 DEMONSTRATION (honest scope — `results/frustration_ls20_demo.json`)

Frustration wired to the ACTUAL 221000 per-cycle signals (surprise + model
accuracy from `investigate`) on the OFFLINE `arc_ls20_scenario` corpus (no live
API):

| ls20 run | model accuracy | frustration | break |
|---|---|---|---|
| PRODUCTIVE (clean perception) | `0.17→0.33→…→1.0` (learns) | flat 0 through the 6-cycle learning phase | breaks only at cycle **9**, AFTER full saturation |
| FUTILE (perception thrashing, σ=64) | flat **0.0** (never models) | rises `0,8,16,24` | breaks at cycle **3** |

The futile run stops early; the learning run is left alone while it gains, and
only frustrates once it has understood everything and keeps mindlessly repeating
(a correct emergent behaviour, not hidden). **Notably, surprise ALONE is fooled**
— it drops in BOTH runs (the noisy recogniser confirms a consistently-WRONG key),
so a surprise-only detector would mis-judge the thrashing as progress. The
model-accuracy gain (`d_hyp`) is the signal that correctly separates real
understanding from consistent-but-wrong, and the discriminator uses it.

**Honest framing:** the live ls20 cycling the owner saw is partly the naive
live-harness action policy (a Python-layer issue). The general deliverable is the
CAPABILITY — emotional regulation against futile repetition — which is the same
modulator on any domain (Doom, harvest, ls20), demonstrated here on the real
understanding signal.

---

## Honest residuals

- The synthetic headline is **deterministic** (CI width 0): the mechanism is a
  pure function of the futile-step facts, and frustration is read at a FIXED
  looped-repeat index, so the only randomised knob (prefix length) does not move
  it. The determinism is the point (glass-box), not hidden variance; the power is
  in the arm CONTRAST, not within-arm spread.
- Frustration here sets a LOCAL `break_now`/`action_tendency` flag, not the global
  207000 `ModulatorState.resolution` drop. Wiring `frustration` into the region
  reader so it lowers global resolution (the true PSI resolution-collapse) is the
  named follow-on.
- STOP is the only regress-break realised; frustration→raise-exploration (switch
  strategy rather than halt) is the other face, named not built.
- The live-harness action-policy fix is a Python-layer gap the agent can only
  FIND/file (per the gap pipeline), not self-repair — out of scope here.
