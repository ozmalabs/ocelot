# 01i — Passive continuation, momentum, and gravity: strict derivation ledger

**Stage:** 2 derivation artifact; standalone and non-paper.
**Status:** a strict negative-and-constructive record. It derives the strongest continuation result licensed by 01, 01a, 01g, 01h, 03, and the Stage-1 research ledger. It does **not** derive physical momentum, four-momentum transport, a metric, a connection, a geodesic equation, proper acceleration, stress--energy sourcing, the equivalence principle, Newtonian gravity, or general relativity. It tests whether those targets could be two readings of one implemented passive-continuation law. It does **not** identify momentum and gravity as the same force.

## 1. Purpose, result, and source boundary

### 1.1 Result in one paragraph

The corpus supplies a frame-indexed cost form: present, operative, history-bearing structure can be reused by an admissible continuation without **additional alteration cost in a declared alteration class**, whereas a continuation that materially alters or replaces that structure incurs the class's alteration increment. This is the strongest internal passive-continuation result. It means neither that nothing happens, nor that no elapsed time is inferred, nor that total activity/cost in a containing frame is zero. In a mechanical grounding, an extra map can identify a change of physical momentum with impulse; in a gravitational grounding, further maps could make physical load source a geometry that selects free paths. Neither map is supplied by the corpus. Thus the maximal physical claim is a conditional theorem candidate: a single concrete dynamics *may* have a flat, momentum-preserving free-transport regime and a load-shaped, geodesic-or-alternative free-propagation regime. Until its state, symmetry, source, geometry, clock, coupling, and observable maps are built and tested, that is a recovery target, not a derived reconciliation.

### 1.2 Sources used and their limited roles

| Source | Used here for | Not used here to establish |
|---|---|---|
| `papers/formal/01_law_of_graphic_equalisation_theory_referenced.tex` (01) | Frame-indexed distinction, graph/admissibility vocabulary, realization, and economics of preserve versus altering write. | A physical state space, global time, energy, force, or spacetime geometry. |
| `papers/formal/03_law_of_narrative_momentum_theory_referenced.tex` (03) | Operative carried history, free continuation, primary cost form, directional special case, and limited mechanical impulse grounding. | SI momentum for Narrative, conservation of a nonmechanical quantity, or a gravitational source. |
| `papers/formal/01a_graphic_equalisation_physics_grounding.tex` (01a) | The change-budget comparison between motion and change-load, explicitly at shape level. | Exact Lorentz transformation/factor, metric, proper-time law, field equation, or equivalence-principle derivation. |
| `papers/formal/01g_graphic_equalisation_total_perspective_vortex_grounding.tex` (01g) | Declared comparison class, support, units/ordinal cost, and mediated cross-frame bridge discipline. | A privileged global frame, directly shared perspective, or physical observable. |
| `papers/formal/01h_graphic_equalisation_information_gravity_quantum_reconciliation.tex` (01h) | The no-source/no-clock results and requirements for source, geometry, observables, clock, universality, and empirical recovery. | Closure of any required physical bridge. |
| `papers/research/01i_passive_continuation_momentum_gravity_notes.md` (Stage 1) | Source-backed Newtonian/GR targets, strict non-equivalences, recovery contract, experimental constraints, and falsifiers. | The project-specific bridge from alteration/history/load to those targets. |

External equations below are recovery targets drawn through the Stage-1 ledger, which gives direct source links and scopes. They are not re-proved as consequences of this project corpus.

### 1.3 Claim classes

- **Definition:** typed notation or a declared class needed to avoid equivocation.
- **Internal proposition:** follows from the stated corpus vocabulary, but is not a theorem of physics.
- **Conditional proposition/theorem candidate:** follows only if all stated additional physical premises hold.
- **Bridge obligation:** an equation, algorithm, action, or operational procedure absent from the corpus.
- **Breakpoint/no-go constraint:** a type, conservation, locality, observability, or limit obstruction to a stronger claim.
- **Falsifier:** an outcome that rejects a proposed bridge or realization, not the mere question of whether a bridge might exist.

No word such as *derive*, *recover*, or *reconcile* crosses these claim classes.

## 2. Declared alteration class and passive continuation

### 2.1 The frame-indexed continuation situation

Let a frame-indexed continuation situation be

\[
\boxed{
\mathfrak C_t^W=(W,G_t,\Gamma_t,\mathcal P_t,S_t,\mathcal A,\kappa,\mathcal R_t,\mathcal O_t)
}
\]

where:

- \(W\) is the individuating/mediating frame;
- \(G_t=(g_t,r_t,\Gamma_t)\) is the present graph and its admissibility grammar;
- \(\mathcal P_t:=\operatorname{Poss}(G_t)\) is the family of admissible continuations;
- \(S_t\) is the presently represented, causally operative, history-bearing structure, when the Narrative dimension exists in \(W\); it is not the whole past, and it is not automatically a physical state variable;
- \(\mathcal A\) is a **declared alteration class**;
- \(\kappa\) is the class's declared cost domain, either an ordered set \((K_{\mathcal A},\preceq)\) or an additive ordered monoid \((K_{\mathcal A},+,0,\preceq)\) when addition is justified;
- \(\mathcal R_t\) is the available support/resource configuration relevant to the comparison; and
- \(\mathcal O_t\) is the record/readout relation held in \(W\).

A declared alteration class is the tuple

\[
\boxed{
\mathcal A=(W,\operatorname{supp},\sim_{\mathcal A},\kappa,\mathcal R,\mathcal U,\mathcal M)
}
\]

with (i) the frame and support on which the comparison is made, (ii) an equivalence/reuse criterion \(\sim_{\mathcal A}\) for the relevant carried structure, (iii) the cost domain \(\kappa\), (iv) resources/support \(\mathcal R\), (v) a declared unit or ordinal convention \(\mathcal U\), and (vi) an observation/measurement protocol \(\mathcal M\). If any of these is unavailable, the corresponding class cost is **undefined**, not silently zero. This imports 01g's comparison discipline and prevents a frame-relative cost from masquerading as a universal scalar.

### 2.2 Definition: alteration and reuse

For \(a\in\mathcal P_t\), let \(S_{t+1}^{(a)}\) denote the successor's relevant representation of the carried structure, when it exists.

- \(a\) **reuses** \(S_t\) in \(\mathcal A\), written \(a\in\operatorname{Reuse}_{\mathcal A}(S_t)\), iff the class's declared criterion judges \(S_{t+1}^{(a)}\sim_{\mathcal A}S_t\).
- \(a\) **alters** \(S_t\) in \(\mathcal A\), written \(a\in\operatorname{Alt}_{\mathcal A}(S_t)\), iff its successor materially changes, replaces, bypasses, or renders irrelevant the class-relevant support of \(S_t\), according to \(\mathcal A\)'s criterion.

This definition is intentionally not a physical force, work, impulse, energy, action, mass, entropy, or stress tensor. It says what one class is counting; a physical identification requires a later typed map.

### 2.3 Definition: additional alteration cost and passive continuation

Where the cost domain is additive, define the class-relative cost form

\[
C_{\mathcal A}(a\mid S_t)=C_{0,\mathcal A}(a)+\Delta C_{\mathrm{alt},\mathcal A}(S_t,a),
\]

with

\[
\boxed{
\Delta C_{\mathrm{alt},\mathcal A}(S_t,a)=0
\quad\text{if }a\in\operatorname{Reuse}_{\mathcal A}(S_t),
}
\]

