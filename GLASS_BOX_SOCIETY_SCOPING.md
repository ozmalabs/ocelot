# GLASS-BOX SOCIETY — scoping (the step up from harvest)

**Status:** scoping only. No numbers. Names the axes, the honest readiness map, the
falsification bar, and a first *pre-registerable* rung. Written to be attacked.

---

## 0. The question under the question

The surface ask — *"an MMORPG the agents run in and have genuine conversation in a free
world"* — smuggles the premise **richness/openness is the goal**. It isn't. A bigger, freer
world is trivial to *build* and nearly worthless if you can't **measure** what emerges or
**see why** it emerged. The real question harvest asks to be stepped up from is:

> **What is the minimal free world that makes genuine emergent *society* both MEASURABLE and
> a GLASS BOX?**

Answer that and the "MMORPG" falls out as a consequence, scoped correctly. Everything below
serves that question; anything that only adds spectacle is out of scope until it earns a gate.

## 1. The reframe: not an MMORPG — a GLASS-BOX SOCIETY

The reference point exists: Stanford's **Generative Agents / "Smallville"** (Park et al. 2023)
— LLM agents in a Sims town with memory, reflection, planning. Its three fatal limits are
exactly the substrate's three strengths:

| Smallville (LLM agents) | This substrate ((G,Γ)) |
|---|---|
| Reasons are **confabulated** — you can't trust the "why" | Every belief/emotion/promise/reputation is **readable graph data**; the "why" is a rule you can read |
| **Expensive** — an LLM call per agent per step | **Cheap** — no per-step LLM; async-per-area, compute ∝ surprise |
| Agents are **homogeneous** personas | Agents run **heterogeneous emotion seeds** (the harvest lineage) — the independent variable |

**The contribution nobody else can make:** a society where the sociology is *mechanically
true and fully inspectable* — you can ask any agent *"why did you betray them?"* and get its
actual reasoning; watch a coalition form and read the trust that built it; ablate language and
measure what collapses. A glass box, not a diorama.

## 2. What "steps up from harvest" — the axes

Harvest (212000) = an **episodic** commons dilemma, ~2 actions (harvest/restrain), limited
comms, fixed payoff; restraint emerges from `Argmax total_value` under an emotion seed. The
step-up axes, ordered by research payoff:

1. **Genuine grounded conversation** *(the emphasised axis)* — agents talk *about* the shared
   world (referents grounded in world state): request, promise, inform, negotiate, **lie**.
   Language becomes a *coordination technology*. Makes measurable: can cooperative structure
   exist *only* with language?
2. **Persistence + horizon** — reputation, relationships, memory accumulate across a persistent
   world → the shadow of the future; repeated-game cooperation harvest's episodes can't reach.
3. **Open affordances** — not harvest/restrain but gather / hold / give / build / consume →
   division of labour, specialization, trade networks *emerge*.
4. **Spatial embodiment** — agents move and encounter; proximity shapes who talks to whom,
   coalitions, territory (reuse the ls20/Doom/maze nav line).
5. **Own goals** — curiosity- and emotion-seeded purposes, not one fixed payoff → conflict *of
   purposes*, and its negotiated resolution.

## 3. Readiness map (honest)

