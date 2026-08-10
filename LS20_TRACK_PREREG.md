# LS20 OBJECT-PERMANENCE TRACK — PRE-REGISTRATION (block 224000)

**Committed ALONE, before any measurement number is trusted.** This rung
RE-LANDS the "richer object model" that converts 222000's honestly-reported
LIVE NULL — under a pre-committed gate, so the number is disciplined.

## WHY THIS IS A RE-LAND (the discipline gap being closed)

222000 (`LS20_PERCELL_RESULTS.md`, on main) proved the per-cell TRANSFORM
mechanism OFFLINE decisively (strict changed-cell F1 **1.0** vs ~0 nulls,
CI-separated) but its LIVE half returned the pre-registered **NULL**: learned
change-set F1 **0.0 == persistence 0.0**, because its whole-frame-colour region
selector could not isolate the real ls20 avatar (nested fields + multi-colour
avatar + move/trail dynamic). 222000 named the fix precisely: *"a local-region /
multi-colour-object tracker with a trail model."*

An autonomous continuation (branch `percell-222000-cont` @ `ec8c18215a`) BUILT
exactly that and measured live change-set strict-F1 **≈0.964** on REAL ls20 —
but produced that number **WITHOUT a prereg commit** (a process gap; the metric
was 222000's inherited strict change-set F1, CI-separated from persistence 0.0,
credible-but-process-incomplete). THIS rung re-lands it PROPERLY: pre-register
the gate FIRST (this file, alone), then re-measure under the pre-committed gate.

## SEED CLAIM (verbatim, before any number)

`python3 scripts/seed_claim.py 224000 224999` →

```
SEED CLAIM 224000-224999: CLEAN -- no collision DETECTED.
  Scope: 929 files with seed sinks; 633 UNRESOLVED sink sites tree-wide (counted, not discarded).
  CAVEAT 1 -- THE UNIT IS THE SEED INTEGER, not consecutive draws from
    one generator. default_rng(S) burns an unbounded stream downstream of
    S; a rung seeding ONCE at its block base measures as ONE seed here.
  CAVEAT 2 -- THIS TOOL UNDER-REPORTS BY DESIGN (7 declared blind spots;
    unresolvable sinks are COUNTED, not discarded). A CLEAN RESULT MEANS
    'NO COLLISION DETECTED', NEVER 'NO COLLISION EXISTS'.
```

CLEAN — no collision detected. `check_claim(224000, 224999)` is recorded HERE
in the prereg, NOT as a permanent pytest: once this rung's ledger row lands the
block is (correctly) DECLARED, so a "range is undeclared" assertion would invert
by construction. (The 223000 flash rung made exactly that inversion mistake and
had to remove the test; the other ls20 rungs carry no such test — this one
matches that pattern.)

## THE MODEL (object permanence — GENERAL, no ls20 constants)

Object permanence via connected-component tracking + centroid shift — the same
object-permanence primitive the substrate uses elsewhere, dimension-arbitrary,
NOT an ls20 hack:

- **field** = the frame's dominant colour(s) (`k` most-frequent; ls20 has a
  NESTED field — a global colour + a local play-field — so `k=2` by default). A
  general "the background is the dominant colour(s)", never a hardcoded 0.
- **object** = the connected 4-neighbour FIGURE (non-field) blob that MOVED,
  tracked across frames (declines to model if it exceeds a compactness cap).
- **per-action shift** = the whole-object centroid displacement (before→after),
  stored in the graph as a `shift:dr:dc` **Hypothesis** on the Percell agent
  (reusing 222000's `pc_*` mint/confirm/revise rules verbatim, via a new optional
  `spec=` path on `Percell.observe`; default `spec=None` = offline byte-identical).
- **predict** = a RULE-held `Transform` TRANSLATES the tracked object → the
  per-cell next frame; persistence fallback when the shift is unknown/zero or no
  object is tracked.

