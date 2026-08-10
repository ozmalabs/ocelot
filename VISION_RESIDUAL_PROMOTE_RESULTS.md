# A PROMOTED REFUSAL — RESULTS

> **LEDGER ROW (for transcription; do not edit VISION_PROTOCOL.md):**
> **120000–120999 ALLOCATED; 120000–120199 DRAWN (LITERAL, in-block) by the WTA
> tie-rate measurement; Term enum index 181 ALLOCATED and UNUSED (175–180 unmoved);
> NO RUST.** **THE LOOP THE ARC CIRCLED IS CLOSED: a heard refusal / a perception
> HOLE becomes a `Residual`, a graph rule PROMOTES it to a `SelfConcern` DISTINCT
> from every ordinary concern, and the REAL human-gated
> `jabberwock_daemon.promote_self_concern` turns it into a
> `StandingConcern{pending}` the self-improvement pipeline runs — shown END TO END
> on the booted agent.** **The load-bearing instance is the PERCEPTION residual
> (`perception_hole_mints_residual`), which fires on REAL hole structure (the
> eye-view rung's un-carved cells), not on a rare tie, and NOT on the FLAT
> space-constancy case.** **DEDUP holds (N same-kind residuals → ONE active
> concern, the retire-survivor guard; idempotent).** **GROUND: a knowledge
> residual's content routed through the documented per-word teacher loop
> (`ground_unknowns`) becomes a grounded concept the agent can then recognise.**
> **CHARACTERISE-FIRST — the real-scene WTA tie rate (n=200 fresh seeds): the
> per-cell nearest-surface WTA is VACUOUS (0/16200, Wilson upper 0.024% ≪ 2% →
> DO NOT ARM); the reference-frame WTA (`mo_dominant`) ties ~0.75% on the SENSED
> field (Wilson upper 3.57%, a 2–5% GREY zone → arming DEFERRED to its own prereg),
> and — the deeper fact — the GROUND-TRUTH reference selection is 100% tied (three
> equal depth surfaces); the sensor CONFABULATES a unique winner out of it.**
> **§9: oracle 222/0 BEFORE (`7041d2e6a7dd`) AND AFTER; the seed is DEFAULT-OFF,
> inert on a plain booted agent (0 residual concerns).** **Migrated gate
> `test_residual_promote_migrated.py` 9/9 incl. the real promote spine + the
> teacher loop.** **WHAT I GOT WRONG: oriented in the SHARED checkout on early
> reads (caught, all writes/builds/measurements in the worktree); my first mint
> guard deduped ACROSS passes only (two same-kind residuals in ONE pass both filed
> — fixed by adding the gap_awareness retire-survivor rule); my prereg left a 2–5%
> GREY zone the reference-frame tie rate landed in; I under-modelled confabulation
> (predicted ties ≈0 — TRUE for the sensed point ~0.75%, but the GT is 100% tied
> and confabulation is exactly what suppresses it, which I did not predict).**

Pre-registration `VISION_RESIDUAL_PROMOTE_PREREG.md`, committed **`e58825ac68`**
before any number. Successor to `VISION_REFUSAL_REPRESENTABLE_RESULTS.md` (HEAR +
MINT). **This rung built PROMOTE + GROUND — the named successor.**

- **worktree (as observed):** `agent-a4321ae58a0e75618`.
- **base SHA:** `da113ec4af`.
- **engine (§10):** built in-tree by `scripts/engine_build.sh` → **`7041d2e6a7dd`**
  (`source_match: own`; NO RUST — same source as the merged ArgminRefusal engine).
  Provenance its OWN step, BEFORE (7 passed) and AFTER (7 passed) all measurement;
  every measuring script asserts `7041d2e6a7dd` in `provenance_line()` in-process.
  Term enum index **181 ALLOCATED, UNUSED**; 175–180 unmoved.
- **oracle (§9):** `bash scripts/rung7_vision_bench.sh` (data/ symlinked, §10.2):
  BEFORE **222 passed / 0 failed**; AFTER **222 passed / 0 failed**.
- **seed_claim (§3 clause 8), post-run verbatim:**
  ```
  SEED CLAIM 120000-120999: REFUSED.
    OCCUPIED: 200 seed integer(s) in this range are measurably drawn by 1 file(s).
      120000..120199: scripts/residual_wta_tierate.py  (LITERAL, in-block; none outside)
    Scope: 825 files with seed sinks; 513 UNRESOLVED sink sites tree-wide (counted, not discarded).
  ```
  `unknown_sinks: 0` for my file (the `default_rng(SEED0 + i)` loop form resolved
  here — SEED0 is a module constant — so all 200 attributed literally). The REFUSAL
  is my OWN in-block draw, the expected post-run state.
- **loadavg:** peak observed ~1.2 on 12 cores; ≤2 workers throughout
  (`OMP_NUM_THREADS=2`); no wall-clock quantity is a verdict.

---

## 0 — THE HEADLINE

**"Matches nothing I hold" → "file it as something to resolve" → (human-gated)
"work on it".** The refusal_representable rung made a refusal a first-class
`Residual`; this rung routes that `Residual` through the EXISTING self-improvement
spine. Two thin seed rules compose onto `seeds/gap_awareness.json` /
`jabberwock_daemon.promote_self_concern`; nothing else is rebuilt.

| arm | result |
|---|---|
| **C1 PROMOTE, perception (load-bearing)** | eye-view HOLE (`uncarved_count>0`) → **1** `Residual{uncarved_hole}` → **1** `SelfConcern{source:residual}`; FLAT space-constancy (`uncarved_count=0`) → **0/0** |
| **C2 PROMOTE, refusal** | `ArgminRefusal` tie → `Residual{no_unique_extremum}` → the SAME promote rule files a **DISTINCT** SelfConcern (distinct `residual_kind`); unique/empty → 0/0 |
| **C2 both sources, one rule** | a hole AND a refusal in one graph → **two DISTINCT** active SelfConcerns through ONE promote rule |
| **C3 REACHES THE SPINE (human-gated)** | the REAL `promote_self_concern` accepts it → `StandingConcern{status:pending, about:"unresolved residual: uncarved_hole", kind:residual}`; the SelfConcern flips to `promoted` |
| **C4 DEDUP / NO FLOOD** | 4 same-kind residuals → **1** active SelfConcern (retire-survivor guard); re-run adds none |
| **C5 DEFAULT-OFF (§9)** | inert on a graph with no `attends`/`has_residual`; byte-identical round-trip; a plain booted agent has **0** residual concerns; oracle 222/0 before & after |
| **C6 GROUND** | a residual's content through `ground_unknowns` (supplied teacher) → the term becomes held + a `taught_<term>` Concept exists |
| **F1 / F2 FALSIFY** | neither: the Residual REACHES the promote rule (no field-boundary erasure one level up); the loop does not flood |

---

## 1 — WHAT WAS BUILT (`seeds/residual_promote.json`, v1.0.0, depends `core`)

Two thin rules (+ one dedup-cleanup rule mirroring `retire_duplicate_gap`):

1. **`promote_residual_to_self_concern`** — THE LOOP CLOSURE. Match
   `[["agent","attends","h"],["h","has_residual","res"]]` (the agent attends a
   source `h`; `h` holds a `Residual` — the shared-var 2-edge join, reusing the
   `h -has_residual-> res` edge `refusal_query_mints_residual` ALREADY mints, NO
   edit to that seed). Guards: mint-once (`res.promoted != 1`) + content-dedup.
   Mints `SelfConcern{status:'noted', source:'residual', kind:'residual',
   content:"unresolved residual: <kind>", residual_kind:<kind>}`; edges
   `agent -has_self_concern-> sc`, `sc -about_residual-> res`. DISTINCT from every
   ordinary concern (source/kind/`about_residual`), and the SAME node shape the
   human-gated `promote_self_concern` and `reflective_faculty._run_self_gaps`
   consume — so it plugs straight into the existing spine.

2. **`perception_hole_mints_residual`** — makes the eye-view rung's un-carved HOLE
   ACTIONABLE. Match `[["agent","attends","field"]]`; where `field.uncarved_count
   > 0` (mint-once); mints `Residual{kind:'uncarved_hole', source_count:<n>}` +
   `field -has_residual-> res`. Fires on REAL hole structure, NOT a tie; and NOT on
   FLAT space-constancy (`uncarved_count=0` — correct "nothing here" is not a
   residual).

3. **`retire_duplicate_residual_concern`** — no-flood part 2 (the
   `retire_duplicate_gap` precedent): the mint guard only blocks NEW same-content
   concerns across passes; two distinct same-kind residuals in ONE pass both file,
   so this retires the non-`Argmin`-survivor (batch-safe, no node-id), scoped to
   `source='residual'`.

Default-OFF by non-existence: no committed seed makes `attends` or `has_residual`
edges, so the rules are inert on every committed graph — `load_all_seeds` globs the
file (SeedSummary records it) yet a plain booted agent mints ZERO residual concerns.

---

## 2 — THE PERCEPTION RESIDUAL, END TO END (the load-bearing instance)

The eye-view rung (118000) recovered the held carve of seed 116000: three depth
surfaces + **9 un-carved HOLE cells** at the right-edge column (the sensor's
aperture-corner confabulation, down-weighted by the participation ratio, RENDERED
as gaps). That rung named the hole "I don't hold this yet" and rendered it; this
rung makes it ACTIONABLE. On the booted agent: the eye holds a `VisionField` with
`uncarved_count=9` → `perception_hole_mints_residual` mints ONE
`Residual{uncarved_hole, source_count:9}` → `promote_residual_to_self_concern`
files ONE `SelfConcern{source:residual}` → the REAL `promote_self_concern` mints
`StandingConcern{status:pending, about:"unresolved residual: uncarved_hole"}`, and
the SelfConcern flips to `promoted`. **The eye sees a region it cannot carve →
mints a residual → files it as something to resolve → (human-gated) it becomes a
standing concern the self-improvement/teacher machinery works on.** No Python
decision — the promote is a graph rule; the human gate is the explicit
`promote_self_concern` call.

The FALSIFY was refuted: the minted `Residual` REACHES the promote rule (no second
field-boundary erasure one level up), and the loop does not double-file.

---

## 3 — CHARACTERISE FIRST: THE REAL-SCENE WTA TIE RATE (arm / don't-arm)

`results/residual_wta_tierate.json`, engine `7041d2e6a7dd`, n=200 fresh seeds
(120000–120199), unit = SEED, 95% Wilson CI. The real-scene WTA is `mo_dominant`
(`vision_motion_group.json`): an **Argmax over motion-group member count** (the
reference frame is the largest common-fate group). Real depth scenes, real SAD
sensor (`parallax_char` + `vector_field`), grouped by common fate.

| WTA site | τ | ties | rate | Wilson95 upper | verdict |
|---|---|---|---|---|---|
| **per-cell nearest-surface** (argmin) | 0 / √5 | **0 / 16200** | 0.000000 | **0.00024** | **VACUOUS — DO NOT ARM** |
| **reference-frame `mo_dominant`** (SENSED) | 0 | 2 / 200 | 0.0100 | 0.0357 | **GREY (2–5%) — DEFER** |
| **reference-frame `mo_dominant`** (SENSED) | √5 | 1 / 200 | 0.0050 | 0.0278 | **GREY — DEFER** |
| **reference-frame `mo_dominant`** (GROUND-TRUTH) | 0 / √5 | **200 / 200** | **1.000** | — | the world's true ambiguity |

**The arm/don't-arm decision it forces:**
- **Per-cell nearest-surface WTA: VACUOUS.** 0 ties in 16 200 cell-firings (Wilson
  upper **0.024% ≪ 2%**). **A refusal there would never fire — DO NOT ARM those
  sites; minting `Residual`s there is dead code.** (This is exactly the discipline
  the refusal rung named: a refusal that never fires is not a capability.)
- **Reference-frame WTA (`mo_dominant`): a 2–5% GREY zone.** The SENSED tie rate is
  ~0.75% (2/200 at τ=0, 1/200 at τ=√5), Wilson upper **3.57%** — above my
  pre-registered 2% "vacuous" line but below the 5% "arm" line. My prereg did not
  resolve 2–5% cleanly (WHAT I GOT WRONG, §6). **Arming `mo_dominant` is therefore
  DEFERRED to its own pre-registration** (§3/§5 — a new mechanism needs its own
  prereg, never a parameter search here). I do NOT arm.
- **The deeper measured fact.** On the GROUND-TRUTH field the reference-frame Argmax
  is tied **200/200 (100%)** — three depth surfaces of exactly equal size (27 cells
  each on this grid), so the world offers NO unique reference. The sensed rate
  ~0.75% is what remains **after the sensor CONFABULATES a unique winner out of that
  ambiguity** (the 2 tie scenes have two equal-largest confabulation fragments of 27;
  memory: CONFABULATION IS THE DEFAULT). So the graph's usual unique reference frame
  is a confabulated tie-break of a genuinely-tied world — the real thing worth
  representing is bigger than a one-line `Eq(sel, RefusalMark)` arming, which is why
  arming is deferred, not done.

**Conclusion:** the WTA-arming instance is NOT the clean win (per-cell vacuous;
reference-frame a small grey rate hidden behind confabulation). **The PERCEPTION
residual — which fires deterministically on real hole structure — is the
load-bearing instance,** exactly as the task predicted and now measured.

---

## 4 — DEDUP / NO FLOOD, and GROUND

**Dedup (C4).** Four same-kind holes → four distinct `Residual`s but **ONE** active
`SelfConcern` (`retire_duplicate_residual_concern` keeps the `Argmin` survivor);
re-running `run_rules` adds none (mint-once). Two DISTINCT kinds (hole + refusal) →
TWO concerns. CLAUDE.md's dedup-by-content requirement holds.

**Ground (C6).** A knowledge residual's content (a token the agent does not hold)
routed through `agent.ground_unknowns(term, teacher=…)` — the DOCUMENTED per-word
teacher loop — grounds the term (the sign becomes held; a `taught_<term>` Concept
exists), so the agent can THEN recognise it. The teacher decides meaning; the
adapter is only the loop. HONEST SCOPE: the real dictionary/wiki self-teacher needs
network (unregistered here — `_self_teacher` is None on a bare boot), so the loop is
shown with a SUPPLIED teacher (the same interface). And the PERCEPTION hole heals by
RE-SAMPLING (the eye-view rung's named lever "holes self-heal by looking"), NOT by
dictionary grounding — GROUND is for content/knowledge residuals, and I do not claim
the hole is dictionary-groundable.

---

## 5 — THE GATE

`tests/test_residual_promote_migrated.py` — **9 passed**, positive-controlled:
`test_default_off_is_byte_identical` (a seed that changed disarmed behaviour fails)
+ `test_no_residual_no_selfconcern` (the loop mints nothing without a residual) +
`test_flat_space_constancy_mints_nothing` (correct absence is not a gap). Two boot
integration tests exercise the REAL spine: `test_selfconcern_reaches_the_real_promote_spine`
(→ StandingConcern) and `test_ground_a_residuals_content_via_the_teacher_loop`.

---

## 6 — WHAT I GOT WRONG (in full)

1. **I ORIENTED IN THE SHARED CHECKOUT ON MY EARLY READS** (the §11 hazard the task
   warned of — "three rungs oriented in the shared checkout by mistake"). Caught by
   `git rev-parse --show-toplevel` on the FIRST command; a later variable slip
   (`WT=…/research/experiments/gamma-substrate`) ran two read-only probes in the
   canonical tree. **ALL writes, the engine build, the data symlink, and every
   measurement are in the worktree** (`agent-a4321ae58a0e75618`); provenance
   confirms `7041d2e6a7dd @ <worktree>`. Nothing was written to the shared tree.
2. **MY FIRST DEDUP GUARD DEDUPED ACROSS PASSES ONLY.** Two same-kind residuals in
   ONE `run_rules` pass both filed a SelfConcern (2 where 1 was wanted) — the mint
   guard's `Not Exists` sees no prior concern within the same pass. Caught by the
   dedup test failing; fixed by ADDING the `retire_duplicate_gap` precedent (a
   third rule), not by weakening the test. The two-part design is exactly what
   CLAUDE.md documents.
3. **MY PREREG LEFT A 2–5% GREY ZONE.** I stated "upper < 2% → don't arm" and
   "> 5% → arm" but not the between. The reference-frame tie rate landed at Wilson
   upper 3.57% — in the gap. I report it AS grey and DEFER arming to its own prereg
   rather than rescue a decision the prereg did not cleanly license.
4. **I UNDER-MODELLED CONFABULATION.** I predicted the tie rate ≈ 0. The SENSED
   point estimate (~0.75%) is roughly that, but I did NOT predict that the
   GROUND-TRUTH reference selection is 100% tied and that the sensor's confabulation
   is exactly what suppresses the tie to ~0.75%. The proviso that broke told me
   what I missed: confabulation is not just "ties are rare", it is the mechanism
   that MANUFACTURES a unique winner from a tied world.
5. **THE PER-CELL WTA I MEASURED IS NOT A LITERAL SEED SITE.** `mo_dominant` is the
   real graph WTA; the per-cell nearest-surface argmin is the finer "cannot assign
   this cell" question I measured alongside it. Both are reported; only `mo_dominant`
   is a committed `Eq(node, sel)` site. Stated, not blurred.

---

## 7 — SCOPE: WHAT IS *NOT* SHOWN

- **Nothing is armed.** The 16 `Eq(node, sel)` WTA sites are UNCHANGED. Per-cell is
  vacuous; `mo_dominant` arming is deferred to its own prereg.
- **The perception residual's `uncarved_count` is written by the adapter** from the
  recovered held carve (mechanical I/O — the eye-view rung's recovery). The RULE
  decides it is a residual; the count is not re-derived graph-natively here.
- **GROUND is shown with a SUPPLIED teacher**, not the live dictionary/wiki
  self-teacher (network). The hole does not dictionary-ground (it re-samples).
- **The human gate is a direct `promote_self_concern` call** (the operator-console
  step), not a full chat-driven promote.
- **The tie-rate is a property of THIS stimulus distribution** (synthetic Fourier
  depth scenes, one sensor/aperture family, N=3 fronto-parallel planes), inherited
  from the parallax rung. It is not a claim about arbitrary natural video.
