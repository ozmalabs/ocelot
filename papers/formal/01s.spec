# The STATEMENT of paper 01 --- not an abridgement of it. This file holds the
# statement's OWN content;
# every @pull line is fetched from the long paper at build time and is never
# copied here. Edit this file and the long paper; never edit the generated .tex.
@source 01_law_of_graphic_equalisation_theory_referenced.tex
@out 01s_graphic_equalisation_statement.tex

\title{The Law of Graphic Equalisation\\\large Statement}
\author{Matthew Parslow\\Independent Researcher}
\date{\PaperStatementDateLine}

\begin{document}
\maketitle
\begin{center}
\fbox{\parbox{0.92\textwidth}{\small
\textbf{STATEMENT.} This is the theory; the companion \emph{Law of Graphic
Equalisation} (Theory) is the case for it. What is missing here is not detail but
\emph{argument} --- the removals that establish how little is required are the long
paper's bulk and its actual work, so anything below that a reader wants shown rather
than asserted is shown there. Calling this a short form would describe
it by its length instead of by what it does. Every labelled block below is pulled from the long paper at build time, and so are the
falsifiability commitments attached to them, so none of those can drift from it; the
commitments the long paper carries for material \emph{not} stated here are listed by
title at the end, so the omission stays checkable in this document rather than only in
the build log. The connecting prose is written here and is not synchronised, so it can.
Four companions are named in the material below without being carried by it: \emph{Is}
(the base claim this paper begins after), the physics companion, the mind companion,
and \emph{Narrativium}.}}
\end{center}
\vspace{1em}

\begin{abstract}
One minimal structure is proposed as underlying phenomena usually studied apart. This statement gives
the structure, the frame machinery through which anything reaches it, what happens when a write is
refused, the single prohibition it carries, and the commitments on which it fails. It argues for none
of them. The removals that establish how little is required are the long paper's bulk, and a reader
who doubts a particular claim here should expect to be persuaded there and not by this.
\end{abstract}

\section{The substrate}
The substrate is structure, the transformations operative upon it, and a grammar of which transformations
are admissible. Only the first is required for there to be anything; the other two are what a world in
which anything \emph{happens} costs. Nothing beyond the three is claimed primitive, and anything else exists
where a graph happens to represent it.

@pull def:graph
@pull def:grounding
@pull def:admissible
@pull def:collapse

The Law is that a graph's admissible continuations are fixed by its present structure, and that
realisation selects one of them, which then becomes the antecedent for what follows.

@pull hyp:the-law

A realised deformation is not submitted for entry, so what a containing grammar declines is not undone
by the declining; it stays where it is. That remainder is the residual, and admitting it is how a grammar grows from residual.

@pull def:residual
@pull prop:residual-inadmissible
@pull cor:mint-is-grammar
@pull rem:only-g

What this paper postulates over \emph{Is} is the ledger of Table~\ref{tab:ledger}: named entries, not
a count, each with where it is argued. The prose defending each entry is the long paper's.

@pull tab:ledger

\section{Determinism and sufficiency}
What the Law requires of a transition and what it does not require of the substrate are separate
claims, and both are exposed here: an antecedent has to be there already for a continuation to be
selected from it, the selection adds no primitive randomness of its own, and nothing beyond the three
is needed to carry any of it.

@pull prop:antecedent-state
@pull prop:determinism
@pull hyp:minimal-graph
@pull hyp:discrete

\section{Frames}
A frame is how anything is reached at all: there is no view from nowhere, so every claim is a claim
made in some frame, and the frame is not a container holding contents but the relation that
demarcates them.

\setcounter{axiom}{-2}
@pull ax:no-view
\setcounter{axiom}{0}

@pull def:frame
@pull cor:frame-dimension
@pull prop:two-gates
@pull def:aperture
@pull def:change-grammar
@pull def:states

Provenance is a relation to what produced a structure or event. Its attribution
is inferred from evidence available in a frame; an origin record is evidence,
not a self-authenticating intrinsic mark. A local attribution can be unique
under a declared model. This is distinct from assumption-free closure of the
recursively supplying operators, which is separately argued in the long paper.

@pull def:provenance
@pull rem:provenance-status
@pull prop:provenance-inference

What a frame's gates admit, and what it can reach from where it stands, are two quantities and not
one; a disclosure that moves a gate changes what the gates admit, and that is where an information hazard is
located here rather than treated as a class of its own.

@pull def:capability
@pull def:info-hazard
@pull prop:hazard-threshold

\section{Identity}
Sameness is not read off the substrate. It is fixed by whatever frame individuates, which leaves two
identity relations where ordinary usage has one --- the graph's own continuity with what produced it,
and the tracking a container does of a situated instance.

@pull thm:no-frame-free
@pull def:self-identity
@pull def:supergraph-identity