and \(\Delta C_{\mathrm{alt},\mathcal A}(S_t,a)\succ0\) for a declared material alteration where the class supplies a positive increment. If the class is only ordinal, replace equality/addition by the strictly weaker statement: reuse is not ranked as requiring an extra alteration relative to the declared baseline, while alteration is ranked above it when the class supports that comparison.

> **Passive continuation (PC).** A continuation is passive *within \(\mathcal A\)* iff it is admissible and has zero **additional alteration cost in \(\mathcal A\)** for reusing the presently operative carried structure. PC is not a claim of zero total cost, zero total activity, zero interaction at every grain, zero environmental support, or zero elapsed/inferred time.

The explicit subscript is essential. A body may be passive in the mechanical-direction class while an enclosing physical system expends energy to maintain an apparatus, or a higher frame registers a transition, or a different class prices the same event. No cross-class addition or equality is licensed without a specified translation map.

### 2.4 Three prohibited conflations

| Incorrect inference | Why it fails | What PC actually says |
|---|---|---|
| \(\Delta C_{\mathrm{alt},\mathcal A}=0\Rightarrow\) no total activity | 01 distinguishes preservation from a destructive/replacing write; 03 makes the price class-specific; 01g makes support and payer part of the comparison. | No additional alteration of the declared carried structure is charged in this class. |
| \(\Delta C_{\mathrm{alt},\mathcal A}=0\Rightarrow\Delta t=0\) | 01 has no global tick, while 01a treats time/clock reading as frame-inferred and physical clock recovery as additional work. | A continuation relation is identified without making a substrate-time or proper-time claim. |
| \(\Delta C_{\mathrm{alt},\mathcal A}=0\Rightarrow\) no force, energy, or exchange in physics | A class cost has no physical units or conservation law until a map supplies them. In particular, an external interaction can exchange subsystem momentum while total momentum is conserved. | Only a structural no-additional-alteration statement has been made. |

## 3. Strongest internal result: carried history persists only as present structure

### 3.1 Proposition P1: present-support sufficiency

**Proposition P1 (no remote history term).** Under 03's historical-sufficiency principle, a past event can affect a later continuation only through consequences represented in the current graph/boundary/support structure available in the relevant frame. Therefore an operative carried history \(S_t\) is present structure, not an unrepresented past event acting at a distance.

**Derivation.** 03 defines Narrative, when present, as realised-history structure represented and causally operative now. Its historical-sufficiency proposition limits causal relevance to what survives in present graph or boundary structure. 01's frame discipline prevents supplementing this with a frame-free historical remainder. Hence any purported influence of a non-surviving, nonrepresented past event is outside the corpus relation. ∎

**Limit.** P1 does not establish that one fixed state representation is sufficient for all questions or all containing frames. A containing frame can carry additional operative relations. Nor does P1 make \(S_t\) a mechanical state vector, phase-space point, or four-momentum.

### 3.2 Proposition P2: passive reuse theorem

**Proposition P2 (class-relative passive continuation).** Let \(\mathfrak C_t^W\) be defined, let \(a\in\mathcal P_t\), and let \(a\in\operatorname{Reuse}_{\mathcal A}(S_t)\). Then the additional alteration cost of \(a\) in the declared class is zero:

\[
\Delta C_{\mathrm{alt},\mathcal A}(S_t,a)=0.
\]

If the class has only ordinal cost, the valid conclusion is the corresponding no-extra-alteration ranking, not an additive numerical equation.

**Proof.** The antecedent says the successor reuses \(S_t\) according to the declared class criterion. Definition PC sets the alteration increment for such reuse to the class zero element (or its ordinal analogue). Therefore the conclusion follows by definition. ∎

**What is substantive.** The result is not a physical conservation law. Its corpus content comes from the disciplined choice to keep admissibility, carried structure, and alteration cost separate: \(\Gamma_t\) determines whether \(a\) is available; \(S_t\) conditions whether changing it requires an extra alteration; neither role licenses the other.

### 3.3 Corollary P2.1: persistence is not propulsion

If a continuation reuses \(S_t\), P2 permits calling the successor a *passive continuation* in \(\mathcal A\). It does not introduce a push, tendency, force, or agent that produces the successor. The persistence is what unchanged instantiated support looks like under the next realized continuation. This is the strongest internal sense in which the corpus supports “carried history/momentum-like persistence.”

### 3.4 Corollary P2.2: directional persistence is conditional

If and only if the frame additionally supplies a directional representation and a grounding map makes \(S_t\)'s reuse project to directional reachable geometry, then P2 has a directional reading: continuations aligned with the carried structure need no extra alteration in that class. This is 03's directional special case.

No vector, speed, mass, momentum component, temporal derivative, or four-vector follows from P2 alone. A frame may lack the required direction; two frames may give different directional readings; and neither fact changes the class-relative reuse relation.

### 3.5 Breakpoint B1: no physical inertia from P2

P2 does not prove Newton's first law. It lacks a physical configuration space, time parameter, mass, momentum map, equations of motion, isolation criterion, and translation symmetry. It is compatible with many dynamics, including dissipative or explicitly history-dependent dynamics that do not conserve physical momentum. “Persistence costs no additional alteration” is therefore structurally adjacent to inertial transport, not a derivation of it.

## 4. The local/in-frame limitation and its exact scope

### 4.1 History-bearing attribution, not present-state identity

Define a typed history-bearing attribution record for frame \(W\) over an interval
\([t_0,t]\):

\[
\mathcal H^W_{[t_0,t]}=
\left\langle (\mathcal O_s,S_s,\mathcal R_s)_{t_0\leq s\leq t},\ I^W,\ \Lambda^W\right\rangle .
\]

Here \(\mathcal O_s\) records the declared observations, \(S_s\) the retained
operative structure, and \(\mathcal R_s\) the declared support relations.
\(I^W\) is an explicit inference map and \(\Lambda^W\) declares the record’s
grain, losses, uncertainty, and comparison domain. The sequence may be
compressed, but the compression must declare what attribution-relevant changes
and supports it preserves. This is neither the entire past nor a frame-free
observer.

**Proposition P3 (history-required attribution, not identity).** A present
in-frame passive-continuation reading cannot, from the corpus alone, uniquely
attribute its physical realization to momentum transport or load-shaped gravity.
Such attribution requires \(\mathcal H^W_{[t_0,t]}\) and its declared inference
map \(I^W\). History is necessary but not sufficient: the map must also connect
the record to typed physical observables, source/support models, and stated
comparison conditions.

**Derivation.** 01 makes distinctions frame-indexed; 03 supplies operative but
not physically typed carried history; 01g requires a mediating frame, evidence,
translation, loss/grain conditions, and use condition for cross-frame bridges;
and 01h denies that the corpus has physical observables, source, geometry, or
clock maps. A present relation can therefore classify reuse in an alteration
class, but contains neither a momentum map nor a source/geometry map by which
one physical factor is assigned. A history record supplies the retained changes,
supports, and comparisons needed to test a proposed assignment; without its
inference map, it is still only a record. Therefore neither a bare snapshot nor
history without a typed inference map uniquely attributes the present
continuation. ∎

This is the strict usable sense of “momentum and gravity are inseparable in
frame without inference.” It is an **attribution limitation**, not a statement
that momentum and gravity are identical, are the same force, or are
experimentally indistinguishable in every regime.

### 4.2 Recovery target: local and extended GR observables

The Stage-1 source ledger records the relevant established target distinction:

