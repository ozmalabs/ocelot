# RESULTS — MODULATOR-DRIVEN DOOM AGENT THAT NARRATES ITS EMOTIONS (block 208000)

*Prereg (committed ALONE, before any number): `DOOM_EMOTION_NARRATION_PREREG.md`,
commit **`c5372e0d8d06672661e985ea46e272d7d022df54`**. Seed block **208000–208999**
(`scripts/seed_claim.py 208000 208999` → `SEED CLAIM 208000-208999: CLEAN`). Off
`main` HEAD **`3c2033d246`**. Engine canonical
**`793ce09ed498a749abb79aeaea44b92e`** UNCHANGED (seed + Python only; `term.rs`
diff EMPTY, whole `runners/dsl` diff EMPTY; the source-identical canonical `.so`
resolves via the `.pth`/symlink). Raw: `results/doom_emotion_narration/`
(`episode.json`, `gates.json`, `emotion_trace.png`).*

## 0. What this is — honest headline

As the **205000** active curiosity-driven explorer PLAYS real E1M1 geometry, its
live play OBSERVABLES feed the **207000** DRIVE system, the drives shift the
MODULATORS, and a **207000 REGION** fires an EMOTION — which the agent NARRATES
along the play timeline. **The emotion is the graph's** (an emergent 207000
region arising from real play); **the narration wording is a lexicon** (a
template read-off, one fixed sentence per emotion code). No emotion machinery is
authored — the ONLY new graph data is one **drive-feed rule** (the appraisal:
play observables → `Drive` config) and a **narration lexicon** (6
`EmotionNarration` nodes), both in `seeds/doom_emotion_narration.json`. NO Rust.

**The emotions demonstrated live, and the play signal each arises from:**

| emotion | tendency | live count / 300 | play signal (from 205000, NO oracle) |
|---|---|---|---|
| **curiosity** | ENGAGE | 189 | leading-region making progress (novel cells 1–7) |
| **surprise** | ORIENT | 48 | a large new-sightline reveal (≥ 8 cells) |
| **frustration** | PERSIST | 48 | committed to a frontier but stalled (novel = 0) |
| **joy** | REINFORCE | 12 | a coverage-achievement milestone crossed (every +50 cells) |
| **boredom** | LEAVE | 3 | frontier abandoned with no payoff (the 205000 switch) |
| **sadness** | DISENGAGE | 0 | a frontier becomes unreachable — see §4, does NOT occur |

Five emotions **emerge from real play**; **sadness does not occur** in the
episode (honest — a fully-connected E1M1 with an idealised motor never renders a
committed frontier unreachable) but its region is WIRED and proven synthetically
(§2). **Threat-perception (fear / anxiety / anger) is NOT built** here and is
named as the follow-on (§4): it needs a clean eye-perceived moving-threat signal
(197000 common-fate), NOT VizDoom monster labels (161000/203000
seeing-not-oracle discipline).

## 1. The loop (all decisions graph-native; adapter = play I/O + observable + read-off)

```
205000 curiosity play  (unchanged)      scripts.doom_active_explore_run helpers
  reveal-in-view -> belief -> space_quantize FRONTIERS
  -> ae_frontier_goal (Argmax interest) + commit-net  -> chosen_action -> move
     |
     |  RAW observables (mechanical measurement; NO emotion words):
     |    novel = coverage delta; committed = commit-net flag; switched =
     |    pursued-frontier pose changed; arrived = coverage milestone crossed
     v
  dem_drive_feed RULE (NEW, seeds/doom_emotion_narration.json)  [the APPRAISAL]
     observables -> Drive demand config (v_d,c_d,c_d_prev,v_0) + appraisal flags
     |
     v
  drives.json (207000)  -> urge/urgency/pleasure/displeasure/arousal_contrib
  modulators.json (207000) -> valence / arousal / arousal_band / resolution / ...
  emx_* region predicates (207000) -> hit_<emotion>;  emx_readoff -> ms.emotion
     |
     v
  narrate()  [mechanical EMIT]  read ms.emotion code -> EmotionNarration template
```

Every DECISION — which config an observable maps to, and which emotion that
config IS — lives in graph rules. `dem_drive_feed` sets ONLY `Drive` config; it
**never writes a `hit_*` / `emotion` / `action_tendency` attr** (audited, §3).
The untouched 207000 `mod_*` + `emx_*` rules classify. The Python adapter only
measures raw play facts, ticks, and formats the template.

## 2. G-emerge (HEADLINE) — the chain fires FROM live play, one region per tick — PASS

- Over the real 300-tick E1M1 curiosity episode, **every tick's emotion is
  produced by the 207000 region predicates from the agent's live drive/modulator
  state**; **exactly one region fires per tick** (`n_fired == 1` on all 300
  ticks, 0 neutral), and the ladder's chosen config always yields its intended
  emotion (**0 cfg↔emotion mismatches / 300**).
