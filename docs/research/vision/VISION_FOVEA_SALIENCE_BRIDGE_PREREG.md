# PREREG — the fovea/salience bridge: MIGRATE the fovea decision Python→graph, resolved by the LOG-WEIGHTED ADMISSIBILITY GRAPH

**Block: 160000–160999. Branch: `gamma-substrate/fovea-salience-bridge`, base HEAD `4bc702a8bf`.**

## SEED CLAIM 160000-160999

`python3 scripts/seed_claim.py 160000 160999`:

```
SEED CLAIM 160000-160999: CLEAN -- no collision DETECTED.
  Scope: 859 files with seed sinks; 581 UNRESOLVED sink sites tree-wide (counted, not discarded).
  CAVEAT 1 -- THE UNIT IS THE SEED INTEGER, not consecutive draws from
    one generator. default_rng(S) burns an unbounded stream downstream of
    S; a rung seeding ONCE at its block base measures as ONE seed here.
  CAVEAT 2 -- THIS TOOL UNDER-REPORTS BY DESIGN (7 declared blind spots;
    unresolvable sinks are COUNTED, not discarded). A CLEAN RESULT MEANS
    'NO COLLISION DETECTED', NEVER 'NO COLLISION EXISTS'.
```

`check_claim(160000, 160999)` → `OK=True`, **581 unresolved sink sites** (§3 clause 8:
the count is recorded, the silence is priced). **`SEED CLAIM 160000-160999 CLEAN`.**

## Engine (§10)

`engine 64dbce1e7f47 @ .../runners/dsl/python/substrate_rs/_native.abi3.so` — `shared`
build, **Rust source identical** to canonical. This rung adds **NO Rust** (composition of
existing DSL Terms only), so `source_match ∈ {own, shared}` holds as `shared`; the coarse
path is byte-identical and the oracle must be UNMOVED (222/0 both sides).

## The migration (the point of the rung)

159000 proved salience-driven foveation but SELECTED the fovea with a numpy `argmax`/top-K
in Python (`scripts/salience_foveation_probe.py::select_fovea`, the `scored.sort(key=-peak)[:top_k]`
line) — an agent DECISION in Python, which CLAUDE.md forbids. This rung MIGRATES that
decision INTO THE GRAPH: the fovea is resolved by the substrate's own **log-weighted
admissible selection**. `grammar.rs` is decisive — Γ is *"the weighted admissibility
grammar; selection over admitted candidates is ∝ exp(w)"*, where the weight `w` is a Term.
The deterministic (MAP) reading of `∝ exp(w)` is `argmax_w over admissible candidates`,
i.e. `ArgminUnique(source = admissible-candidates, value = Neg(w))` — the highest-log-weight
admissible candidate, with tie-refusal (*a comparison can be false, a selection cannot*).

- **Ingest (mechanical world-adapter I/O, NOT a decision):** the residual-salience field →
  `flag_movers` → connected components → per-component peak/box/region — the SAME extraction
  `select_fovea` already does BEFORE its sort — emitted as `FoveaCandidate` graph nodes, each
  carrying `salience` (bottom-up log-evidence source), `on_valid` (the Γ admissibility datum),
  `goal_logweight` (top-down bias, default 0).
- **Resolution (GRAPH-NATIVE, a seed Rule run by `run_rules`):** `seeds/fovea_salience_bridge.json`
  rule `fovea_resolve`: the winning candidate is `ArgminUnique` over the Γ-admissible candidates
  keyed by `Neg(w)`, `w = Log(salience) + goal_logweight`; the winner is marked `is_fovea=1`.
  The fovea target is READ BACK from the graph — never computed by a Python argmax.

## Hypotheses (two-sided) and decision rules

- **A1 — graph-native decision (headline).** The fovea is chosen by the graph; NO Python
  `if`/`argmax`/`max`/`sort` decides it. *Statistic:* a SOURCE audit of the resolution path
  (`domains/fovea_bridge.py::resolve_fovea`) — the fovea target is read from a graph attr
  (`is_fovea`) after `run_rules`, with no Python selection over candidate weights. *Decision:*
  PASS iff the audit finds zero Python selection ops on the resolution path; a found argmax/
  max/sort/`>`-comparison over candidate weights FAILS the rung. Null = I smuggled a Python
  decision (report + diagnose, do NOT paper over).