\[
a^a:=u^b\nabla_bu^a.
\]

For an ideal freely falling GR test body,

\[
\boxed{a^a=0}\tag{GR proper-acceleration target}
\]

whereas a supported body has nonzero proper acceleration because of
nongravitational support. A declared local accelerometer can therefore
operationally distinguish free from supported motion in its domain. It does not,
by itself, attribute a present passive continuation to momentum transport versus
load-shaped gravity: that attribution must use the history-bearing record and
inference map of P3. A sufficiently small local nongravitational experiment
cannot distinguish a homogeneous gravitational field from a uniformly
accelerating frame under the local equivalence-principle conditions. But
extended tidal data target

\[
\boxed{\frac{D^2\xi^a}{D\tau^2}=-R^a{}_{bcd}u^b\xi^c u^d}\tag{GR tidal target}
\]

and can distinguish curvature effects from flat uniformly accelerated coordinates when their domains/measurements are defined.

These equations are **recovery targets**, not facts derived from P1--P3. They demonstrate why the proposed in-frame limitation must remain local and operational. It cannot erase proper acceleration, tidal/curvature observables, source modeling, cross-frame comparisons, or boundary conditions.

## 5. Exact missing maps: from passive continuation to physical targets

A candidate may not fill these slots by metaphor. Every map must state domain, codomain, units, transformation behavior, approximation/control domain, and operational readout.

| Physical target | Existing corpus item | Exact required map or calculation | Current result |
|---|---|---|---|
| Physical state and phase space | \(G_t,S_t,\mathcal P_t\) | \(X:\mathfrak C\to(\mathcal X,\Omega)\) or named state/observable algebra, with composition and physical equivalence. | **Absent.** A graph/history relation is not a phase-space point. |
| Newtonian momentum | Directional reading of 03's Narrative | \(P_{\rm N}:\mathcal X\to\mathbb R^3\), with units \([P]=\mathrm{kg\,m\,s^{-1}}\), operational momentum measurement, and a free equation. | **Absent.** 03's \(\mathbf p=\phi_W(\Narr)\hat{\mathbf d}\) is a frame-scaled structural representation, not this map. |
| Relativistic four-momentum | Carried structure/cost | \(P_4:\mathcal X\to T^*M\), \(x\mapsto p_a\), with mass shell, coordinate/Lorentz transformation law, transport, and energy--momentum composition/exchange. | **Absent.** No manifold, tangent/cotangent bundle, or physical time exists in the corpus. |
| Flat free transport | PC/P2 | An action or dynamics with translations and free solutions that prove \(d\mathbf p/dt=0\), or relativistically \(Dp^a/d\tau=0\), under declared isolation conditions. | **Recovery target only.** |
| Metric and connection | Relational graph, cross-frame bridge, 01a budget image | \(\Phi_\epsilon:\mathfrak C\to(M,g_{ab},\nabla,\mathcal O_{\rm phys})\), with signature, causal structure, gauge/diffeomorphism behavior, and controlled error. | **Absent.** A relation/graph is not a Lorentzian metric or affine connection. |
| Geodesic/free-path equation | “Load-shaped continuation condition” | Particle/matter action or equation whose variation yields \(u^b\nabla_bu^a=0\) (or a named testable alternative). | **Recovery target only.** |
| Proper time and acceleration | Closure/order/cycle language | \(\Theta:\mathfrak C\to\tau\) tied to a physical clock, then \(u^a=dx^a/d\tau\) and \(a^a=u^b\nabla_bu^a\); specify accelerometer observable. | **Absent.** Cycle order is not proper time. |
| Load/source | \(C_{\mathrm{alt},\mathcal A}\), 01a change-load | \(L:\mathfrak C\to T^{\rm eff}_{ab}\) or named replacement source, with dimensions, operational measurement, locality/nonlocality, coupling, and exchange law. | **Absent.** Alteration cost has no fixed physical currency. |
| Geometry dynamics | Budget/change-load shape | \(\mathcal D\) giving a field equation/action, e.g. a controlled route to \(G_{ab}+\Lambda g_{ab}=8\pi G T_{ab}/c^4\), or an explicit alternative. | **Absent.** A metric/geodesic map would still not supply a source equation. |
| Equivalence principle | 01a's seam image and local-frame language | Universal matter-coupling map plus calculation of UFF, local Lorentz/position behavior, composite/binding-energy effects, clock effects, and quantitative bounds. | **Absent.** No equality or identity of inertial and gravitational mass is derived. |
| History-bearing attribution | Frame/cross-frame rules and operative history | \(I:(\mathcal H^W_{[t_0,t]},\mathcal O_{\rm local},\mathcal O_{\rm extended},\mathcal O_{\rm source})\to\) stated momentum/load, curvature, or source attributions, with declared retained history, uncertainty, and gauge-invariant observables. | **Absent.** P3 requires both this record and inference map; neither is supplied. |

### 5.1 Flat recovery targets, not derived facts

A concrete realization seeking a flat physical reading must recover, in its stated Newtonian or special-relativistic domain,

\[
\boxed{\mathbf p=m\mathbf v,\qquad \mathbf F_{\rm net}=\frac{d\mathbf p}{dt}}\tag{F1}
\]

and, for free/isolated transport,

\[
\boxed{\mathbf F_{\rm net}=0\Rightarrow\frac{d\mathbf p}{dt}=0}\tag{F2}
\]

or a declared empirically equivalent formulation. For a relativistic massive test body in flat geometry, a suitable target is

\[
\boxed{\frac{dp^a}{d\tau}=0,\qquad p^a=mu^a}\tag{F3}
\]

with declared conventions and a valid domain. Momentum conservation for a composite system additionally requires a total current/charge and boundary-flux accounting. Noether-style conservation requires the stated symmetry/action/boundary hypotheses; it is not supplied by “continuation” alone.

### 5.2 Curved recovery targets, not derived facts

A concrete metric realization seeking a curved physical reading must supply \(g_{ab}\), \(\nabla\), \(\tau\), and a matter coupling whose free test-body limit gives

\[
\boxed{
\frac{d^2x^\mu}{d\tau^2}+\Gamma^\mu{}_{\nu\rho}
\frac{dx^\nu}{d\tau}\frac{dx^\rho}{d\tau}=0
}\tag{C1}
\]

or an explicitly different tested free-path equation. It must separately supply a source/dynamics relation, for example the GR target

\[
\boxed{G_{ab}+\Lambda g_{ab}=\frac{8\pi G}{c^4}T_{ab}}\tag{C2}
\]

and a compatible exchange/conservation statement. In the weak-field slow-motion regime, targets include

\[
\boxed{\nabla^2\Phi_N=4\pi G\rho,\qquad \ddot{\mathbf x}=-\nabla\Phi_N.}\tag{C3}
\]

Equations C1--C3 are mutually distinct obligations: C1 does not yield C2; a connection can describe a free-path law without identifying a physical source; and a source equation does not follow from a verbal “load” label.

### 5.3 Narrative information-force derivation contract

The user-facing claim that gravity is an information force becomes a derivation
programme only by supplying an explicit residual and translation chain. The
core object is not a physical Newton by name. It is a force in the declared
information realization: the derivative of unresolved balance.

Let a candidate introduce the following **new premises**, none inherited from
01, 03, or 01i's existing propositions:

\[
Z:\bigl(S_t,\mathcal H^W_{[t_0,t]},\mathcal R_t,\mathcal O_t\bigr)
\longrightarrow q\in\mathcal Q_I,
\qquad
\mathcal R_I:\mathcal Q_I\longrightarrow K_I,
\]

