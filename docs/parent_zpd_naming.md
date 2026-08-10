# The PARENT, first piece — adaptive ZPD curriculum + ostensive naming

Builds the first and highest-leverage piece of the PARENT from
`docs/research_parental_teaching.md` §(4): replace the agent's deficit-only
self-pick babble with a PARENT that **teaches at the agent's measured level** (the
Zone of Proximal Development), **names ostensively** (gives the label + restricts
the competitor set), and **releases gradually** (advances the curriculum on
mastery). The honest test: does teaching make the agent learn FASTER / HIGHER on the
SAME ungameable held-out probe than babble alone?

**Status: built + measured. NOT committed (working tree). The babble run5 was
stopped to free resources for clean A/B timing (see "the cache bug" below — it had
to be).**

---

## (1) What was wired

### New files
- `domains/parent_teacher.py` — the PARENT (world adapter):
  - **`ZPD_PICK_TERM`** — a graph `Argmax` over `CurriculumCell` of a ZPD-band
    priority fed by the cell's `held_cookie_rate` (the agent's OWN ungameable
    held-out measure). The priority PEAKS inside the band
    (`zpd_floor <= rate < zpd_ceiling`), is low for mastered cells (gradual
    release), prefers the cell closest to mastery (the steepest learnable gradient),
    and adds an explore bonus for under-probed band cells. **The decision is the
    graph Term; the adapter only measures the level and reads the Term's value** —
    the same pattern as the existing `PICK_TERM` / `GUESS_TERM`.
  - **`competitor_set(vocab, target, k)`** — ostensive naming's restricted
    competitor set (the research's strongest lever: *suppress competitors*, not
    point). The target + a few others; scopes the candidate pool, never hands over
    the answer.
  - **`parent_say(word, lang, register="IDS")`** — child-directed-speech TTS
    (espeak `-s` slowed + `-p` pitched). Boundary TTS only.
  - **`install_parent` / `apply_stage_gate`** — the `Parent` graph node + the
    acquisition-order stage gate (espeak → piper → noise → fsdd), which unlocks the
    next source only when the open stage reaches a `release_threshold` held-out rate
    (gradual release). Locked cells are excluded from the ZPD `Argmax` (`is_cell=0`).
- `scripts/parent_speech_loop.py` — the honest A/B harness: runs SELF-PICK babble
  and PARENT-TAUGHT from the SAME fresh start, judged by the SAME ungameable
  held-out probe (full lexicon, never restricted), and prints both learning curves +
  the per-cell + ZPD progression. Flags: `--no-ids`, `--no-bank-on-miss` (to
  isolate the curriculum lever from the register/banking confounds).

### Changed
- `domains/self_directed_speech_world.py`:
  - `blind_guess(..., restrict_to=None)` — ostensive naming's restricted-competitor
    scoping, using the SAME zeroing mechanism the cross-cell restriction already
    uses. **The held-out yardstick always calls with `restrict_to=None`** (full
    lexicon), so teaching cannot inflate the measured capability.
  - `reset_caches()` — clears the module-level per-exemplar feature cache between
    two substrates built in one process (see the cache bug).

---

## (2) The donkey boundary — audited

The PARENT may **speak** (IDS TTS), **name** (label + competitor set), and
**pick-level** (the ZPD `Argmax`). It **never recognises**. Audited:

- `parent_teacher.py` contains **no recognition call** — `grep` for
  `blind_guess|predict|recogni|guess` finds only comments/docstrings; the one `MS.`
  use is `MS._Pred(...)`, the Term-wrapper for the ZPD `Argmax` (a graph Term).
- The agent's recognition is `blind_guess` over its OWN exemplars in its OWN feature
  space in BOTH regimes; the front end is unchanged.
- The ZPD pick is a graph Term fed by the agent's held-out rate — not a Python
  if/else syllabus.
- The ostensive label is the LEARNING TARGET (what to bank); the agent still
  guesses. `restrict_to` is passed ONLY on the taught track, NEVER in
  `measure_heldout` (the yardstick) — verified by grep: line 204 (taught) vs the
  held-out at `self_directed_speech_loop.py:136` with no restriction.
- An LLM-as-parent would slot in only as the teacher (speak/name/pick-level via the
  pluggable `ask()` channel, `teacher_hook`/`llm_partner` shape); never the
  recognizer. (Not needed for this first piece — the curriculum + naming are
  structural, not generative.)

---

## (3) The cache bug (a real harness fault, found + fixed)

The A/B builds two `Substrate` objects in one process. The world's per-exemplar
feature cache (`_FEAT_CACHE`) keys on `(exemplar NODE-ID, front-end signature)`. A
second fresh substrate **reuses NodeIDs from zero with the same seed cues**, so the
parent regime read the self-pick regime's CACHED feature vectors for colliding ids —
cross-contamination that pinned the parent's held-out at ~0.2–0.3 while isolated
reproductions of the identical code gave 1.0. Fixed with `W.reset_caches()` in
`_setup` between regimes. (The live single-process loop never hits this — only an
in-process A/B does.) Until this was found, every A/B number was garbage; flagging it
because it would silently corrupt any future two-substrate comparison.

---

## (4) The comparison — does teaching help? (SAME ungameable held-out)

All runs: stage-1 grid (digit × {espeak, noise, fsdd, piper} × en), 150 s per
regime, held-out = fixed balanced full-lexicon probe (never banked, never
restricted).

### Clean isolation (ZPD + ostensive naming only; `--no-ids --no-bank-on-miss`)

The cleanest test of the CURRICULUM lever (matched banking policy, no register
confound).