Tracking is MECHANICAL PERCEPTION (the eye's segment_and_track analogue); the
shift is GRAPH DATA; predict applies the held Transform. In-frame cell values are
INTEGER (the integer lattice); the shift `Transform` is the CROSS-FRAME map
(the base-as-dimension invariant — a translation lives in the map, never in a
frame's cells).

### The shift estimator bug the gate MUST catch (pre-committed teeth)

The FIRST shift estimator (in the continuation's development) measured the
object's **EXTENT** — the appeared-vs-vacated leading/trailing edge gap — which
for a 5-wide object moving 1 cell reports shift ≈ object width (`3`/`5`) instead
of `1`. It was FIXED to the whole-object before→after **centroid displacement**.
The pre-committed instrument teeth (G-track-teeth below) require that a WRONG
(extent-not-displacement) estimator scores **below a low bar** while the
centroid estimator scores ≈1.0 — proving the exact-shift result is EARNED, not
an artifact of a permissive metric.

## THE NULL (pre-committed — the model MUST beat it, CI-separated)

**persistence** — predict next = current. Predicts NO changed cells → change-set
recall 0 → strict changed-cell F1 **0**. A model that only ties persistence has
learned nothing (222000's live half tied it — that is the null this rung
converts).

## GATES (pre-registered; thresholds fixed HERE before measuring)

- **G-track-teeth (OFFLINE powered, HEADLINE synthetic).** On synthetic dense
  move+trail scenes (real ls20 palette; nested field + static figure
  contamination — the honest twin of the live mechanic), the tracked model's
  strict change-set F1 is CI/threshold-separated above persistence:
  - **rigid move (no trail): strict-F1 ≈ 1.0 EXACT** — pre-committed bar
    `> 0.99`, and every discovered per-action unit shift equals the true
    translation (not the object extent).
  - **with trail: strict-F1 ≈ 0.86** — pre-committed bar `> 0.7` AND `< 1.0`
    (the honest trail/consume residual: a rigid-translate model cannot predict
    dropped trail cells).
  - both vs **persistence strict-F1 = 0.0**.
  - **INSTRUMENT TEETH:** a WRONG shift estimator (extent-not-displacement) on
    the rigid scene scores strict-F1 **< 0.5** (pre-committed low bar) —
    decisively below the centroid estimator's `> 0.99`. The 1.0 is earned.
- **G-live (the real number, re-measured under this gate).** Run on REAL
  ARC-AGI-3 ls20 (`ls20-9607627b`), larger budget (≤300 steps). Report the
  tracked model's change-set strict-F1 vs the persistence null ON REAL FRAMES,
  over steps where the action had a learned shift AND an object is tracked, with
  a 1000-resample bootstrap 95% CI. **Pre-committed success = learned beats
  persistence, CI-SEPARATED** (learned 95% lower bound > persistence upper bound
  0.0); target replicates the continuation's **≈0.964**. The live frames come
  from the REAL API against the DETERMINISTIC ls20 game (same game_id + same
  action-cycle → reproducible frames — the run is a fresh API call sequence that
  is reproducible; this is stated explicitly in RESULTS). Auth verified BEFORE
  measuring; `ARC_API_KEY` from `/home/matt/ozma/internal/.env`, NEVER
  printed/committed; the `.so` is gitignored, NEVER committed. API
  unreachable/rejected/rate-limited ⇒ **STOP and report the OFFLINE teeth as the
  deliverable; NEVER fabricate/cherry-pick/estimate.**
- **G-mechanic-discovered.** The per-action shifts are DISCOVERED from tracking,
  not given: each real action moves the ~25-cell avatar by a fixed step (up/
  down/left/right). SOURCE-AUDIT: NO hardcoded shift/action table in the agent
  path (only world physics / the deterministic game server has the true map).
- **G-graph-native.** Tracking = mechanical perception; the shift = a graph
  `Hypothesis` (read via `agent.hypothesis`); predict = a rule applying the held
  `Transform`; the adapter is mechanical. Source-audit clean — no agent decision
  (no `if/else` over graph state deciding the model) in Python.
- **G-discipline.** Integer-native in-frame. **Default-OFF byte-identical**: the
  `spec=None` default keeps 222000's 8 base percell gates + all other ls20
  suites byte-identical. **Canonical `.so` md5
  `793ce09ed498a749abb79aeaea44b92e` UNCHANGED** (no Rust — reuses connected
  components + 222000's `Transform`; if a new Rust Term were truly needed, STOP +
  report). `runners/dsl` diff EMPTY (`term.rs` included). Oracle
  `rung7_vision_bench` BEFORE == AFTER. 34-file
  `per_area_settlement_regression.sh` failing NODE-ID SET IDENTICAL before/after.
  `source_match` reported.

## SCOPE — object-permanence re-land ONLY

This rung lands the richer object model, properly pre-registered, with the live
≈0.964 re-measured under a pre-committed gate. It does NOT fold in the flash
(223000) consume-marking — the ~0.036 gap from 1.0 is the honest trail/consume
residual (a rigid-translate model cannot predict dropped trail cells), reported
as the STANDING residual and NAMED as the next rung (225000), NOT attacked here.

## FALSIFICATION BAR

Object permanence is GENERAL (connected-component tracking + centroid-shift, the
same primitive used elsewhere, dimension-arbitrary — not an ls20 hack); the
shift is an EXPLICIT graph `Hypothesis`; the mechanic is DISCOVERED by tracking
with a source audit proving no hardcoded shift/action table. A model whose shift
is a Python/seed constant, or that only ties persistence, or whose exact-shift
number survives a wrong (extent) estimator, FAILS this rung.

## FILES (code re-landed from `ec8c18215a`; docs/gate authored here)

- `LS20_TRACK_PREREG.md` — this file (committed alone).
- `worlds/arc_ls20_percell_track.py` — the `LiveObjectTracker` (field / connected
  figure blob / centroid-shift → graph Hypothesis / translate-predict), + the
  `shift_mode` teeth hook (centroid vs the buggy extent estimator).
- `worlds/arc_ls20_percell.py` — the small optional `spec=` path on
  `Percell.observe` (default None = offline byte-identical).
- `scripts/arc_ls20_percell_live_tracked.py` — the bounded LIVE half.
- `tests/test_ls20_percell_track_migrated.py` — the gate tests (rigid-exact,
  trail-residual, shift-stored-in-graph, + the wrong-shift-estimator teeth).
- `results/arc_ls20_percell_live_tracked.json` — the measured live number.
- `LS20_TRACK_RESULTS.md` — the results (authored AFTER measuring).
