# RESULTS — Fast-tick, surprise-gated town (block 283000)

All five signatures reproduce. **`test_durative_town_migrated.py` 5/5.** Pure-Python
TIME-MODEL demonstrator — no seed, no substrate, no Rust.

## The measured signatures

| # | signature | measured |
|---|---|---|
| 1 | no teleport | one hop per master tick (max step = **1** cell); the walker still arrives |
| 2 | predicted walk → no decisions | a known solo route, nobody unexpected → **0 decisions** (pure no-op continuation) |
| 3 | **surprise gates decisions, not encounters** | same crossing geometry: UNPREDICTED meeting → **≥1 decision at the meeting tick**; PREDICTED meeting (mutual `expect`) → **0 decisions at the meeting** — yet still a habitual chat (≥1 turn) |
| 4 | conversation along a route | two residents walking a shared road → **≥2 turns**, ≥1 utterance spoken **while the speaker is still walking** |
| 5 | decision sparsity | mostly-predicted town → decisions **≪ residents × ticks** |

## What this establishes

The clock reframe holds and is measurable. **A decision is a surprise, not a
heartbeat.** Signature 3 is the load-bearing one: two runs with identical geometry
differ only in the held prediction, and only the *unpredicted* meeting fires a
decision — proving the trigger is the prediction residual, not the encounter event.
Signature 2 shows the common case (executing a known plan) costs nothing; signature
4 shows the payoff the coarse teleport tick could not represent — a conversation
that spans a travelled route, spoken on the move. It is residual all the way:
surprise gates *whether* to decide; the decision core's own residual (282000-a)
gates *how deep*; and the habitual fast path is simply "continue the durative
action" between surprises — which is exactly the internalized targeting the 282000-c
finding wanted.

## Honest scope / residuals

- **Demonstrator, not the production agent.** The held prediction (`expect`) is a
  Python-dict stand-in for a graph-native held-prediction node; computing surprise
  is a mechanical residual comparison (what perception already does), not an agent
  decision. The actual conduct/speech CHOICE at a surprise point is the collapse
  (282000) / speech faculty (278000), scaffolded here (a fixed adjacency-pair
  sequence stands in for real utterance content).
- **Prediction is presence-only, so a parting can surprise.** `expect` is a set of
  names, not a trajectory; a predicted companion peeling off registers as a
  surprise (their staying was predicted). Richer trajectory prediction is a later
  refinement; the meeting-tick discriminator (signature 3) is clean regardless.
- **Graph-native realization is the next rung** — a `SocialPrediction` node + a
  surprise RULE that fires the conduct collapse on divergence + a prediction-update
  rule, reusing perception's held-surface/residual machinery. Then this composes
  directly with the 282000 supergraph town (decisions fire on surprise, the collapse
  runs scoped, replay internalizes the habitual continuation).
