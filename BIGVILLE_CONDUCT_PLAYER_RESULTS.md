# RESULTS — The self-driving conduct spine, made watchable (block 288000)

A playable artifact of the 280–287 conduct spine. Published:
**https://claude.ai/code/artifact/2d777bee-4556-4bc0-9051-fd28944746df**

## What it shows

Six residents, each a full graph-resident mind, walking a 12×8 town toward a shared
square. Every position and event is a REAL read of the running substrate (via
`scripts/conduct_play_run.py` over `BigvilleWalkingTownWorld`) — no scripted
dialogue, no global clock:

- **They walk** one hop per master tick (interpolated for smooth motion).
- **Most ticks nobody decides** — a resident continues its route while the world
  unfolds as predicted (the surprise clock; decisions are `O(surprise)`).
- **Friends greet** at the square (help events, prosocial).
- **The one feud** (Ada resents Eli, and does NOT predict him) resolves in the only
  act of violence: at tick 8, unpredicted co-presence → surprise → **Ada strikes
  Eli** (directed at the resented, Eli 100→75).
- **Inspector**: click a resident to read their held Bonds (warm / hostile /
  neutral) and what they predict.
- **Chronicle**: every decision the town made, tagged reflex vs deliberated.

## Provenance

- `scripts/conduct_play_run.py` — the scenario + exporter (real walking-town reads).
- `results/conduct_play/play.json` — the exported play document (5.2 KB).
- `results/conduct_play/conduct_play.html` — the published player source (self-
  contained; theme-aware; canvas map + timeline + inspector + chronicle).

## Honest scope

This visualises the STANDALONE conduct spine (the walking/surprise/supergraph town),
not the rich integ5 town (map / institutions / paper / council / trade). The
degenerate "everyone greets Ada at the square" reflects the neutral-target arbitrary
tie (the 287000 fast-path bond signal is not loaded in the walking town yet); the
feud harm is the load-bearing, correctly-directed event. Folding the spine into the
live integ5/50-resident town + its player is the deferred big integration (task).
