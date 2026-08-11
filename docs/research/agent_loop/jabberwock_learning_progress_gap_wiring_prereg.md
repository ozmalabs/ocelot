# PREREG — WIRING `learning_progress_curiosity` INTO GAP-AWARENESS AS AN AUTONOMOUS TOPIC-SELECTION TRIGGER

**Charter.** `docs/research/theory_convergence/RAVANA_CONVERGENCE_AUDIT.md` §6.2
names a precise, scoped recommendation: OCELOT already holds a
theoretically-stronger, gated, two-timescale learning-progress signal
(`seeds/learning_progress_curiosity.json`) than RAVANA's single-EMA
prediction-error curiosity, but nothing currently *consumes* it to drive
proactive, autonomous topic selection — `seeds/gap_awareness.json`'s five gap
kinds are all reactive (they fire on an actual conversational miss). This rung
investigates the actual code (not the audit's own unverified §7.3 uncertainty),
registers a GO/NO-GO on wiring scope, and — if GO — builds and demonstrates the
smallest honest wiring.

**House-style note on where this lives.** `learning_progress_curiosity.json`'s
own bar-setting PREREG/RESULTS pair lives in `docs/research/vision/` (block
202000), and its first non-vision consumer (`doom_active_exploration`, block
205000) was *also* placed there, alongside the mechanism, not in a
doom-specific folder — because that folder is where the block-numbered `SEED
CLAIM` collision-registration convention lives. Gap-awareness/self-concern
work, by contrast, has **never used that convention**: `seeds/gap_awareness.json`,
`seeds/conversation_elaborate.json`, `seeds/conversation_topic_route.json`, and
`seeds/conversation_self_concern.json` carry no block number and were never
accompanied by a PREREG/RESULTS pair — that arc's bars were registered
directly in `CLAUDE.md` narrative + commit messages instead. This rung is a
conversation/self-improvement-domain consumer, not a vision/doom one, and the
task brief explicitly names `docs/research/agent_loop/` as the fitting home —
so this PREREG lands there, importing the vision folder's PREREG-then-measure
bars discipline (registered here because the task requires it) without its
block-number machinery (not applicable; nothing here collides with anything
gap-awareness already owns).

---

## 1. Investigation bar — what `learning_progress_curiosity.json` actually measures, grounded in code

Read in full: `seeds/learning_progress_curiosity.json` (403 lines, 12 rules, 3
productions), `scripts/learning_progress_measure.py`, `docs/research/vision/
VISION_LEARNING_PROGRESS_PREREG.md` + `..._RESULTS.md` (the original
proof), and its one existing non-vision consumer, `seeds/doom_active_
exploration.json` + `domains/doom_active_explore_ingest.py`.

**Findings:**

- **The seed is domain-generic, not vision-hardwired.** Its node types
  (`CuriosityHub`, `AttentionItem`, `HeldCuriosityParams`, `Deliberation`) and
  every rule (`lp_residual`/`lp_fast`/`lp_slow`/`lp_progress`/`lp_gate`/
  `lp_interest`/`lp_attend`/`lp_learn`/`lp_advance`, plus the commit-net
  `cn_marginal`/`cn_commit`/`cn_advance`) read and write only `obs`, `held`,
  `input_epoch`, and the derived bookkeeping attrs — there is no vision-specific
  attribute, Concept, or Term anywhere in the file. The `"area": "retina"` tag
  is organisational seed metadata, not a domain gate. This is confirmed by its
  own second consumer already in the tree: `doom_active_exploration.json`
  reuses the identical `lp_*` rules unmodified, keyed on spatial frontier bins
  instead of pixels, with `mode=1` (surprise-gated, deliberately — see
  `doom_active_explore_ingest.py`'s own comment: frontier info-gain is a real
  geometric quantity with no noisy-TV to trap on, so raw-surprise gating is
  the *correct* choice there, not a bug). **The mechanism is a reusable
  primitive, proven once (vision, block 202000) and reused once already
  (doom, block 205000); this rung is the third reuse, conversation-domain.**
- **What it measures:** a two-timescale EMA differential of an integer
  residual — `residual = |obs − held|`, `fast_res`/`slow_res` integer EMAs
  (`fast_div=3`, `slow_div=20`), `learning_progress = slow_res − fast_res`.
  `> 0` exactly when recent surprise is dropping relative to older surprise
  (compression in progress); `≈ 0` for both a fully-resolved item (both EMAs
  converged near the true value) **and** for stationary noise (both EMAs
  track the same mean) — this shared-zero property is the textbook
  Oudeyer/Schmidhuber noisy-TV discriminator, and it is what makes the
  signal robust where a single-EMA prediction-error signal (RAVANA's
  `update_prediction_error`) is not.
- **Where it was proven:** `docs/research/vision/VISION_LEARNING_PROGRESS_
  RESULTS.md`, all 15 pre-registered criteria green — G1 (noisy-TV: gated
  interest on a noise item drops `480→130` while a naive raw-surprise
  falsifier traps at `1008→999`), G2 (leave-the-unresolved: resolved AND
  intractable both decay, only the still-progressing item is held — and the
  discriminator is provably progress, not surprise-magnitude: surprise ranks
  resolved(5) < progressing(22) < intractable(68), yet retained interest
  ranks progressing ≫ intractable > resolved), G3 (commit-net anti-paralysis),
  G4 (integer-native, default-OFF byte-identical, zero Rust diff). This was a
  **synthetic mechanism demonstration** (staged piecewise-constant vs.
  white-noise `obs` streams), not a benchmark-value claim — reported as such
  in its own RESULTS doc, and the same standing rule applies here.
- **Opt-in posture:** `self_load_only: true` — excluded from `load_all_seeds`
  (verified via `substrate/boot_all.py:39`, which explicitly skips
  `self_load_only` seeds during the sweep). It is loaded only by an explicit
  `load_seed_manifest` call (as `learning_progress_measure.py` and
  `doom_active_explore_ingest.install_curiosity` both do), and even then is
  inert without a `HeldCuriosityParams{enabled:1}` node — G4b in the original
  RESULTS gate proves byte-identical behaviour with the seed loaded but not
  opted in. **This rung's own new seed will carry the identical posture**,
  for the identical reason: zero regression risk to any existing default
  boot.
- **`gap_awareness.json` (v1.6.0, 1411 lines) is confirmed reactive-only** —
  its five rules (`note_unresolved_topic_gap`, `note_reported_gap`,
  `note_unhandled_instruction_gap`, `note_self_account_gap`,
  `note_upload_*_gap`) all fire from a Message/Goal outcome the adapter
  mechanically recorded *after a turn already happened*. Grepping the whole
  file for `CuriosityHub`/`AttentionItem`/`learning_progress` returns zero
  hits — the audit's §7.3 uncertainty ("not verified beyond the seed file")
  is now resolved: **confirmed absent**, not merely unobserved.
- **Has no emitter (hand-authored), same as `gap_awareness.json` itself.**
  Grepped `tools/*.py` and `scripts/*.py` for any script that writes either
  `seeds/gap_awareness.json` or `seeds/learning_progress_curiosity.json` as an
  output path — none found (the only hit on `learning_progress_curiosity` is
  `scripts/learning_progress_measure.py`, which *reads* it via `manifest_for`
  to opt a fresh substrate in, not an emitter). This matches the precedent
  CLAUDE.md names for `code_write_gap.json`/`prog_read_gap.json` — a new
  consumer seed here is likewise hand-authored, not machine-emitted.

## 2. GO/NO-GO on wiring scope

**GO — a minimal, correct wiring is achievable at seed/adapter cost
comparable to this arc's other cheap wins.** Concretely, three pieces, all
graph-data-or-mechanical-I/O, zero new Rust, zero new node types, zero new
Terms:

1. **One new rule**, `lp_mint_topic_gap`, in a new hand-authored seed
   `seeds/curiosity_topic_selection.json` (`self_load_only: true`,
   `depends_on: ["learning_progress_curiosity", "gap_awareness"]`) — this is
   §6.2's own scoped recommendation almost verbatim: when an `AttentionItem`
   reaches `attended == 1.0` (already computed by `lp_attend`) and carries a
   `topic` string with no matching `SelfConcern` yet, mint
   `SelfConcern{status:'noted', source:'implicit', kind:'knowledge',
   content:<topic>}` — **the exact node shape `note_unresolved_topic_gap`
   already mints**, wired to the agent via `has_self_concern` (same edge
   type) and content-deduped via the same `Not(Exists(...))` pattern every
   other gap-awareness rule already uses. This is a *proactive* sibling to
   the existing *reactive* rule: same output shape, same dedup discipline,
   same downstream consumer (`promote_self_concern` → `StandingConcern`, the
   existing human-gated spine — **this rung mints nothing that acts on its
   own; it only decides what to flag as worth the human's promotion
   attention**, exactly matching the existing culture around `SelfConcern`).
2. **One new mechanical adapter module**, `domains/curiosity_topic_ingest.py`,
   mirroring `domains/doom_active_explore_ingest.py`'s structure exactly
   (`install_curiosity`/find-or-create AttentionItem/set obs+epoch/
   `run_rules()`). Its one added piece of real *sensor* logic —
   `unknown_word_count(wa, phrase)` — reuses `WorldAdapter.taught_signs()`
   and the identical tokenisation `ground_unknowns` already uses (same strip
   characters, same `min_len` default), so it introduces no new concept of
   "how much is unknown," only a read of the agent's own existing lexical
   state. This is a real, honestly-sourced sensor (mirrors
   `doom_active_explore_ingest._info_gain`'s "count of unknown-bordering
   cells" pattern one-for-one, substituting "count of ungrounded words" for
   "count of unknown cells") — not a fabricated scalar.
3. **A demonstration/measurement script**, matching
   `scripts/learning_progress_measure.py`'s own pattern, feeding candidate
   topics through the real `ground_unknowns` loop.

**Explicitly out of scope for this rung (named, not built):**

- **The commit-net (`cn_*`) is not wired.** §6.2's recommendation only needs
  `lp_attend`'s `attended` flag; the anti-paralysis deliberation-cut is a
  different concern (when to stop reconsidering an in-progress decision) with
  no natural referent yet in "which topic to flag as worth learning." Wiring
  it would require inventing what a conversational "deliberation step" is —
  exactly the kind of scope creep this PREREG is registered against.
- **A fully autonomous, always-on daemon hook is NOT built.** The live
  daemon does not currently create per-candidate-topic `AttentionItem`s from
  real multi-turn conversation on its own tick loop — doing so honestly
  requires deciding, in the daemon's own terms, which recurring
  conversational entities become curiosity candidates and how often they get
  re-sampled (a genuinely separate design question, e.g. "which Mentions
  across how many recent turns become candidates" — the audit's own §7.3
  flags this as unverified and it remains so). What IS built and proven here
  is the complete, correct, reusable **mechanism + wiring + real sensor**,
  exercised end-to-end through the identical adapter/seed shape the daemon
  would call — a human wiring `curiosity_topic_ingest.maintain_topic_interest`
  into a periodic daemon tick (mirroring how `doom_active_explore_ingest` is
  driven by its own `run_arm` loop) is the small, well-named remainder, not a
  new cross-domain abstraction. This is reported honestly as the boundary of
  this rung, not silently assumed away.
- **No cross-domain "progress" abstraction is invented.** `obs`/`held`
  stay exactly what they already are (raw numeric residual inputs); no new
  generic "Progress" node type or protocol is added. Every domain (vision,
  doom, now conversation) supplies its own `obs` through its own honest
  sensor function into the *same* generic `CuriosityHub`/`AttentionItem`
  shape — confirming the audit's own read that the "harder half" (the
  mechanism) was already solved, and only a per-domain sensor + consumer
  rule was missing.

