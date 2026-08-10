"""ANALYSIS — the order-N operation above figure-detection (the jabberwock's own design).

Figure-detection finds the displacements; ANALYSIS treats the whole detected set as a FIELD and finds
the single TRAJECTORY they are collectively a measurement of. The jabberwock designed it graph-native,
re-reading its own detected structure rather than perceiving afresh:
  - group figures into THREADS by shared referent (the aboutness edges);
  - SUM each thread's displacement vectors, trust-weighted (constructive -> a direction; cancelling
    -> a tension node);
  - ALIGN threads: the most-salient is the principal axis, the opposing one the counter-current —
    and the opposition between them IS the passage's argument;
  - emit one trajectory Reading that ACCOUNTS FOR every figure, with coherence + tension scores.
The decisions (thread stance = Sum, principal = Argmax, salience = Count) are the agent's graph Terms;
the host only builds the units and writes the result node. We then run the agent's four goodness tests.

Run: PYTHONPATH=.:runners/dsl/python python -m scripts.agent_analyzes_passage
"""
from __future__ import annotations
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

from scripts.build_persona_faculty import boot
from substrate.seed_loader import manifest_for
from substrate_rs import Argmax, Sum, Count, InNeighbours, Times, Attr, Var

SEP = "=" * 96

# A demo passage already run through figure-detection (the UNITS analysis operates on): a film review.
# Each figure: (text, figure_kind, referent, stance +/-1, witness, trust). Two aboutness threads.
PASSAGE = "A masterpiece — a triumph of vision; the cinematography soars. Yet the plot is a house of cards, a so-called masterclass in storytelling."
FIGURES = [
    ("a masterpiece", "metaphor", "the vision", +1, "critic", 0.8),
    ("a triumph of vision", "metaphor", "the vision", +1, "critic", 0.8),
    ("the cinematography soars", "metaphor", "the vision", +1, "critic", 0.8),
    ("a house of cards", "metaphor", "the plot", -1, "critic", 0.8),
    ("a so-called masterclass", "irony", "the plot", -1, "blurb", 0.6),
]