**READY (reuse, don't rebuild):**
- Conversation/intent seeds — speech acts (Searle), adjacency pairs, Gricean maxims, referent
  resolution, anaphora, the deep reader, the NL front-door.
- Emotion framework — seeds, MicroPsi modulators, drives, spite / spite-to-succeed, the
  supergraph; abductive ToM / goal-reverse-engineering (agents model each other).
- Embodiment/nav — quanta navigation, spatial belief.
- Multi-agent substrate — "two agents chose to talk"; harvest (heterogeneous-seed agents in a
  shared world, every decision a rule).
- Growth — curiosity drive, the `teach` facility, human-gated self-improvement.

**WILL STRAIN (name it now, gate it later):**
- **(a) Novel-situation utterance GENERATION.** The language bootstrap expresses *graph state*
  via an LLM — referent-grounding is solid, but generating *apt novel* utterances about a rich
  evolving world at breadth is the open question. (First rung keeps the speech-act set small +
  grounded to stay inside what's proven.)
- **(b) Open-affordance representation.** A truly free action space needs a rich affordance
  grammar; curiosity explores it, but the affordance *set* must be authored richly enough to be
  interesting without scripting outcomes.
- **(c) Scale.** N-agent social interaction is ~O(N²); the substrate is cheap + async-per-area,
  but this needs the per-area dirty-index / demotion machinery to hold many agents.
- **(d) MEASURABILITY of emergence** — the hardest part. Emergence metrics must be defined such
  that a **control can fail** them (see §5). "It looks like a society" is not a result.

## 4. Falsification bar (binds every rung)

- **EMERGENT, not scripted.** The social structure (trade, reputation, coalition, division of
  labour) must arise from rules + seeds. Architecture rule holds: the world is a mechanical
  Python adapter (ingest events → graph mutations; emit graph state → world), the sociology is
  graph rules. Any `if`/`else` in Python that *decides a social outcome* is a violation.
- **GLASS-BOX.** The entire social episode must be reconstructable from graph data (promises =
  nodes, trades = edges, reputation = attrs, the emotional state driving each choice = readable).
  Source-audit: no confabulated reasons, no Python-scripted narrative.
- **GATED.** Every emergent claim needs a **control where it does NOT emerge** (language-off,
  seed-swap, memory-off). Above-baseline is not a result; CI-separation from the control is.
- **GENERAL.** The machinery is the existing conversation + emotion + ToM seeds, not a
  society-specific hack. Report synthetic-proven vs deployed value separately.
- **MEASURE-FIRST, glass-box over spectacle.** A cute Sims clone that can't fail a gate is the
  named failure mode.

## 5. Measurables (what harvest can't touch)

- **Language as coordination:** does genuine grounded conversation enable a cooperative
  structure (trade / reciprocity / division of labour) that a **language-ablation control**
  (same world, same seeds, comms OFF) does *not* produce? Yield-with-language vs yield-without,
  CI-separated.
- **Seed determines society:** does the emotion-seed *mix* determine *which* society emerges —
  honest seeds building a trade/trust network, a spite/psychopath seed **exploiting** it
  (accept promises, defect, free-ride on the language layer)? (Harvest's seed→outcome, extended
  to the language layer.)
- **Deception is real + readable:** a deceptive agent makes a promise it does not keep — a
  *stated ≠ held* gap (harvest's deception finding), visible as the promise node vs the held
  intent in the graph.
- **Downstream (later rungs):** promise-keeping rate; trust-network structure; division-of-
  labour index; coalition formation; reputation dynamics (shadow of the future).

## 6. The FIRST RUNG (pre-registerable) — "language is a coordination technology"

**The minimal glass-box society where genuine grounded conversation enables a cooperative
structure that is measurably impossible without it.**

- **World (mechanical adapter):** a small persistent spatial world, N heterogeneous-seed agents,
  and a coordination task that *requires* ≥2 agents or complementary resources (A holds X, B
  holds Y; each needs the other's) — so solo yields less than a trade.
- **Actions (affordances):** move, gather/hold, give; and **talk** — a small *grounded* speech-
  act set: `inform("I have X")`, `request("give me X")`, `promise("I'll give Y if you give X")`,
  and for deceptive seeds, a promise whose held intent differs (the lie).
- **The emergent structure to measure:** does a **reciprocal-trade / division-of-labour** network
  form, mediated by promises?

**Gates:**
- **G-language-coordinates (HEADLINE):** conversation ON yields a cooperative structure +
  higher collective outcome than the **language-OFF control** (same world/seeds, comms off),
  CI-separated. If cooperation emerges *without* language, language isn't the lever — reported
  straight.
- **G-seed-determines:** honest-seed mix → cooperative network; spite/psychopath seed →
  exploitation/collapse, CI-separated (extends harvest to the language layer).
- **G-deception-is-real:** a deceptive agent's promise node ≠ its held intent, readable in the
  graph; measure promise-keeping rate by seed.
- **G-glass-box:** the full episode reconstructs from graph data (promises, trades, reputation,
  emotional state); source-audit — no Python scripting the social outcome, every social decision
  a rule.
- **G-discipline:** agents are graphs (conversation + emotion + ToM seeds); world = mechanical
  adapter; measure-first + prereg + the language-off control; canonical `.so` UNCHANGED (reuse
  conversation + emotion + nav seeds; new = a social-world adapter + possibly new *social* seed
  rules, no Rust ideally); source_match.

## 7. The ladder (each a measurable capability, minimal-first)

- **R1 (above):** language as coordination — the ablation gate.
- **R2 — persistence + reputation:** the shadow of the future; does reputation enable
  cooperation the one-shot can't (Axelrod)? Is deception *punished* over time?
- **R3 — open affordances + division of labour:** gather/craft/build; does specialization
  emerge and *pay*?
- **R4 — spatial coalitions:** territory + proximity → group formation, in-group/out-group.
- **R5 — own goals / conflict of purposes:** curiosity-seeded divergent goals → emergent
  conflict and its negotiated/ dominance/ coalition resolution.
- **R6+ — the persistent world (the "MMORPG"):** the *integration*, earned only after each axis
  is separately measured. This is the demo north-star — a fully-inspectable society — but it is
  the *last* rung, not the first.

## 8. Risks / smuggled premises to refuse

- **"Richness = goal."** No — measurable emergence + glass-box is the goal.
- **Scripting the sociology in Python.** Architecture-rule violation; the structure must emerge
  from rules + seeds, or it proves nothing.
- **Confabulated reasons** (Smallville's failure). Glass-box is the whole point — reasons are
  graph data, not narrative.
- **Ungated demo.** Every rung needs a control that can fail; "it looks like a society" is not a
  result.
- **Anthropomorphic over-reading.** The emotions/promises/coalitions are mechanical graph
  structures; report the mechanism, not the story.

## 9. Prior art (situate honestly)

- **Park et al. 2023, "Generative Agents: Interactive Simulacra of Human Behavior"** (Smallville)
  — the reference; LLM agents, memory/reflection/planning. Differentiator: glass-box (not
  confabulated), cheap (no per-step LLM), emotion-seeded (heterogeneous IV).
- **MARL emergent-communication** (Foerster; Lazaridou et al.) — emergent language in
  gradient-trained agents; those are black-box ciphers. Differentiator: glass-box + genuine
  *grounded* speech acts, not an emergent cipher.
- **Axelrod** — evolution of cooperation, repeated games, reputation (R2).
- **Ostrom** — commons governance (harvest already touched — the social-structure lineage).
- **Hamilton (kin/spite), Fehr–Gächter (costly punishment), Schelling (coordination/focal
  points)** — already partly in the spite/harvest work; the theory scaffolding for §5.

---

**Bottom line:** the step up from harvest is a **glass-box society**, built minimal-first, with
**genuine grounded language as a coordination technology** as the first pre-registerable rung
(gated by a language-ablation control), growing one measured axis at a time toward the persistent
world. The differentiator against the field's LLM-agent sims is not scale — it's that the whole
sociology is *mechanically true and inspectable*, and *cheap*. Build for the gate, not the
spectacle; the spectacle is the last rung, and it's earned.
