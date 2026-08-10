# Shape math — literature grounding (for the jabberwock to ground + design from)

Research spike (2026-06-27) into "SHAPE MATH" — operating ON shapes: "this is like X but with Y, or vice versa."
The creator names it the missing piece after order-N shape MATCHING. Per methodology: research → ground the agent
→ the AGENT designs (no donkey, no hand-built Python). The agent HOLDS AntiUnify (anti-unification / lgg, a Rust
Term — the COMMON template of two structures, WILDing differences) + Covers (its dual, the instance TEST). The
four clusters converge sharply.

## The gap
Shape MATCHING (built): recognise that A and B SHARE a deep shape (AntiUnify finds the common template). Shape
MATH (missing): the ALGEBRA on shapes — the DIFFERENCE between shapes, APPLYING a difference ("X but with Y"),
CONSTRUCTING base+modifier, and the inverse DECOMPOSING. Matching = recognition (a predicate); shape math =
construction (a function that EMITS new structure). Strictly more.

## Cluster 1 — proportional analogy / analogical inference ("X but with Y" = a transformation)
A:B::C:D. Two formalisations: the parallelogram/difference model (Rumelhart & Abrahamson 1973: relation = B−A,
so D = C + (B−A)) and the axiomatic analogical-proportion model (Lepage; Miclet & Prade; Prade & Richard —
reflexivity/symmetry/central-permutation; solve a:b::c:x). The arrow view (Antić; Couceiro & Lehtonen): a→b : c→x,
making the TRANSFORMATION T (b = T(a)) a FIRST-CLASS object that is re-applied: x = T(c). "X but with Y" = apply
T_Y to X (forward); DECOMPOSE = T = diff(A,B) (recover the transform from a worked pair). SME's CANDIDATE
INFERENCE / PROJECTION (Falkenhainer/Forbus/Gentner) = "X but with Y" run generatively: once base↔target align,
unmatched base structure connected to the shared system is PROJECTED onto the target, gated by SYSTEMATICITY (only
deltas bound to the shared higher-order system transfer). Sternberg's componential analysis: solving A:B::C:D
needs encode → INFER the A→B relation → map → APPLY it to C → respond; matching covers encode+map, **inference
(extract the relation as an object) + application (re-run it) are the load-bearing extras** = diff + apply.

## Cluster 2 — the TERM ALGEBRA / subsumption lattice (the formal core; the sharpest finding)
Anti-unification (Plotkin 1970; Reynolds 1970; survey Cerna & Kutsia, IJCAI 2023). The lgg of ⟨t₁,t₂⟩ is the most
specific term t with substitutions σ₁,σ₂ s.t. t·σ₁≡t₁, t·σ₂≡t₂. **The lgg is DEFINED by the witness substitutions
{σ₁,σ₂} — the DIFFERENCE is latent inside AntiUnify** (the binding WILD↦subterm), but must be EMITTED/RETAINED
(if AntiUnify returns only the template, the residue is lost; Covers returns only a BOOLEAN, not the witness).
**The subsumption LATTICE (exact framing):** terms ordered by "more general than"; **anti-unification = MEET (glb),
unification = JOIN (lub).** So **"X but with Y" = move DOWN the lattice (instantiate via SUBSTITUTE), "abstract X
out / vice versa" = move UP (anti-unify).** The THREE distinct primitives: (1) AntiUnify (HAVE — abstraction/meet);
(2) **SUBSTITUTE / instantiate (template·σ→term) — realises "X but with Y" — LIKELY MISSING** (not AntiUnify, not
Covers); (3) **MATCH-with-witness (term×template→σ) — Covers upgraded to RETURN σ — LIKELY MISSING** (have the
boolean, not the witness). CHEAPEST CORRECT MOVE: **make AntiUnify RETURN its witnesses {σ₁,σ₂}, then add ONE new
primitive SUBSTITUTE.** Then "X but with Y" = SUBSTITUTE(AntiUnify(A,X), σ_Y); the difference = the returned σ;
instance-test = Covers; everything else (decompose, blend) = composition over {AntiUnify-with-σ, SUBSTITUTE,
Covers} = moving up/down the ONE lattice. Higher-order (order-N): unrestricted HO anti-unification is hard, but
the **higher-order PATTERN fragment is unitary + linear-time** (Baumgartner, Kutsia, Levy & Villaret 2017) — keep
relations-over-relations in the pattern fragment.

