# PREREG — block 312000: generic decision-by-collapse (any agent forms its own conclusion)

The court's `evidence >= bar` was a comparator: the outcome was a monotone
function of the evidence and the agent brought nothing but a threshold. The
correct thing is generic and native: **any agent forms its OWN conclusion about a
matter by COLLAPSE, and acts on it.** The councillor convicting and the citizenry
reaching their own views of the accused are the *same* mechanism — each agent
collapses the same matter against its own held considerations, so they diverge.

This is the substrate's decision idiom (`af_choose_action`, `ss_choose_burn`):
`Attr(Argmax(source=candidates, value=<Term mixing the DECIDING agent's own held
params with each candidate's attrs>), key)`. NOT ShapeDecode (that is perceptual
recognition), NOT `IfThenElse` arithmetic (a comparator in a coat).

## The mechanism (`agent_judgment.json`) — two rules, zero new Rust

Seeded `Stance` candidates form a graded signed set: denounce(+2), condemn(+1),
doubt(−1), exonerate(−2). An agent that `-considers->` a `Matter{claim, weight}`
(`-about_subject->` a person) collapses:

- **`jc_conclude`** — mint `Conclusion.verdict = Attr(Argmax over Stances valued by
  `−(stance.pole − lean)²`, "label")` — the stance whose pole sits **closest** to
  the agent's assessed **lean**, where
  `lean = m.weight·a.credence + a.punitiveness − a.deference·b.standing`:
  the **evidence** (as *this* agent weighs it by its own credence), the agent's own
  **disposition** (punitiveness; negative = lenient), and **who the subject is**
  (deference to the subject's standing buys doubt). Once per (agent, matter).
- **`jc_act`** — the citizenry acts accordingly: a **condemning** conclusion
  (`verdict_pole > 0`) strips the subject's public standing by *that agent's own*
  sanction, once, when the town is armed to act. The accused's standing emerges
  from the distribution of independent private verdicts.

Per-agent divergence is structural: the value Term reads each deciding agent's OWN
attributes, so identical evidence yields different verdicts.

## Gates (pass/fail, pre-registered)

1. **G-divergent-conclusions (HEADLINE):** a disposition-spread population reaches
   **multiple different** verdicts on ONE identical matter (not unanimous) — the
   conclusion is the agent's, not the evidence's.
2. **G-evidence-is-one-input (HEADLINE):** at HIGH evidence weight, a lenient /
   deferential agent still **exonerates** while a harsh agent **condemns** the same
   matter — evidence alone is not decisive; disposition and who-the-subject-is move
   the outcome.
3. **G-subject-identity-matters:** the same agents at the same weight condemn a
   **low-standing** subject more than a **high-standing** one (the deference
   channel is real — who the accused is changes the verdict distribution).
4. **G-collapse-is-graded:** across a population the verdicts span **more than two**
   of the four poles (denounce/condemn/doubt/exonerate both extremes AND a middle
   occur) — a genuine multi-candidate collapse, not a binary sign test.
5. **G-citizenry-acts:** after `enact`, the subject's standing falls by exactly the
   sum of the *condemning* agents' sanctions; exonerating agents strip nothing; a
   second `enact` does not double-strip (the `acted` guard).
6. **G-dispositions-are-load-bearing (falsifier):** give every agent **identical**
   dispositions → the verdict becomes **unanimous** (divergence collapses),
   proving divergence comes from the agents' held params, not noise.
7. **G-no-python-decision (source audit):** `jc_conclude` / `jc_act` are the seed
   rules; the adapter only mints agents/matters/stances, wires who-considers-what,
   ticks, arms the acting phase, and reads state.

## Scope / honesty
- `lean` is a linear mix of three considerations; it is the mechanism, not a model
  of real deliberation. The point is that the decision is the **agent's own
  Argmax collapse** over a data-driven stance set, subjective by construction, and
  **generic** (the court and the townsfolk are two applications of one rule).
- The agent's held **Bond** toward the subject (a directed relational affect) is
  the natural next consideration to add to `lean` as one more addend — deferred to
  keep this rung's collapse clean.
- Isolated demonstrator (`self_load_only`); no Rust; `.so` untouched (`a8a9012c`).