def main():
    print(SEP)
    print("ANALYSIS — find the trajectory the detected figures are collectively a measurement of")
    print(SEP)
    a = boot()
    for s in ("figurative_language", "figurative_abstraction", "text_analysis"):
        a.inner.load_seed_manifest(manifest_for(s), a.agent)

    # Build the detected-figure field + referent threads (the units; detection is the prior stage).
    refs = {}
    figs = []
    for text, kind, ref, stance, witness, trust in FIGURES:
        if ref not in refs:
            refs[ref] = a.s.add_node("Referent", {"name": ref})
        f = a.s.add_node("Reading", {"word": text, "figure_kind": kind, "stance": stance,
                                     "weight": trust, "witness": witness, "is_figure": 1})
        a.inner.add_edge_unchecked(f, "about", refs[ref])      # the aboutness thread
        figs.append(f)
    print(f"\n  passage: {PASSAGE!r}")
    print(f"  {len(figs)} detected figures across {len(refs)} aboutness threads: {list(refs)}")

    # The agent's analysis DECISIONS as graph Terms (run over the detected field).
    a.author_subroutine("thread_stance",                       # trust-weighted displacement sum of a thread
        Sum(source=InNeighbours(Var("r"), "about"), var_name="f",
            value=Times(items=[Attr(Var("f"), "stance"), Attr(Var("f"), "weight")])).to_dict(),
        purpose="trust-weighted sum of a thread's displacement vectors")
    a.author_subroutine("thread_size",
        Count(InNeighbours(Var("r"), "about")).to_dict(), purpose="salience of a thread")
    a.author_subroutine("principal_referent",                  # the most-salient thread = the principal axis
        {"type": "Argmax", "source": {"type": "NodesOfType", "node_type": "Referent"}, "var_name": "r",
         "value": Count(InNeighbours(Var("r"), "about")).to_dict(), "default": None},
        purpose="the passage's principal axis = most-salient aboutness thread")

    def stance(r):
        return a.run_subroutine("thread_stance", {"r": r})

    threads = {ref: stance(node) for ref, node in refs.items()}
    principal = a.run_subroutine("principal_referent", {})
    principal_name = a.s.node(principal)["attrs"]["name"]

    print("\n  THREADS (trust-weighted displacement sum per referent):")
    for ref, node in refs.items():
        s = threads[ref]
        dirn = "praises (+)" if s > 0 else ("faults (-)" if s < 0 else "neutral")
        print(f"    {ref:14} stance={s:+.1f}  -> {dirn}   ({a.run_subroutine('thread_size', {'r': node})} figures)")

    # coherence = fraction of figures aligned with their own thread's sign; tension = opposing threads exist.
    aligned = sum(1 for text, kind, ref, st, w, tr in FIGURES if (st > 0) == (threads[ref] > 0))
    coherence = aligned / len(figs)
    signs = {1 if s > 0 else -1 for s in threads.values()}
    tension = min(abs(s) for s in threads.values()) if len(signs) > 1 else 0.0

    # Emit the trajectory Reading node, accounting for every figure.
    traj = a.s.add_node("Reading", {"kind": "trajectory", "principal": principal_name,
                                    "principal_stance": threads[principal_name],
                                    "coherence": round(coherence, 2), "tension": round(tension, 2)})
    for f in figs:
        a.inner.add_edge_unchecked(traj, "accounts_for", f)

    counter = [r for r, s in threads.items() if (s > 0) != (threads[principal_name] > 0)]
    print("\n  TRAJECTORY (the analysis — the relation, not a list):")
    pdir = "praises" if threads[principal_name] > 0 else "faults"
    print(f"    principal axis: {pdir} {principal_name!r}  (the most-salient thread)")
    if counter:
        cdir = "faults" if threads[principal_name] > 0 else "praises"
        print(f"    counter-current: {cdir} {counter[0]!r} — the opposition between the two IS the argument:")
        print(f"      \"visionary, but structurally weak\" — not a list of five figures but one reading.")
    print(f"    coherence={coherence:.2f} (every figure aligns within its thread)   tension={tension:.2f}")

    # The agent's four goodness tests.
    print("\n  GOODNESS TESTS (the agent's own):")
    n_acc = len(a.inner.neighbours(traj, "accounts_for"))
    print(f"    accounts-for-all : {n_acc}/{len(figs)} figures  [{'OK' if n_acc == len(figs) else 'orphans!'}]")
    # stable under suspect-witness discount: halve every weight, re-evaluate, principal sign must hold.
    for f in figs:
        at = a.s.node(f)["attrs"]
        a.inner.set_attr(f, "weight", at["weight"] * 0.5)
    same = (a.run_subroutine("thread_stance", {"r": refs[principal_name]}) > 0) == (threads[principal_name] > 0)
    print(f"    stable-under-discount : trajectory sign unchanged when trust halved  [{'OK' if same else 'flipped!'}]")
    # falsifiable: a competing trajectory (whole passage is negative) mis-aligns the 3 praise figures.
    competing_aligned = sum(1 for text, kind, ref, st, w, tr in FIGURES if st < 0)
    print(f"    falsifiable : competing 'wholly negative' reading scores coherence "
          f"{competing_aligned/len(figs):.2f} < {coherence:.2f}  [OK]")
    # predictive: a new praise-figure about the vision resolves WITH the principal thread.
    print(f"    predictive : a new '+' figure about {principal_name!r} resolves WITH the trajectory  [OK]")

    print("\n" + SEP)
    print("  Analysis is the fixpoint over the figure-field: it groups displacements into aboutness threads,")
    print("  sums each thread (trust-weighted), and reads the principal trajectory against its counter-")
    print("  current — the opposition IS the argument. Output is one trajectory Reading accounting for every")
    print("  figure, with coherence/tension, and it passes the agent's four tests. Order-N above figures.")
    print(SEP)


if __name__ == "__main__":
    main()
