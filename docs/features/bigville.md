# Bigville

A live "glass-box town" of graph-resident cognitive agents — a society
simulation on the same (G, Γ) substrate as everything else. Townspeople have
drives, affect, bonds, memory, jobs, coin, property, health, and a place on a
grid; they work, trade, gossip, fall ill, grieve, scheme, steal, and are
governed by recognized law. It is the social analogue of "the agent plays
Doom" or "the agent has an eye": one Rust runtime executing graph data, no
per-step LLM, no per-resident hand-written script.

## Scale

By the numbers (from the design reference in
`docs/research/bigville/BIGVILLE_DESIGN_REFERENCE.md`): roughly 100
`bigville_*.json` seeds, ~80 `bigville_*_world.py` adapters (`worlds/`), and
~140 `BIGVILLE_*.md` prereg/results documents — one of the largest single
subsystems in the tree by document count, second only to vision.

## What's actually in it

Reading the design reference (which exists specifically to stop new work
from reinventing an already-canonical mechanism) gives the honest shape:
governance (council, law, courts, bylaws), economy (labour, trade, coin,
firms, fiscal policy, prices), demography (fertility, infancy, school,
death), affect and bonds (first-class interpersonal relationship state, per
project memory `ozma_bond_is_first_class_interpersonal_affect`), a news/
publisher role, a written/legislative language, weather and settlement
geography, and — per project memory `ozma_town_time_is_the_bell` — one
shared clock every resident's cognition ticks against.

Adjacent, smaller multi-agent threads that are not literally "Bigville" but
share its game-theoretic/social-simulation character and are filed alongside
it: **HARVEST** (a commons social-dilemma over a shared resource, with
real inter-agent communication) and **SPITE** (extending the same
commons world's emotion economy into the negative-social region — spite as
a strategy, not just cooperation), **LANGSIM** (a language-limitation map
for N agents in a richer economy coordinating through real produced
utterances — what breaks first, in what order, when the group must actually
talk to get anything done), the **ABUSIVE_RELATIONSHIPS** social-network
scoping work, and **GLASS_BOX_SOCIETY** ("language is a coordination
technology" — a from-scratch re-run of the first rung of multi-agent
communication under the clean engine).

## Known-duplicated / known-broken (as of the design reference)

The design reference is explicit that this subsystem's size is itself a
maintenance risk, and names at least one mechanism (recognition) as
duplicated three different ways across the codebase. Anyone extending
Bigville should read `docs/research/bigville/BIGVILLE_DESIGN_REFERENCE.md`
§3/§6 before adding a new recognition mechanism, relationship scalar,
verdict rule, or affect node — several already have canonical forms.

## Where the code lives

- World adapters: `worlds/bigville_*_world.py` (the majority of the ~130
  files under `worlds/`).
- Seeds: `seeds/bigville_*.json` and the smaller `harvest_*.json`,
  `langsim_*.json` neighbors.
- Viewer: `web/townview/` — a production-quality single-page app that
  renders the town as a pixel-art world; click any resident to read their
  held state, journal, and bonds straight out of the graph. Two modes:
  replay a recorded `play.json`, or connect live.
- Gates: the large `tests/test_bigville_*_migrated.py` family (dozens of
  files — action, affect, bond, build, council, court, decision, doctor,
  drama, econ, fert, fin, fisc, goal, infant, land, lang, law, life, loop,
  loud, move, need, news, scale, school, skill, speech, time, viol, ...).

## For the full history

`docs/research/bigville/BIGVILLE_DESIGN_REFERENCE.md` is the entry point —
it is itself a synthesized reference doc, not a raw prereg/results pair, and
is the closest thing this subsystem has to a map of itself. The full
prereg/results corpus (one pair per capability landed) is indexed at
`docs/research/bigville/INDEX.md`.