## 3. Demonstration bars (registered before any number)

Three co-present, real-sensor-fed candidate topics on one `CuriosityHub`,
gated mode (`mode=0`), reusing the ORIGINAL proof's own calibrated `PARAMS`
(`hl_min=1, hl_scale=4, interest_c0=1024, attend_thresh=256, progress_floor=10,
surprise_floor=4, fast_div=3, slow_div=20, blend_div=2` — unchanged from
`learning_progress_measure.py`, no re-tuning):

- **RESOLVED** — topic phrase built entirely from already-taught words
  (`unknown_word_count == 0` from tick 0). **D1: no `SelfConcern` is ever
  minted for it** (nothing left to flag — matches G2's resolved-decays shape).
- **PROGRESSING** — topic phrase with several genuinely unknown words; a
  scripted fake teacher (same sanctioned pattern as
  `tests/test_topic_route_selfheal_migrated.py::fake_ground_topic`, standing
  in for the dictionary/wiki source) grounds one additional word on a fixed
  tick schedule, driven through the REAL `ground_unknowns` loop each tick.
  **D2: a `SelfConcern{kind:'knowledge', content:'progressing'}` IS minted**
  (attended crosses threshold while progress is sustained).
- **INTRACTABLE / noisy-TV analogue** — topic re-drawn each tick from a pool
  of gibberish tokens the fake teacher never grounds, with a random word
  count per tick (`rng.integers(1,5)`) so `unknown_word_count` is itself
  high-variance and never converges — the real-sensor equivalent of the
  original proof's white-noise `obs` stream (irreducible, non-compressible
  surprise), reusing `unknown_word_count` honestly rather than injecting a
  residual directly. **D3 (headline): no `SelfConcern` is minted for it under
  the gated (`mode=0`) rules** — this is the sharpest form of the audit's own
  claim: not merely "interest decays," but **the actual gap-filing decision**
  correctly declines to chase persistent unresolvable surprise.
