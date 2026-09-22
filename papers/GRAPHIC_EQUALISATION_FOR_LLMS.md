# Graphic Equalisation for LLMs

**Purpose:** a compact operating model of the theory for exploration, checking, and application. It is **not** the proof corpus and grants no result beyond what its linked sources establish. Use this file as the context entry point; follow a source link before asserting a formal theorem, empirical result, or domain-specific consequence.

## 1. Theory in one screen

**Base claim.** *To be is to stand in relation* ([00 — *Is*](formal/00_is.tex)). To say that anything **happens** adds a second, independent admission: transformations occur.

**Minimal running substrate.** A graph is \(G=(g,r,\Gamma)\): `g` = represented relational state; `r` = operative transformation structure; `Γ` = grammar deciding which graph-originated transformations cohere. `g` alone is sufficient for there to be structured distinction; `r` and `Γ` are the extra structure required for occurrence.

**Dynamics (the Law).**

```text
G_t ──present structure──> Poss(G_t) ──collapse/realisation──> G_(t+1)
```

`Poss(G_t)` is the set of immediate continuations expressible in the current vocabulary, meeting antecedent conditions, and admitted by `Γ`. Collapse/realisation selects one continuation; the realised successor is the next antecedent. The Law says this recurrence generates the dynamics. It does **not** identify collapse with deliberative choice.

**Determinacy.** Given a genuinely identical, causally complete antecedent, the realised successor is fixed. Apparent indeterminacy may instead record a frame that omits causally active distinctions; this is not a license to postulate hidden variables in every case.

**Residual.** A graph-originated deformation rejected by the relevant grammar is not thereby undone: it is **residual**—present but inadmissible in that frame. What a system does with residual (propagate, display, catch, cohere it to a value, terminate) is contingent handler/rule content, not substrate semantics.

**Frames.** No operational “view from nowhere” exists. Every distinction, measurement, identity judgement, admissibility judgement, and quantity is relative to a frame. Formally, a frame is the boundary relation individuating a subgraph, not the subgraph itself. Frames can model other frames, never exhaustively close their own provenance or running from within.

**Consequences to preserve while reasoning.**

- **Identity is frame-relative:** continuity of a graph and a container’s tracking of an instance are different relations; no absolute sameness is inferred from \(g,r,\Gamma\) alone.
- **Time is not a substrate coordinate:** realised changes have enabling/succession order; a frame constructs time from closure cycles it holds. There is no required global tick or universal present.
- **No implicit history:** the past affects a transition only via present graph/boundary structure that carries a causal trace.
- **Reflection is ordinary graph dynamics:** if `Γ` represents and transforms itself, that is the loop; a new external homunculus is not required.
- **Groundings are not the substrate:** a grounding fixes particular rule content, initial conditions, and a domain. Physics, minds, institutions, and software may instantiate different groundings without being reduced to one empirical model.

## 2. Economics and structure

**Write economics.** In the substrate characterisation, a destructive delta/write is the characteristic paid operation; standing structure and the boundary are free **to that frame**. Payment may be inherited by a supplying frame, so “free here” never means universally free. This is a revisable detail claim, not an unconditional law of all possible substrates.

**Well-formedness.** A graph is well-formed to the degree that it pays for nothing doing no work. Audit four costs: writes; retention; search over what is held; and silent writes to structure with no effect. An ill-formed graph still runs; it pays more. A useful compression is not “remove everything”: retained structure can reduce future writes but increases search and inert-write risk.

**Carvings are not privileged.** Boundaries/types/categories are frame-made. Under a shared binding constraint, independently developed, economical carvings may converge; convergence outside shared purpose would challenge this account. Do not convert an economical or widely shared classification into an ontological absolute.

## 3. What an LLM should do with the theory

When analysing any claim/system, write the smallest explicit ledger:

```text
Frame F: what boundary/aperture individuates the object and evidence?
State g: what distinctions/relations are presently represented?
Rules r: what can transform g?
Grammar Γ: what is admissible; which gate/rule applies?
Poss: which continuations are actually expressible and antecedent-authorised?
Realisation: what one transition/event is claimed to occur?
Residual: what was rejected, omitted, deferred, or made incoherent?
Cost: who pays which write/search/retention cost, including suppliers?
Grounding: which domain-specific laws/initial conditions have been added?
Test: what observation would distinguish this account from its alternatives?
```

Use this to **clarify**, not to force-fit. If `g`, `r`, `Γ`, the frame, or the realisation rule cannot be independently specified, say the application is underspecified. Keep these separations intact:

1. `can represent/do` (**capability**) ≠ `can reach from current position/resources` (**accessibility**).
2. `not admitted at input` (**absent to the frame**) ≠ `entered then rejected` (**residual**).
3. `deterministic given a complete antecedent` ≠ `predictable by this observer`.
4. `a grounded/domain result` ≠ `a substrate theorem`.
5. `a model’s self-description` ≠ evidence that it has closed its provenance, identity, or truth from within.

