# Shared-substrate multi-sheet visual-task scope pilot preregistration

Date: 2026-09-27. One-seed feasibility/semantic pilot; a successful result must be followed by a preregistered multi-seed replication.

## Question

On two full 4×4 lateral visual sheets sharing one native substrate, does the authored global `st_settle` fold make sheet A's K=16 orientation response depend on sheet B's simultaneous visual input, and does Retina-root scoping remove that dependence while preserving A's response?

## Workload and arms

Create one substrate per arm and load the vision manifests once. Build two separate 16×16 Retina / lateral / SUnit anatomies in that substrate, each with its own `Retina -has_sunit-> SUnit` membership and 4×4 SUnit lattice. The second world reuses the first world's rule installation and shared singleton parameters. Use seed 20260934 and four arms in this order: global/B-blank, global/B-grating, root-scoped/B-blank, root-scoped/B-grating. Root-scoped changes exactly the two SUnit population folds in `st_settle` to the matched A or B Retina's `has_sunit` members. No production manifests or engine sources are modified.

Develop both retinal worlds for 3,000 steps each with cortical learning inert; record each retina's start/end clock and exact requested development steps. The existing `WaveWorld.step` returns the retina clock, not native termination status, so development stop status is not claimed. Adapt theta for 2,000 paired presentations using the same seeded random grating on both retinas; freeze all learning before readout. In the readout, vary A through `cell_stats(key="rate", period=4, K=16)`. B receives either a blank binary frame or a fixed 0-degree binary grating on every A presentation. Use full-rescan `run_rules_report(..., detect_cycles=True)` and retain every adaptation/probe status and progress count. Capture exact root memberships, complete A tuning/OSI arrays, B condition, and complete ordered `oo_post` vectors immediately before/after each readout.

## Gates

Require all four arms to build with exactly two distinct Retina roots, 16 SUnits per root, no overlapping memberships, and exactly one `SettleParams`/`OnOffParams`/`LatParams`/`ComposeParams` singleton where applicable. Require exact requested development clock advances, all adaptation/probe reports to end as fixed point or repeated state (no cap), nonzero finite A responses, and zero within-readout weight drift. Independently recompute A OSI and compare the complete tuning arrays.

The task-separation prediction is that root-scoped A tuning is unchanged by B's stimulus (max absolute delta ≤1e-10), while the global-fold arm's A tuning changes by more than 1e-8. If neither or both occur, retain the result as a failed/disconfirming pilot; do not tune the contrast after observing it. The test is a semantic task-interference pilot, not a natural-task prevalence estimate, performance benchmark, or speedup study.

## Claim boundary and follow-up

One seed can establish shared-builder feasibility and whether the intervention is detectable in this visual task. It cannot estimate variability. If gates and the registered directional contrast pass, replicate with at least three new seeds and counterbalanced arm order. If the common-substrate builder fails its topology/singleton invariants, stop and repair the fixture before interpretation.