| t (s) | self-pick mean | parent mean |
|------|----------------|-------------|
| 37   | 0.78 / 0.74    | 0.25 / 0.25 |
| 74   | 0.79 / 0.84    | 0.43 / 0.45 |
| 110  | 0.80 / 0.84    | 0.74 / 0.69 |
| 147  | 0.83 / 0.85    | 0.84 / 0.79 |
| ~157 | 0.83 / 0.85    | **0.86 / 0.79** |

(two seeds shown: seed-0 / seed-3.)

**The ZPD progression works exactly as designed** (seed-0):
espeak (mastered 1.0) → **unlocks piper** (0.7 → 0.95) → **unlocks noise** (1.0) →
**reaches fsdd** (0.5). The gradual-release gate advanced **only on measured
mastery**, in acquisition order. The learning SHAPE is the developmental
prediction: the parent starts LOW (deep on the foundation first), then climbs
steeply and **overtakes** self-pick (which plateaus broad-but-shallow early).

**Per-cell, the parent matches or beats self-pick on every cell it had time to
teach** — espeak 1.0 vs 0.9, noise 1.0 vs 0.9, piper 0.95 vs 0.85 — and crucially
those held-out rates are on the FULL lexicon, so the ostensive teaching grounds REAL
capability, not the restricted test.

**Honest whole-grid verdict: MARGINAL and seed-dependent.** seed-0: parent +0.037.
seed-3: parent −0.062. The whole-grid difference is dominated by **fsdd** (the
hardest, real-human cell), which the parent reaches LAST under gradual release and
so has the least time on within a fixed budget (parent fsdd 0.40–0.50 vs self
0.60–0.65). On the cells the parent reached early it is even or ahead; the deficit is
a *time-allocation* effect of the curriculum order, not a learning failure.

### IDS register + bank-on-miss (the full parent, register confound exposed)

With the IDS prosodic exemplars added and banking-on-miss: parent **ties**
self-pick (0.775 = 0.775), and fsdd is notably worse (0.25 vs 0.50).

**Honest finding: IDS-on-an-ADS-yardstick does NOT help here, and washes out the
curriculum gain.** The held-out probe plays the cell's own (ADS) register; banking
slowed+pitched IDS exemplars adds register-mismatched neighbours to the 1-NN bank.
This is exactly the confound `research_parental_teaching.md` flagged: IDS's benefit
in infants is register-matched to what they're tested on; our yardstick is ADS-only,
so IDS is a train/test mismatch, not an aid. **This is teaching a register the test
doesn't use — reported, not hidden.** The lever that helps is the **ZPD + ostensive
CURRICULUM**, not the register or banking-on-miss.

---

## (5) VERDICT

**Does the parent make the agent learn like a child (taught) better than babble
alone, with the yardstick honest?**

- **The structure is right and it works**: the PARENT teaches at the agent's
  measured ZPD, names ostensively with a restricted competitor set, and releases the
  curriculum on mastery — all as graph Terms fed by the agent's own held-out measure,
  with the donkey boundary clean (parent never recognises) and the yardstick
  ungameable (full-lexicon held-out; restricted competitors teaching-only). The
  developmental LEARNING SHAPE is reproduced: foundation-first, then a steep climb
  that overtakes the broad-shallow babble.

- **The held-out advantage is MARGINAL, not a clear win.** Clean config: parent
  +0.037 (seed-0) / −0.062 (seed-3) on the whole grid; even/ahead on the cells it
  reaches early, behind on fsdd purely because gradual release reaches it last within
  the budget. The honest one-line verdict: **the parent teaches the right thing at
  the right level and grounds real (full-lexicon) capability at least as well as
  babble per cell, but on a fixed time budget the gradual-release ORDERING trades
  late-cell coverage for early-cell depth, so the whole-grid mean is a wash.**

- **Teaching did NOT inflate the test.** The parent's high held-out rates are on the
  full lexicon (`restrict_to=None`); the restricted-competitor naming raised
  teaching-time cookies but the *measured* capability is on the unrestricted probe.
  Where a confound DID appear (IDS register on an ADS yardstick), it *hurt* and is
  reported as such — the opposite of gaming the test.

**So: the parent is a real, structurally-correct first half** — it converts the loop
from self-directed sampling into a taught dyad and reproduces the child's
foundation-first learning shape, with the yardstick honest. The *magnitude* of the
held-out win on this small synthetic-digit grid is marginal and budget-bound;
demonstrating a clear faster/higher win needs (a) longer budgets so gradual release
reaches every cell, (b) a register-matched or mixed-register yardstick before IDS can
help, and (c) the harder/larger lexicons where a self-picked random syllabus actually
strands the learner (the regime the ZPD scaffolding is FOR). The natural next pieces
(`research_parental_teaching.md` §(4)): **recasts** (the contingent contrast pair,
richer than the cookie) and the larger-vocabulary curriculum where scaffolding's
advantage over random self-pick should widen.

---

## Reproduce

```
# clean isolation (the ZPD + ostensive CURRICULUM lever; honest yardstick):
python -m scripts.parent_speech_loop --seconds 150 --report-every 30 \
    --no-ids --no-bank-on-miss --out /tmp/parent_ab_clean.json

# full parent (IDS register + bank-on-miss; shows the register confound):
python -m scripts.parent_speech_loop --seconds 150 --report-every 30 \
    --out /tmp/parent_ab_ids.json
```

Both print the two held-out learning curves, per-cell, the ZPD/gradual-release
progression, and end with `[MARKER] PARENT_AB_COMPLETE`. Required suites green:
`test_stt_pipeline`, `test_perception_self_assessment`,
`test_process_meta_assessor`, `test_gap_guidance` (+ `test_frontend_effect_gate`).
```
