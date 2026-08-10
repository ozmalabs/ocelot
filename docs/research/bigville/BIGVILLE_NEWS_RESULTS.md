# BIGVILLE R21 — THE NEWSPAPER & THE REPORTER: the fourth estate, a second reconstruction channel (block 269000) — RESULTS

Measured build. Pre-registration: `BIGVILLE_NEWS_PREREG.md` (separate commit,
ahead of this one). Every claim below was fixed in the prereg BEFORE any number.

Base SHA (merge-base, origin/main): `59653fd443fb0e0894b5ea59a51bb39402260f4e`
Branch: `worktree-agent-a672dd60963770a51`
Block: **269000–269999**. Spec `BIGVILLE_MOVEMENT_ECONOMY_SPEC.md` §3 R21 + §0.

## Verdict

**All four glass-box gates PASS. `tests/test_bigville_news_migrated.py` — 16/16
green.** Zero new Rust; both seeds `self_load_only`; the canonical shared engine
`.so` is byte-unchanged.

The town gains a **public sphere** — an independent (or captured) written account
of itself, reaching **beyond earshot** (unlike the R19 proximity-bound oral layer),
gated by **literacy** (R18), whose **freedom is a structural lever** (funding +
fear), and which is a **SECOND lossy reconstruction** of events the observer holds
ground truth for — a richer case-reconstruction benchmark than R20's single channel.

## The nine — sorry, EIGHT — decisions are RULES (honest prereg correction)

The prereg's discipline line said *"the nine decisions are the nine seed rule
names."* That was a **miscount** — there are **EIGHT** rules, and the enumerated
rule list in the same prereg (four in `press`, four in `reach`) is the correct one.
The source-audit gate asserts the eight names. No mechanism changed; only the
prereg's summary count was off by one. Recorded here rather than edited in place.

Four in `bigville_news_press.json`: `np_reporter_writes`, `np_capture_suppresses`,
`np_paper_prints`, `np_clerk_records`.
Four in `bigville_news_reach.json`: `np_witness_knows`, `np_reader_learns`,
`np_count_informed`, `np_coalition_forms`.

## Gate results (read off `results/bigville_news/summary.json`)

### G-paper-propagates-beliefs (mass channel) + the literacy divide

One event (truth=60), reporter_bias=+10 → the paper renders **70**.

