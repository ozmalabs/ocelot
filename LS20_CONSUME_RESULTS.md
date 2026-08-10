# LS20 FLASH-CONSUME FOLD — RESULTS (block 225000)

**Folds 223000's flash consume-marking onto 224000's object-permanence tracker to
close ls20's trail/consume residual.** Pre-registered in `LS20_CONSUME_PREREG.md`
(committed ALONE, SHA **`1a14cc9ab0`**), BEFORE any number here. Block `225000-225999`
claimed via `seed_claim.py 225000 225999` → **CLEAN** (verbatim `check_claim` in the
prereg; NOT a permanent pytest — avoids the 223000 ledger-inversion mistake).

## LEAD — DID FOLDING THE FLASH CLOSE THE TRAIL RESIDUAL?

**OFFLINE: YES, decisively (the mechanism works).** **LIVE on real ls20: NO — an
honest NULL (the fold slightly hurts).** Both reported straight.

## THE HEADLINE — G-trail-closed: THE ABLATION (+flash vs 224-alone), OFFLINE POWERED

24 seeds, 456 scored steps, all arms paired on IDENTICAL frames + onsets (the eye
runs once per seed), 1000-resample bootstrap 95% CI
(`results/arc_ls20_consume_powered.json`):

| arm (change-set strict-F1) | mean [95% CI] |
|---|---|
| **flash-folded (224 + flash consume)** | **0.8444 [0.8277, 0.8595]** |
| 224-alone (translate only) | 0.7717 [0.7587, 0.7833] |
| random-flash control | 0.7669 [0.7535, 0.7793] |
| blind_all (mark ALL vacated) | 0.6298 [0.6162, 0.6420] |

- **PAIRED `flash − translate` = +0.0727 [+0.0630, +0.0814]** — the CI lower bound
  **> 0**, and the arms are CI-SEPARATED (flash lower 0.8277 > translate upper
  0.7833). **Folding the flash CLOSES the trail residual: yes.** 224-alone leaves
  every dropped trail cell mispredicted (translate erases the whole old footprint to
  field); the fold recovers the flash-localised consumed cells to the discovered
  trail value.

## G-flash-localises-consume — THE FLASH CARRIES THE CONSUME SIGNAL

The flash-localised predicted-consumed set vs the ACTUAL consumed set (F1 of
precision/recall), flash vs the random-flash control:

| localiser | consume-cell F1 [95% CI] |
|---|---|
| **the FLASH** | **0.765 [0.746, 0.782]** |
| random-flash control | 0.037 [0.026, 0.051] |

**CI-separated far above chance** — the flash localises the consumed cells; random
marking does not.

## THE ANTI-CIRCULARITY GUARD — HOW THE FLASH STAYED REALISTIC

The fatal trap is a flash that hands the model the exact consumed set. It does not:

1. **HONESTY BOUND MET — flash consume PRECISION = 0.726 (< 1, NOT an oracle).** The
   flash is a soft luminance GLOW (a blob around the consume), whose brightest onsets
   RING the consumed cells (the dim field around them jumps furthest in dB — the same
   223 phenomenon). The model windows the onset-cluster centroid inward, so the
   flash-localised set is measurably IMPRECISE (a quarter of its cells are wrong).
2. **The RANDOM-FLASH anti-rig null holds:** paired `random − translate` =
   **−0.0048 [−0.0074, −0.0023]** — the same fold with the flash location randomised
   does NOT beat 224-alone (it very slightly hurts). **The win is the flash's
   LOCALISATION, not the marking mechanism** — this gate could have failed and did
   not.
3. **The consumed region VARIES per step** (a per-step interior sub-block), so a
   fixed object-relative offset cannot predict it — the per-step flash is genuinely
   needed.
4. **The consumed VALUE T is DISCOVERED ORACLE-FREE** (the vacated cells that did NOT
   revert to the field), minted into a graph `ConsumeHypothesis` — never handed by
   the flash, never hardcoded.