- **D4 (falsifier, the RAVANA-equivalent comparison):** the identical scene
  re-run with `mode=1` (raw-surprise gating, i.e. what a single-EMA
  prediction-error signal like RAVANA's would do) — bar: a `SelfConcern` IS
  minted for the INTRACTABLE topic under this arm, demonstrating the
  two-timescale gate is load-bearing for the DECISION, not just the interest
  curve, and giving a direct, mechanism-level answer to the audit's central
  claim.
- **D5 (regression / no fabrication):** `unknown_word_count` is computed only
  from `taught_signs()` + real tokenisation; `git diff` on `domains/curiosity_
  topic_ingest.py` and the measure script contain no `set_attr` on any `lp_*`/
  `cn_*` decision key (mirrors the original G4c source audit) — every
  decision stays in the seed rule.

## 4. No-regression bars

- `pytest tests/test_gap_awareness_migrated.py tests/test_learning_progress_
  migrated.py tests/test_self_concern_promote_migrated.py tests/test_self_
  gaps_surfacing_migrated.py tests/test_active_exploration_migrated.py -q` —
  full pass/fail node-id list captured BEFORE and AFTER (paired, not counted).
- `git diff --stat runners/dsl/src/` — empty (no Rust touched).
- Canonical `_native.abi3.so` md5 unchanged across the session.
- The new seed is `self_load_only`, so a `load_all_seeds` full boot must be
  byte-identical to a pre-rung boot on every node the new seed does not
  itself add — verified by re-running the existing gap-awareness/self-concern
  suites unmodified (they never opt in to the new seed) and asserting they
  are green exactly as before.

## 5. Discipline commitments

- Graph-data + existing Terms only for the new rule; no new Rust, no new
  Term, no new node type (`SelfConcern`, `CuriosityHub`, `AttentionItem`,
  `HeldCuriosityParams` all pre-exist).
- `domains/curiosity_topic_ingest.py` is mechanical I/O only (sensor read +
  `run_rules()` call), same class as `domains/doom_active_explore_ingest.py`
  — audited at the end via a `set_attr` grep over its own decision-key list,
  same method `learning_progress_measure.py`'s own `source_audit` used.
- Worktree: `/home/matt/ocelot-curiosity-gap-wiring`, branch
  `curiosity-gap-wiring`, off `main`@`554b07c` (verified current tip at
  worktree-creation time; the brief's assumed `fdf2c53` had already advanced).
- Commit before reporting. Do not merge to `main`, do not push, do not touch
  `docs/research/theory_convergence/` or any of the other forbidden paths
  named in the task brief.

An honest measured NEGATIVE on any demonstration bar is a valid landing and
will be reported as such.
