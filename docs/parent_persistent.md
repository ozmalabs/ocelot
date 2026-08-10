# The PERSISTENT, BOUNDED parent — save/resume + bank cap + LOSO probe

**Status: built + verified (short run) + long run launched. NOT committed (working tree).**

The long `--parent-only` A/B run (`scripts/parent_speech_loop`) was EPHEMERAL and
UNBOUNDED: both regimes start fresh (no save/resume), and the per-word exemplar bank
had NO cap. A ~40 min run banked ~6480 espeak exemplars and was reaped (OOM) with
**everything lost** — nothing persisted. This work fixes that by integrating the
PARENT into the PERSISTENT main loop and adding the cross-speaker (LOSO) probe so the
long run also answers the speaker-invariance question.

---

## (1) What was built

`scripts/parent_persistent_loop.py` — the PARENT integrated into the persistent
self-directed loop (reuses `self_directed_speech_loop`'s save/resume, front-end
self-design + effect-gate, and meta-monitor; reuses `parent_speech_loop.ScaledWorld`
for the larger TVTropes WORD grid).

- **Parent integrated (decisions stay graph Terms/Rules).** The ZPD curriculum pick
  (`P.ZPD_PICK_TERM`), ostensive naming (restricted competitor set), recasts, the
  register gate (`P.REGISTER_GATE_TERM`, IDS→ADS), and the stage gate (gradual
  release; mastery = the agent's own held-out rate) all run exactly as in the A/B
  harness. A free-play fraction (default 0.25) keeps self-directed exploration.
- **SAVE/RESUME via `graph_to_dict`.** The loop loads any existing save on boot
  (front end + curriculum + lexicon + capped banks), reinstalls the parent
  idempotently, and saves every `2 * report_every` seconds plus a final save. The run
  survives kills and persists across runs — **verified below**.
- **BANK CAP — the memory bound.** `W.cap_bank(substrate, cap)` (added to the world
  adapter) keeps the **N most-recent** exemplars per `(word, cell)` Concept (Exemplar
  node ids are monotonic, so highest ids = most recently banked) and drops the rest.
  Default **cap = 200 per word**. The cap runs every report, before every save, and
  before the final save — so both live memory and the persisted graph are bounded.
  Recency keeps the freshest clips, which under the IDS→ADS gate are banked closest to
  the ADS test register.
- **LOSO PROBE — cross-speaker.** Alongside the existing clip-holdout FSDD probe
  (seen speakers, held-out clips), a leave-one-speaker-out probe holds out **whole
  FSDD speakers**. The run world's FSDD pool is restricted to TRAIN speakers
  (`LosoWorld` uses `W.fsdd_index_for(train_speakers)`), so the agent **never banks a
  held-out speaker's clip**; the LOSO probe (`build_loso_probe`) is built only from
  the held-out speakers' clips. Each report prints BOTH `digit|fsdd|en` (seen-speaker)
  and `digit|fsdd|en LOSO` (cross-speaker, the ~0.44 wall).

The FSDD corpus has six speakers (`george, jackson, lucas, nicolas, theo, yweweler`);
default LOSO holds out the last (`yweweler`), 5 train / 1 held-out. The split is
configurable via `--loso-speaker` (repeatable).

### Architecture / donkey boundary (CLAUDE.md)

- The bank cap and LOSO probe construction are **world-adapter banking/probe
  mechanics** (a fixed-capacity store + a speaker-scoped clip pool), not decisions —
  the same class of mechanical store operation as `bank_exemplar` /
  `prune_stale_banks`. No new Python decision logic; no `if`/`else` over graph state
  chooses what to drill, guess, or learn.
- The PARENT speaks / names / recasts / picks-level / gates-register, and **never
  recognises**. The agent's `blind_guess` over its own exemplars is the recognizer.
- BOTH held-out probes are **full-lexicon** (`restrict_to=None`) and ungameable; the
  LOSO probe's speakers' clips are **never banked**.

---

## (2) SHORT verify — runs, SAVES, RESUMES, bank bounded, BOTH probes report

A fresh 70 s run then a 35 s resume (`--bank-cap 50 --lexicon-size 12`), 30 s reports:

**Fresh run** (`--fresh`): boots, learns, saves a final 233-node graph.
- `[loso] held-out speakers (never banked): ['yweweler']; train: [...5 speakers]`
- `[probes] 108 clip-holdout probes; 40 LOSO (cross-speaker) probes`
- learns: `digit|espeak|en 0.900`, `word|espeak|en 0.500 → 0.750`; gradual release
  advanced to stage 2; front-end self-modified (`+formant_relation`).
- BOTH probes report every cycle, e.g. `digit|fsdd|en LOSO held-out 0.000
  (cross-speaker; seen-speaker 0.000)`.

**Resume run** (same save, no `--fresh`): `[load] resumed from ...` — and the FIRST
report immediately shows the previously-learned state instead of zero:
`digit|espeak|en 0.900`, `word|espeak|en **0.917**` (up from 0.750 at end of run 1),
`digit|noise|en 0.700`, `word|noise|en 0.250` now climbing. **Learning persisted
across the stop/restart.**

**Bank cap is bounded — verified directly.** Banking 300 exemplars for one word then
`cap_bank(cap=150)` → prunes 150, total 150; banking +100 more → 250; re-cap → flat
at 150, keeping the highest-id (most recent) exemplars. Memory is flat at the cap, not
unbounded.

**Required suites green:** `test_stt_pipeline`, `test_perception_self_assessment`,
`test_process_meta_assessor`, `test_gap_guidance`, `test_frontend_effect_gate` — 36
passed.

---

## (3) The LONG run (detached)

```
setsid bash -c 'PYTHONUNBUFFERED=1 python -m scripts.parent_persistent_loop \
    --seconds 14400 --report-every 120 --bank-cap 200 --lexicon-size 40 \
    --save /tmp/parent_persistent_save.json --fresh \
    > /tmp/parent_persistent_run.txt 2>&1'
```

Launched detached (setsid → its own session SID, survives session exit), 4 h budget,
parent on, bank cap 200, 40-word lexicon, LOSO holding out `yweweler`. Confirmed:

- **Alive + saving + bounded.** `ps` shows the process in its own session; first save
  landed at t≈240 s: `[save] 1054 nodes, bank 951 -> /tmp/parent_persistent_save.json`
  (an 82 MB graph — raw-audio exemplars), and the run continued to t=246 s and beyond.
  220 clip-holdout + 40 LOSO probes built. The bank is bounded by the per-word cap
  (espeak digit ≈ 44 exemplars/word, well under 200; the cap engages as any single
  word/cell saturates — proven flat-at-cap in §2).
- **Live trajectory so far** (early, gradual release still on the easy stages):
  `digit|espeak|en 1.000`, `word|espeak|en 0.750` and climbing; gradual release has
  advanced to stage 2 (espeak + noise + words open). `digit|fsdd|en` and
  `digit|fsdd|en LOSO` are both still 0.000 — the FSDD stage is the LAST to unlock
  (the stage gate opens `espeak → piper → noise → fsdd` only on measured mastery of
  the prior stage), so the FSDD/LOSO cells have not yet been taught at this point.

### Memory note (honest)
The steady-state BANK is bounded by the cap, but the per-report WORKING SET spikes
(RSS ~0.5 GB observed during a report) because each report re-extracts all 220
clip-holdout + 40 LOSO probes plus the bank through the current front end into the
per-exemplar feature cache; the cache is invalidated/rebuilt per front-end change.
This is transient and bounded by `(probes + bank) × front-end width`, not the
unbounded exemplar growth that OOM'd the old run — but at very large lexicons/banks
the report cost (and its transient cache) is the thing to watch, not the persisted
bank. The persisted graph is bounded by the cap.

---

## (4) Headline (honest)

**The persistence/bound/probe machinery is done and proven; the cross-speaker
ANSWER accrues over the 4 h run.** Because gradual release unlocks FSDD LAST (only
after espeak/noise/words are mastered), the seen-speaker and LOSO FSDD rates stay
0.000 in the early reports and begin to move only once the FSDD stage opens. The
definitive seen-vs-LOSO trajectory is captured live to `/tmp/parent_persistent_run.txt`
(each report prints both `digit|fsdd|en` and `digit|fsdd|en LOSO`), and the final
`VERDICT` block states it directly.

The clean question either way: does the parent's teaching lift the CROSS-SPEAKER
(LOSO) wall, or only the seen-speaker recognition? The LOSO probe holds out whole
speakers whose clips are **never banked**, so a LOSO climb is genuine
speaker-invariance; a flat LOSO with a climbing seen-speaker rate means the teaching
grounds only the banked speakers (the expected ~0.44 cross-speaker wall). Both probes
are full-lexicon and ungameable, so neither answer can be inflated by teaching.

**Prior expectation (from the committed FSDD result, MEMORY):** seen-speaker FSDD
reaches ~0.75–0.90 under teaching, while the cross-speaker wall sits ~0.44 — so the
likely honest finding is that the parent lifts SEEN-speaker FSDD well above LOSO, i.e.
teaching crosses seen-speaker recognition but the cross-speaker invariance wall is a
deeper-than-front-end / representation residual the parent's prosodic register
matching cannot remove (the parent speaks espeak; FSDD-real is human voice — a SOURCE
mismatch). The LOSO probe now MEASURES exactly this gap on every report.

## Reproduce

```
# short verify (fresh -> save -> resume -> bounded -> both probes):
python -m scripts.parent_persistent_loop --seconds 70 --report-every 30 \
    --bank-cap 50 --lexicon-size 12 --save /tmp/pp_verify.json --fresh
python -m scripts.parent_persistent_loop --seconds 35 --report-every 30 \
    --bank-cap 50 --lexicon-size 12 --save /tmp/pp_verify.json      # resumes

# the long detached run:
setsid bash -c 'PYTHONUNBUFFERED=1 python -m scripts.parent_persistent_loop \
    --seconds 14400 --report-every 120 --bank-cap 200 --lexicon-size 40 \
    --save /tmp/parent_persistent_save.json --fresh \
    > /tmp/parent_persistent_run.txt 2>&1'
```
