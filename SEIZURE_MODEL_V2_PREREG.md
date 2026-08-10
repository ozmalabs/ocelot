# SEIZURE MODEL V2 — PREREGISTRATION

Registered **before** the confirmatory numbers (a disclosed calibration pilot is
reported below). Base commit `a9fc82eed2`, branch `seizure-model-v2`, isolated
worktree. No timing claims.

## What V1 could not do (the two named limits from `SEIZURE_SCIENCE.md`)

- **P4 (soft refutation → limit).** V1's only lateral coupling `g` is a
  **symmetric diffusive** channel (shed-out and diffuse-in over `projects_to`,
  conservative for a uniform field). Measured consequence: *more* coupling was
  **protective** (give* fell 0.65→0.50 as g rose) — the OPPOSITE sign to the
  epilepsy connectivity/hyperconnectivity literature. V1 cannot speak to
  epileptogenic connectivity.
- **P5 (null → limit).** V1's lattice is **homogeneous** (every area degree-4);
  it has no hubs, so onset locus had no structural answer (give* differed by ≤1
  grid step across center/edge/corner). The literature has a strong hub-onset
  effect V1 cannot represent.

## The two fixes (existing DSL Terms only — NO new Rust Term)

1. **Excitatory-recruitment coupling `g_rec`** — a NEW top-level term appended to
   the `sz_settle_next_residual` rule:
   `+ g_rec * Σ_{rn ∈ recruits(area)} ticking_rn · max(0, rn.residual − c_gen)`.
   An over-threshold (ictal) neighbour **injects** its overload excess into this
   area, **non-conservatively** (nothing is subtracted from the source — it is
   gain-bearing, not diffusion) and **degree-scaling** (a Sum over the `recruits`
   edge set). Carried on a SEPARATE `recruits` edge type so the diffusive
   `projects_to` channel stays homogeneous + conservative. `g_rec` defaults 0 →
   the term is 0 → V1 reproduced exactly (verified byte-identical to the published
   seed-5 give sweep across the whole give range, and the seizure byte-identity
   test still green).
2. **Heterogeneous-degree hubs** — the harness adds `hub_k` extra long-range
   **bidirectional `recruits`** edges to designated hub areas, raising their
   recruits-degree. The diffusive grid is untouched (stays degree-4 everywhere),
   so **recruitment is the only channel that sees the hubs** — hubs = excitatory
   hyperconnectivity, cleanly isolated.

Both are default-off / byte-identity-preserving (the rule fires only on
`sz_managed_by`-edged areas; normal cognition is never touched).

## PREREGISTERED PREDICTIONS (directions)

### V2-P4 — recruitment coupling is PRO-ICTAL (give\* RISES with g_rec)

Homogeneous lattice, everything identical to the published central-onset give
fold (N=41, α=0.5, D=3, g=0.8, θ=1, r_focus=3), **only `g_rec` varied**.
Metric: give\* = the largest give in the grid at which the seizure persists
(`persists`: mean final-60-substep n_active > 5.0). Matched control: `g_rec=0`
(the published fold, give\*=0.5375).

> **PREDICTION:** give\*(g_rec) is a **strictly increasing** function of `g_rec`
> (give\*(g_rec>0) > 0.5375), and beyond some `g_rec` it **saturates at give\*≥1.0**
> — i.e. recruitment seizes even at **full graceful give (give=1.0)**, which the
> symmetric-diffusive `g` NEVER does. This matches the connectivity /
> hyperconnectivity literature (more excitatory coupling → seizure easier).

**Falsifier (reported loudly if it happens):** if give\* is flat or DECREASES
with `g_rec` (recruitment behaves protectively like diffusion), the model still
cannot represent excitatory recruitment — a persistent structural limit.

### V2-P5 — HUBS are the preferred onset locus (give\* higher at a hub)

Heterogeneous lattice: one HUB (hub_k long-range `recruits` edges) and one
matched NON-HUB at **equal eccentricity** (both distance 14.14 from center),
identical tight focal onset (r_onset=1) placed at each in turn on the **same**
lattice (only the onset locus differs = the matched control). Fixed g_rec=0.1
(the locus-sensitive regime from the pilot). Replicated across seeds AND across a
hub-side swap (hub at each corner in turn) to prove it is degree, not position.

> **PREDICTION:** give\*(HUB onset) > give\*(NON-HUB onset) by **at least one give
> grid step**, replicated across seeds and independent of which corner is the hub.
> A homogeneous (no-hub) lattice at the same locus matches the non-hub give\*.
> This matches the strong hub-onset literature.

**Falsifier (reported loudly):** give\*(HUB) ≤ give\*(NON-HUB) (no locus effect,
or hub protective) → the homogeneous-lattice limit persists even with recruitment.

### V2-P6 (EXPLORATORY, clearly marked) — source-escalation is a DIFFERENT pathology

`SEIZURE_SCIENCE.md` Thread 3 noted alpha (settlement-escalation) ⇒ seizure, and
that the SAME escalation MIS-WIRED TO THE SOURCE (aberrant precision) is the
known hallucination pathology. If P4+P5 land cleanly, model source-escalation and
test whether it yields a **DIFFERENT signature** — a **persistent, spatially
STATIONARY confabulated pattern** (high rank-1, near-zero front propagation),
NOT a spreading traveling wave. Prereg direction: source-escalation ⇒ persists
with LOW onset-propagation / LOW max-front relative to a recruitment seizure of
comparable amplitude. Marked exploratory; a null here is reported, not tuned away.

## Confirmatory grids (fixed now)

- **V2-P4:** g_rec ∈ {0, 0.025, 0.05, 0.1, 0.2, 0.4}; give ∈ {1.0, 0.9, 0.8, 0.7,
  0.65, 0.6, 0.575, 0.5375, 0.5, 0.45}; seeds {5,6,7}.
- **V2-P5:** g_rec=0.1, hub_k=16; give ∈ {0.95, 0.9, 0.85, 0.8, 0.75, 0.7, 0.65};
  seeds {5,6,7,8,9}; hub at (10,10) and (30,30) in turn; onset at hub vs non-hub;
  homogeneous control.
- **V2-P6 (if run):** source-escalation variant; compare rank-1 / front /
  persistence against a recruitment seizure.

## DISCLOSED PILOT (calibration only — not confirmatory)

Ran to set the give grids. (a) g_rec sweep at central onset: give=0.7 persists at
g_rec=0.05, give=1.0 persists at g_rec≥0.2 — give\* clearly rises, so the grid
must extend to give=1.0. (b) Hub onset (hub_k=16, g_rec=0.1): at give=0.85 the
hub-onset persisted (final ~31) while non-hub and homogeneous both died (0.0) —
so the give grid is centered on 0.65–0.95. The pilot fixed the intervals only;
the confirmatory directions above were registered before the confirmatory sweeps.
