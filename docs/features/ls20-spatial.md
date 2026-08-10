# LS20 / spatial reasoning (ARC-AGI-style)

Spatial and navigational reasoning on grid worlds in the style of the
**ARC-AGI** benchmark family — a from-scratch agent that discovers a world's
mechanics (which station transforms what, how a map connects) through its
own curiosity and predict-and-residual loop, then navigates it.

**Naming disambiguation:** this "ARC" is ARC-AGI, the spatial-reasoning
benchmark. It is unrelated to `docs/features/program-synthesis.md`'s "ARC
6," which is that project's own internal phase-6 label. A file named
`ARC_LS20_*` (filed under `docs/research/ls20/`) is this thread; a file
named `PROGRAM_SYNTHESIS_ARC6_*` is the other one.

## Understanding before winning

The headline framing, stated directly in the results record: **"winning is
a side effect of understanding — the true victory is knowledge."** A
powered run shows the agent's model of "which station applies which
transform" converging cleanly: surprise (predict-residual) drops from 1.0
to 0.0 exactly at the cycle every station has been modeled, in lockstep with
model accuracy rising from ~0 to 1.0 — a curiosity-driven world model
converging on ground truth, not a policy that happens to win episodes.

## Quanta navigation — the same dynamic-quantization reframe, spatial

The map itself is treated as a persistent observation **belief** — unknown
is absence, a first-class state, not a default zero. `SpaceQuantum` boxes
are decoded from that belief **per body shape** (a 1×1 and a 2×2 agent
route differently over the *same* underlying belief — config-space
erosion), **foveated** (decoding happens only in the current focus region,
reusing prior decode work incrementally rather than re-flooding the whole
map), and **N-dimensional with per-dimension resolution** — the flood does
not occur per pixel, it occurs at quanta, and a remainder routes to a finer
per-dimension split. This is `docs/features/dynamic-quantization.md`'s
codebook-growth loop applied to space itself: the Rust `space_quantize`
implements an epoch-gated Bellman flood over portals, N-dimensional hops via
the `ControlResponse` chain, multi-source frontier-seek exploration, and
stale/retired quanta lifecycles — all as rules, not Python control flow.

Cell-mode navigation (the older, non-quanta representation) remains
available and byte-identical to its pre-quanta baseline; world adapters opt
into the quanta representation via `nav_repr="quanta"`.

## Transformation as a quantum step in a dimension

A rotate/recolour/translate action is not a separate operator class from
perception — it *is* the object's quantum stepping along one dimension of
the same codebook the object was recognized against. This is why
`docs/features/dynamic-quantization.md`'s growth ladder (exact recognize →
transform-in-basis → infer-a-new-dimension → mint novelty) unifies ARC-style
"what transform happened here" tasks with ordinary object recognition
rather than needing a separate transform-detection mechanism.

## Where the code lives

- Rust: `runners/dsl/src/space_quantize.rs`.
- Seeds: `seeds/quanta_navigation.json` (14 `qf_*` rules).
- World adapters: `worlds/arc_ls20_*.py` (`arc_ls20_consume.py`,
  `arc_ls20_flash.py`, `arc_ls20_percell*.py`, `arc_ls20_scenario.py`,
  `arc_ls20_seek.py`, `arc_ls20_see.py`, `arc_ls20_triple.py`,
  `arc_ls20_understanding.py`), plus `worlds/arc.py` (a thinner, more
  general ARC-AGI-3 world adapter — a `Game` node + one `CellC<v>` per
  non-empty cell, translating each `Frame` mechanically).
- Adapters opt in to quanta mode via `nav_repr="quanta"`; see
  `domains/spatial_sense.py`/`domains/spatial_priors.py` and
  `domains/spatial_routing` Term builders (per `CLAUDE.md`'s directory
  notes) for the routing layer this sits under.
- Gates: `tests/test_quanta_navigation_migrated.py` (8/8 — partial-maze
  memory, 3D, two-body, per-dimension split, foveation), plus the
  `arc_ls20_*`-tagged migrated tests.

## For the full history

`docs/research/ls20/` holds the 33 `LS20_*` prereg/results pairs plus the
`ARC_LS20_*` documents (pixel-segmentation and eye-plan work). `CLAUDE.md`'s
own "quanta navigation LANDED" and "Transformation = quantum change..."
sections carry the fullest technical description of the mechanism and its
gates. See `docs/research/ls20/INDEX.md`.
