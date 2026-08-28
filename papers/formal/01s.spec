# Short version of paper 01. This file holds the short paper's OWN content;
# every @pull line is fetched from the long paper at build time and is never
# copied here. Edit this file and the long paper; never edit the generated .tex.
@source 01_law_of_graphic_equalisation_theory_referenced.tex
@out 01s_graphic_equalisation_short.tex

\title{The Law of Graphic Equalisation\\\large Short Form}
\author{Matthew Parslow\\Independent Researcher}
\date{\textbf{Draft \textemdash\ draft-2026-08-28.2}\\[2pt]28 August 2026 \textbullet\ short form}

\begin{document}
\maketitle
\begin{center}
\fbox{\parbox{0.92\textwidth}{\small
\textbf{SHORT FORM.} This is a generated abridgement of \emph{The Law of Graphic
Equalisation} (Theory). It states the substrate and its consequences without
demonstrating the removals that establish minimality; the long paper carries
those, and is the reference for any claim here that a reader wants shown rather
than asserted. Every definition and proposition below is pulled from the long
paper at build time, so the two cannot drift.}}
\end{center}
\vspace{1em}

\begin{center}
\begin{minipage}{0.78\textwidth}
\small\itshape
In the beginning\ldots{} there was no time, so it wasn't really the beginning. Then, at some
non-time, not-later, there was graph.
\end{minipage}
\end{center}
\vspace{0.8em}

\begin{abstract}
One minimal structure is proposed as underlying phenomena usually studied apart. This short form
gives the structure, the frame machinery through which anything reaches it, the single prohibition it
carries, and the commitments on which it fails. It does not argue for minimality: that argument is
the bulk of the long paper and consists of removing candidate primitives one at a time, which is
worth reading only by someone who doubts a particular removal.
\end{abstract}

\section{The substrate}
Reality is modelled as typed graphs plus a grammar of which relations may exist. Nothing beyond that
triple is primitive; anything else exists where a graph happens to represent it.

@pull def:graph
@pull def:grounding
@pull def:admissible
@pull def:collapse

The Law is that a graph's admissible continuations are fixed by its present structure, and that
realisation selects one of them, which then becomes the antecedent for what follows.

@pull def:residual

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

\section{Time}
Time is not a substrate dimension. It is inferred by a frame from its own closure cycles, which is
why a frame that runs no rules has none.

@pull prop:time-inferred
@pull prop:cycle-unit
@pull def:present

\section{The runner, and the single prohibition}
@pull def:runner
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
@pull hyp:located-degradation

\section{Falsifiability}
The substrate risks little by design and the groundings carry the risk. These are the commitments on
which the substrate itself fails.

\begin{enumerate}[leftmargin=*]
@falsifier Minimal graph sufficiency
@falsifier Discrete sufficiency
@falsifier Antecedent-state principle
@falsifier Graph-law determinism
@falsifier Located degradation
@falsifier Convergence is not enforced
\end{enumerate}

\end{document}

# --- regeneration ---
# From papers/formal/:  python3 ../../tools/build_short_paper.py 01s.spec
# The generator exits non-zero if a @pull label no longer exists in the long
# paper, and lists every labelled block the spec does not pull, so material
# added to the long paper surfaces as a review item rather than silently
# diverging.