5. **The flash region alone is insufficient** — it spans FIELD cells; the model MUST
   intersect it with the tracker's VACATED set (the 224 object model). Neither the
   flash nor 224 alone closes the residual — the fold is the composition.
6. **Over-prediction is punished:** `blind_all` (mark ALL vacated cells) scores
   **0.6298 < 0.7717** — marking without the flash's discrimination is strictly worse
   than 224-alone. The flash's precise localisation is what earns the gain.

## G-live (REAL ls20) — THE HONEST NULL, REPORTED STRAIGHT

`arc_ls20_consume_live.py --game ls20-9607627b --steps 300 --n-field 2 --cap 150`
(`results/arc_ls20_consume_live.json`), **n = 120 scored real transitions**,
FRESH API run against the DETERMINISTIC ls20 game (auth verified BEFORE measuring,
`X-Api-Key` from the gitignored `.env`, NEVER printed/committed; RESET returned
`state=NOT_FINISHED`, `available=[ACTION1..4]`):

| metric (CHANGE-SET, REAL frames) | 224-alone | flash-folded |
|---|---|---|
| strict changed-cell F1 | **0.9639 [0.9394, 0.9804]** | **0.9468 [0.9208, 0.9655]** |

- **`flash_folded_beats_224_alone = False`.** The fold does NOT close the real
  ~0.036 residual — it slightly LOWERS the mean (0.9468 < 0.9639), CIs OVERLAPPING.
  **The NULL, reported straight.**
- **224-alone reproduced 0.9639 BYTE-FOR-BYTE** (`mean = 0.963895173453997`) —
  confirming ls20's determinism and that the fold is the only change.
- **WHAT THE FLASH LOCALISED (measured):** the general onset stream fired on
  **129/129 real frames** (rate 1.0), its Argmax onset localising to a CONSISTENT
  region (**rows ≈ 42–47, cols ≈ 29–34** — the same region 223000 reported). The
  real ls20 flash/interaction transients ARE perceivable + localisable by the same
  machinery that works offline.
- **WHY THE OFFLINE MECHANISM DID NOT TRANSFER (honest read):** offline, the consume
  is a per-step trail dropped at the tracked avatar's OWN vacated footprint, and the
  flash rings it — so `vacated ∩ flash` pins the consumed cells. On real ls20 the
  onset localises a FIXED region (rows 42–47) that is not the tracked object's
  per-step vacated cells, so `vacated ∩ flash` marks cells that are NOT the real
  consume → a few false-positive changed cells → the marginal drop. The real ls20
  consume dynamic is richer than the tracked-object-vacated-cell trail the offline
  scenario models; closing the real residual needs the flash region tied to the
  MOVING object (a refined localiser), not the composition alone.