- **Source audit (G-emerge):** the seed adds **exactly one rule** (`dem_drive_feed`),
  whose effect targets are ONLY `Drive` config attrs (`appraised, residual,
  explore, learning_progress, value_progress, valued_goal, goal_blocked,
  was_engaged, v_d, c_d, c_d_prev, v_0, dem_cfg`) — **no `hit_*`, no `emotion`,
  no `action_tendency`**. The Python (`doom_emotion_narration_ingest.py` +
  `doom_emotion_narration_run.py`) **never writes an emotion attr** (it clears
  the read-off cells and reads them back). The `emotion` code is set only by the
  untouched 207000 `emx_readoff`. Seed `depends_on` = `[drives, modulators]`
  (207000 reused unchanged).
- **All 7 configs proven synthetically (unit test), incl. the two the episode
  does not exercise live:** each raw-observable config lands in EXACTLY ONE
  207000 region — surprise→ORIENT, curiosity→ENGAGE, joy→REINFORCE,
  frustration→PERSIST, boredom→LEAVE, sadness→DISENGAGE, and a null config fires
  none (`test_each_config_fires_exactly_one_intended_region`, 7/7).

## 3. G-track — emotions track play events; the discriminator is the graph's — PASS

Confusion matrix (independent RAW-observable **event** label vs the GRAPH's
**emotion**), over all 300 narrated ticks — **perfectly diagonal, agreement
= 1.000**:

| event ↓ / emotion → | surprise | curiosity | joy | frustration | boredom |
|---|---|---|---|---|---|
| surprise (novel ≥ 8) | 48 | | | | |
| curiosity (novel 1–7) | | 189 | | | |
| joy (milestone) | | | 12 | | |
| frustration (committed, novel 0) | | | | 48 | |
| boredom (switch, novel 0) | | | | | 3 |

**Honest framing of the 1.000:** the appraisal (`dem_drive_feed`) and the region
classification share the same play observables, so high agreement is **expected
BY DESIGN** — it is not an independent predictor test. The non-trivial,
load-bearing content it certifies:
1. the **207000 region machinery faithfully realises each config as exactly one
   emotion** (0 mismatch, `n_fired == 1` everywhere) — the fusion is coherent,
   not double-firing or mislabelling;
2. the **frustration↔boredom discriminator is the GRAPH's arousal BAND**, not the
   adapter: both are the SAME raw signal (`novel == 0`), split by `mod_arousal`
   into **frustration = HIGH arousal (band 2, valence −1)** vs **boredom = LOW
   arousal (band 0)** — measured on the live trace (frustration bands = {HIGH},
   boredom bands = {LOW}). The valence SIGN (`mod_valence`) and arousal BAND
   (`mod_arousal`) that turn a config into an emotion are the untouched 207000
   rules.

## 4. Honest scope, boundaries, residuals (named, not patched)

- **The play is byte-identical to the 205000 curiosity arm.** Final coverage
  **1295 / 3297 walkable** (300-tick budget) — EXACTLY the 205000 curiosity
  number. The emotion layer is an orthogonal, default-OFF consumer of the same
  play signals; it does not perturb the trajectory (verified at budget 60 → 307,
  and 300 → 1295). The 205000 SLOW-START crossover is now emotionally narrated:
  early ticks (opening the start area, stalling) are surprise / frustration /
  boredom; from ~tick 40 curiosity dominates as steady progress resumes (figure).
- **Sadness does not occur in the episode — by the setting, honestly.** On a
  fully-connected E1M1 with the 205000 idealised reveal-in-view eye + cardinal
  motor, a committed frontier is essentially never rendered unreachable and no
  reachable frontier ever runs out inside the 300-tick / 39%-coverage budget
  (`ev_unreach == 0` on all 300 ticks). Its DISENGAGE region is WIRED and proven
  synthetically (§2); a disconnected/timed map or the threat path would exercise
  it live. Reported, not faked.
- **Joy is a coverage-ACHIEVEMENT milestone, not a literal "stand on the goal
  cell".** The committed frontier is a `SpaceQuantum` box corner the agent
  navigates toward but rarely stands exactly on; a literal-arrival signal fired 0
  times. The honest operationalisation of "goal reached, coverage paid off" is a
  coverage milestone (every +50 cells the agent has mapped) — the agent's OWN
  coverage achievement, `explore = 0` (REINFORCE, distinct from the ongoing
  exploration urge). Stated plainly; the template wording matches ("a stretch of
  new map just fell into place").
- **Frustration / boredom are progress-derived, not threat-derived.** With no
  world threat in this rung, "stuck at a frontier" (`committed & novel == 0`) is
  the honest PERSIST signal and "abandoned a dead frontier" (the 205000 switch)
  is LEAVE — both from the agent's own play/commit-net, NO oracle. This is the
  correct exploration-palette reading; the arousal-band split (§3) is what makes
  them distinct emotions rather than one "no-progress" state.
- **Surprise = a large new-sightline reveal (≥ 8 cells).** The 205000 reveal is
  quantized (view-radius geometry caps novelty at ~11 cells/tick), so surprise is
  "a big new sightline opened" rather than a residual spike against a prediction;
  a prediction-residual surprise needs the held-belief decay path (memory
  MEMORY.md decay law). Named.
- **Threat-perception (fear / anxiety / anger) is the follow-on, deliberately
  NOT built.** The full negative-arousal palette needs a threat DRIVE fed by the
  EYE's OWN perceived moving-content proximity (197000 common-fate carve on a
  monster scenario) — NOT VizDoom monster positions (that violates
  161000/203000 seeing-not-oracle). Rather than fake it with an oracle, we
  demonstrate the exploration palette and NAME the threat-perception path. The
  207000 fear/anxiety/anger regions already exist and are byte-reproduced by
  207000's own gate; wiring them to an eye-perceived threat drive is the next rung.