| resident | literate | witnessed | reads paper | knows_flag | belief |
|---|---|---|---|---|---|
| lit_far | yes | no | yes | **1** | **70** (the paper's biased rendering) |
| ill_far | no | no | yes | **0** | 0 (oral layer only — R18 divide) |
| ill_wit | no | yes | yes | **1** | **60** (true, DIRECT — R19 proximity) |

- **The literate non-witness learns a distant event FROM the paper** — belief
  propagation **beyond earshot** (R19 is proximity-bound; the paper is not). The
  belief it acquires is the paper's **bias-shaped** rendering (70), NOT the ground
  truth (60) — non-local knowledge is second-hand and biased.
- **The illiterate non-witness stays ignorant** even though the paper printed —
  the R18 informed/uninformed divide. Literacy, not access, is the gate.
- **The illiterate WITNESS knows the true value directly** — the oral/direct layer
  is open to all.
- **ABLATION (load-bearing):** `paper.active=0` → nothing prints → the literate
  non-witness stays ignorant (`knows_flag=0`); `active=1` → learns. **The paper is
  load-bearing for non-local knowledge.**

### G-free-vs-captured-press (HEADLINE — a structural lever)

Damaging story (John's corruption), reporter_bias=+10:

| paper | event | written | suppressed | printed | reader learns |
|---|---|---|---|---|---|
| independent (captured=0) | damaging | 1 | 0 | **1** | yes |
| captured (captured=1) | damaging | 1 | **1** | **0** | no |
| captured (captured=1) | ordinary (non-damaging) | 1 | 0 | **1** | yes |

- The reporter **WROTE** the story in every case (occlusion is separate). An
  **independent** paper (sells copies for coin) **prints** the corruption; a
  **captured** paper (bankrolled/intimidated by John/Scrooge) **launders/omits**
  it — `suppressed=1`, `printed=0` — and readers stay ignorant of the corruption.
- **Press-freedom counterfactual:** flip `captured 1→0` on the SAME damaging event
  → the suppressed story **prints**. Freedom is the structural lever, emergent from
  the funding/power edges.
- **CONTROL (capture is TARGETED):** a captured paper still prints an ORDINARY
  story — it launders only the story that implicates its patron, not the whole
  paper.

### G-second-reconstruction-channel (the benchmark, ties §0)

One event, truth=60; reporter_bias=+15 (attack), clerk_bias=−25 (protect):

| channel | rendering | error vs truth | bias direction |
|---|---|---|---|
| ground truth (WE hold) | **60** | 0 | — |
| the paper (reporter) | **75** | 15 | **overstates** (attacks the council) |
| the noticeboard (clerk) | **35** | 25 | **understates** (protects the council) |

- **Three DISTINCT renderings of ONE event**, both scoreable against the ground
  truth we hold, with **DIFFERENT bias profiles**: the reporter overstates
  (attack), the clerk understates (protect). This is a richer
  case-reconstruction validation than R20's single channel — two independent lossy
  maps of the same closed room, both gradeable.
- A paper-only learner holds the biased **75**; a witness holds the true **60**.
- **R19 occlusion tie:** a reporter who did NOT witness the event writes NO story →
  nothing prints → readers ignorant. The reporter reports only what was
  witnessed/told.

### G-paper-feeds-collective-action

Shared damaging grievance, 3 literate non-witness readers, quorum=2:

| paper | informed | quorum | coalition formed |
|---|---|---|---|
| independent | **3** | 2 | **1** (forms) |
| captured | **0** | 2 | **0** (no coordination) |
| independent, 1 reader only | **1** | 2 | **0** (below quorum) |

- A shared grievance becomes **COMMON KNOWLEDGE** via the (independent) paper →
  enough residents hold it → the **coalition forms**. Information is the substrate
  of collective action.
- **Capture the paper → the grievance never becomes common knowledge** → the
  informed count stays at 0 → no coalition. The coordination is suppressed by
  suppressing the information.
- **CONTROL:** the COUNT binds, not the mere existence of the paper — 1 informed
  reader below a quorum of 2 → no coalition.

## Discipline ledger (all held)

- **PREREG-FIRST** — `BIGVILLE_NEWS_PREREG.md` + the seed-claim output (CLEAN,
  269/269000–269999) committed in a separate commit ahead of this build.
- **Additive-only, ONE prefix `bigville_news_`** — new files only; `git diff
  59653fd443` shows **zero** modifications to any tracked file outside the prefix.
  R20/R18/R19/R11 imported read-only as concepts.
- **NO new Rust** — `git diff 59653fd443 -- runners/dsl` is **empty** (incl.
  `term.rs`). The two seeds compose only known DSL Terms
  (`And`/`Eq`/`Gte`/`Plus`/`Sum`/`Neighbours`/`Attr`/`Var`/`Lit`).
- **Own-engine provenance** — `engine_provenance().source_match == "shared"` ∈
  {own, shared}. No pinned `.so` md5 in any test (lesson 7b).
- **Canonical shared `.so` SACRED** — md5 of
  `runners/dsl/python/substrate_rs/_native.abi3.so` START==END==
  `fd82dc2978dbb055496dd82390ac2ebe`. No `.so` committed.
- **Gates run INLINE** — `test_bigville_news_migrated` 16/16;
  `test_failure_baseline_migrated` 11/11; `test_engine_provenance_migrated` 7/7.
- The ~43-min `per_area_settlement_regression.sh` / `rung7_vision_bench.sh` were
  **NOT** run — an additive `self_load_only` rung loaded only by its own adapter
  cannot regress any other suite (2026-07-29 directive).

## Honest residuals

- **Prereg count typo** — "nine decisions" should read "eight"; the enumerated rule
  list and the source-audit gate are correct at eight (see above). Recorded, not
  hidden.
- **The noticeboard's second channel is re-modelled locally** (`np_clerk_records` +
  a `Minutes` node) inside the news substrate so both renderings score against ONE
  ground truth in ONE fixpoint. It re-uses R20's CONCEPT (the clerk protects the
  council), not R20's seed graph — a deliberate isolation choice.
- **One event per world instance** (fresh world per scenario, R20 style);
  `Resident.witnessed` is the per-event proximity outcome. Multi-event per-resident
  belief is out of scope for this rung.
- **The reporter's bias is a fixed ingest parameter**, not derived from a
  psychology sub-model. Deriving the bias magnitude endogenously (from the
  reporter's `w_supergraph` / spite, the 234 held≠stated machinery) is a future
  rung.
- **The paper→belief propagation is single-hop** (reader reads the paper directly).
  Onward gossip re-transmission (an illiterate learning from a literate neighbour
  who read the paper) is not modelled here — it would compose the R19 oral layer
  with this channel, a future rung.
