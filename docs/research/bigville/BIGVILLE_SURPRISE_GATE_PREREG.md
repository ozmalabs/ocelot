# PREREG — Graph-native surprise gate (block 284000)

`seed_claim 284000 284999`: CLEAN. Canonical `.so` `fd82dc2978dbb055496dd82390ac2ebe`;
NO Rust.

## The claim

The graph-native realization of block 283000's Python time-model demonstrator: a
decision fires on SURPRISE (observation != held social prediction) as RULES, and
only a surprised resident runs its conduct collapse. Composes surprise (284000) +
supergraph conduct (282000) + scoped decision core (279000 v1.1.0) + affordances
(280000). A resident holds a SocialPrediction as `predicts_near` edges; the adapter
mints observation as `sees` edges (proximity, mechanical). Then:
- `sg_surprise` (RULE): a `sees` with no matching `predicts_near` sets
  `m.surprised=1` -- the prediction residual, computed by a rule; a PREDICTED
  co-presence fires nothing.
- `sg_absorb` (RULE): the same unpredicted `sees` adds `predicts_near`, so the
  prediction absorbs the surprise (held-prediction update).
- `sg_provide_directed` (RULE): a directed option is afforded iff ITS OWN target is
  seen.
`m.surprised` gates the conduct collapse (the adapter dispatches only surprised
residents to the 282000 collapse -- a mechanical dispatch on a rule-computed flag).

## Signatures (deterministic)

1. **Predicted meeting → no decision** — A predicts B; meeting B fires no surprise
   and no collapse (a no-op continuation).
2. **Unpredicted encounter → surprise + directed conduct** — an unpredicted rival
   appears → the surprise rule flags A → A's supergraph collapse runs and directs
   harm at the resented rival.
3. **Prediction absorbs → no re-surprise** — after the surprise, re-seeing the same
   other is no longer surprising.
4. **Decision sparsity** — over many ticks of a stable scene, decisions = the
   initial surprises only (O(surprise)).
5. **Surprise is a RULE** — edge-absence `Not(Exists(Neighbours predicts_near ==
   o))` (allocentric/need-drive precedent); the adapter reads the flag, holds no
   rule engine and no argmax over a valuation.

## Discipline

Additive `bigville_surprise_gate.json` (3 rules, self_load_only) + world adapter +
gate; composes existing DSL Terms + edge ops (add_edge/remove_edge/set_attr) —
ZERO new Rust. Does not touch the gated 279000 core. Canonical `.so` untouched.
