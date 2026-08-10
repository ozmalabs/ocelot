# PREREG — MODULATOR-DRIVEN DOOM AGENT THAT NARRATES ITS EMOTIONS (block 208000)

*Committed ALONE, before any result number. Seed block **208000–208999**
(`scripts/seed_claim.py 208000 208999` → `CLEAN`). Off `main` HEAD
**`3c2033d246`**. Engine canonical **`793ce09ed498a749abb79aeaea44b92e`**
(the `.pth`/symlink engine; no Rust added, so the source-identical canonical
`.so` resolves). No Rust; `term.rs` + whole `runners/dsl` diff EMPTY.*

## 0. What this is — a FUSION, not a new mechanism

Fuse **205000** (the active curiosity-driven Doom exploration loop on real E1M1
geometry — perception→DECISION→ACTION, all graph-native) with **207000**
(emotions as EMERGENT regions in a 6-modulator space set by a drive system,
Bach/Dörner PSI/MicroPsi). As the 205000 agent PLAYS, its live play OBSERVABLES
feed the 207000 DRIVE system, the drives shift the MODULATORS, and the 207000
REGION predicates fire an EMOTION — which the agent NARRATES along the play
timeline. **The emotion is the graph's** (an emergent 207000 region arising from
real play); **the narration wording is a lexicon** (a template read-off).

No new emotion machinery is authored. The ONLY new graph data is:
1. a graph-native **drive-feed rule** (the appraisal: play observables →
   `Drive` state), guarded default-OFF, and
2. a **narration lexicon** (`EmotionNarration` nodes, one per emotion code) +
   the read-off — all in a NEW seed `seeds/doom_emotion_narration.json`.

Everything else is reused: 205000 (`doom_active_exploration` + the map/nav
adapters), 207000 (`drives` + `modulators`), 202000 (learning-progress),
196000 (staleness/scale2). NO Rust.

## 1. Architecture (non-negotiable, per CLAUDE.md)

- **Emotions EMERGE graph-native.** The run adapter mechanically writes raw play
  OBSERVABLES the 205000 loop ALREADY produces (coverage-delta / novel-cells;
  committed-frontier pose + whether it changed; commit-net committed flag;
  leading-region learning-progress; arrival at the committed goal) as attrs on
  the play `Drive`. Then `run_rules()` fires: the **drive-feed rule** maps those
  observables → the `Drive`'s MicroPsi demand config (`v_d, c_d, c_d_prev, v_0`)
  + appraisal flags (`appraised, explore, learning_progress, value_progress,
  valued_goal, goal_blocked, was_engaged, residual`); the 207000 modulator rules
  compute `valence/arousal/resolution/…`; the 207000 region predicates fire
  `hit_<emotion>` and `emx_readoff` sets `emotion` + `action_tendency`. **No
  Python `if event: emotion=X`. No hit_/emotion attr is written by Python or by
  any new seed rule.** The discriminators that turn a config into an emotion
  (valence SIGN via `mod_valence`, arousal BAND via `mod_arousal`) are the
  UNTOUCHED 207000 rules.
- **Narration is a mechanical EMIT** — read `ms.emotion` (the code the GRAPH
  produced) → find the `EmotionNarration` node with that code → format its FIXED
  template (numbers `tick`/`coverage` filled mechanically). Admissible emit
  (like `ChatWorld.outbound()`). NOT LLM prose; no Python conditional selects
  the emotion.
- Source-audited: no forbidden `graph_rewrite`/`_match`/`_apply`/`make_rule`; no
  Python conditional selecting the emotion; the adapter only reads graph/world
  state + formats.

## 2. Setting — HONEST palette

PRIMARY (guaranteed honest, builds directly on 205000): the **EXPLORATION
palette** emerging from real E1M1 play. Because E1M1 is fully connected and the
205000 motor is idealised, the agent is essentially never hard-blocked and never
loses a frontier to unreachability — so **frustration and sadness are derived
from the agent's OWN no-progress / commit-net signals**, not from a threat.
Demonstrated emotions and their triggering play signal:

| emotion | tendency | play signal (from 205000, no oracle) |
|---|---|---|
| surprise | ORIENT | novel-cells spike ≥ `NOVEL_HI` (new geometry revealed) |
| curiosity | ENGAGE | leading-region learning-progress > 0 (productively exploring) |
| joy | REINFORCE | arrival at the committed frontier (goal reached, coverage paid off) |
| frustration | PERSIST | committed to a frontier but no coverage progress (stuck, still pursuing) |
| boredom | LEAVE | region exhausted → the 205000 frontier-SWITCH (now emotionally narrated) |
| sadness | DISENGAGE | a committed frontier becomes unreachable / no reachable frontier remains |

