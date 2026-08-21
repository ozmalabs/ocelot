# Are ties consequential? Measured — and the answer is domain-split

**Status: measurement complete. No behaviour changed** (`refuse_all` was run as a probe;
the committed default remains `off`). This triggers a NO-GO condition written in
`DECISION_LAYER_PREREG.md` §B.4 before the result was known.

## The question

`ARGMIN_TIE_CENSUS_RESULTS.md` measured *how often* selectors hit an exact tie broken by
enumeration order: 2,041 of 174,750 firings across five workloads, spanning 0% to 64%.
Counting ties says nothing about whether the choice matters. `refuse_all` — a mode
`argmin_tie.rs` has always shipped and which had never been run before this session —
answers that directly: make every non-unique extremum refuse, and see what breaks.

## Result

| workload | probe | outcome |
|---|---|---|
| conversation (5 utterances) | replies compared | **0 of 5 differ** |
| ls20 + quanta (25 tests) | pass/fail vs baseline | **7 fail, 18 pass** (baseline 25/25) |

**Ties are inconsequential in conversation and load-bearing in space.**

All seven failures are routing:

```
test_arc_ls20_mapnav_migrated.py::test_g_walled_quanta_beats_greedy
test_arc_ls20_mapnav_migrated.py::test_g_open_parity_route_equivalent
test_quanta_navigation_migrated.py::test_rooms_decode_and_route_through_the_hole
test_quanta_navigation_migrated.py::test_partial_maze_frontiers_exploration_persistence_completion
test_quanta_navigation_migrated.py::test_3d_lattice_wall_plane_with_hole_routes
test_quanta_navigation_migrated.py::test_two_bodies_one_belief_different_quanta_and_routes
test_quanta_navigation_migrated.py::test_interior_block_splits_only_the_blocked_dim_and_reroutes
```

Not a scattering across unrelated faculties. One mechanism.

## Why space and not conversation

On a lattice, **equal-cost alternatives are the norm rather than the exception**. Two
routes of the same length around an obstacle, four neighbours at the same flood distance,
a symmetric hole with mirror approaches — these are geometric facts, not modelling
accidents. That is also why ls20 and quanta were the two workloads whose ties were
**entirely genuine, with zero pick-any idiom** (`ARGMIN_TIE_CENSUS_RESULTS.md`
§Multi-workload census): 1,187 and 114 real non-unique extrema.

Conversation has few symmetric alternatives, so its ties were mostly one site ranking a
constant, and refusing them cost nothing.

## The finding

**Enumeration order is silently implementing a navigation tie-break policy that nobody
wrote.**

It works — the routing tests pass, and have passed for as long as they have existed. But
the rule that decides between two equally-good next hops is not represented anywhere in
the graph. It is a consequence of `FxHashMap` iteration and rule insertion order. Nothing
in `seeds/quanta_navigation.json` expresses a preference, because nothing needs to: the
engine has been supplying one for free.

This is the same defect class as every other finding this session — an outcome produced by
implicit state with no signal — but with the sign reversed. Elsewhere the implicit
mechanism was inert (`effect_audit`: zero firings) or harmless (conversation ties: no
observable difference). Here it is **load-bearing**. Removing it does not expose a latent
bug; it removes a working mechanism that was never declared.

## Consequence for the decision-layer prereg

`DECISION_LAYER_PREREG.md` §B.4, written before this was run:

> If `refuse_all` on the current engine shows that refusing ties breaks a large fraction of
> the bench, the seed corpus depends on order-decided outcomes far more than the census
> suggests, and the honest response is to report that and stop — not to build selection on
> top of a corpus that needs the old semantics.

**28% of the spatial slice fails. The gate is triggered.** Stage B as drafted — an `argmax`
over a feasible family where a non-unique maximum becomes a represented SET-TIE — would
make the agent unable to route, because a SET-TIE is precisely a refusal to choose and
routing requires a choice.

That does not make the theory wrong; it makes the missing piece visible. v22's own answer
is that a tie must be resolved by *represented* structure rather than by order or retry.

**What that represented structure should be is worked out in
`AFFECT_WEIGHTED_ROUTE_VALUATION_DESIGN.md`, and the answer reframes this result.** Human
route choice between equal-length options is a *weighted valuation with a felt-cost term*,
not a distance calculation with a tie-break attached — and the weight can be large enough
that feeling overrules distance outright. On that reading a tie is not the phenomenon but
the **diagnostic**: it is where the other terms cancel and the missing term becomes
visible. Ocelot already carries both halves and no wire between them — `qf_relax` relaxes
through a per-portal `cost` attribute, and `EmotionParams`/`mood`/`affect_coupling` exist,
with **zero** references to any of them anywhere in `quanta_navigation.json`.
The work that would make Stage B viable is therefore **seed-data, not engine**: give the
navigation rules an explicit tie-break — a canonical direction preference, a
lowest-coordinate rule, a held heading — so that ties are resolved by something written
down. Until that exists, order is the policy, and replacing it with a refusal removes
capability.

## What this does not establish

- **That the current tie-breaks are *good*.** The tests assert specific routes and pass, so
  order currently produces acceptable answers on those fixtures. Whether route *quality*
  depends on which tied candidate wins — and whether a different iteration order would
  degrade it — is unmeasured. That is the sharper question this result raises and does not
  answer.
- **That 7/25 generalises.** One slice, two seeds. ARC (159,813 firings, 258 genuine ties)
  was not run under `refuse_all` and its dependence is unknown.
- **Anything about `refuse_min`.** Only `refuse_all` was run.

## Reproduce

```bash
# baseline
python3 -m pytest -q tests/test_arc_ls20_see_migrated.py \
    tests/test_arc_ls20_mapnav_migrated.py tests/test_quanta_navigation_migrated.py
# every tie refused
OZMA_ARGMIN_UNIQUE=refuse_all python3 -m pytest -q tests/test_arc_ls20_see_migrated.py \
    tests/test_arc_ls20_mapnav_migrated.py tests/test_quanta_navigation_migrated.py
```
