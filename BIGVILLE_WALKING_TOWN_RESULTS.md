# RESULTS — Self-driving walking town (block 285000)

All five signatures reproduce. **`test_walking_town_migrated.py` 5/5 + surprise /
durative / conduct / baseline 27/27 = 32/32 on the canonical engine
`fd82dc2978dbb055496dd82390ac2ebe`**. `runners/dsl` diff EMPTY — ZERO new Rust.

## What landed

- `worlds/bigville_walking_town_world.py` — the self-driving town: subclasses the
  284000 surprise town, adds positions + goals + one-hop movement, derives
  co-presence from positions (`sees` edges), and runs the surprise-gated conduct
  loop per master tick. No hand-fed scene.
- Enactment added to `bigville_surprise_town_world.py`: a chosen directed act now
  applies its health delta on the target (harm −25 / help +15).

## The measured trace

A walks (0,0)→(8,0) with a friend B walking alongside (predicted); a rival E (whom A
does **not** predict) crosses A's route from the south at x=4:

| tick | positions | outcome |
|---|---|---|
| 1–2 | A/B walk east, E walks north, apart | no-ops |
| **3** | A=(3,0), **E=(4,0)** — the crossing | A surprised → **harm@E** (resented rival, directed); E surprised by A → help@A; enacted → **E health 100→75** |
| 4–9 | E absorbed / walk apart | no-ops |

One act of violence across nine ticks, at the surprise, directed at the resented —
`O(surprise)`, max hop 1 (no teleport), all derived from positions.

**The control is the payoff:** identical geometry, but with A *predicting* E, the
crossing fires no surprise → A never deliberates → **E is never harmed (health 100)**.
Violence is surprise-driven; bracing for the encounter routes it to the habitual
(no-op) path.

## What this establishes

The whole arc is one self-driving loop: **a fast hop clock, movement as a durative
no-op, decisions on surprise (a rule), Bond-directed conduct via the scoped
supergraph collapse, enacted on the world.** No global tick, no teleport, no
everyone-decides-every-frame — the town runs on surprise. The player-facing picture
falls straight out of `pos_log` (hop-by-hop positions) + `decided` (the sparse,
located, directed conduct events).

## Honest residuals (NOT patched)

- **Predicting a threat suppresses the response.** The control shows a *predicted*
  rival draws no conduct at all — because a predicted encounter is a no-op. Whether a
  foreseen threat should still trigger a (habitual, pre-planned) response is the
  internalization refinement: the prediction should carry the learned response, not
  just cancel the surprise. This is the same fast-path-should-be-learned thread from
  282000-c / 283000.
- **Presence-only prediction; adapter still loads net input + arms per surprised
  resident** (284000 residuals carry over).
- **Not yet the live integ5/50-resident town or the published player.** This is a
  self-contained harness proving the end-to-end loop; folding it into integ5 (real
  map, existing social mechanics) + surfacing it in the player is the remaining
  integration. Perf is clear (movement O(residents), decisions O(surprise)).
