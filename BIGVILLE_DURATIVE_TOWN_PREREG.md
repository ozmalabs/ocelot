# PREREG — Fast-tick, surprise-gated town (block 283000)

`seed_claim 283000 283999`: CLEAN. No seed, no substrate, no Rust — a pure-Python
TIME-MODEL demonstrator harness.

## The claim (the architect's reframe)

The town's tick scaling was wrong: a coarse tick made a whole walk happen "in one
tick," so residents teleported (the play world's hop-by-hop movement was only a viz
hack over a coarse *decision* tick). The master tick should be the **hop** — fast —
and a **decision** should fire on **SURPRISE**, not on a clock and not on an
enumerated "encounter/arrival/turn" event list. Surprise = observation ≠ the
resident's held prediction — the SAME held-prediction residual perception runs on
(held surface = prediction; new frame = order-0 residual). It is residual all the
way: surprise gates *whether* to decide; the decision core's own residual (282000-a)
gates *how deep*. Between surprises a resident just continues its durative action —
the habitual fast path — so decisions are **O(surprise)**, not O(residents × ticks):
a faster clock that costs *less*. The payoff the fast clock unlocks: a conversation
that unfolds turn-by-turn ALONG a shared route while both walk.

## Pre-registered signatures (deterministic)

1. **No teleport** — one hop per master tick (max step = 1 cell).
2. **A predicted walk fires no decisions** — a known solo route with nobody
   unexpected → 0 decisions (pure no-op continuation).
3. **Surprise gates decisions, not encounters (THE discriminator)** — identical
   crossing geometry: an UNPREDICTED meeting fires a decision at the meeting tick; a
   PREDICTED meeting (mutual `expect`) fires NONE — yet still produces a habitual
   chat. This is what proves the trigger is *surprise*, not the event.
4. **Conversation along a route** — two residents walking a shared road converse
   over multiple turns, utterances spoken while the speaker is still WALKING.
5. **Decision sparsity** — in a mostly-predicted town, decisions ≪ residents × ticks.

## Honest scope

This harness demonstrates the **CLOCK** (fast hop tick, durative walk, surprise-
gated decision sparsity, walk-and-talk). It is NOT the production agent:
- the prediction (`expect`) held in a Python dict is a demonstrator **stand-in** for
  a graph-native held-prediction node (perception's held-surface/residual is the
  template); computing surprise is a mechanical residual comparison, not an agent
  decision;
- the actual conduct/speech **choice** at a surprise point is the collapse (282000)
  / the speech faculty (278000), deliberately out of scope here (scaffolded).

The graph-native realization — a `SocialPrediction` node + a surprise RULE that
fires the conduct collapse when observation diverges + a prediction-update rule — is
the committed next rung, reusing the existing held-prediction machinery. No Rust,
no seed touched.
