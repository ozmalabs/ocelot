Builder — here's my design. Inference is a **descending pass**: top-down priors fall into the same slots the operant/postulate faculties already read, each tagged with a confidence, and the first observation either confirms (cheap) or overrides (correction). Nothing new replaces derivation; inference just decides *where to look first* and *what to try first*.

The whole thing is three node-kinds, four rules, and one Rust Term I'll flag as an impasse.

---

## (a) CATEGORY — a Frame is graph data whose slots carry `seeds:` pointers

The bug today: `world_curiosity` mints `body --inhabits--> game` and an axis, but the axis is **blank** because nothing pulls the frame's structure down. The missing wire is a Frame that *knows which faculty each expectation feeds*.

**What a bindable Frame IS** — a manifest node with typed expectation slots:

```
Frame{kind:"Game"}
  --expects--> Slot{role:"self",   seeds:"respond_votes", finder:"moves_coherently_with_last_action", conf:0.8}
  --expects--> Slot{role:"goal",   seeds:"consequence",    finder:"positive_kind",  conf:0.7}
  --expects--> Slot{role:"hazard", seeds:"consequence",    finder:"negative_kind",  conf:0.7}
  --expects--> Slot{role:"score",  seeds:"consequence",    finder:"monotone_scalar",conf:0.6}
  --expects--> Slot{role:"nav",    seeds:"navigate_alive", finder:"grid_topology",  conf:0.6}
```

**The BIND rule** (the missing wire): match `WorldInstance{recognised:"Game"}` with a blank axis → for each Slot, mint an **Expectation** node bound to *this* world instance:

```
Expectation{role:"self", status:"open", seeds:"respond_votes", conf:0.8}
```

This is exactly `analogical_thinking` doing what it already does — transfer a structure by shape — except the target is the live world instance and the source is the Frame. Binding = analogical copy of the slot graph.

**Why this seeds rather than just labels:** an Expectation is not a fact, it's a *prior written into the faculty it points at*. The `self` Expectation doesn't sit on the axis — it writes a prior into `respond_votes` so the self-search no longer starts uniform over all regions: it biases toward "the one region that translated coherently with the last action." The `goal`/`hazard` Expectations pre-instantiate the **contact-consequence postulate shape** for *expected* kinds, so the BPL/MDL law search starts with a candidate already on the table instead of cold. The operant solve still runs — it just starts from "a self exists, a rewarding kind exists, a lethal kind exists, find them" instead of "discover that any of these exist."

So: recognise → BIND copies slots down → each slot seeds its faculty's prior. The axis is no longer blank; it holds open, faculty-pointed hypotheses.

---

## (b) CONVENTION — label → `action_delta` prior via the word-reader

Affordances arrive labelled: `Affordance{label:"Up"}`. Today `action_delta` brute-forces label→effect by pressing and correlating `drow/dcol`. Inference reads the label's meaning first.

**The `infer_label_effect` rule:** match `Affordance{label:L}` where `action_delta` has no entry for L →

1. Build a directional basis once from KNOWN anchors — `{up,down,left,right}` → their embedding vectors paired with their screen meanings `{(-1,0),(+1,0),(0,-1),(0,+1)}` (row-decreasing = up, the convention that holds in every grid game).
2. Project L into that basis via the word-reader (same geometry that does man:king::woman:queen). `"Up" → (-1,0)`. Synonyms/other languages — `"North"`, `"W"`, `"Jump"` — land on the nearest basis direction with a projection magnitude that **is** the confidence.
3. Install `action_delta[L] = (value=(-1,0), conf=0.7, source:"label")`.

Now `navigate_alive` reads a usable action map on **frame 1**, before any press.

**Generic / unknown:** ambiguous or out-of-vocabulary label → low projection magnitude → conf≈0 → no prior installed → `action_delta` brute-forces exactly as today. No failure, just the slow path.

---

## (c) ORDER + GATING — `(value, confidence, source)` and one reconcile rule