where \(\mathcal Q_I\) is a declared differential information-state space,
\(K_I\) is an ordered/differentiable residual-value domain, and \(Z\) has a
preparation, readout, composition, equivalence, and loss declaration. Define
only where the derivative exists

\[
\boxed{\mathcal F_I(q):=-D\mathcal R_I(q)\in T_q^*\mathcal Q_I.}\tag{IF1}
\]

\(\mathcal F_I\) is the proposed **information force**: the covector of
unresolved balance. A response map
\(B_q:T_q^*\mathcal Q_I\to T_q\mathcal Q_I\) is additionally required if the
candidate uses it to determine an update direction. The object is intrinsic to
the candidate information theory, but it has no automatic physical units,
spacetime transformation law, or source role.

The physical bridge must then establish all of the following equations or
algorithms in their declared domains:

\[
\begin{aligned}
K_{\rm N}&:(q,\mathcal F_I,\Theta)\to\mathbb R^3,
&[K_{\rm N}]&=\mathrm{kg\,m\,s^{-2}},
&K_{\rm N}&=d\mathbf p/dt,\\
K_4&:(q,\mathcal F_I,\Theta)\to T^*M,
&&&K_4=Dp_\mu/d\tau,\\
L&:(q,\mathcal F_I,\Theta)\to T^{\rm eff}_{\mu\nu},
&&&\nabla^\mu T^{\rm eff}_{\mu\nu}=J_\nu,\\
\Phi&:(q,\mathcal F_I,\Theta)\to(M,g_{\mu\nu},\nabla,\mathcal O_{\rm phys}).
\end{aligned}\tag{IF2}
\]

\(\Theta:(q,\mathcal O_t)\to(\tau,\mathcal A_{\rm acc})\) is the typed physical-clock and proper-acceleration/support readout bridge. The first line
is the proposed \(k_{\rm N}\) translation: a newton is a measured SI readout of
the information force only if the equality to momentum change is proved. The
second line is the corresponding covariant exchange target. The last two lines
remain distinct: force/momentum exchange is not a rank-two source, and a source
is not geometry or a matter free-path law.

**Conditional theorem candidate T0 (information-force gravity recovery).** If
one concrete realization supplies \(Z,\mathcal R_I,B,K_{\rm N},K_4,L,\Phi\) as
above, proves F1--F6 and G1--G8, satisfies H-PC and the history-bearing
attribution condition, derives universal coupling, and meets the stated
weak-field, clock, tidal, UFF, local-Lorentz, and PPN limits, then it derives
its claimed physical gravitational regime from an information-force
construction. The theorem derives neither force identity nor quantum gravity:
it only licenses the named recovery in the proved domain.

**Why T0 remains unproved.** No current corpus artifact supplies
\(\mathcal Q_I\), \(\mathcal R_I\), any \(K\) map, a physical clock, a source,
a geometry, or their dynamics. Consequently IF1 is a precise proposed core
force definition, while IF2 and T0 are bridge obligations. Calling the result
``actual gravity'' before these calculations are closed would be circular or
merely interpretive.

**Additional failure tests.** A candidate fails this contract if it: (i) gives
no derivative domain, residual readout, or response rule; (ii) calls
\(-D\mathcal R_I\) a force in newtons without proving \(K_{\rm N}\); (iii)
inserts the information force directly into a metric or stress tensor without
\(L\), \(\Phi\), and Bianchi-compatible exchange; (iv) defines the residual
using the GR metric, force law, or source equation it announces as derived; or
(v) misses any stated free/support, tidal, universality, clock, or precision
limit. If it gives no finite additional discriminator, it remains an
interpretation of the recovered theory.

### 5.4 Conditional metric-source recovery of general relativity

The exact GR analogue of the EM variational construction begins only after a
candidate supplies the geometric and physical premises. In units \(c=1\),
postulate an oriented, time-orientable four-dimensional Lorentzian \((M,g)\),
the Levi--Civita connection, a non-null Dirichlet boundary prescription,
matter fields \(\psi\) universally coupled through \(S_{\rm m}[g,\psi]\), and

\[
\begin{aligned}
 S_{\rm GR}&=\frac{1}{2\kappa}\int_M(R-2\Lambda)\sqrt{|g|}\,d^4x
 +\frac{1}{\kappa}\int_{\partial M}\varepsilon K\sqrt{|h|}\,d^3x\\
 &\quad+S_{\rm joint}+S_{\rm m}[g,\psi],
 \qquad
 T_{\mu\nu}:=-\frac{2}{\sqrt{|g|}}\frac{\delta S_{\rm m}}{\delta g^{\mu\nu}},
 \quad\kappa=8\pi G.
\end{aligned}\tag{GR1}
\]

Every item in GR1 is a **new realization premise**. The Gibbons--Hawking--York
term and any joint terms are required by the stated boundary problem; fixing
the induced metric does not make the bare Einstein--Hilbert integral
stationary. The source \(T_{\mu\nu}\) is a symmetric rank-two tensor from
matter metric variation, not a scalar information residual.

With the declared allowed metric/matter variations, stationarity gives

\[
\boxed{G_{\mu\nu}+\Lambda g_{\mu\nu}=\kappa T_{\mu\nu}}
\qquad\left(=\frac{8\pi G}{c^4}T_{\mu\nu}\text{ after restoring }c\right).
\tag{GR2}
\]

The contracted Bianchi identity is an off-shell geometric identity, so GR2
requires \(\nabla^\mu T_{\mu\nu}=0\) for the total modeled matter source.
Diffeomorphism invariance of the matter action gives the corresponding Noether
identity and, on the matter equations, this conservation statement. Components
may exchange energy--momentum; open regions retain boundary flux.

Geodesic recovery needs one more premise. A test-particle action
\(S_{\rm pp}=-m\int ds\) gives by fixed-endpoint worldline variation

\[
\boxed{u^\nu\nabla_\nu u^\mu=0.}\tag{GR3}
\]

Universal metric coupling is required before this is a
composition-independent free-fall target. It does not cover charged, spinning,
extended, self-gravitating, or quantum bodies without further limits. In the
weak, quasi-static, asymptotically Minkowskian regime with
\(T_{00}\simeq\rho c^2\) and negligible \(\Lambda\) at the stated scale, GR2
and GR3 recover \(\nabla^2\Phi=4\pi G\rho\) and
\(\ddot{\mathbf x}=-\nabla\Phi\). Clock, light, tidal, and PPN recovery still
require the relevant metric solution, coupling, and experimental domain.

**Exact GE breakpoint.** The open problem is a noncircular selection map

\[
\mathsf{Select}_{\rm GR}:
(\mathcal F_I,\mathcal H^W,\mathcal O,\mathsf{BC},\mathsf{Units})
rightrightarrows
[g,\nabla,S_{\rm GR},S_{\rm m},G,\Lambda]_{\mathrm{Diff}(M)}.\tag{GR4}
\]

No current artifact supplies GR4. It must define its residual codomain,
admissible geometry/action class, gauge quotient, boundary/initial conditions,
units/calibration, uncertainty/data rule, and a uniqueness or empirical
selection rule. Listing the Einstein--Hilbert action, Lorentzian metric,
constants, or universal coupling directly as output constraints assumes rather
than derives GR. GR1--GR3 are therefore an exact conditional classical-GR
derivation; GR4 is the remaining information-gravity derivation.

