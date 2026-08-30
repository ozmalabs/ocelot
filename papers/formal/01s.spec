# The STATEMENT of paper 01 --- not an abridgement of it. This file holds the
# statement's OWN content;
# every @pull line is fetched from the long paper at build time and is never
# copied here. Edit this file and the long paper; never edit the generated .tex.
@source 01_law_of_graphic_equalisation_theory_referenced.tex
@out 01s_graphic_equalisation_statement.tex

\title{The Law of Graphic Equalisation\\\large Statement}
\author{Matthew Parslow\\Independent Researcher}
\date{\textbf{Draft \textemdash\ draft-2026-08-30.2}\\[2pt]30 August 2026 \textbullet\ statement}

\begin{document}
\maketitle
\begin{center}
\fbox{\parbox{0.92\textwidth}{\small
\textbf{STATEMENT.} This is the theory; the companion \emph{Law of Graphic
Equalisation} (Theory) is the case for it. What is missing here is not detail but
\emph{argument} --- the removals that establish how little is required are the long
paper's bulk and its actual work, so anything below that a reader wants shown rather
than asserted is shown there. Calling this a short form, as an earlier version did,
described it by its length instead of by what it does. Every definition and proposition
below is pulled from the long paper at build time, so the two cannot drift.}}
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
The substrate is structure, the transformations operative upon it, and a grammar of which relations
may exist. Only the first is required for there to be anything; the other two are what a world in
which anything \emph{happens} costs. Nothing beyond the three is primitive, and anything else exists
where a graph happens to represent it.

@pull def:graph
@pull def:grounding
@pull def:admissible
@pull def:collapse

The Law is that a graph's admissible continuations are fixed by its present structure, and that
realisation selects one of them, which then becomes the antecedent for what follows.

@pull def:residual
@pull rem:only-g

\section{Frames}
A frame is how anything is reached at all: there is no view from nowhere, so every claim is a claim
made in some frame, and the frame is not a container holding contents but the relation that
demarcates them.

@pull def:frame
@pull cor:frame-dimension
@pull prop:two-gates
@pull def:aperture
@pull def:change-grammar
@pull def:states

\section{Economics}
Cost attaches to writes rather than to holding, and what a write costs is set by whatever runs the
rules rather than by any universal.

@pull prop:economics
@pull def:well-formed
@pull rem:evaluation-writes
@pull prop:leak

\section{When a write is refused}
An inadmissible write yields no continuation in that frame. What happens after that --- whether
anything propagates, whether a value is produced instead --- is rule content and not substrate, so the
exception reading below is an analogy and the systems it names are policies rather than discoveries.

@pull rem:decoherence-one
@pull rem:handler-abuse
@pull rem:vacated
@pull rem:supply-not-containment
@pull rem:failure-instrument

\section{Time}
Time is not a substrate dimension. It is inferred by a frame from its own closure cycles, which is
why a frame that runs no rules has none.

@pull prop:time-inferred
@pull prop:cycle-unit
@pull def:present

\section{Primitives, and the single prohibition}
@pull def:runner
@pull rem:nothing-compulsory
@pull prop:rule-runner
@pull prop:runner-opaque
@pull prop:runner-recursion

The account forbids one thing: a frame cannot get outside itself. It cannot be transparent to itself
at the level it is running at, cannot measure its own throughput, and cannot hold a view from
nowhere. That prohibition has a formal analogue --- a language of sufficient strength cannot define
its own truth predicate, and must be given it from a metalanguage --- and the analogue is proved,
though the mapping from frames to formal systems is argued rather than proved. What is forbidden is
complete self-capture and not partial self-modelling, which is why reflective towers work and a frame
can know a great deal about itself.

\section{Carvings}
Since the rules draw the boundary and the rules are contingent, no carving is privileged. That does
not make the notion vacuous: an ill-formed cut costs more writes, so a frame under a budget tends to
be running cheaper cuts, and the cuts that look like joints are the cheap ones rather than the real
ones.

@pull prop:convergence-observed
@pull prop:compression-convergence
@pull hyp:located-degradation

\section{Falsifiability}
The substrate risks little by design and the groundings carry the risk. Below are the commitments
attached to the material this abridgement states. They are a subset: the long paper carries the full
set, including those for results not stated here, and the generator reports the difference on every
build so the omission stays visible rather than becoming a claim.

\begin{enumerate}[leftmargin=*]
@falsifier Minimal graph sufficiency
@falsifier Discrete sufficiency
@falsifier Antecedent-state principle
@falsifier Graph-law determinism
@falsifier Located degradation
@falsifier Convergence is not enforced
@falsifier Provenance is never closed by inference
@falsifier Solutions are nearly unique under a binding constraint
@falsifier Decoherence is one operation
@falsifier A swallowed failure is relocated, never closed
@falsifier Dependents are not held by the referent
@falsifier Termination follows supply, not containment
@falsifier A boundary is known only by crossing it
@falsifier Robustness trades against legibility
\end{enumerate}

\end{document}

# --- regeneration ---
# From papers/formal/:  python3 ../../tools/build_statement.py 01s.spec
# The generator exits non-zero if a @pull label no longer exists in the long
# paper, and lists every labelled block the spec does not pull, so material
# added to the long paper surfaces as a review item rather than silently
# diverging.