- **A2 — it works (scored, by ground truth).** The graph-resolved fovea (i) matches the
  retired numpy `select_fovea` top-1 target on the synthetic case, and (ii) lands on the
  ground-truth mover cell (`mover_c` synthetic; labels-buffer object on E1M1). *Statistic:*
  equality of `peak_rc` (graph vs numpy) and GT membership of the graph `peak_rc`. *Decision:*
  PASS iff graph==numpy AND graph∈GT on the synthetic scenes (one-mover and a two-mover
  selection); E1M1 confirmatory, skipped if WAD/VizDoom absent. Null (graph≠numpy) ⇒ honest
  DEGRADE with diagnosis.
- **A3 — log-weighted co-presence, not selection.** Two co-present admissible candidates
  resolve by log-weight: (i) bottom-up alone → fovea on the more salient; (ii) a co-present
  top-down goal log-weight `g` on the OTHER candidate shifts the resolution CONTINUOUSLY as
  `g` rises (the winner's total `w` is monotone in `g`; the override is a weight-shift, not a
  switch), crossing over exactly when `Log(s_B)+g` overtakes `Log(s_A)`; (iii) a strong-enough
  bottom-up salience still WINS the race against a top-down weight. *Statistic:* the swept
  curve `g ↦ (w_A, w_B, winner)`; monotonicity of `w_B(g)` and of the winner indicator.
  *Decision:* PASS iff `w_B(g)` is monotone non-decreasing and the winner flips A→B exactly at
  the log-weight crossover, and the strong-bottom-up race is won by the higher `w`. `g` is a
  SWEPT parameter (§13 — monotonicity shown, not a fixed magic number).
- **A4 — admissibility governs (Γ gates before weighting).** An INADMISSIBLE candidate
  (`on_valid=0` — a fovea target on an unobserved cell violates the consistency constraint
  "you cannot foveate what you have no valid observation of") is excluded from the resolution
  regardless of its weight: a high-`w` inadmissible candidate never wins over a lower-`w`
  admissible one. *Statistic:* the winner's `admissible` status. *Decision:* PASS iff the
  admissible candidate wins despite the inadmissible one carrying a strictly larger salience.

## §13 — every number falls out

- `salience` = the measured residual tangential magnitude (157000's residual field); not tuned.
- `w = Log(salience) + goal_logweight`: `Log` is the map to log-evidence (a CROSS-FRAME rule
  applied, per the frame/continuum invariant), so `exp(w) = salience · exp(g)` — selection ∝
  salience, exactly the intended "more salient ⇒ more likely the fovea". No constant.
- `goal_logweight g` in A3 is a SWEPT parameter; monotonicity is the claim, not a value.
- admissibility = a declared consistency predicate (`on_valid==1`), the Γ where-clause; no
  threshold, no tuned filter.
- extraction floors (`FOVEA_MIN_HALF`, `MIN_REGION`, `SAL_FLOOR`) are 159000's already-declared
  geometric/rounding floors, unchanged and inherited — not re-tuned here.

## Prediction (stated in advance, with provisos)

The graph `ArgminUnique(Neg(Log(salience)))` will reproduce the numpy `argmax(peak)` top-1 EXACTLY
on the synthetic scenes, because `Log` is monotone so `argmax Log(s) = argmax s`, and both consume
the identical candidate set. **Proviso that would break it:** a genuine TIE in log-weight — then
the graph REFUSES (null, no fovea) where numpy's stable sort picks the lower index. If a synthetic
scene produces exactly-equal peaks, the graph will (correctly) refuse and diverge from numpy;
I expect the synthetic peaks to be distinct, so no tie. A second proviso: if `boot_core`'s core
rules mutate `FoveaCandidate` nodes (they should not — unknown types), the read-back could be
polluted; I expect inertness and will assert it.

## Gate

`tests/test_fovea_salience_bridge_migrated.py` — A1 (source/structural: resolution path has no
Python argmax over candidates; able to fail), A2 (graph==numpy top-1 AND graph∈GT), A3 (monotone
in `g`; strong bottom-up wins the race), A4 (inadmissible high-weight never wins). Reads
graph/measured values; cross-process stable; skips E1M1 if WAD/VizDoom absent.