\section{Economics}
Cost characteristically attaches to writes rather than to holding, and what a write costs is set by
whatever runs the rules rather than by any universal. A graph changes itself directly and its
container only as the region of it that it is, so the distribution of what is free, what is costly and
what is directly writeable is a characterisation of a common configuration rather than a necessity.

@pull prop:economics
@pull prop:no-direct-self-alter
@pull rem:writeability
@pull def:well-formed
@pull prop:evaluation-writes
@pull prop:leak

\section{When a write is refused}
An inadmissible write yields no continuation in that frame. What happens after that --- whether
anything propagates, whether a value is produced instead --- is rule content and not substrate. The
failure itself does not vary; the frames do, and a handler is an installed policy rather than a
discovered semantics.

@pull prop:decoherence-one
@pull prop:handler-relocates
@pull prop:vacated-three-states
@pull prop:termination-supply
@pull prop:boundary-by-crossing

\section{Time}
Time is not a substrate dimension. It is a dimension a frame constructs from represented succession.
A closure cycle is the simplest self-contained, repeatable operational unit for that construction, and
is therefore the default hypothesis where no finer or externally supplied counter is represented. It
is not a substrate requirement: a frame cannot establish from inside whether an apparent cycle is
self-closing, clocked, superframe-scheduled, or realised at a fixed hidden duration.

@pull ax:no-time
@pull prop:time-inferred
@pull prop:cycle-unit
@pull def:present
@pull prop:no-implicit-historical-state
@pull cor:history

\section{Primitives, and the single prohibition}
@pull def:primitives
@pull rem:nothing-compulsory
@pull prop:rule-runner
@pull prop:runner-opaque
@pull prop:runner-recursion

Stepping back: the account forbids very little, and what it does forbid is one thing recurring rather than a list.

@pull prop:prohibition

That prohibition has a formal analogue --- under classical bivalence, a language strong enough to represent its own syntax cannot define its own
truth predicate, and must be given it from a metalanguage --- and the analogue is proved, though the
mapping from frames to formal systems is argued rather than proved. What is forbidden is complete
self-capture and not partial self-modelling, which is why reflective towers work and a frame can know
a great deal about itself. Two candidates are deliberately not on the list: that a frame cannot obtain
a quantity whose unit does not close within it is contingent rule content, and that a frame cannot
decide anything without writing is a pattern of the write-economics rather than a universal.

\section{Carvings}
Since the rules draw the boundary and the rules are contingent, no carving is privileged. That does
not make the notion vacuous: an ill-formed cut costs more writes, so a frame under a budget tends to
be running cheaper cuts, and what looks like a joint is where the cheap cuts of frames doing shared
work coincide. The step from shared work to similar cuts rests on a posit, labelled here as one.

@pull hyp:cheap-cut
@pull prop:convergence-observed
@pull prop:compression-convergence
@pull hyp:located-degradation

\section{Falsifiability}
The substrate risks little by design and the groundings carry the risk. Below are the commitments
attached to the material this statement carries. They are a subset: the long paper carries the full
set, including those for results not stated here, and the omitted commitments are listed below by
title, so the omission stays visible rather than becoming a claim.

\begin{enumerate}[leftmargin=*]
@falsifier Time is inferred, not primitive
@falsifier Closure is the default operational clock hypothesis
@falsifier Two gates, and absence is not residual
@falsifier Partial-order sufficiency
@falsifier Composition
@falsifier Minimal graph sufficiency
@falsifier Discrete sufficiency
@falsifier Antecedent-state principle
@falsifier Graph-law determinism
@falsifier No implicit historical state
@falsifier Frame-relative identity
@falsifier Located degradation
@falsifier Convergence is not enforced
@falsifier Provenance is never closed by inference
@falsifier Solutions are nearly unique under a binding constraint
@falsifier Cost is the write
@falsifier Self-change is subset-change
@falsifier Minting is a rule
@falsifier Residual is inadmissibility
@falsifier Realisation is single-valued
@falsifier No-copy
@falsifier Decoherence is one operation
@falsifier A swallowed failure is relocated, never closed
@falsifier Dependents are not held by the referent
@falsifier Termination follows supply, not containment
@falsifier A boundary is known only by crossing it
@falsifier Robustness trades against legibility
@falsifier Capability and accessibility are distinct
@falsifier A hazard is a signed capability change above a frame-relative threshold
@falsifier The relativity of grounding is a consequence, and can fail as one
\end{enumerate}

\end{document}

# --- regeneration ---
# From the repository root:  python3 tools/build_statement.py papers/formal/01s.spec
# The generator exits non-zero if a @pull label no longer exists in the long
# paper, and lists every labelled block the spec does not pull, so material
# added to the long paper surfaces as a review item rather than silently
# diverging.