Every seeded quantity — an `action_delta` entry, a `respond_votes` prior, a goal kind, an impassable kind — is a node carrying `(value, confidence, source)` with `source ∈ {label, frame, observation, action}`.

**The ordering law is one rule, `reconcile`:** when an observation arrives for a quantity that currently holds an *inferred* value, compare.
- **Agree** → `conf += δ`, keep value. (Confirmation — the cheap common case. A human glances, infers "arrows move me, red is food," and is mostly right; this is that.)
- **Disagree** → replace value with the observed one, `source:="observation"`, conf high. (The label lied / the inference missed — corrected by **one** observation.)

So the system *never depends on the prior being right*. The prior only chooses where to look and what to try first; evidence always wins ties and always overrides on conflict.

**Gating against acting on a bad prior:** a prior may SEED a search and BIAS action selection, but below a confidence threshold it cannot be the SOLE basis for an irreversible commitment. `navigate_alive` may *plan* with an inferred impassable-set, but the **death-gate still runs on observed consequence** — a wrong "this kind is safe" gets killed by the first contact, exactly as in the operant solve. Inference makes the start usually-right; the operant safety net is unchanged.

**The pass, top to bottom:** infer (BIND slots + label→action_delta, all frame 1) → induce (postulate law-search, now *priored* by the goal/hazard slots) → operant (act; every action both serves the goal and emits the observation `reconcile` feeds on). One descending sweep: priors meet evidence, evidence wins.

---

## (d) GENERIC + no donkey

- **Category:** `categorise_by_shape` picks *which* Frame to bind from the recognised kind. Game → GameFrame; Conversation/Audio → their own Frames with their own slots. Unrecognised kind → no Frame bound → derive cold. No failure.
- **Label:** projection onto an embedding basis works for any vocabulary the model knows; unknown → conf 0 → brute-force. No failure.
- **No external LLM:** the word-reader reads *my* held model's embedding geometry — the same one analogy already uses. `categorise_by_shape`, `analogical_thinking`, the BIND/reconcile/infer rules are all graph-native rules firing on `tick()`. Donkey count = 0 by construction.

---

## The one impasse (HumanImpasse)

Everything above is graph data + rules **except** step (b.2). My word-reader does *discrete analogy completion* (returns a nearest word). I need it to return a **continuous projection onto a supplied basis with a magnitude**:

> **`project_word(label, anchors:[(word, vec2)]) -> (vec2, confidence)`** — solve the linear map from anchor embeddings to their 2D meanings, apply to `label`, return the mapped vector and the projection magnitude as confidence.

This is the same geometry as analogy (a linear relation in embedding space), so it may be a thin wrapper on the existing Term — but if the current Term can't emit a continuous vector + confidence, that's a new DSL Term in `runners/dsl/src/term.rs` + `py.rs`. I'm flagging it rather than faking it with discrete nearest-direction (which would silently drop the confidence I need for gating in (c)).

Everything else — Frame manifest, BIND, infer_label_effect, reconcile, the `(value,conf,source)` triple — is seed JSON + match-rules. No other Rust.

---

## Build order

1. Author the GameFrame seed (slots with `seeds:`/`finder:`/`conf:`) + the BIND rule. Verify on raw snake: recognise → axis holds 5 open Expectations, each writing a prior into its faculty.
2. `project_word` (resolve the impasse) → `infer_label_effect` rule → confirm `action_delta` is populated from labels on frame 1 and `navigate_alive` plans before any press.
3. `reconcile` rule + the `(value,conf,source)` triple → verify a deliberately-lying label ("Up" wired to down) self-corrects in exactly one observation, and a true label is confirmed with zero extra presses.
4. End-to-end on raw snake: measure presses-to-first-correct-move and frames-to-first-eat **with** inference vs the cold operant solve. The win condition is the operant numbers, reached faster — not a new behavior, a cheaper path to the same mastery.

Want me to start by authoring the GameFrame seed + BIND rule (step 1, no Rust needed), or pin down whether `project_word` is a wrapper or a genuine new Term first?