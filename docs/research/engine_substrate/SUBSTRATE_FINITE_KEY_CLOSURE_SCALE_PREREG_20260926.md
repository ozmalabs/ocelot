# Finite-key closure scale gate — preregistration (2026-09-26)

**Status:** confirmatory within the named synthetic fragment and generated family; not a general engine termination theorem. This follows the finite-key monotone closure proof in `SUBSTRATE_FINITE_KEY_CLOSURE_TERMINATION_20260926.md` and expands beyond its N=4 validation.

## Frozen family

- Initial nodes: `N ∈ {4,16,64}`.
- Initial topologies: directed cycle and dense directed no-self-loop graph; every initial node has at least one incoming `link` edge.
- Fixed mint signatures / interacting rules: `M ∈ {1,2,4}`; each positive `link(x,y)` match makes one `Witness{tag:literal}` available via `add_node_if_absent` and inserts `link(y,witness)` with empty attrs.
- For M=4, literal `tag` types are null, boolean, integer, and string; prefixes at smaller M use null, bool, then integer. This exercises all scalar JSON types accepted by the analyzer and runtime loader.
- Three fresh substrate constructions per N×topology×M cell; 54 cases total. Rule order is fixed ascending signature index.
- Initial graph is present before rules are installed. Closure uses a fixed progress budget of 200,000 with cycle detection disabled.

## Outcomes and checks

For each cell, run the static analyzer on the complete initial node IDs/edge facts. Independently compute the expected terminal nodes and edges: all initial edges plus every edge from each initial node and minted witness node to every minted witness. Check native status is fixed point, exact terminal graph equality, and `progress_steps ≤ M + E(N+M)^2 − e₀`; report passes, firings, fact counts, and the bound. Preserve all cases and raw graph states. The separate analyzer recomputes topology, graph equality, and bound from raw outputs. No latency claim is a primary endpoint.

## Claim limit

This tests one generated positive-rule schema and fixed rule order, not arbitrary programs accepted by the analyzer; tests behavior at N≤64, not all finite graphs. It can strengthen validation of finite-key termination under sparse/dense initial states, but cannot establish weak acyclicity, unrestricted chase termination, or runtime/admission grammar equivalence beyond the generated rule forms. Deletions, replacements, computed values, negative guards, external dependencies, and dynamic rule patching remain outside the fragment.

## Execution

```sh
PYTHONPATH=.:runners/dsl/python python3 scripts/verify_mint_termination_scale_v1.py
python3 scripts/analyze_mint_termination_scale_v1.py
```
