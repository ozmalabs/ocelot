# A PROMOTED REFUSAL — PRE-REGISTRATION

> Written and committed BEFORE any number. Successor to
> `VISION_REFUSAL_REPRESENTABLE_RESULTS.md` ("a rule can finally HEAR a refusal
> and MINT a `Residual`"). That rung built HEAR + MINT and named the successor:
> **PROMOTE** (`Residual → SelfConcern → (human-gated) StandingConcern`) and
> **GROUND** (route a `Residual`'s content through the teacher). This rung closes
> the loop the whole arc has circled: *"matches nothing I hold" → "file it as
> something to resolve" → (human-gated) "work on it".*

- **worktree:** `agent-a4321ae58a0e75618` — the name I actually see;
  gamma-substrate at
  `.../.claude/worktrees/agent-a4321ae58a0e75618/research/experiments/gamma-substrate`.
- **base SHA:** `da113ec4af` (contains `ArgminRefusal` idx 180 +
  `refusal_representable` + the parallax + eye-view carves — verified present).
- **engine (§10):** built in-tree by `scripts/engine_build.sh` →
  **`7041d2e6a7dd`** (`source_match: own`; byte-identical hash to the refusal
  rung's changed engine — same Rust source, ArgminRefusal at 180). THIS RUNG
  ADDS **NO RUST** — Term enum index **181 ALLOCATED and UNUSED**; the build is
  seed data only. Provenance re-verified after measurement.
- **oracle (§9):** `bash scripts/rung7_vision_bench.sh` (data/ symlinked, §10.2)
  BEFORE and AFTER. My seed is DEFAULT-OFF / additive (inert on any graph without
  the `attends`+`has_residual` edges — no committed seed makes them), so §9
  requires 222/0 unchanged.
- **seed_claim (§3 clause 8), verbatim at prereg time:**
  ```
  SEED CLAIM 120000-120999: CLEAN -- no collision DETECTED.
    Scope: 825 files with seed sinks; 518 UNRESOLVED sink sites tree-wide (counted, not discarded).
    CAVEAT 1 -- THE UNIT IS THE SEED INTEGER, not consecutive draws...
    CAVEAT 2 -- THIS TOOL UNDER-REPORTS BY DESIGN (7 declared blind spots...)
  ```
  Confirmatory tie-rate seeds draw **120000–120199** (LITERAL, in-block). A
  post-run re-check is recorded in the results.

---

## 1 — WHAT IS BUILT (seed data only)

**`seeds/residual_promote.json`** (v1.0.0, depends on `core`), TWO thin rules —
the composition onto the EXISTING gap-awareness / `SelfConcern → StandingConcern`
spine (`seeds/gap_awareness.json`, `scripts/jabberwock_daemon.py::promote_self_concern`).
Nothing else is rebuilt.

1. `promote_residual_to_self_concern` — **THE LOOP CLOSURE.** Match
   `[["agent","attends","h"],["h","has_residual","res"]]` (the agent attends a
   source `h`; `h` holds a `Residual` `res` — the shared-var 2-edge join, reusing
   the `h -has_residual-> res` edge `refusal_query_mints_residual` ALREADY mints,
   with NO edit to that seed). Where: `res.promoted != 1` (mint-once) AND a
   content-dedup guard (`Not Exists` a `SelfConcern` whose `content` equals this
   residual's — the SAME guard shape every gap rule carries). Effects: set
   `res.promoted=1`; mint `SelfConcern{status:'noted', source:'residual',
   kind:'residual', content:<a readable phrase built from res.kind>,
   residual_kind:<res.kind>}`; `agent -has_self_concern-> sc`; `sc -about_residual-> res`.
   The SelfConcern is the SAME node shape the human-gated `promote_self_concern`
   consumes, and DISTINCT from every ordinary concern (source='residual',
   kind='residual', the `about_residual` edge no other concern carries).

2. `perception_hole_mints_residual` — **making the eye-view HOLE ACTIONABLE.**
   Match `[["agent","attends","field"]]`. Where: `field.uncarved_count > 0` (a
   `VisionField` the eye holds whose carve left un-carved HOLE cells — the eye-view
   rung's 9 right-edge cells) AND mint-once (`field.hole_residual_minted != 1`).
   Effects: set `field.hole_residual_minted=1`; mint `Residual{kind:'uncarved_hole',
   source_count: field.uncarved_count}`; `field -has_residual-> res`. This fires on
   REAL structure (a genuine un-carved region), NOT on a rare tie — and does NOT
   fire on the FLAT space-constancy case (`uncarved_count=0`: every cell is the
   one reference group; correct "nothing here" is not a residual).

The adapter writes `field.uncarved_count` from the recovered held carve
(mechanical I/O — reading the sensor's un-carved count, the eye-view rung's
recovery); the RULE decides it is a residual.

---

## 2 — THE DISCRIMINATOR (pre-registered, two-sided)

**CONFIRM** (all must hold):
- **C1 PROMOTE, perception (load-bearing):** the eye-view HOLE
  (`uncarved_count>0`) → `perception_hole_mints_residual` mints EXACTLY ONE
  `Residual{kind:uncarved_hole}` → `promote_residual_to_self_concern` files
  EXACTLY ONE `SelfConcern{source:residual}` linked `about_residual`, in ONE
  `run_rules` fixpoint. A clean full carve (`uncarved_count=0`) and the FLAT
  space-constancy case mint ZERO.
- **C2 PROMOTE, refusal:** a `refusal_probe` with no unique extremum →
  `refusal_query_mints_residual` (existing) mints a `Residual{kind:no_unique_extremum}`
  → the SAME promote rule files a DISTINCT `SelfConcern` (distinct content, because
  distinct kind). Both residual sources reach the spine through ONE promote rule.
- **C3 REACHES THE SPINE (human-gated):** the minted `SelfConcern` is accepted by
  `promote_self_concern(adapter, id)` → mints `StandingConcern{status:'pending'}`
  with `promoted_to` linkage. I FILE the SelfConcern and STOP at the gate; the
  promote call IS the human step, invoked explicitly to prove reachability.
- **C4 DEDUP / NO FLOOD:** two same-kind residuals → EXACTLY ONE SelfConcern (the
  content-dedup guard); two distinct-kind residuals → TWO. Re-running `run_rules`
  does not add more (mint-once). CLAUDE.md records gaps must be deduped by content.
- **C5 DEFAULT-OFF byte-identity (§9):** the seed loaded onto a committed graph
  with no `attends`/`has_residual`/`refusal_probe` edges changes nothing; oracle
  222/0 BEFORE and AFTER.
- **C6 GROUND:** a knowledge-style `Residual` whose content names an unknown term,
  routed through `agent.ground_unknowns(<term>)`, exercises the documented per-word
  teacher loop — grounding the term (or, offline, queuing the inquiry the loop
  falls back to). Honest scope: the PERCEPTION hole heals by RE-SAMPLING (the
  eye-view rung's named lever), NOT by dictionary grounding — dictionary GROUND is
  for content/knowledge residuals; I will not claim the hole is dictionary-groundable.

**FALSIFY** (either kills it):
- **F1 FIELD-BOUNDARY ERASURE ONE LEVEL UP:** the minted `Residual` cannot reach
  the promote rule — the promote rule's match/where cannot bind a genuinely-minted
  Residual (a second `ArgminRefusal`-class erasure, one level higher). If so I
  report WHERE the boundary is and stop, exactly as the ArgminUnique rung reported
  its C1 erasure.
- **F2 FLOOD / DOUBLE-FILE:** the loop files more than one SelfConcern per distinct
  residual content, or re-fires each pass (the dedup/mint-once guards fail).

---

## 3 — CHARACTERISE FIRST: THE REAL-SCENE WTA TIE RATE (decides arm / don't-arm)

The refusal rung named "arm the 16 existing `Eq(node, sel)` WTA sites (one
`Eq(sel, RefusalMark)` read each)" as future work, **priced by the still-unmeasured
real-scene tie rate.** The ArgminUnique rung measured **0.0453%** on the bench and
said explicitly it is NOT a natural-scene statistic (201/201 ties came from
calibration gates installing IDENTICAL ideal cells).

**Measurement.** The load-bearing real-scene WTA is `mo_dominant`
(`vision_motion_group.json`): an **Argmax over motion-group member counts** — the
reference frame is the LARGEST common-fate group. I run the parallax carve (real
SAD sensor `vector_field`, the parallax rung's `parallax_char`) on **real depth
scenes**, group by common fate, and at the dominant-group Argmax count the fraction
of scenes with a **NON-UNIQUE largest group** (a tie: the max member count achieved
by ≥2 groups). I ALSO measure the finer per-cell nearest-surface assignment tie
(a cell whose velocity is EXACTLY equidistant to ≥2 surface mean-velocities — the
"cannot assign this cell" question).

- **statistic:** tie fraction over scenes (dominant-group Argmax) and over cells
  (nearest-surface assignment), with 95% Wilson CI.
- **n:** 200 fresh seeds **120000–120199**, unit = SEED. (This is a NULL
  characterisation; n is set for a tight upper bound, not a power analysis on a
  predicted effect.)
- **prediction (mine, stated in advance, ~85% confidence):** tie rate **≈ 0**.
  The SAD sensor CONFABULATES a value per cell rather than abstaining (parallax
  rung §6), and the selectors run over accumulated/derived values that almost never
  collide exactly (ArgminUnique P1). I predict the dominant-group Argmax tie
  fraction and the per-cell tie fraction are both **< 1%** on natural depth scenes.
- **decision rule / VACUITY:** if the 95% Wilson UPPER bound on the tie rate is
  **below ~2%**, arming the 16 WTA sites with `ArgminRefusal` buys **negligible**
  coverage on natural scenes — **a refusal that never fires is not a capability** —
  so **do NOT arm them**, and record it as the vacuity finding. The perception
  residual (`perception_hole_mints_residual`, which fires on REAL hole structure,
  not a tie) is the load-bearing instance instead. If the tie rate is unexpectedly
  HIGH (>5%), the WTA instance is load-bearing and arming is warranted — under a
  NEW pre-registration to arm (never a parameter search here).

---

## 4 — DISCIPLINE

- Engine built in-tree (`7041d2e6a7dd`, own); provenance its own step, before AND
  after; every measuring script prints `provenance_line()` from inside its own
  process and aborts on divergence (`engine_preamble()` at import).
- Oracle 222/0 before AND after (§9). Migrated gate
  `tests/test_residual_promote_migrated.py` with a POSITIVE control (a graph with a
  minted Residual that the promote rule MUST turn into a SelfConcern, and a graph
  without any residual that must stay byte-identical).
- ≤2 workers; `os.getloadavg()` recorded; NO wall-clock cutoff as a verdict.
- Term enum index 181 ALLOCATED, UNUSED (175–180 unmoved). No `Value` variant, no
  `py.rs` change, no existing Term touched.
- `python3 -m domains.seed_record --write` when the seed lands.
- I do NOT edit `VISION_PROTOCOL.md`. Errors reported in the results.