## 4. Limits, burden of proof, and falsification

This is an information-level framework, not a replacement for field theories and not a blanket proof of the groundings. Its central empirical/compositional claim is that the same arrangement recurs across independently developed domains; that can fail if the vocabulary renders adversarially unrelated domains equally well merely by being generic.

Important failure conditions include: (a) realised dynamics needing a primitive beyond \(g,r,\Gamma\); (b) two causally complete identical antecedents yielding different successors with no operative distinction; (c) persistence/sameness derivable without frame individuation; (d) residual and non-admission coming apart; (e) a frame settling its own provenance/boundary from inside without a crossing/write; (f) an irreducible non-write cost where the economics claims none; or (g) a change paid nowhere in both the acting frame and sustaining container. Some failures revise a mechanism; others bound the theory’s claimed range. Read the formal falsifiability section before treating any item as settled.

**Do not infer:** a universal physical theory, a proof of consciousness, a specific quantum interpretation, a privileged ontology, an absolute ethics, or a successful implementation from this brief. `01a`–`01i` are explicit, separately assessable groundings/programmes, not automatic consequences of the definitions.

## 5. Source map — follow links for authority

### Core formal record

- [00 — *Is*: base relational claim and removal method](formal/00_is.tex)
- [01 — *The Law of Graphic Equalisation — Theory*: definitions, arguments, propositions, and falsifiers](formal/01_law_of_graphic_equalisation_theory_referenced.tex)
- [01s — generated formal statement of 01](formal/01s_graphic_equalisation_statement.tex) · [generation specification](formal/01s.spec)
- [06 — assessment: what an account of this kind can claim/test](formal/06_assessing_an_account_of_this_kind.tex)
- [A1 — constructive implementation](formal/A1_constructive_graphic_equalisation_implementation_referenced.tex)

### Direct 01 groundings and extensions

- [01a — Physics: change, `c`, relativity, Born recovery, constants, second law](formal/01a_graphic_equalisation_physics_grounding.tex)
- [01b — Mind and self: frames, run/record, self-models, identity, death](formal/01b_graphic_equalisation_mind_and_self_grounding.tex)
- [01c — Cosmology grounding](formal/01c_graphic_equalisation_cosmology_grounding.tex)
- [01d — Born recovery](formal/01d_graphic_equalisation_born_recovery.tex)
- [01e — Communication grounding](formal/01e_graphic_equalisation_communication_grounding.tex)
- [01f — Qualia and consciousness grounding](formal/01f_graphic_equalisation_qualia_and_consciousness_grounding.tex)
- [01g — Total Perspective Vortex grounding](formal/01g_graphic_equalisation_total_perspective_vortex_grounding.tex)
- [01h — Information gravity / quantum reconciliation programme](formal/01h_graphic_equalisation_information_gravity_quantum_reconciliation.tex) · [derivation notes](derivations/01h_information_gravity_quantum_reconciliation_derivation.md) · [research notes](research/01h_information_gravity_quantum_reconciliation_notes.md)
- [01i — Passive continuation: momentum, gravity, alteration cost](formal/01i_graphic_equalisation_passive_continuation_momentum_gravity.tex) · [derivation](derivations/01i_passive_continuation_momentum_gravity_derivation.md) · [research notes](research/01i_passive_continuation_momentum_gravity_notes.md)

### Related machinery (use only when needed)

- [02 — Seldon Manifolds: represented reachable futures](formal/02_seldon_manifolds_theory_referenced.tex) · [02a psychological grounding](formal/02a_seldon_manifolds_psychological_grounding.tex) · [02b application](formal/02b_seldon_manifolds_social_and_psychological_application.tex)
- [03 — Narrative Momentum](formal/03_law_of_narrative_momentum_theory_referenced.tex)
- [04 — Narrativium](formal/04_narrativium_theory_referenced.tex)
- [05 — Frames, Relation, and the Empty Limit](formal/05_frames_relation_and_the_empty_limit.tex)
- [07 — Causal Attitude Networks](formal/07_causal_attitude_networks_on_the_substrate.tex)
- [08 — Certified Answers as an Audit](formal/08_certified_answers_as_an_audit.tex)
- [09 — Adaptability](formal/09_adaptability.tex) · [09a implementation](formal/09a_adaptability_implementation.tex)
- [10 — Applied Graphic Equalisation](formal/10_applied_graphic_equalisation.tex)

**Portable invocation:** give an LLM this file’s repository URL or local path, then state the target question and ask it to use §3’s ledger, label inference vs. source-backed claim, and open only the relevant source links when verification matters.