REACH (threat → fear/anxiety/anger) is **NOT built** here: a clean
eye-perceived moving-threat signal (197000 common-fate, no VizDoom monster
oracle) is out of scope for this rung. We DEMONSTRATE the exploration palette
and NAME threat-perception as the follow-on (per 161000/203000
seeing-not-oracle discipline). We will report exactly which emotions are
demonstrated from which signal, and whether each actually occurs in the episode.

## 3. Gates (pre-registered)

- **G-emerge (HEADLINE).** Over a real curiosity play episode, the emotion at
  each tick is produced by the 207000 modulator regions FROM the agent's live
  drive/modulator state, with NO scripted per-tick emotion in the seed set or
  Python. PASS iff: (a) the drive→modulator→region chain fires under `run_rules`
  (a non-trivial fraction of ticks carry a fired emotion with exactly one region
  per tick); (b) an audit shows NO new seed rule and NO Python line writes any
  `hit_*` / `emotion` / `action_tendency` attr; (c) the emotion codes on the
  `ModulatorState` are set only by the untouched 207000 `emx_*` / `emx_readoff`
  rules.
- **G-track.** Emotions TRACK play events as a MEASURABLE alignment. PASS iff, on
  the episode, each emotion fires on its intended play-event class with high
  agreement — reported as an event↔emotion confusion matrix + overall agreement
  fraction over all narrated ticks (≥ 0.90 pre-registered). Specifically:
  surprise ⇔ novel-spike; curiosity ⇔ learning-progress>0; boredom ⇔ the
  frontier-switch; frustration ⇔ committed-but-no-progress; joy ⇔ arrival;
  sadness ⇔ frontier-unreachable. The event trace is defined from RAW
  observables (coverage delta, pose-change, commit flag), independently of the
  emotion labels the GRAPH produces.
- **G-narrate.** The narration is a mechanical read-off (emotion code →
  `EmotionNarration` template), aligned to the timeline, source-audited (no
  forbidden engine calls; no Python conditional selecting the emotion). Deliver
  the actual narration transcript for one episode.
- **G-discipline.** Integer-native (no `Div/Exp/Log/Sqrt/Sin/Cos/Pow` in the new
  seed; every produced attr integer). **Default-OFF byte-identical**: the new
  drive-feed rule guards on `ModulatorState.enabled` AND a `play_fed` drive flag
  set only by this adapter; absent them every existing path (including the
  207000 canonical measure and the 205000 exploration run) is byte-identical.
  Canonical `.so` md5 stays `793ce09ed498a749abb79aeaea44b92e`; `term.rs` +
  whole `runners/dsl` diff EMPTY. Oracle `bash scripts/rung7_vision_bench.sh`
  BEFORE==AFTER; 34-file `bash scripts/per_area_settlement_regression.sh`
  BEFORE==AFTER.

## 4. Deliverables

- `seeds/doom_emotion_narration.json` (drive-feed rule + `EmotionNarration`
  lexicon), emitted by `scripts/build_doom_emotion_narration_seed.py`.
- `domains/doom_emotion_narration_ingest.py` (mechanical observable extraction +
  narration read-off) + `scripts/doom_emotion_narration_run.py` (the episode) +
  `scripts/doom_emotion_narration_report.py` (gates.json + figure).
- `tests/test_doom_emotion_narration_migrated.py` (the gates).
- `DOOM_EMOTION_NARRATION_RESULTS.md` (transcript + event↔emotion alignment
  numbers), an emotion-trace figure (emotions over ticks with triggering events
  marked), and — if cheap — a rendered overlay toward the demo north-star. The
  gate is the emergent-emotion trace + narration, not video polish.

## 5. Honesty commitments

- Lead with: the emotions are the 207000 emergent regions arising from real
  205000 play; the narration is a template read-off (the emotion is the graph's,
  the wording is a lexicon).
- The drive-feed rule is the APPRAISAL (observable→drive config); it does NOT
  write the emotion — the untouched 207000 region predicates classify. Because
  appraisal and classification share the drive-feed inputs, high G-track
  agreement is expected BY DESIGN; the non-trivial content is that the region
  machinery faithfully realises the appraisal and that the SIGN/BAND
  discriminators are the graph's, not the adapter's. This is stated plainly, not
  hidden.
- Name which emotions actually occur in the episode and which are triggered by a
  progress/commit signal rather than a world threat. If an emotion does NOT track
  its event, report it straight. A partial palette honestly measured beats a full
  palette faked. Threat-perception (fear/anxiety/anger) is named as the follow-on,
  not faked with a monster oracle.