### 5.5 Strongest four-dimensional metric-selection result

The maximal rigorous selector result is conditional. Suppose GR4 proves all of
the following restrictions rather than writing them into its output: a fixed
four-dimensional Lorentzian signature; metric \(g\) as the sole gravitational
geometrical field; a bulk metric equation \(E_{\mu\nu}[g]\) that is local,
natural under every local diffeomorphism, a function of only the metric two-jet,
symmetric, and identically Levi--Civita-divergence-free; no nondynamical
background structure; and a nonzero Einstein-tensor coefficient. The
four-dimensional Lovelock classification then gives

\[
\boxed{E_{\mu\nu}=aG_{\mu\nu}+b g_{\mu\nu}.}\tag{GR5}
\]

With a separately supplied universal metric matter coupling, divide by
\(a\ne0\) to write the result as GR2 with \(\Lambda=b/a\) and relative matter
normalization \(\kappa=1/a\) in the selected convention. At action level this
restricted bulk dynamics is represented by Einstein--Hilbert plus a volume term;
boundary completion and four-dimensional topological/total-derivative additions
remain separately specified.

**What GR5 leaves free.** The theorem does not fix \(a\), \(b\), \(G\),
\(\Lambda\), signature, topology, boundary conditions, matter species, or
universal coupling. It does not derive locality, metric-only gravity, absence
of extra fields/backgrounds, or the second-order restriction. Relaxing any of
these admits higher-curvature EFT terms, nonlocal actions, metric-affine or
torsional formulations, extra fields, and other alternatives.

**Residual nonselection.** A bare residual-minimization statement cannot prove
these hypotheses: its domain, norm, measure, admissible fields, and boundary
data encode the selection. Positive residual reweightings preserve zero sets,
and a squared equation residual generally yields higher-order normal equations.
GR5 therefore reduces GR4 to a precise proof obligation, not an assumption-free
GE derivation.

### 5.6 Prior-layer realization obstruction

The selector cannot reach GR5 until it closes a prior physical realization map.
A candidate must supply: (R1) an event carrier and causal/order relation; (R2)
a controlled manifold-like continuum limit with declared dimension and time
orientation; (R3) a volume/scale and observable map that gives a Lorentzian
metric rather than only conformal or Riemannian data; and (R4) a dynamical
selection rule excluding or quantitatively controlling nonlocal, nonmetric,
higher-derivative, and extra-field alternatives. These are the missing domain
of \(\Phi_\epsilon\) and GR4, not consequences of an untyped residual.

External comparison strengthens this boundary. Horizon thermodynamics and
entanglement equilibrium begin with Lorentzian causal geometry, area entropy,
and a stress tensor. Causal-order reconstruction begins with a manifold-like
causal order and a volume element. Information geometry yields a statistical
Riemannian metric. Massless-spin-two consistency begins with Lorentzian QFT and
a graviton. Each can constrain an already specified gravitational regime; none
selects Lorentzian four-dimensional local metric GR plus universal matter
coupling from a generic information residual. This is an underdetermination
result, not a claim that a future specified GE microtheory cannot derive more.

### 5.7 R1: realized-support proto-causal order

The strongest direct GE construction is a combinatorial candidate, not yet
physical spacetime causality. For a declared realization trace, define typed
realized-transition events

\[
e_t=\langle W,G_t,a_t,G_{t+1},\mathcal R_t,\mathcal O_t\rangle\in E^W,
\]

