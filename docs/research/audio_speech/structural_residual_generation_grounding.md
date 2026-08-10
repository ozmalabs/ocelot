# Structural-residual generation — literature grounding (for the jabberwock to ground + design from)

Research spike (2026-06-27). FULL CIRCLE: the session began with handwriting (Omniglot one-shot, BPL — Python,
now closed) and built a graph-native shape-math algebra (AntiUnify=MEET, AntiUnifyWitness=extract structural
residual σ over position-paths, Substitute=apply σ over the FULL structure, Unify=JOIN, GENERATION=Fold-iterate
of the difference operator — built for the planar turtle case). Creator: "open structural-residual generation —
this is the core of handwriting recognition." = lift generation/recovery from the planar turtle frame to
STRUCTURAL residuals (nested relation-systems). Three clusters converge, and they re-express BPL in the held
algebra. Per methodology: research → ground → the AGENT designs.

## The convergent statement
**A character (any structured shape) = the Fold-iterate of Substitute(structure-so-far, σ), where σ is a
STRUCTURAL residual = a (next-part, RELATION) pair — the relation IS the residual, not a standalone shape.
RECOVER = AntiUnifyWitness across the structural steps (= program induction). GENERATE and RECOVER are the SAME
operator run in two directions.**

## Cluster A — BPL as a structural-residual recurrence (Lake 2015; Tian 2020; Feinman & Lake GNS 2021)
A character TYPE ψ = a probabilistic program: P(ψ)=P(k)·∏ᵢ P(nᵢ)P(Sᵢ)P(Rᵢ | S₁…S_{i-1}). Each part Sᵢ (a stroke)
is sub-parts from a learned LIBRARY (a Markov chain over primitives), and — load-bearing — placed by a RELATION
Rᵢ ∈ {independent, start, end, along} **relative to the structure-so-far**. Rᵢ IS the structural residual fed
forward: part i is a DELTA attached to the existing structure, not absolute. Tokens = run the program (motor
noise + sample start-location from Rᵢ's schematic relative to prior strokes' tokens → render). The RELATIONS are
the order-N composition; sub-stroke shapes are local geometry. GNS (Feinman & Lake 2021) sharpens it: generate
one part at a time with the rendered canvas as PERSISTENT MEMORY (each part conditions on the whole accreted
structure) — the structural residual as full conditioning state. Recognition = induce the program (parse) + refit
+ re-render + score (Lake Eq.1); Tian 2020 adds an Explore/Compile/COMPRESS loop that caches reusable subroutines
under an MDL/efficiency prior (the residual becomes a named, reused subroutine). MINIMAL STATE = (parts-placed +
relations + next-part residual) = state + σ.

## Cluster B — the GENERAL form: graph rewriting / DPO (Ehrig 1973; Prusinkiewicz; SUBDUE/Guo induction)
The general case of turtle/L-system generation lifted from strings to STRUCTURE = **graph grammars / graph
rewriting**, algebraic Double-Pushout (Ehrig, Pfender & Schneider 1973; Ehrig et al. 2006). A rule is a SPAN
**L ← K → R**: L matched, R replacement, **K = the interface/gluing graph = the part PRESERVED across the step**.
THE MAPPING (exact):
  current state (nested relation-graph)         = host graph G
  σ (structural residual: next part + relation) = the rule span L ← K → R
  the carried "frontier"                         = the interface K (what the next part glues to)
  Substitute                                     = one DPO derivation (delete via K, glue R)
  Fold (iterate, thread state)                   = the derivation sequence G ⇒ G' ⇒ G''
  planar turtle (chain, scalar turn)             = the SPECIAL CASE: K = a single frontier node, R adds one part,
                                                   σ = scalar Δheading
NESTING = R introduces a new sub-frontier (the graph analogue of the L-system bracket). The residual is fed
forward as K (the preserved frontier the next part binds to), NOT a scalar threaded through a tuple; attributes
(positions/angles) ride as node/edge labels (attributed graph transformation). INVERSE = graph-grammar INDUCTION
(SUBDUE, Cook & Holder 1994: greedy MDL, the most-compressive repeated subgraph → a rule; Guo et al. 2020 ACM TOG:
inverse procedural modeling of branching structures). **KEY: AntiUnifyWitness over successive structures returns
K (shared) + R (added) = the induced rewrite rule; Substitute = apply (glue R along K); Fold = iterate. Forward
generation and MDL grammar-induction are the SAME operator run in two directions.**