- `final_state = GAME_OVER` at step 129 (win/lose is a SIDE EFFECT of blind
  action-cycling, never optimised), `n_scored = 120`, `n_no_prior_or_untracked = 9`
  (identical bookkeeping to 224's live run). Perception roundtrip: at least one later
  frame did not round-trip through the 216000 pixel eye (content-dependent, as 223
  also found on the longer run) — a diagnostic, never fed to a decision.

## G-graph-native + SOURCE-AUDIT

- **Flash LOCATION = a graph RULE** (`fg_pick_flash`, 223's Argmax-onset attention,
  REUSED unchanged).
- **Consume VALUE = a graph RULE** (`cm_mint`/`cm_confirm`/`cm_revise`,
  `seeds/ls20_consume.json`): a `ConsumeHypothesis` carrying the DISCOVERED trail
  value, grown by observation exactly as `pc_*` grow the shift Hypothesis.
- **The 224 tracker is UNCHANGED** (imported, never modified); the fold reads its
  vacated footprint + the graph shift.
- **The marking RENDER is mechanical adapter I/O** — the same split 224 uses for the
  translate (shift Hypothesis in graph; render in Python).
- **SOURCE-AUDIT PASS** (in the powered JSON): the agent path
  (`ConsumeTracker` + the seed rules) contains NO hardcoded consume table
  (`_CONSUME_TABLE`/`consume_map` = none) and NEVER writes the trail value into a
  grid (`g[...] = TRAIL` = none — only the ARENA/world physics does). The value is
  minted from observation; the location from the flash.

## DISCIPLINE

- **Canonical `.so` md5 `793ce09ed498a749abb79aeaea44b92e` UNCHANGED** (no Rust;
  reuses 223's onset stream + `fg_pick_flash` + 224's tracker/`Transform`).
- **`runners/dsl` diff EMPTY** (`term.rs` included) — no tracked Rust file modified;
  the rung is entirely NEW files.
- **Default-OFF byte-identical:** `ConsumeTracker(mode="translate")` loads NO consume
  rules and predicts EXACTLY the 224 `LiveObjectTracker` (gate
  `test_fold_default_off_is_224_byte_identical`); the consume rules are guarded on
  `consume_on==1` (`test_consume_seed_rules_default_off`). The existing ls20 migrated
  suites (base percell 8 + tracker 4 + planning + mapnav + flash) = **31 passed**
  (unchanged with the fold off).
- **Oracle `rung7_vision_bench`:** BEFORE **214 passed, 10 skipped** == AFTER **214
  passed, 10 skipped** (`results/consume_oracle_before.txt` == `_after.txt`).
- **34-file `per_area_settlement_regression.sh`:** failing NODE-ID SET IDENTICAL
  before/after (**23 ids, 277 passed, 5 skipped**; `results/consume_regress_before_ids.txt`
  == after — the documented 224/223 23-id baseline).
- **New gates:** `tests/test_ls20_consume_migrated.py` **9 passed** (headline ablation,
  flash-localises-vs-random, anti-rig null, over-predict punished, precision<1 honesty
  bound, default-off byte-identical, oracle-free discovered value, source-audit,
  consume-rules-default-off).
- **Integer-native in-frame:** cell values are the integer lattice; the flash is a
  luminance transient the eye reads; the shift + the consume value are cross-frame
  map data.
- **Seed round-trips:** `domains/ls20_consume_seed.py` → `seeds/ls20_consume.json`
  rebuilds byte-stable (source_match).

## SCOPE HONESTY (synthetic-proven ≠ benchmark value — both reported)

The OFFLINE powered ablation proves the fold MECHANISM DECISIVELY: +flash beats
224-alone **+0.073 [+0.063, +0.081]** CI-separated, the flash localises the consumed
cells (0.765 vs 0.037), the anti-rig random-flash null holds, over-prediction is
punished, and the flash is honestly coarse (precision 0.726, not an oracle). The
LIVE half reports the honest NULL: the flash is DETECTED on real ls20 (onset 129/129)
but the fold does NOT close the real residual (0.9468 vs 0.9639) — the real consume
localises to a fixed region, not the tracked object's per-step vacated cells, so the
composition marks the wrong cells. Both reported. The NAMED next lever: tie the flash
region to the MOVING object so `vacated ∩ flash` pins the real per-step consume.

## FILES

- `LS20_CONSUME_PREREG.md` — pre-registration (committed alone, SHA `1a14cc9ab0`).
- `worlds/arc_ls20_consume.py` — `ConsumeArena` (world physics: varying consume +
  luminance glow), `ConsumeTracker` (wraps the 224 tracker + 223 flash attention +
  the consume fold; oracle-free value discovery), the paired-episode driver.
- `domains/ls20_consume_seed.py` → `seeds/ls20_consume.json` — the `cm_*`
  ConsumeHypothesis rules (depends on `ls20_flash`; default-OFF).
- `scripts/arc_ls20_consume_measure.py` — the powered offline ablation + gates + audit.
- `scripts/arc_ls20_consume_live.py` — the bounded LIVE half.
- `tests/test_ls20_consume_migrated.py` — 9 gate tests.
- `results/arc_ls20_consume_{powered,live}.json` — the measured numbers.