where \(a_t\) is an actually selected admissible continuation. Define a
primitive link \(e\leadsto e'\) only where the trace declares the output/support
of \(e\) a necessary input/support for \(e'\) at the stated grain. This is a
support relation, not automatically physical influence. If (R1a) the link
relation is acyclic and (R1b) every proposed comparable pair has a finite set
of intermediate link-reachable events at the declared resolution, define

\[
e\prec_D e'\quad\Longleftrightarrow\quad e\ne e'
\ \text{and a finite directed }\leadsto\text{ path connects }e\text{ to }e'.
\tag{R1}
\]

**Conditional proposition R1-P.** Under R1a--R1b,
\((E^W,\prec_D)\) is a locally finite strict partial order. Acyclicity gives
irreflexivity, path concatenation gives transitivity, and R1b gives local
finiteness. If observables depend only on the typed relation/trace rather than
event labels or construction order, the result is relabeling invariant;
otherwise construction-order-sensitive observables remain declared physical or
operational data.

**Promotion gates.** R1-P does not make the poset physical causal order. A
candidate must still prove that nodes are physically individuated events, links
are propagating possible influence under an intervention/dynamical model rather
than inference/correlation/resource support, and latent mediators/common causes
are controlled. A Lorentzian-order claim needs a faithful manifoldlike continuum
limit with dimension and causal regularity. Under the corresponding continuum
hypotheses causal order fixes only conformal geometry; a volume/counting
calibration, clocks, and observables remain needed for full metric. Thus R1 is
only the first part of R1--R4, not gravity dynamics or GR4 closure.

### 5.8 Conditional electromagnetic alternate-grounding contract

Electromagnetism is a **separate proposed field-edge grounding/physical realization** of the same information-force construction, not gravity under another name and not a second information-force definition. A candidate retains the single core residual derivative

\[
\boxed{\mathcal F_I(q):=-D\mathcal R_I(q)\in T_q^*\mathcal Q_I}
\]

from IF1. It may translate that one object into an electromagnetic realization only through new, separately typed bridges; it does not add another residual derivative or identify \(\mathcal F_I\) with a physical electromagnetic force by declaration. This leaves unchanged every gravity boundary: momentum is not force; gravity and EM are not identical forces; the local accelerometry/history-attribution limitation remains; gravity recovery remains conditional; and 01i remains unreleased.

**01a boundary.** 01a's phase material reads the traversal circle as \(S^1=U(1)\), motivates a complex amplitude, and treats global phase invariance as a conditional Born-rule constraint. It does **not** supply a local U(1) connection, curvature/field strength, charge/current, matter coupling, Maxwell equation, QED construction, or EM observable. Its statement that the gauge group is contingent rule-content is not a completed gauge derivation. H-EM must not present any of these as inherited.

**H-EM required bridges.** A concrete EM realization must supply all of the following, with domain, codomain, units, composition rule, measurement protocol, approximation/control domain, and relativistic transformation behavior:

1. **Separately typed state and clock:** \(X_{\rm EM}:\mathfrak C\to\mathcal X_{\rm EM}\) and \(\Theta_{\rm EM}:\mathcal X_{\rm EM}\to(\tau_{\rm EM},\mathcal O_{\rm EM})\), including preparation, readout, and physical-clock validation. A continuation record or cycle order is not automatically either object.
2. **Local gauge structure:** a U(1) connection \(A_\mu\), its covariant derivative and curvature/field strength \(F_{\mu\nu}\), the local gauge transformation of connection and charged matter, and a declared physical equivalence relation; or an explicit viable alternative with equal specificity.
3. **Charge and current:** an operational charge assignment and current \((\rho,j^\mu)\), their source role, and an exchange/continuity law such as \(\nabla_\mu j^\mu=0\) in the stated domain.
4. **Matter coupling and response:** a charged-matter coupling and Lorentz-force target \(m u^\nu\nabla_\nu u^\mu=qF^\mu{}_{\nu}u^\nu\), or a named viable alternative with distinct, testable response predictions. The response is not gravity and must not be imported as its own proof.
5. **Dynamics:** an action and derived equations, or a viable alternative that supplies equivalent stated dynamical, conservation, and boundary content.
6. **Gauge-invariant observables:** operational observables built from field strength, flux, holonomy/Wilson loop, scattering, or declared alternatives; a gauge-dependent potential alone is not an observable claim.
7. **Boundary and interface conditions:** stated source, material/interface, and asymptotic or finite-boundary conditions, including flux and matching rules.
8. **Conservation and exchange:** field--matter stress--energy and charge/current accounting, including all local and boundary exchange terms.
9. **Relativistic covariance:** a covariant formulation and stated transformation/domain conditions.
10. **Empirical recovery:** Maxwell theory and QED in their respective tested domains, or an explicit quantitatively tested alternative with finite discriminators and error bounds.

**Anti-circularity.** The realization fails if it defines \(\mathcal R_I\), \(X_{\rm EM}\), \(\Theta_{\rm EM}\), or the translation from the single \(\mathcal F_I\) by assuming the Maxwell/QED action, Maxwell equations, a physical connection or field strength, charge conservation, Lorentz-force response, or the EM observables that it then claims to derive. A gauge label, global phase invariance, or a pre-existing Maxwell/QED equation is not a closure of this bridge.

**EM falsifiers.** The candidate fails if: (i) its allegedly physical observables vary under gauge transformations without an explicit physical symmetry-breaking account; (ii) charge/current or field--matter balance fails in its declared closed/bounded system after fluxes are counted; (iii) its stated interface/boundary conditions contradict the claimed field or source behavior; (iv) its response law fails the declared covariant matter tests; (v) it cannot recover the named Maxwell/QED target or its alternative prediction is experimentally excluded; or (vi) it has no finite additional discriminator while claiming more than an interpretation. These falsify H-EM, not P1--P3 or the passive-reuse result. The ledger therefore does **not** claim physical electromagnetism, Maxwell theory, or QED is derived.

**Conditional variational recovery (new premises, exact consequences).** The
strongest classical derivation available is conditional on a concrete field-edge
realization. Postulate an oriented four-dimensional Lorentzian \((M,g)\), a
principal \(U(1)\) bundle with connection \(A\), curvature \(F=dA\), charged
matter \(\Phi\), and

\[
 S_{\rm edge}[A,\Phi]=-
 \frac{1}{4g_{\rm em}^{2}}\int_M F_{\mu\nu}F^{\mu\nu}\sqrt{|g|}\,d^4x
 +S_{\rm m}[g,A,\Phi],
 \qquad
 J^\nu:=-\frac{1}{\sqrt{|g|}}\frac{\delta S_{\rm m}}{\delta A_\nu}.
 \tag{EM1}
\]

These are **new physical premises**. They do not follow from generic residual
balancing, 01a's global phase discussion, or the existence of
\(\mathcal F_I=-D\mathcal R_I\). In particular, they posit the gauge group,
connection, Maxwell quadratic form, coupling, matter representation, and
spacetime/boundary structure.

For allowed connection variations,

\[
\begin{aligned}
 \delta S_{\rm edge}
 &=\int_M\sqrt{|g|}\left[
 g_{\rm em}^{-2}\nabla_\mu F^{\mu\nu}-J^\nu\right]\delta A_\nu\,d^4x\\
 &\quad-g_{\rm em}^{-2}\int_{\partial M}\sqrt{|h|}\,
 n_\mu F^{\mu\nu}\delta A_\nu\,d^3x.
\end{aligned}\tag{EM2}
\]

A declared Dirichlet boundary condition, or a stated alternative boundary
Legendre term and flux datum, removes or accounts for the surface variation.
Stationarity for arbitrary interior variations then gives

\[
\boxed{\nabla_\mu(g_{\rm em}^{-2}F^{\mu\nu})=J^\nu,
\qquad dF=0.}\tag{EM3}
\]

The homogeneous equation is a consequence of \(F=dA\); the sourced equation
is a consequence of EM1 plus the variational and boundary premises. Smooth
ordinary Maxwell dynamics requires \(\nabla_\nu J^\nu=0\), which follows from
the sourced equation or, with the matter equations, the local gauge Noether
identity. For a region with boundary, its integral statement includes current
flux and is not blanket subsystem conservation.

If the realization also supplies the charged-particle premise

\[
S_{\rm pp}=-m\int ds+q\int A_\mu dx^\mu,\tag{EM4}
\]

then fixed-endpoint worldline variation yields

\[
\boxed{m u^\nu\nabla_\nu u^\mu=qF^\mu{}_{\nu}u^\nu.}\tag{EM5}
\]

The associated field stress tensor gives matching field--matter momentum
exchange only with a diffeomorphism-covariant matter action, matter equations,
and retained specified boundary flux. Thus EM1--EM4 plus those conditions entail
the classical Maxwell equations, current balance, and Lorentz-force response in
their declared domain.

**Exact breakpoint.** This is a conditional *classical-electrodynamics*
derivation, not a derivation of EM1 from GE. A global phase gives at most a
pure-gauge derivative and cannot provide nonzero curvature, the Maxwell kinetic
term, charge/current, or a source. The map from \(\mathcal F_I\) to EM1 remains
a required noncircular bridge. QED further requires quantization, physical-state
gauge treatment, charged quantum fields/statistics, anomaly control, and
renormalization; photons and QED are not consequences of EM3--EM5.

## 6. Units, observables, and conservation constraints

### 6.1 Units/type table

| Candidate object | Required physical type/units | What the corpus currently supplies | Prohibited shortcut |
|---|---|---|---|
| \(C_{\mathrm{alt},\mathcal A}\) | Class-specific ordered value or, only when defined, a class unit. | A grounding-dependent cost relation. | Treating it as joules, newton-seconds, action, kilograms, or curvature by name. |
| \(\mathbf p\) | Three-vector, \(\mathrm{kg\,m\,s^{-1}}\), with measurement and frame transformation. | A possible directional structural reading. | Equating arbitrary Narrative magnitude with physical momentum. |
| \(p^a\) | Four-vector/covector under the declared relativistic structure; energy-momentum composition and mass shell. | Nothing of this type. | Calling any carried history “four-momentum.” |
| \(g_{ab},\nabla\) | Lorentzian metric/connection or declared alternative with transformation and curvature structures. | Graph/frame relations and an analogy of budget. | Calling a graph, statistical distance, or frame relation a spacetime metric. |
| \(\tau,a^a\) | Physical-clock proper time and covariant acceleration/accelerometer observable. | Local realization/cycle ordering. | Equating a cycle count or coordinate acceleration with proper acceleration. |
| \(T_{ab}\) | Dimensioned stress--energy source, tensor/current behavior, operational definition, and exchange/conservation structure. | No source type. | Inserting cost/load directly into a field equation. |

Setting \(c=\hbar=G=1\) would not remove these distinctions. It can hide dimensions numerically while leaving tensor type, operational meaning, and conservation requirements unresolved.

### 6.2 Observable constraints

A physical realization must define at least:

1. a state-preparation and momentum/four-momentum measurement protocol;
2. a clock protocol whose reading is demonstrably the claimed \(\tau\), not merely an event count;
3. an accelerometer/support-force observable distinguishing free and supported bodies in its stated domain;
4. an extended/tidal observable (or explicit replacement) for the claimed curvature distinction;
5. source/flux or quasi-local/asymptotic accounting with boundary conditions, especially because GR has no generally unique local gravitational-energy tensor; and
6. a history-bearing attribution protocol that names the retained observations, support/source changes, compression losses, translation, gauge treatment, uncertainty, and the domain in which its inference map may distinguish momentum-like from load-shaped readings.

No frame-free observer is needed or allowed. A mediating frame may form comparisons, but it must itself be explicit and operationally constrained. A local accelerometer is one input to this protocol, not a sufficient attribution procedure.

### 6.3 Conservation and Bianchi constraint

If a candidate claims a covariant metric equation with Einstein-tensor form, the contracted Bianchi identity requires a compatible source/exchange relation. At minimum it must state

\[
\nabla^aT^{\rm eff}_{ab}=J_b,
\]

including every modeled exchange term, and show how the gravitational dynamics accommodate \(J_b\). A candidate cannot assert conserved “load” while leaving its current/tensor type, boundary flux, or exchange law undefined.

Likewise, a candidate claims conserved total physical momentum only after it names the symmetry/current or equivalent balance law, specifies the system boundary, and includes field and boundary fluxes. Subsystem persistence is not total conservation.

## 7. Conditional theorem candidate: two readings of one implemented law

### 7.1 Required-premises table

Let \(\mathfrak S\) be a concrete physical realization of \(\mathfrak C\). The following are new premises for \(\mathfrak S\), not results of this artifact.

| ID | Required premise | Minimum content | Failure if absent |
|---|---|---|---|
| P-1 | Physical state/identity | A physical state space/algebra, composition rule, and map identifying the candidate continuation support with measurable system states. | \(S_t\) remains project-level structure, not physical state. |
| P-2 | Declared physical alteration class | A physical \(\mathcal A_{\rm phys}\) with units, support, measurement, and a demonstrated relation between its alteration increment and state change. | “Zero cost” is undefined or merely verbal. |
| P-3 | Momentum map | \(P_{\rm N}\) and, if relativistic, \(P_4\), plus measurement, transformation, and composition/exchange laws. | No physical momentum or four-momentum claim. |
| P-4 | Flat dynamics/symmetry | Action/equations plus translation symmetry or stated alternative proving F1--F3 and total balance laws in the stated regime. | No inertial/free-transport recovery. |
| P-5 | Load/source map | Dimensioned \(L\) to \(T^{\rm eff}_{ab}\) or named source, with Bianchi-compatible conservation/exchange. | No gravitational source claim. |
| P-6 | Geometry map | Controlled \(\Phi_\epsilon\) to metric/connection or stated alternative, causal observables, and transformation/gauge rules. | No geometry or curved continuation. |
| P-7 | Matter/free-path map | Matter action/coupling proving C1 or a stated alternative; include range of test-body approximation. | No geodesic/free-fall claim. |
| P-8 | Clock/acceleration map | Physical proper-time and accelerometer maps, with kinematic dilation and gravitational redshift/clock targets or declared alternatives. | No claim about proper acceleration or clock behavior. |
| P-9 | Universality/equivalence map | Universal coupling calculation including composition, self-energy/binding energy, spin/history dependence, UFF, local Lorentz/position, and redshift constraints. | No equivalence-principle recovery. |
| P-10 | Weak-field/precision limits | Newtonian/PPN, light/clock, tidal, and local-Lorentz limits with parameters and error domain. | No empirical compatibility claim. |
| P-11 | History-bearing inference map | A typed \(\mathcal H^W_{[t_0,t]}\), plus a local/extended/source/cross-frame attribution protocol with no privileged external viewpoint. | A present local record cannot be used to attribute momentum versus gravity, and “inseparable in frame” is untestable or overextended. |
| P-12 | Discriminator | A finite parameterized prediction that differs from GR plus standard low-energy matter, or an honest interpretation-only status. | No new physical reconciliation claim beyond reinterpretation. |

### 7.2 Theorem candidate T1

**Theorem candidate T1 (conditional passive-continuation recovery).** Let \(\mathfrak S\) satisfy P-1 through P-12. Suppose its physical alteration class has a passive-reuse sector in which the additional alteration increment vanishes, and suppose the same implemented dynamics has:

1. a controlled flat regime in which P-3 and P-4 prove momentum-preserving free transport; and
2. a controlled load-shaped regime in which P-5 through P-8 prove a geometry-selected free-path equation and the claimed source/clock relations.

Then \(\mathfrak S\) recovers, in its stated domains, two readings of one implemented passive-continuation law: **flat free transport** and **load-shaped free propagation**. If P-9--P-12 also hold, it is an empirically constrained candidate for relating the two readings.

**Proof skeleton.** P-1--P-2 give a physically typed meaning to passive reuse rather than a project-internal cost. P-3--P-4 establish that, in the flat domain, the physical free solution carries conserved measured momentum as F2/F3. P-5--P-7 establish that, in the curved/load-shaped domain, the physical source and geometry select the free-path equation C1 (or its declared alternative). P-8 makes the clock and acceleration terms operational; P-9--P-10 constrain universality and empirical limits; P-11 requires any momentum/load attribution to be made from the declared history-bearing record rather than a present local snapshot; P-12 separates a new testable theory from an interpretation. Therefore the two regimes share one *implemented* dynamics under the listed premises. ∎

**Strict limit.** T1 does **not** conclude that momentum and gravity are the same force. Physical momentum is a state/charge-like quantity with a change/transfer law; in GR, ideal free fall is not locally a gravitational force on the test body, while support forces and tidal curvature remain measurable. T1 only tests whether one lawful continuation structure can recover both regimes without collapsing their distinct physical roles.

## 8. Unresolved bridges and no-go constraints

Every item below is unresolved in the current corpus. A candidate must close, evade under stated assumptions, or narrow its claim domain; it may not hide the item with terminology.

1. **State bridge:** no map tells which graph/history equivalence class is one physical system state, how composites form, or how gauge-equivalent descriptions are identified.
2. **Alteration bridge:** no physical alteration class equates a project cost increment with impulse, work, action, or any other measurable exchange in general.
3. **Momentum bridge:** no \(P_{\rm N}\) or \(P_4\) exists; no mass, time, velocity, phase space, mass shell, or transformation law has been derived.
4. **Noether/symmetry constraint:** passive reuse cannot replace translation symmetry/action hypotheses needed for a physical momentum conservation theorem.
5. **Geometry bridge:** no continuum/coarse-graining, dimension, signature, metric, connection, curvature, or gauge/diffeomorphism map exists.
6. **Geodesic bridge:** a geodesic equation requires metric/connection and a matter/test-body principle; it is not a rewording of continued history.
7. **Clock bridge:** no proper-time functional or validated physical-clock map identifies cycle/order with \(\tau\); exact time dilation and redshift remain recovery targets.
8. **Acceleration bridge:** no operational accelerometer map distinguishes coordinate acceleration, proper acceleration, support stress, and frame convention.
9. **Load/source bridge:** no dimensioned source maps \(C_{\mathrm{alt}}\) or 01a load to \(T_{ab}\), an alternative source, or a measurable flux.
10. **Bianchi/exchange constraint:** any covariant source equation must meet the relevant divergence identity with accounted exchange; an undefined load cannot do so.
11. **Field-dynamics bridge:** a connection/free-path law does not determine an Einstein, Poisson, teleparallel, scalar-tensor, or any other field equation.
12. **Equivalence-principle bridge:** no universal matter coupling derives equality of inertial/passive gravitational response, UFF, or local Lorentz/position behavior. The 01a “seam” remains a shape-level proposal.
13. **History-attribution constraint:** a present local record, including an accelerometer result, cannot alone attribute passive continuation to momentum or gravity. The model must preserve the relevant change, support/source, and comparison history and supply a typed inference map from it; history without that map is also insufficient.
14. **Energy-localization constraint:** absence of a unique generally covariant local gravitational-energy tensor does not excuse missing source, quasi-local/asymptotic energy, flux, or boundary accounting.
15. **Teleparallel/Mach constraint:** a torsion reformulation or relational/Machian language is not a bridge unless it gives action, matter coupling, equivalence proof, source/observable accounting, and tested limits. It cannot be invoked to call gravity ordinary flat-space inertia.
16. **UFF/EEP constraint:** composition-, internal-energy-, spin-, or history-dependent coupling must be calculated and remain within established equivalence and clock constraints, or be a quantitatively testable exclusion.
17. **Local-Lorentz/PPN constraint:** preferred-frame, anisotropic, nonmetric, or propagation deviations require finite parameters and must meet the stated experimental bounds.
18. **Extended-body limitation:** simple test-particle geodesics do not automatically cover spinning, charged, self-gravitating, quantum, or extended systems.
19. **Observable/gauge constraint:** a frame-relative record is not automatically a gauge-invariant gravitational observable; the model must supply relational instruments or another operational construction.
20. **Discriminator constraint:** if every realization is observationally identical to GR plus standard low-energy matter and supplies no additional finite parameter prediction, the result may be an interpretation but not a novel empirical reconciliation.

## 9. Falsifiers for a proposed implementation

The following falsify a *candidate bridge/realization*, not the structural P1--P3 result merely by being unmet.

1. **Class-definition failure:** the proposed alteration class lacks a comparison class, support, unit/ordering, or measurement protocol, yet treats its cost as zero or comparable.
2. **Flat-limit failure:** its claimed free flat regime does not yield constant measured momentum/four-momentum under its stated isolation conditions.
3. **Conservation failure:** it claims conserved physical momentum/load but gives no symmetry/current/exchange law, or measured field/boundary flux violates its balance equation.
4. **Units/type failure:** it cannot map the alleged load to an operational dimensioned source of the required tensor/current type.
5. **Bianchi/source failure:** its covariant field equation requires a source relation that its proposed load cannot satisfy, without an accounted exchange mechanism.
6. **Clock failure:** its physical clock conflicts with established kinematic dilation, gravitational redshift, Shapiro-delay, precision-clock, or stated PPN measurements in its claimed domain.
7. **Free/support failure:** it cannot distinguish zero proper acceleration of a free ideal test body from nonzero proper acceleration of a supported body, or conflicts with tested free-fall behavior.
8. **Tidal failure:** it calls gravity removable in all cases yet produces no extended relative-acceleration/curvature-or-alternative observable consistent with tidal phenomena.
9. **Universality failure:** it predicts composition, internal-energy, spin, or history dependence outside established UFF/EEP limits without a surviving quantitative fit.
10. **Local-Lorentz/PPN failure:** it produces preferred-frame, anisotropic, or post-Newtonian departures outside constraints in the regime claimed.
11. **Teleparallel/Mach shortcut failure:** it invokes either as an explanation without the complete physical maps and empirical calculations listed in §8.
12. **Circularity failure:** it assumes a metric, geodesic principle, universal coupling, stress tensor, or conservation law in order to announce that passive continuation derived it.
13. **History-free attribution failure:** it assigns a present passive continuation to momentum transport or gravity from a local snapshot, including an accelerometer reading, without the declared history-bearing record and inference map.
14. **No-discriminator failure:** it supplies only a rephrasing of established GR/matter predictions and no finite, rejectable additional claim while asserting novel physical reconciliation.

## 10. Final claim ledger

| Claim | Status | Reason |
|---|---|---|
| Present operative history is carried only as current represented/support structure. | **Internal proposition (P1).** | Follows from 03's historical-sufficiency and 01's frame-indexed vocabulary. |
| Reuse of carried structure has zero additional alteration cost in a declared class. | **Internal proposition (P2).** | Follows from the declared passive-continuation cost definition; ordinal version is weaker where no addition exists. |
| Passive continuation means no total activity/cost or no elapsed time. | **Rejected.** | The class increment is not total activity, higher-frame support, global time, or physical proper time. |
| Carried history is physical momentum. | **Not derived.** | Requires P-1--P-4 of §7, especially a dimensioned momentum map and free dynamics. |
| Momentum is force. | **Rejected.** | Physical momentum and its rate of transfer/change are distinct target types. |
| Gravity is a force on a freely falling GR test body. | **Rejected as a GR target statement.** | Free test-body proper acceleration target is zero; support and tidal phenomena remain physical. |
| Momentum and gravity are the same force. | **Rejected.** | The proposed programme tests two recovered readings/regimes, not force identity. |
| A present local record, including a proper-acceleration reading, attributes passive continuation to momentum or gravity. | **Rejected.** | Proper acceleration distinguishes free from supported motion in its declared domain; momentum/load attribution requires the history-bearing record and inference map of P3. |
| In-frame inseparability erases gravity/inertia distinctions. | **Rejected.** | It is a history-required attribution limitation, not force identity; extended/tidal/source comparisons remain part of the required inference. |
| Flat inertial momentum transport follows from passive continuation. | **Recovery target only.** | Requires physical state, momentum, dynamics, symmetry, and observable maps. |
| Four-momentum transport follows. | **Recovery target only.** | Requires relativistic geometry, \(P_4\), proper time, and transport law. |
| Metric, connection, geodesic equation, proper acceleration, and stress--energy follow. | **Recovery targets only.** | All corresponding maps remain absent. |
| Equivalence principle follows from common budget/passive continuation language. | **Recovery target only.** | Requires universal coupling plus UFF/local-Lorentz/clock calculations and tests. |
| One physical implementation can have flat and load-shaped passive-continuation readings. | **Conditional theorem candidate T1.** | Only if every premise P-1--P-12 is supplied and the recovery/falsifier audit is passed. |

## 11. Conclusion

The corpus has one exact passive-continuation result: within a declared class, reuse of operative carried structure incurs zero **additional alteration cost**. The result preserves the distinction between class-relative reuse, total activity, and inferred/physical time. It supports a momentum-like structural reading only in the limited sense that present carried structure conditions later continuation without a new alteration of that structure.

A physics result needs much more. Flat momentum transport requires a physical state/momentum map and dynamical/symmetry theorem. Curved free propagation requires a geometry, clock, matter coupling, and source dynamics. Equivalence requires universal coupling and its experimental consequences. The source-backed Stage-1 record and the present ledger establish that no reviewed source or current formal paper supplies these project-specific bridges. A present in-frame record may establish its declared local relation, including proper acceleration, but it cannot alone attribute passive continuation to momentum or gravity; that requires the typed history-bearing record and inference map of P3. The proposal therefore remains a constrained research programme: test whether one concrete passive-continuation implementation can recover both regimes, while preserving the fact that momentum and gravity are not the same force.

H-EM adds a distinct conditional electromagnetic field-edge programme. It preserves the single information-force residual derivative and requires separately typed state/clock, local gauge structure, charge/current, matter response, action/equations, gauge-invariant observables, interfaces/boundaries, exchange, covariance, and Maxwell/QED-or-tested-alternative recovery. It is not a gravity identity claim, does not remove the local attribution limitation, and does not derive physical electromagnetism, Maxwell theory, or QED. The gravity programme remains conditional and 01i remains unreleased.