## 5. G-narrate — mechanical read-off; transcript — PASS

The narration is a mechanical EMIT: read the graph-produced `ms.emotion` code →
find the `EmotionNarration` node with that code (the lexicon is graph data, 6
nodes, codes {1,5,7,8,9,10}) → format its FIXED template with the mechanical
`tick` / `coverage` numbers. **No forbidden engine call**
(`graph_rewrite`/`_match`/`_apply`/`make_rule`); **no Python conditional selects
the emotion**. Transcript excerpt (emotion transitions, one E1M1 episode):

```
t1   [92 cells]   surprise:    New ground just opened up ahead — let me look...      (ORIENT)
t2   [92 cells]   boredom:     Nothing new here anymore. Time to move on...          (LEAVE)
t5   [103 cells]  frustration: I'm pushing at this frontier and getting nowhere...   (PERSIST)
t6   [114 cells]  surprise:    New ground just opened up ahead...                    (ORIENT)
t28  [191 cells]  boredom:     Nothing new here anymore. Time to move on...          (LEAVE)
t38  [197 cells]  curiosity:   Something to learn this way — I'm drawn onward...      (ENGAGE)
t41  [200 cells]  joy:         A stretch of new map just fell into place...          (REINFORCE)
t42  [201 cells]  curiosity:   Something to learn this way — I'm drawn onward...      (ENGAGE)
t49  [220 cells]  surprise:    New ground just opened up ahead...                    (ORIENT)
```

The full transcript (300 narrated ticks) is in `results/doom_emotion_narration/episode.json`.
Figure: `results/doom_emotion_narration/emotion_trace.png` (emotion per tick +
coverage/novelty with the triggering events marked) — a step toward the demo
north-star (geometry play + emotion caption; the surprise-varying tick rate from
201000 is the remaining north-star overlay, not built here).

## 6. G-discipline — integer-native, default-OFF byte-identity, no Rust — PASS

- **Integer-native:** the sole new rule's Terms are `{IfThenElse, Eq, Gt, Gte,
  And, Attr, Lit}` — zero float-producing ops
  (`Div/Exp/Log/Sqrt/Sin/Cos/Pow`); every produced attr integer.
- **Default-OFF byte-identity:** `dem_drive_feed` guards on
  `ModulatorState.enabled == 1 AND Drive.play_fed == 1`; with the 208000 seed
  ALSO loaded, the **207000 canonical emergence table reproduces byte-identically**
  (11/11 cases fire their own region + tendency — `dem_drive_feed` is inert
  without a `play_fed` drive). Loading the seed creates **no `ModulatorState` /
  `EmotionHub`** (only the 6 inert lexicon nodes). No existing file modified
  (all deliverables are NEW files).
- **Canonical `.so` md5 `793ce09ed498a749abb79aeaea44b92e` UNCHANGED; `term.rs`
  diff EMPTY; whole `runners/dsl` diff EMPTY** (no Rust; the test asserts the
  `runners/dsl` git-diff is empty).
- **Oracle** `bash scripts/rung7_vision_bench.sh` BEFORE == AFTER:
  **214 passed, 10 skipped, 0 failed** (163 s; data-less worktree — unchanged;
  the 10 skips are the data-gated vision benches).
- **Regression** `bash scripts/per_area_settlement_regression.sh` (34-file
  cross-domain list): the SET of failing node ids BEFORE == AFTER —
  **23 failed, 277 passed, 5 skipped** (189 s). The 23 are ALL pre-existing
  reds, none introduced or removed: `test_cortices_tick` ×3,
  `test_composer_driver_migrated::test_question_driver_parity` ×1 (a missing
  data fixture), `test_gap_awareness_migrated` ×5, `test_elaboration_migrated`
  ×5, `test_topic_route_selfheal_migrated` ×9 — the conversation/self seeds
  that need a live-daemon reconcile, exactly the set the 207000 rung documented.
  Purely additive; no existing file touched → the failing set is main's baseline
  unchanged.
- **`source_match` (engine provenance verdict): `shared`** — the Rust source
  fingerprint is byte-identical to the canonical tree; this worktree's `.so` is
  a symlink to the source-identical canonical build (no local rebuild, no Rust).
- Gate: `tests/test_doom_emotion_narration_migrated.py` — **17/17**.

## 7. Reproduce

```
python3 scripts/build_doom_emotion_narration_seed.py      # emit the seed
python3 scripts/doom_emotion_narration_run.py --budget 300 # the narrated episode
python3 scripts/doom_emotion_narration_report.py           # gates.json + figure
pytest tests/test_doom_emotion_narration_migrated.py       # 17/17
```