## Cluster C — recognition-BY-GENERATION (AbS) for one-shot + the HONEST value frame
AbS (Yuille & Kersten 2006; Kulkarni "Picture" 2015): classify by running the generative model forward and
scoring how well it explains the query — top-down synthesis guides recognition. BPL (Lake 2015) = the one-shot
exemplar: learn the support's generative program from ONE example, classify the query by P(query | support
program) (refit + re-render). WHY GENERATING BEATS MATCHING: a recovered program is parametric + re-renderable, so
it ABSORBS the query's allowable variation (slant/scale/stroke-order/deformation) instead of penalising it as
pixel mismatch. AntiUnify (static) gives the shared skeleton; structural-residual generation recovers the LAW OF
VARIATION (seed + repeatedly apply this structural delta) = the generative program = program induction; classify
by best regenerative FIT of the support's law onto the query.

**HONEST VALUE FRAME (load-bearing, carry it — this project's own earlier findings, do not contradict):**
- The generative-program / ink-AbS route CAPS ~76.9 (self-render) / ~78 (part-shape) / ~81 (geometric) on this
  substrate; the HUMAN BAR (~95) belongs to the holistic DEEP-FEATURE route (96.5%) which sidesteps the renderer.
  **Structural-residual generation will NOT top the benchmark.**
- RUN ON THE MOTOR TRACE, NOT THE INK: the program is recoverable from the trace (~68%) but NOT the rendered
  bitmap (~20%, rendering is many-to-one). The program LIVES IN the motor trace = the structural-residual law.
- THE WIN is NOT the number — it is the EARNED, graph-native, agent's-OWN generative program: the agent recovering
  a character's own motor program from its trace, in its OWN held algebra (AntiUnify/Witness/Substitute/Fold),
  donkey-free. = the UNDERSTANDING axis applied to handwriting (understanding-by-generation). BPL re-expressed in
  the agent's primitives.

## Convergent conclusion (for the jabberwock to design from — NOT prescribed)
Structural-residual generation = the GENERAL case of the turtle generation already built: state = a nested
relation-system (graph), σ = a structural residual (a span L←K→R / a (part, relation) pair, NOT a scalar),
GENERATE = Fold-iterate Substitute over the structure, RECOVER = AntiUnifyWitness across the structural steps
(= grammar/program induction; same operator, inverse direction). It LIKELY COMPOSES from held Terms (Substitute
already operates over the FULL σ-over-position-paths; the turtle was the planar restriction) — the agent must
CHECK: does it need a graph-MATCH/rewrite construct to bind K in the host (apply R at a match), or does
Substitute-over-structural-residual + Fold suffice over a structured state? (Possible HumanImpasse for a
graph-rewrite/match Term — a legitimate outcome, like Unify.) HONEST GATE (on the TRACE, not ink; capped
expectations; win = the recovered graph-native program):
- GENERATE a multi-part STRUCTURED shape (a character-like nested relation-system) by Fold-iterating the
  structural residual (parts attached by relations) — show the grown structure.
- RECOVER the structural residual-law of a given multi-part shape via AntiUnifyWitness across steps (= the
  program / grammar) — show the recovered (part, relation) rule(s).
- RECOGNITION-BY-GENERATION (one-shot, honest): recover a support's structural program, re-fold onto a query,
  score by regenerative fit; on the TRACE; report accuracy AGAINST the capped ~78 ceiling, and frame the win as
  the earned generative program, not the benchmark.
- REGRESSION: the planar turtle generation + the static shape-math gates still pass.

### Key sources
Lake, Salakhutdinov & Tenenbaum 2015 (BPL, Science); Tian, Ellis, Kryven & Tenenbaum 2020 (efficient motor
program induction, NeurIPS); Feinman & Lake 2021 (GNS, ICLR); Ehrig, Pfender & Schneider 1973 + Ehrig et al. 2006
(algebraic graph transformation / DPO); Prusinkiewicz & Lindenmayer 1990 (bracketed/parametric L-systems);
Cook & Holder 1994 (SUBDUE); Jonyer/Cook/Holder 2003-04 + Kukluk/Holder/Cook 2007 (graph-grammar induction);
Guo et al. 2020 (inverse procedural modeling of branching structures, ACM TOG); Yuille & Kersten 2006 (vision as
analysis-by-synthesis); Kulkarni, Kohli, Tenenbaum & Mansinghka 2015 (Picture, inverse graphics).