## Cluster 3 — vector analogy as literal math (borrow the intuition, reject the lossiness)
king − man + woman ≈ queen (Mikolov 2013): the difference VECTOR b−a is the relation, applied to c (d ≈ c+(b−a);
3CosAdd/3CosMul, Levy & Goldberg 2014). Why it works: embeddings are linear projections of PMI (Allen &
Hospedales 2019); holds when the two pairs share co-occurrence statistics (Ethayarajh 2019). HONEST LIMITS
(Linzen 2016; Nissim 2020): much "success" is nearest-neighbour + forced question-word exclusion; an unreliable
probe. CRUCIAL CONTRAST: the vector offset is a **FLAT, first-order difference** — one translation in attribute
space; it CANNOT carry the relational graph (which roles bind to what, preserved vs altered structure, nesting) —
exactly what AntiUnify keeps. **Borrow:** difference-as-a-first-class-object, store-once-reapply (d = c ⊕ Δ).
**Do better:** make Δ a difference SHAPE — a reified rewrite between AntiUnify's residuals — applied AND CHECKED
structurally (validate by re-anti-unifying the result; the structural analogue of Ethayarajh's precondition).

## Cluster 4 — conceptual blending / the CONSTRUCTIVE dual (build, not just recognise)
Conceptual blending (Fauconnier & Turner 1998/2002): two inputs + a GENERIC space (= the agent's AntiUnify!) →
a BLEND by composition/completion/elaboration (emergent structure). Copycat (Hofstadter & Mitchell): apply a
transformation to a new base under conceptual SLIPPAGE (re-derive, don't rigidly transplant). **Amalgams
(Ontañón & Plaza 2010; Bou, Plaza & Schorlemmer 2014): the formal COMBINE op = the explicit DUAL of
anti-unification** — generalise each input only DOWN TO the meet χ = AntiUnify(a,b), then UNIFY the relaxations;
the **asymmetric amalgam (keep target, generalise source to the generic, transfer source's residual) is LITERALLY
"X but with Y".** Category theory (Goguen; Bou et al.): AntiUnify + its two Cover maps **IS the span G→I₁, G→I₂**;
the blend = the **pushout / colimit over G** (gluing along the shared generic). "AntiUnify is the meet (pull-back
side); the blend is the join (push-out side) over it." ACTIONABLE: **don't add a new matcher — INVERT the held
one.** difference = I − G (what a Cover adds over the generic); "X but with Y" = asymmetric amalgam; decompose =
factor a target back through G. One primitive — UNIFY the down-to-generic relaxations of the span AntiUnify
already computes — gives the whole constructive side.

## Convergent conclusion (for the jabberwock to design from — NOT prescribed)
Shape math = **the lattice algebra over the agent's HELD AntiUnify**: AntiUnify is the MEET (abstract UP); its
missing duals are the JOIN direction (instantiate DOWN). The agent holds AntiUnify (✓) + Covers (✓, boolean). The
likely-MISSING pieces (the agent should CHECK its held Terms — it may already hold Unify/Substitute, as it already
held AntiUnify): (1) **AntiUnify returning its WITNESS substitutions** (the difference, currently latent); (2)
**SUBSTITUTE / instantiate** (apply σ = "X but with Y" = move down the lattice); (3) **Covers-with-witness / MATCH**
(extract σ, not just the boolean); and the constructive (4) **UNIFY / amalgam** (combine over the generic = blend
= the dual of AntiUnify). The whole of "this is like X but with Y, or vice versa" then composes: lgg gives X
(common), the residual gives Y (difference), SUBSTITUTE applies a different Y (forward / construct), generalise-up
inverts (decompose), amalgam/unify builds the blend. Keep it STRUCTURAL + higher-order (pattern fragment for
tractability), gated by re-anti-unification (the structural validity check the vector version lacks).

**CONTROL/GATE for any design** (the falsifiable test, via the held primitives, donkey=0):
- "X but with Y" FORWARD: given solar-system's shape + the gravity→electrostatic difference, CONSTRUCT/derive the
  atom shape (or the proportional analogy solar:atom :: [given]:? solved correctly).
- DECOMPOSE (vice versa): factor the atom shape into solar-system-base + the difference.
- VALIDITY: a STRUCTURAL difference applies + re-anti-unifies clean; a flat/wrong difference does NOT (don't
  collapse to the lossy vector version).
- the existing matching controls still hold (solar↔atom MATCH, solar↔billiards NO).

### Key sources
Rumelhart & Abrahamson 1973; Gentner 1983 + Falkenhainer/Forbus/Gentner 1989 (SME candidate inference); Sternberg
1977 (componential); Lepage / Miclet & Prade / Prade & Richard (analogical proportions); Antić, Couceiro &
Lehtonen (arrow equations). Plotkin 1970 / Reynolds 1970 (anti-unification); Cerna & Kutsia 2023 (survey);
Baumgartner/Kutsia/Levy/Villaret 2017 (HO pattern AU, linear); subsumption lattice. Mikolov 2013; Levy & Goldberg
2014; Allen & Hospedales 2019; Ethayarajh 2019; Linzen 2016; Nissim 2020. Fauconnier & Turner 1998/2002; Hofstadter
& Mitchell (Copycat); Ontañón & Plaza 2010 / Bou, Plaza & Schorlemmer 2014 (amalgams); Goguen (blending = colimit).
