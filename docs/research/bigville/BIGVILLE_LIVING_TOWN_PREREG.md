# PREREG — The full fold-in: conduct spine into the live town (block 289000)

`seed_claim 289000 289999`: CLEAN. Canonical `.so` `fd82dc2978dbb055496dd82390ac2ebe`;
NO Rust. No new seed — composes the 280-287 spine.

## The claim
The 280-287 conduct spine wired into the LIVE integ5/play town. The town keeps ALL
its own mechanics (produce/buy/trade/paper/council/life-death/routing); a CONDUCT
LAYER -- the residents' minds, a BigvilleSurpriseTownWorld mirroring the residents as
ConductState minds with held Bonds -- is the agent graph. Architecture = the
project's own split: the TOWN is the WORLD (moves bodies, provides observations = who
is co-present, from real positions); the conduct layer is the AGENT GRAPH. Each town
tick: read co-presence from the town's real positions, drive the surprise-gated
Bond-directed conduct collapse (with the 287000 fast-path bond signal), and write the
resulting conduct back into the town's event feed. ADDITIVE: the town's substrate +
mechanics are untouched.

## Signatures
1. Conduct flows into the town -- the layer writes real help/give/harm events into
   the town's own event feed (so paper/narration/player surface them).
2. Violence is rare AND Bond-directed -- harm is a small minority of conduct and is
   aimed at a RESENTED partner (a feud), never a random or a friend.
3. Help is the norm (prosocial default).
4. The town survives the fold-in (residents alive, feed flows; no mass death).
5. Conduct is cleanly disableable (conduct=False -> no layer, no events).
6. No Python agent decision in the fold-in adapter.

## Discipline
Additive `bigville_living_town_world.py` (a BigvillePlayWorld subclass) + a
parameter on `bigville_surprise_town_world.py` (extra_seeds / fast_gain, default =
byte-compatible) + gate. Composes the 280-287 spine; ZERO new Rust. Canonical `.so`
untouched.
